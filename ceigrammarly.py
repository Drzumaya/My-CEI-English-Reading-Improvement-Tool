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
from datetime import datetime
import gspread
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="CEFR B1 Academic Grammar & Discourse System - Career English Institute",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CLIENTE GLOBAL DE GOOGLE SHEETS (CONEXIÓN DIRECTA POR ID) ---
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(creds_dict)

def get_spreadsheet():
    return get_gspread_client().open_by_key(st.secrets["spreadsheet_key"])

def get_google_sheet():
    return get_spreadsheet().sheet1

def get_padron_sheet():
    return get_spreadsheet().worksheet("Padron_Estudiantes")

# --- COMPRESIÓN Y GUARDADO PERMANENTE DEL LOGO EN GOOGLE SHEETS ---
def compress_logo_to_base64(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        # Mantener transparencia si es PNG redimensionando suavemente
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        if len(b64_str) <= 45000:
            return b64_str, "image/png"
        # Si sigue pesando mucho, convertir a JPEG con fondo blanco
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
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

# --- DETECCIÓN DE DISPOSITIVO (MÓVIL/QR VS ESCRITORIO) ---
user_agent = st.context.headers.get("User-Agent", "").lower()
is_mobile = any(device in user_agent for device in ["iphone", "android", "ipad", "mobile"])

# --- INICIALIZACIÓN DE ESTADOS ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = "Estudiante"
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "image_url" not in st.session_state:
    st.session_state.image_url = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "app_exited" not in st.session_state:
    st.session_state.app_exited = False
if "show_saved_audios" not in st.session_state:
    st.session_state.show_saved_audios = False
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_graded" not in st.session_state:
    st.session_state.quiz_graded = False
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = None
if "quiz_user_answers" not in st.session_state:
    st.session_state.quiz_user_answers = {}

# --- RECUPERACIÓN AUTOMÁTICA DE SESIÓN RECORDADA (QUERY PARAMS) ---
if not st.session_state.authenticated and not st.session_state.app_exited:
    saved_token = st.query_params.get("auth_token", "")
    if saved_token:
        try:
            decoded_json = base64.urlsafe_b64decode(saved_token.encode("utf-8")).decode("utf-8")
            token_data = json.loads(decoded_json)
            u_tok = token_data.get("u", "")
            c_tok = token_data.get("c", "")
            if u_tok and c_tok:
                registros = get_padron_sheet().get_all_records()
                for reg in registros:
                    if (str(reg.get("Usuario", "")).strip().lower() == u_tok.lower() and
                        str(reg.get("Clave", "")).strip() == c_tok and
                        str(reg.get("Estatus", "Activo")).strip().lower() == "activo"):
                        st.session_state.authenticated = True
                        st.session_state.current_user = str(reg.get("Usuario", "")).strip()
                        st.session_state.user_role = str(reg.get("Rol", "Estudiante")).strip()
                        break
        except Exception:
            st.query_params.clear()

# --- PANTALLA DE SALIDA ---
if st.session_state.app_exited:
    st.title("👋 Academic Session Ended")
    st.info("Thank you for using the CEFR B1 Academic Grammar & Discourse System by CAREER ENGLISH INSTITUTE. You may close this tab now.")
    st.caption("© 2026 CAREER ENGLISH INSTITUTE. Todos los derechos reservados. Creado por JACOB ZUMAYA PRIANTI.")
    if st.button("Volver al Inicio de Sesión"):
        st.session_state.app_exited = False
        st.session_state.authenticated = False
        st.rerun()
    st.stop()

# --- PANTALLA DE CONTROL DE ACCESO (LOGIN CON OPCIÓN DE RECORDAR) ---
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        saved_logo = load_permanent_logo()
        if saved_logo and saved_logo.get("Logo_Base64"):
            st.markdown(
                f'<div style="text-align: center;"><img src="data:{saved_logo["Mime_Type"]};base64,{saved_logo["Logo_Base64"]}" style="width: 115px; border-radius: 10px;"></div>',
                unsafe_allow_html=True
            )
        st.markdown("<h3 style='text-align: center;'>🏛️ CAREER ENGLISH INSTITUTE</h3>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🎓 CEFR B1 ACADEMIC GRAMMAR & DISCOURSE SYSTEM</h2>", unsafe_allow_html=True)
        st.divider()
        
        with st.form("login_form"):
            st.subheader("🔐 Control de Acceso Académico")
            input_user = st.text_input("👤 Usuario registrado:")
            input_pass = st.text_input("🔑 Clave de Acceso:", type="password")
            remember_me = st.checkbox("💾 Recordar mi usuario y contraseña en este navegador", value=True)
            submit_login = st.form_submit_button("Ingresar a la Plataforma", type="primary", use_container_width=True)
            
            if submit_login:
                if not input_user or not input_pass:
                    st.warning("⚠️ Ingresa tu Usuario y Clave de Acceso.")
                else:
                    try:
                        with st.spinner("Verificando credenciales en el padrón..."):
                            sheet_padron = get_padron_sheet()
                            registros = sheet_padron.get_all_records()
                            acceso_valido = False
                            
                            for reg in registros:
                                u_db = str(reg.get("Usuario", "")).strip()
                                c_db = str(reg.get("Clave", "")).strip()
                                e_db = str(reg.get("Estatus", "Activo")).strip().lower()
                                r_db = str(reg.get("Rol", "Estudiante")).strip()
                                
                                if u_db.lower() == input_user.strip().lower() and c_db == input_pass.strip():
                                    if e_db == "activo":
                                        st.session_state.authenticated = True
                                        st.session_state.current_user = u_db
                                        st.session_state.user_role = r_db
                                        if remember_me:
                                            payload = json.dumps({"u": u_db, "c": c_db}).encode("utf-8")
                                            st.query_params["auth_token"] = base64.urlsafe_b64encode(payload).decode("utf-8")
                                        else:
                                            st.query_params.clear()
                                        acceso_valido = True
                                        break
                                    else:
                                        st.error("⛔ Tu cuenta se encuentra inactiva. Contacta a CAREER ENGLISH INSTITUTE.")
                                        acceso_valido = None
                                        break
                            
                            if acceso_valido is True:
                                st.rerun()
                            elif acceso_valido is False:
                                st.error("❌ Usuario o Clave incorrectos. Verifica tu registro en el padrón.")
                    except Exception as e:
                        st.error(f"Error al conectar con 'Padron_Estudiantes': {e}")
        
        st.markdown(
            "<div style='text-align: center; color: #777; font-size: 12px; margin-top: 15px;'>© 2026 CAREER ENGLISH INSTITUTE | Todos los derechos reservados.<br>Creado por JACOB ZUMAYA PRIANTI</div>",
            unsafe_allow_html=True
        )
    st.stop()
# --- PARTE 1: BARRA IZQUIERDA (INPUTS DEL ALGORITMO) ---
with st.sidebar:
    st.markdown("### 🏛️ CAREER ENGLISH INSTITUTE")
    st.success(f"👤 **{st.session_state.current_user}** | *{st.session_state.user_role}*")
    st.divider()

    st.header("⚙️ Academic Parameters")
    
    usuario = st.session_state.current_user
    
    st.subheader("1. Context & Characters (Español / English)")
    contexto = st.text_input("Contexto / Lugar / Tema:", placeholder="Ej: En un aeropuerto en Londres / At an airport")
    personas = st.text_input("Personas / Personajes:", placeholder="Ej: Un turista y una azafata / A tourist and a pilot")
    
    st.subheader("2. Subject Matter (Español / English)")
    asunto = st.text_input("Asunto / Materia:", placeholder="Ej: Equipaje perdido / Lost luggage")
    
    st.subheader("3. CEFR B1 Grammar Topics")
    gramatica_b1 = st.selectbox(
        "Selecciona el tema gramatical (B1):",
        [
            "Present Perfect vs. Past Simple",
            "First and Second Conditionals (If clauses)",
            "Modal Verbs of Obligation & Deduction (must, have to, might, could)",
            "Passive Voice (Present & Past)",
            "Relative Clauses (who, which, that, where)",
            "Used to / Would for past habits",
            "Reported Speech (Statements & Questions)",
            "Comparatives and Superlatives (as...as, much more)"
        ]
    )
    
    st.subheader("4. Discourse Mode (Parte 3)")
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
    generar_btn = st.button("🚀 Generate B1 Lesson", type="primary", use_container_width=True)

# --- CABECERA INSTITUCIONAL (LOGO PERMANENTE + TÍTULO + FACULTY BACKEND + QR + SALIR) ---
saved_logo = load_permanent_logo()

default_width = int(saved_logo["Width"]) if saved_logo and saved_logo.get("Width") else 115
default_shape = saved_logo["Shape"] if saved_logo and saved_logo.get("Shape") else "Original"
shape_options = ["Original", "Redondeado", "Circular"]
default_shape_idx = shape_options.index(default_shape) if default_shape in shape_options else 0

is_teacher_desktop = (st.session_state.user_role.strip().lower() in ["teacher", "admin"]) and (not is_mobile)

col_logo, col_title, col_qr, col_exit = st.columns([1.6, 4.9, 2, 1.5])

with col_logo:
    if is_teacher_desktop:
        with st.popover("✏️ Editar Logo", use_container_width=True):
            logo_file = st.file_uploader("Subir imagen (PNG/JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
            logo_width = st.slider("Tamaño (px):", min_value=60, max_value=220, value=default_width, step=5)
            logo_shape = st.radio("Forma:", shape_options, index=default_shape_idx, horizontal=True)
            
            if st.button("💾 Guardar Logo Permanente", type="primary", use_container_width=True):
                b64_to_save = None
                mime_to_save = None
                if logo_file is not None:
                    b64_to_save, mime_to_save = compress_logo_to_base64(logo_file)
                elif saved_logo and saved_logo.get("Logo_Base64"):
                    b64_to_save = saved_logo["Logo_Base64"]
                    mime_to_save = saved_logo["Mime_Type"]
                    
                if b64_to_save:
                    try:
                        with st.spinner("Optimizando y guardando logo..."):
                            save_permanent_logo(b64_to_save, mime_to_save, logo_width, logo_shape)
                            st.success("✅ ¡Logo guardado permanentemente!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar logo: {e}")
                else:
                    st.warning("⚠️ Sube una imagen primero.")
    else:
        logo_file = None
        logo_width = default_width
        logo_shape = default_shape

    active_b64 = None
    active_mime = None
    if logo_file is not None:
        active_b64, active_mime = compress_logo_to_base64(logo_file)
    elif saved_logo and saved_logo.get("Logo_Base64"):
        active_b64 = saved_logo["Logo_Base64"]
        active_mime = saved_logo["Mime_Type"]

    if active_b64:
        radius = "0px"
        if logo_shape == "Redondeado":
            radius = "15px"
        elif logo_shape == "Circular":
            radius = "50%"
        st.markdown(
            f'<div style="text-align: center;"><img src="data:{active_mime};base64,{active_b64}" style="width: {logo_width}px; height: auto; border-radius: {radius}; object-fit: cover;"></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="border: 1px dashed #888; border-radius: 8px; padding: 12px; text-align: center; color: #888; font-size: 11px; width: {logo_width}px; margin: auto;">
                <b>CAREER ENGLISH<br>INSTITUTE</b>
            </div>
            """,
            unsafe_allow_html=True
        )

with col_title:
    st.markdown("#### 🏛️ CAREER ENGLISH INSTITUTE")
    st.title("🎓 CEFR B1 ACADEMIC GRAMMAR & DISCOURSE SYSTEM")
    st.caption("Applied Linguistics & B1 Proficiency Assessment Platform | APA Style Output")

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
        with st.popover("🎓 Faculty Backend", use_container_width=True):
            st.markdown("### 📚 Student Enrollment & Access Registry")
            st.caption("Panel exclusivo del Docente / Teacher")
            
            tab_alta, tab_gestion = st.tabs(["➕ Nuevo Registro", "⚙️ Gestionar Estatus"])
            
            with tab_alta:
                new_est_user = st.text_input("Nombre / Usuario:", key="new_u")
                new_est_pass = st.text_input("Clave de Acceso:", key="new_p")
                new_est_rol = st.selectbox("Rol Académico:", ["Estudiante", "Teacher"], key="new_r")
                if st.button("Registrar en Padrón", type="primary", use_container_width=True):
                    if new_est_user and new_est_pass:
                        try:
                            p_sheet = get_padron_sheet()
                            p_sheet.append_row([new_est_user.strip(), new_est_pass.strip(), new_est_rol, "Activo"])
                            st.success(f"✅ {new_est_user} registrado ({new_est_rol}).")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Completa usuario y clave.")
            
            with tab_gestion:
                try:
                    p_sheet = get_padron_sheet()
                    records_p = p_sheet.get_all_records()
                    if records_p:
                        df_p = pd.DataFrame(records_p)
                        st.dataframe(df_p[["Usuario", "Rol", "Estatus"]], use_container_width=True, hide_index=True)
                        
                        st.markdown("**Activar / Desactivar Acceso:**")
                        user_to_edit = st.selectbox("Seleccionar Usuario:", df_p["Usuario"].tolist(), key="edit_u_sel")
                        new_status = st.radio("Nuevo Estatus:", ["Activo", "Inactivo"], horizontal=True, key="edit_st_rad")
                        
                        if st.button("Actualizar Estatus", use_container_width=True):
                            cell = p_sheet.find(user_to_edit)
                            if cell:
                                p_sheet.update_cell(cell.row, 4, new_status)
                                st.success(f"Estatus de {user_to_edit} cambiado a {new_status}.")
                                st.rerun()
                    else:
                        st.info("No hay registros en el padrón.")
                except Exception as e:
                    st.error(f"Error al cargar padrón: {e}")

    if st.button("🚪 Salir", type="secondary", use_container_width=True):
        st.query_params.clear()
        st.session_state.app_exited = True
        st.session_state.authenticated = False
        st.rerun()

st.divider()
# --- LÓGICA DE GENERACIÓN DE MÁXIMA POTENCIA (PRO-FIRST AUTO-DISCOVERY + FLUX HD) ---
def generar_con_maxima_potencia(client, prompt_contenido, instruccion_sistema=None):
    modelos_potentes = [
        "gemini-3.1-pro-preview",
        "gemini-3.5-pro",
        "gemini-3.8-flash",
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash"
    ]
    try:
        pro_detectados = []
        otros_detectados = []
        for m in client.models.list():
            nombre = m.name.replace("models/", "")
            if "gemini" in nombre and not any(x in nombre for x in ["embedding", "imagen", "aqa", "tts", "audio"]):
                if nombre not in modelos_potentes:
                    if "pro" in nombre or "ultra" in nombre:
                        pro_detectados.append(nombre)
                    else:
                        otros_detectados.append(nombre)
        modelos_potentes = modelos_potentes + sorted(pro_detectados, reverse=True) + sorted(otros_detectados, reverse=True)
    except Exception:
        pass

    ultimo_error = None
    for modelo in modelos_potentes:
        try:
            config = types.GenerateContentConfig(temperature=0.65)
            if instruccion_sistema:
                config = types.GenerateContentConfig(
                    system_instruction=instruccion_sistema,
                    temperature=0.65
                )
            respuesta = client.models.generate_content(
                model=modelo,
                contents=prompt_contenido,
                config=config
            )
            if respuesta and respuesta.text:
                return respuesta.text, modelo
        except Exception as e:
            ultimo_error = e
            continue
            
    raise ultimo_error

# --- FUNCIÓN GENERADORA DE QUIZ EN JSON ESTRUCTURADO ---
def generar_quiz_leccion(texto_leccion, tema_gramatical, evitar_preguntas=None):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    evitar_txt = ""
    if evitar_preguntas:
        evitar_txt = f"IMPORTANT: Create COMPLETELY DIFFERENT questions from these previous ones: {evitar_preguntas}"

    prompt_quiz = f"""
    Based on the following CEFR Level B1 English lesson, create a 5-question multiple-choice quiz in English to evaluate reading comprehension and the target grammar ({tema_gramatical}).
    {evitar_txt}
    
    LESSON TEXT:
    {texto_leccion}
    
    RETURN ONLY VALID JSON (no markdown code blocks, no extra text) with this exact structure:
    [
      {{
        "question": "Question text in English?",
        "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
        "answer": "A) Option 1"
      }}
    ]
    Ensure the "answer" field matches one of the strings in "options" character-for-character.
    """
    raw_resp, _ = generar_con_maxima_potencia(
        client,
        prompt_quiz,
        instruccion_sistema="You are an English assessment specialist. Output strictly valid JSON array only."
    )
    cleaned = raw_resp.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned.strip())

# --- EJECUCIÓN DE GENERACIÓN DE LECCIÓN ---
if generar_btn:
    if "GEMINI_API_KEY" not in st.secrets:
        st.sidebar.error("⚠️ GEMINI_API_KEY no configurada en st.secrets.")
    elif not contexto or not asunto:
        st.sidebar.warning("⚠️ Completa los campos de Contexto y Asunto.")
    else:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        with st.spinner("🧠 Engaging High-Reasoning AI Engine (CEFR B1 Academic Synthesis)..."):
            try:
                system_prompt_pro = (
                    "You are a Senior Applied Linguist and Curriculum Architect at CAREER ENGLISH INSTITUTE. "
                    "Your task is to synthesize high-precision CEFR Level B1 pedagogical texts in strict APA academic format. "
                    "Regardless of whether the user inputs are in Spanish, English, or mixed, you MUST translate, conceptualize, "
                    "and write 100% of your final response in natural, idiomatic, grammatically flawless English. "
                    "Never include any Spanish words in the output."
                )

                prompt_texto = f"""
                Design an academically rigorous CEFR Level B1 English lesson artifact based on the following parameters:
                - Context / Setting: {contexto}
                - Characters / Participants: {personas}
                - Subject / Core Theme: {asunto}
                - Target CEFR B1 Grammar Structure: {gramatica_b1}
                - Required Rhetorical / Discourse Mode: {tipo_texto}
                
                EXECUTION & QUALITY STANDARDS:
                1. **100% English Immersion:** Translate any Spanish concepts seamlessly into natural English. Zero Spanish words allowed.
                2. **CEFR B1 Calibration:** Ensure sentence complexity, connectors, and lexical range align strictly with CEFR Level B1 descriptors.
                3. **Grammar Highlighting:** Integrate at least 6 to 8 natural, clear examples of **{gramatica_b1}** and highlight every single target grammar structure in **bold**.
                4. **APA Academic Structure:** 
                   - Formal Academic Title (Centered/Bold Markdown)
                   - Structured Section Headings
                   - Well-developed body paragraphs tailored to the selected discourse mode ({tipo_texto})
                   - A realistic, properly formatted APA Reference List at the conclusion of the text.
                """
                
                texto_generado, modelo_usado = generar_con_maxima_potencia(
                    client,
                    prompt_texto,
                    instruccion_sistema=system_prompt_pro
                )
                st.session_state.generated_text = texto_generado
                st.session_state.active_model_name = modelo_usado
                
                st.session_state.quiz_data = None
                st.session_state.quiz_graded = False
                st.session_state.quiz_score = None
                st.session_state.quiz_user_answers = {}
                
                img_desc, _ = generar_con_maxima_potencia(
                    client,
                    f"Act as an art director. Write a vivid 20-word visual prompt in English for a modern editorial textbook illustration depicting: setting '{contexto}', characters '{personas}', theme '{asunto}'. Specify lighting, composition, and clean flat-editorial art style. Strictly NO text, letters, or numbers in the image."
                )
                encoded_prompt = urllib.parse.quote(img_desc.strip())
                st.session_state.image_url = f"https://pollinations.ai{encoded_prompt}?model=flux&width=1024&height=640&nologo=true"
                
                clean_text_for_audio = st.session_state.generated_text.replace("*", "").replace("#", "")
                tts = gTTS(text=clean_text_for_audio, lang='en', slow=False)
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.session_state.audio_bytes = audio_fp.getvalue()
                
            except Exception as e:
                st.error(f"⚠️ Error al ejecutar el motor de IA: {e}")
# --- PARTE 2: CENTRO (LECCIÓN APA + QUIZ DE LA LECCIÓN + IMAGEN) ---
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
            st.info("👈 Escribe los datos en Español o Inglés en la barra izquierda y presiona **Generate B1 Lesson**.")

    # --- SECCIÓN DE QUIZ POR LECCIÓN (DEBAJO DE LA LECCIÓN) ---
    if st.session_state.generated_text:
        if st.session_state.quiz_data is None:
            if st.button("📝 Generar Quiz de la Lección (CEFR B1 Assessment)", type="primary", use_container_width=True):
                with st.spinner("Generando preguntas de evaluación sobre la lección..."):
                    try:
                        st.session_state.quiz_data = generar_quiz_leccion(st.session_state.generated_text, gramatica_b1)
                        st.session_state.quiz_graded = False
                        st.session_state.quiz_score = None
                        st.session_state.quiz_user_answers = {}
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo generar el quiz: {e}")
        else:
            with st.container(border=True):
                st.subheader("📝 Lesson Comprehension & Grammar Quiz")
                
                for idx, item in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**{idx + 1}. {item['question']}**")
                    choice = st.radio(
                        label=f"q_{idx}",
                        options=item["options"],
                        key=f"radio_quiz_{idx}",
                        label_visibility="collapsed",
                        index=None
                    )
                    st.session_state.quiz_user_answers[idx] = choice
                    
                    if st.session_state.quiz_graded:
                        if choice == item["answer"]:
                            st.success(f"✅ Correct! ({item['answer']})")
                        else:
                            st.error(f"❌ Incorrect. Your answer: {choice or 'None'} | **Correct answer:** {item['answer']}")
                    st.write("")

                # Botones lado a lado: Calificar y Nuevo Quiz
                col_btn_grade, col_btn_new = st.columns(2)
                with col_btn_grade:
                    if st.button("✅ Calificar Quiz", type="primary", use_container_width=True):
                        correctas = 0
                        total = len(st.session_state.quiz_data)
                        for idx, item in enumerate(st.session_state.quiz_data):
                            if st.session_state.quiz_user_answers.get(idx) == item["answer"]:
                                correctas += 1
                        porcentaje = round((correctas / total) * 100, 1)
                        st.session_state.quiz_score = f"{correctas}/{total} ({porcentaje}%)"
                        st.session_state.quiz_graded = True
                        st.rerun()
                
                with col_btn_new:
                    if st.button("🔄 Nuevo Quiz (Cambiar Preguntas)", type="secondary", use_container_width=True):
                        with st.spinner("Generando nuevas preguntas..."):
                            try:
                                prev_qs = [q["question"] for q in st.session_state.quiz_data]
                                st.session_state.quiz_data = generar_quiz_leccion(
                                    st.session_state.generated_text, gramatica_b1, evitar_preguntas=prev_qs
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
    bottom_container = st.container(height=260, border=True)
    with bottom_container:
        if st.session_state.image_url:
            st.image(st.session_state.image_url, use_container_width=True)
        else:
            st.caption("La imagen ilustrativa aparecerá aquí / The illustrative image will appear here.")
# --- PANEL DERECHO: AUDIO IA + DESCARGA, GRABACIÓN ESTUDIANTE Y GOOGLE SHEETS ---
with col_tools_right:
    # 1. AUDIO DE REFERENCIA (IA) + BOTÓN DESCARGAR AUDIO
    st.subheader("🎧 AI Model Audio")
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        st.download_button(
            label="📥 Descargar Audio (MP3)",
            data=st.session_state.audio_bytes,
            file_name=f"CEI_B1_Audio_{usuario.replace(' ', '_')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )
    else:
        st.caption("Audio will be ready after generation.")
        
    st.divider()

    # 2. GRABACIÓN DEL ESTUDIANTE Y GOOGLE SHEETS
    st.subheader("🎙️ Student Speaking Practice")
    student_audio = st.audio_input("Graba tu lectura aquí:")
    
    if st.button("☁️ Guardar Audio en Google Sheets", use_container_width=True, disabled=(student_audio is None)):
        try:
            with st.spinner("Guardando en Google Sheets..."):
                sheet = get_google_sheet()
                audio_bytes = student_audio.getvalue()
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                if len(audio_b64) > 49000:
                    st.error("⚠️ El audio es muy largo para la celda. Graba un fragmento más corto (10-15 segundos).")
                else:
                    tema_completo = f"{asunto} ({gramatica_b1})" if asunto else gramatica_b1
                    fecha_subida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    fila = [usuario, tema_completo, audio_b64, fecha_subida]
                    sheet.append_row(fila)
                    st.success("✅ ¡Audio guardado en la base de datos!")
        except Exception as e:
            st.error(f"Error al conectar con Google Sheets: {e}")

    # BOTÓN PARA VER AUDIOS GUARDADOS
    if st.button("📂 Ver Audios Guardados", use_container_width=True):
        st.session_state.show_saved_audios = not st.session_state.show_saved_audios

    if st.session_state.show_saved_audios:
        with st.container(height=250, border=True):
            st.markdown("**Historial de Grabaciones:**")
            try:
                sheet = get_google_sheet()
                records = sheet.get_all_records()
                if not records:
                    st.info("Aún no hay grabaciones guardadas.")
                else:
                    df = pd.DataFrame(records)
                    if st.session_state.user_role.strip().lower() not in ["teacher", "admin"]:
                        df = df[df["Usuario"].astype(str).str.lower() == usuario.lower()]
                    
                    if df.empty:
                        st.warning(f"No se encontraron audios para '{usuario}'.")
                    else:
                        for idx, row in df.tail(5).iloc[::-1].iterrows():
                            st.caption(f"👤 **{row['Usuario']}** | 📅 {row['Fecha_de_subida']}")
                            st.caption(f"📘 *{row['Tema']}*")
                            if row.get("Audio"):
                                decoded_audio = base64.b64decode(row["Audio"])
                                st.audio(decoded_audio, format="audio/wav")
                            st.divider()
            except Exception as e:
                st.error(f"No se pudieron cargar los registros: {e}")

    st.divider()
    # 3. EXPORTAR PDF (INCLUYE LECCIÓN + QUIZ Y CALIFICACIÓN OBTENIDA) Y BORRAR
    def create_pdf(text, quiz_items=None, user_ans=None, score=None):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", "B", 14)
        pdf.cell(0, 10, txt="CAREER ENGLISH INSTITUTE", ln=True, align="C")
        pdf.set_font("Times", "B", 11)
        pdf.cell(0, 7, txt="CEFR B1 Academic Grammar & Discourse System", ln=True, align="C")
        pdf.set_font("Times", "I", 10)
        pdf.cell(0, 7, txt=f"Student / Candidate: {usuario} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align="C")
        pdf.ln(5)
        
        # Cuerpo de la lección
        pdf.set_font("Times", size=12)
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, txt=safe_text)
        
        # Sección del Quiz y Calificación (si fue generado)
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
                q_txt = f"{i+1}. {q['question']}".encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, txt=q_txt)
                
                pdf.set_font("Times", size=10)
                for opt in q["options"]:
                    opt_txt = f"   {opt}".encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 6, txt=opt_txt)
                
                u_choice = user_ans.get(i) if user_ans else "No answered"
                ans_line = f"   -> Student Answer: {u_choice or 'None'} | Correct Answer: {q['answer']}"
                pdf.set_font("Times", "I", 10)
                pdf.multi_cell(0, 6, txt=ans_line.encode('latin-1', 'replace').decode('latin-1'))
                pdf.ln(3)

        # Pie de página institucional
        pdf.ln(10)
        pdf.set_font("Times", "I", 10)
        pdf.cell(0, 10, txt="© 2026 CAREER ENGLISH INSTITUTE. Todos los derechos reservados. Creado por JACOB ZUMAYA PRIANTI.", ln=True, align="C")
        return pdf.output(dest='S').encode('latin-1')

    if st.session_state.generated_text:
        pdf_bytes = create_pdf(
            st.session_state.generated_text.replace("*", ""),
            quiz_items=st.session_state.quiz_data,
            user_ans=st.session_state.quiz_user_answers,
            score=st.session_state.quiz_score
        )
        st.download_button(
            label="📥 Descargar PDF (Lección + Quiz)",
            data=pdf_bytes,
            file_name=f"CEI_B1_Academic_Lesson_{usuario.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    else:
        st.button("📥 Descargar PDF (Lección + Quiz)", disabled=True, use_container_width=True)

    st.write("")

    if st.button("🗑️ Borrar Todo", type="secondary", use_container_width=True):
        st.session_state.generated_text = ""
        st.session_state.image_url = None
        st.session_state.audio_bytes = None
        st.session_state.show_saved_audios = False
        st.session_state.quiz_data = None
        st.session_state.quiz_graded = False
        st.session_state.quiz_score = None
        st.session_state.quiz_user_answers = {}
        st.rerun()

# --- PIE DE PÁGINA INSTITUCIONAL Y DERECHOS DE AUTOR ---
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 13px; padding: 10px;">
        © 2026 <b>CAREER ENGLISH INSTITUTE</b> | Todos los derechos reservados.<br>
        Creado y desarrollado por <b>JACOB ZUMAYA PRIANTI</b>
    </div>
    """,
    unsafe_allow_html=True
)
