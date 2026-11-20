# ==============================================================================
# Inscripcion_alumnosCEI.py — PARTE 1 DE 2: CONEXIÓN Y CABECERA INSTITUCIONAL
# ==============================================================================
from datetime import date, datetime
import os
from zoneinfo import ZoneInfo
import psycopg
import streamlit as st

st.set_page_config(
    page_title="Inscripción Oficial — Career English Institute (CEI)",
    page_icon="🎓",
    layout="centered"
)

GRADOS_ACADEMICOS_INS = [
    "Preescolar",
    "Primaria",
    "Secundaria",
    "Preparatoria / Bachillerato",
    "Licenciatura / Universidad",
    "Maestría / Posgrado",
    "Doctorado / Investigación"
]

NIVELES_CEFR_INS = [
    "A1 (Beginner)",
    "A2 (Elementary)",
    "B1 (Intermediate)",
    "B2 (Upper-Intermediate)",
    "C1 (Advanced)",
    "C2 (Proficiency)"
]


def _find_secret_ins(key_name: str) -> str:
    if key_name in st.secrets:
        return str(st.secrets[key_name]).strip()
    key_low = key_name.lower()
    for k, v in st.secrets.items():
        if str(k).lower() == key_low and not isinstance(v, dict):
            return str(v).strip()
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                if str(sub_k).lower() == key_low:
                    return str(sub_v).strip()
    return ""


def _get_conn_ins():
    pg_host = _find_secret_ins("PG_HOST") or _find_secret_ins("DB_HOST") or _find_secret_ins("HOST")
    pg_user = _find_secret_ins("PG_USER") or _find_secret_ins("DB_USER") or _find_secret_ins("USER")
    pg_pass = _find_secret_ins("PG_PASSWORD") or _find_secret_ins("DB_PASSWORD") or _find_secret_ins("PASSWORD")
    pg_port = int(_find_secret_ins("PG_PORT") or _find_secret_ins("DB_PORT") or 6543)
    pg_db = _find_secret_ins("PG_DBNAME") or _find_secret_ins("DB_NAME") or "postgres"

    if pg_host and pg_user and pg_pass:
        return psycopg.connect(
            host=pg_host, port=pg_port, dbname=pg_db,
            user=pg_user, password=pg_pass, sslmode="require",
            connect_timeout=10, prepare_threshold=None
        )
    db_url = _find_secret_ins("SUPABASE_DB_URL") or _find_secret_ins("DATABASE_URL")
    if db_url and db_url.startswith("postgres"):
        if "sslmode=" not in db_url:
            db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
        return psycopg.connect(db_url, connect_timeout=10, prepare_threshold=None)
    return None


def _buscar_nombre_afiliado(ref_code: str) -> tuple[str, str]:
    """Devuelve (usuario_login, nombre_completo) del Socio Afiliado que invitó al alumno."""
    code = str(ref_code or "").strip()
    if not code:
        return "", ""
    conn = _get_conn_ins()
    if not conn:
        return code, code
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT usuario_login, COALESCE(nombre || ' ' || apellido_paterno, usuario_login)
                FROM affiliate_partners
                WHERE LOWER(TRIM(affiliate_id)) = LOWER(TRIM(%s))
                   OR LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (code, code))
            row = cur.fetchone()
            if row:
                return str(row).strip(), str(row).strip()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return code, code


col_l, col_t = st.columns([0.9, 3.5])
with col_l:
    if os.path.exists("LOGO CEI APP.png"):
        st.image("LOGO CEI APP.png", width=95)
    else:
        st.markdown("## 🎓")
with col_t:
    st.markdown("### 🏛️ CAREER ENGLISH INSTITUTE (CEI)")
    st.title("📝 Solicitud Oficial de Inscripción")
    st.caption("Agua Prieta, Sonora, México  |  Marco Común Europeo de Referencia (CEFR A1 – C2)")

ref_param = str(st.query_params.get("ref_aff") or st.query_params.get("ref") or "").strip()
aff_user_vinculado, aff_nombre_mostrado = _buscar_nombre_afiliado(ref_param)

if aff_user_vinculado:
    st.success(f"🤝 **Inscripción Referida por Socio Afiliado:** {aff_nombre_mostrado} (`{ref_param}`)")
# ==============================================================================
# Inscripcion_alumnosCEI.py — PARTE 2 DE 2: FORMULARIO Y REGISTRO EN SUPABASE
# ==============================================================================
if st.session_state.get("ins_alumno_ok"):
    st.balloons()
    st.success(f"🎉 **¡Bienvenido(a) a Career English Institute, {st.session_state.get('ins_alumno_nom', '')}!**")
    st.info(
        f"• **🆔 Matrícula Oficial Asignada:** `{st.session_state.get('ins_alumno_mat', '')}`\n"
        f"• **👤 Usuario de Acceso:** `{st.session_state.get('ins_alumno_usr', '')}`\n"
        "• **📌 Siguiente Paso:** Conserva tu matrícula para incluirla como referencia en tu pago de inscripción y mensualidades."
    )
    if st.button("➕ Registrar Otro Estudiante", type="secondary"):
        st.session_state["ins_alumno_ok"] = False
        st.rerun()
    st.stop()

with st.form("form_inscripcion_alumnos_cei", clear_on_submit=False):
    st.markdown("#### 1️⃣ Datos Personales del Estudiante")
    c1, c2 = st.columns(2)
    with c1:
        nom_al = st.text_input("Nombre(s) *", placeholder="Ej. Sofía")
        pat_al = st.text_input("Apellido Paterno *", placeholder="Ej. Ramírez")
        mat_al = st.text_input("Apellido Materno", placeholder="Ej. López")
        fec_nac = st.date_input("Fecha de Nacimiento *", value=date(2005, 1, 1), min_value=date(1940, 1, 1), max_value=date.today())
    with c2:
        tel_al = st.text_input("Teléfono / WhatsApp *", placeholder="Ej. 633-123-4567")
        mail_al = st.text_input("Correo Electrónico *", placeholder="estudiante@correo.com")
        tutor_al = st.text_input("Nombre del Padre o Tutor (si es menor de edad)", placeholder="Opcional para mayores de 18 años")
        dom_al = st.text_input("Ciudad / Domicilio *", placeholder="Agua Prieta, Sonora")

    st.divider()
    st.markdown("#### 2️⃣ Datos Académicos y Acceso a la Plataforma IA")
    ca1, ca2 = st.columns(2)
    with ca1:
        grado_al = st.selectbox("Grado Académico Actual *", GRADOS_ACADEMICOS_INS, index=4)
        nivel_al = st.selectbox("Nivel de Inglés Estimado (CEFR) *", NIVELES_CEFR_INS, index=0)
        modalidad_al = st.selectbox("Modalidad de Estudio *", ["Presencial (Agua Prieta)", "En Línea / Híbrido (Zoom + Plataforma IA)"])
    with ca2:
        usr_al = st.text_input("Usuario Deseado para Plataforma *", placeholder="Ej. Sofia Ramirez")
        pwd_al = st.text_input("Crea tu Contraseña de Acceso *", type="password", placeholder="Mínimo 6 caracteres")
        ref_manual = st.text_input(
            "Código o Usuario de Socio Afiliado (si alguien te invitó):",
            value=aff_user_vinculado,
            disabled=bool(aff_user_vinculado)
        )

    acepta_reg = st.checkbox("✅ Confirmo que mis datos son verídicos y acepto el Reglamento Académico de Career English Institute (CEI) *")
    enviar_ins = st.form_submit_button("🎓 Completar Inscripción Oficial", type="primary", width="stretch")

    if enviar_ins:
        if not nom_al.strip() or not pat_al.strip() or not tel_al.strip() or not usr_al.strip() or not pwd_al.strip():
            st.error("⚠️ Por favor completa Nombre, Apellido Paterno, Teléfono, Usuario y Contraseña.")
        elif len(pwd_al.strip()) < 6:
            st.error("⚠️ La contraseña debe tener al menos 6 caracteres.")
        elif not acepta_reg:
            st.error("⚠️ Debes confirmar y aceptar el Reglamento Académico para completar tu inscripción.")
        else:
            conn = _get_conn_ins()
            if not conn:
                st.error("❌ No fue posible conectar con el servidor académico. Intenta nuevamente en unos momentos.")
            else:
                try:
                    anio_act = datetime.now(ZoneInfo("America/Hermosillo")).year
                    hoy_str = datetime.now(ZoneInfo("America/Hermosillo")).strftime("%Y-%m-%d")
                    u_final = usr_al.strip()
                    n_completo = f"{nom_al.strip()} {pat_al.strip()} {mat_al.strip()}".strip()
                    aff_final = (aff_user_vinculado or ref_manual).strip()
                    nivel_code = next(iter(nivel_al.split()), "A1")

                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                CREATE TABLE IF NOT EXISTS inscripciones_web_cei (
                                    id SERIAL PRIMARY KEY,
                                    matricula TEXT,
                                    usuario TEXT UNIQUE,
                                    nombre_completo TEXT,
                                    fecha_nacimiento DATE,
                                    telefono TEXT,
                                    email TEXT,
                                    tutor TEXT,
                                    domicilio TEXT,
                                    grado_academico TEXT,
                                    nivel_cefr TEXT,
                                    modalidad TEXT,
                                    socio_afiliado TEXT,
                                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                                );
                            """)
                            cur.execute("""
                                INSERT INTO users_padron (
                                    usuario, clave_hash, rol, permisos, nivel, grado_academico,
                                    estatus, fecha_inscripcion, fecha_inicio_curso, socio_afiliado
                                ) VALUES (%s, %s, 'Estudiante', 'Basico', %s, %s, 'Activo', %s, %s, %s)
                                ON CONFLICT (usuario) DO UPDATE SET
                                    nivel = EXCLUDED.nivel,
                                    grado_academico = EXCLUDED.grado_academico,
                                    socio_afiliado = COALESCE(NULLIF(EXCLUDED.socio_afiliado, ''), users_padron.socio_afiliado)
                                RETURNING id, matricula;
                            """, (u_final, pwd_al.strip(), nivel_code, grado_al, hoy_str, hoy_str, aff_final))
                            r_pad = cur.fetchone()
                            mat_oficial = str(r_pad or "")
                            if r_pad and not mat_oficial:
                                mat_oficial = f"CEI-{anio_act}-{int(r_pad):04d}"
                                cur.execute("UPDATE users_padron SET matricula = %s WHERE id = %s;", (mat_oficial, r_pad))

                            cur.execute("""
                                INSERT INTO inscripciones_web_cei (
                                    matricula, usuario, nombre_completo, fecha_nacimiento,
                                    telefono, email, tutor, domicilio, grado_academico,
                                    nivel_cefr, modalidad, socio_afiliado
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (usuario) DO UPDATE SET
                                    matricula = EXCLUDED.matricula,
                                    nombre_completo = EXCLUDED.nombre_completo,
                                    telefono = EXCLUDED.telefono,
                                    email = EXCLUDED.email,
                                    socio_afiliado = EXCLUDED.socio_afiliado;
                            """, (
                                mat_oficial, u_final, n_completo, fec_nac,
                                tel_al.strip(), mail_al.strip(), tutor_al.strip(), dom_al.strip(),
                                grado_al, nivel_code, modalidad_al, aff_final
                            ))

                    st.session_state["ins_alumno_ok"] = True
                    st.session_state["ins_alumno_nom"] = n_completo
                    st.session_state["ins_alumno_mat"] = mat_oficial
                    st.session_state["ins_alumno_usr"] = u_final
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar inscripción: {e}")
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass

