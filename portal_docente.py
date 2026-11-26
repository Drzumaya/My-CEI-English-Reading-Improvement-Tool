import base64
from datetime import datetime, timedelta
import urllib.parse
from zoneinfo import ZoneInfo
import psycopg
import streamlit as st

TZ_SONORA = ZoneInfo("America/Hermosillo")


def _find_secret_pd(key_name: str) -> str:
    if key_name in st.secrets:
        return str(st.secrets[key_name]).strip()
    key_low = key_name.lower()
    for k, v in st.secrets.items():
        if str(k).lower() == key_low and not isinstance(v, dict):
            return str(v).strip()
        if isinstance(v, dict):
            for sk, sv in v.items():
                if str(sk).lower() == key_low:
                    return str(sv).strip()
    return ""


def _open_pg_pd():
    pg_host = _find_secret_pd("PG_HOST") or _find_secret_pd("DB_HOST")
    pg_user = _find_secret_pd("PG_USER") or _find_secret_pd("DB_USER")
    pg_pass = _find_secret_pd("PG_PASSWORD") or _find_secret_pd("DB_PASSWORD")
    pg_port = int(_find_secret_pd("PG_PORT") or _find_secret_pd("DB_PORT") or 6543)
    pg_db = _find_secret_pd("PG_DBNAME") or _find_secret_pd("DB_NAME") or "postgres"
    if pg_host and pg_user and pg_pass:
        puertos = [pg_port, 6543] if pg_port != 6543 else [6543]
        for p in puertos:
            try:
                return psycopg.connect(
                    host=pg_host, port=p, dbname=pg_db, user=pg_user, password=pg_pass,
                    sslmode="require", connect_timeout=10, prepare_threshold=None
                )
            except Exception:
                pass
    db_url = _find_secret_pd("SUPABASE_DB_URL") or _find_secret_pd("DATABASE_URL")
    if db_url and db_url.startswith("postgres"):
        if "sslmode=" not in db_url:
            db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
        try:
            return psycopg.connect(db_url, connect_timeout=10, prepare_threshold=None)
        except Exception:
            pass
    return None



def asegurar_tablas_portal_docente(conn):
    """Crea y actualiza las tablas para la bóveda fiscal, pagos y bitácora docente."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teacher_profiles (
                teacher_id TEXT PRIMARY KEY,
                usuario_login TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                apellido_paterno TEXT NOT NULL,
                apellido_materno TEXT DEFAULT '',
                curp TEXT DEFAULT '',
                rfc TEXT DEFAULT '',
                cedula_profesional TEXT DEFAULT '',
                grado_academico TEXT DEFAULT '',
                certificacion_ingles TEXT DEFAULT '',
                niveles_autorizados TEXT DEFAULT '',
                telefono TEXT DEFAULT '',
                email TEXT DEFAULT '',
                disponibilidad TEXT DEFAULT '',
                documento_b64 TEXT DEFAULT '',
                porcentaje_comision NUMERIC(5,2) DEFAULT 0.0,
                clabe_interbancaria TEXT DEFAULT '',
                estatus TEXT DEFAULT 'Activo',
                registrado_por TEXT DEFAULT '',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        cur.execute("""
            ALTER TABLE teacher_profiles
            ADD COLUMN IF NOT EXISTS porcentaje_comision NUMERIC(5,2) DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS clabe_interbancaria TEXT DEFAULT '';
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teacher_fiscal_vault (
                usuario_login TEXT PRIMARY KEY,
                csf_b64 TEXT DEFAULT '',
                csf_updated_at TIMESTAMP WITH TIME ZONE,
                opinion_32d_b64 TEXT DEFAULT '',
                opinion_32d_updated_at TIMESTAMP WITH TIME ZONE,
                caratula_banco_b64 TEXT DEFAULT '',
                clabe_interbancaria TEXT DEFAULT '',
                ine_cedula_b64 TEXT DEFAULT '',
                cfdi_periodo TEXT DEFAULT '',
                cfdi_pdf_b64 TEXT DEFAULT '',
                cfdi_xml_b64 TEXT DEFAULT '',
                cfdi_uploaded_at TIMESTAMP WITH TIME ZONE,
                validado_admin BOOLEAN DEFAULT FALSE,
                observaciones_admin TEXT DEFAULT '',
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teacher_payouts (
                id SERIAL PRIMARY KEY,
                usuario_docente TEXT NOT NULL,
                periodo TEXT NOT NULL,
                monto_bruto NUMERIC(12,2) DEFAULT 0.0,
                estatus_pago TEXT DEFAULT 'Pendiente CFDI',
                referencia_bancaria TEXT DEFAULT '',
                fecha_pago DATE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teacher_pedagogical_notes (
                id SERIAL PRIMARY KEY,
                usuario_docente TEXT NOT NULL,
                usuario_estudiante TEXT NOT NULL,
                nota TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)


def evaluar_cumplimiento_fiscal_docente(vault_row: dict, dia_corte_mensual: int = 25) -> dict:
    """Evalúa el estado del expediente legal/fiscal y la alerta de 3 días para CFDI."""
    ahora = datetime.now(TZ_SONORA)
    hoy = ahora.date()
    periodo_actual = hoy.strftime("%Y-%m")

    faltantes = []
    vencidos = []

    if not vault_row.get("csf_b64"):
        faltantes.append("Constancia de Situación Fiscal (CSF)")
    elif vault_row.get("csf_updated_at"):
        dias_csf = (ahora - vault_row["csf_updated_at"]).days
        if dias_csf > 30:
            vencidos.append(f"Constancia de Situación Fiscal ({dias_csf} días > 30 días)")

    if not vault_row.get("opinion_32d_b64"):
        faltantes.append("Opinión de Cumplimiento SAT (32-D Positiva)")
    elif vault_row.get("opinion_32d_updated_at"):
        dias_32d = (ahora - vault_row["opinion_32d_updated_at"]).days
        if dias_32d > 30:
            vencidos.append(f"Opinión de Cumplimiento 32-D ({dias_32d} días > 30 días)")

    if not vault_row.get("caratula_banco_b64") or len(str(vault_row.get("clabe_interbancaria", "")).strip()) != 18:
        faltantes.append("Carátula Bancaria y CLABE (18 dígitos)")

    if not vault_row.get("ine_cedula_b64"):
        faltantes.append("Identificación Oficial (INE) o Cédula Profesional")

    cfdi_ok_mes = (
        str(vault_row.get("cfdi_periodo") or "").strip() == periodo_actual
        and bool(vault_row.get("cfdi_pdf_b64"))
        and bool(vault_row.get("cfdi_xml_b64"))
    )

    expediente_base_completo = (len(faltantes) == 0 and len(vencidos) == 0)

    ultimo_dia_mes = (hoy.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    dia_limite = min(max(1, int(dia_corte_mensual)), ultimo_dia_mes.day)
    fecha_corte = hoy.replace(day=dia_limite)
    dias_para_corte = (fecha_corte - hoy).days

    alerta_3_dias = (not cfdi_ok_mes) and (0 <= dias_para_corte <= 3)
    plazo_vencido_mes = (not cfdi_ok_mes) and (dias_para_corte < 0)

    return {
        "periodo_actual": periodo_actual,
        "expediente_base_completo": expediente_base_completo,
        "faltantes": faltantes,
        "vencidos": vencidos,
        "cfdi_ok_mes": cfdi_ok_mes,
        "fecha_corte_str": fecha_corte.strftime("%d/%m/%Y"),
        "dias_para_corte": dias_para_corte,
        "alerta_3_dias": alerta_3_dias,
        "plazo_vencido_mes": plazo_vencido_mes,
    }


def build_whatsapp_recordatorio_cfdi(nombre_docente: str, telefono_docente: str, fecha_corte_str: str, dias_restantes: int, periodo_actual: str) -> str:
    """Genera enlace de WhatsApp para recordar el envío oportuno del CFDI."""
    digs = "".join(c for c in str(telefono_docente or "") if c.isdigit())
    if len(digs) == 10:
        digs = f"52{digs}"

    if dias_restantes == 0:
        urgencia_txt = f"hoy *{fecha_corte_str}* vence el plazo"
    elif dias_restantes == 1:
        urgencia_txt = f"falta *1 día* (cierre *{fecha_corte_str}*)"
    else:
        urgencia_txt = f"faltan *{dias_restantes} días* (cierre *{fecha_corte_str}*)"

    msg = (
        f"¡Hola Prof. {nombre_docente}! 👋 Te saludamos de *Administración — Career English Institute (CEI)*. "
        f"Te recordamos amablemente que {urgencia_txt} para subir tu factura *CFDI 4.0 (PDF + XML)* "
        f"correspondiente al periodo *{periodo_actual}* en *Mi Portal Docente CEI*, a fin de programar tu pago en tiempo y forma. 💼✅"
    )
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me{digs}?text={encoded}" if digs else f"https://wa.me?text={encoded}"
# ==============================================================================
# BLOQUE 2A — CABECERA DOCENTE, FICHA Y ALERTAS FISCALES
# ==============================================================================
def render_portal_docente_cei(
    usuario_actual: str,
    rol_actual: str,
    puede_ver_estudiantes: bool = True,
    puede_motivar_wa: bool = True,
    puede_retroalimentar: bool = True,
    puede_ver_comisiones: bool = True,
    es_admin_o_owner: bool = False,
    dia_corte_cfdi: int = 25,
    institute_address: str = "Agua Prieta, Sonora, México"
):
    """Renderiza el Portal Docente CEI con Bóveda Fiscal y Radar Estudiantil."""
    conn = _open_pg_pd()
    if not conn:
        st.error("❌ Sin conexión con la base de datos institucional.")
        return

    try:
        asegurar_tablas_portal_docente(conn)
        conn.commit()

        doc_objetivo = str(usuario_actual or "").strip()
        if es_admin_o_owner:
            with conn.cursor() as cur:
                cur.execute("SELECT usuario_login FROM teacher_profiles ORDER BY nombre ASC;")
                lista_docs = [str(r[0]).strip() for r in cur.fetchall() if r and r[0]]
            if lista_docs:
                doc_objetivo = st.selectbox(
                    "Seleccionar Docente a auditar / gestionar:",
                    lista_docs,
                    key="sel_docente_portal_admin"
                )

        try:
            from compliance_engine import render_medidor_compliance_confianza
            render_medidor_compliance_confianza(doc_objetivo, "Teacher", conn)
        except Exception:
            pass

        with conn.cursor() as cur:
            cur.execute("""
                SELECT teacher_id, usuario_login, nombre, apellido_paterno, apellido_materno,
                       COALESCE(curp, ''), COALESCE(rfc, ''), COALESCE(cedula_profesional, ''),
                       COALESCE(grado_academico, ''), COALESCE(certificacion_ingles, ''),
                       COALESCE(niveles_autorizados, 'A1-C2'), COALESCE(telefono, ''),
                       COALESCE(email, ''), COALESCE(porcentaje_comision, 0.0),
                       COALESCE(clabe_interbancaria, ''), COALESCE(estatus, 'Activo')
                FROM teacher_profiles
                WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (doc_objetivo,))
            t_row = cur.fetchone()

        if not t_row:
            st.info(f"ℹ️ Aún no existe ficha en **Plantilla Docente** para **`{doc_objetivo}`**.")
            return

        (
            t_id, _t_usr, t_nom, t_pat, t_mat, t_curp, t_rfc, t_ced,
            t_grado, t_cert, t_niveles, t_tel, t_mail, t_pct, t_clabe, t_est
        ) = (list(t_row) + ["", "", "", "", "", "", "", "", "", "", "A1-C2", "", "", 0.0, "", "Activo"])[:16]

        nombre_doc_completo = f"{t_nom} {t_pat} {t_mat}".strip()

        st.info(
            f"🆔 **ID Docente:** `{t_id}`  |  🧑‍🏫 **Titular:** **{nombre_doc_completo}**\n\n"
            f"🎓 **Grado:** {t_grado}  |  📜 **Cédula:** `{t_ced or 'En trámite'}`  |  🌍 **Certificación:** {t_cert}\n\n"
            f"🪪 **CURP:** `{t_curp}`  |  🧾 **RFC:** `{t_rfc}`  |  📚 **Niveles:** `{t_niveles}`  |  🏷️ **Estatus:** `{t_est}`"
        )

        with conn.cursor() as cur:
            cur.execute("""
                SELECT csf_b64, csf_updated_at, opinion_32d_b64, opinion_32d_updated_at,
                       caratula_banco_b64, clabe_interbancaria, ine_cedula_b64,
                       cfdi_periodo, cfdi_pdf_b64, cfdi_xml_b64, cfdi_uploaded_at,
                       validado_admin, observaciones_admin
                FROM teacher_fiscal_vault
                WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (doc_objetivo,))
            v_row = cur.fetchone()

        vault_dict = {}
        if v_row:
            keys_v = [
                "csf_b64", "csf_updated_at", "opinion_32d_b64", "opinion_32d_updated_at",
                "caratula_banco_b64", "clabe_interbancaria", "ine_cedula_b64",
                "cfdi_periodo", "cfdi_pdf_b64", "cfdi_xml_b64", "cfdi_uploaded_at",
                "validado_admin", "observaciones_admin"
            ]
            vault_dict = dict(zip(keys_v, v_row))
        if not vault_dict.get("clabe_interbancaria") and t_clabe:
            vault_dict["clabe_interbancaria"] = t_clabe

        eval_f = evaluar_cumplimiento_fiscal_docente(vault_dict, dia_corte_mensual=dia_corte_cfdi)

        if eval_f["alerta_3_dias"]:
            wa_cfdi_url = build_whatsapp_recordatorio_cfdi(
                nombre_docente=nombre_doc_completo,
                telefono_docente=t_tel,
                fecha_corte_str=eval_f["fecha_corte_str"],
                dias_restantes=eval_f["dias_para_corte"],
                periodo_actual=eval_f["periodo_actual"]
            )
            st.warning(
                f"⏰ **AVISO URGENTE DE FACTURACIÓN ({eval_f['periodo_actual']}):** "
                f"Faltan **{eval_f['dias_para_corte']} día(s)** para el cierre (**{eval_f['fecha_corte_str']}**) "
                "y falta cargar tu **CFDI 4.0 (PDF + XML)**."
            )
            st.link_button("📲 Recordatorio de Facturación por WhatsApp (3 Días)", url=wa_cfdi_url, type="primary")
        elif eval_f["plazo_vencido_mes"]:
            st.error(f"🚨 **PLAZO DE FACTURACIÓN VENCIDO ({eval_f['fecha_corte_str']}):** Sube tu CFDI 4.0 (PDF + XML).")

        if eval_f["expediente_base_completo"] and eval_f["cfdi_ok_mes"]:
            st.success(f"✅ **Documentación Legal y Fiscal Completa ({eval_f['periodo_actual']}):** Expediente y CFDI validados al 100%.")
        elif not eval_f["expediente_base_completo"]:
            det_f = "; ".join(eval_f["faltantes"] + eval_f["vencidos"])
            st.error(f"⚠️ **Documentación Legal/Fiscal Pendiente o Vencida:** {det_f}")
        # ======================================================================
        # SUB-BLOQUE 2B — PESTAÑA ACADÉMICA (ESTUDIANTES, WHATSAPP Y NOTAS)
        # ======================================================================
        tab_acad, tab_fin = st.tabs([
            "🎓 Mis Estudiantes, Rachas y Retroalimentación",
            "💰 Comisiones, Pagos y Bóveda Legal/Fiscal"
        ])

        with tab_acad:
            if not puede_ver_estudiantes:
                st.warning("⛔ Tu perfil actual no tiene permiso para visualizar la cartera de estudiantes.")
            else:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users_padron ORDER BY id DESC;")
                    u_cols = [d for d in cur.description]
                    u_rows = cur.fetchall()

                alumnos_doc = []
                targets_doc = {doc_objetivo.lower(), str(t_id).lower()} - {""}
                for ur in u_rows:
                    ud = dict(zip(u_cols, ur))
                    if str(ud.get("rol") or "").strip().lower() in ("estudiante", "student", "alumno"):
                        asig = str(ud.get("docente_asignado") or ud.get("teacher") or "").strip().lower()
                        if asig in targets_doc:
                            alumnos_doc.append(ud)

                k1, k2 = st.columns(2)
                k1.metric("🎓 Estudiantes Asignados", f"{len(alumnos_doc)}")
                k2.metric("📚 Niveles Autorizados", f"{t_niveles}")

                if not alumnos_doc:
                    st.info("ℹ️ Aún no tienes estudiantes asignados directamente a tu matrícula docente.")
                else:
                    app_pub = str(_find_secret_pd("PUBLIC_APP_URL") or ("https://" + "myceigrammarly.streamlit.app")).strip()
                    for al in alumnos_doc:
                        al_u = str(al.get("usuario") or "").strip()
                        al_mat = str(al.get("matricula") or "").strip()
                        al_niv = str(al.get("nivel") or al.get("nivel_cefr") or "B1").strip()
                        al_tel = str(al.get("telefono") or "").strip()

                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT COUNT(*), COALESCE(AVG(calificacion_global), 0.0)
                                FROM lessons_folios
                                WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s));
                            """, (al_u,))
                            cnt_f, avg_f = cur.fetchone() or (0, 0.0)

                        with st.container(border=True):
                            st.markdown(f"**🎓 {al_u}**" + (f" • 🆔 `{al_mat}`" if al_mat else "") + f" • Nivel **{al_niv}**")
                            st.caption(f"📚 Lecciones: **{int(cnt_f or 0)}**  •  📊 Promedio: **{float(avg_f or 0.0):.1f}%**")

                            c_d1, c_d2 = st.columns([1.4, 1.8])
                            with c_d1:
                                if puede_motivar_wa:
                                    digs = "".join(ch for ch in al_tel if ch.isdigit())
                                    if len(digs) == 10:
                                        digs = f"52{digs}"
                                    msg_w = (
                                        f"¡Hola {al_u}! 👋 Te saluda tu docente *{nombre_doc_completo}* de *Career English Institute (CEI)*. "
                                        f"Llevas *{int(cnt_f or 0)} lecciones* con promedio de *{float(avg_f or 0.0):.1f}%*. "
                                        f"¡Sigue practicando esta semana para alcanzar tu meta! 🚀 {app_pub}"
                                    )
                                    wa_u = f"https://wa.me{digs}?text={urllib.parse.quote(msg_w)}" if digs else f"https://wa.me?text={urllib.parse.quote(msg_w)}"
                                    st.link_button("📲 Motivar por WhatsApp", url=wa_u, width="stretch")

                            with c_d2:
                                if puede_retroalimentar:
                                    with st.expander("📝 Agregar Nota Pedagógica", expanded=False):
                                        nota_txt = st.text_input("Observación académica:", key=f"nota_doc_{al_u}")
                                        if st.button("Guardar Nota", key=f"btn_save_nota_{al_u}"):
                                            if nota_txt.strip():
                                                with conn:
                                                    with conn.cursor() as cur:
                                                        cur.execute("""
                                                            INSERT INTO teacher_pedagogical_notes (usuario_docente, usuario_estudiante, nota)
                                                            VALUES (%s, %s, %s);
                                                        """, (doc_objetivo, al_u, nota_txt.strip()))
                                                st.success("✅ Nota guardada en el expediente.")
        # ======================================================================
        # BLOQUE 3 DE 3 (FINAL) — COMISIONES, PAGOS Y BÓVEDA LEGAL / FISCAL
        # ======================================================================
        with tab_fin:
            if not puede_ver_comisiones:
                st.warning("⛔ Tu perfil actual no tiene permiso para visualizar comisiones y pagos docentes.")
            else:
                pct_doc_f = float(t_pct or 0.0)
                total_base_doc = 0.0
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT COALESCE(SUM(sp.monto_total), 0.0)
                            FROM student_payments sp
                            JOIN users_padron up ON LOWER(TRIM(sp.usuario_estudiante)) = LOWER(TRIM(up.usuario))
                            WHERE LOWER(COALESCE(sp.estatus, 'pagado')) IN ('pagado', 'completado', 'activo')
                              AND LOWER(TRIM(COALESCE(up.docente_asignado, ''))) IN (LOWER(TRIM(%s)), LOWER(TRIM(%s)));
                        """, (doc_objetivo, str(t_id)))
                        total_base_doc = float(cur.fetchone() or 0.0)
                except Exception:
                    pass

                com_devengada = round(total_base_doc * (pct_doc_f / 100.0), 2)

                kf1, kf2, kf3 = st.columns(3)
                kf1.metric("💼 Tasa Honorario / Comisión", f"{pct_doc_f:.1f}%")
                kf2.metric("🏦 Base Cobrada de Grupo", f"${total_base_doc:,.2f}")
                kf3.metric("💰 Honorario / Comisión Generada", f"${com_devengada:,.2f}")

                st.divider()
                st.markdown("##### 📜 Requerimientos Legales y Fiscales Vigentes (SAT México / CEI)")
                st.markdown(
                    "- **1. Constancia de Situación Fiscal (CSF):** Antigüedad menor a **30 días** (Servicios Profesionales / Honorarios o RESICO).\n"
                    "- **2. Opinión de Cumplimiento SAT (32-D):** Sentido **Positivo** con antigüedad menor a **30 días**.\n"
                    "- **3. Carátula Bancaria (CLABE 18 dígitos):** A nombre del titular docente.\n"
                    "- **4. Identificación Oficial (INE) o Cédula Profesional Vigente.**\n"
                    f"- **5. Factura Electrónica CFDI 4.0 (PDF + XML):** Subir antes del **día {dia_corte_cfdi}** de cada mes (Uso CFDI `G03`)."
                )

                with st.form(f"form_boveda_fiscal_{doc_objetivo}"):
                    st.markdown(f"##### 🗂️ Subir o Actualizar Documentación Fiscal ({eval_f['periodo_actual']})")
                    cb1, cb2 = st.columns(2)
                    with cb1:
                        f_csf = st.file_uploader("📄 Constancia de Situación Fiscal (PDF)", type=["pdf"], key=f"up_csf_{doc_objetivo}")
                        f_32d = st.file_uploader("📄 Opinión de Cumplimiento 32-D (PDF)", type=["pdf"], key=f"up_32d_{doc_objetivo}")
                        clabe_in = st.text_input(
                            "🏦 CLABE Interbancaria (18 dígitos) *",
                            value=str(vault_dict.get("clabe_interbancaria") or ""),
                            max_chars=18
                        )
                    with cb2:
                        f_banco = st.file_uploader("🏦 Carátula Estado de Cuenta (PDF/PNG/JPG)", type=["pdf", "png", "jpg", "jpeg"], key=f"up_bnc_{doc_objetivo}")
                        f_ine = st.file_uploader("🪪 INE o Cédula Profesional (PDF/PNG/JPG)", type=["pdf", "png", "jpg", "jpeg"], key=f"up_ine_{doc_objetivo}")

                    st.markdown(f"**🧾 Factura Mensual CFDI 4.0 — Periodo `{eval_f['periodo_actual']}`**")
                    cf1, cf2 = st.columns(2)
                    with cf1:
                        f_cfdi_pdf = st.file_uploader("📑 CFDI en formato PDF", type=["pdf"], key=f"up_cfdi_pdf_{doc_objetivo}")
                    with cf2:
                        f_cfdi_xml = st.file_uploader("💻 CFDI en formato XML", type=["xml"], key=f"up_cfdi_xml_{doc_objetivo}")

                    if st.form_submit_button("💾 Guardar y Actualizar Bóveda Fiscal", type="primary", width="stretch"):
                        clabe_ok = "".join(c for c in clabe_in if c.isdigit())
                        if clabe_ok and len(clabe_ok) != 18:
                            st.error("⚠️ La CLABE Interbancaria debe tener exactamente 18 dígitos.")
                        else:
                            csf_b = base64.b64encode(f_csf.read()).decode("utf-8") if f_csf else vault_dict.get("csf_b64", "")
                            o32_b = base64.b64encode(f_32d.read()).decode("utf-8") if f_32d else vault_dict.get("opinion_32d_b64", "")
                            bnc_b = base64.b64encode(f_banco.read()).decode("utf-8") if f_banco else vault_dict.get("caratula_banco_b64", "")
                            ine_b = base64.b64encode(f_ine.read()).decode("utf-8") if f_ine else vault_dict.get("ine_cedula_b64", "")
                            cpdf_b = base64.b64encode(f_cfdi_pdf.read()).decode("utf-8") if f_cfdi_pdf else (
                                vault_dict.get("cfdi_pdf_b64", "") if vault_dict.get("cfdi_periodo") == eval_f["periodo_actual"] else ""
                            )
                            cxml_b = base64.b64encode(f_cfdi_xml.read()).decode("utf-8") if f_cfdi_xml else (
                                vault_dict.get("cfdi_xml_b64", "") if vault_dict.get("cfdi_periodo") == eval_f["periodo_actual"] else ""
                            )

                            with conn:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        INSERT INTO teacher_fiscal_vault (
                                            usuario_login, csf_b64, csf_updated_at,
                                            opinion_32d_b64, opinion_32d_updated_at,
                                            caratula_banco_b64, clabe_interbancaria, ine_cedula_b64,
                                            cfdi_periodo, cfdi_pdf_b64, cfdi_xml_b64, cfdi_uploaded_at, updated_at
                                        ) VALUES (
                                            %s, %s, CASE WHEN %s THEN NOW() ELSE NULL END,
                                            %s, CASE WHEN %s THEN NOW() ELSE NULL END,
                                            %s, %s, %s,
                                            %s, %s, %s, CASE WHEN %s THEN NOW() ELSE NULL END, NOW()
                                        )
                                        ON CONFLICT (usuario_login) DO UPDATE SET
                                            csf_b64 = EXCLUDED.csf_b64,
                                            csf_updated_at = CASE WHEN %s THEN NOW() ELSE teacher_fiscal_vault.csf_updated_at END,
                                            opinion_32d_b64 = EXCLUDED.opinion_32d_b64,
                                            opinion_32d_updated_at = CASE WHEN %s THEN NOW() ELSE teacher_fiscal_vault.opinion_32d_updated_at END,
                                            caratula_banco_b64 = EXCLUDED.caratula_banco_b64,
                                            clabe_interbancaria = COALESCE(NULLIF(EXCLUDED.clabe_interbancaria, ''), teacher_fiscal_vault.clabe_interbancaria),
                                            ine_cedula_b64 = EXCLUDED.ine_cedula_b64,
                                            cfdi_periodo = CASE WHEN %s THEN EXCLUDED.cfdi_periodo ELSE teacher_fiscal_vault.cfdi_periodo END,
                                            cfdi_pdf_b64 = EXCLUDED.cfdi_pdf_b64,
                                            cfdi_xml_b64 = EXCLUDED.cfdi_xml_b64,
                                            cfdi_uploaded_at = CASE WHEN %s THEN NOW() ELSE teacher_fiscal_vault.cfdi_uploaded_at END,
                                            updated_at = NOW();
                                    """, (
                                        doc_objetivo, csf_b, bool(f_csf),
                                        o32_b, bool(f_32d),
                                        bnc_b, clabe_ok, ine_b,
                                        eval_f["periodo_actual"], cpdf_b, cxml_b, bool(f_cfdi_pdf or f_cfdi_xml),
                                        bool(f_csf), bool(f_32d),
                                        bool(f_cfdi_pdf or f_cfdi_xml or vault_dict.get("cfdi_periodo") == eval_f["periodo_actual"]),
                                        bool(f_cfdi_pdf or f_cfdi_xml)
                                    ))
                            st.success("✅ Bóveda Legal y Fiscal actualizada correctamente.")
                            st.rerun()

                st.divider()
                st.markdown("##### 💳 Historial de Liquidaciones y Pagos Docentes")
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT periodo, monto_bruto, estatus_pago, COALESCE(referencia_bancaria, '—'), fecha_pago
                        FROM teacher_payouts
                        WHERE LOWER(TRIM(usuario_docente)) = LOWER(TRIM(%s))
                        ORDER BY id DESC;
                    """, (doc_objetivo,))
                    pays_d = cur.fetchall()
                if not pays_d:
                    st.info("ℹ️ Aún no hay dispersiones bancarias registradas en el historial.")
                else:
                    for per_p, mto_p, est_p, ref_p, fch_p in pays_d:
                        st.markdown(
                            f"• **Periodo `{per_p}`** — **`${float(mto_p or 0.0):,.2f}`** | "
                            f"Estatus: **{est_p}** | Ref: `{ref_p}`"
                            + (f" | Fecha: `{fch_p}`" if fch_p else "")
                        )
    finally:
        try:
            conn.close()
        except Exception:
            pass

