import streamlit as st
import re

# ==============================================================================
# SUBPARTE 1: CONFIGURACIÓN GENERAL DE LA PLATAFORMA
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
# ==============================================================================
# SUBPARTE 2: PUERTO DE SEGURIDAD Y LOGIN (PASSWORD DIALOG)
# ==============================================================================
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
import requests
from PIL import Image
from io import BytesIO

# ==============================================================================
# SUBPARTE 3: MOTOR DE AUDIO HUMANO PREMIUM (VOCES DISTINTAS HOMBRE / MUJER US)
# ==============================================================================
def crear_boton_practica(texto_en_ingles, texto_en_espanol, id_unico, url_imagen=None):
    """
    Descarga la imagen internamente para evitar bloqueos, mapea colores gramaticales
    e inyecta un motor de voz humano real que alterna entre hombre y mujer según el ID.
    """
    if url_imagen:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            respuesta = requests.get(url_imagen, headers=headers, timeout=5)
            if respuesta.status_code == 200:
                imagen_binaria = Image.open(BytesIO(respuesta.content))
                st.image(imagen_binaria, width=420)
        except Exception:
            st.caption("📷 *[Ilustración técnica de apoyo]*")
        
    st.markdown(f"📖 **English:** {texto_en_ingles}", unsafe_allow_html=True)
    st.markdown(f"🔹 **Español:** {texto_en_espanol}", unsafe_allow_html=True)
    
    # Limpiar las etiquetas de color HTML para el lector de voz
    texto_plano = re.sub(r'<[^>]+>', '', texto_en_ingles)
    texto_escapado = texto_plano.replace("'", "\\'").replace('"', '\\"')
    
    # Determinar género basado en el hash o texto del id_unico para que sea consistente
    # IDs que terminan en número par o letras específicas usarán voz de mujer, otros de hombre
    es_par = any(char in id_unico for char in ['0', '2', '4', '6', '8', 'p', 'boss', 'footer'])
    genero_objetivo = "female" if es_par else "male"
    label_genero = "👩 Female Voice" if genero_objetivo == "female" else "👨 Male Voice"
    
    codigo_html = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <button onclick="playHumanVoice()" style="
            background-color: #1e88e5; 
            color: white; 
            border: none; 
            padding: 7px 15px; 
            font-size: 13px; 
            font-weight: bold;
            border-radius: 20px; 
            cursor: pointer; 
            box-shadow: 0px 2px 4px rgba(0,0,0,0.15);
            font-family: sans-serif;
            margin-top: 5px;
            margin-bottom: 15px;
            display: inline-flex;
            align-items: center;
            gap: 6px;">
            🔊 Listen & Practice ({label_genero})
        </button>

        <script>
            function playHumanVoice() {{
                var mainWin = window.parent || window;
                if ('speechSynthesis' in mainWin) {{
                    mainWin.speechSynthesis.cancel(); // Liberar memoria colgada de audio
                    
                    var msg = new mainWin.SpeechSynthesisUtterance('{texto_escapado}');
                    var voices = mainWin.speechSynthesis.getVoices();
                    
                    // Filtrar estrictamente voces en inglés de Estados Unidos (en-US / en)
                    var usVoices = voices.filter(function(v) {{
                        return v.lang.startsWith('en');
                    }});
                    
                    var targetVoice = null;
                    var targetGender = '{genero_objetivo}';
                    
                    if (targetGender === "female") {{
                        // Buscar perfiles de voz femenina Premium (Google, Zira, Samantha, Hazel, etc.)
                        targetVoice = usVoices.find(function(v) {{
                            var name = v.name.toLowerCase();
                            return name.includes('zira') || name.includes('samantha') || name.includes('hazel') || name.includes('female') || name.includes('google us english');
                        }});
                    }} else {{
                        // Buscar perfiles de voz masculina Premium (David, George, Male, etc.)
                        targetVoice = usVoices.find(function(v) {{
                            var name = v.name.toLowerCase();
                            return name.includes('david') || name.includes('george') || name.includes('male') || name.includes('desktop');
                        }});
                    }}
                    
                    # Fallback de seguridad: si no encuentra el género exacto, usa la primera voz en inglés disponible
                    if (!targetVoice && usVoices.length > 0) {{
                        targetVoice = usVoices[0];
                    }}
                    
                    if (targetVoice) {{
                        msg.voice = targetVoice;
                    }}
                    
                    msg.lang = 'en-US';
                    msg.rate = 0.85;   // Velocidad humana y clara para entrenamiento de oído
                    msg.pitch = 1.0;  // Tono de frecuencia natural no robótico
                    msg.volume = 1.0; 
                    
                    mainWin.speechSynthesis.speak(msg);
                }}
            }}
            
            // Forzar precarga de voces en el hilo principal del navegador
            if ('speechSynthesis' in (window.parent || window)) {{
                (window.parent || window).speechSynthesis.getVoices();
            }}
        </script>
    </body>
    </html>
    """
    st.components.v1.html(codigo_html, height=48, scrolling=False)
# ==============================================================================
# SUBPARTE 4: MENÚ DE NAVEGACIÓN Y CIERRE DE SESIÓN (SIDEBAR)
# ==============================================================================
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

st.title("🚗 Quality Inspector - Pronunciation & Training Simulator")
st.subheader("IATF 16949 Standards & Shop Floor Communication Practice")
st.markdown("---")
# ==============================================================================
# SUBPARTE 5: SECCIÓN CORE I (OBJECTIVE Y REPORTES ESCRITOS CON IMÁGENES SEGURAS)
# ==============================================================================
if seccion == "I. Objective & Scope":
    st.header("I. OBJECTIVE & SCOPE")
    
    p1_en = "<span style='color:#424242; font-weight:bold;'>The</span> <span style='color:#1565c0; font-weight:bold;'>purpose of this assessment</span> <span style='color:#2e7d32; font-weight:bold;'>is to identify</span> <span style='color:#1565c0; font-weight:bold;'>specific language gaps</span> <span style='color:#ef6c00; font-weight:bold;'>and</span> <span style='color:#1565c0; font-weight:bold;'>technical English competencies</span> <span style='color:#2e7d32; font-weight:bold;'>required by the Quality Inspector role</span>."
    p1_es = "<span style='color:#424242; font-weight:bold;'>El</span> <span style='color:#1565c0; font-weight:bold;'>propósito de esta evaluación</span> <span style='color:#2e7d32; font-weight:bold;'>es identificar</span> <span style='color:#1565c0; font-weight:bold;'>brechas lingüísticas específicas</span> <span style='color:#ef6c00; font-weight:bold;'>y</span> <span style='color:#1565c0; font-weight:bold;'>competencias técnicas en inglés</span> <span style='color:#2e7d32; font-weight:bold;'>requeridas por el rol de Inspector de Calidad</span>."
    
    p2_en = "<span style='color:#424242; font-weight:bold;'>The</span> <span style='color:#1565c0; font-weight:bold;'>insights gathered</span> <span style='color:#2e7d32; font-weight:bold;'>will align</span> <span style='color:#1565c0; font-weight:bold;'>language training</span> <span style='color:#ef6c00; font-weight:bold;'>with</span> <span style='color:#1565c0; font-weight:bold;'>IATF 16949 standards</span>, <span style='color:#2e7d32; font-weight:bold;'>minimize</span> <span style='color:#1565c0; font-weight:bold;'>operational risk</span>, <span style='color:#ef6c00; font-weight:bold;'>and</span> <span style='color:#2e7d32; font-weight:bold;'>optimize</span> <span style='color:#1565c0; font-weight:bold;'>shop floor communication</span>."
    p2_es = "<span style='color:#424242; font-weight:bold;'>La</span> <span style='color:#1565c0; font-weight:bold;'>información recopilada</span> <span style='color:#2e7d32; font-weight:bold;'>alineará</span> <span style='color:#1565c0; font-weight:bold;'>la capacitación lingüística</span> <span style='color:#ef6c00; font-weight:bold;'>con</span> <span style='color:#1565c0; font-weight:bold;'>los estándares IATF 16949</span>, <span style='color:#2e7d32; font-weight:bold;'>minimizará</span> <span style='color:#1565c0; font-weight:bold;'>el riesgo operativo</span>, <span style='color:#ef6c00; font-weight:bold;'>y</span> <span style='color:#2e7d32; font-weight:bold;'>optimizará</span> <span style='color:#1565c0; font-weight:bold;'>la comunicación en el piso de producción</span>."
    
    with st.container(border=True):
        crear_boton_practica(p1_en, p1_es, "p1", "https://pexels.com")
    with st.container(border=True):
        crear_boton_practica(p2_en, p2_es, "p2", "https://pexels.com")

elif seccion == "II-A. Written English (Reports)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("A. WRITTEN ENGLISH: REPORTS & TRACEABILITY")
    
    preguntas_escritas = [
        ("<span style='color:#1565c0; font-weight:bold;'>Which official quality documents</span> <span style='color:#2e7d32; font-weight:bold;'>do you require me to write</span> <span style='color:#6a1b9a; font-weight:bold;'>more clearly</span> <span style='color:#ef6c00; font-weight:bold;'>in</span> <span style='color:#1565c0; font-weight:bold;'>English</span>?",
         "<span style='color:#1565c0; font-weight:bold;'>Cuáles documentos oficiales de calidad</span> <span style='color:#2e7d32; font-weight:bold;'>requiere que yo escriba</span> <span style='color:#6a1b9a; font-weight:bold;'>con mayor claridad</span> <span style='color:#ef6c00; font-weight:bold;'>en</span> <span style='color:#1565c0; font-weight:bold;'>inglés</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#1565c0; font-weight:bold;'>What specific sections of the 8D report</span> <span style='color:#2e7d32; font-weight:bold;'>should I practice writing</span> <span style='color:#ef6c00; font-weight:bold;'>to</span> <span style='color:#2e7d32; font-weight:bold;'>make</span> <span style='color:#424242; font-weight:bold;'>my</span> <span style='color:#1565c0; font-weight:bold;'>explanations</span> <span style='color:#6a1b9a; font-weight:bold;'>clearer</span>?",
         "<span style='color:#1565c0; font-weight:bold;'>Qué secciones específicas del reporte 8D</span> <span style='color:#2e7d32; font-weight:bold;'>debería practicar escribir</span> <span style='color:#ef6c00; font-weight:bold;'>para</span> <span style='color:#2e7d32; font-weight:bold;'>hacer</span> <span style='color:#424242; font-weight:bold;'>mis</span> <span style='color:#1565c0; font-weight:bold;'>explicaciones</span> <span style='color:#6a1b9a; font-weight:bold;'>más claras</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#ef6c00; font-weight:bold;'>When</span> <span style='color:#2e7d32; font-weight:bold;'>I enter</span> <span style='color:#1565c0; font-weight:bold;'>defect codes</span>, <span style='color:#1565c0; font-weight:bold;'>what</span> <span style='color:#2e7d32; font-weight:bold;'>are</span> <span style='color:#424242; font-weight:bold;'>the</span> <span style='color:#6a1b9a; font-weight:bold;'>most common formatting mistakes</span>?",
         "<span style='color:#ef6c00; font-weight:bold;'>Cuando</span> <span style='color:#2e7d32; font-weight:bold;'>ingreso</span> <span style='color:#1565c0; font-weight:bold;'>códigos de defectos</span>, <span style='color:#1565c0; font-weight:bold;'>cuáles</span> <span style='color:#2e7d32; font-weight:bold;'>son</span> <span style='color:#424242; font-weight:bold;'>los</span> <span style='color:#6a1b9a; font-weight:bold;'>errores de formato más comunes</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#ef6c00; font-weight:bold;'>When</span> <span style='color:#2e7d32; font-weight:bold;'>I email</span> <span style='color:#1565c0; font-weight:bold;'>global engineering teams</span>, <span style='color:#1565c0; font-weight:bold;'>what areas of my written English</span> <span style='color:#2e7d32; font-weight:bold;'>need</span> <span style='color:#1565c0; font-weight:bold;'>improvement</span>?",
         "<span style='color:#ef6c00; font-weight:bold;'>Cuando</span> <span style='color:#2e7d32; font-weight:bold;'>envío correos electrónicos</span> <span style='color:#424242; font-weight:bold;'>a</span> <span style='color:#1565c0; font-weight:bold;'>equipos globales de ingeniería</span>, <span style='color:#1565c0; font-weight:bold;'>qué áreas de mi inglés escrito</span> <span style='color:#2e7d32; font-weight:bold;'>necesitan</span> <span style='color:#1565c0; font-weight:bold;'>mejorar</span>?",
         "https://pexels.com")
    ]
    for i, (en, es, img) in enumerate(preguntas_escritas, 1):
        with st.container(border=True):
            crear_boton_practica(en, es, f"written_{i}", img)
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_written_{i}")
# ==============================================================================
# SUBPARTE 6: SECCIÓN CORE II (SPOKEN ENGLISH, AUDITORÍAS Y SIGLAS CON IMÁGENES SEGURAS)
# ==============================================================================
elif seccion == "II-B. Spoken English (Floor Alerts)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("B. SPOKEN ENGLISH: FLOOR ALERTS & PUSHBACK")
    
    preguntas_habladas = [
        ("<span style='color:#1565c0; font-weight:bold;'>What specific technical vocabulary</span> <span style='color:#2e7d32; font-weight:bold;'>do you want me to master</span> <span style='color:#ef6c00; font-weight:bold;'>when</span> <span style='color:#2e7d32; font-weight:bold;'>describing</span> <span style='color:#1565c0; font-weight:bold;'>physical defects</span>?",
         "<span style='color:#1565c0; font-weight:bold;'>Qué vocabulario técnico específico</span> <span style='color:#2e7d32; font-weight:bold;'>desea que domine</span> <span style='color:#ef6c00; font-weight:bold;'>al</span> <span style='color:#2e7d32; font-weight:bold;'>describir</span> <span style='color:#1565c0; font-weight:bold;'>defectos físicos</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#6a1b9a; font-weight:bold;'>How</span> <span style='color:#2e7d32; font-weight:bold;'>can I improve</span> <span style='color:#424242; font-weight:bold;'>my</span> <span style='color:#1565c0; font-weight:bold;'>communication</span> <span style='color:#ef6c00; font-weight:bold;'>when</span> <span style='color:#2e7d32; font-weight:bold;'>I need to urgently report</span> <span style='color:#424242; font-weight:bold;'>a</span> <span style='color:#1565c0; font-weight:bold;'>critical quality issue</span>?",
         "<span style='color:#6a1b9a; font-weight:bold;'>Cómo</span> <span style='color:#2e7d32; font-weight:bold;'>puedo mejorar</span> <span style='color:#424242; font-weight:bold;'>mi</span> <span style='color:#1565c0; font-weight:bold;'>comunicación</span> <span style='color:#ef6c00; font-weight:bold;'>cuando</span> <span style='color:#2e7d32; font-weight:bold;'>necesito reportar urgentemente</span> <span style='color:#424242; font-weight:bold;'>un</span> <span style='color:#1565c0; font-weight:bold;'>problema de calidad crítico</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#1565c0; font-weight:bold;'>What specific phrases</span> <span style='color:#2e7d32; font-weight:bold;'>should I use to confidently defend</span> <span style='color:#424242; font-weight:bold;'>my</span> <span style='color:#1565c0; font-weight:bold;'>quality decisions</span>?",
         "<span style='color:#1565c0; font-weight:bold;'>Qué frases específicas</span> <span style='color:#2e7d32; font-weight:bold;'>debería usar para defender con confianza</span> <span style='color:#424242; font-weight:bold;'>mis</span> <span style='color:#1565c0; font-weight:bold;'>decisiones de calidad</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#1565c0; font-weight:bold;'>What key terms</span> <span style='color:#2e7d32; font-weight:bold;'>should I focus on using</span> <span style='color:#ef6c00; font-weight:bold;'>during</span> <span style='color:#424242; font-weight:bold;'>our</span> <span style='color:#6a1b9a; font-weight:bold;'>daily</span> <span style='color:#1565c0; font-weight:bold;'>Gemba Walks</span>?",
         "<span style='color:#1565c0; font-weight:bold;'>En qué términos clave</span> <span style='color:#2e7d32; font-weight:bold;'>debería enfocarme al usar</span> <span style='color:#ef6c00; font-weight:bold;'>durante</span> <span style='color:#424242; font-weight:bold;'>nuestras</span> <span style='color:#6a1b9a; font-weight:bold;'>caminatas Gemba</span> <span style='color:#6a1b9a; font-weight:bold;'>diarias</span>?",
         "https://pexels.com")
    ]
    for i, (en, es, img) in enumerate(preguntas_habladas, 1):
        with st.container(border=True):
            crear_boton_practica(en, es, f"spoken_{i}", img)
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_spoken_{i}")

elif seccion == "II-C. Audits & Standards (IATF)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("C. AUDITS & STANDARDS (IATF 16949)")
    
    preguntas_auditoria = [
        ("<span style='color:#1565c0; font-weight:bold;'>What specific questions from external auditors</span> <span style='color:#2e7d32; font-weight:bold;'>do you think I need to practice answering</span>?",
         "<span style='color:#1565c0; font-weight:bold;'>Qué preguntas específicas de auditores externos</span> <span style='color:#2e7d32; font-weight:bold;'>cree que necesito practicar responder</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#6a1b9a; font-weight:bold;'>How</span> <span style='color:#2e7d32; font-weight:bold;'>can I improve</span> <span style='color:#424242; font-weight:bold;'>my</span> <span style='color:#1565c0; font-weight:bold;'>explanation of our company’s quality policy</span>?",
         "<span style='color:#6a1b9a; font-weight:bold;'>Cómo</span> <span style='color:#2e7d32; font-weight:bold;'>puedo mejorar</span> <span style='color:#424242; font-weight:bold;'>mi</span> <span style='color:#1565c0; font-weight:bold;'>explicación de la política de calidad de nuestra empresa</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#ef6c00; font-weight:bold;'>When</span> <span style='color:#2e7d32; font-weight:bold;'>reading engineering blueprints</span>, <span style='color:#1565c0; font-weight:bold;'>what technical terms</span> <span style='color:#2e7d32; font-weight:bold;'>do I struggle with</span> <span style='color:#6a1b9a; font-weight:bold;'>most</span>?",
         "<span style='color:#ef6c00; font-weight:bold;'>Al</span> <span style='color:#2e7d32; font-weight:bold;'>leer planos de ingeniería</span>, <span style='color:#1565c0; font-weight:bold;'>con qué términos técnicos</span> <span style='color:#2e7d32; font-weight:bold;'>tengo</span> <span style='color:#6a1b9a; font-weight:bold;'>más</span> <span style='color:#1565c0; font-weight:bold;'>dificultad</span>?",
         "https://pexels.com")
    ]
    for i, (en, es, img) in enumerate(preguntas_auditoria, 1):
        with st.container(border=True):
            crear_boton_practica(en, es, f"audit_{i}", img)
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_audit_{i}")

elif seccion == "II-D. Technical Glossary & Tools":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("D. TECHNICAL GLOSSARY & INDUSTRY ACRONYMS")
    
    preguntas_glosario = [
        ("<span style='color:#1565c0; font-weight:bold;'>Which automotive quality acronyms</span> <span style='color:#2e7d32; font-weight:bold;'>do you need me to explain</span> <span style='color:#6a1b9a; font-weight:bold;'>more comfortably</span>?",
         "<span style='color:#1565c0; font-weight:bold;'>Cuáles acrónimos de calidad automotriz</span> <span style='color:#2e7d32; font-weight:bold;'>necesita que explique</span> <span style='color:#6a1b9a; font-weight:bold;'>con mayor comodidad</span>?",
         "https://pexels.com"),
        
        ("<span style='color:#2e7d32; font-weight:bold;'>Are there</span> <span style='color:#1565c0; font-weight:bold;'>specific OEM portals</span> <span style='color:#ef6c00; font-weight:bold;'>where</span> <span style='color:#2e7d32; font-weight:bold;'>you want me to improve</span> <span style='color:#424242; font-weight:bold;'>my</span> <span style='color:#1565c0; font-weight:bold;'>navigation skills</span>?",
         "<span style='color:#2e7d32; font-weight:bold;'>Existen</span> <span style='color:#1565c0; font-weight:bold;'>portales OEM específicos</span> <span style='color:#ef6c00; font-weight:bold;'>donde</span> <span style='color:#2e7d32; font-weight:bold;'>desee que mejore</span> <span style='color:#424242; font-weight:bold;'>mis</span> <span style='color:#1565c0; font-weight:bold;'>habilidades de navegación</span>?",
         "https://pexels.com")
    ]
    for i, (en, es, img) in enumerate(preguntas_glosario, 1):
        with st.container(border=True):
            crear_boton_practica(en, es, f"glossary_{i}", img)
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_glossary_{i}")
    st.markdown("---")
    st.subheader("III. APPROVAL & SIGN-OFF")
    st.caption("The signatures below confirm that the communication gaps outlined above will be used to develop a targeted English training curriculum for the employee.")
# ==============================================================================
# SUBPARTE 7: SIMULADOR DE FEEDBACK CASUAL CON SUPERVISOR E IMÁGENES SEGURAS
# ==============================================================================
elif seccion == "💡 Supervisor Feedback Version (Casual)":
    st.header("💬 MY ENGLISH GROWTH PLAN: FEEDBACK QUESTIONS FOR MY SUPERVISOR")
    st.info("💡 Casual Shop Floor / Coffee Meeting Version")
    
    intro_en = "<span style='color:#2e7d32; font-weight:bold;'>I want to make sure</span> <span style='color:#424242; font-weight:bold;'>my</span> <span style='color:#1565c0; font-weight:bold;'>English skills</span> <span style='color:#2e7d32; font-weight:bold;'>are fully supporting</span> <span style='color:#424242; font-weight:bold;'>our</span> <span style='color:#1565c0; font-weight:bold;'>team's goals</span>."
    intro_es = "<span style='color:#2e7d32; font-weight:bold;'>Quiero asegurarme de que</span> <span style='color:#424242; font-weight:bold;'>mis</span> <span style='color:#1565c0; font-weight:bold;'>habilidades en inglés</span> <span style='color:#2e7d32; font-weight:bold;'>respalden plenamente</span> <span style='color:#424242; font-weight:bold;'>los</span> <span style='color:#1565c0; font-weight:bold;'>objetivos de nuestro equipo</span>."
    
    with st.container(border=True):
        crear_boton_practica(intro_en, intro_es, "intro_boss", "https://pexels.com")
        
    st.markdown("#### Checklists to Practice with your Supervisor:")
    
    v_written = [
        ("<span style='color:#1565c0; font-weight:bold;'>Which official reports</span> <span style='color:#2e7d32; font-weight:bold;'>do you need me to write</span> <span style='color:#6a1b9a; font-weight:bold;'>better</span> <span style='color:#ef6c00; font-weight:bold;'>in</span> <span style='color:#1565c0; font-weight:bold;'>English</span>?", 
         "<span style='color:#1565c0; font-weight:bold;'>Cuáles reportes oficiales</span> <span style='color:#2e7d32; font-weight:bold;'>necesita que escriba</span> <span style='color:#6a1b9a; font-weight:bold;'>mejor</span> <span style='color:#ef6c00; font-weight:bold;'>en</span> <span style='color:#1565c0; font-weight:bold;'>inglés</span>?"),
        ("<span style='color:#1565c0; font-weight:bold;'>What mistakes</span> <span style='color:#2e7d32; font-weight:bold;'>do you notice</span> <span style='color:#ef6c00; font-weight:bold;'>when</span> <span style='color:#2e7d32; font-weight:bold;'>I enter defect data</span>?", 
         "<span style='color:#1565c0; font-weight:bold;'>Qué errores</span> <span style='color:#2e7d32; font-weight:bold;'>nota</span> <span style='color:#ef6c00; font-weight:bold;'>cuando</span> <span style='color:#2e7d32; font-weight:bold;'>ingreso datos de defectos</span>?")
    ]
    
    v_spoken = [
        ("<span style='color:#1565c0; font-weight:bold;'>What specific defect words</span> <span style='color:#2e7d32; font-weight:bold;'>do I need to learn</span>?", 
         "<span style='color:#1565c0; font-weight:bold;'>Qué palabras específicas de defectos</span> <span style='color:#2e7d32; font-weight:bold;'>necesito aprender</span>?"),
        ("<span style='color:#6a1b9a; font-weight:bold;'>How</span> <span style='color:#2e7d32; font-weight:bold;'>can I sound</span> <span style='color:#6a1b9a; font-weight:bold;'>more urgent</span> <span style='color:#ef6c00; font-weight:bold;'>when</span> <span style='color:#2e7d32; font-weight:bold;'>triggering a Line Down</span>?", 
         "<span style='color:#6a1b9a; font-weight:bold;'>Cómo</span> <span style='color:#2e7d32; font-weight:bold;'>puedo sonar</span> <span style='color:#6a1b9a; font-weight:bold;'>más urgente</span> <span style='color:#ef6c00; font-weight:bold;'>al</span> <span style='color:#2e7d32; font-weight:bold;'>activar una Línea Parada</span>?")
    ]
    
    categorias = [
        ("📝 MY WRITTEN ENGLISH (Reports & Emails)", v_written, "c_wr"),
        ("🗣️ MY SPOKEN ENGLISH (Shop Floor & Team Meetings)", v_spoken, "c_sp")
    ]
    for titulo, lista, prefijo in categorias:
        with st.expander(titulo, expanded=True):
            for idx, (en, es) in enumerate(lista):
                crear_boton_practica(en, es, f"{prefijo}_{idx}")
            st.text_area("📝 Boss's Feedback & Examples:", key=f"boss_feed_{prefijo}", height=70)

    st.markdown("---")
    st.subheader("🎯 TOP 3. PRIORITY AREAS TO START TRAINING NEXT WEEK:")
    st.text_input("1.", key="prio_1")
    st.text_input("2.", key="prio_2")
    st.text_input("3.", key="prio_3")
    
    gracias_en = "<span style='color:#2e7d32; font-weight:bold;'>Thanks for your time</span> <span style='color:#ef6c00; font-weight:bold;'>and</span> <span style='color:#1565c0; font-weight:bold;'>feedback</span>!"
    gracias_es = "<span style='color:#2e7d32; font-weight:bold;'>¡Gracias por su tiempo</span> <span style='color:#ef6c00; font-weight:bold;'>y</span> <span style='color:#1565c0; font-weight:bold;'>retroalimentación</span>!"
    crear_boton_practica(gracias_en, gracias_es, "thanks_footer", "https://pexels.com")
