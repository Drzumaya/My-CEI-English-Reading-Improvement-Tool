import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado estable de PDFs en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# PARTE 1 DE 25: CONFIGURACIÓN CORPORATIVA DEL ENTORNO WEB JZPAC
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - JACOB ZUMAYA PRIANTI, A.C.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ==============================================================================
# PARTE 2 DE 25: INICIALIZACIÓN DE CONTEXTOS Y BANDERAS DE NAVEGACIÓN
# ==============================================================================
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

if "ver_formulario_registro" not in st.session_state:
    st.session_state["ver_formulario_registro"] = False
if "ver_padron_flotante" not in st.session_state:
    st.session_state["ver_padron_flotante"] = False
# ==============================================================================
# PARTE 3 DE 25: BASE DE DATOS DEL PADRÓN DE DIRECTORES CON CLÁUSULA DE AUTONOMÍA
# ==============================================================================
if "directores_registrados" not in st.session_state:
    st.session_state["directores_registrados"] = [
        {
            "Fecha Registro": "2026-08-19 14:22:10",
            "Nombre": "Ing. Carlos Mendoza", 
            "Entidad": "4. Equipo de Investigación Científica APSON", 
            "Puesto": "Director de Transferencia Tecnológica", 
            "RFC": "MEC840512XX1", 
            "Estatus": "Activo / Con Cédula"
        },
        {
            "Fecha Registro": "2026-08-20 09:15:43",
            "Nombre": "Sra. María Elena Ortiz", 
            "Entidad": "2. Cooperativa de Logística (S.C.)", 
            "Puesto": "Directora de Operaciones de Flete", 
            "RFC": "OIME761102XX3", 
            "Estatus": "Activa / Juez de Distrito"
        }
    ]
# ==============================================================================
# PARTE 4 DE 25: MATRIZ DE MANUALES - ASOCIACIÓN CIVIL MATRIZ (TOMOS 1-4)
# ==============================================================================
if "repositorio_institucional" not in st.session_state:
    st.session_state["repositorio_institucional"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL\n\nFunciona como la sociedad controladora social (Holding) que coordina los subsistemas autónomos en Agua Prieta. Diseña los planes de capacitación para el trabajo de la periferia urbana.",
            "Marco legal": "FUNDAMENTACIÓN FISCAL TÍTULO II LISR\n\nTributa en Régimen General corporativo (30% ISR). Blinda sus egresos comunitarios al 100% como deducciones mediante Nómina Asimilada (Art. 94 LISR). Exenta de trasladar el 16% de IVA en capacitación según el Art. 15 de la LIVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS DE GOBERNANZA CENTRAL (MAP-01)\n\n1. Recepción de comisiones de la S.A. y aportaciones cooperativas.\n2. Validación de listas de asistencia de talleres.\n3. Dispersión mensual y timbrado de CFDI de asimilados a salarios.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RECURSOS HUMANOS Y CONTROL (MAC-01)\n\nRegula las políticas de contratación de promotores barriales, el control de activos en comodato y los lineamientos de transparencia para auditorías externas del SAT.",
# ==============================================================================
# PARTE 5 DE 25: MATRIZ DE MANUALES - ASOCIACIÓN CIVIL MATRIZ (TOMOS 5-8)
# ==============================================================================
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS Y RIESGO SOCIOECONÓMICO (MTC-01)\n\nMonitorea la inflación en la franja fronteriza, los cambios en las reglas misceláneas del SAT y el impacto del tipo de cambio peso-dólar en el poder adquisitivo de Agua Prieta.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EVALUACIÓN DE ADOPCIÓN DE PROGRAMAS SOCIALES\n\nVARIABLE LATENTE CENTRAL: 'Aceptación Institucional del Modelo de Economía Popular'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Frecuencia con la que el asociado acude voluntariamente a las mesas de gobernanza.\n2. [X2] Nivel de confianza percibido en la transparencia del manejo de fondos.\n3. [X3] Disposición declarada para transitar de contratos informales a Nómina de Asimilados.\n4. [X4] Grado de recomendación del programa de capacitación de la A.C. a otros microemprendedores del barrio.\n5. [X5] Percepción de mejora en la estabilidad de su negocio tras el cobro vía recibo estatutario.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ADHESIÓN Y ASIMILACIÓN A SALARIOS (A.C. MATRIZ)\n\nCONTRATO que celebran la Asociación Civil Matriz JACOB ZUMAYA PRIANTI, A.C., y el Usuario Inscrito en su carácter de Director Asociado:\n\nPRIMERA: OBJETO. El Usuario acepta la designación técnica para coordinar los talleres de capacitación en Agua Prieta.\n\nSEGUNDA: RÉGIMEN FISCAL. El Usuario manifiesta su consentimiento para someter sus honorarios al régimen de Asimilados a Salarios (Art. 94 Fracc. V de la LISR).\n\nTERCERA: EXENCIÓN DE IVA. Las partes acuerdan que las cuotas extraordinarias de recuperación de Miembros Adherentes quedan exentas de IVA (Art. 15-XII LIVA).",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [XXXX] | CONSTITUCIÓN DE ASOCIACIÓN CIVIL BAJO EL RÉGIMEN GENERAL (TÍTULO II LISR)\n\nEn Agua Prieta, Sonora, ante mí, Notario Público, se formaliza el ACTA CONSTITUTIVA de la persona moral JACOB ZUMAYA PRIANTI, A.C.:\n\nCLÁUSULA PRIMERA: DENOMINACIÓN. La organización se denominará 'JACOB ZUMAYA PRIANTI', seguida de las siglas 'A.C.'.\n\nCLÁUSULA SEGUNDA: OBJETO. Impartir capacitación exenta de IVA (Art. 15 LIVA). Al operar en Título II LISR, los excedentes no se distribuirán como dividendos corporativos, sino que se dispersarán al 100% como erogaciones asimiladas (Art. 94 LISR) para el fomento social."
        },
# ==============================================================================
# PARTE 6 DE 25: MATRIZ DE MANUALES - COOPERATIVA DE LOGÍSTICA (TOMOS 1-4)
# ==============================================================================
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA OPERATIVO DE TRANSPORTE BARRIAL\n\nAsociación de choferes y transportistas de base popular organizados para competir en el mercado de fletes industriales B2B y última milla, absorbiendo la demanda del nearshoring maquilador.",
            "Marco legal": "LEY GENERAL DE SOCIEDADES COOPERATIVAS (LGSC)\n\nSociedad Cooperativa de Producción de Servicios de Responsabilidad Limitada (S.C. de R.L. de C.V.). Las plantas maquiladoras contratantes efectúan la retención del 4% de ISR sobre fletes terrestres.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS OPERATIVOS LOGÍSTICOS (MOP-02)\n\n1. Asignación de rutas comerciales en Agua Prieta.\n2. Auditoría física del Factor de Retorno Vacío (Deadhead).\n3. Retención automática del 6% para el fondo de amortiguación de diésel.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE FLOTILLA Y MANTENIMIENTO (MAF-02)\n\nEstablece los roles de los Asociados Directores en la administración de talleres mecánicos asignados, control de bitácoras de viaje y asignación de viáticos logísticos fronterizos.",
# ==============================================================================
# PARTE 7 DE 25: MATRIZ DE MANUALES - COOPERATIVA DE LOGÍSTICA (TOMOS 5-8)
# ==============================================================================
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS DE TRANSPORTE TRANSFRONTERIZO (MTC-02)\n\nAnaliza los tiempos de espera en las aduanas, la fluctuación estacional de la producción automotriz de las maquiladoras y el impacto de aranceles comerciales en el flujo de fletes.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA OPERATIVA DE LA LOGÍSTICA DE BARRIO\n\nVARIABLE LATENTE CENTRAL: 'Cultura de Optimización de Ruta en Choferes Cooperativistas'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Índice de cumplimiento exacto de los horarios de recolección aduanal.\n2. [X2] Nivel de reducción voluntaria reportada en el Factor de Retorno Vacío.\n3. [X3] Frecuencia de registro y uso correcto de la aplicación Streamlit para el reporte del COK.\n4. [X4] Grado de apego a los lineamientos de mantenimiento preventivo y revisión de presión de neumáticos.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO DE ADHESIÓN INDIVIDUAL DE SOCIO TRABAJADOR COOPERATIVISTA (S.C. LOGÍSTICA)\n\nCONTRATO que celebran la Cooperativa de Logística filial de JACOB ZUMAYA PRIANTI, A.C., y el Socio Conductor:\n\nPRIMERA: RÉGIMEN. El Usuario aporta su trabajo bajo la Ley General de Sociedades Cooperativas (LGSC).\n\nSEGUNDA: LOGÍSTICA. El Socio acepta deducir el Costo por Kilómetro (COK), el Factor de Retorno Vacío y la retención del 4% de ISR.\n\nTERCERA: EXCEDENTES. Los excedentes se inyectarán a la cuenta de la A.C. central para la Caja de Ahorro común.",
            "Acta Constitutiva Notarial Oficial": "BASES CONSTITUTIVAS DE SOCIEDAD COOPERATIVA DE RESPONSABILIDAD LIMITADA (S.C. DE R.L.)\n\nEn Agua Prieta, Sonora, filial estratégica de JACOB ZUMAYA PRIANTI, A.C., se formaliza la cooperativa popular:\n\nCLÁUSULA PRIMERA: RÉGIMEN. Se denominará 'COOPERATIVA DE LOGÍSTICA Y TRANSPORTE TRANSFRONTERIZO DE AGUA PRIETA, S.C. DE R.L. DE C.V.'.\n\nCLÁUSULA SEGUNDA: OBJETO. Servicios de transporte y carga pesada B2B para maquiladoras ancla, aplicando la retención del 4% de ISR del SAT.\n\nCLÁUSULA TERCERA: EXCEDENTES. Al cierre de mes, se deducirá un 6% bruto para amortiguación de diésel y un 5% neto que se transferirá a la cuenta de orden de la A.C. nodriza."
        },
# ==============================================================================
# PARTE 8 DE 25: MATRIZ DE MANUALES - AGENCIA DE MICROSEGUROS (TOMOS 1-4)
# ==============================================================================
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE CONTROL DE RIESGOS COMERCIAL\n\nEntidad financiera diseñada para proteger los activos mecánicos de los talleres populares y mitigar vulnerabilidades por accidentes de trabajo o fallecimiento de líderes comunitarios.",
            "Marco legal": "LEY DE INSTITUCIONES DE SEGUROS Y DE FIANZAS (LISF)\n\nSociedad Anónima regulada por la CNSF. Transfiere legalmente el 20% de las primas a la A.C. mediante contratos de Corretaje Social y capacitación en prevención de accidentes.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS Y ATENCIÓN DE SINIESTROS (MAP-03)\n\n1. Reporte técnico de avería mecánica o accidente en las colonias.\n2. Evaluación social del riesgo y dictamen del Asociado Director.\n3. Liquidación de la reparación con cargo al fondo de reserva.",
            "Manual administrative": "MANUAL ADMINISTRATIVO DE RESERVAS TÉCNICAS Y RECAUDACIÓN (MAR-03)\n\nRegula el proceso de cobranza mensual de las primas a través de plataformas digitales y el resguardo seguro del capital de reserva en instrumentos de renta fija de bajo riesgo.",
# ==============================================================================
# PARTE 9 DE 25: MATRIZ DE MANUALES - AGENCIA DE MICROSEGUROS (TOMOS 5-8)
# ==============================================================================
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS ACTUARIALES EN MICROSEGUROS (MTC-03)\n\nMide la tasa de siniestralidad de los talleres de barrio, la tasa de renovación de pólizas y proyecta modelos de vulnerabilidad ante fallas mecánicas en maquinaria pesada depreciada.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - PERCEPCIÓN DE SEGURIDAD PATRIMONIAL\n\nVARIABLE LATENTE CENTRAL: 'Aversión al Riesgo y Confianza en la Póliza Solidaria'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Puntualidad exacta en el pago de la prima mensual simulada en la plataforma.\n2. [X2] Grado de conocimiento de los talleres sobre el alcance real de las coberturas de siniestralidad.\n3. [X3] Nivel de tranquilidad manifestada por el micro-empresario respecto a la continuidad de su negocio.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO COLECTIVO DE ADHESIÓN A LA PÓLIZA DE MICROSEGUROS FRONTERIZOS\n\nContrato de la filial mercantil de JACOB ZUMAYA PRIANTI, A.C. con el Titular Asegurado:\n\nPRIMERA: COBERTURA. El taller protege sus activos mecánicos (soldadoras, tornos) contra averías o incendios.\n\nSEGUNDA: RETORNO. El 20% de las primas recaudadas se transfiere a la A.C. central bajo el rubro de Honorarios de Capacitación en Prevención de Accidentes.\n\nTERCERA: SINIESTROS. Las liquidaciones de daños se pagarán directo con cargo al fondo de reserva técnico.",
            "Acta Constitutiva Notarial Oficial": "CONSTITUCIÓN DE SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE (RAMO RIESGOS CNSF)\n\nAnte Notario Público, se constituye la filial comercial de la matriz corporativa JACOB ZUMAYA PRIANTI, A.C.:\n\nCLÁUSULA PRIMERA: DENOMINACIÓN. Se constituirá como 'AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA, S.A. DE C.V.'.\n\nCLÁUSULA SEGUNDA: ACCIONES. Para resguardar el patrimonio del barrio, la matriz JACOB ZUMAYA PRIANTI, A.C. retiene la titularidad exclusiva del 99% de las acciones Clase 'A'.\n\nCLÁUSULA TERCERA: RETORNO. La sociedad mercantil se obliga estatutariamente a transferir el 20% de sus primas brutas mensuales a la A.C. por concepto de corretaje social exento de IVA."
        },
# ==============================================================================
# PARTE 10 DE 25: MATRIZ DE MANUALES - EQUIPO CIENTÍFICO APSON (TOMOS 1-4)
# ==============================================================================
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE INVESTIGACIÓN, DESARROLLO E INNOVACIÓN (I+D)\n\nCélula científica encargada de realizar estudios de densidad económica, análisis metalúrgicos para el reciclaje (Upcycling) de las mermas de las maquiladoras y optimización de modelos predictivos de crédito social.",
            "Marco legal": "LEY GENERAL DE HUMANIDADES, CIENCIAS, TECNOLOGÍAS E INNOVACIÓN\n\nOpera bajo el amparo de la Cláusula Estatutaria de Autonomía de los Asociados Directores. Los fondos de investigación científica se consideran aportaciones de fomento exentas de IVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS EN RECOLECCIÓN Y PROCESAMIENTO (MAP-04)\n\n1. Recolección de muestras de mermas industriales (cueros, maderas, polímeros) en las maquiladoras.\n2. Pruebas de resistencia en laboratorios comunitarios.\n3. Transferencia de patentes sociales a los talleres.",
            "Manual administrative": "MANUAL ADMINISTRATIVO DE PROYECTOS Y FIDEICOMISOS CIENTÍFICOS (MAP-04)\n\nCoordina la gobernanza presupuestal de los laboratorios, la asignación de becas de investigación a estudiantes de Agua Prieta y el inventario de reactivos técnicos.",
# ==============================================================================
# PARTE 11 DE 25: MATRIZ DE MANUALES - EQUIPO CIENTÍFICO APSON (TOMOS 5-8)
# ==============================================================================
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS EN INNOVACIÓN INDUSTRIAL (MTC-04)\n\nMapea las tecnologías emergentes de manufactura esbelta automatizada, el volumen de desperdicios utilizables por tipo de maquila y las proyecciones de crecimiento del nearshoring real.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA DE LA TRANSFERENCIA TECNOLÓGICA I+D\n\nVARIABLE LATENTE CENTRAL: 'Capacidad de Absorción del Saber Científico en Talleres de Barrio'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Tasa de adopción de manuales Lean-Barrio y diagramas de flujo técnicos dentro de los procesos diarios.\n2. [X2] Cantidad de mermas industriales recolectadas (cuero, madera) efectivamente transformadas.\n3. [X3] Frecuencia de asistencia de los artesanos a las células de co-diseño del Equipo Científico.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ASIGNACIÓN CIENTÍFICA Y PROPIEDAD INTELECTUAL SOCIAL\n\nContrato del brazo de I+D de JACOB ZUMAYA PRIANTI, A.C. con el Investigador Técnico:\n\nPRIMERA: OBJETO. Ejecución de estudios metalúrgicos de mermas y modelado econométrico de variables latentes.\n\nSEGUNDA: INTELECTUAL. Los diseños y marcas colectivas resultantes pertenecen a la A.C., licenciándose a tasa cero para los talleres.\n\nTERCERA: BECA. Los recursos se canalizarán vía fideicomisos autónomos exentos de IVA.",
            "Acta Constitutiva Notarial Oficial": "PROTOCOLO NOTARIAL DE NOMBRAMIENTO Y APERTURA DE CONSEJO DE INVESTIGACIÓN CIENTÍFICA\n\nAnte Notario, se formaliza el nodo de desarrollo tecnológico amparado por la matriz JACOB ZUMAYA PRIANTI, A.C.:\n\nCLÁUSULA PRIMERA: AUTONOMÍA. Operará bajo el nombre de 'EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON', con poder general delegado para convenios con universidades.\n\nCLÁUSULA SEGUNDA: PATENTES. Las patentes de reciclaje industrial (upcycling) se registrarán ante el IMPI bajo titularidad unificada de la A.C.\n\nCLÁUSULA TERCERA: FONDOS. Las aportaciones públicas o privadas de fomento científico se registrarán en cuentas de orden exentas de IVA corporativo."
        }
    }
# ==============================================================================
# PARTE 12 DE 25: SUBRUTINAS DE AUDITORÍA REGISTRAL Y ACCESO MANDATORIO (SAT/LISR)
# ==============================================================================
def registrar_descarga(modulo, archivo):
    """Inyecta de forma síncrona la estampa de tiempo de las descargas en la bitácora contable."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["historial_descargas"].append({
        "Fecha y Hora": now, 
        "Módulo": modulo, 
        "Archivo Descargado": archivo, 
        "Estatus": "Éxito (Generado en Servidor)"
    })

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

    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l2:
        st.title("🔐 Acceso Restringido")
        st.subheader("Plataforma Integral de Economía Popular")
        st.caption("JACOB ZUMAYA PRIANTI, A.C. • Régimen General Título II LISR • Agua Prieta, Sonora")
        st.text_input("Introduce la contraseña de acceso:", type="password", on_change=password_entered, key="password")
        if st.session_state.get("show_login_error", False):
            st.error("❌ Credenciales inválidas. Intento bloqueado por seguridad.")
        with st.expander("ℹ️ Soporte Técnico"):
            st.caption("Las claves son administradas de forma directa por el Agente Capacitador.")
    return False

if not check_password():
    st.stop()

def logout():
    st.session_state["password_correct"] = False
    st.session_state["show_login_error"] = False
    st.rerun()
# ==============================================================================
# PARTE 13 DE 25: MOTOR DE COMPILACIÓN VANGUARDISTA DE INFORMES INDIVIDUALES
# ==============================================================================
def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto, lang_en=False):
    """Compila estados contables individuales con cabecera asimétrica y logo corporativo."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    color_primario = colors.HexColor("#1e4620")   # Verde Forestal JZPAC
    color_acento = colors.HexColor("#495057")     # Gris Ejecutivo
    
    estilo_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=14, fontName='Helvetica-Bold', textColor=color_primario, spaceAfter=2)
    estilo_sub = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=color_acento, spaceAfter=12)
    estilo_cuerpo = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=10, fontName='Helvetica', leading=15, textColor=colors.HexColor("#212529"), spaceAfter=14)
    estilo_firmas = ParagraphStyle('DocSign', parent=styles['Normal'], fontSize=8, fontName='Helvetica', alignment=1)
    
    story = []
    
    from reportlab.platypus import Image as RLImage
    logo_flowable = ""
    try:
        logo_flowable = [RLImage("JZPACLOGOREDONDO.png", width=42, height=42)]
    except Exception:
        logo_flowable = [Paragraph("<b>🦅 JZPAC</b>", ParagraphStyle('Fb', fontSize=10, textColor=color_primario, alignment=2))]

    sub_label = "Official Validation Report" if lang_en else "Validación Documental de Control Oficial"
    header_text = [
        [Paragraph(f"<b>{titulo_modulo.upper()}</b>", estilo_titulo), logo_flowable],
        [Paragraph(f"<b>JACOB ZUMAYA PRIANTI, A.C.</b> • {sub_label}", estilo_sub), ""]
    ]
    
    header_table = Table(header_text, colWidths=[380.0, 100.0])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('SPAN', (1,0), (1,1)), ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
# ==============================================================================
# PARTE 14 DE 25: CONCLUSIÓN DEL COMPILADOR INDIVIDUAL (LÍNEAS Y TRIPLES FIRMAS)
# ==============================================================================
    color_primario = colors.HexColor("#1e4620")
    divider_line = Table([[""]], colWidths=[480.0])
    divider_line.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, color_primario), ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(divider_line)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    story.append(Spacer(1, 8))
    
    tabla_pdf = Table(datos_tabla, colWidths=[240.0, 240.0])
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), color_primario), ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(tabla_pdf)
    story.append(Spacer(1, 30))
    
    # Cuadro de Triples Firmas de Materialidad para el SAT sin tags HTML prohibidos
    lbl_f1 = "Central Agent" if lang_en else "Agente Capacitador Central"
    lbl_f2 = "Subsystem Director" if lang_en else "Director de Subsistema"
    lbl_f3 = "SAT Control Delegation" if lang_en else "Delegación de Control SAT"
    
    datos_firmas = [
        ["____________________________", "____________________________", "____________________________"],
        [Paragraph(f"<b>{lbl_f1}</b>", estilo_firmas), Paragraph(f"<b>{lbl_f2}</b>", estilo_firmas), Paragraph(f"<b>{lbl_f3}</b>", estilo_firmas)],
        [Paragraph("Jacob Zumaya Prianti, A.C.", estilo_firmas), Paragraph("Gobernanza de Célula de Barrio", estilo_firmas), Paragraph("Materialidad e Inclusión Fiscal", estilo_firmas)]
    ]
    
    tabla_firmas = Table(datos_firmas, colWidths=[155.0, 170.0, 155.0])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(tabla_firmas)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
# ==============================================================================
# PARTE 15 DE 25: ENCUADERNADOR MAESTRO DE LIBROS COMPENDIOS EN ESTILO APA 7
# ==============================================================================
def generar_libro_apa7(nombre_entidad, diccionario_marcos, lang_en=False):
    """Compila toda la documentación de una unidad en un libro formal bilingüe en formato APA 7."""
    buffer_libro = io.BytesIO()
    doc = SimpleDocTemplate(buffer_libro, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    color_corporativo = colors.HexColor("#1e4620")
    
    estilo_portada_titulo = ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=color_corporativo, alignment=1, spaceAfter=15)
    estilo_portada_meta = ParagraphStyle('CoverMeta', fontName='Helvetica', fontSize=10, leading=15, textColor=colors.HexColor("#495057"), alignment=1, spaceAfter=10)
    estilo_apa_h1 = ParagraphStyle('APAH1', fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.black, alignment=1, spaceBefore=24, spaceAfter=12)
    estilo_apa_h2 = ParagraphStyle('APAH2', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.black, alignment=0, spaceBefore=16, spaceAfter=6)
    estilo_apa_parrafo = ParagraphStyle('APABody', fontName='Helvetica', fontSize=11, leading=22, textColor=colors.HexColor("#212529"), spaceAfter=14, firstLineIndent=36)
    estilo_indice = ParagraphStyle('DocIndex', fontName='Helvetica', fontSize=10, textColor=colors.black, spaceAfter=8)
    
    story = []
    story.append(Spacer(1, 20))
    
    from reportlab.platypus import Image as RLImage
    try:
        story.append(RLImage("JZPACLOGOREDONDO.png", width=60, height=65))
        story.append(Spacer(1, 15))
    except Exception:
        pass
# ==============================================================================
# PARTE 16 DE 25: ENCUADERNADOR APA 7 (CONSTRUCCIÓN DEL ÍNDICE BILINGÜE)
# ==============================================================================
    color_corporativo = colors.HexColor("#1e4620")
    lbl_main = "INTEGRATED INSTITUTIONAL COMPENDIUM OF AUTONOMOUS CONTROL" if lang_en else "COMPENDIO INSTITUCIONAL INTEGRAL DE CONTROL VINCULADO"
    lbl_sub = f"Autonomous Technical-Legal Subsystem: {nombre_entidad.upper()}" if lang_en else f"Subsistema Técnico-Legal: {nombre_entidad.upper()}"
    lbl_l1 = "Research Line: Endogenous Growth and Border Value Retention" if lang_en else "Línea de Investigación: Crecimiento Endógeno y Retención de Valor Fronterizo"
    lbl_l2 = "Corporate Author: JZPAC Central Board - Training Agent" if lang_en else "Autor Corporativo: Consejo Directivo Central JZPAC - Agente Capacitador"
    lbl_l3 = "Jurisdiction: Agua Prieta, Sonora, Mexico" if lang_en else "Jurisdicción de la Materia: Agua Prieta, Sonora, México"
    lbl_l4 = f"Certification Date: {datetime.now().strftime('%B %d, %Y')}" if lang_en else f"Fecha de Certificación y Cierre: {datetime.now().strftime('%d de %B de %Y')}"
    lbl_l5 = "Internal Organization Monograph for Validation of Surplus Distribution under Mexican Tax Laws" if lang_en else "Monografía Ejecutiva de Organización interna para Validación del Remanente Distribuible conforme al Título II de la LISR"

    story.append(Paragraph("<b>JACOB ZUMAYA PRIANTI, A.C.</b>", ParagraphStyle('TopN', fontName='Helvetica-Bold', fontSize=11, textColor=color_corporativo, alignment=1, spaceAfter=20)))
    story.append(Paragraph(f"<b>{lbl_main}</b>", estilo_portada_titulo))
    story.append(Paragraph(f"<b>{lbl_sub}</b>", ParagraphStyle('SubC', parent=estilo_portada_titulo, fontSize=13, textColor=colors.black)))
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"<b>{lbl_l1}</b>", estilo_portada_meta))
    story.append(Paragraph(f"<b>{lbl_l2}</b>", estilo_portada_meta))
    story.append(Paragraph(f"<b>{lbl_l3}</b>", estilo_portada_meta))
    story.append(Paragraph(f"<b>{lbl_l4}</b>", estilo_portada_meta))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<i>{lbl_l5}</i>", estilo_portada_meta))
    
    story.append(PageBreak())
    
    # Índice General de Capítulos con puntos de tabulación
    lbl_idx = "GENERAL TABLE OF CONTENTS" if lang_en else "ÍNDICE GENERAL DE CAPÍTULOS"
    story.append(Paragraph(f"<b>{lbl_idx}</b>", estilo_apa_h1))
    story.append(Spacer(1, 15))
    
    num_capitulo = 1
    for titulo_manual in diccionario_marcos.keys():
        linea_puntos = ". " * 32
        lbl_cap = f"Chapter {num_capitulo}" if lang_en else f"Capítulo {num_capitulo}"
        lbl_sec = "[See Section]" if lang_en else "[Ver Sección]"
        renglon_indice = f"<b>{lbl_cap}:</b> {titulo_manual} {linea_puntos} {lbl_sec}"
        story.append(Paragraph(renglon_indice, estilo_indice))
        num_capitulo += 1
        
    story.append(PageBreak())
# ==============================================================================
# PARTE 17 DE 25: CONCLUSIÓN DEL ENCUADERNADOR APA 7 (CIERRE DE ARCHIVOS)
# ==============================================================================
    for titulo_manual, texto_contenido in diccionario_marcos.items():
        story.append(Paragraph(f"<b>{titulo_manual}</b>", estilo_apa_h1))
        story.append(Spacer(1, 10))
        for fragmento in texto_contenido.split('\n\n'):
            if fragmento.strip():
                if fragmento.strip().startswith("ARTÍCULO") or fragmento.strip().startswith("MÓDULO") or ":" in fragmento.split('\n'):
                    story.append(Paragraph(f"<b>{fragmento.strip()}</b>", estilo_apa_h2))
                else:
                    story.append(Paragraph(fragmento.strip(), estilo_apa_parrafo))
        story.append(Spacer(1, 15))
        
    doc.build(story)
    buffer_libro.seek(0)
    return buffer_libro
# ==============================================================================
# PARTE 18 DE 25: CONTROLES SIDEBAR Y DECLARACIÓN DE LA ARQUITECTURA BI-COLUMNA
# ==============================================================================
with st.sidebar:
    st.header("📋 Operaciones")
    st.success("🔒 Conexión Encriptada")
    if st.button("❌ Cerrar Sesión (Logout)", use_container_width=True, type="primary"):
        logout()
    st.markdown("---")
    st.markdown("**Organización:**")
    st.caption("JACOB ZUMAYA PRIANTI, A.C.")
    presupuesto_total = st.number_input("Bolsa Económica Mensual Operativa (MXN)", min_value=10000, value=250000, step=10000)

# SOLUCIÓN DE SINTAXIS Y NAMEERROR: Apertura síncrona obligatoria de las columnas
col_izquierda_matriz, col_derecha_documental = st.columns([0.70, 0.30])

num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_calculado = 0.0
# ==============================================================================
# PARTE 19 DE 25: COLUMNA IZQUIERDA - ENTORNO INTERACTIVO DE PÁGINA FLOTANTE
# ==============================================================================
with col_izquierda_matriz:
    if (st.session_state["ver_visor_legal"] and 
        st.session_state["entidad_seleccionada"] in st.session_state["repositorio_institucional"] and 
        st.session_state["tipo_doc_seleccionado"] in st.session_state["repositorio_institucional"][st.session_state["entidad_seleccionada"]]):
        
        ent = st.session_state["entidad_seleccionada"]
        tdoc = st.session_state["tipo_doc_seleccionado"]
        
        st.info(f"📁 Ventana de Trabajo Activa: {ent} ➔ {tdoc}")
        st.markdown("---")
        
        texto_editable_actual = st.text_area(label="Editor Oficial de Cláusulas e Instructivos:", value=st.session_state["repositorio_institucional"][ent][tdoc], height=380)
        
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("💾 Guardar Ajustes", use_container_width=True):
                st.session_state["repositorio_institucional"][ent][tdoc] = texto_editable_actual
                st.success("✓ Cambios guardados.")
        with b2:
            tabla_legal_dummy = [["Validación de Consistencia", "Aprobado por el Consejo"], ["Fecha de Auditoría", "2026-08-20"], ["Estatus Regulatorio", "Vigente Exento"]]
            # Inyección de la bandera bilingüe al visor individual
            is_english_local = (st.session_state.get("selector_idioma_global", "Español (ES)") == "English (EN)")
            pdf_legal = generar_informe_pdf(f"{ent} - {tdoc}", tabla_legal_dummy, texto_editable_actual, lang_en=is_english_local)
            if st.download_button(label="📥 PDF", data=pdf_legal, file_name=f"{tdoc.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True):
                registrar_descarga(ent, f"{tdoc}.pdf")
        with b3:
            buffer_word = io.BytesIO(texto_editable_actual.encode('utf-8'))
            st.download_button(label="📝 Word", data=buffer_word, file_name=f"{tdoc.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with b4:
            if st.button("🛑 Cerrar Visor", use_container_width=True, type="primary"):
                st.session_state["ver_visor_legal"] = False
                st.rerun()
# ==============================================================================
# PARTE 20 DE 25: COLUMNA IZQUIERDA - FORMULARIO FLOTANTE DE ALTA DE DIRECTORES
# ==============================================================================
    elif st.session_state["ver_formulario_registro"]:
        st.success("📝 Formulario Flotante Activo: Alta y Nombramiento de Directores Asociados")
        st.markdown("---")
        
        datos_universales_mexico = {
            "1. Asociación Civil Matriz (A.C.)": {"Regimen_SAT": "Régimen General de Ley de las Personas Morales (Título II LISR)", "Obligacion_Fiscal": "Declaración anual en marzo, pagos provisionales mensuales de ISR (30%), entero de retenciones de asimilados.", "Normativa_Clave": "Artículos 15 Fracc. IV y XII de la Ley del IVA (Exención de traslado del 16% en capacitación)."},
            "2. Cooperativa de Logística (S.C.)": {"Regimen_SAT": "Régimen de las Personas Morales con Fines no Lucrativos (Título III LISR)", "Obligacion_Fiscal": "Facturación electrónica de fletes terrestres, aplicación obligatoria de la Retención del 4% de ISR por personas morales.", "Normativa_Clave": "Ley General de Sociedades Cooperativas (LGSC) - Responsabilidad Limitada, fondo de reserva del 6% diésel."},
            "3. Agencia de Microseguros (S.A.)": {"Regimen_SAT": "Régimen General de Ley (Sociedades Anónimas de Capital Variable - Título II LISR)", "Obligacion_Fiscal": "Contabilidad corporativa mercantil auditada, facturación general de pólizas comerciales con desglose de IVA.", "Normativa_Clave": "Ley de Instituciones de Seguros y de Fianzas (LISF) - Cédula vigente ante la Comisión Nacional de Seguros y Fianzas (CNSF)."},
            "4. Equipo de Investigación Científica APSON": {"Regimen_SAT": "Régimen General con asignación de Fideicomisos Tecnológicos Autónomos (Exento por Fomento)", "Obligacion_Fiscal": "Reporte de transparencia de recursos captados de Fondos de Innovación, exención de IVA en contratos de I+D.", "Normativa_Clave": "Ley General de Humanidades, Ciencias, Tecnologías e Innovación - Patentes sociales exentas."}
        }

        f_nom = st.text_input("👤 Nombre Completo del Director a Registrar:", placeholder="Ej. Lic. Alejandro Anaya")
        f_rfc = st.text_input("🆔 Clave de Registro Federal de Contribuyentes (RFC):", max_chars=13, placeholder="Ej. ANAA850423XX9")
        f_entidad = st.selectbox("🏢 Selecciona la Entidad o Subsistema que pasará a dirigir:", list(datos_universales_mexico.keys()))
        f_puesto = st.text_input("💼 Cargo u Oficio Directivo Asignado:", placeholder="Ej. Director General de Operaciones")

        st.markdown(f"#### 🏛️ Datos Universales Obligatorios (Marco Regulatorio Mexicano - {f_entidad})")
        st.markdown(f"""
        <div style='background-color: #f1f3f5; padding: 15px; border-radius: 6px; border-left: 5px solid #1e4620; margin-bottom:15px;'>
            <p style='margin-bottom:5px; font-size:13px;'><b>1. Régimen Fiscal SAT Obligatorio:</b> {datos_universales_mexico[f_entidad]['Regimen_SAT']}</p>
            <p style='margin-bottom:5px; font-size:13px;'><b>2. Declaraciones y Retenciones Críticas:</b> {datos_universales_mexico[f_entidad]['Obligacion_Fiscal']}</p>
            <p style='margin-bottom:0px; font-size:13px;'><b>3. Ley Federal de Control:</b> {datos_universales_mexico[f_entidad]['Normativa_Clave']}</p>
        </div>
        """, unsafe_allow_html=True)

        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("💾 Validar e Inscribir Director", use_container_width=True, type="secondary"):
                if f_nom and f_rfc and f_puesto:
                    st.session_state["directores_registrados"].append({
                        "Fecha Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Nombre": f_nom, "Entidad": f_entidad, "Puesto": f_puesto, "RFC": f_rfc.upper(), "Estatus": "Alta Exitosa / Acta Firmada"
                    })
                    st.success(f"✓ El {f_puesto} ha sido legalmente registrado.")
                else:
                    st.error("Por favor, llena todos los campos obligatorios.")
        with rc2:
            if st.button("🛑 Cancelar y Cerrar Formulario", use_container_width=True, type="primary"):
                st.session_state["ver_formulario_registro"] = False
                st.rerun()
# ==============================================================================
# PARTE 21 DE 25: COLUMNA IZQUIERDA - VISOR DE DATOS EN TIEMPO REAL (PADRÓN)
# ==============================================================================
    elif st.session_state["ver_padron_flotante"]:
        st.warning("👁️ Ventana Flotante de Datos Activa: Monitoreo del Padrón de Directores en Tiempo Real")
        st.markdown("---")
        st.table(st.session_state["directores_registrados"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🛑 Ocultar Vista de Datos y Volver", use_container_width=True, type="primary"):
            st.session_state["ver_padron_flotante"] = False
            st.rerun()
# ==============================================================================
# PARTE 22 DE 25: COLUMNA IZQUIERDA - PESTAÑAS MAESTRAS DE SIMULACIÓN FISCAL
# ==============================================================================
    else:
        # El else condicional maestro se activa si las ventanas flotantes están en falso
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
            distancia_viaje = st.slider("Distancia Promedio por Viaje (Kilómetros):", min_value=10, max_value=150, value=45)
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
# ==============================================================================
# PARTE 23 DE 25: COLUMNA IZQUIERDA - SIMULADORES DE MICROSEGUROS Y FONDOS MULTUALES
# ==============================================================================
        with tab4:
            st.header("Subsistema de Gestión de Riesgos de la Célula Mercantil")
            prima_mensual = st.number_input("Prima Mensual por Taller (MXN)", min_value=50.0, value=prima_individual_global)
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
# PARTE 24 DE 25: COLUMNA DERECHA - GESTOR DE CARGA RECONVERTIDO CON AUTO-INYECCIÓN
# ==============================================================================
    st.markdown("---")
    label_upload = "📤 Upload Complementary Deeds (.txt)" if is_english else "📤 Uploading de Nuevas Actas (.txt)"
    archivo_cargado = st.file_uploader(label_upload, type=["txt"])
    
    if archivo_cargado is not None:
        nombre_archivo_crudo = archivo_cargado.name.replace(".txt", "")
        if nombre_archivo_crudo not in st.session_state["repositorio_institucional"]:
            try:
                # Leer el buffer del archivo en caliente decodificando en UTF-8
                contenido_texto = archivo_cargado.read().decode("utf-8", errors="ignore")
                
                # Inyección automatizada de las 8 carpetas obligatorias del Agente Capacitador JZPAC
                st.session_state["repositorio_institucional"][nombre_archivo_crudo] = {
                    "Marco conceptual y descriptivo": contenido_texto,
                    "Marco legal": "Borrador de marco legal en espera de adición fiscal para JACOB ZUMAYA PRIANTI, A.C.",
                    "Manual de procedimientos": "Borrador de manual de procedimientos en espera de adición operativa.",
                    "Manual administrativo": "Borrador de manual administrativo de control interno.",
                    "Manual de Tendencias criticas": "Borrador de tendencias críticas en espera de modelado actuarial.",
                    "Manual de Variables latentes con items observables": "Borrador de variables latentes con ítems observables (Likert 1-5).",
                    "Contrato de Incorporación y Adhesión Individual": "Borrador de contrato de incorporación individual para Directores Asociados.",
                    "Acta Constitutiva Notarial Oficial": "Borrador de sub-acta constitutiva notarial oficial para firma de asamblea."
                }
                
                msg_success = f"✓ '{archivo_cargado.name}' successfully indexed." if is_english else f"✓ '{archivo_cargado.name}' guardado e indexado."
                st.success(msg_success)
                
                label_refresh = "🔄 Refresh Repository" if is_english else "🔄 Actualizar Menú"
                if st.button(label_refresh, key="refresh_uploader_nested_final"):
                    st.rerun()
            except Exception as e:
                st.error("Error al decodificar o indexar el archivo txt.")
# ==============================================================================
# PARTE 25 DE 25: PIE DE PÁGINA - INFOGRAFÍA DE LA MATRIZ DEL VÍNCULO FINANCIERO
# ==============================================================================
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("""
    <div style='background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 5px solid #28a745; height: 110px;'>
        <h4 style='color: #155724; margin-top:0; font-size:14px; font-weight:bold;'>🟢 Nodo Central: JACOB ZUMAYA PRIANTI, A.C.</h4>
        <p style='color: #1c7430; font-size: 12px; margin-bottom:0;'><b>Estatus SAT:</b> Título II Régimen General corporativo.<br><b>Escudo Fiscal:</b> 0% IVA en capacitación / Mitigación del 30% de ISR vía Nómina de Asimilados.</p>
    </div>
    """, unsafe_allow_html=True)

with col_v2:
    st.markdown("""
    <div style='background-color: #d1ecf1; padding: 12px; border-radius: 6px; border-left: 5px solid #17a2b8; height: 110px;'>
        <h4 style='color: #0c5460; margin-top:0; font-size:14px; font-weight:bold;'>🔵 Brazo Fuerte: Caja de Ahorro Comunitario</h4>
        <p style='color: #117a8b; font-size: 12px; margin-bottom:0;'><b>Contrato Blanco:</b> Fideicomiso y Cuentas de Orden.<br><b>Impacto:</b> Capitaliza excedentes líquidos de fletes logísticos y comisiones exentos de base gravable corporativa.</p>
    </div>
    """, unsafe_allow_html=True)

with col_v3:
    st.markdown("""
    <div style='background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 5px solid #ffc107; height: 110px;'>
        <h4 style='color: #856404; margin-top:0; font-size:14px; font-weight:bold;'>💛 Riesgos: Agencia de Microseguros (S.A.)</h4>
        <p style='color: #9e7e1a; font-size: 12px; margin-bottom:0;'><b>Vínculo CNSF:</b> Intermediario de Pólizas Colectivas de Maquinaria.<br><b>Impacto:</b> Transforma utilidades mercantiles en transferencias del 20% vía Corretaje Social Docente.</p>
    </div>
    """, unsafe_allow_html=True)
