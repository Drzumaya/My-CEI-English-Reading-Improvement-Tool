import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado de PDFs en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# PARTE 1 DE 10: CONFIGURACIÓN ESTRUCTURAL DE PÁGINA E INICIALIZACIÓN DE SESIÓN
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - Agua Prieta",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar estados de sesión críticos para el control de accesos
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if "historial_descargas" not in st.session_state:
    st.session_state["historial_descargas"] = []

if "ver_visor_legal" not in st.session_state:
    st.session_state["ver_visor_legal"] = False
if "entidad_seleccionada" not in st.session_state:
    st.session_state["entidad_seleccionada"] = ""
if "tipo_doc_seleccionado" not in st.session_state:
    st.session_state["tipo_doc_seleccionado"] = ""
# ==============================================================================
# PARTE 2 DE 10: BASE DE DATOS EN MEMORIA - ASOCIACIÓN CIVIL MATRIZ (A.C.)
# ==============================================================================
if "repositorio_institucional" not in st.session_state:
    st.session_state["repositorio_institucional"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL\n\nFunciona como la sociedad controladora social (Holding) que coordina los subsistemas autónomos en Agua Prieta. Diseña los planes de capacitación para el trabajo de la periferia urbana.",
            "Marco legal": "FUNDAMENTACIÓN FISCAL TÍTULO II LISR\n\nTributa en Régimen General corporativo (30% ISR). Blinda sus egresos comunitarios al 100% como deducciones mediante Nómina Asimilada (Art. 94 LISR). Exenta de trasladar el 16% de IVA en capacitación según el Art. 15 de la LIVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS DE GOBERNANZA CENTRAL (MAP-01)\n\n1. Recepción de comisiones de la S.A. y aportaciones cooperativas.\n2. Validación de listas de asistencia de talleres.\n3. Dispersión mensual y timbrado de CFDI de asimilados a salarios.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RECURSOS HUMANOS Y CONTROL (MAC-01)\n\nRegula las políticas de contratación de promotores barriales, el control de activos en comodato y los lineamientos de transparencia para auditorías externas del SAT.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS Y RIESGO SOCIOECONÓMICO (MTC-01)\n\nMonitorea la inflación en la franja fronteriza, los cambios en las reglas misceláneas del SAT y el impacto del tipo de cambio peso-dólar en el poder adquisitivo de Agua Prieta.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EVALUACIÓN DE ADOPCIÓN DE PROGRAMAS SOCIALES\n\nVARIABLE LATENTE CENTRAL: 'Aceptación Institucional del Modelo de Economía Popular'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Frecuencia con la que el asociado acude voluntariamente a las mesas de gobernanza de la A.C.\n2. [X2] Nivel de confianza percibido en la transparencia del manejo de fondos del Título II corporativo.\n3. [X3] Disposición declarada para transitar de contratos informales en efectivo a Nómina de Asimilados.\n4. [X4] Grado de recomendación del programa de capacitación de la A.C. a otros microemprendedores del barrio.\n5. [X5] Percepción de mejora en la estabilidad de su negocio tras el cobro vía recibo estatutario."
        },
# ==============================================================================
# PARTE 3 DE 10: BASE DE DATOS EN MEMORIA - COOPERATIVA DE LOGÍSTICA (S.C.)
# ==============================================================================
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA OPERATIVO DE TRANSPORTE BARRIAL\n\nAsociación de choferes y transportistas de base popular organizados para competir en el mercado de fletes industriales B2B y última milla, absorbiendo la demanda del nearshoring maquilador.",
            "Marco legal": "LEY GENERAL DE SOCIEDADES COOPERATIVAS (LGSC)\n\nSociedad Cooperativa de Producción de Servicios de Responsabilidad Limitada (S.C. de R.L. de C.V.). Las plantas maquiladoras contratantes efectúan la retención del 4% de ISR sobre fletes terrestres.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS OPERATIVOS LOGÍSTICOS (MOP-02)\n\n1. Asignación de rutas comerciales en Agua Prieta.\n2. Auditoría física del Factor de Retorno Vacío (Deadhead).\n3. Retención automática del 6% para el fondo de amortiguación de diésel.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE FLOTILLA Y MANTENIMIENTO (MAF-02)\n\nEstablece los roles de los Asociados Directores en la administración de talleres mecánicos asignados, control de bitácoras de viaje y asignación de viáticos logísticos fronterizos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS DE TRANSPORTE TRANSFRONTERIZO (MTC-02)\n\nAnaliza los tiempos de espera en las aduanas, la fluctuación estacional de la producción automotriz de las maquiladoras y el impacto de aranceles comerciales en el flujo de fletes.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA OPERATIVA DE LA LOGÍSTICA DE BARRIO\n\nVARIABLE LATENTE CENTRAL: 'Cultura de Optimización de Ruta en Choferes Cooperativistas'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Índice de cumplimiento exacto de los horarios de recolección reportados en la aduana.\n2. [X2] Nivel de reducción voluntaria reportada en el Factor de Retorno Vacío.\n3. [X3] Frecuencia de registro y uso correcto de la aplicación Streamlit para el reporte del COK.\n4. [X4] Grado de apego a los lineamientos de mantenimiento preventivo y revisión de presión de neumáticos.\n5. [X5] Proporción de fletes ejecutados sin registrar incidencias o penalizaciones por retraso.\n6. [X6] Disposición del chofer para cooperar en cargas consolidadas compartidas con otros talleres."
        },
# ==============================================================================
# PARTE 4 DE 10: BASE DE DATOS EN MEMORIA - AGENCIA DE MICROSEGUROS (S.A.)
# ==============================================================================
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE CONTROL DE RIESGOS COMERCIAL\n\nEntidad financiera diseñada para proteger los activos mecánicos de los talleres populares y mitigar vulnerabilidades por accidentes de trabajo o fallecimiento de líderes comunitarios.",
            "Marco legal": "LEY DE INSTITUCIONES DE SEGUROS Y DE FIANZAS (LISF)\n\nSociedad Anónima regulada por la CNSF. Transfiere legalmente el 20% de las primas a la A.C. mediante contratos de Corretaje Social y capacitación en prevención de accidentes.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS Y ATENCIÓN DE SINIESTROS (MAP-03)\n\n1. Reporte técnico de avería mecánica o accidente en las colonias.\n2. Evaluación social del riesgo y dictamen del Asociado Director.\n3. Liquidación de la reparación con cargo al fondo de reserva.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RESERVAS TÉCNICAS Y RECAUDACIÓN (MAR-03)\n\nRegula el proceso de cobranza mensual de las primas a través de plataformas digitales y el resguardo seguro del capital de reserva en instrumentos de renta fija de bajo riesgo.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS ACTUARIALES EN MICROSEGUROS (MTC-03)\n\nMide la tasa de siniestralidad de los talleres de barrio, la tasa de renovación de pólizas y proyecta modelos de vulnerabilidad ante fallas mecánicas en maquinaria pesada depreciada.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - PERCEPCIÓN DE SEGURIDAD PATRIMONIAL\n\nVARIABLE LATENTE CENTRAL: 'Aversión al Riesgo y Confianza en la Póliza Solidaria'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Puntualidad exacta en el pago de la prima mensual simulada en la plataforma.\n2. [X2] Grado de conocimiento de los talleres sobre el alcance real de las coberturas de siniestralidad.\n3. [X3] Nivel de tranquilidad manifestada por el micro-empresario respecto a la continuidad de su negocio.\n4. [X4] Frecuencia con la que el micro-taller reporta de forma preventiva riesgos de infraestructura.\n5. [X5] Confianza declarada en la velocidad de respuesta del fondo de reserva de la A.C. ante siniestros."
        },
# ==============================================================================
# PARTE 5 DE 10: BASE DE DATOS EN MEMORIA - EQUIPO CIENTÍFICO APSON
# ==============================================================================
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE INVESTIGACIÓN, DESARROLLO E INNOVACIÓN (I+D)\n\nCélula científica encargada de realizar estudios de densidad económica, análisis metalúrgicos para el reciclaje (Upcycling) de las mermas de las maquiladoras y optimización de modelos predictivos de crédito social.",
            "Marco legal": "LEY GENERAL DE HUMANIDADES, CIENCIAS, TECNOLOGÍAS E INNOVACIÓN\n\nOpera bajo el amparo de la Cláusula Estatutaria de Autonomía de los Asociados Directores. Los fondos de investigación científica se consideran aportaciones de fomento exentas de IVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS EN RECOLECCIÓN Y PROCESAMIENTO (MAP-04)\n\n1. Recolección de muestras de mermas industriales (cueros, maderas, polímeros) en las maquiladoras.\n2. Pruebas de resistencia en laboratorios comunitarios.\n3. Transferencia de patentes sociales a los talleres.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE PROYECTOS Y FIDEICOMISOS CIENTÍFICOS (MAP-04)\n\nCoordina la gobernanza presupuestal de los laboratorios, la asignación de becas de investigación a estudiantes universitarios de Agua Prieta y el inventario de reactivos técnicos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS EN INNOVACIÓN INDUSTRIAL (MTC-04)\n\nMapea las tecnologías emergentes de manufactura esbelta automatizada, el volumen de desperdicios utilizables por tipo de maquila y las proyecciones de crecimiento del nearshoring real.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA DE LA TRANSFERENCIA TECNOLÓGICA I+D\n\nVARIABLE LATENTE CENTRAL: 'Capacidad de Absorción del Saber Científico en Talleres de Barrio'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Tasa de adopción de manuales Lean-Barrio y diagramas de flujo técnicos dentro de los procesos diarios.\n2. [X2] Cantidad de mermas industriales recolectadas (cuero, madera) efectivamente transformadas.\n3. [X3] Frecuencia de asistencia de los artesanos a las células de co-diseño del Equipo Científico.\n4. [X4] Reducción porcentual de costos de materia prima lograda por el taller al sustituir insumos.\n5. [X5] Nivel de comprensión técnica manifestada por el micro-productor sobre el uso y cuidado de maquinaria.\n6. [X6] Cantidad de nuevos prototipos funcionales o innovaciones locales de producto generadas de forma autónoma.\n7. [X7] Incremento reportado en la calidad final de la proveeduría indirecta entregada a las plantas."
        }
    }
# ==============================================================================
# PARTE 6 DE 10: LOGIN DE ALTA SEGURIDAD Y FUNCIÓN COMPILADORA REPORTLAB PDF
# ==============================================================================
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["access_control"]["password"]:
            st.session_state["password_correct"] = True
            st.session_state["show_login_error"] = False
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
            st.session_state["show_login_error"] = True

    if st.session_state["password_correct"]:
        return True

    # Renderizado oportuno del login limpio libre de advertencias en primera carga
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l2:
        st.title("🔐 Acceso Restringido")
        st.subheader("Plataforma Integral de Economía Popular")
        st.caption("Asociación Civil en Régimen General (Título II LISR) • Agua Prieta, Sonora")
        st.text_input("Introduce la contraseña de acceso:", type="password", on_change=password_entered, key="password")
        if st.session_state.get("show_login_error", False):
            st.error("❌ Credenciales inválidas. Intento bloqueado por seguridad.")
        with st.expander("ℹ️ Soporte Técnico"):
            st.caption("Las claves son administradas de forma directa por el Agente Capacitador.")
    return False

if not check_password():
    st.stop()

# Generador de Informes Técnicos en PDF (REPARADO: colWidths con tupla de floats)
def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    color_primario = colors.HexColor("#1e4620")
    
    estilo_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=14, textColor=color_primario, spaceAfter=12)
    estilo_sub = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, textColor=colors.gray, spaceAfter=12)
    estilo_cuerpo = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=12)
    
    story = []
    story.append(Paragraph(f"<b>{titulo_modulo}</b>", estilo_titulo))
    story.append(Paragraph("Ecosistema de Economía Popular AP-AC | Validación Documental Oficial", estilo_sub))
    story.append(Spacer(1, 10))
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    story.append(Spacer(1, 15))
    
    # SE ASIGNAN 240 PUNTOS DE IMPRESIÓN POR CELDA PARA EVITAR EL SYNTAXERROR VISTO ANTES
    tabla_pdf = Table(datos_tabla, colWidths=[240.0, 240.0])
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), color_primario), ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(tabla_pdf)
    doc.build(story)
    buffer.seek(0)
    return buffer
# ==============================================================================
# PARTE 7 DE 10: CONTROLES DE SIDEBAR Y PARTICIÓN DE ARQUITECTURA DE PANTALLA
# ==============================================================================
st.sidebar.header("📋 Operaciones")
if st.sidebar.button("❌ Cerrar Sesión (Logout)", use_container_width=True, type="primary"):
    logout()
presupuesto_total = st.sidebar.number_input("Bolsa Económica Mensual Operativa (MXN)", min_value=10000, value=250000, step=10000)

# Partición maestra de pantalla: 70% Simuladores (Izquierda), 30% Almacén (Derecha)
col_izquierda_matriz, col_derecha_documental = st.columns([0.70, 0.30])

num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_calculado = 0.0
# ==============================================================================
# PARTE 8 DE 10: COLUMNA IZQUIERDA - ENTORNO INTERACTIVO DE PÁGINA FLOTANTE
# ==============================================================================
with col_izquierda_matriz:
    if st.session_state["ver_visor_legal"]:
        ent = st.session_state["entidad_seleccionada"]
        tdoc = st.session_state["tipo_doc_seleccionado"]
        
        st.info(f"📁 Ventana de Trabajo Activa: {ent} ➔ {tdoc}")
        st.markdown("---")
        
        texto_editable_actual = st.text_area(
            label="Editor Oficial de Cláusulas e Instructivos (Cambios en Caliente):",
            value=st.session_state["repositorio_institucional"][ent][tdoc],
            height=380
        )
        
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("💾 Guardar Ajustes", use_container_width=True):
                st.session_state["repositorio_institucional"][ent][tdoc] = texto_editable_actual
                st.success("✓ Cambios guardados.")
        with b2:
            tabla_legal_dummy = [["Validación de Consistencia", "Aprobado por el Consejo"], ["Fecha de Auditoría", "2026-08-20"], ["Estatus Regulatorio", "Vigente Exento"]]
            pdf_legal = generar_informe_pdf(f"{ent} - {tdoc}", tabla_legal_dummy, texto_editable_actual)
            st.download_button(label="📥 PDF", data=pdf_legal, file_name=f"{tdoc.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
        with b3:
            buffer_word = io.BytesIO(texto_editable_actual.encode('utf-8'))
            st.download_button(label="📝 Word", data=buffer_word, file_name=f"{tdoc.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with b4:
            if st.button("🛑 Cerrar Visor", use_container_width=True, type="primary"):
                st.session_state["ver_visor_legal"] = False
                st.rerun()
# ==============================================================================
# PARTE 9 DE 10: COLUMNA IZQUIERDA - PESTAÑAS ORDINARIAS DE TRABAJO Y SIMULACIÓN
# ==============================================================================
    else:
        tabs = st.tabs(["🛡️ IVA e ISR", "🔮 Módulo Logístico Cooperativo", "📊 Microseguros", "🏦 Caja de Ahorro", "📑 Historial de Descargas"])
        tab1, tab_logistica, tab4, tab5, tab_log = tabs
        
        with tab1:
            st.header("Control Fiscal de Operaciones de la Base Social")
            num_talleres = st.slider("Talleres Populares Integrados", min_value=5, max_value=300, value=num_talleres_global)
            num_talleres_global = num_talleres
            cuota_calculada = float(presupuesto_total / num_talleres)
            st.metric("Cuota Extraordinaria de Recuperación", f"${cuota_calculada:,.2f} MXN", "0% IVA (Exento)")

        with tab_logistica:
            st.header("🔮 Parametrización de Fletes y Logística de Última Milla")
            viajes_mensuales = st.number_input("Número de Fletes Ejecutados al Mes:", min_value=1, value=48)
            distancia_viaje = st.slider("Distancia Promedio por Viaje (Kilómetros Redondos):", min_value=10, max_value=150, value=45)
            tarifa_por_km = st.number_input("Tarifa Base de Cobro por Kilómetro (MXN):", min_value=10.0, value=85.0)
            costo_operacion_km = st.number_input("Costo de Operación por Kilómetro (COK):", min_value=5.0, value=32.5)
            factor_vacio = st.slider("Factor de Retorno Vacío (% de Km):", min_value=0, max_value=50, value=25)
            reserva_combustible_pct = st.slider("Fondo de Amortiguación de Diésel (% Tarifa):", min_value=2, max_value=15, value=6)
            
            ingreso_bruto_fletes = viajes_mensuales * distancia_viaje * tarifa_por_km
            kilometros_gastados_reales = (viajes_mensuales * distancia_viaje) * (1 + (factor_vacio / 100))
            costo_operativo_total = kilometros_gastados_reales * costo_operacion_km
            retencion_isr_4pct = ingreso_bruto_fletes * 0.04
            fondo_diesel_retenido = ingreso_bruto_fletes * (reserva_combustible_pct / 100)
            excedente_neto_cooperativa = ingreso_bruto_fletes - costo_operativo_total - retencion_isr_4pct - fondo_diesel_retenido
            excedente_coop_calculado = excedente_neto_cooperativa
            
            l_m1, l_m2 = st.columns(2)
            l_m1.metric("Ingresos Brutos por Fletes", f"${ingreso_bruto_fletes:,.2f} MXN")
            l_m2.metric("Excedente Neto Líquido Cooperativo", f"${excedente_neto_cooperativa:,.2f} MXN", delta="Disponible para Caja")

        with tab4:
            st.header("Subsistema de Gestión de Riesgos de la Célula Mercantil")
            prima_mensual = st.number_input("Prima Monsual por Taller (MXN)", min_value=50.0, value=prima_individual_global)
            prima_individual_global = prima_mensual
            retorno_pct = st.slider("Porcentaje de Retorno Pactado para la A.C.", min_value=5, max_value=40, value=comision_retorno_global)
            comision_retorno_global = retorno_pct
            prima_anual = float(num_talleres_global * prima_mensual * 12)
            retorno_anual_ac = prima_anual * (retorno_pct / 100)
            st.metric("Retorno de Comisión Anual para la A.C.", f"${retorno_anual_ac:,.2f} MXN")

        with tab5:
            st.header("Caja de Ahorro (El Brazo Fuerte Financiero Interconectado)")
            ahorrio_mensual = st.number_input("Ahorros Directos de los Trabajadores", min_value=0.0, value=55000.0)
            comision_seguros_mensual = float(retorno_anual_ac / 12)
            capital_mensual_total = ahorrio_mensual + comision_seguros_mensual + excedente_coop_calculado
            st.metric("Fondo de Emprendimiento Mensual Consolidado Abierto", f"${capital_mensual_total:,.2f} MXN")

        with tab_log:
            st.header("📑 Historial de Auditoría de Descargas")
            if len(st.session_state["historial_descargas"]) == 0:
                st.info("No se registran descargas en el ciclo actual.")
            else:
                st.table(st.session_state["historial_descargas"])
# ==============================================================================
# PARTE 10 DE 10: COLUMNA DE LA DERECHA - REPOSITORIO ANIDADO Y PIE DE PÁGINA
# ==============================================================================
with col_derecha_documental:
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 15px;'>
        <h3 style='color: #1e4620; margin-top:0; font-size:15px; font-weight:bold;'>📜 Almacén Documental Autónomo</h3>
        <p style='color: #6c757d; font-size:11px; margin-bottom:5px;'>Estructura Completa de 6 Manuales Científicos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # MENÚ DESPLEGABLE INTERACTIVO SECUENCIAL (Nivel 1: Entidad)
    lista_entidades = list(st.session_state["repositorio_institucional"].keys())
    seleccion_entidad = st.selectbox("🏢 1. Selecciona la Entidad / Subsistema:", ["-- Elige una Entidad --"] + lista_entidades)
    
    # MENÚ DESPLEGABLE INTERACTIVO SECUENCIAL (Nivel 2: Marcos y Manuales de la Entidad)
    if seleccion_entidad != "-- Elige una Entidad --":
        lista_marcos = list(st.session_state["repositorio_institucional"][seleccion_entidad].keys())
        seleccion_marco = st.selectbox("📋 2. Selecciona el Documento Oficial:", ["-- Elige el Manual --"] + lista_marcos)
        
        if seleccion_marco != "-- Elige el Marco --":
            st.session_state["ver_visor_legal"] = True
            st.session_state["entidad_seleccionada"] = seleccion_entidad
            st.session_state["tipo_doc_seleccionado"] = seleccion_marco
            st.button("⚡ Abrir Documento en Visor", key="btn_trigger_open_nested")
            
    st.markdown("---")
    
    # CARGADOR DE NUEVAS ESTRUCTURAS CON AUTO-INYECCIÓN DE 6 REPOSITORIOS POR DEFECTO
    st.markdown("#### 📤 Uploading de Nuevas Estructuras")
    archivo_cargado = st.file_uploader("Sube un acta o instructivo complementario (.txt):", type=["txt"])
    
    if archivo_cargado is not None:
        nombre_archivo_crudo = archivo_cargado.name.replace(".txt", "")
        if nombre_archivo_crudo not in st.session_state["repositorio_institucional"]:
            try:
                contenido_texto = archivo_cargado.read().decode("utf-8", errors="ignore")
                st.session_state["repositorio_institucional"][nombre_archivo_crudo] = {
                    "Marco conceptual y descriptivo": contenido_texto,
                    "Marco legal": "Borrador de marco legal en espera de adición fiscal.",
                    "Manual de procedimientos": "Borrador de manual de procedimientos en espera de adición operativa.",
                    "Manual administrativo": "Borrador de manual administrativo en espera de asignación de control.",
                    "Manual de Tendencias criticas": "Borrador de tendencias críticas en espera de modelado actuarial.",
                    "Manual de Variables latentes con items observables": "Borrador de variables latentes en espera de ítems psicométricos."
                }
                st.success(f"✓ '{nombre_archivo_crudo}' indexado con la estructura de 6 manuales.")
                st.button("🔄 Actualizar Menú", key="refresh_uploader_nested")
            except Exception as e:
                st.error("Error de decodificación.")

# MATRIZ INDUSTRIAL DE CIERRE AL PIE DE LA INTERFAZ
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0; font-size:14px;'>🟢 Nodo Central: Asociación Civil</h4><p style='color: #1c7430; font-size: 12px;'><b>Estatus:</b> 0% IVA / Escudo 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 12px; border-radius: 6px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0; font-size:14px;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 12px;'><b>Impacto:</b> Capitaliza excedentes netos de fletes e intermediación libre de ISR.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0; font-size:14px;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 12px;'><b>Impacto:</b> Transforma primas comerciales de la S.A. en fondos de fomento.</p></div>", unsafe_allow_html=True)
