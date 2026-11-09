import streamlit as st
from openai import OpenAI
from gtts import gTTS
import qrcode
from PIL import Image
from fpdf import FPDF
import io
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="MY ENGLISH GRAMMAR FAN TOOL",
    page_icon="🇬🇧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DETECCIÓN DE DISPOSITIVO (MÓVIL VS ESCRITORIO) ---
# Usamos los headers para detectar si el usuario entra desde un celular
user_agent = st.context.headers.get("User-Agent", "").lower()
is_mobile = any(device in user_agent for device in ["iphone", "android", "ipad", "mobile"])

# --- INICIALIZACIÓN DE ESTADOS (SESSION STATE) ---
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "image_url" not in st.session_state:
    st.session_state.image_url = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "app_exited" not in st.session_state:
    st.session_state.app_exited = False

# --- PANTALLA DE SALIDA ---
if st.session_state.app_exited:
    st.title("👋 Session Ended")
    st.info("Thank you for using MY ENGLISH GRAMMAR FAN TOOL. You may close this tab now.")
    if st.button("Restart Application"):
        st.session_state.app_exited = False
        st.rerun()
    st.stop()

# --- CABECERA Y PARTE 6 (QR DINÁMICO + BOTÓN SALIR) ---
col_title, col_qr, col_exit = st.columns([6, 2, 1])

with col_title:
    st.title("🇬🇧 MY ENGLISH GRAMMAR FAN TOOL")
    st.caption("CEFR Level B1 Adaptive Learning System | APA Style Output")

with col_qr:
    # El QR solo se muestra si NO es un dispositivo móvil (Pantalla del Teacher)
    if not is_mobile:
        # Cambia esta URL por el enlace real de tu app cuando la subas a Streamlit Cloud
        APP_URL = "https://streamlit.app" 
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(APP_URL)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img_qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="📱 Scan for Mobile View", width=110)

with col_exit:
    st.write("") # Espaciador
    if st.button("🚪 Salir", type="secondary", use_container_width=True):
        st.session_state.app_exited = True
        st.rerun()

st.divider()

# --- PARTE 1: BARRA IZQUIERDA (ALIMENTADORES DEL ALGORITMO) ---
with st.sidebar:
    st.header("⚙️ Configuration & Inputs")
    
    # API Key de OpenAI (Se recomienda usar st.secrets en producción)
    api_key = st.text_input("OpenAI API Key:", type="password", help="Enter your OpenAI key to power the AI.")
    
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
    if not api_key:
        st.sidebar.error("⚠️ Please enter your OpenAI API Key first.")
    elif not contexto or not asunto:
        st.sidebar.warning("⚠️ Please fill in the Context and Subject fields.")
    else:
        client = OpenAI(api_key=api_key)
        
        with st.spinner("Generating CEFR B1 content, audio, and illustration..."):
            # 1. Generación de Texto en formato APA
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
            2. Structure the output following APA Style guidelines (Running head/Title, Clear Headings, Double-spaced academic tone, indented paragraphs simulation, and a mock/placeholder APA Reference list at the bottom based on the topic).
            3. Note: Apply latest APA academic standards (APA 7th/8th edition conventions).
            """
            
            response_text = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt_texto}],
                temperature=0.7
            )
            st.session_state.generated_text = response_text.choices[0].message.content
            
            # 2. Generación de Imagen Ilustrativa (DALL-E 3)
            prompt_imagen = f"Educational illustration for an English lesson. Scene: {contexto}. Characters: {personas}. Topic: {asunto}. Clean, modern textbook illustration style, no text inside the image."
            response_img = client.images.generate(
                model="dall-e-3",
                prompt=prompt_imagen,
                size="1024x1024",
                quality="standard",
                n=1
            )
            st.session_state.image_url = response_img.data[0].url
            
            # 3. Generación de Audio (Parte 4)
            # Limpiamos asteriscos de markdown para que el lector de voz no los lea
            clean_text_for_audio = st.session_state.generated_text.replace("*", "").replace("#", "")
            tts = gTTS(text=clean_text_for_audio, lang='en', slow=False)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.session_state.audio_bytes = audio_fp.getvalue()

# --- PARTE 2: CENTRO (DIVIDIDO EN DOS VERTICALMENTE: ARRIBA MÁS ALTA QUE ABAJO) ---
col_main_center, col_tools_right = st.columns([4, 1])

with col_main_center:
    # SECCIÓN SUPERIOR (Más alta - Contenedor con altura fija de 450px y scroll)
    st.subheader("📄 Generated Content (APA Format)")
    top_container = st.container(height=450, border=True)
    with top_container:
        if st.session_state.generated_text:
            st.markdown(st.session_state.generated_text)
        else:
            st.info("👈 Configure the parameters on the left sidebar and click **Generate B1 Lesson** to start.")

    # SECCIÓN INFERIOR (Más baja - Imagen Ilustrativa)
    st.subheader("🖼️ Visual Context")
    bottom_container = st.container(height=280, border=True)
    with bottom_container:
        if st.session_state.image_url:
            st.image(st.session_state.image_url, use_container_width=True)
        else:
            st.caption("The illustrative image will appear here once generated.")

# --- PANEL DERECHO: PARTE 4 (AUDIO) Y PARTE 5 (BORRAR Y PDF) ---
with col_tools_right:
    st.subheader("🎧 Audio & Export")
    
    # PARTE 4: Reproductor de Audio
    st.markdown("**Listening Practice:**")
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
    else:
        st.caption("Audio will be ready after generation.")
        
    st.divider()
    
    # PARTE 5: Función para generar PDF
    def create_pdf(text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", size=12) # Times New Roman es estándar APA
        # Codificación segura para caracteres básicos en FPDF
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

    st.write("") # Espaciador

    # PARTE 5: Botón de Borrar
    if st.button("🗑️ Borrar Todo", type="secondary", use_container_width=True):
        st.session_state.generated_text = ""
        st.session_state.image_url = None
        st.session_state.audio_bytes = None
        st.rerun()
