import streamlit as st
from openai import OpenAI
from gtts import gTTS
import qrcode
from fpdf import FPDF
import io
import base64
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

# --- CONEXIÓN A GOOGLE SHEETS ---
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
# --- PARTE 1: BARRA IZQUIERDA (LOGO EDITABLE E INPUTS EN ESPAÑOL/INGLÉS) ---
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

# --- CABECERA INSTITUCIONAL (LOGO EDITABLE IN-SITU + TÍTULO + QR + SALIR) ---
col_logo, col_title, col_qr, col_exit = st.columns([1.6, 4.9, 2, 1.5])

with col_logo:
    # Menú flotante (popover) para editar o subir el logo directamente en su lugar
    with st.popover("✏️ Editar Logo", use_container_width=True):
        logo_file = st.file_uploader("Subir imagen (PNG/JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
        logo_width = st.slider("Tamaño (px):", min_value=60, max_value=220, value=115, step=5)
        logo_shape = st.radio("Forma:", ["Original", "Redondeado", "Circular"], horizontal=True)

    # Renderizado del logo en su posición junto al título
    if logo_file is not None:
        b64_logo = base64.b64encode(logo_file.getvalue()).decode("utf-8")
        mime_type = logo_file.type
        radius = "0px"
        if logo_shape == "Redondeado":
            radius = "15px"
        elif logo_shape == "Circular":
            radius = "50%"
            
        st.markdown(
            f'<div style="text-align: center;"><img src="data:{mime_type};base64,{b64_logo}" style="width: {logo_width}px; height: auto; border-radius: {radius}; object-fit: cover;"></div>',
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
        APP_URL = "https://streamlit.app" 
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


# --- LÓGICA DE GENERACIÓN DE IA (INPUT ES/EN -> OUTPUT 100% EN) ---
if generar_btn:
    if "OPENAI_API_KEY" not in st.secrets:
        st.sidebar.error("⚠️ API Key no configurada en st.secrets.")
    elif not contexto or not asunto:
        st.sidebar.warning("⚠️ Completa los campos de Contexto y Asunto.")
    else:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
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
            
            response_text = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strict English-only CEFR B1 content generator. Regardless of the input language (Spanish or English), you always output 100% in English."},
                    {"role": "user", "content": prompt_texto}
                ],
                temperature=0.7
            )
            st.session_state.generated_text = response_text.choices.message.content
            
            prompt_imagen = (
                f"Educational textbook illustration for an English class. "
                f"Translate this scene concept into visuals: Setting is '{contexto}', "
                f"characters are '{personas}', action/theme is '{asunto}'. "
                f"Clean, modern, colorful flat-vector educational style. NO text, letters, or words inside the image."
            )
            response_img = client.images.generate(
                model="dall-e-3",
                prompt=prompt_imagen,
                size="1024x1024",
                quality="standard",
                n=1
            )
            st.session_state.image_url = response_img.data.url
            
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
        
        # Pie de página con derechos reservados en el PDF
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
