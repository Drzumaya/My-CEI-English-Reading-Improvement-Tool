import streamlit as st

# ==============================================================================
# 🧩 PARTE 1: CONFIGURACIÓN GENERAL, PUERTO DE SEGURIDAD Y LOGIN (PASSWORD)
# ==============================================================================
st.set_page_config(
    page_title="Quality Inspector - English Practice Tool",
    page_icon="🚗",
    layout="wide"
)

# Inicializar estados de sesión para el bloqueo de seguridad involuntario
if "training_authenticated" not in st.session_state:
    st.session_state.training_authenticated = False

# Definición de la clave de acceso maestra para el personal de planta
PASSWORD_MAESTRA = "QUALITY2026"

# Ventana emergente (Dialog) para validar las credenciales del inspector
@st.dialog("🔒 Autenticación de Entrada al Simulador")
def popup_seguridad_entrenamiento():
    st.write("Por favor, introduce la clave de acceso autorizada para el rol de Inspector de Calidad.")
    input_pass = st.text_input("Clave de Acceso Técnica:", type="password", key="training_pass_field").strip()
    
    if st.button("Validar Código de Planta", type="primary", use_container_width=True, key="btn_validate_training"):
        if input_pass == PASSWORD_MAESTRA:
            st.session_state.training_authenticated = True
            st.success("¡Acceso correcto! Inicializando glosarios técnicos...")
            st.rerun()
        else:
            st.error("❌ Clave incorrecta. Solicita el código al supervisor de entrenamiento.")

# Bloqueo total de la interfaz si el usuario no se ha autenticado previamente
if not st.session_state.training_authenticated:
    st.info("👋 Bienvenido al Simulador de Pronunciación y Práctica de Inglés Técnico.")
    st.markdown("### Módulo de Entrenamiento Restringido")
    st.write("Este portal contiene lineamientos de comunicación alineados a las normas IATF 16949.")
    
    if st.button("🔐 Abrir Terminal de Autenticación", type="primary", key="btn_open_gate"):
        popup_seguridad_entrenamiento()
    st.stop()  # Aborta la lectura del resto del código hasta que se inicie sesión con éxito
# ==============================================================================
# 🧩 PARTE 2: NÚCLEO DE PRONUNCIACIÓN (MOTOR JAVASCRIPT TEXT-TO-SPEECH NATIVO)
# ==============================================================================
def crear_boton_practica(texto_a_reproducir, id_unico):
    """
    Inyecta un botón HTML5/JS que utiliza el motor TTS nativo del dispositivo del estudiante.
    Garantiza que el audio suene de inmediato al hacer clic sin cargar archivos de red externos.
    """
    # Escapar comillas para evitar rupturas en la cadena de texto de JavaScript
    texto_escapado = texto_a_reproducir.replace("'", "\\'").replace('"', '\\"')
    
    html_control = f"""
    <button onclick="speakPhrases('{texto_escapado}')" style="
        background-color: #1e88e5; 
        color: white; 
        border: none; 
        padding: 6px 14px; 
        font-size: 13px; 
        font-weight: bold;
        border-radius: 20px; 
        cursor: pointer; 
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        display: inline-flex;
        align-items: center;
        gap: 5px;
        margin: 4px 0px;">
        🔊 Listen & Practice
    </button>
    <script>
    if (typeof window.speakPhrases !== 'function') {{
        window.speakPhrases = function(text) {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel(); // Detener cualquier reproducción previa activa
                var msg = new SpeechSynthesisUtterance();
                msg.text = text;
                msg.lang = 'en-US'; // Forzar pronunciación técnica americana nativa
                msg.rate = 0.85;    // Velocidad ligeramente reducida para facilitar el aprendizaje
                msg.volume = 1.0;
                window.speechSynthesis.speak(msg);
            }} else {{
                alert('Tu navegador no soporta reproducción de voz nativa. Intente usando Google Chrome.');
            }}
        }};
    }}
    </script>
    """
    st.markdown(html_control, unsafe_allow_html=True)
# ==============================================================================
# 🧩 PARTE 3: INTERFAZ GRÁFICA, MENÚS Y CONTENIDO DEL GLOSARIO (IATF 16949)
# ==============================================================================
# Sistema en la barra lateral para cerrar sesión de forma segura y borrar caché
if st.sidebar.button("🚪 Cerrar Sesión de Entrenamiento", type="secondary", key="btn_logout_training"):
    st.session_state.training_authenticated = False
    st.rerun()

st.sidebar.markdown("---")
seccion = st.sidebar.radio(
    "📂 Selecciona la Sección del Documento:",
    [
        "I. Objective & Scope", 
        "II-A. Written English (Reports)", 
        "II-B. Spoken English (Floor Alerts)", 
        "II-C. Audits & Standards (IATF)", 
        "II-D. Technical Glossary & Tools",
        "💡 Supervisor Feedback Version (Casual)"
    ]
)

# Encabezado fijo superior una vez desbloqueada la plataforma
st.title("🚗 Quality Inspector - Pronunciation & Training Simulator")
st.subheader("IATF 16949 Standards & Shop Floor Communication Practice")
st.markdown("---")

# --- RENDERIZADO DINÁMICO DE CONTENIDO ---

if seccion == "I. Objective & Scope":
    st.header("I. OBJECTIVE & SCOPE")
    parrafo_1 = "The purpose of this assessment is to identify specific language gaps and technical English competencies required by the Quality Inspector role."
    parrafo_2 = "The insights gathered will align language training with IATF 16949 standards, minimize operational risk, and optimize shop floor communication."
    
    with st.container(border=True):
        st.write(f"*{parrafo_1}*")
        crear_boton_practica(parrafo_1, "p1")
    with st.container(border=True):
        st.write(f"*{parrafo_2}*")
        crear_boton_practica(parrafo_2, "p2")

elif seccion == "II-A. Written English (Reports)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("A. WRITTEN ENGLISH: REPORTS & TRACEABILITY")
    preguntas_escritas = [
        "Which official quality documents do you require me to write more clearly in English (e.g., Non-Conformance Reports (NCR), 8D Reports, Quality Alerts, or shift handovers)?",
        "What specific sections of the 8D report (like Containment Actions or Root Cause Analysis) should I practice writing to make my explanations clearer?",
        "When I enter defect codes or dimensions into our shop floor system, what are the most common English vocabulary or formatting mistakes you notice?",
        "When I email global engineering teams, suppliers, or OEM customers about part deviations, what areas of my written English need improvement?"
    ]
    for i, pregunta in enumerate(preguntas_escritas, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {pregunta}**")
            crear_boton_practica(pregunta, f"written_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_written_{i}")

elif seccion == "II-B. Spoken English (Floor Alerts)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("B. SPOKEN ENGLISH: FLOOR ALERTS & PUSHBACK")
    preguntas_habladas = [
        "What specific technical vocabulary do you want me to master when describing physical automotive defects during a teardown or inspection (e.g., burrs, flash, porosity, mismatch, cross-threading, orange peel)?",
        "How can I improve my English communication when I need to urgently report a critical quality issue or trigger a Line Down / Hold status?",
        "What specific phrases should I use to confidently defend my quality decisions in English when production supervisors pressure me to release a suspect batch?",
        "What key terms or metrics should I focus on using during our daily Gemba Walks or production meetings to report quality data and scrap percentages?"
    ]
    for i, pregunta in enumerate(preguntas_habladas, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {pregunta}**")
            crear_boton_practica(pregunta, f"spoken_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_spoken_{i}")

elif seccion == "II-C. Audits & Standards (IATF)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("C. AUDITS & STANDARDS (IATF 16949)")
    preguntas_auditoria = [
        "What specific questions from external auditors (like IATF, or clients like Ford, GM, Toyota) do you think I need to practice answering verbally on the shop floor?",
        "How can I improve my explanation of our company’s quality policy and gauge calibration procedures when I am audited in English?",
        "When reading or discussing engineering blueprints, GD&T symbols, and Control Plans in English, what technical terms do I struggle with most?"
    ]
    for i, pregunta in enumerate(preguntas_auditoria, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {pregunta}**")
            crear_boton_practica(pregunta, f"audit_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_audit_{i}")

elif seccion == "II-D. Technical Glossary & Tools":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("D. TECHNICAL GLOSSARY & INDUSTRY ACRONYMS")
    preguntas_glosario = [
        "Which automotive quality acronyms do you need me to explain and speak about more comfortably (e.g., PPAP, APQP, FMEA, MSA, SPC, Poka-Yoke)?",
        "Are there specific OEM portals or English software tools where you want me to improve my data entry and navigation skills?"
    ]
    for i, pregunta in enumerate(preguntas_glosario, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {pregunta}**")
            crear_boton_practica(pregunta, f"glossary_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_glossary_{i}")
    st.markdown("---")
    st.subheader("III. APPROVAL & SIGN-OFF")
    st.caption("The signatures below confirm that the communication gaps outlined above will be used to develop a targeted English training curriculum for the employee.")

elif seccion == "💡 Supervisor Feedback Version (Casual)":
    st.header("💬 MY ENGLISH GROWTH PLAN: FEEDBACK QUESTIONS FOR MY SUPERVISOR")
    st.info("💡 Casual Shop Floor / Coffee Meeting Version")
    frase_intro = "Hi Boss, I want to make sure my English skills are fully supporting our team's goals and keeping the line running smoothly. Let's use this quick checklist to find out exactly where I can improve my written and spoken English."
    
    with st.container(border=True):
        st.markdown(f'**Introductory Icebreaker:** "{frase_intro}"')
        crear_boton_practica(frase_intro, "intro_boss")
        
    st.markdown("#### Checklists to Practice with your Supervisor:")
    v_written = [
        "Which official reports do you need me to write better in English? (NCRs, 8D Reports, Quality Alerts, Shift Handovers)",
        "Any specific sections of the 8D report I should practice writing?",
        "What mistakes do you notice when I enter defect data into the system?",
        "How can I improve my emails to global teams, suppliers, or customers?"
    ]
    v_spoken = [
        "What specific defect words do I need to learn? (burrs, flash, porosity, mismatch, orange peel...)",
        "How can I sound more urgent when triggering a Line Down or Hold status?",
        "What phrases should I use when production managers challenge my quality decisions?",
        "What key metrics should I practice talking about during Gemba Walks?"
    ]
    v_audit = [
        "What specific questions from auditors (IATF, Ford, GM, Toyota) should I practice?",
        "Can I explain our quality policy and tool calibration clearly enough?",
        "What terms do I trip over when reading blueprints, GD&T, or Control Plans?"
    ]
    v_tools = [
        "Which acronyms do I need to explain better? (PPAP, FMEA, SPC, Poka-Yoke...)",
        "Which English customer portals or software tools do I need to master?"
    ]

    categorias = [
        ("📝 MY WRITTEN ENGLISH (Reports & Emails)", v_written, "c_wr"),
        ("🗣️ MY SPOKEN ENGLISH (Shop Floor & Team Meetings)", v_spoken, "c_sp"),
        ("🔍 AUDITS & TECHNICAL DATA (IATF 16949)", v_audit, "c_au"),
        ("🛠️ GLOSSARY & SOFTWARE TOOLS", v_tools, "c_tl")
    ]
    for titulo, lista, prefijo in categorias:
        with st.expander(titulo, expanded=True):
            for idx, item in enumerate(lista):
                st.markdown(f"• {item}")
                crear_boton_practica(item, f"{prefijo}_{idx}")
            st.text_area("📝 Boss's Feedback & Examples:", key=f"boss_feed_{prefijo}", height=70)

    st.markdown("---")
    st.subheader("🎯 TOP 3. PRIORITY AREAS TO START TRAINING NEXT WEEK:")
    st.text_input("1.", key="prio_1")
    st.text_input("2.", key="prio_2")
    st.text_input("3.", key="prio_3")
    
    gracias = "Thanks for your time and feedback! Let's touch base again in 4 weeks to track progress."
    st.markdown(f'*{gracias}*')
    crear_boton_practica(gracias, "thanks_footer")
