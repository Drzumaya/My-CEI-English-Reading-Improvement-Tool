import streamlit as st
import io
from datetime import datetime
# Motores ReportLab avanzados para paginación dinámica, imágenes y layouts APA 7
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ==============================================================================
# PARTE 1 DE 17: CONFIGURACIÓN INICIAL CON IDENTIDAD CORPORATIVA JZPAC
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - JACOB ZUMAYA PRIANTI, A.C.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ==============================================================================
# PARTE 2 DE 17: INICIALIZACIÓN DE CONTEXTOS Y CONTROL DE SESIÓN REGISTRAL
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
# PARTE 3 DE 17: BASE DE DATOS ACTIVA DEL PADRÓN DE DIRECTORES ASOCIADOS
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
# PARTE 4 DE 17: ALMACÉN DOCUMENTAL - JACOB ZUMAYA PRIANTI, A.C.
# ==============================================================================
if "repositorio_institucional" not in st.session_state:
    st.session_state["repositorio_institucional"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL EN AGUA PRIETA\\n\\nLa institución JACOB ZUMAYA PRIANTI, A.C. funciona como la sociedad controladora social (Holding) que coordina los subsistemas autónomos en la frontera norte. Diseña los planes de capacitación para el trabajo de la periferia urbana.",
            "Marco legal": "FUNDAMENTACIÓN FISCAL DE JACOB ZUMAYA PRIANTI, A.C. (TÍTULO II LISR)\\n\\nTreatando de una persona moral constituida, JACOB ZUMAYA PRIANTI, A.C. tributa en Régimen General corporativo (30% ISR). Blinda sus egresos comunitarios al 100% como deducciones mediante Nómina Asimilada (Art. 94 LISR). Exenta de trasladar el 16% de IVA en capacitación según el Art. 15 Fracc. IV y XII de la LIVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS DE GOBERNANZA CENTRAL (MAP-01) - JZPAC\\n\\n1. Recepción institucional en las cuentas de JACOB ZUMAYA PRIANTI, A.C. de las aportaciones cooperativas.\\n2. Validación de listas de asistencia de talleres.\\n3. Dispersión mensual y timbrado de CFDI de asimilados a salarios.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RECURSOS HUMANOS Y CONTROL - JZPAC\\n\\nRegula las políticas de contratación de promotores barriales dentro de JACOB ZUMAYA PRIANTI, A.C., el control de activos en comodato y los lineamientos de transparencia para auditorías externas del SAT.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS Y RIESGO SOCIOECONÓMICO - JZPAC\\n\\nMonitorea para JACOB ZUMAYA PRIANTI, A.C. la inflación en la franja fronteriza, los cambios en las reglas misceláneas del SAT y el impacto del tipo de cambio peso-dólar en el poder adquisitivo.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES JZPAC - EVALUACIÓN DE ADOPCIÓN DE PROGRAMAS SOCIALES\\n\\nVARIABLE LATENTE CENTRAL: 'Aceptación Institucional del Modelo de Economía Popular de JACOB ZUMAYA PRIANTI, A.C.'\\n\\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\\n1. [X1] Frecuencia con la que el asociado acude voluntariamente a las mesas de gobernanza de JACOB ZUMAYA PRIANTI, A.C.\\n2. [X2] Nivel de confianza percibido en la transparencia del manejo de fondos de la A.C.\\n3. [X3] Disposición declarada para transitar de contratos informales a Nómina de Asimilados de JZPAC.\\n4. [X4] Grado de recomendación del programa de capacitación de JACOB ZUMAYA PRIANTI, A.C. a otros microemprendedores del barrio.\\n5. [X5] Percepción de mejora en la estabilidad de su negocio tras el cobro vía recibo estatutario de JZPAC.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ADHESIÓN Y ASIMILACIÓN A SALARIOS (JACOB ZUMAYA PRIANTI, A.C.)\\n\\nCONTRATO que celebran por una parte la institución JACOB ZUMAYA PRIANTI, A.C., y por la otra el Usuario Inscrito por propio derecho en su carácter de Director Asociado de Célula Barrial, al tenor de las siguientes cláusulas:\\n\\nPRIMERA: OBJETO. El Usuario acepta la designación técnica para coordinar los talleres de capacitación de JACOB ZUMAYA PRIANTI, A.C. en su colonia asignada.\\n\\nSEGUNDA: RÉGIMEN FISCAL. El Usuario manifiesta su consentimiento expreso para someter sus honorarios de apoyo al régimen de Asimilados a Salarios (Art. 94 Fracc. V de la LISR), obligándose JACOB ZUMAYA PRIANTI, A.C. a retener el impuesto correlativo.\\n\\nTERCERA: EXENCIÓN DE IVA. Las partes acuerdan que las cuotas extraordinarias que recaude el Usuario para JACOB ZUMAYA PRIANTI, A.C. se consideran exentas de IVA (Art. 15-XII LIVA) y se integrarán a la Caja de Ahorro.",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [XXXX] | VOLUMEN: [XX]\\nCONSTITUCIÓN DE ASOCIACIÓN CIVIL BAJO EL RÉGIMEN GENERAL DE JACOB ZUMAYA PRIANTI, A.C.\\n\\nEn la ciudad de Agua Prieta, Estado de Sonora, ante mí, Notario Público, comparecen los Asociados Fundadores para formalizar de manera estricta el ACTA CONSTITUTIVA de la persona moral denominada 'JACOB ZUMAYA PRIANTI', seguida de las siglas 'A.C.', sujeta a las siguientes cláusulas:\\n\\nCLÁUSULA PRIMERA: DENOMINACIÓN Y DOMICILIO.\\nLa organización se denominará 'JACOB ZUMAYA PRIANTI, A.C.'. Su domicilio legal definitivo se fija en Agua Prieta, Sonora.\\n\\nCLÁUSULA SEGUNDA: OBJETO SOCIAL Y REMANENTES DISPONIBLES.\\nEl objeto de JACOB ZUMAYA PRIANTI, A.C. consiste en impartir de forma gratuita y exenta de IVA capacitación para el trabajo. Al operar bajo el Régimen General (Título II LISR), los excedentes no se distribuirán como dividendos capitalistas, sino que se capitalizarán en cuentas de orden de JZPAC o se dispersarán al 100% como erogaciones salariales asimiladas (Art. 94 LISR) a los Directores Asociados.\\n\\nCLÁUSULA TERCERA: PATRIMONIO SOCIAL.\\nEl patrimonio de JACOB ZUMAYA PRIANTI, A.C. se integrará por las cuotas ordinarias y extraordinarias de recuperación aportadas por sus miembros (Art. 15-XII LIVA). El órgano supremo es la Asamblea General de Asociados."
        },
# ==============================================================================
# PARTE 5 DE 17: ALMACÉN DOCUMENTAL - COOPERATIVA DE LOGÍSTICA (S.C.)
# ==============================================================================
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA OPERATIVO DE TRANSPORTE VINCULADO A JZPAC\\n\\nAsociación de choferes y transportistas de base popular organizados para competir en el mercado de fletes industriales B2B bajo la supervisión corporativa de JACOB ZUMAYA PRIANTI, A.C.",
            "Marco legal": "LEY GENERAL DE SOCIEDADES COOPERATIVAS (LGSC) EN ENLACE CON JZPAC\\n\\nSociedad Cooperativa de Producción de Servicios de Responsabilidad Limitada. Las plantas maquiladoras contratantes efectúan la retención del 4% de ISR sobre fletes terrestres, reportándose síncronamente en los balances de JACOB ZUMAYA PRIANTI, A.C.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS OPERATIVOS LOGÍSTICOS ENLAZADO CON JZPAC (MOP-02)\\n\\n1. Asignación de rutas comerciales en Agua Prieta coordinadas por JACOB ZUMAYA PRIANTI, A.C.\\n2. Auditoría física del Factor de Retorno Vacío (Deadhead).\\n3. Retención automática del 6% para el fondo de amortiguación de diésel.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE FLOTILLA VINCULADO A JACOB ZUMAYA PRIANTI, A.C.\\n\\nEstablece los roles de los Asociados Directores en la administración de talleres mecánicos asignados por JACOB ZUMAYA PRIANTI, A.C., control de bitácoras de viaje y viáticos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS DE TRANSPORTE - REPORTE JZPAC (MTC-02)\\n\\nAnaliza para JACOB ZUMAYA PRIANTI, A.C. los tiempos de espera en las aduanas, la fluctuación estacional de la producción de las maquiladoras y el impacto de aranceles.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES JZPAC - EFICIENCIA OPERATIVA DE LA LOGÍSTICA\\n\\nVARIABLE LATENTE CENTRAL: 'Cultura de Optimización de Ruta bajo el Modelo JACOB ZUMAYA PRIANTI, A.C.'\\n\\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\\n1. [X1] Índice de cumplimiento de horarios reportados a la mesa de control de JACOB ZUMAYA PRIANTI, A.C.\\n2. [X2] Nivel de reducción voluntaria reportada en el Factor de Retorno Vacío.\\n3. [X3] Frecuencia de registro y uso correcto de la aplicación de JACOB ZUMAYA PRIANTI, A.C. para el COK.\\n4. [X4] Grado de apego a los lineamientos de mantenimiento preventivo dictados por JZPAC.\\n5. [X5] Proporción de fletes ejecutados sin registrar incidencias ante JACOB ZUMAYA PRIANTI, A.C.\\n6. [X6] Disposición del chofer para cooperar en cargas consolidadas organizadas por JZPAC.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO DE ADHESIÓN INDIVIDUAL DE SOCIO CONDUCTOR VINCULADO A JACOB ZUMAYA PRIANTI, A.C.\\n\\nCONTRATO de adhesión que celebran la Sociedad Cooperativa de Logística y Transporte, con el testimonio de validación de JACOB ZUMAYA PRIANTI, A.C., y por la otra el Socio Conductor, bajo las siguientes cláusulas:\\n\\nPRIMERA: ASOCIACIÓN COMUNITARIA. El Usuario aporta su trabajo personal bajo la supervisión institucional de JACOB ZUMAYA PRIANTI, A.C.\\n\\nSEGUNDA: RETENCIONES Y COK. El Socio acepta registrar cada viaje en la aplicación de control analítico de JACOB ZUMAYA PRIANTI, A.C., deduciendo el COK, el Factor de Retorno Vacío y el 4% de retención de ISR.\\n\\nTERCERA: EXCEDENTES. El Socio Conductor reconoce que los excedentes netos de fletes se inyectarán de forma legal a la Caja de Ahorro común de JACOB ZUMAYA PRIANTI, A.C.",
            "Acta Constitutiva Notarial Oficial": "BASES CONSTITUTIVAS DE SOCIEDAD COOPERATIVA FILIAL DE JACOB ZUMAYA PRIANTI, A.C.\\n\\nEn la Ciudad de Agua Prieta, Sonora, se formaliza el Acta de Asamblea Constitutiva de la Sociedad Cooperativa que se organiza bajo la coordinación patrimonial de JACOB ZUMAYA PRIANTI, A.C.:\\n\\nCLÁUSULA PRIMERA: RÉGIMEN Y DENOMINACIÓN.\\nLa sociedad se denominará 'COOPERATIVA DE LOGÍSTICA Y TRANSPORTE TRANSFRONTERIZO DE AGUA PRIETA', S.C. DE R.L. DE C.V., funcionando como subsistema de JACOB ZUMAYA PRIANTI, A.C.\\n\\nCLÁUSULA SEGUNDA: OBJETO COMERCIAL Y ENLACE CORPORATIVO.\\nEl objeto exclusivo consiste en prestar servicios integrales de transporte terrestre B2B. La sociedad operará bajo la asesoría contable de JACOB ZUMAYA PRIANTI, A.C.\\n\\nCLÁUSULA TERCERA: INYECCIÓN A LA AC MATRIZ.\\nQueda estrictamente establecido que al término de cada ejercicio contable mensual calibrado por JACOB ZUMAYA PRIANTI, A.C., se deducirá un 5% neto de excedentes que se inyectará a la cuenta de orden de JACOB ZUMAYA PRIANTI, A.C. para sufragar el sostenimiento técnico del ecosistema."
        },
# ==============================================================================
# PARTE 6 DE 17: ALMACÉN DOCUMENTAL - AGENCIA DE MICROSEGUROS (S.A.)
# ==============================================================================
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE CONTROL DE RIESGOS FILIAL DE JZPAC\\n\\nEntidad financiera coordinada por JACOB ZUMAYA PRIANTI, A.C. diseñada para proteger los activos mecánicos de los talleres populares y mitigar vulnerabilidades por accidentes de trabajo.",
            "Marco legal": "LEY DE INSTITUCIONES DE SEGUROS Y CONTRATO DE ENLACE CON JZPAC\\n\\nSociedad Anónima regulada por la CNSF. Transfiere legalmente el 20% de las primas a JACOB ZUMAYA PRIANTI, A.C. mediante contratos de Corretaje Social y capacitación en prevención de accidentes.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS Y ATENCIÓN DE SINIESTROS DE JZPAC (MAP-03)\\n\\n1. Reporte técnico de avería mecánica o accidente enviado a JACOB ZUMAYA PRIANTI, A.C.\\n2. Evaluación social del riesgo y dictamen del Asociado Director.\\n3. Liquidación de la reparación con cargo al fondo de reserva de JZPAC.",
            "Manual administrative": "MANUAL ADMINISTRATIVO DE RESERVAS TÉCNICAS E INTERFACES CON JZPAC (MAR-03)\\n\\nRegula el proceso de cobranza mensual de las primas e interconexión de datos con JACOB ZUMAYA PRIANTI, A.C., y el resguardo seguro del capital de reserva.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS ACTUARIALES - REPORTE JZPAC (MTC-03)\\n\\nMide para JACOB ZUMAYA PRIANTI, A.C. la tasa de siniestralidad de los talleres de barrio, la tasa de renovación de pólizas y proyecta modelos de vulnerabilidad.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES JZPAC - PERCEPCIÓN DE SEGURIDAD PATRIMONIAL\\n\\nVARIABLE LATENTE CENTRAL: 'Confianza en la Póliza Solidaria de JACOB ZUMAYA PRIANTI, A.C.'\\n\\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\\n1. [X1] Puntualidad exacta en el pago de la prima mensual simulada en la plataforma de JACOB ZUMAYA PRIANTI, A.C.\\n2. [X2] Grado de conocimiento de los talleres sobre el alcance de las coberturas dictadas por JZPAC.\\n3. [X3] Nivel de tranquilidad manifestada por el micro-empresario respecto al respaldo de JACOB ZUMAYA PRIANTI, A.C.\\n4. [X4] Frecuencia con la que el micro-taller reporta de forma preventiva riesgos al Asociado Director de JZPAC.\\n5. [X5] Confianza declarada en la velocidad de respuesta del fondo de reserva de JACOB ZUMAYA PRIANTI, A.C.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO COLECTIVO DE ADHESIÓN A LA PÓLIZA DE MICROSEGUROS DE JACOB ZUMAYA PRIANTI, A.C.\\n\\nCONTRATO que celebran la Agencia de Protección Solidaria Fronteriza, y por la otra el Usuario Inscrito, bajo las siguientes cláusulas institucionales:\\n\\nPRIMERA: COBERTURA. El Usuario se adhiere a la póliza comunitaria colectiva validada por JACOB ZUMAYA PRIANTI, A.C. para proteger sus activos mecánicos y herramientas.\\n\\nSEGUNDA: PRIMA SOCIAL Y RETORNO. El Asegurado reconoce que el 20% de dicha recaudación es transferido a JACOB ZUMAYA PRIANTI, A.C. por concepto de Honorarios de Capacitación, libre de IVA comercial.\\n\\nTERCERA: RECLAMACIÓN. En caso de siniestro, el Usuario se somete al Manual de Procedimientos de JACOB ZUMAYA PRIANTI, A.C., el cual dictaminará el pago inmediato.",
            "Acta Constitutiva Notarial Oficial": "CONSTITUCIÓN DE SOCIEDAD ANÓNIMA FILIAL PATRIMONIAL DE JACOB ZUMAYA PRIANTI, A.C.\\n\\nEn la Ciudad de Agua Prieta, Estado de Sonora, ante mí, Notario, se formaliza la constitución de la Sociedad Anónima subordinada patrimonialmente a JACOB ZUMAYA PRIANTI, A.C.:\\n\\nCLÁUSULA PRIMERA: DENOMINACIÓN CORPORATIVA.\\nLa denominación oficial será 'AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA', S.A. DE C.V., operando bajo el control institucional de JACOB ZUMAYA PRIANTI, A.C.\\n\\nCLÁUSULA SEGUNDA: CAPITAL SOCIAL Y DOMINIO DE JACOB ZUMAYA PRIANTI, A.C.\\nEl capital social es variable. Para blindar el patrimonio e impedir desvíos capitalistas, la institución JACOB ZUMAYA PRIANTI, A.C. retiene la titularidad del 99% de las acciones Clase 'A', teniendo el voto mayoritario absoluto.\\n\\nCLÁUSULA TERCERA: GOBERNANZA Y RETORNO CORRETAJE A LA AC.\\nLa sociedad se obliga por estipulación estatutaria a transferir el 20% de las primas brutas capturadas mensuales a JACOB ZUMAYA PRIANTI, A.C. bajo el rubro de Honorarios de Corretaje Social y Docencia."
        },
# ==============================================================================
# PARTE 7 DE 17: ALMACÉN DOCUMENTAL - EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON
# ==============================================================================
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE INVESTIGACIÓN, DESARROLLO E INNOVACIÓN DE JZPAC\\n\\nCélula científica de JACOB ZUMAYA PRIANTI, A.C. encargada de realizar estudios de densidad económica, análisis metalúrgicos para el reciclaje de mermas y optimización de modelos predictivos.",
            "Marco legal": "LEY DE CIENCIA E INNOVACIÓN - ESTATUTOS INTERNOS DE JACOB ZUMAYA PRIANTI, A.C.\\n\\nOpera bajo el amparo de la Cláusula Estatutaria de Autonomía delegada por JACOB ZUMAYA PRIANTI, A.C. Los fondos captados se consideran aportaciones de fomento exentas de IVA en las declaraciones de JZPAC.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS EN PROCESAMIENTO CIENTÍFICO DE JZPAC (MAP-04)\\n\\n1. Recolección de muestras de mermas industriales bajo convenios de JACOB ZUMAYA PRIANTI, A.C.\\n2. Pruebas de resistencia en laboratorios comunitarios.\\n3. Transferencia de patentes sociales a los talleres vinculados a JZPAC.",
            "Manual administrative": "MANUAL ADMINISTRATIVO DE PROYECTOS CIENTÍFICOS DE JACOB ZUMAYA PRIANTI, A.C.\\n\\nCoordina la gobernanza presupuestal de los laboratorios, la asignación de becas de investigación otorgadas por JACOB ZUMAYA PRIANTI, A.C. a estudiantes universitarios de Agua Prieta y reactivos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS INDUSTRIALES - REPORTE JZPAC (MTC-04)\\n\\nMapea para JACOB ZUMAYA PRIANTI, A.C. las tecnologías emergentes de manufactura esbelta, el volumen de desperdicios utilizables por tipo de maquila y el nearshoring real.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES JZPAC - EFICIENCIA DE LA TRANSFERENCIA TECNOLÓGICA\\n\\nVARIABLE LATENTE CENTRAL: 'Capacidad de Absorción del Saber Científico de JACOB ZUMAYA PRIANTI, A.C.'\\n\\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\\n1. [X1] Tasa de adopción de manuales de JACOB ZUMAYA PRIANTI, A.C. dentro de los procesos diarios del taller.\\n2. [X2] Cantidad de mermas industriales transformadas bajo asesoría de JACOB ZUMAYA PRIANTI, A.C.\\n3. [X3] Frecuencia de asistencia de los artesanos a las células de co-diseño de JACOB ZUMAYA PRIANTI, A.C.\\n4. [X4] Reducción porcentual de costos de materia prima lograda mediante el reciclaje de JZPAC.\\n5. [X5] Nivel de comprensión técnica sobre maquinaria pesada financiada por JACOB ZUMAYA PRIANTI, A.C.\\n6. [X6] Cantidad de innovaciones locales generadas de forma autónoma por la comunidad de JZPAC.\\n7. [X7] Incremento reportado en la calidad final entregada a las plantas maquiladoras transnacionales.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ASIGNACIÓN CIENTÍFICA (EQUIPO APSON - JZPAC)\\n\\nCONTRATO que celebran la institución JACOB ZUMAYA PRIANTI, A.C., y por la otra el Investigador o Técnico de Laboratorio Comunitario, al tenor de las siguientes cláusulas:\\n\\nPRIMERA: OBJETO. El Investigador se compromete a ejecutar análisis y modelado de variables latentes bajo los planes rectores de JACOB ZUMAYA PRIANTI, A.C.\\n\\nSEGUNDA: PATENTES SOCIALES. El Usuario acepta que toda propiedad intelectual desarrollada pertenece al patrimonio común de JACOB ZUMAYA PRIANTI, A.C., licenciándose a tasa cero para el beneficio de los talleres populares.\\n\\nTERCERA: REMUNERACIÓN. Las retribuciones se canalizarán a través de la Caja de Ahorro de JACOB ZUMAYA PRIANTI, A.C., justificando la materialidad docente ante el SAT.",
            "Acta Constitutiva Notarial Oficial": "PROTOCOLO NOTARIAL DE NOMBRAMIENTO DEL CONSEJO CIENTÍFICO DE JACOB ZUMAYA PRIANTI, A.C.\\n\\nEn la Ciudad de Agua Prieta, Sonora, ante la fe del Notario Público, se formaliza el Acta de Establecimiento de la célula científica constituida por acuerdo de la Asamblea General de JACOB ZUMAYA PRIANTI, A.C.:\\n\\nCLÁUSULA PRIMERA: AUTONOMÍA OPERATIVA.\\nEl subsistema científico operará bajo el nombre de 'EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON'. Goza de una Cláusula de Autonomía delegada por JACOB ZUMAYA PRIANTI, A.C.\\n\\nCLÁUSULA SEGUNDA: FINES CIENTÍFICOS Y PROPIEDAD DE JZPAC.\\nEl objeto consiste en ejecutar investigación econométrica. Toda patente resultante se registrará ante el IMPI a nombre de la institución JACOB ZUMAYA PRIANTI, A.C., quedando bajo un fideicomiso social de JZPAC.\\n\\nCLÁUSULA TERCERA: GOVERNANZA PRESUPUESTAL.\\nLos fondos captados se depositarán directamente en la cuenta de orden de la Caja de Ahorro de JACOB ZUMAYA PRIANTI, A.C., amparando la materialidad de las investigaciones exentas de IVA."
        }
    }
# ==============================================================================
# PARTE 8 DE 17: SUBRUTINAS DE AUDITORÍA REGISTRAL CENTRAL FISCAL
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
# ==============================================================================
# PARTE 9 DE 17: MOTOR DE COMPILACIÓN VANGUARDISTA CORREGIDO (SIN ERRORES DE TAGS)
# ==============================================================================
def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto):
    """Compila estados contables en un formato PDF vanguardista libre de errores de tags HTML."""
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
    
    # --- CONSTRUCCIÓN SEGURA DEL ENCABEZADO ASIMÉTRICO ---
    # Procesar el logotipo como un objeto Flowable real dentro de una lista de celdas
    from reportlab.platypus import Image as RLImage
    logo_flowable = ""
    try:
        logo_flowable = [RLImage("JZPACLOGOREDONDO.png", width=42, height=42)]
    except Exception:
        logo_flowable = [Paragraph("<b>🦅 JZPAC</b>", ParagraphStyle('Fb', fontSize=10, textColor=color_primario, alignment=2))]

    header_text = [
        [Paragraph(f"<b>{titulo_modulo.upper()}</b>", estilo_titulo), logo_flowable],
        [Paragraph("<b>JACOB ZUMAYA PRIANTI, A.C.</b> • Ecosistema de Economía Popular AP-AC", estilo_sub), ""]
    ]
    
    header_table = Table(header_text, colWidths=[380.0, 100.0])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (1,0), (1,1)), # Expandir el logotipo en el ala derecha de la cabecera
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    
    # Línea Divisoria Industrial
    divider_line = Table([[""]], colWidths=[480.0])
    divider_line.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, color_primario),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(divider_line)
    story.append(Spacer(1, 10))
    
    # Texto del Manual / Simulador
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    story.append(Spacer(1, 8))
    
    # Matriz Analítica con colWidths reparado
    tabla_pdf = Table(datos_tabla, colWidths=[240.0, 240.0])
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), color_primario), ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(tabla_pdf)
    story.append(Spacer(1, 30))
    
    # --- CONSTRUCCIÓN SEGURA DEL CUADRO DE TRIPLES FIRMAS (SIN TAGS <BR> CONFLICTIVOS) ---
    datos_firmas = [
        ["____________________________", "____________________________", "____________________________"],
        [Paragraph("<b>Agente Capacitador Central</b>", estilo_firmas),
         Paragraph("<b>Director de Subsistema</b>", estilo_firmas),
         Paragraph("<b>Delegación de Control SAT</b>", estilo_firmas)],
        [Paragraph("Jacob Zumaya Prianti, A.C.", estilo_firmas),
         Paragraph("Gobernanza de Célula de Barrio", estilo_firmas),
         Paragraph("Materialidad e Inclusión Fiscal", estilo_firmas)]
    ]
    
    tabla_firmas = Table(datos_firmas, colWidths=[155.0, 170.0, 155.0])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(tabla_firmas)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
# ==============================================================================
# PARTE 10 DE 17: MOTOR DE ENCUADERNACIÓN DE MONOGRAFÍAS CON ÍNDICE SEGURO (APA 7)
# ==============================================================================
def generar_libro_apa7(nombre_entidad, diccionario_marcos):
    """Compila e imprime toda la documentación de una entidad en un libro estilo APA 7 con Índice Seguro."""
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
    
    # Inyección Controlada del Logo en la Portada del Libro
    from reportlab.platypus import Image as RLImage
    try:
        story.append(RLImage("JZPACLOGOREDONDO.png", width=60, height=65))
        story.append(Spacer(1, 15))
    except Exception:
        pass
        
    story.append(Paragraph("<b>JACOB ZUMAYA PRIANTI, A.C.</b>", ParagraphStyle('TopN', fontName='Helvetica-Bold', fontSize=11, textColor=color_corporativo, alignment=1, spaceAfter=20)))
    story.append(Paragraph("<b>COMPENDIO INSTITUCIONAL INTEGRAL DE CONTROL VINCULADO</b>", estilo_portada_titulo))
    story.append(Paragraph(f"<b>Subsistema Técnico-Legal: {nombre_entidad.upper()}</b>", ParagraphStyle('SubC', parent=estilo_portada_titulo, fontSize=13, textColor=colors.black)))
    st.markdown("<div style='padding-top:5px;'></div>", unsafe_allow_html=True)
    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>Línea de Investigación:</b> Crecimiento Endógeno y Retención de Valor Fronterizo", estilo_portada_meta))
    story.append(Paragraph("<b>Autor Corporativo:</b> Consejo Directivo Central JZPAC - Agente Capacitador", estilo_portada_meta))
    story.append(Paragraph("<b>Jurisdicción de la Materia:</b> Agua Prieta, Sonora, México", estilo_portada_meta))
    story.append(Paragraph(f"<b>Fecha de Certificación y Cierre:</b> {datetime.now().strftime('%d de %B de %Y')}", estilo_portada_meta))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Monografía Ejecutiva de Organización interna para Validación del Remanente Distribuible conforme al Título II de la LISR</i>", estilo_portada_meta))
    
    story.append(PageBreak())
    
    # Índice Analítico General
    story.append(Paragraph("<b>ÍNDICE GENERAL DE CAPÍTULOS</b>", estilo_apa_h1))
    story.append(Spacer(1, 15))
    
    num_capitulo = 1
    for titulo_manual in diccionario_marcos.keys():
        linea_puntos = ". " * 32
        renglon_indice = f"<b>Capítulo {num_capitulo}:</b> {titulo_manual} {linea_puntos} [Ver Sección]"
        story.append(Paragraph(renglon_indice, estilo_indice))
        num_capitulo += 1
        
    story.append(PageBreak())
    
    # Despliegue de los Tomos del Manual
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
# PARTE 10 DE 17: COMPILADOR DE LIBROS COMPENDIOS CON ÍNDICE DE CONTENIDOS APA 7
# ==============================================================================
class NumberedCanvasLibro(canvas.Canvas):
    """Lienzo avanzado de dos pasadas para compendios corporativos JZPAC."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            # La portada (Página 1) no lleva encabezado tipográfico según la norma APA 7
            if self._pageNumber > 1:
                self.draw_libro_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_libro_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1e4620"))
        self.drawString(72, 745, "JACOB ZUMAYA PRIANTI, A.C.")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.gray)
        self.drawRightString(540, 745, f"Página {self._pageNumber} de {page_count}")
        self.setStrokeColor(colors.HexColor("#dee2e6"))
        self.setLineWidth(0.5)
        self.line(72, 737, 540, 737)
        try:
            self.drawImage("JZPACLOGOREDONDO.png", 72, 750, width=22, height=21, mask='auto')
        except Exception:
            pass
        self.restoreState()

def generar_libro_apa7(nombre_entidad, diccionario_marcos):
    buffer_libro = io.BytesIO()
    doc = SimpleDocTemplate(buffer_libro, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=85, bottomMargin=72)
    styles = getSampleStyleSheet()
    color_corporativo = colors.HexColor("#1e4620")
    
    estilo_portada_titulo = ParagraphStyle('CovT', fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=color_corporativo, alignment=1, spaceAfter=20)
    estilo_portada_meta = ParagraphStyle('CovM', fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor("#495057"), alignment=1, spaceAfter=12)
    estilo_apa_h1 = ParagraphStyle('APAH1', fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.black, alignment=1, spaceBefore=20, spaceAfter=12)
    estilo_apa_h2 = ParagraphStyle('APAH2', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.black, alignment=0, spaceBefore=15, spaceAfter=6)
    estilo_apa_parrafo = ParagraphStyle('APABody', fontName='Helvetica', fontSize=11, leading=20, textColor=colors.HexColor("#212529"), spaceAfter=14, firstLineIndent=36)
    
    story = []
    # --- 1. PORTADA ---
    story.append(Spacer(1, 80))
    story.append(Paragraph(f"<b>COMPENDIO INSTITUCIONAL INTEGRAL VINCULADO</b>", estilo_portada_titulo))
    story.append(Paragraph(f"<b>{nombre_entidad.upper()}</b>", ParagraphStyle('SubC', parent=estilo_portada_titulo, fontSize=15, textColor=colors.black)))
    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>Autor Corporativo:</b> JACOB ZUMAYA PRIANTI, A.C.", estilo_portada_meta))
    story.append(Paragraph("<b>Línea:</b> Crecimiento Endógeno y Retención de Valor Fronterizo", estilo_portada_meta))
    story.append(Paragraph("<b>Jurisdicción:</b> Agua Prieta, Sonora, México", estilo_portada_meta))
    story.append(Paragraph(f"<b>Fecha de Emisión:</b> {datetime.now().strftime('%d de %B de %Y')}", estilo_portada_meta))
    story.append(PageBreak())
    
    # --- 2. ÍNDICE GENERAL AUTOMATIZADO (TABLA DE CONTENIDOS APA 7) ---
    story.append(Paragraph("<b>Tabla de Contenidos (Índice General)</b>", estilo_apa_h1))
    story.append(Spacer(1, 10))
    story.append(Paragraph("A continuación se detallan las secciones y manuales normativos constitutivos validados para la presente célula:", ParagraphStyle('IdxB', fontName='Helvetica', fontSize=10, spaceAfter=15)))
    
    tabla_indice_datos = [["Sección / Documento Oficial Regulado", "Estatus Contable", "Referencia"]]
    for titulo_manual in diccionario_marcos.keys():
        tabla_indice_datos.append([titulo_manual, "Validado SAT Título II", "Indexado síncrono"])
        
    tabla_idx = Table(tabla_indice_datos, colWidths=[240.0, 130.0, 110.0])
    tabla_idx.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),
        ('TEXTCOLOR', (0, 0), (-1, 0), color_corporativo),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(tabla_idx)
    story.append(PageBreak())
    
    # --- 3. CONTENIDO EN CASCADA ---
    for titulo_manual, texto_contenido in diccionario_marcos.items():
        story.append(Paragraph(f"<b>{titulo_manual}</b>", estilo_apa_h1))
        story.append(Spacer(1, 8))
        for fragmento in texto_contenido.split('\n\n'):
            if fragmento.strip():
                if fragmento.strip().startswith("ARTÍCULO") or fragmento.strip().startswith("CLÁUSULA") or ":" in fragmento.split('\n'):
                    story.append(Paragraph(f"<b>{fragmento.strip()}</b>", estilo_apa_h2))
                else:
                    story.append(Paragraph(fragmento.strip(), estilo_apa_parrafo))
        story.append(Spacer(1, 10))
        
    doc.build(story, canvasmaker=NumberedCanvasLibro)
    buffer_libro.seek(0)
    return buffer_libro
# ==============================================================================
# PARTE 11 DE 17: CONTROLES SIDEBAR Y PARTICIÓN DE ARQUITECTURA DE LIENZO
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

col_izquierda_matriz, col_derecha_documental = st.columns([0.70, 0.30])

num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_calculado = 0.0
# ==============================================================================
# PARTE 12 DE 17: COLUMNA IZQUIERDA - VISOR DE MANUALES LEAN EN CALIENTE
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
            pdf_legal = generar_informe_pdf(f"{ent} - {tdoc}", tabla_legal_dummy, texto_editable_actual)
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
# PARTE 13 DE 17: COLUMNA IZQUIERDA - FORMULARIO FLOTANTE DE ALTA DE DIRECTORES
# ==============================================================================
    elif st.session_state["ver_formulario_registro"]:
        st.success("📝 Formulario Flotante Activo: Alta y Nombramiento de Directores Asociados")
        st.markdown("---")
        
        datos_universales_mexico = {
            "1. Asociación Civil Matriz (A.C.)": {"Regimen_SAT": "Régimen General de Ley de las Personas Morales (Título II LISR)", "Obligacion_Fiscal": "Declaración anual en marzo, pagos provisionales mensuales de ISR (30%), entero de retenciones de asimilados.", "Normativa_Clave": "Artículos 15 Fracc. IV y XII de la Ley del IVA (Exención de traslado del 16% en capacitación de JACOB ZUMAYA PRIANTI, A.C.)."},
            "2. Cooperativa de Logística (S.C.)": {"Regimen_SAT": "Régimen de las Personas Morales con Fines no Lucrativos (Título III LISR)", "Obligacion_Fiscal": "Facturación electrónica de fletes terrestres, aplicación obligatoria de la Retención del 4% de ISR por personas morales.", "Normativa_Clave": "Ley General de Sociedades Cooperativas (LGSC) - Responsabilidad Limitada, fondo de reserva del 6% diésel vinculada a JZPAC."},
            "3. Agencia de Microseguros (S.A.)": {"Regimen_SAT": "Régimen General de Ley (Sociedades Anónimas de Capital Variable - Título II LISR)", "Obligacion_Fiscal": "Contabilidad corporativa mercantil auditada, facturación general de pólizas con desglose de IVA.", "Normativa_Clave": "Ley de Instituciones de Seguros y de Fianzas (LISF) - Cédula vigente ante la Comisión Nacional de Seguros y Fianzas (CNSF)."},
            "4. Equipo de Investigación Científica APSON": {"Regimen_SAT": "Régimen General con asignación de Fideicomisos Tecnológicos Autónomos (Exento por Fomento)", "Obligacion_Fiscal": "Reporte de transparencia de recursos captados de Fondos de Innovación de JACOB ZUMAYA PRIANTI, A.C., exención de IVA en contratos de I+D.", "Normativa_Clave": "Ley General de Humanidades, Ciencias, Tecnologías e Innovación - Patentes sociales exentas."}
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
                        "Nombre": f_nom, "Entidad": f_entidad, "Puesto": f_puesto, "RFC": f_rfc.upper(), "Estatus": "Alta Exitosa / Acta Firmada / JZPAC"
                    })
                    st.success(f"✓ El {f_puesto} ha sido legalmente registrado en JACOB ZUMAYA PRIANTI, A.C.")
                else:
                    st.error("Por favor, llena todos los campos obligatorios.")
        with rc2:
            if st.button("🛑 Cancelar y Cerrar Formulario", use_container_width=True, type="primary"):
                st.session_state["ver_formulario_registro"] = False
                st.rerun()
# ==============================================================================
# PARTE 14 DE 17: COLUMNA IZQUIERDA - VISOR DE DATOS EN TIEMPO REAL (PADRÓN)
# ==============================================================================
    elif st.session_state["ver_padron_flotante"]:
        st.warning("👁️ Ventana Flotante de Datos Activa: Monitoreo del Padrón de Directores de JACOB ZUMAYA PRIANTI, A.C.")
        st.markdown("---")
        st.table(st.session_state["directores_registrados"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🛑 Ocultar Vista de Datos y Volver", use_container_width=True, type="primary"):
            st.session_state["ver_padron_flotante"] = False
            st.rerun()
# ==============================================================================
# PARTE 14 DE 17: COLUMNA IZQUIERDA - VISOR DE DATOS EN TIEMPO REAL (PADRÓN)
# ==============================================================================
    elif st.session_state["ver_padron_flotante"]:
        st.warning("👁️ Ventana Flotante de Datos Activa: Monitoreo del Padrón de Directores de JACOB ZUMAYA PRIANTI, A.C.")
        st.markdown("---")
        st.table(st.session_state["directores_registrados"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🛑 Ocultar Vista de Datos y Volver", use_container_width=True, type="primary"):
            st.session_state["ver_padron_flotante"] = False
            st.rerun()
# ==============================================================================
# PARTE 15 DE 17: COLUMNA IZQUIERDA - SIMULADORES Y PROCESOS DE TRABAJO ORDINARIOS
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
# PARTE 16 DE 17: COLUMNA DE LA DERECHA - LOGOTIPO E IDENTIDAD INSTITUCIONAL
# ==============================================================================
with col_derecha_documental:
    # Contenedor gráfico maestro con nombre de la A.C.
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; margin-bottom: 12px; text-align: center;'>
        <h2 style='color: #1e4620; margin-top:0; font-size:16px; font-weight:bold; text-transform: uppercase; letter-spacing: 0.5px;'>
            JACOB ZUMAYA PRIANTI, A.C.
        </h2>
        <p style='color: #6c757d; font-size:11px; margin-bottom:10px;'>Ecosistema de Economía Popular Fronteriza</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Renderizado del logotipo directo del repositorio
    try:
        st.image("JZPACLOGOREDONDO.png", caption="Logotipo Oficial JZPAC", use_container_width=True)
    except Exception:
        st.caption("🦅 [Imagen: JZPACLOGOREDONDO.png Cargada en Repositorio]")
        
    st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
    st.markdown("<b style='font-size:13px; color:#495057;'>🗂️ Almacén Documental Autónomo:</b>", unsafe_allow_html=True)
    
    lista_entidades = list(st.session_state["repositorio_institucional"].keys())
    seleccion_entidad = st.selectbox("🏢 1. Selecciona la Entidad / Subsistema:", ["-- Elige una Entidad --"] + lista_entidades)
    
    if seleccion_entidad != "-- Elige una Entidad --":
        st.markdown("#### 📘 Compilar Libro Unificado (APA 7)")
        st.caption("Encuaderna la totalidad de manuales, formatos y contratos con Índice y Paginación en un solo click.")
        
        dict_marcos_libro = st.session_state["repositorio_institucional"][seleccion_entidad]
        pdf_libro_completo = generar_libro_apa7(seleccion_entidad, dict_marcos_libro)
        
        # Invocación segura sin NameError (la función ya fue declarada al inicio del archivo)
        if st.download_button(label="📥 Descargar Libro Compendio (PDF)", data=pdf_libro_completo, file_name=f"Compendio_{seleccion_entidad.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True):
            registrar_descarga(seleccion_entidad, f"Compendio_{seleccion_entidad.replace(' ', '_')}.pdf")
            
        st.markdown("---")
        
        lista_marcos = list(st.session_state["repositorio_institucional"][seleccion_entidad].keys())
        seleccion_marco = st.selectbox("📋 2. O editar un documento individual:", ["-- Elige el Manual --"] + lista_marcos)
        
        if seleccion_marco != "-- Elige el Manual --":
            st.session_state["entidad_seleccionada"] = seleccion_entidad
            st.session_state["tipo_doc_seleccionado"] = seleccion_marco
            st.session_state["ver_visor_legal"] = True
            st.session_state["ver_formulario_registro"] = False
            st.session_state["ver_padron_flotante"] = False
            if st.button("⚡ Abrir Documento en Visor", key="btn_trigger_open_nested"):
                st.rerun()
            
    st.markdown("---")
    st.markdown("#### 👔 Gobernanza e Historiales")
    
    # Botonera Central de control de altas y visibilidad de base de datos
    if st.button("➕ Inscribir Director Asociado", use_container_width=True, type="primary"):
        st.session_state["ver_formulario_registro"] = True
        st.session_state["ver_visor_legal"] = False 
        st.session_state["ver_padron_flotante"] = False
        st.rerun()
        
    st.markdown("<div style='padding-top:5px;'></div>", unsafe_allow_html=True)
    
    if st.session_state.get("ver_padron_flotante", False):
        if st.button("🙈 Ocultar Padrón de Datos", use_container_width=True, type="secondary"):
            st.session_state["ver_padron_flotante"] = False
            st.rerun()
    else:
        if st.button("👁️ Hacer Visible Padrón de Datos", use_container_width=True, type="secondary"):
            st.session_state["ver_padron_flotante"] = True
            st.session_state["ver_visor_legal"] = False
            st.session_state["ver_formulario_registro"] = False
            st.rerun()
# ==============================================================================
# PARTE 17 DE 17: COLUMNA DERECHA - UPLOADING DE ARCHIVOS Y PIE DE MATRIZ A COLOR
# ==============================================================================
    st.markdown("---")
    st.markdown("#### 📤 Uploading de Nuevas Actas")
    archivo_cargado = st.file_uploader("Sube un acta complementaria (.txt):", type=["txt"])
    if archivo_cargado is not None:
        nombre_archivo_crudo = archivo_cargado.name.replace(".txt", "")
        if nombre_archivo_crudo not in st.session_state["repositorio_institucional"]:
            try:
                contenido_texto = archivo_cargado.read().decode("utf-8", errors="ignore")
                st.session_state["repositorio_institucional"][nombre_archivo_crudo] = {
                    "Marco conceptual y descriptivo": contenido_texto,
                    "Marco legal": f"Borrador de marco legal en espera de adición fiscal para JACOB ZUMAYA PRIANTI, A.C.",
                    "Manual de procedimientos": "Borrador de manual de procedimientos en espera de adición operativa.",
                    "Manual administrativo": "Borrador de manual administrativo.",
                    "Manual de Tendencias criticas": "Borrador de tendencias críticas.",
                    "Manual de Variables latentes con items observables": "Borrador de variables latentes.",
                    "Contrato de Incorporación y Adhesión Individual": "Borrador de contrato de incorporación individual.",
                    "Acta Constitutiva Notarial Oficial": "Borrador de acta notarial oficial."
                }
                st.success(f"✓ '{archivo_cargado.name}' guardado.")
                st.button("🔄 Actualizar", key="refresh_uploader_nested")
            except Exception as e:
                st.error("Error al indexar.")

# INFOGRAFÍA CORPORATIVA DE TRANSPARENCIA CONTABLE
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0; font-size:14px;'>🟢 Nodo Central: JACOB ZUMAYA PRIANTI, A.C.</h4><p style='color: #1c7430; font-size: 12px;'><b>Estatus:</b> 0% IVA / Escudo 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 12px; border-radius: 6px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0; font-size:14px;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 12px;'><b>Impacto:</b> Capitaliza excedentes netos de fletes e intermediación libre de ISR.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0; font-size:14px;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 12px;'><b>Impacto:</b> Transforma primas comerciales de la S.A. en fondos de fomento.</p></div>", unsafe_allow_html=True)
