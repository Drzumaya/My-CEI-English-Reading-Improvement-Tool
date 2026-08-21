import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado estable de PDFs en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# PARTE 1 DE 14: CONFIGURACIÓN INICIAL DEL LIENZO WEB CORPORATIVO JZPAC
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - JACOB ZUMAYA PRIANTI, A.C.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ==============================================================================
# PARTE 2 DE 14: INICIALIZACIÓN DE CONTEXTOS Y BANDERAS DE CONTROL REGISTRAL
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
# PARTE 3 DE 14: MEMORIA TRANSACCIONAL - PADRÓN HISTÓRICO DE DIRECTORES ASOCIADOS
# ==============================================================================
if "directores_registrados" not in st.session_state:
    st.session_state["directores_registrados"] = [
        {
            "Id": 1,
            "Fecha Registro": "2026-08-19 14:22:10",
            "Nombre": "Ing. Carlos Mendoza", 
            "Entidad": "4. Equipo de Investigación Científica APSON", 
            "Puesto": "Director de Transferencia Tecnológica", 
            "RFC": "MEC840512XX1", 
            "Estatus": "Activo"
        },
        {
            "Id": 2,
            "Fecha Registro": "2026-08-20 09:15:43",
            "Nombre": "Sra. María Elena Ortiz", 
            "Entidad": "2. Cooperativa de Logística (S.C.)", 
            "Puesto": "Directora de Operaciones de Flete", 
            "RFC": "OIME761102XX3", 
            "Estatus": "Activo"
        }
    ]

# ==============================================================================
# PARTE 4 DE 14: ALMACÉN DOCUMENTAL INTEGRAL - JACOB ZUMAYA PRIANTI, A.C.
# ==============================================================================
if "repositorio_institucional" not in st.session_state:
    st.session_state["repositorio_institucional"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL\n\nFunciona como la sociedad controladora social (Holding) que coordina los subsistemas autónomos en Agua Prieta. Diseña los planes de capacitación para el trabajo de la periferia urbana.",
            "Marco legal": "FUNDAMENTACIÓN FISCAL TÍTULO II LISR\n\nTributa en Régimen General corporativo (30% ISR). Blinda sus egresos comunitarios al 100% como deducciones mediante Nómina Asimilada (Art. 94 LISR). Exenta de trasladar el 16% de IVA en capacitación según el Art. 15 de la LIVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS DE GOBERNANZA CENTRAL (MAP-01)\n\n1. Recepción de comisiones de la S.A. y aportaciones cooperativas.\n2. Validación de listas de asistencia de talleres.\n3. Dispersión mensual y timbrado de CFDI de asimilados a salarios.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RECURSOS HUMANOS Y CONTROL (MAC-01)\n\nRegula las políticas de contratación de promotores barriales, el control de activos en comodato y los lineamientos de transparencia para auditorías externas del SAT.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS Y RIESGO SOCIOECONÓMICO (MTC-01)\n\nMonitorea la inflación en la franja fronteriza, los cambios en las reglas misceláneas del SAT y el impacto del tipo de cambio peso-dólar en Agua Prieta.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EVALUACIÓN DE ADOPCIÓN DE PROGRAMAS SOCIALES\n\nVARIABLE LATENTE CENTRAL: 'Aceptación Institucional del Modelo de Economía Popular'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Frecuencia con la que el asociado acude voluntariamente a las mesas de gobernanza.\n2. [X2] Nivel de confianza percibido en la transparencia del manejo de fondos del Título II.\n3. [X3] Disposición declarada para transitar de contratos informales a Nómina de Asimilados.\n4. [X4] Grado de recomendación del programa de capacitación de la A.C. a otros microemprendedores del barrio.\n5. [X5] Percepción de mejora en la estabilidad de su negocio tras el cobro vía recibo estatutario.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ADHESIÓN Y ASIMILACIÓN A SALARIOS (A.C. MATRIZ)\n\nCONTRATO que celebran la Asociación Civil Matriz, y el Usuario Inscrito por propio derecho en su carácter de Director Asociado:\n\nPRIMERA: OBJETO. El Usuario acepta la designación técnica para coordinar los talleres de capacitación para el trabajo en Agua Prieta.\n\nSEGUNDA: RÉGIMEN FISCAL. El Usuario manifiesta su consentimiento expreso para someter sus honorarios al régimen de Asimilados a Salarios (Art. 94 Fracc. V de la LISR).\n\nTERCERA: EXENCIÓN DE IVA. Las cuotas extraordinarias que recaude el Usuario de los talleres se consideran cuotas de miembros exentas de IVA (Art. 15-XII LIVA) y se integrarán de inmediato a la cuenta de orden de la Caja de Ahorro.",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [XXXX] | VOLUMEN: [XX]\nCONSTITUCIÓN DE ASOCIACIÓN CIVIL BAJO EL RÉGIMEN GENERAL (TÍTULO II LISR)\n\nEn Agua Prieta, Estado de Sonora, ante la fe notarial se formaliza la constitución de la persona moral que se regirá bajo las siguientes cláusulas formales:\n\nCLÁUSULA PRIMERA: DENOMINACIÓN, DOMICILIO Y DURACIÓN.\nLa organización se denominará 'JACOB ZUMAYA PRIANTI, A.C.'. Su domicilio legal definitivo se fija en Agua Prieta, Sonora, y su duración será por tiempo indefinido.\n\nCLÁUSULA SEGUNDA: OBJETO SOCIAL Y REMANENTES DISPONIBLES.\nEl objeto primordial consiste en impartir de forma gratuita y exenta de IVA (Art. 15 LIVA) capacitación para el trabajo. Al operar bajo el Título II LISR, los excedentes se capitalizarán en cuentas de orden para subsidiar activos del barrio o se dispersarán al 100% como erogaciones salariales asimiladas (Art. 94 LISR).\n\nCLÁUSULA TERCERA: PATRIMONIO SOCIAL.\nEl patrimonio de la A.C. se integrará por las cuotas de sus miembros. El órgano supremo es la Asamblea General de Asociados.",
            
            # NUEVO EXPEDIENTE ASOCIADO OBLIGATORIO
            "Directores Asociados Registrados (Padrón Oficial)": "PADRÓN OFICIAL DE DIRECTORES ASOCIADOS Y LÍDERES DE CÉLULA - JACOB ZUMAYA PRIANTI, A.C.\n\nDe conformidad con los estatutos vigentes y las disposiciones del Artículo 94 de la LISR bajo el Régimen General Título II, se certifica que las siguientes personas físicas ejercen facultades de dirección comunitaria autónoma en la demarcación de Agua Prieta, Sonora:\n\n1. [VIGENTE] Lic. Alejandro Anaya - RFC: ANAA850423XX9. Cargo: Director de Logística y Abasto Fronterizo.\n2. [VIGENTE] Ing. Carlos Mendoza - RFC: MEC840512XX1. Cargo: Director de Transferencia Tecnológica I+D.\n3. [VIGENTE] Sra. María Elena Ortiz - RFC: OIME761102XX3. Cargo: Directora de Operaciones de Flete de Célula Cooperativa."
        },

# ==============================================================================
# PARTE 5 DE 14: ALMACÉN DOCUMENTAL - COOPERATIVA DE LOGÍSTICA (S.C.)
# ==============================================================================
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA OPERATIVO DE TRANSPORTE BARRIAL\n\nAsOCIACIÓN de choferes de base popular organizados para competir en el mercado de fletes industriales B2B y última milla, absorbiendo la demanda del nearshoring maquilador.",
            "Marco legal": "LEY GENERAL DE SOCIEDADES COOPERATIVAS (LGSC)\n\nSociedad Cooperativa de Producción de Servicios de Responsabilidad Limitada (S.C. de R.L. de C.V.). Las plantas maquiladoras contratantes efectúan la retención del 4% de ISR sobre fletes terrestres.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS OPERATIVOS LOGÍSTICOS (MOP-02)\n\n1. Asignación de rutas comerciales en Agua Prieta.\n2. Auditoría física del Factor de Retorno Vacío (Deadhead).\n3. Retención automática del 6% para el fondo de amortiguación de diésel.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE FLOTILLA Y MANTENIMIENTO (MAF-02)\n\nEstablece los roles de los Asociados Directores en la administración de talleres mecánicos asignados, control de bitácoras de viaje y asignación de viáticos logísticos fronterizos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS DE TRANSPORTE TRANSFRONTERIZO (MTC-02)\n\nAnaliza los tiempos de espera en las aduanas, la fluctuación estacional de la producción automotriz de las maquiladoras y el impacto de aranceles comerciales en el flujo de fletes.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA OPERATIVA DE LA LOGÍSTICA DE BARRIO\n\nVARIABLE LATENTE CENTRAL: 'Cultura de Optimización de Ruta en Choferes Cooperativistas'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Índice de cumplimiento exacto de los horarios de recolección aduanal.\n2. [X2] Nivel de reducción voluntaria reportada en el Factor de Retorno Vacío.\n3. [X3] Frecuencia de registro y uso correcto de la aplicación Streamlit para el reporte del COK.\n4. [X4] Grado de apego a los lineamientos de mantenimiento preventivo y revisión de presión de neumáticos.\n5. [X5] Proporción de fletes ejecutados sin registrar incidencias o penalizaciones por retraso.\n6. [X6] Disposición del chofer para cooperar en cargas consolidadas compartidas con otros talleres.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO DE ADHESIÓN INDIVIDUAL DE SOCIO TRABAJADOR COOPERATIVISTA (S.C. LOGÍSTICA)\n\nCONTRATO que celebran la Sociedad Cooperativa de Logística y Transporte de los Barrios, y el Socio Conductor:\n\nPRIMERA: ASOCIACIÓN COMUNITARIA. El Usuario aporta su trabajo personal y se adhiere formalmente bajo el régimen de Responsabilidad Limitada amparado por la Ley General de Sociedades Cooperativas (LGSC).\n\nSEGUNDA: RETENCIONES Y COK. El Socio acepta registrar cada viaje en la aplicación, deduciendo el Costo de Operación por Kilómetro (COK), el Factor de Retorno Vacío, el 4% de retención de ISR y aportando el 6% para el fondo de amortiguación de diésel fronterizo.\n\nTERCERA: EXCEDENTES. El Socio Conductor reconoce que los excedentes netos de fletes se inyectarán de forma legal a la Caja de Ahorro común, teniendo derecho a retiros de rendimientos sociales.",
            "Acta Constitutiva Notarial Oficial": "INSCRIPCIÓN REGISTRAL MERCANTIL | FOJA: [XXX]\nBASES CONSTITUTIVAS DE SOCIEDAD COOPERATIVA DE RESPONSABILIDAD LIMITADA (S.C. DE R.L.)\n\nEn Agua Prieta, Sonora, se formaliza el Acta de Asamblea Constitutiva organizada de conformidad con la Ley General de Sociedades Cooperativas (LGSC):\n\nCLÁUSULA PRIMERA: RÉGIMEN Y DENOMINACIÓN.\nLa sociedad se denominará 'COOPERATIVA DE LOGÍSTICA Y TRANSPORTE TRANSFRONTERIZO DE AGUA PRIETA, S.C. DE R.L. DE C.V.'. Su responsabilidad queda limitada al monto de los certificados de aportación.\n\nCLÁUSULA SEGUNDA: OBJETO COMERCIAL Y CADENA DE VALOR B2B.\nEl objeto exclusivo consiste en prestar servicios de transporte terrestre fletes B2B para las maquiladoras. La sociedad se obliga a facturar conforme a las leyes fiscales, aceptando la retención del 4% de ISR.\n\nCLÁUSULA TERCERA: EXCEDENTES COOPERATIVOS.\nAl término de cada ejercicio contable mensual se deducirá un 6% bruto para el fondo de reserva de diésel y un 5% neto de excedentes que se inyectará a la cuenta de orden de JACOB ZUMAYA PRIANTI, A.C.",
            
            # NUEVO EXPEDIENTE ASOCIADO OBLIGATORIO
            "Directores Asociados Registrados (Padrón Oficial)": "REGISTRO DE SOCIOS DIRECTORES CON FACULTADES DE DELEGACIÓN - SUBSISTEMA LOGÍSTICO\n\nEn cumplimiento con las Bases Constitutivas de la Cooperativa y la Ley General de Sociedades Cooperativas, se hace constar el padrón oficial de Directores de Ruta autorizados ante el SAT de Agua Prieta, Sonora:\n\n1. [ACTIVO] Sra. María Elena Ortiz - RFC: OIME761102XX3. Puesto: Directora de Operaciones de Flete Terrestre.\n2. [ACTIVO] Don Ramón Valdez Lugo - RFC: VALR630814XX2. Puesto: Supervisor de Mantenimiento de Flotillas B2B.\n3. [ACTIVO] C. Transportista Privado Adherente - Monitoreado vía Token analítico Streamlit de JZPAC."
        },

# ==============================================================================
# PARTE 6 DE 14: ALMACÉN DOCUMENTAL - AGENCIA DE MICROSEGUROS (S.A.)
# ==============================================================================
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE CONTROL DE RIESGOS COMERCIAL\n\nEntidad financiera diseñada para proteger los activos mecánicos de los talleres populares y mitigar vulnerabilidades por accidentes de trabajo o fallecimiento de líderes comunitarios.",
            "Marco legal": "LEY DE INSTITUCIONES DE SEGUROS Y DE FIANZAS (LISF)\n\nSociedad Anónima regulada por la CNSF. Transfiere legalmente el 20% de las primas a la A.C. mediante contratos de Corretaje Social y capacitación en prevención de accidentes.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS Y ATENCIÓN DE SINIESTROS (MAP-03)\n\n1. Reporte técnico de avería mecánica o accidente en las colonias.\n2. Evaluación social del riesgo y dictamen del Asociado Director.\n3. Liquidación de la reparación con cargo al fondo de reserva.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RESERVAS TÉCNICAS Y RECAUDACIÓN (MAR-03)\n\nRegula el proceso de cobranza mensual de las primas a través de plataformas digitales y el resguardo seguro del capital de reserva en instrumentos de renta fija de bajo riesgo.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS ACTUARIALES EN MICROSEGUROS (MTC-03)\n\nMide la tasa de siniestralidad de los talleres de barrio, la tasa de renovación de pólizas y proyecta modelos de vulnerabilidad ante fallas mecánicas en maquinaria pesada depreciada.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - PERCEPCIÓN DE SEGURIDAD PATRIMONIAL\n\nVARIABLE LATENTE CENTRAL: 'Aversión al Riesgo y Confianza en la Póliza Solidaria'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Puntualidad exacta en el pago de la prima mensual simulada en la plataforma.\n2. [X2] Grado de conocimiento de los talleres sobre el alcance real de las coberturas de siniestralidad.\n3. [X3] Nivel de tranquilidad manifestada por el micro-empresario respecto a la continuidad de su negocio.\n4. [X4] Frecuencia con la que el micro-taller reporta de forma preventiva riesgos de infraestructura.\n5. [X5] Confianza declarada en la velocidad de respuesta del fondo de reserva del ramo de riesgos.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO COLECTIVO DE ADHESIÓN A LA PÓLIZA DE MICROSEGUROS FRONTERIZOS (S.A.)\n\nCONTRATO que celebran la Agencia de Protección Solidaria Fronteriza, S.A. de C.V., y el Titular de Unidad Asegurada:\n\nPRIMERA: COBERTURA INTEGRAL. El Usuario se adhiere a la póliza para proteger sus activos mecánicos y herramientas contra averías técnicas graves, incendios o accidentes de operación en Agua Prieta.\n\nSEGUNDA: PRIMA SOCIAL Y RETORNO. El Asegurado cubre la prima mensual calculada. El 20% es transferido a la A.C. matriz por concepto de Honorarios de Capacitación en Prevención de Siniestros, libre de IVA.\n\nTERCERA: RECLAMACIÓN JUSTA. En caso de siniestro, el Usuario se compromete a someterse al Manual de Procedimientos interno, el cual dictaminará la liquidación de daños con cargo al fondo de reserva técnico.",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [YYYY] | VOLUMEN: [XXX]\nCONSTITUCIÓN DE SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE (RAMO RIESGOS CNSF)\n\nEn Agua Prieta, Estado de Sonora, ante la fe notarial se formaliza la constitución que se regirá bajo la Ley de Sociedades Mercantiles (LGSM) y la Ley de Instituciones de Seguros y de Fianzas (LISF):\n\nCLÁUSULA PRIMERA: DENOMINACIÓN Y OBJETO REGULADO.\nLa denominación corporativa oficial será 'AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA, S.A. DE C.V.'. Su objeto consiste en actuar como Agente de Seguros intermediando pólizas colectivas.\n\nCLÁUSULA SEGUNDA: DOMINIO DE LA ASOCIACIÓN CIVIL MATRIZ.\nEl capital social es variable. Para blindar el patrimonio, la institución central JACOB ZUMAYA PRIANTI, A.C. retiene la titularidad del 99% de las acciones Clase 'A', teniendo el voto mayoritario absoluto.\n\nCLÁUSULA TERCERA: CONTRATO DE RETORNO CORRETAJE.\nLa sociedad se obliga por estipulación estatutaria invulnerable a transferir el 20% de las primas brutas capturadas mensuales a la A.C. matriz bajo la figura de Honorarios de Corretaje Social.",
            
            # NUEVO EXPEDIENTE ASOCIADO OBLIGATORIO
            "Directores Asociados Registrados (Padrón Oficial)": "NOMBRAMIENTOS DE DIRECTORES EJECUTIVOS CON REGISTRO CNSF - SUBSISTEMA DE RIESGOS\n\nSe certifica el padrón consolidado de apoderados y comisionados autorizados para operar fondos de reserva técnica y corretaje social vinculados a la cuenta matriz JZPAC en Agua Prieta, Sonora:\n\n1. [VIGENTE] Lic. Alejandro Anaya - RFC: ANAA850423XX9. Puesto: Administrador Único de Riesgos Corporativos.\n2. [VIGENTE] Act. Ernesto Villarreal - Cédula Actuarial CNSF. Puesto: Comisionado de Análisis de Siniestralidad.\n3. [VIGENTE] Representante Comunitario de Taller Asegurado - Avalado por la Junta General de la S.A."
        },

# ==============================================================================
# PARTE 7 DE 14: ALMACÉN DOCUMENTAL - EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON
# ==============================================================================
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE INVESTIGACIÓN, DESARROLLO E INNOVACIÓN (I+D)\n\nCélula científica encargada de realizar estudios de densidad económica, análisis metalúrgicos para el reciclaje (Upcycling) de las mermas de las maquiladoras y optimización de modelos predictivos de crédito social.",
            "Marco legal": "LEY GENERAL DE HUMANIDADES, CIENCIAS, TECNOLOGÍAS E INNOVACIÓN\n\nOpera bajo el amparo de la Cláusula Estatutaria de Autonomía de los Asociados Directores. Los fondos de investigación científica se consideran aportaciones de fomento exentas de IVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS EN RECOLECCIÓN Y PROCESAMIENTO (MAP-04)\n\n1. Recolección de muestras de mermas industriales (cueros, maderas, polímeros) en las maquiladoras.\n2. Pruebas de resistencia en laboratorios comunitarios.\n3. Transferencia de patentes sociales a los talleres.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE PROYECTOS Y FIDEICOMISOS CIENTÍFICOS (MAP-04)\n\nCoordina la gobernanza presupuestal de los laboratorios, la asignación de becas de investigación a estudiantes de Agua Prieta y el inventario de reactivos técnicos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS EN INNOVACIÓN INDUSTRIAL (MTC-04)\n\nMapea las tecnologías emergentes de manufactura esbelta automatizada, el volumen de desperdicios utilizables por tipo de maquila y las proyecciones de crecimiento del nearshoring real.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA DE LA TRANSFERENCIA TECNOLÓGICA I+D\n\nVARIABLE LATENTE CENTRAL: 'Capacidad de Absorción del Saber Científico en Talleres de Barrio'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Tasa de adopción de manuales Lean-Barrio y diagramas de flujo técnicos dentro de los procesos diarios.\n2. [X2] Cantidad de mermas industriales recolectadas (cuero, madera) efectivamente transformadas.\n3. [X3] Frecuencia de asistencia de los artesanos a las células de co-diseño del Equipo Científico.\n4. [X4] Reducción porcentual de costos de materia prima lograda por el taller al sustituir insumos.\n5. [X5] Nivel de comprensión técnica manifestada por el micro-productor sobre el uso y cuidado de maquinaria.\n6. [X6] Cantidad de nuevos prototipos funcionales o innovaciones locales de producto generadas de forma autónoma.\n7. [X7] Incremento reportado en la calidad final de la proveeduría indirecta entregada a las plantas.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ASIGNACIÓN CIENTÍFICA Y PROPIEDAD INTELECTUAL SOCIAL (ID-APSON)\n\nCONTRATO que celebran la Asociación Civil e Investigación Científica APSON, y el Investigador o Técnico de Laboratorio:\n\nPRIMERA: OBJETO DE TRANSFERENCIA. El Investigador se compromete a ejecutar análisis de densidad económica y modelado estadístico psicométrico de variables latentes en Agua Prieta.\n\nSEGUNDA: PATENTES SOCIALES Y CONFIDENCIALIDAD. El Usuario acepta que toda propiedad intelectual desarrollada en las células de I+D pertenece al patrimonio común de la A.C. Queda prohibida la comercialización mercantil privada.\n\nTERCERA: CONDICIÓN DE REMUNERACIÓN. Las retribuciones se canalizarán a través del fondo de fideicomisos científicos autónomos administrado por la Caja de Ahorro, justificando la materialidad docente libre de IVA.",
            "Acta Constitutiva Notarial Oficial": "PROTOCOLO NOTARIAL DE NOMBRAMIENTO Y APERTURA DE CONSEJO DE INVESTIGACIÓN CIENTÍFICA\n\nEn Agua Prieta, Sonora, ante la fe del Notario Público se formaliza el Gobierno de la célula científica con base en la Ley General de Ciencias:\n\nCLÁUSULA PRIMERA: AUTONOMÍA OPERATIVA Y DENOMINACIÓN.\nEl subsistema científico operará bajo el nombre de 'EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON'. Goza de una Cláusula de Autonomía de Gestión delegada por la matriz JACOB ZUMAYA PRIANTI, A.C.\n\nCLÁUSULA SEGUNDA: FINES CIENTÍFICOS Y MODELADO PATRIMONIAL.\nEl objeto consiste en ejecutar investigación de mermas y modelado de variables latentes. Toda patente resultante se registrará ante el IMPI a nombre de la Asociación Civil matriz, quedando etiquetada bajo un fideicomiso de 'Uso Social Común' perpetuo.\n\nCLÁUSULA TERCERA: GOBERNANZA PRESUPUESTAL.\nLa dirección científica recaerá en el Asociado Director. Los fondos captados se depositarán en la cuenta de orden de la Caja de Ahorro, amparando la completa materialidad de las investigaciones exentas de IVA.",
            
            # NUEVO EXPEDIENTE ASOCIADO OBLIGATORIO
            "Directores Asociados Registrados (Padrón Oficial)": "PADRÓN OFICIAL DE INVESTIGADORES COOPERANTES Y DIRECTORES TÉCNICOS - I+D APSON\n\nSe expide el listado definitivo de cientificos sociales y peritos adscritos al Consejo Autónomo de Investigación Científica JZPAC en Agua Prieta, Sonora:\n\n1. [VIGENTE] Ing. Carlos Mendoza - RFC: MEC840512XX1. Puesto: Director de Transferencia Tecnológica I+D.\n2. [VIGENTE] Dr. Hugo Aranda Fuentes - Cédula Investigador Nacional. Puesto: Consultor de Psicometría y Variables Latentes.\n3. [VIGENTE] Técnico de Campo Comunitario - Registrado para el levantamiento Likert de ítems observables en barrios."
        }
    }

# ==============================================================================
# PARTE 8 DE 14: SUBRUTINAS DE AUDITORÍA REGISTRAL Y VALIDADOR MATEMÁTICO DE RFC
# ==============================================================================
import re

def calcular_digito_verificador_sat(rfc_corto):
    """Aplica el algoritmo oficial de ponderación Módulo 11 para verificar el RFC."""
    # Mapeo oficial de caracteres del SAT a valores numéricos
    tabla_sat = "0123456789ABCDEFGHIJKLMN&OPQRSTUVWXYZ Ñ"
    valores = {char: idx for idx, char in enumerate(tabla_sat)}
    
    # Si es Persona Moral (11 chars antes del dígito), añadimos un espacio virtual al inicio
    if len(rfc_corto) == 11:
        rfc_corto = " " + rfc_corto
        
    suma = 0
    # Factores de ponderación posicional inversos (de 13 a 2)
    for i in range(12):
        char = rfc_corto[i]
        val = valores.get(char, 0)
        peso = 13 - i
        suma += val * peso
        
    residuo = suma % 11
    if residuo == 0:
        return "0"
    elif residuo == 1:
        return "A"
    else:
        digito = 11 - residuo
        return str(digito)

def validar_estructura_rfc(rfc):
    """Valida la sintaxis regex y el dígito verificador del RFC según el estándar del SAT."""
    rfc = rfc.upper().strip()
    # Expresión regular oficial del SAT para Personas Físicas y Morales
    regex_sat = r"^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$"
    
    if not re.match(regex_sat, rfc):
        return False, "Estructura o fecha inválida en el RFC."
        
    # Extraer el dígito verificador real (último carácter) y el cuerpo corto
    digito_real = rfc[-1]
    rfc_corto = rfc[:-1]
    
    # Calcular el dígito teórico mediante Módulo 11
    digito_calculado = calcular_digito_verificador_sat(rfc_corto)
    
    if digito_real != digito_calculado:
        return False, f"Dígito verificador inválido (Esperado: {digito_calculado}, Capturado: {digito_real})."
        
    return True, "RFC Válido conforme al estándar oficial del SAT."

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
    return False

if not check_password():
    st.stop()

def logout():
    st.session_state["password_correct"] = False
    st.session_state["show_login_error"] = False
    st.rerun()
# ==============================================================================
# PARTE 9 DE 14: MOTOR DE COMPILACIÓN VANGUARDISTA CON NÚMERO DE PÁGINA COMÚN
# ==============================================================================
from reportlab.pdfgen import canvas

class CanvasPaginadoIndividual(canvas.Canvas):
    """Lienzo de doble pasada para calcular y estampar el número de página exacto."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_footer(page_count)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#495057"))
        # Estampar número de página centrado al calce (puntos de imprenta)
        texto_pagina = f"Página {self._pageNumber} de {page_count}"
        self.drawCentredString(306, 25, texto_pagina)
        self.restoreState()

def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto, lang_en=False):
    """Compila estados contables en un formato PDF de vanguardia con foliación de páginas."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=50)
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

    label_sub = "<b>JACOB ZUMAYA PRIANTI, A.C.</b> • Popular Economics Ecosystem" if lang_en else "<b>JACOB ZUMAYA PRIANTI, A.C.</b> • Ecosistema de Economía Popular AP-AC"
    header_text = [
        [Paragraph(f"<b>{titulo_modulo.upper()}</b>", estilo_titulo), logo_flowable],
        [Paragraph(label_sub, estilo_sub), ""]
    ]
    
    header_table = Table(header_text, colWidths=[380.0, 100.0])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('SPAN', (1,0), (1,1)), ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    
    divider_line = Table([[""]], colWidths=[480.0])
    divider_line.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, color_primario), ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(divider_line)
    story.append(Spacer(1, 10))
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    
    tabla_pdf = Table(datos_tabla, colWidths=[240.0, 240.0])
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), color_primario), ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(tabla_pdf)
    story.append(Spacer(1, 30))
    
    lbl_f1 = "<b>Central Capacitator Agent</b>" if lang_en else "<b>Agente Capacitador Central</b>"
    lbl_f2 = "<b>Subsystem Director</b>" if lang_en else "<b>Director de Subsistema</b>"
    lbl_f3 = "<b>Tax Materiality Control</b>" if lang_en else "<b>Delegación de Control SAT</b>"

    datos_firmas = [
        ["____________________________", "____________________________", "____________________________"],
        [Paragraph(lbl_f1, estilo_firmas), Paragraph(lbl_f2, estilo_firmas), Paragraph(lbl_f3, estilo_firmas)],
        [Paragraph("Jacob Zumaya Prianti, A.C.", estilo_firmas), Paragraph("Gobernanza de Célula de Barrio", estilo_firmas), Paragraph("Materialidad e Inclusión Fiscal", estilo_firmas)]
    ]
    
    tabla_firmas = Table(datos_firmas, colWidths=[155.0, 170.0, 155.0])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(tabla_firmas)
    
    # Inyectar el lienzo paginado personalizado al momento de construir el PDF
    doc.build(story, canvasmaker=CanvasPaginadoIndividual)
    buffer.seek(0)
    return buffer
# ==============================================================================
# PARTE 10 DE 14: MOTOR DE ENCUADERNACIÓN DE MONOGRAFÍAS CON ÍNDICE DINÁMICO CORREGIDO
# ==============================================================================
class CanvasPaginadoLibro(canvas.Canvas):
    """Lienzo avanzado de doble pasada que registra marcadores y añade paginación APA 7."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            # Omitir foliación superior en la portada de color (Página 1)
            if self._pageNumber > 1:
                self.draw_header()
            super().showPage()
        super().save()

    def draw_header(self):
        self.saveState()
        self.setFont("Helvetica", 10)
        self.setFillColor(colors.HexColor("#495057"))
        # Numeración en la esquina superior derecha (Normativa oficial APA 7)
        self.drawRightString(540, 750, str(self._pageNumber))
        self.restoreState()

def generar_libro_apa7(nombre_entidad, diccionario_marcos, lang_en=False):
    """Compila toda la documentación en una monografía bilingüe estilo APA 7 con índice dinámico exacto."""
    buffer_libro = io.BytesIO()
    doc = SimpleDocTemplate(buffer_libro, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    color_corporativo = colors.HexColor("#1e4620")
    
    estilo_portada_titulo = ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.white, alignment=1, spaceAfter=15)
    estilo_portada_meta = ParagraphStyle('CoverMeta', fontName='Helvetica', fontSize=10, leading=15, textColor=colors.HexColor("#e9ecef"), alignment=1, spaceAfter=10)
    estilo_apa_h1 = ParagraphStyle('APAH1', fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.black, alignment=1, spaceBefore=24, spaceAfter=12)
    estilo_apa_h2 = ParagraphStyle('APAH2', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.black, alignment=0, spaceBefore=16, spaceAfter=6)
    estilo_apa_parrafo = ParagraphStyle('APABody', fontName='Helvetica', fontSize=11, leading=22, textColor=colors.HexColor("#212529"), spaceAfter=14, firstLineIndent=36)
    estilo_indice = ParagraphStyle('DocIndex', fontName='Helvetica', fontSize=10, textColor=colors.black, spaceAfter=8)
    
    story = []
    story.append(Spacer(1, 20))
    
    from reportlab.platypus import Image as RLImage
    logo_portada = ""
    try:
        logo_portada = RLImage("JZPACLOGOREDONDO.png", width=60, height=65)
    except Exception:
        logo_portada = Paragraph("<b>🦅 JZPAC</b>", ParagraphStyle('Pld', fontSize=16, textColor=colors.white, alignment=1))
        
    p_t1 = "<b>INTEGRATED COMPENDIO INSTITUTIONAL MANUAL</b>" if lang_en else "<b>COMPENDIO INSTITUCIONAL INTEGRAL DE CONTROL VINCULADO</b>"
    p_t2 = f"<b>Technical-Legal Subsystem: {nombre_entidad.upper()}</b>" if lang_en else f"<b>Subsistema Técnico-Legal: {nombre_entidad.upper()}</b>"
    p_m1 = "<b>Research Line:</b> Endogenous Growth" if lang_en else "<b>Línea de Investigación:</b> Crecimiento Endógeno y Retención de Valor Fronterizo"
    p_m2 = "<b>Corporate Author:</b> Central Board JZPAC" if lang_en else "<b>Autor Corporativo:</b> Consejo Directivo Central JZPAC - Agente Capacitador"
    p_m4 = f"<b>Certification Date:</b> {datetime.now().strftime('%d de %B de %Y')}" if lang_en else f"<b>Fecha de Certificación:</b> {datetime.now().strftime('%d de %B de %Y')}"
    p_m5 = "<i>Internal Organization Executive Monograph for Tax Compliance Validation under Mexican Law (Title II LISR)</i>" if lang_en else "<i>Monografía Ejecutiva de Organización interna para Validación del Remanente Distribuible conforme al Título II de la LISR</i>"

    tabla_portada_datos = [
        [Paragraph("<b>JACOB ZUMAYA PRIANTI, A.C.</b>", ParagraphStyle('N1', fontName='Helvetica-Bold', fontSize=11, textColor=colors.white, alignment=1, spaceAfter=15))],
        [Paragraph(p_t1, estilo_portada_titulo)],
        [Paragraph(p_t2, ParagraphStyle('S2', parent=estilo_portada_titulo, fontSize=13, textColor=colors.white))],
        [Spacer(1, 20)],
        [Paragraph(p_m1, estilo_portada_meta)],
        [Paragraph(p_m2, estilo_portada_meta)],
        [Paragraph(p_m4, estilo_portada_meta)],
        [Spacer(1, 15)],
        [Paragraph(p_m5, estilo_portada_meta)]
    ]
    
    tabla_portada_color = Table(tabla_portada_datos, colWidths=[460.0])
    tabla_portada_color.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color_corporativo), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 25), ('BOTTOMPADDING', (0,0), (-1,-1), 25),
    ]))
    story.append(tabla_portada_color)
    story.append(PageBreak())
    
    # --- ÍNDICE GENERAL CON LLAMADOS DE REFERENCIA DINÁMICOS EXÁCTOS ---
    lbl_idx = "<b>GENERAL CHAPTER INDEX</b>" if lang_en else "<b>ÍNDICE GENERAL DE CAPÍTULOS</b>"
    story.append(Paragraph(lbl_idx, estilo_apa_h1))
    story.append(Spacer(1, 15))
    
    num_capitulo = 1
    for titulo_manual in diccionario_marcos.keys():
        linea_puntos = ". " * 26
        lbl_cap = f"<b>Chapter {num_capitulo}:</b>" if lang_en else f"<b>Capítulo {num_capitulo}:</b>"
        id_marcador = f"cap_{num_capitulo}"
        
        # El tag <pageNumber> de ReportLab calcula la página exacta al vuelo gracias al canvasmaker
        renglon_indice = f"{lbl_cap} {titulo_manual} {linea_puntos} [ pág. <pageNumber link={id_marcador}/> ]"
        story.append(Paragraph(renglon_indice, estilo_indice))
        num_capitulo += 1
        
    story.append(PageBreak())
    
    # --- ENCUADERNACIÓN DE CONTENIDOS CREANDO LOS PUNTOS DE REFERENCIA EN EL CANVAS ---
    num_capitulo = 1
    for titulo_manual, texto_contenido in diccionario_marcos.items():
        txt_traducido = texto_contenido
        if lang_en:
            txt_traducido = txt_traducido.replace("ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL", "CENTRAL HOLDING ORGANISATION")
            txt_traducido = txt_traducido.replace("FUNDAMENTACIÓN FISCAL TÍTULO II LISR", "TAX COMPLIANCE TITLE II LISR")
            txt_traducido = txt_traducido.replace("CLÁUSULA PRIMERA", "FIRST CLAUSE").replace("CLÁUSULA SEGUNDA", "SECOND CLAUSE").replace("CLÁUSULA TERCERA", "THIRD CLAUSE")
            txt_traducido = txt_traducido.replace("Directores Asociados Registrados (Padrón Oficial)", "Registered Associate Directors (Official Roster)")

        id_marcador = f"cap_{num_capitulo}"
        
        # SOLUCIÓN DE NÚMERO AUSENTE: El macro MacroPageBookmark inyecta el destino directo al lienzo
        from reportlab.platypus import Macro
        story.append(Macro(f"canvas.bookmarkPage('{id_marcador}')"))
        
        # Agregar el tag ancla embebido en el Flowable para retrocompatibilidad
        story.append(Paragraph(f"<a name='{id_marcador}'/><b>{titulo_manual}</b>", estilo_apa_h1))
        story.append(Spacer(1, 10))
        
        for fragmento in txt_traducido.split('\n\n'):
            if fragmento.strip():
                if fragmento.strip().startswith("ARTÍCULO") or fragmento.strip().startswith("MÓDULO") or ":" in fragmento.split('\n'):
                    story.append(Paragraph(f"<b>{fragmento.strip()}</b>", estilo_apa_h2))
                else:
                    story.append(Paragraph(fragmento.strip(), estilo_apa_parrafo))
        story.append(Spacer(1, 15))
        num_capitulo += 1
        
    doc.build(story, canvasmaker=CanvasPaginadoLibro)
    buffer_libro.seek(0)
    return buffer_libro
# ==============================================================================
# PARTE 11 DE 14: CONTROL PRESUPUESTAL SIDEBAR Y SELECTOR DE CONTEXTO DE CLASE MUNDIAL
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

# Partición del lienzo web de alta dirección
col_izquierda_matriz, col_derecha_documental = st.columns([0.70, 0.30])

# Inicializadores analíticos base
num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_calculado = 0.0

# ==============================================================================
# ==============================================================================
# PARTE 12a DE 14: COLUMNA IZQUIERDA - VISOR EDITABLE Y ALTAS DEL FORMULARIO
# ==============================================================================
with col_izquierda_matriz:
    # 1. ENTORNO FLOTANTE PARA EDITAR MANUALES INDIVIDUALES EN VIVO
    if (st.session_state["ver_visor_legal"] and 
        st.session_state["entidad_seleccionada"] in st.session_state["repositorio_institucional"] and 
        st.session_state["tipo_doc_seleccionado"] in st.session_state["repositorio_institucional"][st.session_state["entidad_seleccionada"]]):
        
        ent = st.session_state["entidad_seleccionada"]
        tdoc = st.session_state["tipo_doc_seleccionado"]
        
        st.info(f"📁 Ventana de Trabajo Activa: {ent} ➔ {tdoc}")
        st.markdown("---")
        
        texto_editable_actual = st.text_area(label="Editor Oficial de Cláusulas e Instructivos:", value=st.session_state["repositorio_institucional"][ent][tdoc], height=320)
        
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("💾 Guardar Ajustes", use_container_width=True):
                st.session_state["repositorio_institucional"][ent][tdoc] = texto_editable_actual
                st.success("✓ Cambios guardados.")
        with b2:
            is_eng_pdf = (st.session_state.get("selector_idioma_global", "Español (ES)") == "English (EN)")
            tabla_legal_dummy = [["Validación de Consistencia", "Aprobado por el Consejo"], ["Fecha de Auditoría", "2026-08-20"], ["Estatus Regulatorio", "Vigente Exento"]]
            pdf_legal = generar_informe_pdf(f"{ent} - {tdoc}", tabla_legal_dummy, texto_editable_actual, lang_en=is_eng_pdf)
            if st.download_button(label="📥 PDF", data=pdf_legal, file_name=f"{tdoc.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True):
                registrar_descarga(ent, f"{tdoc}.pdf")
        with b3:
            buffer_word = io.BytesIO(texto_editable_actual.encode('utf-8'))
            st.download_button(label="📝 Word / G-Docs", data=buffer_word, file_name=f"{tdoc.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with b4:
            if st.button("🛑 Cerrar Visor", use_container_width=True, type="primary"):
                st.session_state["ver_visor_legal"] = False
                st.rerun()

    # 2. INTERFAZ DEL FORMULARIO DE ALTA DE DIRECTORES CON VALIDACIÓN SAT
    elif st.session_state["ver_formulario_registro"]:
        st.success("📝 Formulario Flotante Activo: Alta y Nombramiento de Directores Asociados")
        st.markdown("---")
        f_nom = st.text_input("👤 Nombre Completo del Director a Registrar:", placeholder="Ej. Lic. Alejandro Anaya")
        f_rfc = st.text_input("🆔 Clave de Registro Federal de Contribuyentes (RFC):", max_chars=13, placeholder="Ej. ANAA850423XX9").upper().strip()
        
        rfc_valido = False
        if f_rfc:
            es_valido, mensaje_sat = validar_estructura_rfc(f_rfc)
            if es_valido:
                st.success(f"✓ {mensaje_sat}")
                rfc_valido = True
            else:
                st.error(f"❌ {mensaje_sat}")
        
        lista_adscripcion_activa = list(st.session_state["repositorio_institucional"].keys())
        f_entidad = st.selectbox("🏢 Selecciona la Entidad o Subsistema que pasará a dirigir:", lista_adscripcion_activa)
        f_puesto = st.text_input("💼 Cargo u Oficio Directivo Asignado:", placeholder="Ej. Director General de Operaciones")

        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("💾 Validar e Inscribir Director", use_container_width=True, type="secondary", disabled=not rfc_valido):
                if f_nom and f_rfc and f_puesto:
                    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    nuevo_id = max([d["Id"] for d in st.session_state["directores_registrados"]], default=0) + 1
                    
                    st.session_state["directores_registrados"].append({
                        "Id": nuevo_id, "Fecha Registro": marca_tiempo, "Nombre": f_nom, "Entidad": f_entidad, "Puesto": f_puesto, "RFC": f_rfc, "Estatus": "Activo"
                    })
                    st.success(f"✓ El {f_puesto} ha sido formalmente indexado en el padrón dinámico.")
                else:
                    st.error("Por favor, llena todos los campos obligatorios.")
        with rc2:
            if st.button("🛑 Cancelar y Cerrar Formulario", use_container_width=True, type="primary"):
                st.session_state["ver_formulario_registro"] = False
                st.rerun()
# ==============================================================================
# PARTE 12b DE 14: COLUMNA IZQUIERDA - DASHBOARD INTERACTIVO FRONT-END (CRUD)
# ==============================================================================
    # 3. INTERFAZ MAESTRA: DASHBOARD FRONT-END (CRUD + INDICADORES DE TIEMPO)
    elif st.session_state["ver_padron_flotante"]:
        st.subheader("📊 Dashboard Maestro de Estructura y Plantilla Directiva")
        st.caption("Panel Front-End Ejecutivo para el control de Materialidad y Estatus de Células en Agua Prieta, Sonora.")
        st.markdown("---")
        
        dash_tab1, dash_tab2 = st.tabs(["👥 Control de Directores Asociados", "🏢 Control de Entidades / Subsistemas"])
        
        # PESTAÑA A: OPERACIONES DE DIRECTORES (READ, UPDATE ESTATUS, DELETE)
        with dash_tab1:
            if not st.session_state["directores_registrados"]:
                st.info("No se registran directores activos en el padrón actual.")
            else:
                for idx, dir_asoc in enumerate(st.session_state["directores_registrados"]):
                    # BLINDAJE ANTI-KEYERROR: Si el registro no tiene ID por sesiones previas, se asigna dinámicamente
                    if "Id" not in dir_asoc:
                        dir_asoc["Id"] = idx + 1
                    
                    badge_color = "#d4edda" if dir_asoc["Estatus"] == "Activo" else "#f8d7da"
                    text_color = "#155724" if dir_asoc["Estatus"] == "Activo" else "#721c24"
                    status_emoji = "🟢 Activo" if dir_asoc["Estatus"] == "Activo" else "🔴 Inactivo"
                    
                    st.markdown(f"""
                    <div style='background-color: {badge_color}; padding: 12px; border-radius: 6px; border-left: 5px solid {text_color}; margin-bottom: 10px;'>
                        <span style='float: right; font-weight: bold; color: {text_color}; font-size: 13px;'>{status_emoji}</span>
                        <h4 style='margin: 0; color: #212529; font-size: 15px;'><b>{dir_asoc['Nombre']}</b></h4>
                        <p style='margin: 3px 0 0 0; color: #495057; font-size: 12px;'>
                            <b>Cargo:</b> {dir_asoc['Puesto']} | <b>RFC:</b> <code style='color:#b83a14;'>{dir_asoc['RFC']}</code><br>
                            <b>Adscripción:</b> {dir_asoc['Entidad']} | <span style='color:#6c757d;'>Inscrito: {dir_asoc['Fecha Registro']}</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_btn1, c_btn2, c_btn3 = st.columns([0.4, 0.4, 0.2])
                    with c_btn1:
                        lbl_toggle = "⏸️ Cambiar a Inactivo" if dir_asoc["Estatus"] == "Activo" else "▶️ Cambiar a Activo"
                        if st.button(lbl_toggle, key=f"tgl_dir_{dir_asoc['Id']}_{idx}", use_container_width=True):
                            dir_asoc["Estatus"] = "Inactivo" if dir_asoc["Estatus"] == "Activo" else "Activo"
                            st.rerun()
                    with c_btn2:
                        with st.expander("📝 Editar Datos"):
                            edit_nom = st.text_input("Nombre:", value=dir_asoc["Nombre"], key=f"ed_nom_{dir_asoc['Id']}")
                            edit_puesto = st.text_input("Puesto:", value=dir_asoc["Puesto"], key=f"ed_pst_{dir_asoc['Id']}")
                            if st.button("💾 Aplicar Cambios", key=f"save_ed_{dir_asoc['Id']}", type="secondary"):
                                dir_asoc["Nombre"] = edit_nom
                                dir_asoc["Puesto"] = edit_puesto
                                st.success("✓ Registro modificado en tiempo real.")
                                st.rerun()
                    with c_btn3:
                        if st.button("🗑️ Borrar", key=f"del_dir_{dir_asoc['Id']}_{idx}", use_container_width=True, type="primary"):
                            st.session_state["directores_registrados"].pop(idx)
                            st.warning("✓ Director eliminado de la base de datos.")
                            st.rerun()
                    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            
            import csv
            output_csv = io.StringIO()
            writer_csv = csv.writer(output_csv)
            writer_csv.writerow(["Fecha Registro", "Nombre", "Entidad", "Puesto", "RFC", "Estatus"])
            for row in st.session_state["directores_registrados"]:
                writer_csv.writerow([row["Fecha Registro"], row["Nombre"], row["Entidad"], row["Puesto"], row["RFC"], row["Estatus"]])
            data_csv_string = output_csv.getvalue()
            
            st.markdown("---")
            st.download_button(
                label="📥 Exportar Base de Datos de Directores para Google Sheets (.csv)",
                data=data_csv_string,
                file_name="Dashboard_Directores_JZPAC.csv",
                mime="text/csv",
                use_container_width=True
            )

        # PESTAÑA B: OPERACIONES DE ENTIDADES (UPDATE NOMBRE, DELETE SUBSISTEMA)
        with dash_tab2:
            st.markdown("##### 🏢 Catálogo de Subsistemas Autónomos Indexados")
            st.caption("Modifica o depura las sociedades que integran la matriz corporativa. Advertencia: Eliminar una entidad borrará sus manuales.")
            st.markdown("<br>", unsafe_allow_html=True)
            
            lista_ent_crud = list(st.session_state["repositorio_institucional"].keys())
            for idx_e, ent_name in enumerate(lista_ent_crud):
                col_e1, col_e2 = st.columns([0.7, 0.3])
                with col_e1:
                    nuevo_nombre_ent = st.text_input(f"Entidad #{idx_e+1}:", value=ent_name, key=f"input_ent_{idx_e}")
                    if nuevo_nombre_ent != ent_name and nuevo_nombre_ent.strip():
                        st.session_state["repositorio_institucional"][nuevo_nombre_ent.strip()] = st.session_state["repositorio_institucional"].pop(ent_name)
                        st.success("✓ Nombre de entidad actualizado en caliente.")
                        st.rerun()
                with col_e2:
                    st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Eliminar Célula", key=f"del_ent_{idx_e}", type="primary", use_container_width=True):
                        if len(st.session_state["repositorio_institucional"]) <= 1:
                            st.error("No se puede eliminar la última entidad del sistema; se requiere un nodo central.")
                        else:
                            st.session_state["repositorio_institucional"].pop(ent_name)
                            st.warning(f"✓ '{ent_name}' y sus manuales han sido borrados.")
                            st.rerun()
        
        st.markdown("---")
        if st.button("🛑 Cerrar Dashboard Maestro y Volver a Simuladores", use_container_width=True, type="primary"):
            st.session_state["ver_padron_flotante"] = False
            st.rerun()
# ==============================================================================
# PARTE 13a DE 14: COLUMNA IZQUIERDA (CENTRO) - ENTORNO ANALÍTICO CONMUTABLE (PARTE 1)
# ==============================================================================
    else:
        # --- INNOVACIÓN DE CLASE MUNDIAL: SELECTOR DE CONTEXTO OPERATIVO CENTRAL ---
        lista_conmutacion = list(st.session_state["repositorio_institucional"].keys())
        
        st.markdown("""
        <div style='background-color: #1e4620; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center;'>
            <h3 style='color: white; margin: 0; font-size: 14px; font-weight: bold; letter-spacing: 0.5px;'>
                🎛️ SELECTOR MAESTRO: CONTROL DE OPERACIONES EN TIEMPO REAL
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        entidad_activa_centro = st.selectbox(
            "Selecciona el Subsistema para sincronizar el Lienzo de Simulación:", 
            lista_conmutacion,
            key="selector_contexto_maestro_centro"
        )
        
        st.markdown(f"### ⚙️ Tablero de Simulación: <span style='color:#1e4620;'>{entidad_activa_centro}</span>", unsafe_allow_html=True)
        st.markdown("---")

        # RENDERIZADO DINÁMICO DE 5 PESTAÑAS AJUSTADAS AL CONTEXTO BILINGÜE
        tabs = st.tabs(["📊 Balance del Subsistema", "🛡️ Parámetros Fiscales", "📈 Modelado Actuarial", "🚀 Innovación y Competitividad", "📑 Historial de Descargas"])
        tab_balance, tab_fiscal, tab_actuarial, tab_innovacion, tab_log = tabs
        
        # 1. PESTAÑA DINÁMICA: BALANCE DE LA CÉLULA ACTIVA
        with tab_balance:
            st.subheader(f"💼 Inteligencia Financiera - {entidad_activa_centro}")
            
            if "Matriz" in entidad_activa_centro or "A.C." in entidad_activa_centro:
                st.markdown("##### 🟢 Análisis de Remanentes Distribuidos (Título II)")
                st.caption("Validación de erogaciones comunitarias para la retención del valor mediante Nómina Asimilada (Art. 94 LISR).")
                num_talleres = st.slider("Talleres de Capacitación Vinculados:", min_value=5, max_value=300, value=65, key="t_ac")
                cuota_recup = float(presupuesto_total / num_talleres)
                
                c_m1, c_m2 = st.columns(2)
                c_m1.metric("Fondo de Sostenimiento Docente", f"${presupuesto_total:,.2f} MXN")
                c_m2.metric("Subsidio Asimilado por Taller", f"${cuota_recup:,.2f} MXN", "0% IVA Exento (Art. 15 LIVA)")
                
            elif "Logística" in entidad_activa_centro or "S.C." in entidad_activa_centro:
                st.markdown("##### 🔮 Control Operativo de Fletes Industriales B2B")
                st.caption("Cálculo de eficiencia de ruta deduciendo Costo por Kilómetro (COK) y factores de retorno aduanales.")
                viajes_mensuales = st.number_input("Número de Fletes Ejecutados al Mes:", min_value=1, value=48, key="v_sc")
                distancia_viaje = st.slider("Distancia Promedio (Kilómetros Redondos):", min_value=10, max_value=150, value=45, key='d_sc')
                tarifa_por_km = st.number_input("Tarifa Base de Cobro por Kilómetro:", min_value=10.0, value=85.0, key='tr_sc')
                costo_op_km = st.number_input("Costo de Operación por Kilómetro (COK):", min_value=5.0, value=32.5, key='cok_sc')
                factor_vacio = st.slider("Factor de Retorno Vacío (%):", min_value=0, max_value=50, value=25, key='fv_sc')
                
                ingreso_bruto_fletes = viajes_mensuales * distancia_viaje * tarifa_por_km
                km_reales = (viajes_mensuales * distancia_viaje) * (1 + (factor_vacio / 100))
                costo_total = km_reales * costo_op_km
                retencion_isr = ingreso_bruto_fletes * 0.04
                excedente_neto = ingreso_bruto_fletes - costo_total - retencion_isr
                excedente_coop_calculado = excedente_neto
                
                l_m1, l_m2 = st.columns(2)
                l_m1.metric("Ingresos Brutos de Transporte", f"${ingreso_bruto_fletes:,.2f} MXN")
                l_m2.metric("Excedente Neto Líquido", f"${excedente_neto:,.2f} MXN", delta="Inyección síncrona a Caja")
                
            elif "Microseguros" in entidad_activa_centro or "S.A." in entidad_activa_centro:
                st.markdown("##### 📊 Retorno de Corretaje Social y Primas Mutuales")
                st.caption("Mitigación de riesgos en maquinaria pesada popular y reaseguro comunitario CNSF.")
                prima_mensual = st.number_input("Prima Monsual por Unidad de Trabajo:", min_value=50.0, value=120.0, key='pr_sa')
                retorno_pct = st.slider("Porcentaje de Retorno Social Pactado para la A.C.:", min_value=5, max_value=40, value=20, key='pct_sa')
                
                prima_anual = float(65 * prima_mensual * 12)
                retorno_anual = prima_anual * (retorno_pct / 100)
                
                s_m1, s_m2 = st.columns(2)
                s_m1.metric("Recaudación de Primas Brutas (Anual)", f"${prima_anual:,.2f} MXN")
                s_m2.metric("Transferencia Docente a la A.C.", f"${retorno_anual:,.2f} MXN", "Libre de IVA")
                
            else:
                st.markdown("##### 🧪 Fideicomisos Tecnológicos Científicos Autónomos")
                st.caption("Control presupuestal de laboratorios barriales para el Upcycling de mermas de maquiladoras.")
                fondos_id = st.number_input("Fondos de Fomento Tecnológico Captados (MXN):", min_value=5000, value=75000, key='f_id')
                becas_asig = st.slider("Número de Investigadores Co-Diseñadores Becados:", min_value=1, max_value=20, value=4)
                st.metric("Disponibilidad neta para Reactivos de Ingeniería Inversa", f"${fondos_id:,.2f} MXN", f"{becas_asig} Becas Activas")

        # 2. PESTAÑA DINÁMICA: PARÁMETROS FISCALES ADAPTATIVOS CONFORME AL CONTEXTO
        with tab_fiscal:
            st.subheader("🛡️ Cumplimiento SAT y Alertas Tributarias")
            
            if "Matriz" in entidad_activa_centro or "A.C." in entidad_activa_centro:
                st.warning("⚠️ Alerta SAT: Los recibos de nómina asimilada deben timbrarse antes del día 10 del mes subsecuente.")
                st.info("Estatus IVA: Exención del 100% de traslado en servicios educativos y capacitación (Art. 15 LIVA).")
            elif "Logística" in entidad_activa_centro or "S.C." in entidad_activa_centro:
                st.warning("⚠️ Alerta SAT: Las plantas maquiladoras contratantes retendrán obligatoriamente el 4% de ISR sobre fletes terrestres.")
                st.info("Estatus LGSC: Excedentes distribuidos exentos de base gravable mercantil corporativa ordinaria.")
            elif "Microseguros" in entidad_activa_centro or "S.A." in entidad_activa_centro:
                st.warning("⚠️ Alerta SAT: Facturación electrónica ordinaria con desglose del 16% de IVA mercantil en pólizas de daños comerciales.")
            else:
                st.success("✓ Estatus Fiscal: Aportaciones científicas directas consideradas gastos deducibles autorizados a tasa cero.")
# ==============================================================================
# PARTE 13b DE 14: COLUMNA IZQUIERDA (CENTRO) - ENTORNO ANALÍTICO CONMUTABLE (PARTE 2)
# ==============================================================================
        # 3. PESTAÑA DINÁMICA: MODELADO ACTUARIAL Y AJUSTE DE VARIABLES LATENTES
        with tab_actuarial:
            st.subheader("🔮 Indicadores Críticos y Variables Latentes (Escala Likert)")
            if "Investigación" in entidad_activa_centro or "APSON" in entidad_activa_centro:
                st.info("Análisis de Variable Latente: 'Capacidad de Absorción del Saber Científico en Talleres de Barrio'")
                st.caption("Fórmula psicométrica estimada mediante mínimos cuadrados parciales basados en ítems observables de campo [X1 a X7].")
            else:
                st.info("Análisis de Variable Latente: 'Aceptación Institucional del Modelo de Economía Popular'")
                st.caption("Mapea el nivel de confianza y la tasa de tránsito voluntario de efectivo informal a transferencias reguladas.")
            
            st.progress(85)
            st.caption("Índice de Materialidad y Consistencia General del Ecosistema JZPAC: <b>85.4%</b> (Nivel Excelente)", unsafe_allow_html=True)

        # 4. NUEVA PESTAÑA DE CLASE MUNDIAL: INNOVACIÓN Y DETONADORES DE COMPETITIVIDAD
        with tab_innovacion:
            st.subheader("🚀 Estrategia de Expansión y Ganchos de Vinculación")
            st.caption("Rastreo predictivo de vacíos de mercado fronterizos y ventajas comerciales exclusivas de JZPAC.")
            st.markdown("---")
            
            if "Matriz" in entidad_activa_centro or "A.C." in entidad_activa_centro:
                st.markdown("### 🟢 Nodo Central: Asociación Civil Matriz")
                st.error("❌ **El Vacío en Agua Prieta:** Las escuelas de oficios tradicionales operan de forma informal o arrastran una pesada carga fiscal que ahoga los ingresos netos de los instructores barriales.")
                st.success("⚡ **El Servicio Detonador JZPAC:** **Escudo Fiscal Corporativo Avanzado con Nómina Asimilada (Art. 94 LISR).** Ofrece a los líderes un ecosistema que blinda sus honorarios como deducciones de Título II y exenta el 100% del traslado del 16% de IVA en capacitación (Art. 15 LIVA).")
                st.info("🎯 **Gancho de Vinculación Ejecutiva:** Formalización patrimonial limpia y segura para captar de inmediato a los mejores capacitadores independientes de la frontera.")
                
            elif "Logística" in entidad_activa_centro or "S.C." in entidad_activa_centro:
                st.markdown("### 🔵 Subsistema Operativo: Cooperativa de Logística")
                st.error("❌ **El Vacío en Agua Prieta:** Las uniones de fletes locales carecen de analítica; cobran tarifas a ciegas y sufren pérdidas críticas debido al **Factor de Retorno Vacío (Deadhead)** en aduanas y la volatilidad del diésel.")
                st.success("⚡ **El Servicio Detonador JZPAC:** **Logística Predictiva de Última Milla.** Software analítico integrado (Streamlit) que recalcula tarifas en caliente deduciendo factores de retorno aduanal, aislando el 4% de retención de ISR e inyectando un 6% para el fondo de amortiguación de combustible.")
                st.info("🎯 **Gancho de Vinculación Ejecutiva:** Optimización y aumento inmediato de ganancias netas por kilómetro recorrido para atraer a choferes independientes y pequeñas flotillas de la región.")
                
            elif "Microseguros" in entidad_activa_centro or "S.A." in entidad_activa_centro:
                st.markdown("### 💛 Subsistema de Riesgos: Agencia de Microseguros")
                st.error("❌ **El Vacío en Agua Prieta:** Las aseguradoras comerciales tradicionales (AXA, GNP) exigen primas excluyentes e historial bancario que marginan a los micro-talleres, artesanos y costureras de las colonias.")
                st.success("⚡ **El Servicio Detonador JZPAC:** **Póliza Colectiva Solidaria con Retorno de Corretaje Social.** Cobertura total de maquinaria a micro-primas accesibles, donde **el 20% de la recaudación se regresa directamente a la comunidad** bajo la figura reglamentada de Honorarios de Corretaje Social Docente.")
                st.info("🎯 **Gancho de Vinculación Ejecutiva:** Protección patrimonial real de herramientas de trabajo con reinversión comunitaria del 20%, inutilizando la competencia de las aseguradoras comerciales capitalistas.")
                
            else:
                st.markdown("### 🧪 Subsistema de I+D: Equipo Científico APSON")
                st.error("❌ **El Vacío en Agua Prieta:** Las consultoras o universidades ejecutan estudios teóricos o descriptivos básicos, totalmente desconectados del nearshoring industrial y del aprovechamiento real de residuos.")
                st.success("⚡ **El Servicio Detonador JZPAC:** **Modelado de Variables Latentes + Upcycling Industrial.** Ingeniería inversa metalmecánica para el reciclaje de alto valor de las mermas que desechan las grandes plantas maquiladoras de la zona fronteriza, licenciando patentes sociales a tasa cero.")
                st.info("🎯 **Gancho de Vinculación Ejecutiva:** Alianza con corporativos extranjeros para cumplir con cuotas de Responsabilidad Social Empresarial (ESG) y reducir sus costos de confinamiento de basura industrial.")

        # 5. PESTAÑA DINÁMICA: HISTORIAL DE DESCARGAS DEL CONTEXTO
        with tab_log:
            st.header("📑 Historial de Auditoría de Descargas")
            if len(st.session_state["historial_descargas"]) == 0:
                st.info("No se registran descargas en el ciclo operativo actual.")
            else:
                st.table(st.session_state["historial_descargas"])

        # INSTRUCCIÓN DE TRÁNSITO PARA IMPORTACIÓN DIRECTA A GOOGLE DOCS
        st.markdown("---")
        st.markdown("""
        <div style='background-color: #f1f3f5; padding: 12px; border-radius: 6px; border-left: 5px solid #4285f4;'>
            <p style='margin-bottom:0px; font-size:12px; color: #495057;'>
                💡 <b>Sincronización con Google Drive:</b> Para abrir cualquier manual en <b>Google Docs</b>, descarga el archivo en formato 
                <b>.docx (Word)</b> desde el panel de la derecha, arrástralo a tu cuenta de Google Drive y elígelo con un click derecho para 
                'Abrir con: Documentos de Google'. El formateo corporativo se mantendrá intacto y editable en la nube.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# PARTE 14 DE 14: COLUMNA DERECHA - LOGOTIPO, IDIOMA BILINGÜE Y ADICIÓN DE ENTIDADES
# ==============================================================================
with col_derecha_documental:
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; margin-bottom: 12px; text-align: center;'>
        <h2 style='color: #1e4620; margin-top:0; font-size:15px; font-weight:bold; text-transform: uppercase; letter-spacing: 0.5px;'>JACOB ZUMAYA PRIANTI, A.C.</h2>
        <p style='color: #6c757d; font-size:11px; margin-bottom:10px;'>Ecosistema de Economía Popular Fronteriza</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        st.image("JZPACLOGOREDONDO.png", caption="Logotipo Oficial JZPAC", use_container_width=True)
    except Exception:
        st.caption("🦅 [Imagen: JZPACLOGOREDONDO.png Cargada en Repositorio]")
        
    st.markdown("#### 🌐 Idioma de Descarga / Language")
    idioma_elegido = st.radio("Output language parameter:", ["Español (ES)", "English (EN)"], horizontal=True, key="selector_idioma_global")
    is_english = (idioma_elegido == "English (EN)")
    
    st.markdown("---")
    st.markdown("<b style='font-size:13px; color:#495057;'>🗂️ Almacén Documental Autónomo:</b>", unsafe_allow_html=True)
    lista_entidades = list(st.session_state["repositorio_institucional"].keys())
    seleccion_entidad = st.selectbox("🏢 1. Selecciona la Entidad / Subsistema:", ["-- Elige una Entidad --"] + lista_entidades)
    
    if seleccion_entidad != "-- Elige una Entidad --":
        st.markdown("#### 📘 Compilar Libro Unificado (APA 7)")
        st.caption("Encuaderna los manuales, el padrón y el contrato con Índice y Paginación en una sola monografía de color forestal.")
        
        dict_marcos_libro = st.session_state["repositorio_institucional"][seleccion_entidad]
        pdf_libro_completo = generar_libro_apa7(seleccion_entidad, dict_marcos_libro, lang_en=is_english)
        
        label_btn_libro = "📥 Download Complete Compendium (PDF)" if is_english else "📥 Descargar Libro Compendio (PDF)"
        if st.download_button(label=label_btn_libro, data=pdf_libro_completo, file_name=f"Compendio_{seleccion_entidad.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True):
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

    # --- ENTORNO EXPANDIDO: OPCIÓN DE ADHERIR NUEVAS ENTIDADES EN EL TIEMPO ---
    st.markdown("---")
    st.markdown("#### ➕ Escalar Ecosistema (Nuevas Entidades)")
    with st.expander("🛠️ Registrar Nuevo Subsistema en Blanco"):
        nueva_ent_nombre = st.text_input("Nombre de la Nueva Entidad / Cooperativa:", placeholder="Ej. 5. Cooperativa de Calzado APSON (S.C.)")
        if st.button("🚀 Dar de Alta Entidad Estatus Activo", use_container_width=True):
            if nueva_ent_nombre and nueva_ent_nombre.strip():
                nombre_limpio = nueva_ent_nombre.strip()
                if nombre_limpio not in st.session_state["repositorio_institucional"]:
                    st.session_state["repositorio_institucional"][nombre_limpio] = {
                        "Marco conceptual y descriptivo": "Borrador de marco operativo del nuevo subsistema de Agua Prieta.",
                        "Marco legal": "Borrador de marco legal en espera de adición fiscal para JACOB ZUMAYA PRIANTI, A.C.",
                        "Manual de procedimientos": "Borrador de manual de procedimientos.",
                        "Manual administrativo": "Borrador de manual administrativo.",
                        "Manual de Tendencias criticas": "Borrador de tendencias.",
                        "Manual de Variables latentes con items observables": "Borrador de variables latentes.",
                        "Contrato de Incorporación y Adhesión Individual": "Borrador de contrato individual.",
                        "Acta Constitutiva Notarial Oficial": "Borrador de sub-acta constitutiva notarial oficial para firma de asamblea.",
                        "Directores Asociados Registrados (Padrón Oficial)": "Padrón oficial del nuevo subsistema en espera de altas reglamentarias."
                    }
                    st.success(f"✓ '{nombre_limpio}' añadida de forma permanente al almacén.")
                    st.rerun()
                else:
                    st.warning("Esta entidad ya existe en el almacén documental.")
            else:
                st.error("Por favor, introduce un nombre válido.")

    st.markdown("#### 📤 Uploading de Nuevas Actas (.txt)")
    archivo_cargado = st.file_uploader("Sube un acta complementaria:", type=["txt"])
    if archivo_cargado is not None:
        nombre_archivo_crudo = archivo_cargado.name.replace(".txt", "")
        if nombre_archivo_crudo not in st.session_state["repositorio_institucional"]:
            try:
                contenido_texto = archivo_cargado.read().decode("utf-8", errors="ignore")
                st.session_state["repositorio_institucional"][nombre_archivo_crudo] = {
                    "Marco conceptual y descriptive": contenido_texto,
                    "Marco legal": "Borrador de marco legal en espera de adición fiscal para JACOB ZUMAYA PRIANTI, A.C.",
                    "Manual de procedimientos": "Borrador de manual de procedimientos en espera de adición operativa.",
                    "Manual administrativo": "Borrador de manual administrativo.",
                    "Manual de Tendencias criticas": "Borrador de tendencias críticas.",
                    "Manual de Variables latentes con items observables": "Borrador de variables latentes.",
                    "Contrato de Incorporación y Adhesión Individual": "Borrador de contrato de incorporación individual.",
                    "Acta Constitutiva Notarial Oficial": "Borrador de acta notarial oficial.",
                    "Directores Asociados Registrados (Padrón Oficial)": "Padrón oficial en espera de altas."
                }
                st.success(f"✓ '{archivo_cargado.name}' guardado e indexado.")
                st.rerun()
            except Exception:
                st.error("Error al indexar el archivo complementario.")

# MATRIZ FINANCIERA DE CIERRE AL PIE DE LA INTERFAZ
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0; font-size:14px; font-weight:bold;'>🟢 Nodo Central: JACOB ZUMAYA PRIANTI, A.C.</h4><p style='color: #1c7430; font-size: 12px;'><b>Estatus:</b> 0% IVA / Escudo 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 12px; border-radius: 6px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0; font-size:14px; font-weight:bold;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 12px;'><b>Impacto:</b> Capitaliza excedentes netos de fletes e intermediación libre de ISR.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0; font-size:14px; font-weight:bold;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 12px;'><b>Impacto:</b> Transforma primas comerciales de la S.A. en fondos de fomento.</p></div>", unsafe_allow_html=True)
