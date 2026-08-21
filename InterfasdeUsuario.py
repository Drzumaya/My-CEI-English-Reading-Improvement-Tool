import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado estable de PDFs en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# PARTE 1 DE 20: CONFIGURACIÓN INICIAL DEL LIENZO VISUAL DE LA PLATAFORMA
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - JACOB ZUMAYA PRIANTI, A.C.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ==============================================================================
# PARTE 2 DE 20: INICIALIZACIÓN DE CONTEXTOS Y CONTROL DE SESIÓN REGISTRAL
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
# PARTE 3 DE 20: BASE DE DATOS ACTIVA DEL PADRÓN DE DIRECTORES ASOCIADOS
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
# PARTE 4 DE 20: ALMACÉN DOCUMENTAL ES-419 - ASOCIACIÓN CIVIL MATRIZ (A.C.)
# ==============================================================================
if "repositorio_es" not in st.session_state:
    st.session_state["repositorio_es"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL\n\nFunciona como la sociedad controladora social (Holding) que coordina los subsistemas autónomos en Agua Prieta. Diseña los planes de capacitación para el trabajo de la periferia urbana.",
            "Marco legal": "FUNDAMENTACIÓN FISCAL TÍTULO II LISR\n\nTributa en Régimen General corporativo (30% ISR). Blinda sus egresos comunitarios al 100% como deducciones mediante Nómina Asimilada (Art. 94 LISR). Exenta de trasladar el 16% de IVA en capacitación según el Art. 15 de la LIVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS DE GOBERNANZA CENTRAL (MAP-01)\n\n1. Recepción de comisiones de la S.A. y aportaciones cooperativas.\n2. Validación de listas de asistencia de talleres.\n3. Dispersión mensual y timbrado de CFDI de asimilados a salarios.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RECURSOS HUMANOS Y CONTROL (MAC-01)\n\nRegula las políticas de contratación de promotores barriales, el control de activos en comodato y los lineamientos de transparencia para auditorías externas del SAT.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS Y RIESGO SOCIOECONÓMICO (MTC-01)\n\nMonitorea la inflación en la franja fronteriza, los cambios en las reglas misceláneas del SAT y el impacto del tipo de cambio peso-dólar en el poder adquisitivo de Agua Prieta.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EVALUACIÓN DE ADOPCIÓN DE PROGRAMAS SOCIALES\n\nVARIABLE LATENTE CENTRAL: 'Aceptación Institucional del Modelo de Economía Popular'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Frecuencia con la que el asociado acude voluntariamente a las mesas de gobernanza de la A.C.\n2. [X2] Nivel de confianza percibido en la transparencia del manejo de fondos del Título II corporativo.\n3. [X3] Disposición declarada para transitar de contratos informales en efectivo a Nómina de Asimilados.\n4. [X4] Grado de recomendación del programa de capacitación de la A.C. a otros microemprendedores del barrio.\n5. [X5] Percepción de mejora en la estabilidad de su negocio tras el cobro vía recibo estatutario.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ADHESIÓN Y ASIMILACIÓN A SALARIOS (A.C. MATRIZ)\n\nCONTRATO que celebran por una parte la Asociación Civil Matriz, y por la otra el Usuario Inscrito por propio derecho en su carácter de Director Asociado de Célula Barrial, al tenor de las siguientes cláusulas:\n\nPRIMERA: OBJETO. El Usuario acepta la designación técnica para coordinar los talleres de capacitación para el trabajo y fomento económico en su colonia asignada de Agua Prieta.\n\nSEGUNDA: RÉGIMEN FISCAL. El Usuario manifiesta su consentimiento expreso para someter sus honorarios de apoyo al régimen de Asimilados a Salarios (Art. 94 Fracc. V de la LISR), obligándose la A.C. a retener el impuesto correlativo y timbrar el CFDI de nómina para amparar deducciones autorizadas de Título II.\n\nTERCERA: EXENCIÓN DE IVA. Las partes acuerdan que las cuotas extraordinarias que recaude el Usuario de los talleres se consideran cuotas de miembros exentas de IVA (Art. 15-XII LIVA) y se integrarán de inmediato a la cuenta de orden de la Caja de Ahorro.",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [XXXX] | VOLUMEN: [XX]\nCONSTITUCIÓN DE ASOCIACIÓN CIVIL BAJO EL RÉGIMEN GENERAL (TÍTULO II LISR)\n\nEn la ciudad de Agua Prieta, Estado de Sonora, ante mí, Notario Público Número [X], comparecen los Asociados Fundadores para formalizar de manera estricta el ACTA CONSTITUTIVA de la persona moral que se regirá bajo las siguientes cláusulas formales:\n\nCLÁUSULA PRIMERA: DENOMINACIÓN, DOMICILIO Y DURACIÓN.\nLa organización se denominará 'DESARROLLO OPERATIVO DE LA ECONOMÍA POPULAR DE AGUA PRIETA', seguida de las siglas 'A.C.'. Su domicilio legal definitivo se fija en Agua Prieta, Sonora, y su duración será por tiempo indefinido.\n\nCLÁUSULA SEGUNDA: OBJETO SOCIAL Y REMANENTES DISPONIBLES.\nEl objeto primordial consiste en impartir de forma gratuita y exenta de IVA (Art. 15 LIVA) capacitación para el trabajo, educación técnica, fomento de oficios y asesoría de microcréditos para la retención del valor fronterizo. Al operar bajo el Régimen General (Título II LISR), los excedentes o remanentes de operación no se distribuirán como dividendos capitalistas, sino que se capitalizarán en cuentas de orden para subsidiar activos del barrio o se dispersarán al 100% como erogaciones salariales asimiladas (Art. 94 LISR) a los Directores Asociados.\n\nCLÁUSULA TERCERA: PATRIMONIO SOCIAL Y ASAMBLEA CENTRAL.\nEl patrimonio de la A.C. se integrará por las cuotas ordinarias y extraordinarias de recuperación aportadas por sus Miembros Adherentes (Art. 15-XII LIVA), así como por las comisiones docentes y de fomento ingresadas desde sus subsistemas secundarios filiales. El órgano supremo es la Asamblea General de Asociados, representada por el Agente Capacitador como Director General, dotado de Poder General Amplio para Pleitos, Cobranzas y Actos de Dominio."
        },
# ==============================================================================
# PARTE 5 DE 20: ALMACÉN DOCUMENTAL ES-419 - COOPERATIVA DE LOGÍSTICA (S.C.)
# ==============================================================================
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA OPERATIVO DE TRANSPORTE BARRIAL\n\nAsociación de choferes y transportistas de base popular organizados para competir en el mercado de fletes industriales B2B y última milla, absorbiendo la demanda del nearshoring maquilador.",
            "Marco legal": "LEY GENERAL DE SOCIEDADES COOPERATIVAS (LGSC)\n\nSociedad Cooperativa de Producción de Servicios de Responsabilidad Limitada (S.C. de R.L. de C.V.). Las plantas maquiladoras contratantes efectúan la retención del 4% de ISR sobre fletes terrestres.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS OPERATIVOS LOGÍSTICOS (MOP-02)\n\n1. Asignación de rutas comerciales en Agua Prieta.\n2. Auditoría física del Factor de Retorno Vacío (Deadhead).\n3. Retención automática del 6% para el fondo de amortiguación de diésel.",
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE FLOTILLA Y MANTENIMIENTO (MAF-02)\n\nEstablece los roles de los Asociados Directores en la administración de talleres mecánicos asignados, control de bitácoras de viaje y asignación de viáticos logísticos fronterizos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS DE TRANSPORTE TRANSFRONTERIZO (MTC-02)\n\nAnaliza los tiempos de espera en las aduanas, la fluctuación estacional de la producción automotriz de las maquiladoras y el impacto de aranceles comerciales en el flujo de fletes.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA OPERATIVA DE LA LOGÍSTICA DE BARRIO\n\nVARIABLE LATENTE CENTRAL: 'Cultura de Optimización de Ruta en Choferes Cooperativistas'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Índice de cumplimiento exacto de los horarios de recolección aduanal.\n2. [X2] Nivel de reducción voluntaria reportada en el Factor de Retorno Vacío.\n3. [X3] Frecuencia de registro y uso correcto de la aplicación Streamlit para el reporte del COK.\n4. [X4] Grado de apego a los lineamientos de mantenimiento preventivo y revisión de presión de neumáticos.\n5. [X5] Proporción de fletes ejecutados sin registrar incidencias o penalizaciones por retraso.\n6. [X6] Disposición del chofer para cooperar en cargas consolidadas compartidas con otros talleres.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO DE ADHESIÓN INDIVIDUAL DE SOCIO TRABAJADOR COOPERATIVISTA (S.C. LOGÍSTICA)\n\nCONTRATO de adhesión que celebran la Sociedad Cooperativa de Logística y Transporte de los Barrios, y por la otra el Usuario en su carácter de Socio Conductor, bajo las siguientes cláusulas:\n\nPRIMERA: ASOCIACIÓN COMUNITARIA. El Usuario aporta su trabajo personal y se adhiere formalmente a las Bases Constitutivas vigentes, bajo el régimen de Responsabilidad Limitada amparado por la Ley General de Sociedades Cooperativas (LGSC).\n\nSEGUNDA: RETENCIONES Y COK. El Socio acepta registrar cada viaje en la aplicación de control analítico Streamlit de la A.C., deduciendo el Costo de Operación por Kilómetro (COK), el Factor de Retorno Vacío, el 4% de retención de ISR y aportando de forma síncrona el 6% para el fondo de amortiguación de diésel fronterizo.\n\nTERCERA: EXCEDENTES. El Socio Conductor reconoce que los excedentes netos de fletes calculados en la plataforma se inyectarán de forma legal a la Caja de Ahorro común, teniendo derecho a retiros de rendimientos sociales según los acuerdos de la Asamblea General.",
            "Acta Constitutiva Notarial Oficial": "INSCRIPCIÓN REGISTRAL MERCANTIL | FOJA: [XXX]\nBASES CONSTITUTIVAS DE SOCIEDAD COOPERATIVA DE RESPONSABILIDAD LIMITADA (S.C. DE R.L.)\n\nEn la Ciudad de Agua Prieta, Sonora, se formaliza el Acta de Asamblea Constitutiva de la Sociedad Cooperativa que se organiza de conformidad con la Ley General de Sociedades Cooperativas (LGSC) y el Código Comercio de México:\n\nCLÁUSULA PRIMERA: RÉGIMEN, DENOMINACIÓN Y JURISDICCIÓN.\nLa sociedad se denominará 'COOPERATIVA DE LOGÍSTICA Y TRANSPORTE TRANSFRONTERIZO DE AGUA PRIETA', operando obligatoriamente con las siglas 'S.C. DE R.L. DE C.V.'. Su responsabilidad frente a terceros queda estrictamente LIMITADA al monto de los certificados de aportación de sus miembros.\n\nCLÁUSULA SEGUNDA: OBJETO COMERCIAL Y CADENA DE VALOR B2B.\nEl objeto exclusivo consiste en prestar servicios integrales de transporte terrestre, carga pesada, distribución aduanal y fletes logísticos industriales B2B para las plantas maquiladoras de la zona norte del país. La sociedad se obliga a facturar conforme a las leyes fiscales mexicanas, aceptando la aplicación de la retención del 4% de ISR sobre fletes terrestres mandada por el SAT.\n\nCLÁUSULA TERCERA: CERTIFICADOS DE APORTACIÓN Y EXCEDENTES COOPERATIVOS.\nEl capital social se representa por certificados de aportación nominativos, indivisibles y de igual valor. Queda estrictamente establecido que al término de cada ejercicio contable mensual calibrado en el software Streamlit, se deducirá un 6% bruto de ingresos para blindar el fondo de reserva contra volatilidad de diésel y un 5% neto de excedentes que se inyectará de forma transparente a la cuenta de orden de la Asociación Civil central para sufragar el sostenimiento técnico del ecosistema."
        },
# ==============================================================================
# PARTE 6 DE 20: ALMACÉN DOCUMENTAL ES-419 - AGENCIA DE MICROSEGUROS (S.A.)
# ==============================================================================
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE CONTROL DE RIESGOS COMERCIAL\n\nEntidad financiera diseñada para proteger los activos mecánicos de los talleres populares y mitigar vulnerabilidades por accidentes de trabajo o fallecimiento de líderes comunitarios.",
            "Marco legal": "LEY DE INSTITUCIONES DE SEGUROS Y DE FIANZAS (LISF)\n\nSociedad Anónima regulada por la CNSF. Transfiere legalmente el 20% de las primas a la A.C. mediante contratos de Corretaje Social y capacitación en prevención de accidentes.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS Y ATENCIÓN DE SINIESTROS (MAP-03)\n\n1. Reporte técnico de avería mecánica o accidente en las colonias.\n2. Evaluación social del riesgo y dictamen del Asociado Director.\n3. Liquidación de la reparación con cargo al fondo de reserva.",
            "Manual administrative": "MANUAL ADMINISTRATIVO DE RESERVAS TÉCNICAS Y RECAUDACIÓN (MAR-03)\n\nRegula el proceso de cobranza mensual de las primas a través de plataformas digitales y el resguardo seguro del capital de reserva en instrumentos de renta fija de bajo riesgo.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS ACTUARIALES EN MICROSEGUROS (MTC-03)\n\nMide la tasa de siniestralidad de los talleres de barrio, la tasa de renovación de pólizas y proyecta modelos de vulnerabilidad ante fallas mecánicas en maquinaria pesada depreciada.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - PERCEPCIÓN DE SEGURIDAD PATRIMONIAL\n\nVARIABLE LATENTE CENTRAL: 'Aversión al Riesgo y Confianza en la Póliza Solidaria'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Puntualidad exacta en el pago de la prima mensual simulada en la plataforma.\n2. [X2] Grado de conocimiento de los talleres sobre el alcance real de las coberturas de siniestralidad.\n3. [X3] Nivel de tranquilidad manifestada por el micro-empresario respecto a la continuidad de su negocio.\n4. [X4] Frecuencia con la que el micro-taller reporta de forma preventiva riesgos de infraestructura.\n5. [X5] Confianza declarada en la velocidad de respuesta del fondo de reserva de la A.C. ante siniestros.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO COLECTIVO DE ADHESIÓN A LA PÓLIZA DE MICROSEGUROS FRONTERIZOS (S.A.)\n\nCONTRATO que celebran la Agencia de Protección Solidaria Fronteriza, S.A. de C.V., y por la otra el Usuario Inscrito en su carácter de Titular de Unidad Productiva Popular Asegurada, al tenor de las siguientes cláusulas:\n\nPRIMERA: COBERTURA INTEGRAL. El Usuario se adhiere a la póliza comunitaria colectiva para proteger sus activos mecánicos y herramientas de taller (soldadoras, tornos, cortadoras de cuero) contra averías técnicas graves, incendios o accidentes de operación en Agua Prieta.\n\nSEGUNDA: PRIMA SOCIAL Y RETORNO. El Asegurado se obliga a cubrir la prima mensual calculada dinámicamente en el Módulo 3. Reconoce que el 20% de dicha recaudación es transferido a la A.C. matriz por concepto de Honorarios de Capacitación en Prevención de Siniestros, libre de IVA comercial.\n\nTERCERA: RECLAMACIÓN JUSTA. En caso de ocurrencia de un siniestro, el Usuario se compromete a no iniciar litigios mercantiles ordinarios, sometiéndose al Manual de Procedimientos interno de la A.C., el cual dictaminará el pago y liquidación de daños con cargo al fondo de reserva técnico de forma inmediata.",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [YYYY] | VOLUMEN: [XXX]\nCONSTITUCIÓN DE SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE (RAMO RIESGOS CNSF)\n\nEn la Ciudad de Agua Prieta, Estado de Sonora, ante mí, Titular de la Notaría Pública Asociada, se formaliza la constitución de una SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE que se regirá bajo la Ley General de Sociedades Mercantiles (LGSM) y la Ley de Instituciones de Seguros y de Fianzas (LISF):\n\nCLÁUSULA PRIMERA: DENOMINACIÓN, DURACIÓN Y OBJETO REGULADO.\nLa denominación corporativa oficial será 'AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA', seguida de las siglas 'S.A. DE C.V.'. Su objeto exclusivo consiste en actuar como Agente de Seguros Persona Moral regulado por la CNSF, intermediando pólizas de microseguros colectivos de vida, accidentes de trabajo y daños estructurales mecánicos.\n\nCLÁUSULA SEGUNDA: CAPITAL SOCIAL Y DOMINIO DE LA ASOCIACIÓN CIVIL MATRIZ.\nEl capital social es variable, fijándose un monto mínimo obligatorio de capitalización de $50,000.00 MXN totalmente suscrito y pagado. Para blindar el patrimonio comunitario e impedir desvíos capitalistas privados, la Asociación Civil central del ecosistema retiene la titularidad del 99% de las acciones Clase 'A', teniendo el voto mayoritario absoluto en cualquier asamblea.\n\nCLÁUSULA TERCERA: GOBERNANZA, DEDUCCIONES Y CONTRATO DE RETORNO CORRETAJE.\nLa administración estará a cargo de un Administrador Único designado de forma directa por la Asamblea de la A.C. (Asociado Director). Para salvaguardar la deducibilidad de egresos mercantiles y fondeo de la Caja de Ahorro, la sociedad se obliga por estipulación estatutaria invulnerable a transferir el 20% de las primas brutas capturadas mensuales a la A.C. matriz bajo la figura de Honorarios de Corretaje Social y Docencia en Prevención de Accidentes."
        },
# ==============================================================================
# PARTE 7 DE 20: ALMACÉN DOCUMENTAL ES-419 - EQUIPO CIENTÍFICO APSON
# ==============================================================================
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE INVESTIGACIÓN, DESARROLLO E INNOVACIÓN (I+D)\n\nCélula científica encargada de realizar estudios de densidad económica, análisis metalúrgicos para el reciclaje (Upcycling) de las mermas de las maquiladoras y optimización de modelos predictivos de crédito social.",
            "Marco legal": "LEY GENERAL DE HUMANIDADES, CIENCIAS, TECNOLOGÍAS E INNOVACIÓN\n\nOpera bajo el amparo de la Cláusula Estatutaria de Autonomía de los Asociados Directores. Los fondos de investigación científica se consideran aportaciones de fomento exentas de IVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS EN RECOLECCIÓN Y PROCESAMIENTO (MAP-04)\n\n1. Recolección de muestras de mermas industriales (cueros, maderas, polímeros) en las maquiladoras.\n2. Pruebas de resistencia en laboratorios comunitarios.\n3. Transferencia de patentes sociales a los talleres.",
            "Manual administrative": "MANUAL ADMINISTRATIVO DE PROYECTOS Y FIDEICOMISOS CIENTÍFICOS (MAP-04)\n\nCoordina la gobernanza presupuestal de los laboratorios, la asignación de becas de investigación a estudiantes de Agua Prieta y el inventario de reactivos técnicos.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS EN INNOVACIÓN INDUSTRIAL (MTC-04)\n\nMapea las tecnologías emergentes de manufactura esbelta automatizada, el volumen de desperdicios utilizables por tipo de maquila y las proyecciones de crecimiento del nearshoring real.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA DE LA TRANSFERENCIA TECNOLÓGICA I+D\n\nVARIABLE LATENTE CENTRAL: 'Capacidad de Absorción del Saber Científico en Talleres de Barrio'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Tasa de adopción de manuales Lean-Barrio y diagramas de flujo técnicos dentro de los procesos diarios.\n2. [X2] Cantidad de mermas industriales recolectadas (cuero, madera) efectivamente transformadas.\n3. [X3] Frecuencia de asistencia de los artesanos a las células de co-diseño del Equipo Científico.\n4. [X4] Reducción porcentual de costos de materia prima lograda por el taller al sustituir insumos.\n5. [X5] Nivel de comprensión técnica manifestada por el micro-productor sobre el uso y cuidado de maquinaria.\n6. [X6] Cantidad de nuevos prototipos funcionales o innovaciones locales de producto generadas de forma autónoma.\n7. [X7] Incremento reportado en la calidad final de la proveeduría indirecta entregada a las plantas.",
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ASIGNACIÓN CIENTÍFICA Y PROPIEDAD INTELECTUAL SOCIAL (ID-APSON)\n\nCONTRATO que celebran la Asociación Civil e Investigación Científica APSON, y por la otra el Usuario en su carácter de Investigador o Técnico de Laboratorio Comunitario, al tenor de las siguientes cláusulas:\n\nPRIMERA: OBJETO DE TRANSFERENCIA. El Investigador se compromete a ejecutar análisis de densidad económica, estudios metalúrgicos de mermas industriales de maquiladoras y modelado de variables latentes en Agua Prieta.\n\nSEGUNDA: PATENTES SOCIALES. El Usuario acepta que toda propiedad intelectual desarrollada en las células de I+D pertenece al patrimonio común de la A.C. Queda prohibido el acaparamiento privado, licenciándose a tasa cero para el beneficio de los talleres populares.\n\nTERCERA: CONDICIÓN DE REMUNERACIÓN. Las retribuciones se canalizarán a través del fondo de fideicomisos científicos autónomos administrado por la Caja de Ahorro de la A.C., justificando la materialidad docente libre de IVA ante las autoridades hacendarias.",
            "Acta Constitutiva Notarial Oficial": "PROTOCOLO NOTARIAL DE NOMBRAMIENTO Y APERTURA DE CONSEJO DE INVESTIGACIÓN CIENTÍFICA\n\nEn la Ciudad de Agua Prieta, Sonora, ante la fe del Notario Público adscrito al protocolo estatal, se formaliza el Acta de Establecimiento y Gobierno de la célula científica con base en la Ley General de Ciencias y el Código Civil vigente:\n\nCLÁUSULA PRIMERA: AUTONOMÍA OPERATIVA Y DENOMINACIÓN DE NODO.\nEl subsistema científico operará bajo el nombre de 'EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON'. Goza de una Cláusula de Autonomía de Gestión delegada por la A.C. nodriza, permitiéndole al Asociado Director celebrar minutas, convenios y acuerdos técnicos con universidades y parques industriales sin requerir autorizaciones burocráticas previas.\n\nCLÁUSULA SEGUNDA: FINES CIENTÍFICOS Y MODELADO PATRIMONIAL SOCIAL.\nEl objeto primordial consiste en ejecutar investigación econométrica de variables latentes, mapear densidades de mermas industriales y realizar ingeniería inversa metalmecánica para el diseño de productos de reciclaje. Toda patente, secreto industrial o marca colectiva resultante se registrará ante el IMPI a nombre de la Asociación Civil matriz, quedando etiquetada bajo un fideicomiso de 'Uso Social Común' perpetuo a tasa cero para beneficio de los barrios de Agua Prieta.\n\nCLÁUSULA TERCERA: GOBERNANZA PRESUPUESTAL Y CUENTAS DE ORDEN EN CAJA.\nLa dirección científica recaerá en el Asociado Director electo por el consejo. Los fondos de fomento económico o becas captadas se depositarán directamente en la cuenta de orden de la Caja de Ahorro de la A.C., amparando la completa materialidad de las investigaciones para fines científicos exentos de IVA, prohibiéndose el uso especulativo o financiero mercantil ajeno a la economía popular."
        }
    }
# ==============================================================================
# PARTE 8 DE 20: ALMACÉN DOCUMENTAL EN-US - ASOCIACIÓN CIVIL MATRIZ (A.C.)
# ==============================================================================
if "repositorio_en" not in st.session_state:
    st.session_state["repositorio_en"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "PARENT ACADEMY AND SOCIAL CONTAINMENT SYSTEM\n\nOperates as the social holding entity that coordinates autonomous subsystems in Agua Prieta. Designs technical training plans for work and inclusion for the urban periphery.",
            "Marco legal": "FISCAL AMENDMENT UNDER TITLE II OF MEXICAN INCOME TAX LAW\n\nTributable under Corporate General Regime (30% ISR). Converts direct community outlays into 100% legitimate deductions via Assimilated Wages (Art. 94 LISR). Exempt from VAT under Art. 15 of LIVA.",
            "Manual de procedimientos": "CENTRAL GOVERNANCE PROCEDURES MANUAL (MAP-01)\n\n1. Collection of comissions from the S.A. and cooperative contributions.\n2. Validation of workshop attendance logs.\n3. Monthly dispersion and CFDI digital invoicing of assimilated wages.",
            "Manual administrativo": "ADMINISTRATIVE MANUAL FOR HUMAN RESOURCES AND AUDIT CONTROL (MAC-01)\n\nRegulates hiring policies for neighborhood promoters, asset allocation under commodatum, and SAT transparency guidelines.",
            "Manual de Tendencias criticas": "CRITICAL TENDENCIES AND SOCIOECONOMIC RISK MANUAL (MTC-01)\n\nMonitors border-zone inflation, SAT miscellany amendments, and MXN-USD exchange rate fluctuations in Agua Prieta.",
            "Manual de Variables latentes con items observables": "LATENT VARIABLES MANUAL - SOCIAL PROGRAM ADOPTION METRICS\n\nLATENT CONSTRUCT: 'Institutional Acceptance of the Popular Economy Model'\n\nOBSERVABLE ITEMS (Likert Scale 1-5):\n1. [X1] Frequency of voluntary attendance at central A.C. governance tables.\n2. [X2] Perceived level of trust in the transparency of Title II corporate fund handling.\n3. [X3] Expressed willingness to transition from informal cash arrangements to Assimilated Salaries.\n4. [X4] Degree of recommendation of the A.C. training program to other neighborhood micro-entrepreneurs.\n5. [X5] Perception of business stability improvement after statutory receipt adoption.",
            "Contrato de Incorporación y Adhesión Individual": "INDIVIDUAL ADHESION AND ASSIMILATED WAGES CONTRACT\n\nCONTRACT celebrated between the Parent Association Civil, and the Registered User as an Associated Director, under the following clauses:\n\nFIRST: OBJECT. User accepts the assignment to coordinate local training workshops in Agua Prieta.\n\nSECOND: FISCAL REGIME. User consents to subject supports to the Assimilated to Salaries tax regime (Art. 94 LISR).\n\nTHIRD: VAT EXEMPTION. Extraordinaries receipts represent statutory member quotas exempt from VAT (Art. 15 LIVA).",
            "Acta Constitutiva Notarial Oficial": "OFFICIAL NOTARIAL DEED NUMBER: [XXXX] | VOLUME: [XX]\nCONSTITUTION OF AN ASSOCIATION CIVIL UNDER TITLE II TAX REGIME\n\nIn the City of Agua Prieta, Sonora, before me, Notary Public Number [X], founders formalize the STATUTORY DEED under the following rules:\n\nFIRST CLAUSE: DENOMINATION. The organization shall be named 'DESARROLLO OPERATIVO DE LA ECONOMÍA POPULAR DE AGUA PRIETA', A.C.\n\nSECOND CLAUSE: SOCIAL OBJECT. Imparting free and VAT-exempt work training (Art. 15 LIVA). Surplus will be capitalized or dispersed as assimilated salaries (Art. 94 LISR).\n\nTHIRD CLAUSE: ASSETS. Quotas are exempt under Art. 15-XII LIVA. The supreme organ is the General Assembly represented by the Central Capacitator."
        },
# ==============================================================================
# PARTE 9 DE 20: ALMACÉN DOCUMENTAL EN-US - COOPERATIVA DE LOGÍSTICA (S.C.)
# ==============================================================================
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "NEIGHBORHOOD FREIGHT AND OPERATIONAL COOPERATIVE\n\nAssociation of popular drivers organized to compete in the industrial B2B last-mile market, capturing indirect demand from maquiladora nearshoring.",
            "Marco legal": "GENERAL LAW OF COOPERATIVE SOCIETIES (LGSC)\n\nCooperative Society of Production of Services of Limited Liability (S.C. de R.L. de C.V.). Anchor maquiladoras apply a mandatory 4% ISR withholding.",
            "Manual de procedimientos": "LOGISTICS PROCEDURES MANUAL (MOP-02)\n\n1. Assignment of commercial routes in Agua Prieta.\n2. Physical audit of the Deadhead Empty Return Factor.\n3. Automatic 6% withholding for the border diesel stabilization buffer.",
            "Manual administrativo": "FLEET MANAGEMENT AND MAINTENANCE ADMINISTRATIVE MANUAL (MAF-02)\n\nEstablishes Associated Directors' roles in supervising fleet mechanics, trip logs, and border per diem allocations.",
            "Manual de Tendencias criticas": "CRITICAL TENDENCIES IN TRANSBORDER FREIGHT (MTC-02)\n\nAnalyzes customs border wait times, seasonal automotive production cycles, and tariff impacts.",
            "Manual de Variables latentes con items observables": "LATENT VARIABLES MANUAL - LAST MILE OPERATIONS\n\nLATENT CONSTRUCT: 'Route Optimization Culture among Conductor Partners'\n\nOBSERVABLE ITEMS (Likert Scale 1-5):\n1. [X1] Compliance index with scheduled collection times at the customs terminal.\n2. [X2] Voluntary reduction rate in the Deadhead Factor via backhaul consolidation.\n3. [X3] Frequency of correct Streamlit app deployment to report the Operational Cost per Kilometer (COK).\n4. [X4] Attachment degree to preventative asset maintenance and tire pressure regulations.\n5. [X5] Ratio of freight executed without registering delays or commercial penalties.\n6. [X6] Partner availability to handle shared consolidated freights with other neighborhood units.",
            "Contrato de Incorporación y Adhesión Individual": "INDIVIDUAL COOPERATIVE WORKER ADHESION CONTRACT\n\nCONTRACT signed between the Cooperative Society and the User as a Conductor Partner under the following clauses:\n\nFIRST: ADHESION. User contributes personal work under Limited Liability regulations (LGSC).\n\nSECOND: WITHHOLDINGS. Partner accepts tracking journeys via the Streamlit app, computing COK, Deadhead, and 4% ISR.\n\nTHIRD: SURPLUS. Net surpluses will be injected into the common Savings Fund, giving right to social drawdowns.",
            "Acta Constitutiva Notarial Oficial": "COMMERCIAL REGISTRY INSCRIPTION | LEAF: [XXX]\nCOOPERATIVE STATUTORY BASE DEED OF LIMITED LIABILITY (S.C. DE R.L.)\n\nIn Agua Prieta, Sonora, the Assembly Deed is formalised under the General Law of Cooperative Societies (LGSC):\n\nFIRST CLAUSE: REGIME. The society will be 'COOPERATIVA DE LOGÍSTICA Y TRANSPORTE TRANSFRONTERIZO DE AGUA PRIETA', S.C. DE R.L. DE C.V.\n\nSECOND CLAUSE: MERCANTIL OBJECT. Last-mile freight logistics for border assembly plants. Invoicing will include the 4% ISR SAT withholding.\n\nTHIRD CLAUSE: CAPITAL ASSETS. Capital is represented by indivisible certificates. 6% will fund the fuel buffer and 5% net surplus will fund the Parent A.C."
        },
# ==============================================================================
# PARTE 10 DE 10: ALMACÉN DOCUMENTAL EN-US - AGENCIA DE MICROSEGUROS (S.A.)
# ==============================================================================
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "RISK MANAGEMENT FILIAL AND SOLIDARITY PÓLIZA\n\nFinancial cell engineered to protect workshops' machinery and mitigate vulnerabilities due to labor accidents or death of neighborhood leaders.",
            "Marco legal": "LAW OF INSURANCE AND BONDING INSTITUTIONS (LISF)\n\nCorporation (S.A.) monitored by the CNSF. Transfers 20% of premiums to the A.C. via Social Brokerage and risk mitigation training.",
            "Manual de procedimientos": "CLAIMS PROCEDURES MANUAL (MAP-03)\n\n1. Technical incident or machinery damage report in neighborhoods.\n2. Social risk evaluation and Associated Director dictamen.\n3. Damage liquidation funded by the technical reserve.",
            "Manual administrative": "TECHNICAL RESERVES ADMINISTRATIVE MANUAL (MAR-03)\n\nRegulates the collection process via digital channels and secure capital allocation in low-risk fixed income assets.",
            "Manual de Tendencias criticas": "CRITICAL ACTUARIAL TENDENCIES IN MICROINSURANCE (MTC-03)\n\nMeasures the accident ratio inside neighborhood units, policy renewal cycles, and macro-vulnerability projections.",
            "Manual de Variables latentes con items observables": "LATENT VARIABLES MANUAL - FINANCIAL SECURITY PERCEPTION\n\nLATENT CONSTRUCT: 'Risk Aversion and Trust in the Solidarity Policy'\n\nOBSERVABLE ITEMS (Likert Scale 1-5):\n1. [X1] On-time payment of the monthly premium simulated in Module 3.\n2. [X2] Level of understanding among workshops regarding machinery damage policy coverage.\n3. [X3] Stated tranquility of the producer regarding business continuity during mechanical failures.\n4. [X4] Frequency of preventative infrastructure risk reports filed to the Associated Director.\n5. [X5] Confidence index in the technical response velocity of the A.C. emergency fund.",
            "Contrato de Incorporación y Adhesión Individual": "COLLECTIVE MICROINSURANCE ADHESION ADHERENT CONTRACT\n\nCONTRACT between the Agency and the User as a Protected Workshop Owner under the following rules:\n\nFIRST: COVERAGE. User adheres to the collective policy to protect assets against severe mechanical failures.\n\nSECOND: PREMIUM. Insured pays the premium from Module 3. Recognizes 20% is transferred to the parent A.C. as training honorariums.\n\nTHIRD: CLAIMS. In case of damages, User accepts the internal manual dictamen funded by the reserve.",
            "Acta Constitutiva Notarial Oficial": "NOTARIAL DEED NUMBER: [YYYY] | VOLUME: [XXX]\nCONSTITUTION OF A CORPORATION FOR RISK BROKERAGE (S.A. DE C.V.)\n\nBefore me, Notary Public, a Corporation is formalized under the General Law of Commercial Societies (LGSM) and LISF:\n\nFIRST CLAUSE: DENOMINATION. It shall operate as 'AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA', S.A. DE C.V.\n\nSECOND CLAUSE: CAPITAL AND CONTROL. Parent A.C. retains 99% of Class A voting shares to safeguard assets.\n\nTHIRD CLAUSE: REVENUE RETURNING. The corporation is obligated to transfer 20% of monthly premiums to the parent A.C. as risk-prevention teaching fees."
        },
# ==============================================================================
# PARTE 11 DE 20: ALMACÉN DOCUMENTAL EN-US - EQUIPO CIENTÍFICO APSON
# ==============================================================================
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "RESEARCH, DEVELOPMENT AND INNOVATION SUBSISTEMA (R&D)\n\nScientific node focused on economic density, metallurgical upcycling of maquiladora wastes, and social credit risk calibrations.",
            "Marco legal": "GENERAL LAW OF HUMANITIES, SCIENCES, TECHNOLOGIES AND INNOVATION\n\nOperates under the Autonomy Clause. Research grants from public or private funds represent social investments exempt from VAT.",
            "Manual de procedimientos": "RECOVERY AND PROCESSING TECHNICAL MANUAL (MAP-04)\n\n1. Collection of material wastes (leather, timber, polymers) from maquiladoras.\n2. Stress-testing inside community laboratories.\n3. Transfer of social patents to the workshops.",
            "Manual administrative": "PROJECT GOVERNANCE AND SCIENTIFIC GRANTS ADMINISTRATIVE MANUAL (MAP-04)\n\nCoordinates budget allocation for labs, research scholarships for Agua Prieta students, and reactives inventory tracking.",
            "Manual de Tendencias criticas": "CRITICAL TENDENCIES IN INDUSTRIAL INNOVATION (MTC-04)\n\nMaps automated lean manufacturing developments, waste volumes by facility, and real nearshoring growth trends.",
            "Manual de Variables latentes con items observables": "LATENT VARIABLES MANUAL - TECHNOLOGY TRANSFER RESULTS\n\nLATENT CONSTRUCT: 'Absorptive Capacity of Scientific Knowledge in Neighborhood Workshops'\n\nOBSERVABLE ITEMS (Likert Scale 1-5):\n1. [X1] Adoption rate of Lean-Barrio manuals and technical flowcharts inside daily routing.\n2. [X2] Volume of raw industrial wastes successfully converted into high-end commercial products.\n3. [X3] Attendance frequency of artisans at co-design workshops held by the Scientific Team.\n4. [X4] Percent cost reduction achieved by replacing commercial inputs with upcycled maquiladora materials.\n5. [X5] Level of technical comprehension shown by the producer regarding financed machinery operations.\n6. [X6] Number of functional new prototypes or local product modifications generated by the community.\n7. [X7] Reported quality increase in indirect supply chains delivered to transnational assembly plants.",
            "Contrato de Incorporación y Adhesión Individual": "INDIVIDUAL SCIENTIFIC ENGAGEMENT AND SOCIAL PROPRIETY CONTRACT\n\nCONTRACT celebrated between the A.C. and the User as a Laboratory Researcher under the following rules:\n\nFIRST: LABORS. Researcher commits to perform economic density studies and metallurgical upcycling analyses.\n\nSECOND: SOCIAL PATENTS. Intellectual property belongs to the parent A.C. Asset commercialization is prohibited.\n\nTHIRD: STIPEND. Remunerations will be dispersed from the science grant fund administered by the common Savings Fund.",
            "Acta Constitutiva Notarial Oficial": "NOTARIAL RESOLUTION DEED | SCIENTIFIC GOVERNANCE ESTABLISHMENT\n\nIn Agua Prieta, Sonora, the establishment of the scientific node is formalized under the Civil Code and science regulations:\n\nFIRST CLAUSE: AUTONOMY. It shall operate as 'EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON' with full management autonomy.\n\nSECOND CLAUSE: SCIENTIFIC OBJECT. Econometric analysis of latent constructs and metallurgical waste upcycling. Patents will be under a common-use asset pool.\n\nTHIRD CLAUSE: BUFFERING. Grants will be deposited into the parent A.C. account as scientific allocations exempt from VAT."
        }
    }
# ==============================================================================
# PARTE 12 DE 20: AUDITORÍA DE BITÁCORA Y ACCESO RESTRINGIDO INSTITUTIONAL
# ==============================================================================
def registrar_descarga(modulo, archivo):
    """Inyecta de forma síncrona la estampa de tiempo de las descargas en la bitácora contable."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["historial_descargas"].append({
        "Fecha y Hora": now, "Módulo": modulo, "Archivo Descargado": archivo, "Estatus": "Éxito (Generado en Servidor)"
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
# PARTE 13 DE 20: COMPILADOR INDIVIDUAL DE REPORTES PDF (CON LOGO Y FIRMAS)
# ==============================================================================
def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto):
    """Compila estados contables en un formato PDF vanguardista libre de errores de tags HTML."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    color_primario = colors.HexColor("#1e4620")   # Verde Forestal JZPAC
    color_acento = colors.HexColor("#495057")     # Gris Ejecutivo
    
    estilo_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=13, fontName='Helvetica-Bold', textColor=color_primario, spaceAfter=2)
    estilo_sub = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=color_acento, spaceAfter=12)
    estilo_cuerpo = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=10, fontName='Helvetica', leading=15, textColor=colors.HexColor("#212529"), spaceAfter=14)
    estilo_firmas = ParagraphStyle('DocSign', parent=styles['Normal'], fontSize=8, fontName='Helvetica', alignment=1)
    
    story = []
    
    # --- CONSTRUCCIÓN GEOMÉTRICA SEGURA DEL ENCABEZADO ---
    from reportlab.platypus import Image as RLImage
    logo_flowable = ""
    try:
        logo_flowable = [RLImage("JZPACLOGOREDONDO.png", width=42, height=42)]
    except Exception:
        logo_flowable = [Paragraph("<b>🦅 JZPAC</b>", ParagraphStyle('Fb', fontSize=10, textColor=color_primario, alignment=2))]

    header_text = [
        [Paragraph(f"<b>{titulo_modulo.upper()}</b>", estilo_titulo), logo_flowable],
        [Paragraph("<b>JACOB ZUMAYA PRIANTI, A.C.</b> • Ecosistema de Economía Popular", estilo_sub), ""]
    ]
    
    header_table = Table(header_text, colWidths=[380.0, 100.0])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (1,0), (1,1)), 
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    
    divider_line = Table([[""]], colWidths=[480.0])
    divider_line.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, color_primario),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 2),
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
    
    # Cuadro de firmas triples libre de tags HTML conflictivos
    datos_firmas = [
        ["____________________________", "____________________________", "____________________________"],
        [Paragraph("<b>Agente Capacitador Central</b>", estilo_firmas), Paragraph("<b>Director de Subsistema</b>", estilo_firmas), Paragraph("<b>Delegación de Control SAT</b>", estilo_firmas)],
        [Paragraph("Jacob Zumaya Prianti, A.C.", estilo_firmas), Paragraph("Gobernanza de Célula de Barrio", estilo_firmas), Paragraph("Materialidad e Inclusión Fiscal", estilo_firmas)]
    ]
    tabla_firmas = Table(datos_firmas, colWidths=[155.0, 170.0, 155.0])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(tabla_firmas)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
# ==============================================================================
# PARTE 14 DE 20: COLUMNA IZQUIERDA - SIMULADORES FISCALES Y DE LOGÍSTICA DE RUTA
# ==============================================================================
    else:
        # Pestañas ordinarias de simulación macroeconómica barrial
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
# ==============================================================================
# PARTE 15 DE 20: COLUMNA IZQUIERDA - SIMULADORES DE RIESGOS Y TRÁNSITO DE FONDOS
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
# PARTE 16 DE 20: COLUMNA DE LA DERECHA - LOGOTIPO E IDENTIDAD INSTITUCIONAL
# ==============================================================================
with col_derecha_documental:
    # Contenedor gráfico corporativo con la denominación de la A.C.
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; margin-bottom: 12px; text-align: center;'>
        <h2 style='color: #1e4620; margin-top:0; font-size:15px; font-weight:bold; text-transform: uppercase; letter-spacing: 0.5px;'>
            JACOB ZUMAYA PRIANTI, A.C.
        </h2>
        <p style='color: #6c757d; font-size:11px; margin-bottom:10px;'>Ecosistema de Economía Popular Fronteriza</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        st.image("JZPACLOGOREDONDO.png", caption="Logotipo Oficial JZPAC", use_container_width=True)
    except Exception:
        st.caption("🦅 [Imagen: JZPACLOGOREDONDO.png Cargada en Repositorio]")
        
    st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
# ==============================================================================
# PARTE 17 DE 17 (NIVEL GLOBAL): CONTROL DE CONMUTACIÓN DE IDIOMA (ESPAÑOL / ENGLISH)
# ==============================================================================
    st.markdown("#### 🌐 Idioma de Descarga / Language Output")
    idioma_elegido = st.radio(
        "Selecciona el idioma para compilar tus PDFs y Words:",
        ["Español (ES)", "English (EN)"],
        horizontal=True,
        key="selector_idioma_global"
    )
    is_english = (idioma_elegido == "English (EN)")
    
    st.markdown("---")
    st.markdown("<b style='font-size:13px; color:#495057;'>🗂️ Almacén Documental Autónomo:</b>", unsafe_allow_html=True)
    
    lista_entidades = list(st.session_state["repositorio_institucional"].keys())
    seleccion_entidad = st.selectbox("🏢 1. Selecciona la Entidad / Subsistema:", ["-- Elige una Entidad --"] + lista_entidades)
# ==============================================================================
# PARTE 18 DE 20: COLUMNA DERECHA - DISPARADOR DE LIBROS COMPENDIOS EN APA 7
# ==============================================================================
    if seleccion_entidad != "-- Elige una Entidad --":
        st.markdown("#### 📘 Compilar Libro Unificado (APA 7)")
        st.caption("Encuaderna la totalidad de manuales y contratos en una sola monografía de un solo click.")
        
        dict_marcos_libro = st.session_state["repositorio_institucional"][seleccion_entidad]
        
        # Ejecución del compilador inyectando la bandera bilingüe de traducción
        pdf_libro_completo = generar_libro_apa7(seleccion_entidad, dict_marcos_libro, lang_en=is_english)
        
        label_btn_libro = "📥 Download Complete Compendium (PDF)" if is_english else "📥 Descargar Libro Compendio (PDF)"
        if st.download_button(label=label_btn_libro, data=pdf_libro_completo, file_name=f"Compendio_{seleccion_entidad.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True):
            registrar_descarga(seleccion_entidad, f"Compendio_{seleccion_entidad.replace(' ', '_')}.pdf")
            
        st.markdown("---")
# ==============================================================================
# PARTE 19 DE 20: COLUMNA DERECHA - VISOR INDIVIDUAL Y BOTONERA DE GOBERNANZA
# ==============================================================================
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
# ==============================================================================
# PARTE 20 DE 20: COLUMNA DERECHA - UPLOADING DE ARCHIVOS Y PIE DE MATRIZ A COLOR
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

st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0; font-size:14px;'>🟢 Nodo Central: JACOB ZUMAYA PRIANTI, A.C.</h4><p style='color: #1c7430; font-size: 12px;'><b>Estatus:</b> 0% IVA / Escudo 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 12px; border-radius: 6px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0; font-size:14px;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 12px;'><b>Impacto:</b> Capitaliza excedentes netos de fletes e intermediación libre de ISR.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0; font-size:14px;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 12px;'><b>Impacto:</b> Transforma primas comerciales de la S.A. en fondos de fomento.</p></div>", unsafe_allow_html=True)
