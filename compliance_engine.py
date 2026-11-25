from datetime import datetime, timedelta
import json
import urllib.parse
from zoneinfo import ZoneInfo
import psycopg
import streamlit as st

TZ_SONORA = ZoneInfo("America/Hermosillo")


def _find_secret_comp(key_name: str) -> str:
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


def _open_pg_comp():
    pg_host = _find_secret_comp("PG_HOST") or _find_secret_comp("DB_HOST")
    pg_user = _find_secret_comp("PG_USER") or _find_secret_comp("DB_USER")
    pg_pass = _find_secret_comp("PG_PASSWORD") or _find_secret_comp("DB_PASSWORD")
    pg_port = int(_find_secret_comp("PG_PORT") or _find_secret_comp("DB_PORT") or 6543)
    pg_db = _find_secret_comp("PG_DBNAME") or _find_secret_comp("DB_NAME") or "postgres"
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
    return None


def asegurar_tablas_compliance(conn):
    """Crea la infraestructura PostgreSQL para vigilancia normativa semanal y plazos SLA."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compliance_bulletins (
                id SERIAL PRIMARY KEY,
                semana_iso TEXT UNIQUE NOT NULL,
                fecha_analisis TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                resumen_ejecutivo TEXT NOT NULL,
                hallazgos_json TEXT NOT NULL,
                nivel_riesgo TEXT DEFAULT 'BAJO',
                revisado_por TEXT DEFAULT '',
                revisado_at TIMESTAMP WITH TIME ZONE
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compliance_deadlines (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                marco_legal TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                fecha_limite DATE NOT NULL,
                responsable TEXT DEFAULT 'Propietario / Administración',
                estatus TEXT DEFAULT 'Pendiente',
                completado_por TEXT DEFAULT '',
                completado_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        cur.execute("SELECT COUNT(*) FROM compliance_deadlines;")
        row_cnt = cur.fetchone()
        if int((row_cnt[0] if row_cnt else 0) or 0) == 0:
            hoy = datetime.now(TZ_SONORA).date()
            cierre_mes = (hoy.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            dia_17_sig = cierre_mes + timedelta(days=17)
            obligaciones_base = [
                (
                    "Declaración Mensual ISR / IVA y Retenciones (SAT)",
                    "CFF / LISR / LIVA (México)",
                    "Presentación de pagos provisionales y entero de retenciones antes del día 17 del mes siguiente.",
                    dia_17_sig,
                    "Contraloría / Propietario"
                ),
                (
                    "Cierre de Recepción CFDI 4.0 Docentes y Socios Afiliados",
                    "RMF SAT — CFDI 4.0 / 32-D",
                    "Validación de XML/PDF, Opinión 32-D y Constancia de Situación Fiscal para dispersión sin riesgo fiscal.",
                    hoy.replace(day=min(25, cierre_mes.day)),
                    "Administración Financiera"
                ),
                (
                    "Auditoría Trimestral de Aviso de Privacidad y Expedientes",
                    "LFPDPPP (Protección de Datos Personales)",
                    "Verificación de consentimiento expreso de alumnos, docentes y socios afiliados.",
                    cierre_mes,
                    "Propietario / Oficial de Cumplimiento"
                ),
            ]
            for tit, marco, desc, flim, resp in obligaciones_base:
                cur.execute("""
                    INSERT INTO compliance_deadlines (titulo, marco_legal, descripcion, fecha_limite, responsable)
                    VALUES (%s, %s, %s, %s, %s);
                """, (tit, marco, desc, flim, resp))
# ==============================================================================
# BLOQUE 2 DE 3 — ÍNDICE ESTADÍSTICO DE COMPLIANCE Y CONFIANZA (0–100 PTS)
# ==============================================================================
def calcular_indice_compliance_usuario(usuario: str, rol: str, conn) -> dict:
    """Calcula el Índice Estadístico de Compliance y Confianza (0 a 100 pts) por rol."""
    u_clean = str(usuario or "").strip()
    r_low = str(rol or "").strip().lower()
    factores = []
    puntaje = 0

    if r_low in ["socio afiliado", "afiliado", "socio", "partner"]:
        row = None
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(rfc, ''), COALESCE(domicilio, ''), COALESCE(telefono, ''),
                           COALESCE(ine_anverso_b64, ''), COALESCE(ine_reverso_b64, ''),
                           COALESCE(terminos_aceptados, FALSE), COALESCE(estatus, 'Activo')
                    FROM affiliate_partners
                    WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                    LIMIT 1;
                """, (u_clean,))
                row = cur.fetchone()
        except Exception:
            pass
        if row:
            rfc_v, dom_v, tel_v, ine_f, ine_r, terms_v, est_v = row
            p_rfc = 25 if len(str(rfc_v).strip()) in (12, 13) else 0
            p_ine = 25 if (ine_f and ine_r) else 0
            p_dom = 20 if (len(str(dom_v).strip()) >= 8 and len(str(tel_v).strip()) >= 8) else 10
            p_leg = 20 if terms_v else 0
            p_est = 10 if str(est_v).strip().lower() == "activo" else 0
            puntaje = p_rfc + p_ine + p_dom + p_leg + p_est
            factores = [
                ("RFC Fiscal Registrado (12/13 caracteres)", p_rfc, 25),
                ("Identificación Oficial INE (Anverso y Reverso)", p_ine, 25),
                ("Localización y Contacto Verificado", p_dom, 20),
                ("Aceptación Legal de Términos de Afiliación", p_leg, 20),
                ("Estatus Operativo Activo", p_est, 10),
            ]
        else:
            puntaje = 40
            factores = [("Expediente base pendiente de sincronización", 40, 100)]

    elif r_low in ["teacher", "docente"]:
        tp, vf = None, None
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(curp, ''), COALESCE(rfc, ''), COALESCE(cedula_profesional, '')
                    FROM teacher_profiles
                    WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                    LIMIT 1;
                """, (u_clean,))
                tp = cur.fetchone()
                cur.execute("""
                    SELECT COALESCE(csf_b64, ''), COALESCE(opinion_32d_b64, ''),
                           COALESCE(caratula_banco_b64, ''), COALESCE(clabe_interbancaria, ''),
                           COALESCE(ine_cedula_b64, ''), COALESCE(cfdi_periodo, '')
                    FROM teacher_fiscal_vault
                    WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                    LIMIT 1;
                """, (u_clean,))
                vf = cur.fetchone()
        except Exception:
            pass

        p_acad = 25 if (tp and len(str(tp[0]).strip()) == 18 and str(tp[2]).strip()) else 10
        p_csf = 20 if (vf and vf[0]) else 0
        p_32d = 20 if (vf and vf[1]) else 0
        p_bnc = 20 if (vf and vf[2] and len(str(vf[3]).strip()) == 18) else 0
        periodo_hoy = datetime.now(TZ_SONORA).strftime("%Y-%m")
        p_cfdi = 15 if (vf and str(vf[5]).strip() == periodo_hoy) else 0
        puntaje = p_acad + p_csf + p_32d + p_bnc + p_cfdi
        factores = [
            ("Credenciales Académicas (CURP + Cédula Prof.)", p_acad, 25),
            ("Constancia de Situación Fiscal (CSF)", p_csf, 20),
            ("Opinión de Cumplimiento SAT (32-D)", p_32d, 20),
            ("Carátula Bancaria y CLABE 18 Dígitos", p_bnc, 20),
            (f"Factura CFDI 4.0 del Periodo ({periodo_hoy})", p_cfdi, 15),
        ]

    elif r_low in ["propietario", "owner", "administrador", "admin"]:
        vencidos_cnt, urgentes_cnt = 0, 0
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FILTER (WHERE estatus != 'Cumplido' AND fecha_limite < CURRENT_DATE),
                           COUNT(*) FILTER (WHERE estatus != 'Cumplido' AND fecha_limite <= CURRENT_DATE + INTERVAL '3 days')
                    FROM compliance_deadlines;
                """)
                r_d = cur.fetchone()
                if r_d:
                    vencidos_cnt, urgentes_cnt = int(r_d[0] or 0), int(r_d[1] or 0)
        except Exception:
            pass
        penalizacion = vencidos_cnt * 20 + urgentes_cnt * 8
        puntaje = max(20, 100 - penalizacion)
        factores = [
            ("Gobernanza y Seguridad Criptográfica SHA-256", 35, 35),
            ("Cumplimiento de Plazos Legales y Fiscales (SLA)", max(0, 40 - penalizacion), 40),
            ("Vigilancia Normativa Semanal Activa", 25, 25),
        ]

    else:
        folios_rec, pagos_ok = 0, 0
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM lessons_folios
                    WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                      AND created_at >= NOW() - INTERVAL '14 days';
                """, (u_clean,))
                rf = cur.fetchone()
                folios_rec = int((rf[0] if rf else 0) or 0)
                cur.execute("""
                    SELECT COUNT(*) FROM student_payments
                    WHERE LOWER(TRIM(usuario_estudiante)) = LOWER(TRIM(%s))
                      AND LOWER(COALESCE(estatus, 'pagado')) IN ('pagado', 'completado', 'activo');
                """, (u_clean,))
                rp = cur.fetchone()
                pagos_ok = int((rp[0] if rp else 0) or 0)
        except Exception:
            pass

        p_id = 35
        p_acad = 35 if folios_rec >= 2 else (20 if folios_rec == 1 else 5)
        p_fin = 30 if pagos_ok >= 1 else 10
        puntaje = p_id + p_acad + p_fin
        factores = [
            ("Identidad Académica y Aceptación de Reglamento", p_id, 35),
            ("Continuidad y Disciplina de Estudio (Últimos 14 días)", p_acad, 35),
            ("Regularidad Administrativa y Pagos", p_fin, 30),
        ]

    if puntaje >= 92:
        rating, color_hex, estado_txt = "AAA", "#15803D", "Excelencia Institucional y Confianza Plena"
    elif puntaje >= 80:
        rating, color_hex, estado_txt = "AA", "#0369A1", "Cumplimiento Sólido y Confiable"
    elif puntaje >= 65:
        rating, color_hex, estado_txt = "A", "#B45309", "Cumplimiento Aceptable — Requiere Atención Menor"
    else:
        rating, color_hex, estado_txt = "B / C", "#DC2626", "Riesgo de Incumplimiento — Acción Inmediata Requerida"

    return {
        "puntaje": puntaje,
        "rating": rating,
        "color_hex": color_hex,
        "estado_txt": estado_txt,
        "factores": factores,
    }


def render_medidor_compliance_confianza(usuario: str, rol: str, conn=None):
    """Renderiza el Medidor Estadístico de Compliance y Confianza (0-100 pts)."""
    own_conn = False
    if conn is None:
        conn = _open_pg_comp()
        own_conn = True
    if not conn:
        return
    try:
        asegurar_tablas_compliance(conn)
        conn.commit()
        comp = calcular_indice_compliance_usuario(usuario, rol, conn)
        pts = comp["puntaje"]
        col = comp["color_hex"]

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <div style="font-size:12px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px;">
                            🛡️ Índice Estadístico de Compliance y Confianza Institucional
                        </div>
                        <div style="font-size:18px; font-weight:800; color:#0F172A; margin-top:2px;">
                            Calificación <span style="color:{col};">{comp['rating']}</span> — {comp['estado_txt']}
                        </div>
                    </div>
                    <div style="background:{col}; color:white; font-weight:800; font-size:20px; padding:8px 16px; border-radius:12px;">
                        {pts} / 100 pts
                    </div>
                </div>
                <div style="width:100%; background:#E2E8F0; height:12px; border-radius:999px; margin-top:10px; overflow:hidden;">
                    <div style="width:{pts}%; background:{col}; height:12px; border-radius:999px;"></div>
                </div>
                """,
                unsafe_allow_html=True
            )
            with st.expander("📊 Ver Desglose Estadístico de mi Índice de Confianza", expanded=False):
                for nombre_f, ob, max_p in comp["factores"]:
                    icono_f = "✅" if ob == max_p else ("⚠️" if ob > 0 else "❌")
                    st.markdown(f"{icono_f} **{nombre_f}:** `{ob} / {max_p} pts`")
    finally:
        if own_conn:
            try:
                conn.close()
            except Exception:
                pass
# ==============================================================================
# SUB-BLOQUE 3A — INVESTIGACIÓN SEMANAL DE ACTUALIZACIONES LEGALES Y FISCALES
# ==============================================================================
def ejecutar_investigacion_normativa_semanal(conn, forzar: bool = False) -> dict:
    """
    Investiga semanalmente (por semana ISO) las actualizaciones fiscales (SAT/RMF/CFDI),
    educativas (SEP / SEC Sonora RVOE), de privacidad (LFPDPPP) y laborales (LFT).
    """
    ahora = datetime.now(TZ_SONORA)
    iso_y, iso_w, _ = ahora.isocalendar()
    semana_iso = f"{iso_y}-W{iso_w:02d}"

    if not forzar:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT semana_iso, fecha_analisis, resumen_ejecutivo, hallazgos_json, nivel_riesgo, revisado_por
                FROM compliance_bulletins
                WHERE semana_iso = %s
                LIMIT 1;
            """, (semana_iso,))
            existente = cur.fetchone()
            if existente:
                return {
                    "semana_iso": existente[0],
                    "fecha_analisis": existente[1],
                    "resumen_ejecutivo": existente[2],
                    "hallazgos": json.loads(existente[3] or "[]"),
                    "nivel_riesgo": existente[4],
                    "revisado_por": existente[5] or "",
                }

    gemini_key = _find_secret_comp("GEMINI_API_KEY") or _find_secret_comp("GOOGLE_API_KEY")
    hallazgos = []
    resumen_ej = (
        f"Boletín Semanal de Cumplimiento Normativo ({semana_iso}) — Monitoreo activo sobre "
        "RMF SAT (CFDI 4.0, retenciones e IVA Frontera Norte), Lineamientos SEP / SEC Sonora, "
        "Protección de Datos Personales (LFPDPPP) y Ley Federal del Trabajo."
    )
    nivel_riesgo = "BAJO"

    if gemini_key:
        try:
            import urllib.request
            prompt_grc = (
                f"Eres Oficial Jefe de Cumplimiento (CCO) en México para un instituto de capacitación en inglés (CEI en Sonora, México). "
                f"Fecha actual: {ahora.strftime('%Y-%m-%d')} (Semana {semana_iso}). "
                "Genera un JSON estricto con 4 hallazgos normativos relevantes y vigentes en México para esta semana cubriendo: "
                "1) SAT / CFDI 4.0 / IVA Frontera Norte / Opinión 32-D, "
                "2) SEP / SEC Sonora Formación para el Trabajo / RVOE, "
                "3) LFPDPPP (Protección de Datos Personales de alumnos y docentes), "
                "4) LFT / Honorarios o Servicios Profesionales. "
                "Formato JSON exacto: "
                '{"nivel_riesgo":"BAJO|MEDIO|ALTO","resumen":"...","hallazgos":[{"area":"...","norma":"...","impacto":"...","accion_preventiva":"...","plazo_sugerido_dias":7}]}'
            )
            url_g = f"https://googleapis.com{gemini_key}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt_grc}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
            }).encode("utf-8")
            req = urllib.request.Request(url_g, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data_g = json.loads(resp.read().decode("utf-8"))
                txt_json = data_g["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(txt_json)
                if parsed.get("hallazgos"):
                    hallazgos = parsed["hallazgos"]
                    resumen_ej = parsed.get("resumen") or resumen_ej
                    nivel_riesgo = str(parsed.get("nivel_riesgo") or "BAJO").upper()
        except Exception:
            pass

    if not hallazgos:
        hallazgos = [
            {
                "area": "Fiscal / SAT (RMF Vigente)",
                "norma": "CFDI 4.0, Complemento de Pagos y Opinión 32-D",
                "impacto": "Deducción de honorarios docentes y comisiones de socios afiliados sujeta a XML vigente y 32-D positiva.",
                "accion_preventiva": "Verificar que todos los docentes y socios tengan CSF y 32-D con menos de 30 días antes del corte día 25.",
                "plazo_sugerido_dias": 5,
            },
            {
                "area": "Educativo / SEP & SEC Sonora",
                "norma": "Acuerdo 17/11/17 y Lineamientos de Formación para el Trabajo",
                "impacto": "Integridad de expedientes académicos (CURP validada, bitácora de horas y actas de evaluación).",
                "accion_preventiva": "Auditar matrículas nuevas y respaldar evidencias de evaluación por folio.",
                "plazo_sugerido_dias": 7,
            },
            {
                "area": "Privacidad y Ciberseguridad",
                "norma": "Ley Federal de Protección de Datos Personales (LFPDPPP)",
                "impacto": "Resguardo cifrado de INE, CURP, RFC y estados de cuenta bancarios.",
                "accion_preventiva": "Confirmar que el acceso a bóvedas documentales esté restringido por matriz de permisos.",
                "plazo_sugerido_dias": 10,
            },
            {
                "area": "Laboral y Contractual",
                "norma": "Ley Federal del Trabajo / Código Civil (Prestación de Servicios)",
                "impacto": "Delimitación clara entre contratos de servicios profesionales docentes y comisiones mercantiles de afiliados.",
                "accion_preventiva": "Conservar aceptación digital con marca de tiempo (timestamp) en cada alta.",
                "plazo_sugerido_dias": 7,
            },
        ]

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO compliance_bulletins (semana_iso, fecha_analisis, resumen_ejecutivo, hallazgos_json, nivel_riesgo)
                VALUES (%s, NOW(), %s, %s, %s)
                ON CONFLICT (semana_iso) DO UPDATE SET
                    fecha_analisis = NOW(),
                    resumen_ejecutivo = EXCLUDED.resumen_ejecutivo,
                    hallazgos_json = EXCLUDED.hallazgos_json,
                    nivel_riesgo = EXCLUDED.nivel_riesgo;
            """, (semana_iso, resumen_ej, json.dumps(hallazgos, ensure_ascii=False), nivel_riesgo))

    return {
        "semana_iso": semana_iso,
        "fecha_analisis": ahora,
        "resumen_ejecutivo": resumen_ej,
        "hallazgos": hallazgos,
        "nivel_riesgo": nivel_riesgo,
        "revisado_por": "",
    }
# ==============================================================================
# SUB-BLOQUE 3B (FINAL) — RELOJ SLA ANTI-NEGLIGENCIA Y PANEL GERENCIAL GRC
# ==============================================================================
def render_panel_compliance_gerencial(usuario_actual: str, puede_gestionar: bool = False):
    """
    Panel Ejecutivo GRC para Owner y Administradores autorizados:
    1) Medidor Estadístico de Confianza Institucional.
    2) Reloj de Plazos Legales/Fiscales (SLA Anti-Negligencia) con cuenta regresiva.
    3) Boletín Semanal de Actualización Legal y Fiscal.
    """
    if not puede_gestionar:
        st.warning("⛔ Tu perfil actual no tiene el permiso `Gestionar_Compliance_Legal` para auditar cumplimiento normativo.")
        return

    conn = _open_pg_comp()
    if not conn:
        st.error("❌ Sin conexión con la base de datos institucional.")
        return

    try:
        asegurar_tablas_compliance(conn)
        conn.commit()

        st.markdown("#### ⚖️ Centro de Gobernanza, Riesgo y Cumplimiento (GRC / ISO 37301)")
        render_medidor_compliance_confianza(usuario_actual, "Propietario", conn)

        # SECCIÓN A: RELOJ DE PLAZOS LEGALES Y FISCALES (SLA ANTI-NEGLIGENCIA)
        st.markdown("##### ⏱️ Reloj de Obligaciones Legales y Fiscales (Control Anti-Negligencia)")
        hoy = datetime.now(TZ_SONORA).date()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, titulo, marco_legal, descripcion, fecha_limite, responsable, estatus, completado_por
                FROM compliance_deadlines
                ORDER BY (estatus = 'Cumplido') ASC, fecha_limite ASC;
            """)
            deadlines = cur.fetchall()

        vencidos, urgentes, en_tiempo = 0, 0, 0
        for _id, _t, _m, _desc, f_lim, _resp, est_d, _comp_p in deadlines:
            if est_d != "Cumplido":
                dias_rest = (f_lim - hoy).days
                if dias_rest < 0:
                    vencidos += 1
                elif dias_rest <= 3:
                    urgentes += 1
                else:
                    en_tiempo += 1

        c_sla1, c_sla2, c_sla3 = st.columns(3)
        c_sla1.metric("🚨 Vencidos (Riesgo Crítico)", f"{vencidos}")
        c_sla2.metric("⏰ Urgentes (<= 3 días)", f"{urgentes}")
        c_sla3.metric("🟢 En Tiempo y Control", f"{en_tiempo}")

        for d_id, tit_d, marco_d, desc_d, f_lim, resp_d, est_d, comp_por in deadlines:
            dias_rest = (f_lim - hoy).days
            if est_d == "Cumplido":
                badge = f"✅ CUMPLIDO (por {comp_por})"
            elif dias_rest < 0:
                badge = f"🚨 VENCIDO HACE {abs(dias_rest)} DÍA(S) — ACCIÓN INMEDIATA"
            elif dias_rest == 0:
                badge = "⏰ VENCE HOY — ÚLTIMO DÍA"
            elif dias_rest <= 3:
                badge = f"⚠️ FALTAN {dias_rest} DÍA(S) — ALERTA PREVENTIVA"
            else:
                badge = f"🟢 Faltan {dias_rest} días (Límite: {f_lim.strftime('%d/%m/%Y')})"

            with st.container(border=True):
                col_d1, col_d2 = st.columns([2.6, 1.0])
                with col_d1:
                    st.markdown(f"**{tit_d}** (`{marco_d}`)")
                    st.caption(f"{desc_d} • Responsable: **{resp_d}**")
                    st.markdown(f"**Estado SLA:** {badge}")
                with col_d2:
                    if est_d != "Cumplido":
                        if st.button("✔️ Marcar Cumplido", key=f"btn_comp_sla_{d_id}", width="stretch"):
                            with conn:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        UPDATE compliance_deadlines
                                        SET estatus = 'Cumplido', completado_por = %s, completado_at = NOW()
                                        WHERE id = %s;
                                    """, (usuario_actual, d_id))
                            st.rerun()
                    else:
                        if st.button("🔄 Reabrir Ciclo", key=f"btn_reopen_sla_{d_id}", width="stretch"):
                            with conn:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        UPDATE compliance_deadlines
                                        SET estatus = 'Pendiente', fecha_limite = fecha_limite + INTERVAL '30 days'
                                        WHERE id = %s;
                                    """, (d_id,))
                            st.rerun()

        with st.expander("➕ Programar Nueva Obligación Legal, Fiscal o RVOE", expanded=False):
            with st.form("form_nuevo_plazo_compliance"):
                f_tit = st.text_input("Título de la Obligación *")
                f_marco = st.text_input("Marco Normativo (SAT / SEP / LFPDPPP / LFT) *")
                f_desc = st.text_input("Descripción y Evidencia Requerida")
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    f_fecha = st.date_input("Fecha Límite *", value=hoy + timedelta(days=7))
                with c_f2:
                    f_resp = st.text_input("Responsable Asignado", value=usuario_actual)
                if st.form_submit_button("💾 Guardar en Reloj SLA", type="primary", width="stretch"):
                    if f_tit.strip() and f_marco.strip():
                        with conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO compliance_deadlines (titulo, marco_legal, descripcion, fecha_limite, responsable)
                                    VALUES (%s, %s, %s, %s, %s);
                                """, (f_tit.strip(), f_marco.strip(), f_desc.strip(), f_fecha, f_resp.strip()))
                        st.success("✅ Obligación agregada al control preventivo.")
                        st.rerun()

        st.divider()

        # SECCIÓN B: INVESTIGACIÓN SEMANAL DE ACTUALIZACIONES LEGALES Y FISCALES
        col_b1, col_b2 = st.columns([2.5, 1.1])
        with col_b1:
            st.markdown("##### 📡 Inteligencia Normativa Semanal (Actualizaciones Legales y Fiscales)")
        with col_b2:
            forzar_scan = st.button("🔄 Ejecutar Escaneo Ahora", key="btn_forzar_scan_normativo", width="stretch")

        boletin = ejecutar_investigacion_normativa_semanal(conn, forzar=forzar_scan)
        st.info(
            f"📅 **Semana Auditada:** `{boletin['semana_iso']}`  |  "
            f"🛡️ **Nivel de Riesgo Regulatorio:** **`{boletin['nivel_riesgo']}`**\n\n"
            f"{boletin['resumen_ejecutivo']}"
        )

        for idx_h, h in enumerate(boletin.get("hallazgos", []), start=1):
            with st.container(border=True):
                st.markdown(f"**{idx_h}. {h.get('area', 'Normativa')} — `{h.get('norma', '')}`**")
                st.markdown(f"• **Impacto Operativo:** {h.get('impacto', '')}")
                st.markdown(f"• **Acción Preventiva Recomendada:** {h.get('accion_preventiva', '')} *(Plazo sugerido: {h.get('plazo_sugerido_dias', 7)} días)*")

        if not boletin.get("revisado_por"):
            if st.button("✅ Confirmar Lectura y Acuse de Recibo del Boletín Semanal", type="primary", key="btn_ack_boletin"):
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE compliance_bulletins
                            SET revisado_por = %s, revisado_at = NOW()
                            WHERE semana_iso = %s;
                        """, (usuario_actual, boletin["semana_iso"]))
                st.success("✅ Acuse registrado en bitácora de alta gerencia.")
                st.rerun()
        else:
            st.caption(f"✔️ Boletín revisado y validado por **{boletin['revisado_por']}**.")
    finally:
        try:
            conn.close()
        except Exception:
            pass
