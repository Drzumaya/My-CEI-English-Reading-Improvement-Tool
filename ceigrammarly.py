import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import qrcode
from PIL import Image
from fpdf import FPDF
import io
import json
import base64
import urllib.parse
import requests
from datetime import datetime
import gspread
import pandas as pd
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="CEFR Academic Grammar & Discourse System - Career English Institute",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CLIENTE GLOBAL DE GOOGLE SHEETS ---
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(creds_dict)

def get_spreadsheet():
    return get_gspread_client().open_by_key(st.secrets["spreadsheet_key"])

def get_google_sheet():
    return get_spreadsheet().sheet1

def get_padron_sheet():
    return get_spreadsheet().worksheet("Padron_Estudiantes")

# --- COMPRESIÓN Y GUARDADO PERMANENTE DEL LOGO ---
def compress_logo_to_base64(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        if len(b64_str) <= 45000:
            return b64_str, "image/png"
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg

    img = img.convert("RGB")
    img.thumbnail((280, 280), Image.Resampling.LANCZOS)
    quality = 85
    while quality >= 30:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        if len(b64_str) <= 45000:
            return b64_str, "image/jpeg"
        quality -= 10
    return b64_str, "image/jpeg"

@st.cache_data(ttl=600)
def load_permanent_logo():
    try:
        sheet_logo = get_spreadsheet().worksheet("Config_Logo")
        records = sheet_logo.get_all_records()
        if records:
            return records[-1]
    except Exception:
        pass
    return None

def save_permanent_logo(b64_str, mime, width, shape):
    ss = get_spreadsheet()
    try:
        sheet_logo = ss.worksheet("Config_Logo")
    except Exception:
        sheet_logo = ss.add_worksheet(title="Config_Logo", rows=10, cols=4)
    sheet_logo.clear()
    sheet_logo.append_row(["Logo_Base64", "Mime_Type", "Width", "Shape"])
    sheet_logo.append_row([b64_str, mime, width, shape])
    load_permanent_logo.clear()

def get_default_logo_b64():
    try:
        with open("LOGO CEI APP.png", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8"), "image/png"
    except Exception:
        return None, None
# --- DETECCIÓN DE DISPOSITIVO ---
user_agent = st.context.headers.get("User-Agent", "").lower()
is_mobile = any(device in user_agent for device in ["iphone", "android", "ipad", "mobile"])

CEFR_MAP = {
    "A1": "A1 (Beginner)",
    "A2": "A2 (Elementary)",
    "B1": "B1 (Intermediate)",
    "B2": "B2 (Upper-Intermediate)",
    "C1": "C1 (Advanced)",
    "C2": "C2 (Proficiency)"
}

def normalize_cefr(raw_val):
    code = str(raw_val).strip().upper()[:2]
    return CEFR_MAP.get(code, "B1 (Intermediate)")

# --- INICIALIZACIÓN DE ESTADOS ---
for key, default in [
    ("authenticated", False), ("current_user", ""), ("user_role", "Estudiante"),
    ("user_assigned_level", "B1 (Intermediate)"), ("generated_text", ""),
    ("image_bytes", None), ("audio_bytes", None), ("app_exited", False),
    ("show_saved_audios", False), ("quiz_data", None), ("quiz_graded", False),
    ("quiz_score", None), ("quiz_user_answers", {}), ("pending_ls_token", None),
    ("selected_cefr", "B1 (Intermediate)"), ("show_teacher_registry", False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- LIMPIEZA AUTOMÁTICA DE URL ---
if st.query_params:
    st.query_params.clear()

# --- ESCRITURA INVISIBLE EN LOCALSTORAGE ---
if st.session_state.pending_ls_token is not None:
    if st.session_state.pending_ls_token == "REMOVE":
        streamlit_js_eval(js_expressions="localStorage.removeItem('cei_auth_token')", key="rm_ls_init")
    else:
        streamlit_js_eval(js_expressions=f"localStorage.setItem('cei_auth_token', '{st.session_state.pending_ls_token}')", key="sv_ls_init")
    st.session_state.pending_ls_token = None

# --- RECUPERACIÓN INVISIBLE DE SESIÓN (ACTUALIZA NIVEL DESDE EL PADRÓN) ---
if not st.session_state.authenticated and not st.session_state.app_exited:
    saved_token = streamlit_js_eval(js_expressions="localStorage.getItem('cei_auth_token')", key="get_ls_token")
    if saved_token and isinstance(saved_token, str):
        try:
            decoded_json = base64.urlsafe_b64decode(saved_token.encode("utf-8")).decode("utf-8")
            token_data = json.loads(decoded_json)
            u_tok, c_tok = token_data.get("u", ""), token_data.get("c", "")
            if u_tok and c_tok:
                for reg in get_padron_sheet().get_all_records():
                    if (str(reg.get("Usuario", "")).strip().lower() == u_tok.lower() and
                        str(reg.get("Clave", "")).strip() == c_tok and
                        str(reg.get("Estatus", "Activo")).strip().lower() == "activo"):
                        st.session_state.authenticated = True
                        st.session_state.current_user = str(reg.get("Usuario", "")).strip()
                        st.session_state.user_role = str(reg.get("Rol", "Estudiante")).strip()
                        lvl_norm = normalize_cefr(reg.get("Nivel", "B1"))
                        st.session_state.user_assigned_level = lvl_norm
                        st.session_state.selected_cefr = lvl_norm
                        st.rerun()
        except Exception:
            pass

# --- PANTALLA DE SALIDA ---
if st.session_state.app_exited:
    streamlit_js_eval(js_expressions="localStorage.removeItem('cei_auth_token')", key="exit_rm_ls")
    st.title("👋 Academic Session Ended")
    st.info("Thank you for using the CEFR Academic Grammar & Discourse System by CAREER ENGLISH INSTITUTE.")
    st.caption("© 2026 CAREER ENGLISH INSTITUTE. Todos los derechos reservados. Author: Jacob Zumaya Prianti.")
    if st.button("Volver al Inicio de Sesión"):
        st.session_state.app_exited = False
        st.session_state.authenticated = False
        st.rerun()
    st.stop()

# --- PANTALLA DE LOGIN ---
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        saved_logo = load_permanent_logo()
        b64_l, mime_l = (saved_logo["Logo_Base64"], saved_logo["Mime_Type"]) if (saved_logo and saved_logo.get("Logo_Base64")) else get_default_logo_b64()
        if b64_l:
            st.markdown(f'<div style="text-align: center;"><img src="data:{mime_l};base64,{b64_l}" style="width: 115px; border-radius: 50%;"></div>', unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center;'>🏛️ CAREER ENGLISH INSTITUTE</h3>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🎓 CEFR ACADEMIC GRAMMAR & DISCOURSE SYSTEM</h2>", unsafe_allow_html=True)
        st.divider()
        
        with st.form("login_form"):
            st.subheader("🔐 Control de Acceso Académico")
            input_user = st.text_input("👤 Usuario registrado:")
            input_pass = st.text_input("🔑 Clave de Acceso:", type="password")
            remember_me = st.checkbox("💾 Recordar mi usuario y contraseña en este navegador", value=True)
            submit_login = st.form_submit_button("Ingresar a la Plataforma", type="primary", width="stretch")
            
            if submit_login:
                if not input_user or not input_pass:
                    st.warning("⚠️ Ingresa tu Usuario y Clave de Acceso.")
                else:
                    try:
                        with st.spinner("Verificando credenciales y nivel asignado..."):
                            registros = get_padron_sheet().get_all_records()
                            acceso_valido = False
                            for reg in registros:
                                u_db = str(reg.get("Usuario", "")).strip()
                                c_db = str(reg.get("Clave", "")).strip()
                                e_db = str(reg.get("Estatus", "Activo")).strip().lower()
                                r_db = str(reg.get("Rol", "Estudiante")).strip()
                                n_db = normalize_cefr(reg.get("Nivel", "B1"))
                                
                                if u_db.lower() == input_user.strip().lower() and c_db == input_pass.strip():
                                    if e_db == "activo":
                                        st.session_state.authenticated = True
                                        st.session_state.current_user = u_db
                                        st.session_state.user_role = r_db
                                        st.session_state.user_assigned_level = n_db
                                        st.session_state.selected_cefr = n_db
                                        if remember_me:
                                            payload = json.dumps({"u": u_db, "c": c_db}).encode("utf-8")
                                            st.session_state.pending_ls_token = base64.urlsafe_b64encode(payload).decode("utf-8")
                                        else:
                                            st.session_state.pending_ls_token = "REMOVE"
                                        acceso_valido = True
                                        break
                                    else:
                                        st.error("⛔ Tu cuenta se encuentra inactiva.")
                                        acceso_valido = None
                                        break
                            if acceso_valido is True:
                                st.rerun()
                            elif acceso_valido is False:
                                st.error("❌ Usuario o Clave incorrectos.")
                    except Exception as e:
                        st.error(f"Error al conectar con 'Padron_Estudiantes': {e}")
        st.markdown("<div style='text-align: center; color: #777; font-size: 12px; margin-top: 15px;'>© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti</div>", unsafe_allow_html=True)
    st.stop()
# --- DETECCIÓN DE ROL TEACHER EN ESCRITORIO (OCULTO EN MÓVILES/QR) ---
is_teacher_desktop = (st.session_state.user_role.strip().lower() in ["teacher", "admin"]) and (not is_mobile)

cefr_options = list(CEFR_MAP.values())

# --- BARRA IZQUIERDA (INPUTS DEL ALGORITMO) ---
with st.sidebar:
    st.markdown("### 🏛️ CAREER ENGLISH INSTITUTE")
    st.success(f"👤 **{st.session_state.current_user}** | *{st.session_state.user_role}*")
    st.divider()

    st.header("⚙️ Academic Parameters")
    usuario = st.session_state.current_user

    if is_teacher_desktop:
        st.subheader("🎯 CEFR Preview Level (Teacher)")
        default_idx = cefr_options.index(st.session_state.user_assigned_level) if st.session_state.user_assigned_level in cefr_options else 2
        cefr_level = st.selectbox(
            "Select CEFR Level (A1 - C2):",
            cefr_options,
            index=default_idx,
            help="Para asignar el nivel permanente a cada alumno, usa el botón Registrar Alumnos."
        )
    else:
        cefr_level = st.session_state.user_assigned_level
        st.info(f"🎯 **Assigned Student Level:** {cefr_level}")

    st.subheader("1. Context & Characters (Español / English)")
    contexto = st.text_input("Contexto / Lugar / Tema:", placeholder="Ej: En un aeropuerto en Londres / At an airport")
    personas = st.text_input("Personas / Personajes:", placeholder="Ej: Un turista y una azafata / A tourist and a pilot")
    
    st.subheader("2. Subject Matter (Español / English)")
    asunto = st.text_input("Asunto / Materia:", placeholder="Ej: Equipaje perdido / Lost luggage")
    
    st.subheader(f"3. Grammar Topics ({cefr_level.split()[0]})")
    gramatica_b1 = st.selectbox(
        "Selecciona el tema gramatical:",
        [
            "Present Simple & Continuous / Verb To Be",
            "Past Simple & Past Continuous",
            "Present Perfect vs. Past Simple",
            "Future Forms (Will, Going to, Present Continuous)",
            "First, Second & Third Conditionals (If clauses)",
            "Modal Verbs (can, must, have to, might, should, could)",
            "Passive Voice (All Tenses)",
            "Relative Clauses (who, which, that, where, whose)",
            "Used to / Would for past habits",
            "Reported Speech (Statements, Questions & Commands)",
            "Comparatives, Superlatives & Inversion"
        ],
        index=2
    )
    
    st.subheader("4. Discourse Mode")
    tipo_texto = st.selectbox(
        "Formato de generación para el estudiante:",
        [
            "Preguntas (Comprehension & Grammar Questions)",
            "Descripción (Detailed Description)",
            "Narración (Narration)",
            "Juicio (Critical Judgment / Opinion)",
            "Explicación (Clear Explanation)",
            "Historia (Short Story)",
            "Storytelling (Engaging Narrative)"
        ]
    )
    
    st.markdown("---")
    generar_btn = st.button(f"🚀 Generate {cefr_level.split()[0]} Lesson", type="primary", width="stretch")

# --- CABECERA INSTITUCIONAL ---
saved_logo = load_permanent_logo()
default_width = int(saved_logo["Width"]) if saved_logo and saved_logo.get("Width") else 115
default_shape = saved_logo["Shape"] if saved_logo and saved_logo.get("Shape") else "Circular"
shape_options = ["Original", "Redondeado", "Circular"]
default_shape_idx = shape_options.index(default_shape) if default_shape in shape_options else 2

col_logo, col_title, col_qr, col_exit = st.columns([1.6, 4.9, 2, 1.5])

with col_logo:
    if is_teacher_desktop:
        with st.popover("✏️ Editar Logo", width="stretch"):
            logo_file = st.file_uploader("Subir imagen (PNG/JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
            logo_width = st.slider("Tamaño (px):", min_value=60, max_value=220, value=default_width, step=5)
            logo_shape = st.radio("Forma:", shape_options, index=default_shape_idx, horizontal=True)
            
            if st.button("💾 Guardar Logo Permanente", type="primary", width="stretch"):
                b64_to_save, mime_to_save = None, None
                if logo_file is not None:
                    b64_to_save, mime_to_save = compress_logo_to_base64(logo_file)
                elif saved_logo and saved_logo.get("Logo_Base64"):
                    b64_to_save, mime_to_save = saved_logo["Logo_Base64"], saved_logo["Mime_Type"]
                else:
                    b64_to_save, mime_to_save = get_default_logo_b64()
                    
                if b64_to_save:
                    try:
                        with st.spinner("Guardando logo..."):
                            save_permanent_logo(b64_to_save, mime_to_save, logo_width, logo_shape)
                            st.success("✅ ¡Logo guardado!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        logo_file = None
        logo_width = default_width
        logo_shape = default_shape

    if logo_file is not None:
        active_b64, active_mime = compress_logo_to_base64(logo_file)
    elif saved_logo and saved_logo.get("Logo_Base64"):
        active_b64, active_mime = saved_logo["Logo_Base64"], saved_logo["Mime_Type"]
    else:
        active_b64, active_mime = get_default_logo_b64()

    if active_b64:
        radius = "15px" if logo_shape == "Redondeado" else ("50%" if logo_shape == "Circular" else "0px")
        st.markdown(
            f'<div style="text-align: center;"><img src="data:{active_mime};base64,{active_b64}" style="width: {logo_width}px; height: auto; border-radius: {radius}; object-fit: cover;"></div>',
            unsafe_allow_html=True
        )
with col_title:
    st.markdown("#### 🏛️ CAREER ENGLISH INSTITUTE")
    st.title(f"🎓 CEFR {cefr_level.split()[0]} ACADEMIC GRAMMAR & DISCOURSE SYSTEM")
    st.caption("Author: Jacob Zumaya Prianti | Applied Linguistics & Proficiency Assessment | APA Style")

with col_qr:
    if not is_mobile:
        APP_URL = "https://myceigrammarly.streamlit.app" 
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(APP_URL)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img_qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="📱 Scan for Mobile View", width=110)

with col_exit:
    if is_teacher_desktop:
        btn_label = "✖️ Ocultar Registro" if st.session_state.show_teacher_registry else "🎓 Registrar Alumnos"
        if st.button(btn_label, type="primary" if not st.session_state.show_teacher_registry else "secondary", width="stretch"):
            st.session_state.show_teacher_registry = not st.session_state.show_teacher_registry
            st.rerun()

    if st.button("🚪 Salir", type="secondary", width="stretch"):
        st.session_state.app_exited = True
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# --- FORMULARIO DESPLEGABLE EXCLUSIVO DEL TEACHER ---
if is_teacher_desktop and st.session_state.show_teacher_registry:
    with st.container(border=True):
        col_head_reg, col_close_reg = st.columns([5, 1])
        with col_head_reg:
            st.markdown("### 🎓 FACULTY BACKEND: Registro de Estudiantes y Asignación de Nivel CEFR (A1 - C2)")
        with col_close_reg:
            if st.button("🔼 Cerrar Panel", width="stretch"):
                st.session_state.show_teacher_registry = False
                st.rerun()

        col_form_reg, col_tabla_reg = st.columns([1.2, 1.8])
        
        with col_form_reg:
            st.markdown("#### ➕ Alta de Nuevo Estudiante")
            with st.form("form_registro_estudiante", clear_on_submit=True):
                reg_usuario = st.text_input("👤 Nombre Completo / Usuario:", placeholder="Ej: Carlos Mendoza")
                reg_clave = st.text_input("🔑 Clave de Acceso asignada:", placeholder="Ej: CEI-2026-05")
                
                c_r1, c_r2 = st.columns(2)
                with c_r1:
                    reg_rol = st.selectbox("Rol:", ["Estudiante", "Teacher"])
                with c_r2:
                    reg_nivel = st.selectbox("Nivel CEFR asignado:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2)
                
                btn_registrar_alumno = st.form_submit_button("💾 Guardar Estudiante en Padrón", type="primary", width="stretch")
                
                if btn_registrar_alumno:
                    if not reg_usuario.strip() or not reg_clave.strip():
                        st.warning("⚠️ Por favor completa el nombre del estudiante y su clave de acceso.")
                    else:
                        try:
                            with st.spinner("Registrando en Google Sheets..."):
                                p_sheet = get_padron_sheet()
                                existentes = [str(r.get("Usuario", "")).strip().lower() for r in p_sheet.get_all_records()]
                                if reg_usuario.strip().lower() in existentes:
                                    st.error(f"⚠️ El usuario '{reg_usuario.strip()}' ya está registrado en el padrón.")
                                else:
                                    p_sheet.append_row([reg_usuario.strip(), reg_clave.strip(), reg_rol, "Activo", reg_nivel])
                                    st.success(f"✅ ¡{reg_usuario.strip()} registrado con éxito en nivel {reg_nivel}!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar estudiante: {e}")

        with col_tabla_reg:
            st.markdown("#### 📋 Padrón Actual y Edición Rápida")
            try:
                p_sheet = get_padron_sheet()
                records_p = p_sheet.get_all_records()
                if records_p:
                    df_p = pd.DataFrame(records_p)
                    cols_mostrar = [c for c in ["Usuario", "Rol", "Nivel", "Estatus"] if c in df_p.columns]
                    st.dataframe(df_p[cols_mostrar], height=180, width="stretch", hide_index=True)
                    
                    c_ed1, c_ed2, c_ed3 = st.columns([1.5, 1, 1])
                    with c_ed1:
                        user_to_edit = st.selectbox("Seleccionar alumno:", df_p["Usuario"].tolist(), key="edit_u_sel")
                    with c_ed2:
                        new_lvl_edit = st.selectbox("Cambiar Nivel:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2, key="edit_lv_sel")
                    with c_ed3:
                        new_status = st.selectbox("Estatus:", ["Activo", "Inactivo"], key="edit_st_sel")
                        
                    if st.button("🔄 Actualizar Alumno", width="stretch"):
                        cell = p_sheet.find(user_to_edit)
                        if cell:
                            p_sheet.update_cell(cell.row, 4, new_status)
                            p_sheet.update_cell(cell.row, 5, new_lvl_edit)
                            st.success(f"✅ Datos de {user_to_edit} actualizados.")
                            st.rerun()
                else:
                    st.info("Aún no hay estudiantes registrados en el padrón.")
            except Exception as e:
                st.error(f"Error al cargar el padrón: {e}")
    st.divider()
# --- MOTOR DE IA DE MÁXIMA POTENCIA ---
def generar_con_maxima_potencia(client, prompt_contenido, instruccion_sistema=None):
    modelos_potentes = [
        "gemini-3.1-pro-preview", "gemini-3.5-pro", "gemini-3.8-flash",
        "gemini-3.1-flash-lite-preview", "gemini-2.5-pro", "gemini-2.5-flash"
    ]
    try:
        pro_det, otros_det = [], []
        for m in client.models.list():
            nombre = m.name.replace("models/", "")
            if "gemini" in nombre and not any(x in nombre for x in ["embedding", "imagen", "aqa", "tts", "audio"]):
                if nombre not in modelos_potentes:
                    (pro_det if ("pro" in nombre or "ultra" in nombre) else otros_det).append(nombre)
        modelos_potentes += sorted(pro_det, reverse=True) + sorted(otros_det, reverse=True)
    except Exception:
        pass

    ultimo_error = None
    for modelo in modelos_potentes:
        try:
            config = types.GenerateContentConfig(system_instruction=instruccion_sistema, temperature=0.65) if instruccion_sistema else types.GenerateContentConfig(temperature=0.65)
            respuesta = client.models.generate_content(model=modelo, contents=prompt_contenido, config=config)
            if respuesta and respuesta.text:
                return respuesta.text, modelo
        except Exception as e:
            ultimo_error = e
            continue
    raise ultimo_error

# --- FUNCIÓN DE GENERACIÓN DE IMAGEN CON DESCARGA DIRECTA EN SERVIDOR ---
def generar_imagen_estable(prompt_ingles):
    clean_p = "".join(c for c in prompt_ingles if c.isalnum() or c in " ,.-").strip()
    encoded = urllib.parse.quote(clean_p)
    urls_intento = [
        f"https://pollinations.ai{encoded}?width=800&height=500&nologo=true&seed={datetime.now().second}",
        f"https://pollinations.ai{encoded}?model=turbo&width=800&height=500&nologo=true"
    ]
    headers = {"User-Agent": "Mozilla/5.0"}
    for u in urls_intento:
        try:
            resp = requests.get(u, headers=headers, timeout=18)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content
        except Exception:
            continue
    return None

def generar_quiz_leccion(texto_leccion, tema_gramatical, nivel_cefr, evitar_preguntas=None):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    evitar_txt = f"IMPORTANT: Create COMPLETELY DIFFERENT questions from: {evitar_preguntas}" if evitar_preguntas else ""
    prompt_quiz = f"""
    Based on this CEFR Level {nivel_cefr} English lesson, create a 5-question multiple-choice quiz in English calibrated strictly to level {nivel_cefr}, evaluating comprehension and target grammar ({tema_gramatical}).
    {evitar_txt}
    LESSON TEXT:
    {texto_leccion}
    RETURN ONLY VALID JSON array:
    [{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A) ..."}}]
    """
    raw_resp, _ = generar_con_maxima_potencia(client, prompt_quiz, "Output strictly valid JSON array only.")
    cleaned = raw_resp.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]
    return json.loads(cleaned.strip())

# --- EJECUCIÓN DE GENERACIÓN ---
if generar_btn:
    if "GEMINI_API_KEY" not in st.secrets:
        st.sidebar.error("⚠️ GEMINI_API_KEY no configurada.")
    elif not contexto or not asunto:
        st.sidebar.warning("⚠️ Completa Contexto y Asunto.")
    else:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        with st.spinner(f"🧠 Generating CEFR {cefr_level} Lesson, Illustration & Audio..."):
            try:
                cefr_guidelines = {
                    "A1": "Use very basic everyday vocabulary, short simple sentences (5-8 words), present simple/continuous, and concrete familiar topics.",
                    "A2": "Use simple, clear sentences, basic connectors (and, but, because, so), past simple, and everyday routine vocabulary.",
                    "B1": "Use clear standard English, connected paragraphs, intermediate vocabulary, and a mix of simple and complex clauses.",
                    "B2": "Use fluent, detailed academic/semi-formal English, complex sentence structures, nuanced connectors, and abstract concepts.",
                    "C1": "Use sophisticated, advanced academic English, idiomatic expressions, complex subordinate clauses, and high lexical precision.",
                    "C2": "Use near-native, scholarly English with subtle rhetorical devices, advanced syntax, and specialized academic vocabulary."
                }
                nivel_corto = cefr_level.split()[0]
                guia_nivel = cefr_guidelines.get(nivel_corto, cefr_guidelines["B1"])

                sys_prompt = (
                    f"You are a Senior Applied Linguist at CAREER ENGLISH INSTITUTE. "
                    f"Translate any Spanish inputs and write 100% in natural English calibrated STRICTLY to CEFR Level {cefr_level}. "
                    f"LINGUISTIC CALIBRATION RULE: {guia_nivel} "
                    f"Follow strict APA Style. The official author of every generated academic document MUST be Jacob Zumaya Prianti (APA citation: Zumaya Prianti, J., 2026). "
                    f"Zero Spanish words allowed."
                )
                prompt_texto = f"""
                Create a CEFR Level {cefr_level} English lesson artifact authored by Jacob Zumaya Prianti:
                - Context: {contexto} | Characters: {personas} | Subject: {asunto}
                - Target Grammar: {gramatica_b1} | Discourse Mode: {tipo_texto}
                
                STRICT RULES:
                1. 100% English only. Calibrate vocabulary and grammar strictly to CEFR {cefr_level}. Highlight all {gramatica_b1} structures in **bold**.
                2. APA Header & Byline: Include the academic title in bold, followed immediately by:
                   **Author:** Jacob Zumaya Prianti  
                   **Institution:** Career English Institute (2026) | **CEFR Level:** {cefr_level}
                3. APA References: Include an APA Reference list at the end, listing as primary source:
                   Zumaya Prianti, J. (2026). *{asunto.title()}: CEFR {nivel_corto} Applied Grammar & Discourse Module*. Career English Institute.
                """
                texto_gen, mod_usado = generar_con_maxima_potencia(client, prompt_texto, sys_prompt)
                st.session_state.generated_text = texto_gen
                st.session_state.active_model_name = mod_usado
                st.session_state.selected_cefr = cefr_level
                st.session_state.quiz_data = None
                st.session_state.quiz_graded = False
                st.session_state.quiz_score = None
                st.session_state.quiz_user_answers = {}
                
                img_desc, _ = generar_con_maxima_potencia(
                    client,
                    f"Write a simple 12-word visual description in English for an illustration: {contexto}, {personas}, {asunto}. Flat vector illustration, colorful, no text."
                )
                st.session_state.image_bytes = generar_imagen_estable(img_desc)
                
                tts = gTTS(text=texto_gen.replace("*", "").replace("#", ""), lang='en', slow=False)
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.session_state.audio_bytes = audio_fp.getvalue()
            except Exception as e:
                st.error(f"⚠️ Error al generar lección: {e}")
# --- PANEL CENTRAL Y DERECHO ---
col_main_center, col_tools_right = st.columns([7, 3.5])

with col_main_center:
    col_sub_t, col_badge = st.columns([3, 1.5])
    with col_sub_t:
        st.subheader("📄 Generated Content (APA Format - 100% English)")
    with col_badge:
        if st.session_state.get("active_model_name"):
            st.caption(f"⚡ Engine: `{st.session_state.active_model_name}`")

    top_container = st.container(height=420, border=True)
    with top_container:
        if st.session_state.generated_text:
            st.markdown(st.session_state.generated_text)
        else:
            st.info("👈 Escribe los datos en Español o Inglés en la barra izquierda y presiona **Generate Lesson**.")

    # --- QUIZ INTERACTIVO DE LA LECCIÓN ---
    if st.session_state.generated_text:
        if st.session_state.quiz_data is None:
            if st.button(f"📝 Generar Quiz de la Lección (CEFR {st.session_state.selected_cefr.split()[0]} Assessment)", type="primary", width="stretch"):
                with st.spinner("Generando preguntas de evaluación..."):
                    try:
                        st.session_state.quiz_data = generar_quiz_leccion(
                            st.session_state.generated_text, gramatica_b1, st.session_state.selected_cefr
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al generar quiz: {e}")
        else:
            with st.container(border=True):
                st.subheader("📝 Lesson Comprehension & Grammar Quiz")
                for idx, item in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**{idx + 1}. {item['question']}**")
                    choice = st.radio(f"q_{idx}", item["options"], key=f"radio_quiz_{idx}", label_visibility="collapsed", index=None)
                    st.session_state.quiz_user_answers[idx] = choice
                    if st.session_state.quiz_graded:
                        if choice == item["answer"]:
                            st.success(f"✅ Correct! ({item['answer']})")
                        else:
                            st.error(f"❌ Incorrect. Your answer: {choice or 'None'} | **Correct answer:** {item['answer']}")
                    st.write("")

                col_btn_grade, col_btn_new = st.columns(2)
                with col_btn_grade:
                    if st.button("✅ Calificar Quiz", type="primary", width="stretch"):
                        correctas = sum(1 for i, it in enumerate(st.session_state.quiz_data) if st.session_state.quiz_user_answers.get(i) == it["answer"])
                        total = len(st.session_state.quiz_data)
                        st.session_state.quiz_score = f"{correctas}/{total} ({round((correctas / total) * 100, 1)}%)"
                        st.session_state.quiz_graded = True
                        st.rerun()
                with col_btn_new:
                    if st.button("🔄 Nuevo Quiz (Cambiar Preguntas)", type="secondary", width="stretch"):
                        with st.spinner("Generando nuevas preguntas..."):
                            try:
                                prev_qs = [q["question"] for q in st.session_state.quiz_data]
                                st.session_state.quiz_data = generar_quiz_leccion(
                                    st.session_state.generated_text, gramatica_b1, st.session_state.selected_cefr, prev_qs
                                )
                                st.session_state.quiz_graded = False
                                st.session_state.quiz_score = None
                                st.session_state.quiz_user_answers = {}
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al renovar quiz: {e}")

                if st.session_state.quiz_graded and st.session_state.quiz_score:
                    st.info(f"🏆 **Calificación Obtenida / Final Score:** {st.session_state.quiz_score}")

    st.subheader("🖼️ Visual Context")
    bottom_container = st.container(height=280, border=True)
    with bottom_container:
        if st.session_state.image_bytes:
            st.image(st.session_state.image_bytes, width="stretch")
        elif st.session_state.generated_text:
            st.warning("⚠️ El servidor gráfico tardó en responder. Presiona nuevamente el botón Generate Lesson para reintentar la imagen.")
        else:
            st.caption("La imagen ilustrativa aparecerá aquí / The illustrative image will appear here.")
# --- PANEL DERECHO EN ORDEN PROFESIONAL ---
with col_tools_right:
    # 1. AUDIO MODELO + DESCARGAR AUDIO
    st.subheader("🎧 1. Model Pronunciation")
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        st.download_button(
            label="📥 Descargar Audio (MP3)",
            data=st.session_state.audio_bytes,
            file_name=f"CEI_Audio_{usuario.replace(' ', '_')}.mp3",
            mime="audio/mp3",
            width="stretch"
        )
    else:
        st.caption("Audio available after generating lesson.")
        
    st.divider()

    # 2. PRÁCTICA DE LECTURA: GRABAR AUDIO Y GRABAR/DESCARGAR VIDEO
    st.subheader("🎙️ 2. Speaking & Video Practice")
    tab_rec_audio, tab_rec_video = st.tabs(["🎤 Grabar Audio", "📹 Grabar Video"])
    
    with tab_rec_audio:
        student_audio = st.audio_input("Graba tu voz leyendo el texto:")
        
    with tab_rec_video:
        st.caption("Graba o selecciona tu video de lectura:")
        student_video = st.file_uploader(
            "Activar Cámara / Video (MP4/MOV/WEBM):",
            type=["mp4", "mov", "webm"],
            accept_multiple_files=False,
            key="video_rec_uploader"
        )
        if student_video is not None:
            st.video(student_video)
            st.download_button(
                label="📥 Descargar Video en Dispositivo",
                data=student_video.getvalue(),
                file_name=f"CEI_Video_{usuario.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.mp4",
                mime=student_video.type or "video/mp4",
                type="primary",
                width="stretch"
            )
        else:
            st.button("📥 Descargar Video en Dispositivo", disabled=True, width="stretch")

    st.write("")

    # 3. BOTONES EN ORDEN PROFESIONAL:
    # (A) GUARDAR AUDIO -> (B) DESCARGAR PDF EN TIEMPO REAL -> (C) VER AUDIOS GUARDADOS
    if st.button("☁️ Guardar Audio en Google Sheets", type="primary", width="stretch", disabled=(student_audio is None)):
        try:
            with st.spinner("Guardando audio en base de datos..."):
                sheet = get_google_sheet()
                audio_b64 = base64.b64encode(student_audio.getvalue()).decode("utf-8")
                if len(audio_b64) > 49000:
                    st.error("⚠️ El audio supera los 15 seg. Graba un fragmento más corto.")
                else:
                    tema_completo = f"[{st.session_state.selected_cefr.split()[0]}] {asunto} ({gramatica_b1})" if asunto else gramatica_b1
                    fecha_subida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet.append_row([usuario, tema_completo, audio_b64, fecha_subida])
                    st.success("✅ ¡Audio guardado en Google Sheets!")
        except Exception as e:
            st.error(f"Error al guardar audio: {e}")

    # FUNCIÓN GENERADORA DE PDF EN TIEMPO REAL CON AUTORÍA JACOB ZUMAYA PRIANTI
    def create_pdf(text, quiz_items=None, user_ans=None, score=None):
        pdf = FPDF()
        pdf.set_author("Jacob Zumaya Prianti")
        pdf.set_creator("Career English Institute")
        pdf.add_page()
        pdf.set_font("Times", "B", 14)
        pdf.cell(0, 10, txt="CAREER ENGLISH INSTITUTE", ln=True, align="C")
        pdf.set_font("Times", "B", 11)
        pdf.cell(0, 7, txt=f"CEFR {st.session_state.selected_cefr} Academic Grammar & Discourse System", ln=True, align="C")
        pdf.set_font("Times", "B", 10)
        pdf.cell(0, 7, txt="Author: Jacob Zumaya Prianti", ln=True, align="C")
        pdf.set_font("Times", "I", 10)
        pdf.cell(0, 7, txt=f"Student: {usuario} | Level: {st.session_state.selected_cefr} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_font("Times", size=12)
        pdf.multi_cell(0, 8, txt=text.encode("latin-1", "replace").decode("latin-1"))
        
        if quiz_items:
            pdf.ln(8)
            pdf.set_font("Times", "B", 13)
            pdf.cell(0, 10, txt="LESSON COMPREHENSION & GRAMMAR QUIZ", ln=True)
            if score:
                pdf.set_font("Times", "B", 11)
                pdf.cell(0, 8, txt=f"Final Grade / Calificacion Obtenida: {score}", ln=True)
            pdf.ln(3)
            for i, q in enumerate(quiz_items):
                pdf.set_font("Times", "B", 11)
                pdf.multi_cell(0, 7, txt=f"{i+1}. {q['question']}".encode("latin-1", "replace").decode("latin-1"))
                pdf.set_font("Times", size=10)
                for opt in q["options"]:
                    pdf.multi_cell(0, 6, txt=f"   {opt}".encode("latin-1", "replace").decode("latin-1"))
                u_choice = user_ans.get(i) if user_ans else "None"
                ans_line = f"   -> Student Answer: {u_choice or 'None'} | Correct: {q['answer']}"
                pdf.set_font("Times", "I", 10)
                pdf.multi_cell(0, 6, txt=ans_line.encode("latin-1", "replace").decode("latin-1"))
                pdf.ln(3)

        pdf.ln(10)
        pdf.set_font("Times", "I", 10)
        pdf.cell(0, 10, txt="© 2026 CAREER ENGLISH INSTITUTE. Todos los derechos reservados. Author: Jacob Zumaya Prianti.", ln=True, align="C")
        return pdf.output(dest="S").encode("latin-1")

    # BOTÓN DESCARGAR PDF EN TIEMPO REAL
    if st.session_state.generated_text:
        pdf_bytes = create_pdf(
            st.session_state.generated_text.replace("*", ""),
            quiz_items=st.session_state.quiz_data,
            user_ans=st.session_state.quiz_user_answers,
            score=st.session_state.quiz_score
        )
        st.download_button(
            label="📥 Descargar PDF (Tiempo Real)",
            data=pdf_bytes,
            file_name=f"CEI_Lesson_{usuario.replace(' ', '_')}.pdf",
            mime="application/pdf",
            width="stretch"
        )
    else:
        st.button("📥 Descargar PDF (Tiempo Real)", disabled=True, width="stretch")

    # BOTÓN VER AUDIOS GUARDADOS
    if st.button("📂 Ver Audios Guardados", width="stretch"):
        st.session_state.show_saved_audios = not st.session_state.show_saved_audios

    if st.session_state.show_saved_audios:
        with st.container(height=260, border=True):
            st.markdown("**Historial de Grabaciones:**")
            try:
                records = get_google_sheet().get_all_records()
                if not records:
                    st.info("Aún no hay audios guardados.")
                else:
                    df = pd.DataFrame(records)
                    if st.session_state.user_role.strip().lower() not in ["teacher", "admin"]:
                        df = df[df["Usuario"].astype(str).str.lower() == usuario.lower()]
                    if df.empty:
                        st.warning(f"Sin registros para '{usuario}'.")
                    else:
                        for _, row in df.tail(5).iloc[::-1].iterrows():
                            st.caption(f"👤 **{row['Usuario']}** | 📅 {row['Fecha_de_subida']}")
                            st.caption(f"📘 *{row['Tema']}*")
                            if row.get("Audio"):
                                st.audio(base64.b64decode(row["Audio"]), format="audio/wav")
                            st.divider()
            except Exception as e:
                st.error(f"Error al cargar historial: {e}")

    st.divider()

    # 4. BOTÓN LIMPIAR PANTALLA
    if st.button("🗑️ Borrar Todo", type="secondary", width="stretch"):
        st.session_state.generated_text = ""
        st.session_state.image_bytes = None
        st.session_state.audio_bytes = None
        st.session_state.show_saved_audios = False
        st.session_state.quiz_data = None
        st.session_state.quiz_graded = False
        st.session_state.quiz_score = None
        st.session_state.quiz_user_answers = {}
        st.rerun()

# --- PIE DE PÁGINA INSTITUCIONAL ---
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 13px; padding: 10px;">
        © 2026 <b>CAREER ENGLISH INSTITUTE</b> | Todos los derechos reservados.<br>
        Author / Creado y desarrollado por: <b>Jacob Zumaya Prianti</b>
    </div>
    """,
    unsafe_allow_html=True
)
