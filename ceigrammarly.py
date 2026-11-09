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
    page_title="MY ENGLISH GRAMMAR FAN TOOL",
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
    st.info("Thank you for using MY ENGLISH GRAMMAR FAN TOOL. You may close this tab now.")
    if st.button("Restart Application"):
        st.session_state.app_exited = False
        st.rerun()
    st.stop()
# --- CABECERA Y PARTE 6 (QR DINÁMICO + BOTÓN SALIR) ---
col_title, col_qr, col_exit = st.columns([6, 2, 1.5])

with col_title:
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

# --- PARTE 1: BARRA IZQUIERDA (ALIMENTADORES DEL ALGORITMO) ---
with st.sidebar:
    st.header("⚙️ Configuration & Inputs")
    
    usuario = st.text_input("👤 Usuario (Nombre del Estudiante):", placeholder="e.g., Ana López")
    
    st.subheader("1. Context & Characters")
    contexto = st.text_input("Contexto / Lugar / Tema:", placeholder="e.g., At a busy airport in London")
    personas = st.text_input("Personas / Personajes:", placeholder="e.g., A tourist and a flight attendant")
    
    st.subheader("2. Subject Matter")
    asunto = st.text_input("Asunto / Materia:", placeholder="e.g., Lost luggage and travel insurance")
    
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
# --- LÓGICA DE GENERACIÓN DE IA ---
if generar_btn:
    if "OPENAI_API_KEY" not in st.secrets:
        st.sidebar.error("⚠️ API Key no configurada en st.secrets.")
    elif not contexto or not asunto:
        st.sidebar.warning("⚠️ Completa los campos de Contexto y Asunto.")
    else:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        with st.spinner("Generating CEFR B1 content, audio, and illustration..."):
            prompt_texto = f"""
            Act as an expert English teacher specializing in the CEFR B1 level.
            Create an educational text in English based on these parameters:
            - Context/Place: {contexto}
            - Characters: {personas}
            - Subject/Topic: {asunto}
            - Target B1 Grammar: {gramatica_b1}
            - Format/Mode: {tipo_texto}
            
            STRICT FORMATTING RULES:
            1. Write strictly at a CEFR B1 level. Highlight the target grammar structures in **bold**.
            2. Structure the output following APA Style guidelines (Running head/Title, Clear Headings, academic tone, and a mock APA Reference list at the bottom).
            """
            
            response_text = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt_texto}],
                temperature=0.7
            )
            st.session_state.generated_text = response_text.choices.message.content
            
            prompt_imagen = f"Educational illustration for an English lesson. Scene: {contexto}. Characters: {personas}. Topic: {asunto}. Clean, modern textbook illustration style, no text inside the image."
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

# --- PARTE 2: CENTRO Y PANEL DERECHO ---
col_main_center, col_tools_right = st.columns([7, 3.5])

with col_main_center:
    st.subheader("📄 Generated Content (APA Format)")
    top_container = st.container(height=450, border=True)
    with top_container:
        if st.session_state.generated_text:
            st.markdown(st.session_state.generated_text)
        else:
            st.info("👈 Configure the parameters on the left sidebar and click **Generate B1 Lesson** to start.")

    st.subheader("🖼️ Visual Context")
    bottom_container = st.container(height=280, border=True)
    with bottom_container:
        if st.session_state.image_url:
            st.image(st.session_state.image_url, use_container_width=True)
        else:
            st.caption("The illustrative image will appear here once generated.")
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
        pdf.set_font("Times", size=12)
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, txt=safe_text)
        return pdf.output(dest='S').encode('latin-1')

    if st.session_state.generated_text:
        pdf_bytes = create_pdf(st.session_state.generated_text.replace("*", ""))
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_bytes,
            file_name="English_B1_Lesson_APA.pdf",
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
