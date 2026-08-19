import streamlit as st

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
# ==============================================================================
# SUBPARTE 3: MOTOR DE AUDIO NATIVO DESCONGELADO CON TRADUCCIÓN Y VOZ PREMIUM US
# ==============================================================================
def crear_boton_practica(texto_en_ingles, texto_en_espanol, id_unico):
    """
    Muestra la traducción al español e inyecta un botón HTML5 que interactúa
    directamente con las voces nativas americanas del sistema, eliminando el acento español.
    """
    # Mostrar la traducción escrita al español de manera inmediata
    st.markdown(f"🔹 **Español:** *{texto_en_espanol}*")
    
    # Escapar comillas para evitar rupturas en la cadena de texto de JavaScript
    texto_escapado = texto_en_ingles.replace("'", "\\'").replace('"', '\\"')
    
    codigo_html = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <button onclick="reproducirConVozAmericana()" style="
            background-color: #1e88e5; 
            color: white; 
            border: none; 
            padding: 7px 15px; 
            font-size: 13px; 
            font-weight: bold;
            border-radius: 20px; 
            cursor: pointer; 
            box-shadow: 0px 2px 4px rgba(0,0,0,0.15);
            font-family: sans-serif;">
            🔊 Listen & Practice (Play)
        </button>

        <script>
            function reproducirConVozAmericana() {{
                // Acceder a la ventana superior para romper el aislamiento de Streamlit
                var tWindow = window.parent || window;
                
                if ('speechSynthesis' in tWindow) {{
                    tWindow.speechSynthesis.cancel(); // Limpiar cola colgada previa
                    
                    var msg = new tWindow.SpeechSynthesisUtterance('{texto_escapado}');
                    
                    // OBLIGAR AL MOTOR A ENCONTRAR UNA VOZ NATIVA DE ESTADOS UNIDOS (USA)
                    var vocesDisponibles = tWindow.speechSynthesis.getVoices();
                    
                    // Intentar buscar la voz premium americana de Google o fallbacks de Microsoft/Apple en inglés
                    var vozSeleccionada = vocesDisponibles.find(function(v) {{
                        return v.lang === 'en-US' && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('David') || v.name.includes('Zira'));
                    }});
                    
                    // Si no encuentra una específica, buscar cualquier voz que contenga 'en' o 'en-US'
                    if (!vozSeleccionada) {{
                        vozSeleccionada = vocesDisponibles.find(function(v) {{
                            return v.lang.startsWith('en');
                        }});
                    }}
                    
                    // Asignar la voz en inglés americano encontrada al mensaje
                    if (vozSeleccionada) {{
                        msg.voice = vozSeleccionada;
                    }}
                    
                    msg.lang = 'en-US'; // Reforzar el código de idioma
                    msg.rate = 0.85;    # Cadencia humana ligeramente pausada para entrenamiento
                    msg.volume = 1.0;   # Volumen operativo completo
                    
                    tWindow.speechSynthesis.speak(msg);
                }} else {{
                    alert("Tu navegador no soporta el motor de audio. Se recomienda usar Google Chrome en PC o celular.");
                }}
            }}
            
            # Forzar al navegador a precargar la lista de voces en cuanto se renderice el botón
            if ('speechSynthesis' in (window.parent || window)) {{
                (window.parent || window).speechSynthesis.getVoices();
            }}
        </script>
    </body>
    </html>
    """
    st.components.v1.html(codigo_html, height=42, scrolling=False)
    
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
# SUBPARTE 5: SECCIÓN CORE I (OBJECTIVE Y REPORTES ESCRITOS)
# ==============================================================================
if seccion == "I. Objective & Scope":
    st.header("I. OBJECTIVE & SCOPE")
    p1_en = "The purpose of this assessment is to identify specific language gaps and technical English competencies required by the Quality Inspector role."
    p1_es = "El propósito de esta evaluación es identificar brechas lingüísticas específicas y competencias técnicas en inglés requeridas por el rol de Inspector de Calidad."
    
    p2_en = "The insights gathered will align language training with IATF 16949 standards, minimize operational risk, and optimize shop floor communication."
    p2_es = "La información recopilada alineará la capacitación lingüística con los estándares IATF 16949, minimizará el riesgo operativo y optimizará la comunicación en el piso de producción."
    
    with st.container(border=True):
        st.markdown(f"**English:** {p1_en}")
        crear_boton_practica(p1_en, p1_es, "p1")
    with st.container(border=True):
        st.markdown(f"**English:** {p2_en}")
        crear_boton_practica(p2_en, p2_es, "p2")

elif seccion == "II-A. Written English (Reports)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("A. WRITTEN ENGLISH: REPORTS & TRACEABILITY")
    preguntas_escritas = [
        ("Which official quality documents do you require me to write more clearly in English (e.g., Non-Conformance Reports (NCR), 8D Reports, Quality Alerts, or shift handovers)?",
         "¿Cuáles documentos oficiales de calidad requiere que yo escriba con mayor claridad en inglés (por ejemplo, Reportes de No Conformidad (NCR), Reportes 8D, Alertas de Calidad o entregas de turno)?"),
        ("What specific sections of the 8D report (like Containment Actions or Root Cause Analysis) should I practice writing to make my explanations clearer?",
         "¿Qué secciones específicas del reporte 8D (como Acciones de Contención o Análisis de Causa Raíz) debería practicar escribir para hacer mis explicaciones más claras?"),
        ("When I enter defect codes or dimensions into our shop floor system, what are the most common English vocabulary or formatting mistakes you notice?",
         "Cuando ingreso códigos de defectos o dimensiones en nuestro sistema de piso de producción, ¿cuáles son los errores de vocabulario en inglés o de formato más comunes que nota?"),
        ("When I email global engineering teams, suppliers, or OEM customers about part deviations, what areas of my written English need improvement?",
         "Cuando envío correos electrónicos a equipos globales de ingeniería, proveedores o clientes OEM sobre desviaciones de piezas, ¿qué áreas de mi inglés escrito necesitan mejorar?")
    ]
    for i, (en, es) in enumerate(preguntas_escritas, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {en}**")
            crear_boton_practica(en, es, f"written_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_written_{i}")
# ==============================================================================
# SUBPARTE 6: SECCIÓN CORE II (SPOKEN ENGLISH, AUDITORÍAS Y SIGLAS)
# ==============================================================================
elif seccion == "II-B. Spoken English (Floor Alerts)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("B. SPOKEN ENGLISH: FLOOR ALERTS & PUSHBACK")
    preguntas_habladas = [
        ("What specific technical vocabulary do you want me to master when describing physical automotive defects during a teardown or inspection (e.g., burrs, flash, porosity, mismatch, cross-threading, orange peel)?",
         "¿Qué vocabulario técnico específico desea que domine al describir defectos automotrices físicos durante un desensamble o inspección (por ejemplo, rebabas, destellos, porosidad, desalineación, roscado cruzado, piel de naranja)?"),
        ("How can I improve my English communication when I need to urgently report a critical quality issue or trigger a Line Down / Hold status?",
         "¿Cómo puedo mejorar mi comunicación en inglés cuando necesito reportar urgentemente un problema de calidad crítico o activar un estado de Línea Parada / Retención?"),
        ("What specific phrases should I use to confidently defend my quality decisions in English when production supervisors pressure me to release a suspect batch?",
         "¿Qué frases específicas debería usar para defender con confianza mis decisiones de calidad en inglés cuando los supervisores de producción me presionan para liberar un lote sospechoso?"),
        ("What key terms or metrics should I focus on using during our daily Gemba Walks or production meetings to report quality data and scrap percentages?",
         "¿En qué términos clave o métricas debería enfocarme al usar durante nuestras caminatas Gemba diarias o reuniones de producción para reportar datos de calidad y porcentajes de scrap?")
    ]
    for i, (en, es) in enumerate(preguntas_habladas, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {en}**")
            crear_boton_practica(en, es, f"spoken_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_spoken_{i}")

elif seccion == "II-C. Audits & Standards (IATF)":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("C. AUDITS & STANDARDS (IATF 16949)")
    preguntas_auditoria = [
        ("What specific questions from external auditors (like IATF, or clients like Ford, GM, Toyota) do you think I need to practice answering verbally on the shop floor?",
         "¿Qué preguntas específicas de auditores externos (como IATF, o clientes como Ford, GM, Toyota) cree que necesito practicar responder verbalmente en el piso de producción?"),
        ("How can I improve my explanation of our company’s quality policy and gauge calibration procedures when I am audited in English?",
         "¿Cómo puedo mejorar mi explicación de la política de calidad de nuestra empresa y los procedimientos de calibración de instrumentos cuando me auditan en inglés?"),
        ("When reading or discussing engineering blueprints, GD&T symbols, and Control Plans in English, what technical terms do I struggle with most?",
         "Al leer o discutir planos de ingeniería, símbolos de GD&T y Planes de Control en inglés, ¿con qué términos técnicos tengo más dificultad?")
    ]
    for i, (en, es) in enumerate(preguntas_auditoria, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {en}**")
            crear_boton_practica(en, es, f"audit_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_audit_{i}")

elif seccion == "II-D. Technical Glossary & Tools":
    st.header("II. TARGETED COMPETENCY INQUIRIES")
    st.subheader("D. TECHNICAL GLOSSARY & INDUSTRY ACRONYMS")
    preguntas_glosario = [
        ("Which automotive quality acronyms do you need me to explain and speak about more comfortably (e.g., PPAP, APQP, FMEA, MSA, SPC, Poka-Yoke)?",
         "¿Cuáles acrónimos de calidad automotriz necesita que explique y hable con mayor comodidad (por ejemplo, PPAP, APQP, FMEA, MSA, SPC, Poka-Yoke)?"),
        ("Are there specific OEM portals or English software tools where you want me to improve my data entry and navigation skills?",
         "¿Existen portales OEM específicos o herramientas de software en inglés donde desee que mejore mis habilidades de ingreso de datos y navegación?")
    ]
    for i, (en, es) in enumerate(preguntas_glosario, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {en}**")
            crear_boton_practica(en, es, f"glossary_{i}")
            st.text_input("✏️ Notes / Personal Practice:", key=f"notes_glossary_{i}")
    st.markdown("---")
    st.subheader("III. APPROVAL & SIGN-OFF")
    st.caption("The signatures below confirm that the communication gaps outlined above will be used to develop a targeted English training curriculum for the employee.")
# ==============================================================================
# SUBPARTE 7: SIMULADOR DE FEEDBACK CASUAL CON SUPERVISOR Y CIERRE
# ==============================================================================
elif seccion == "💡 Supervisor Feedback Version (Casual)":
    st.header("💬 MY ENGLISH GROWTH PLAN: FEEDBACK QUESTIONS FOR MY SUPERVISOR")
    st.info("💡 Casual Shop Floor / Coffee Meeting Version")
    
    intro_en = "Hi Boss, I want to make sure my English skills are fully supporting our team's goals and keeping the line running smoothly. Let's use this quick checklist to find out exactly where I can improve my written and spoken English."
    intro_es = "Hola Jefe, quiero asegurarme de que mis habilidades en inglés respalden plenamente los objetivos de nuestro equipo y mantengan la línea funcionando sin problemas. Usemos esta lista de verificación rápida para descubrir exactamente dónde puedo mejorar mi inglés escrito y hablado."
    
    with st.container(border=True):
        st.markdown(f'**Introductory Icebreaker:** "{intro_en}"')
        crear_boton_practica(intro_en, intro_es, "intro_boss")
        
    st.markdown("#### Checklists to Practice with your Supervisor:")
    v_written = [
        ("Which official reports do you need me to write better in English? (NCRs, 8D Reports, Quality Alerts, Shift Handovers)", "¿Cuáles reportes oficiales necesita que escriba mejor en inglés?"),
        ("Any specific sections of the 8D report I should practice writing?", "¿Alguna sección específica del reporte 8D que deba practicar escribir?"),
        ("What mistakes do you notice when I enter defect data into the system?", "¿Qué errores nota cuando ingreso datos de defectos en el sistema?"),
        ("How can I improve my emails to global teams, suppliers, or customers?", "¿Cómo puedo mejorar mis correos electrónicos a equipos globales, proveedores o clientes?")
    ]
    v_spoken = [
        ("What specific defect words do I need to learn? (burrs, flash, porosity, mismatch, orange peel...)", "¿Qué palabras específicas de defectos necesito aprender?"),
        ("How can I sound more urgent when triggering a Line Down or Hold status?", "¿Cómo puedo sonar más urgente al activar un estado de Línea Parada o Retención?"),
        ("What phrases should I use when production managers challenge my quality decisions?", "¿Qué frases debería usar cuando los gerentes de producción desafían mis decisiones de calidad?"),
        ("What key metrics should I practice talking about during Gemba Walks?", "¿Sobre qué métricas clave debería practicar hablar durante las caminatas Gemba?")
    ]
    v_audit = [
        ("What specific questions from auditors (IATF, Ford, GM, Toyota) should I practice?",  "¿Qué preguntas específicas de los auditores debería practicar?"),
        ("Can I explain our quality policy and tool calibration clearly enough?", "¿Puedo explicar nuestra política de calidad y la calibración de herramientas con suficiente claridad?"),
        ("What terms do I trip over when reading blueprints, GD&T, or Control Plans?", "¿Con qué términos tropiezo al leer planos, GD&T o Planes de Control?")
    ]
    v_tools = [
        ("Which acronyms do I need to explain better? (PPAP, FMEA, SPC, Poka-Yoke...)", "¿Qué acrónimos necesito explicar mejor?"),
        ("Which English customer portals or software tools do I need to master?", "¿Qué portales de clientes o herramientas de software en inglés necesito dominar?")
    ]

    categorias = [
        ("📝 MY WRITTEN ENGLISH (Reports & Emails)", v_written, "c_wr"),
        ("🗣️ MY SPOKEN ENGLISH (Shop Floor & Team Meetings)", v_spoken, "c_sp"),
        ("🔍 AUDITS & TECHNICAL DATA (IATF 16949)", v_audit, "c_au"),
        ("🛠️ GLOSSARY & SOFTWARE TOOLS", v_tools, "c_tl")
    ]
    for titulo, lista, prefijo in categorias:
        with st.expander(titulo, expanded=True):
            for idx, (en, es) in enumerate(lista):
                st.markdown(f"• {en}")
                crear_boton_practica(en, es, f"{prefijo}_{idx}")
            st.text_area("📝 Boss's Feedback & Examples:", key=f"boss_feed_{prefijo}", height=70)

    st.markdown("---")
    st.subheader("🎯 TOP 3. PRIORITY AREAS TO START TRAINING NEXT WEEK:")
    st.text_input("1.", key="prio_1")
    st.text_input("2.", key="prio_2")
    st.text_input("3.", key="prio_3")
    
    gracias_en = "Thanks for your time and feedback! Let's touch base again in 4 weeks to track progress."
    gracias_es = "¡Gracias por su tiempo y retroalimentación! Volvamos a ponernos en contacto en 4 semanas para realizar un seguimiento del progreso."
    st.markdown(f'*{gracias_en}*')
    crear_boton_practica(gracias_en, gracias_es, "thanks_footer")
