# ==============================================================================
# Inscripcion_alumnosCEI.py — BLOQUE 1 DE 2: CONEXIÓN, AFILIADO Y TÉRMINOS CEI
# ==============================================================================
from datetime import date, datetime
import os
from zoneinfo import ZoneInfo
import psycopg
import streamlit as st
from ui_branding_cleaner import ocultar_badges_plataforma_cei

st.set_page_config(
    page_title="Inscripción Oficial — Career English Institute (CEI)",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)
ocultar_badges_plataforma_cei()

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

TERMINOS_INSCRIPCION_ALUMNOS_CEI = """TÉRMINOS, CONDICIONES Y REGLAMENTO ACADÉMICO DE INSCRIPCIÓN
CAREER ENGLISH INSTITUTE (CEI) — AGUA PRIETA, SONORA, MÉXICO

PRIMERA. NATURALEZA DEL SERVICIO (100% EN LÍNEA) Y MARCO LEGAL APLICABLE.
Los presentes Términos y Condiciones regulan la prestación de servicios educativos privados de enseñanza del idioma inglés en modalidad 100% en línea (clases en vivo por videoconferencia y plataforma educativa interactiva), impartidos por Career English Institute (CEI), con sede administrativa en Agua Prieta, Sonora, México, de conformidad con la legislación civil, educativa y de protección al consumidor vigente en los Estados Unidos Mexicanos y en el Estado de Sonora.

SEGUNDA. CALIBRACIÓN AL MARCO COMÚN EUROPEO (CEFR).
Los programas académicos de CEI son flexibles y ajustables al nivel real del estudiante conforme al Marco Común Europeo de Referencia para las Lenguas (CEFR: A1, A2, B1, B2, C1 y C2). Al formalizar su inscripción, la plataforma educativa y todas las lecciones, audios, evaluaciones y ejercicios generados en ella quedarán calibrados automáticamente al nivel CEFR indicado en este formulario, pudiendo ajustarse previa valoración académica.

TERCERA. DURACIÓN DEL PROGRAMA (9 PERIODOS) Y PERIODOS VACACIONALES ACTIVOS.
1. Estructura del Nivel: Cada nivel académico está estructurado en nueve (9) periodos mensuales de cuatro (4) semanas cada uno.
2. Periodos Vacacionales Activos (Verano e Invierno): Durante los recesos vacacionales largos de verano e invierno no se imparten clases en vivo en línea; sin embargo, la plataforma educativa permanecerá plenamente activa y disponible las 24 horas para que el estudiante continúe practicando y manteniendo su avance académico.
3. Conclusión del Nivel: Al finalizar satisfactoriamente los 9 periodos y acreditar la rúbrica correspondiente, el estudiante obtiene su constancia o certificado institucional del nivel cursado.

CUARTA. ASISTENCIA EN LÍNEA, INASISTENCIAS JUSTIFICADAS Y RECUPERACIÓN DE CLASES.
1. Asistencia del Estudiante y Asignación de Trabajo (Homework): El estudiante se compromete a conectarse puntualmente a sus clases en línea. En caso de requerir ausentarse por causa justificada, deberá avisar con anticipación a la institución o docente para recibir su asignación de trabajo (homework). La entrega y cumplimiento oportuno de dicha asignación será suficiente para dar la clase por dada o satisfecha.
2. Ausencia del Docente: En caso de que el docente deba ausentarse por causa justificada, se notificará con anticipación al estudiante y, por mutuo acuerdo entre ambas partes, se reprogramará y recuperará íntegramente la clase perdida sin costo adicional.

QUINTA. RÚBRICA DE EVALUACIÓN POR CRITERIOS Y ACCESO AL BOLETÍN.
1. Evaluación Integral: El estudiante deberá asegurarse de completar en tiempo y forma los criterios de la rúbrica de calificaciones acordes a su nivel (Reading & Quiz 30%, Viewing & Listening 25%, Alphabetical & Speaking 25% y Writing Skill APA 7 20%).
2. Puntualidad en Mensualidades y Boletín: El estudiante (o su padre/tutor) se compromete a mantenerse al corriente en el pago de sus mensualidades (dentro de la 4ta semana de cada bloque) e informarlo oportunamente en la plataforma para conservar activo su acceso al Boletín Informativo de Calificaciones y avances.

SEXTA. PROTECCIÓN DE DATOS PERSONALES Y JURISDICCIÓN.
De conformidad con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP), los datos recabados se utilizarán exclusivamente para fines académicos, administrativos y de certificación interna. Para cualquier controversia derivada de la interpretación o cumplimiento de este acuerdo, las partes se someten a las leyes vigentes y a los tribunales competentes de Agua Prieta, Sonora, México.

SÉPTIMA. COMPLIANCE INSTITUCIONAL, ÍNDICE DE CONFIANZA Y INTEGRIDAD DIGITAL.
El estudiante acepta que su continuidad académica, disciplina de estudio y regularidad administrativa alimentan el Índice Estadístico de Compliance y Confianza Institucional (0 a 100 puntos). Las credenciales de acceso son estrictamente personales e intransferibles; cualquier suplantación de identidad o alteración de folios o certificados protegidos mediante sello criptográfico HMAC-SHA256 será causal de baja definitiva."""


def get_terminos_inscripcion_estudiantes() -> str:
    """Obtiene los términos vigentes de inscripción desde PostgreSQL (o usa el texto base de 7 cláusulas)."""
    try:
        from legal_terms_manager import get_institutional_terms_pg
        txt_db = str(get_institutional_terms_pg("estudiante").get("texto") or "").strip()
        if txt_db and "PRIMERA." in txt_db:
            return txt_db
    except Exception:
        pass
    return TERMINOS_INSCRIPCION_ALUMNOS_CEI


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


def obtener_terminos_estudiantes_pg() -> str:
    """Lee desde Supabase PostgreSQL los Términos y Condiciones de Estudiantes vigentes (con cláusula de Compliance)."""
    conn = _get_conn_ins()
    if not conn:
        return TERMINOS_INSCRIPCION_ALUMNOS_CEI
    try:
        with conn:
            with conn.cursor() as cur:
                # 1) Verificar primero la tabla centralizada de gobernanza legal (institutional_legal_terms)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS institutional_legal_terms (
                        tipo_rol TEXT PRIMARY KEY,
                        texto TEXT NOT NULL,
                        updated_by TEXT DEFAULT 'Owner',
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                cur.execute("SELECT texto FROM institutional_legal_terms WHERE tipo_rol = 'estudiante' LIMIT 1;")
                row_inst = cur.fetchone()
                if row_inst and str(row_inst or "").strip() and "PRIMERA." in str(row_inst):
                    return str(row_inst).strip()

                # 2) Compatibilidad con tabla previa cei_configuracion_legal
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cei_configuracion_legal (
                        clave TEXT PRIMARY KEY,
                        contenido TEXT NOT NULL,
                        updated_by TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("SELECT contenido FROM cei_configuracion_legal WHERE clave = 'terminos_estudiantes' LIMIT 1;")
                row = cur.fetchone()
                if row and str(row or "").strip():
                    return str(row).strip()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return TERMINOS_INSCRIPCION_ALUMNOS_CEI


def _buscar_datos_afiliado(ref_code: str) -> tuple[str, str, str]:
    """Devuelve (affiliate_id, usuario_login, nombre_completo) del Socio Afiliado que invitó al alumno."""
    code = str(ref_code or "").strip()
    if not code:
        return "", "", ""
    conn = _get_conn_ins()
    if not conn:
        return code, code, code
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(affiliate_id, usuario_login),
                       usuario_login,
                       COALESCE(nombre || ' ' || apellido_paterno, usuario_login)
                FROM affiliate_partners
                WHERE LOWER(TRIM(affiliate_id)) = LOWER(TRIM(%s))
                   OR LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (code, code))
            row = cur.fetchone()
            if row:
                return str(row).strip(), str(row).strip(), str(row).strip()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return code, code, code


col_l, col_t = st.columns([0.9, 3.5])
with col_l:
    if os.path.exists("static/LOGO CEI APP.png"):
        st.image("static/LOGO CEI APP.png", width=95)
    elif os.path.exists("LOGO CEI APP.png"):
        st.image("LOGO CEI APP.png", width=95)
    else:
        st.markdown("## 🎓")
with col_t:
    st.markdown("### 🏛️ CAREER ENGLISH INSTITUTE (CEI)")
    st.title("📝 Solicitud Oficial de Inscripción")
    st.caption("Agua Prieta, Sonora, México  |  Modalidad 100% En Línea  |  Marco Común Europeo (CEFR A1 – C2)")

ref_param = str(st.query_params.get("ref_aff") or st.query_params.get("ref") or "").strip()
aff_id_oficial, aff_user_vinculado, aff_nombre_mostrado = _buscar_datos_afiliado(ref_param)

if aff_user_vinculado:
    st.success(
        f"🤝 **Inscripción Referida por Socio Afiliado:** {aff_nombre_mostrado}\n\n"
        f"🆔 **ID Oficial del Socio Afiliado:** `{aff_id_oficial}`"
    )

# ==============================================================================
# Inscripcion_alumnosCEI.py — BLOQUE 2 DE 2 (FINAL): FORMULARIO Y REGISTRO EN BD
# ==============================================================================
if st.session_state.get("ins_alumno_ok"):
    st.balloons()
    st.success(f"🎉 **¡Bienvenido(a) a Career English Institute, {st.session_state.get('ins_alumno_nom', '')}!**")
    st.info(
        f"• **🆔 Matrícula Oficial Asignada:** `{st.session_state.get('ins_alumno_mat', '')}`\n"
        f"• **👤 Usuario de Acceso:** `{st.session_state.get('ins_alumno_usr', '')}`\n"
        f"• **🤝 Socio Afiliado Registrado:** `{st.session_state.get('ins_alumno_aff_id', 'Directo')}`\n"
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
        modalidad_al = st.selectbox("Modalidad de Estudio *", ["100% En Línea (Clases en Vivo + Plataforma IA)"])
    with ca2:
        usr_al = st.text_input("Usuario Deseado para Plataforma *", placeholder="Ej. Sofia Ramirez")
        pwd_al = st.text_input("Crea tu Contraseña de Acceso *", type="password", placeholder="Mínimo 6 caracteres")
        etiqueta_ref_default = f"{aff_id_oficial} — {aff_nombre_mostrado}" if aff_id_oficial else ""
        ref_manual = st.text_input(
            "🆔 ID del Socio Afiliado que te invitó:",
            value=etiqueta_ref_default,
            placeholder="Ej. AFIL-CEI-2026-1234 (opcional si entras directo)",
            disabled=bool(aff_id_oficial)
        )

    st.divider()
    st.markdown("#### 3️⃣ Términos, Condiciones, Reglamento Académico y Compliance CEI")
    with st.container(height=230, border=True):
        st.markdown(obtener_terminos_estudiantes_pg())

    acepta_reg = st.checkbox(
        "✅ He leído, comprendo y acepto los Términos, Condiciones, Reglamento Académico y Políticas de Compliance de Career English Institute (CEI) *",
        key="chk_acepta_terminos_alumno_cei"
    )
    enviar_ins = st.form_submit_button("🎓 Completar Inscripción Oficial", type="primary", width="stretch")

    if enviar_ins:
        if not nom_al.strip() or not pat_al.strip() or not tel_al.strip() or not usr_al.strip() or not pwd_al.strip():
            st.error("⚠️ Por favor completa Nombre, Apellido Paterno, Teléfono, Usuario y Contraseña.")
        elif len(pwd_al.strip()) < 6:
            st.error("⚠️ La contraseña debe tener al menos 6 caracteres.")
        elif not acepta_reg:
            st.error("⚠️ Debes leer y aceptar los Términos, Condiciones, Reglamento Académico y Políticas de Compliance para completar tu inscripción.")
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
                    aff_id_guardar = aff_id_oficial or ref_manual.strip()
                    if aff_user_vinculado:
                        aff_user_guardar = aff_user_vinculado
                    elif ref_manual.strip():
                        _, aff_u_res, _ = _buscar_datos_afiliado(ref_manual.strip())
                        aff_user_guardar = aff_u_res
                    else:
                        aff_user_guardar = ""
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
                                    socio_afiliado_id TEXT,
                                    terminos_aceptados BOOLEAN DEFAULT TRUE,
                                    terminos_aceptados_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                                );
                            """)
                            cur.execute("""
                                ALTER TABLE inscripciones_web_cei
                                ADD COLUMN IF NOT EXISTS socio_afiliado_id TEXT DEFAULT '',
                                ADD COLUMN IF NOT EXISTS terminos_aceptados BOOLEAN DEFAULT TRUE,
                                ADD COLUMN IF NOT EXISTS terminos_aceptados_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                            """)
                            cur.execute("""
                                ALTER TABLE users_padron
                                ADD COLUMN IF NOT EXISTS telefono TEXT DEFAULT '',
                                ADD COLUMN IF NOT EXISTS terminos_aceptados BOOLEAN DEFAULT TRUE,
                                ADD COLUMN IF NOT EXISTS terminos_aceptados_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                            """)
                            cur.execute("""
                                INSERT INTO users_padron (
                                    usuario, clave_hash, rol, permisos, nivel, grado_academico,
                                    estatus, fecha_inscripcion, fecha_inicio_curso, socio_afiliado,
                                    telefono, terminos_aceptados, terminos_aceptados_at
                                ) VALUES (%s, %s, 'Estudiante', 'Basico', %s, %s, 'Activo', %s, %s, %s, %s, TRUE, NOW())
                                ON CONFLICT (usuario) DO UPDATE SET
                                    nivel = EXCLUDED.nivel,
                                    grado_academico = EXCLUDED.grado_academico,
                                    socio_afiliado = COALESCE(NULLIF(EXCLUDED.socio_afiliado, ''), users_padron.socio_afiliado),
                                    telefono = COALESCE(NULLIF(EXCLUDED.telefono, ''), users_padron.telefono),
                                    terminos_aceptados = TRUE,
                                    terminos_aceptados_at = COALESCE(users_padron.terminos_aceptados_at, NOW())
                                RETURNING id, matricula;
                            """, (u_final, pwd_al.strip(), nivel_code, grado_al, hoy_str, hoy_str, aff_user_guardar, tel_al.strip()))
                            r_pad = cur.fetchone()
                            mat_oficial = str(r_pad[1] or "") if r_pad else ""
                            if r_pad and not mat_oficial:
                                mat_oficial = f"CEI-{anio_act}-{int(r_pad[0]):04d}"
                                cur.execute("UPDATE users_padron SET matricula = %s WHERE id = %s;", (mat_oficial, r_pad[0]))

                            cur.execute("""
                                INSERT INTO inscripciones_web_cei (
                                    matricula, usuario, nombre_completo, fecha_nacimiento,
                                    telefono, email, tutor, domicilio, grado_academico,
                                    nivel_cefr, modalidad, socio_afiliado, socio_afiliado_id,
                                    terminos_aceptados, terminos_aceptados_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
                                ON CONFLICT (usuario) DO UPDATE SET
                                    matricula = EXCLUDED.matricula,
                                    nombre_completo = EXCLUDED.nombre_completo,
                                    telefono = EXCLUDED.telefono,
                                    email = EXCLUDED.email,
                                    socio_afiliado = EXCLUDED.socio_afiliado,
                                    socio_afiliado_id = EXCLUDED.socio_afiliado_id,
                                    terminos_aceptados = TRUE,
                                    terminos_aceptados_at = COALESCE(inscripciones_web_cei.terminos_aceptados_at, NOW());
                            """, (
                                mat_oficial, u_final, n_completo, fec_nac,
                                tel_al.strip(), mail_al.strip(), tutor_al.strip(), dom_al.strip(),
                                grado_al, nivel_code, modalidad_al, aff_user_guardar, aff_id_guardar
                            ))

                    st.session_state["ins_alumno_ok"] = True
                    st.session_state["ins_alumno_nom"] = n_completo
                    st.session_state["ins_alumno_mat"] = mat_oficial
                    st.session_state["ins_alumno_usr"] = u_final
                    st.session_state["ins_alumno_aff_id"] = aff_id_guardar or "Directo"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar inscripción: {e}")
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass

