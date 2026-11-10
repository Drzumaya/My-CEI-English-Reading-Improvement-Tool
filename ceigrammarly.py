import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import qrcode
from fpdf import FPDF
import io
import base64
import urllib.parse
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="MY ENGLISH GRAMMAR FAN TOOL - Career English Institute",
    page_icon="🇬🇧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONEXIÓN A GOOGLE SHEETS (AUDIOS DE ESTUDIANTES) ---
def get_google_sheet():
    scopes = [
        "https://googleapis.com",
        "https://googleapis.com"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client.open("English_Grammar_Audios").sheet1

# --- FUNCIONES DE LOGO PERMANENTE EN GOOGLE SHEETS ---
@st.cache_data(ttl=300)
def load_permanent_logo():
    try:
        scopes = [
            "https://googleapis.com",
            "https://googleapis.com"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet_logo = client.open("English_Grammar_Audios").worksheet("Config_Logo")
        records = sheet_logo.get_all_records()
        if records:
            return records[-1]
    except Exception:
        pass
    return None

def save_permanent_logo(b64_str, mime, width, shape):
    scopes = [
        "https://googleapis.com",
        "https://googleapis.com"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet_logo = client.open("English_Grammar_Audios").worksheet("Config_Logo")
    sheet_logo.clear()
    sheet_logo.append_row(["Logo_Base64", "Mime_Type", "Width", "Shape"])
    sheet_logo.append_row([b64_str, mime, width, shape])
    load_permanent_logo.clear()

# --- DETECCIÓN DE DISPOSITIVO (MÓVIL VS ESCRITORIO) ---
user_agent = st.context.headers.get("User-Agent", "").lower()
is_mobile = any(device in user_agent for device in ["iphone", "android", "ipad", "mobile"])

# --- INICIALIZACIÓN DE ESTADOS ---
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

# --- PANTALLA DE SALIDA ---
if st.session_state.app_exited:
    st.title("👋 Session Ended")
    st.info("Thank you for using MY ENGLISH GRAMMAR FAN TOOL by CAREER ENGLISH INSTITUTE. You may close this tab now.")
    st.caption("© 2026 CAREER ENGLISH INSTITUTE. Todos los derechos reservados. Creado por JACOB ZUMAYA PRIANTI.")
    if st.button("Restart Application"):
        st.session_state.app_exited = False
        st.rerun()
    st.stop()
# --- PARTE 1: BARRA IZQUIERDA (LIMPIA, SOLO INPUTS DEL ALGORITMO) ---
with st.sidebar:
    st.markdown("### 🏛️ CAREER ENGLISH INSTITUTE")
    st.divider()

    st.header("⚙️ Configuration & Inputs")
    
    usuario = st.text_input("👤 Usuario (Nombre del Estudiante):", placeholder="Ej: Ana López")
    
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

# --- CABECERA INSTITUCIONAL (LOGO PERMANENTE + EDICIÓN IN-SITU + TÍTULO + QR + SALIR) ---
saved_logo = load_permanent_logo()

default_width = int(saved_logo["Width"]) if saved_logo and saved_logo.get("Width") else 115
default_shape = saved_logo["Shape"] if saved_logo and saved_logo.get("Shape") else "Original"
shape_options = ["Original", "Redondeado", "Circular"]
default_shape_idx = shape_options.index(default_shape) if default_shape in shape_options else 0

col_logo, col_title, col_qr, col_exit = st.columns([1.6, 4.9, 2, 1.5])

with col_logo:
    with st.popover("✏️ Editar Logo", use_container_width=True):
        logo_file = st.file_uploader("Subir imagen nueva (PNG/JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
        logo_width = st.slider("Tamaño (px):", min_value=60, max_value=220, value=default_width, step=5)
        logo_shape = st.radio("Forma:", shape_options, index=default_shape_idx, horizontal=True)
        
        if st.button("💾 Guardar Logo Permanente", type="primary", use_container_width=True):
            b64_to_save = None
            mime_to_save = None
            
            if logo_file is not None:
                b64_to_save = base64.b64encode(logo_file.getvalue()).decode("utf-8")
                mime_to_save = logo_file.type
            elif saved_logo and saved_logo.get("Logo_Base64"):
                b64_to_save = saved_logo["Logo_Base64"]
                mime_to_save = saved_logo["Mime_Type"]
                
            if b64_to_save:
                if len(b64_to_save) > 49000:
                    st.error("⚠️ La imagen pesa demasiado (máx. 35 KB). Comprímela antes de subirla.")
                else:
                    try:
                        with st.spinner("Fijando logo..."):
                            save_permanent_logo(b64_to_save, mime_to_save, logo_width, logo_shape)
                            st.success("✅ ¡Logo guardado permanentemente!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar en Config_Logo: {e}")
            else:
                st.warning("⚠️ Sube una imagen primero.")

    active_b64 = None
    active_mime = None
    if logo_file is not None:
        active_b64 = base64.b64encode(logo_file.getvalue()).decode("utf-8")
        active_mime = logo_file.type
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
    st.title("🇬🇧 MY ENGLISH GRAMMAR FAN TOOL")
    st.caption("CEFR Level B1 Adaptive Learning System | APA Style Output")

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
    st.write("")
    if st.button("🚪 Salir", type="secondary", use_container_width=True):
        st.session_state.app_exited = True
        st.rerun()

st.divider()
# --- LÓGICA DE GENERACIÓN GRATUITA (GEMINI + POLLINATIONS.AI) ---
if generar_btn:
    if "GEMINI_API_KEY" not in st.secrets:
        st.sidebar.error("⚠️ GEMINI_API_KEY no configurada en st.secrets.")
    elif not contexto or not asunto:
        st.sidebar.warning("⚠️ Completa los campos de Contexto y Asunto.")
    else:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        with st.spinner("Translating inputs and generating CEFR B1 content in English..."):
            prompt_texto = f"""
            You are an expert English teacher at CAREER ENGLISH INSTITUTE specializing in CEFR Level B1.
            The user may provide the input parameters in Spanish, English, or a mix of both.
            
            USER INPUTS (Translate/adapt internally to English if written in Spanish):
            - Context/Place: {contexto}
            - Characters: {personas}
            - Subject/Topic: {asunto}
            - Target B1 Grammar: {gramatica_b1}
            - Discourse Format: {tipo_texto}
            
            STRICT OUTPUT RULES:
            1. LANGUAGE: Your ENTIRE output MUST be written 100% in natural, accurate English. Do NOT include a single word of Spanish anywhere in the title, headings, body, or references.
            2. CEFR B1 LEVEL: Adapt all vocabulary and sentence structures strictly to CEFR Level B1. Highlight the target grammar structures ({gramatica_b1}) in **bold**.
            3. APA FORMAT: Structure the output following APA Style conventions (Academic Title in English, Clear Headings, formal/semi-formal tone, and a simulated APA Reference list in English at the end).
            """
            
            response_text = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_texto,
                config=types.GenerateContentConfig(
                    system_instruction="You are a strict English-only CEFR B1 content generator. Regardless of the input language (Spanish or English), you always output 100% in English.",
                    temperature=0.7
                )
            )
            st.session_state.generated_text = response_text.text
            
            # Generación de Imagen Ilustrativa Gratuita (Pollinations.ai)
            img_prompt_resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Write a short 15-word image description in English for an educational textbook illustration about: setting '{contexto}', characters '{personas}', topic '{asunto}'. Flat vector style, no text in image."
            )
            encoded_prompt = urllib.parse.quote(img_prompt_resp.text.strip())
            st.session_state.image_url = f"https://pollinations.ai{encoded_prompt}?width=800&height=500&nologo=true"
            
            # Generación de Audio Gratuita (gTTS en Inglés)
            clean_text_for_audio = st.session_state.generated_text.replace("*", "").replace("#", "")
            tts = gTTS(text=clean_text_for_audio, lang='en', slow=False)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.session_state.audio_bytes = audio_fp.getvalue()

# --- PARTE 2: CENTRO (DIVIDIDO VERTICALMENTE: ARRIBA MÁS ALTA QUE ABAJO) ---
col_main_center, col_tools_right = st.columns([7, 3.5])

with col_main_center:
    st.subheader("📄 Generated Content (APA Format - 100% English)")
    top_container = st.container(height=450, border=True)
    with top_container:
        if st.session_state.generated_text:
            st.markdown(st.session_state.generated_text)
        else:
            st.info("👈 Escribe los datos en Español o Inglés en la barra izquierda y presiona **Generate B1 Lesson**.")

    st.subheader("🖼️ Visual Context")
    bottom_container = st.container(height=280, border=True)
    with bottom_container:
        if st.session_state.image_url:
            st.image(st.session_state.image_url, use_container_width=True)
        else:
            st.caption("La imagen ilustrativa aparecerá aquí / The illustrative image will appear here.")
# --- PANEL DERECHO: AUDIO IA, GRABACIÓN ESTUDIANTE, GOOGLE SHEETS Y PDF ---
with col_tools_right:
    # 1. AUDIO DE REFERENCIA (IA)
    st.subheader("🎧 AI Model Audio")
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
    else:
        st.caption("Audio will be ready after generation.")
        
    st.divider()

    # 2. GRABACIÓN DEL ESTUDIANTE Y GOOGLE SHEETS
    st.subheader("🎙️ Student Speaking Practice")
    student_audio = st.audio_input("Graba tu lectura aquí:")
    
    if st.button("☁️ Guardar Audio en Google Sheets", use_container_width=True, disabled=(student_audio is None)):
        if not usuario:
            st.warning("⚠️ Por favor escribe tu Usuario en la barra izquierda antes de guardar.")
        else:
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
                        
                        # Columnas: Usuario | Tema | Audio | Fecha_de_subida
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
                    if usuario:
                        df = df[df["Usuario"].astype(str).str.contains(usuario, case=False, na=False)]
                    
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
    
    # 3. EXPORTAR PDF Y BORRAR
    def create_pdf(text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", "B", 14)
        pdf.cell(0, 10, txt="CAREER ENGLISH INSTITUTE - CEFR B1 Lesson", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Times", size=12)
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, txt=safe_text)
        
        pdf.ln(10)
        pdf.set_font("Times", "I", 10)
        pdf.cell(0, 10, txt="© 2026 CAREER ENGLISH INSTITUTE. Todos los derechos reservados. Creado por JACOB ZUMAYA PRIANTI.", ln=True, align="C")
        return pdf.output(dest='S').encode('latin-1')

    if st.session_state.generated_text:
        pdf_bytes = create_pdf(st.session_state.generated_text.replace("*", ""))
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_bytes,
            file_name="Career_English_Institute_B1_Lesson.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    else:
        st.button("📥 Descargar PDF", disabled=True, use_container_width=True)

    st.write("")

    if st.button("🗑️ Borrar Todo", type="secondary", use_container_width=True):
        st.session_state.generated_text = ""
        st.session_state.image_url = None
        st.session_state.audio_bytes = None
        st.session_state.show_saved_audios = False
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
