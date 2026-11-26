import base64
from datetime import date
import random
import psycopg
import streamlit as st


def _find_secret_doc(key_name: str) -> str:
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


def _open_pg_doc():
    pg_host = _find_secret_doc("PG_HOST") or _find_secret_doc("DB_HOST")
    pg_user = _find_secret_doc("PG_USER") or _find_secret_doc("DB_USER")
    pg_pass = _find_secret_doc("PG_PASSWORD") or _find_secret_doc("DB_PASSWORD")
    pg_port = int(_find_secret_doc("PG_PORT") or _find_secret_doc("DB_PORT") or 6543)
    pg_db = _find_secret_doc("PG_DBNAME") or _find_secret_doc("DB_NAME") or "postgres"
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


def render_formulario_registro_docente(
    registrado_por: str = "Administración",
    key_prefix: str = "doc_reg",
    es_registro_externo: bool = False
):
    """Formulario Oficial de Alta y Certificación de Docentes CEI / SEP."""
    st.markdown("#### 🧑‍🏫 Registro Oficial de Plantilla Docente (CEI / RVOE)")
    st.caption(
        "Registra el expediente académico, fiscal y credencialización del profesor. "
        "Se creará automáticamente su cuenta con acceso a **Mi Portal Docente CEI**."
    )

    anio_act = date.today().year
    id_doc_sug = f"DOC-CEI-{anio_act}-{random.randint(100, 999)}"

    try:
        from legal_terms_manager import get_institutional_terms_pg, render_documento_apa7
        terms_doc_txt = get_institutional_terms_pg("docente").get("texto", "")
    except Exception:
        render_documento_apa7 = None
        terms_doc_txt = (
            "### Términos, Condiciones y Código de Compliance Docente\n\n"
            "**Career English Institute (CEI) — Agua Prieta, Sonora, México**\n\n"
            "El Docente declara la veracidad de sus credenciales académicas, se obliga a mantener actualizada "
            "su documentación fiscal (CSF, Opinión 32-D y CFDI 4.0) para cobro de honorarios/comisiones "
            "y acepta el monitoreo del Índice Estadístico de Compliance y Confianza de CEI."
        )

    with st.form(f"{key_prefix}_form_doc", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            doc_id = st.text_input("🆔 ID Docente Oficial *", value=id_doc_sug, disabled=es_registro_externo)
            usuario_doc = st.text_input("👤 Usuario de Acceso *", placeholder="Ej. Prof. Laura Gómez")
            nombre = st.text_input("Nombre(s) *", placeholder="Ej. Laura Elena")
            ap_pat = st.text_input("Apellido Paterno *", placeholder="Ej. Gómez")
            ap_mat = st.text_input("Apellido Materno", placeholder="Ej. Morales")
            curp = st.text_input("🪪 CURP (18 caracteres) *", max_chars=18, placeholder="Ej. GOML880512MSRRZ01")
            rfc = st.text_input("🧾 RFC (12 o 13 caracteres) *", max_chars=13, placeholder="Ej. GOML880512ABC")
        with c2:
            telefono = st.text_input("📱 Teléfono / WhatsApp *", placeholder="Ej. 633-123-4567")
            email = st.text_input("✉️ Correo Electrónico *", placeholder="docente@cei.edu.mx")
            clave_doc = st.text_input("🔑 Contraseña Inicial *", type="password", placeholder="Mínimo 6 caracteres")
            grado_acad = st.selectbox(
                "🎓 Grado Académico Máximo *",
                [
                    "Licenciatura en Enseñanza del Inglés",
                    "Licenciatura (Otra Área)",
                    "Maestría en Educación / TESOL",
                    "Doctorado",
                    "Normal Superior"
                ]
            )
            cedula_prof = st.text_input("📜 Número de Cédula Profesional *", placeholder="Ej. 12345678")
            cert_ingles = st.selectbox(
                "🌍 Certificación Internacional de Idioma *",
                [
                    "CENNI Nivel 14-20 (C1/C2)",
                    "Cambridge C1 Advanced / C2 Proficiency",
                    "CELTA / DELTA / TKT",
                    "TOEFL iBT (95+ pts)",
                    "IELTS Academic (7.0+)",
                    "En Trámite / Validación Interna"
                ]
            )
            niveles_auth = st.multiselect(
                "📚 Niveles CEFR Autorizados *",
                ["A1", "A2", "B1", "B2", "C1", "C2"],
                default=["A1", "A2", "B1", "B2"]
            )

        c3, c4 = st.columns(2)
        with c3:
            clabe_doc = st.text_input("🏦 CLABE Interbancaria (18 dígitos — Opcional)", max_chars=18, placeholder="012345678901234567")
        with c4:
            if es_registro_externo:
                pct_com_doc = 0.0
                st.info("💼 **Comisión / Honorario Base (%):** Será asignado por Dirección.")
            else:
                pct_com_doc = st.number_input("💼 Comisión / Honorario Docente (%) *", min_value=0.0, max_value=100.0, value=15.0, step=1.0)

        disponibilidad = st.text_input("🗓️ Disponibilidad Horaria y Modalidad", placeholder="Ej. Lunes a Viernes 16:00 - 21:00 hrs")
        titulo_file = st.file_uploader("📎 Título, Cédula o Certificado (PDF/PNG/JPG - Opcional)", type=["pdf", "png", "jpg", "jpeg"], key=f"{key_prefix}_doc_file")

        st.markdown("##### 📜 Términos, Condiciones y Código de Compliance Docente")
        if render_documento_apa7:
            render_documento_apa7(terms_doc_txt, max_height_px=360)
        else:
            st.markdown(terms_doc_txt)

        acepta_codigo = st.checkbox(
            "✅ He leído y acepto los Términos, Condiciones, Requisitos Fiscales (CFDI/32-D) y Código de Compliance Docente de CEI *",
            key=f"{key_prefix}_chk_doc"
        )
        submit_doc = st.form_submit_button("💾 Registrar Docente y Activar Portal", type="primary", width="stretch")
        if submit_doc:
            if not usuario_doc.strip() or not nombre.strip() or not ap_pat.strip() or not clave_doc.strip():
                st.error("⚠️ Completa Usuario, Nombre, Apellido Paterno y Contraseña.")
                return
            curp_clean = curp.strip().upper()
            if len(curp_clean) != 18 or not curp_clean.isalnum():
                st.error("⚠️ La CURP debe contener exactamente 18 caracteres alfanuméricos.")
                return
            rfc_clean = rfc.strip().upper()
            if len(rfc_clean) not in (12, 13) or not rfc_clean.isalnum():
                st.error("⚠️ Ingresa un RFC válido de 12 o 13 caracteres alfanuméricos.")
                return
            clabe_clean = "".join(ch for ch in clabe_doc if ch.isdigit())
            if clabe_clean and len(clabe_clean) != 18:
                st.error("⚠️ Si capturas la CLABE Interbancaria, debe tener exactamente 18 dígitos.")
                return
            if not acepta_codigo:
                st.error("⚠️ Debes aceptar los Términos, Condiciones y Código de Compliance Docente para continuar.")
                return

            doc_b64 = base64.b64encode(titulo_file.read()).decode("utf-8") if titulo_file else ""
            u_clean = usuario_doc.strip()
            id_clean = doc_id.strip().upper()
            niveles_str = ", ".join(niveles_auth) if niveles_auth else "A1, A2, B1"

            conn = _open_pg_doc()
            if not conn:
                st.error("❌ Sin conexión con la base de datos institucional.")
                return


            try:
                with conn:
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
                                terminos_aceptados BOOLEAN DEFAULT TRUE,
                                terminos_aceptados_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                estatus TEXT DEFAULT 'Activo',
                                registrado_por TEXT DEFAULT '',
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                        """)
                        cur.execute("""
                            ALTER TABLE teacher_profiles
                            ADD COLUMN IF NOT EXISTS porcentaje_comision NUMERIC(5,2) DEFAULT 0.0,
                            ADD COLUMN IF NOT EXISTS clabe_interbancaria TEXT DEFAULT '',
                            ADD COLUMN IF NOT EXISTS terminos_aceptados BOOLEAN DEFAULT TRUE,
                            ADD COLUMN IF NOT EXISTS terminos_aceptados_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                        """)
                        cur.execute("""
                            INSERT INTO teacher_profiles (
                                teacher_id, usuario_login, nombre, apellido_paterno, apellido_materno,
                                curp, rfc, cedula_profesional, grado_academico, certificacion_ingles,
                                niveles_autorizados, telefono, email, disponibilidad, documento_b64,
                                porcentaje_comision, clabe_interbancaria, terminos_aceptados, terminos_aceptados_at,
                                estatus, registrado_por
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), 'Activo', %s)
                            ON CONFLICT (usuario_login) DO UPDATE SET
                                teacher_id = EXCLUDED.teacher_id,
                                nombre = EXCLUDED.nombre,
                                apellido_paterno = EXCLUDED.apellido_paterno,
                                apellido_materno = EXCLUDED.apellido_materno,
                                curp = EXCLUDED.curp,
                                rfc = EXCLUDED.rfc,
                                cedula_profesional = EXCLUDED.cedula_profesional,
                                grado_academico = EXCLUDED.grado_academico,
                                certificacion_ingles = EXCLUDED.certificacion_ingles,
                                niveles_autorizados = EXCLUDED.niveles_autorizados,
                                telefono = EXCLUDED.telefono,
                                email = EXCLUDED.email,
                                disponibilidad = EXCLUDED.disponibilidad,
                                porcentaje_comision = CASE
                                    WHEN %s THEN teacher_profiles.porcentaje_comision
                                    ELSE EXCLUDED.porcentaje_comision
                                END,
                                clabe_interbancaria = COALESCE(NULLIF(EXCLUDED.clabe_interbancaria, ''), teacher_profiles.clabe_interbancaria),
                                terminos_aceptados = TRUE,
                                terminos_aceptados_at = COALESCE(teacher_profiles.terminos_aceptados_at, NOW());
                        """, (
                            id_clean, u_clean, nombre.strip(), ap_pat.strip(), ap_mat.strip(),
                            curp_clean, rfc_clean, cedula_prof.strip(),
                            grado_acad, cert_ingles, niveles_str,
                            telefono.strip(), email.strip(), disponibilidad.strip(),
                            doc_b64, float(pct_com_doc), clabe_clean, registrado_por,
                            es_registro_externo
                        ))

                        cur.execute("""
                            ALTER TABLE users_padron
                            ADD COLUMN IF NOT EXISTS telefono TEXT DEFAULT '',
                            ADD COLUMN IF NOT EXISTS docente_asignado TEXT DEFAULT '',
                            ADD COLUMN IF NOT EXISTS porcentaje_comision NUMERIC(5,2) DEFAULT 0.0,
                            ADD COLUMN IF NOT EXISTS terminos_aceptados BOOLEAN DEFAULT TRUE,
                            ADD COLUMN IF NOT EXISTS terminos_aceptados_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                        """)
                        cur.execute("""
                            INSERT INTO users_padron (
                                usuario, clave_hash, rol, permisos, estatus, telefono,
                                porcentaje_comision, terminos_aceptados, terminos_aceptados_at
                            )
                            VALUES (%s, %s, 'Teacher', 'Docente', 'Activo', %s, %s, TRUE, NOW())
                            ON CONFLICT (usuario) DO UPDATE SET
                                rol = 'Teacher',
                                permisos = 'Docente',
                                estatus = 'Activo',
                                telefono = EXCLUDED.telefono,
                                porcentaje_comision = CASE
                                    WHEN %s THEN users_padron.porcentaje_comision
                                    ELSE EXCLUDED.porcentaje_comision
                                END,
                                terminos_aceptados = TRUE,
                                terminos_aceptados_at = COALESCE(users_padron.terminos_aceptados_at, NOW());
                        """, (u_clean, clave_doc.strip(), telefono.strip(), float(pct_com_doc), es_registro_externo))

                st.cache_data.clear()
                st.success(f"🎉 **Docente {nombre.strip()} {ap_pat.strip()} (`{id_clean}`) registrado y habilitado en Mi Portal Docente CEI.**")
            except Exception as e_doc:
                st.error(f"Error al guardar expediente docente: {e_doc}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass


if __name__ == "__main__":
    st.set_page_config(
        page_title="Registro Oficial de Docentes — CEI",
        page_icon="🧑‍🏫",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    from ui_branding_cleaner import ocultar_badges_plataforma_cei
    ocultar_badges_plataforma_cei()

    render_formulario_registro_docente(
        registrado_por="Auto-Registro Docente",
        key_prefix="ext_doc_reg",
        es_registro_externo=True
    )



