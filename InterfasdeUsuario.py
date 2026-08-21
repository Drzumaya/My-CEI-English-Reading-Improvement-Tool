import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado estable de PDFs en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
# ==============================================================================
# PARTE 2 DE 28: CONFIGURACIÓN INICIAL DEL LIENZO VISUAL DE LA PLATAFORMA
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - JACOB ZUMAYA PRIANTI, A.C.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar estados de sesión críticos para la gobernanza corporativa
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
# PARTE 3 DE 28: BASE DE DATOS ACTIVA DEL PADRÓN DE DIRECTORES ASOCIADOS
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
# PARTE 4 DE 28: MATRIZ DOCUMENTAL JZPAC - ASOCIACIÓN CIVIL MATRIZ (TOMOS 1-3)
# ==============================================================================
if "repositorio_institucional" not in st.session_state:
    st.session_state["repositorio_institucional"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL\n\nJACOB ZUMAYA PRIANTI, A.C. funciona como la sociedad de contención social y docencia central que coordina y ampara los flujos financieros de los subsistemas autónomos en Agua Prieta. Diseña los planes de capacitación técnica y los esquemas de retención de valor en la periferia urbana, operando como el holding social del circuito cerrado.",
            "Marco legal": "FUNDAMENTACIÓN JURÍDICA FISCAL (TÍTULO II LISR)\n\nTributa bajo el Régimen General de las Personas Morales. Blinda el 100% de la dispersión de fondos comunitarios mediante Nómina de Asimilados a Salarios (Art. 94 Fracc. V LISR), transformándolos en deducciones autorizadas perfectas. Sus ingresos por cuotas de recuperación y talleres de capacitación para el trabajo se declaran exentos del traslado del 16% de IVA por mandato expreso del Artículo 15 Fracciones IV y XII de la Ley del IVA.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS DE GOBERNANZA CENTRAL (MAP-AC-01)\n\n1. Recepción mensual de los retornos del 20% de primas desde la Agencia S.A. y aportaciones de la Cooperativa.\n2. Validación física y digital de las listas de asistencia de los talleres de barrio.\n3. Dispersión síncrona y timbrado de CFDI de asimilados a salarios para neutralizar la base gravable corporativa.",
# ==============================================================================
# PARTE 5 DE 28: MATRIZ DOCUMENTAL JZPAC - ASOCIACIÓN CIVIL MATRIZ (TOMOS 4-6)
# ==============================================================================
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RECURSOS HUMANOS Y CONTROL (MAC-AC-01)\n\nRegula las políticas de contratación de promotores barriales, las bitácoras de asignación de herramientas en comodato y los lineamientos de transparencia contable en cuentas de orden para auditorías externas del SAT.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS Y RIESGO SOCIOECONÓMICO (MTC-AC-01)\n\nMonitorea los índices de inflación en la franja fronteriza norte, las adecuaciones a las reglas misceláneas del SAT y el impacto de la paridad cambiaria peso-dólar en el poder adquisitivo real de los asociados en Agua Prieta.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EVALUACIÓN DE ADOPCIÓN DE PROGRAMAS SOCIALES\n\nVARIABLE LATENTE CENTRAL: 'Aceptación Institucional del Modelo de Economía Popular de JACOB ZUMAYA PRIANTI, A.C.'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Frecuencia con la que el asociado acude voluntariamente a las mesas de gobernanza central de la A.C.\n2. [X2] Nivel de confianza percibido en la transparencia del manejo de fondos del Título II corporativo.\n3. [X3] Disposición declarada para transitar de contratos informales en efectivo a Nómina de Asimilados.\n4. [X4] Grado de recomendación del programa de capacitación de la A.C. a otros microemprendedores del barrio.\n5. [X5] Percepción de mejora en la estabilidad de su negocio tras el cobro vía recibo estatutario.",
# ==============================================================================
# PARTE 6 DE 28: MATRIZ DOCUMENTAL JZPAC - ASOCIACIÓN CIVIL MATRIZ (TOMOS 7-8)
# ==============================================================================
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ADHESIÓN Y ASIMILACIÓN A SALARIOS (A.C. MATRIZ)\n\nCONTRATO que celebran por una parte JACOB ZUMAYA PRIANTI, A.C., y por la otra el Usuario Inscrito por propio derecho en su carácter de Director Asociado de Célula Barrial, al tenor de las siguientes cláusulas:\n\nPRIMERA: OBJETO. El Usuario acepta la designación técnica para coordinar los talleres de capacitación para el trabajo y fomento económico en su colonia asignada de Agua Prieta.\n\nSEGUNDA: RÉGIMEN FISCAL. El Usuario manifiesta su consentimiento expreso para someter sus honorarios de apoyo al régimen de Asimilados a Salarios (Art. 94 Fracc. V de la LISR), obligándose la A.C. a retener el impuesto correlativo y timbrar el CFDI de nómina para amparar deducciones autorizadas de Título II.\n\nTERCERA: EXENCIÓN DE IVA. Las partes acuerdan que las cuotas extraordinarias que recaude el Usuario de los talleres se consideran cuotas de miembros exentas de IVA (Art. 15-XII LIVA) y se integrarán de inmediato a la cuenta de orden de la Caja de Ahorro.",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [XXXX] | VOLUMEN: [XX]\nCONSTITUCIÓN DE ASOCIACIÓN CIVIL BAJO EL RÉGIMEN GENERAL (TÍTULO II LISR)\n\nEn la ciudad de Agua Prieta, Estado de Sonora, ante mí, Notario Público Número [X], comparecen los Asociados Fundadores para formalizar de manera estricta el ACTA CONSTITUTIVA de la persona moral JACOB ZUMAYA PRIANTI, A.C., la cual se regirá bajo las siguientes cláusulas formales:\n\nCLÁUSULA PRIMERA: DENOMINACIÓN, DOMICILIO Y DURACIÓN.\nLa organización se denominará 'JACOB ZUMAYA PRIANTI', seguida de las siglas 'A.C.'. Su domicilio legal definitivo se fija en Agua Prieta, Sonora, y su duración será por tiempo indefinido.\n\nCLÁUSULA SEGUNDA: OBJETO SOCIAL Y REMANENTES DISPONIBLES.\nEl objeto primordial consiste en impartir de forma gratuita y exenta de IVA (Art. 15 LIVA) capacitación para el trabajo, educación técnica, fomento de oficios y asesoría de microcréditos para la retención del valor fronterizo. Al operar bajo el Régimen General (Título II LISR), los excedentes o remanentes de operación no se distribuirán como dividendos capitalistas, sino que se capitalizarán en cuentas de orden para subsidiar activos del barrio o se dispersarán al 100% como erogaciones salariales asimiladas (Art. 94 LISR) a los Directores Asociados.\n\nCLÁUSULA TERCERA: PATRIMONIO SOCIAL AND ASAMBLEA CENTRAL.\nEl patrimonio de la A.C. se integrará por las cuotas ordinarias y extraordinarias de recuperación aportadas por sus Miembros Adherentes (Art. 15-XII LIVA), así como por las comisiones docentes y de fomento ingresadas desde sus subsistemas secundarios filiales. El órgano supremo es la Asamble General de Asociados, representada por el Agente Capacitador como Director General, dotado de Poder General Amplio para Pleitos, Cobranzas y Actos de Dominio."
        },
# ==============================================================================
# PARTE 7 DE 28: MATRIZ DOCUMENTAL JZPAC - COOPERATIVA DE LOGÍSTICA (TOMOS 1-3)
# ==============================================================================
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA OPERATIVO DE TRANSPORTE BARRIAL\n\nAsociación democrática de choferes, mecánicos y transportistas de base popular organizados de forma colectiva bajo el cobijo de JACOB ZUMAYA PRIANTI, A.C. Su finalidad es competir de forma eficiente en el mercado de fletes industriales B2B y última milla, absorbiendo la derrama económica indirecta provocada por el nearshoring en las maquiladoras de la aduana.",
            "Marco legal": "LEY GENERAL DE SOCIEDADES COOPERATIVAS (LGSC)\n\nSe constituye bajo la figura jurídica de Sociedad Cooperativa de Producción de Servicios de Responsabilidad Limitada de Capital Variable (S.C. de R.L. de C.V.). El marco legal mexicano ampara la separación total del patrimonio personal de los choferes frente a pasivos comerciales. Fiscalmente, está sujeta a la retención obligatoria del 4% de ISR sobre fletes terrestres facturados a personas morales.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS OPERATIVOS LOGÍSTICOS (MOP-SC-02)\n\n1. Asignación y optimización de rutas comerciales hacia los parques industriales de Agua Prieta.\n2. Auditoría física y satelital del Factor de Retorno Vacío (Deadhead Miles).\n3. Retención síncrona en el software del 6% bruto de cobro para el fondo de amortización contra fluctuaciones del precio del diésel.",
# ==============================================================================
# PARTE 8 DE 28: MATRIZ DOCUMENTAL JZPAC - COOPERATIVA DE LOGÍSTICA (TOMOS 4-6)
# ==============================================================================
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE FLOTILLA Y MANTENIMIENTO (MAF-SC-02)\n\nEstablece los roles de los Directores Asociados en la administración de talleres mecánicos comunitarios asignados, control de bitácoras de desgaste de neumáticos, asignación de viáticos logísticos fronterizos y aseguramiento de unidades.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS DE TRANSPORTE TRANSFRONTERIZO (MTC-SC-02)\n\nAnaliza los tiempos de espera y cuellos de botella en las aduanas, la fluctuación estacional de la producción automotriz y manufacturera de las maquiladoras ancla y el impacto de aranceles comerciales en el flujo de fletes.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA OPERATIVA DE LA LOGÍSTICA DE BARRIO\n\nVARIABLE LATENTE CENTRAL: 'Cultura de Optimización de Ruta en Choferes Cooperativistas de la Red JZPAC'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Índice de cumplimiento exacto de los horarios de recolección reportados en la aduana de Agua Prieta.\n2. [X2] Nivel de reducción voluntaria reportada en el Factor de Retorno Vacío (viajes con carga consolidada).\n3. [X3] Frecuencia de registro y uso correcto de la aplicación Streamlit para el reporte del Costo de Operación por Kilómetro (COK).\n4. [X4] Grado de apego a los lineamientos de mantenimiento preventivo y revisión de presión de neumáticos del camión.\n5. [X5] Proporción de fletes ejecutados sin registrar incidencias o penalizaciones por retraso con las maquiladoras ancla.\n6. [X6] Disposición del chofer para cooperar en cargas consolidadas compartidas con otros talleres barriales.",
# ==============================================================================
# PARTE 9 DE 28: MATRIZ DOCUMENTAL JZPAC - COOPERATIVA DE LOGÍSTICA (TOMOS 7-8)
# ==============================================================================
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO DE ADHESIÓN INDIVIDUAL DE SOCIO TRABAJADOR COOPERATIVISTA (S.C. LOGÍSTICA)\n\nCONTRATO de adhesión que celebran la Sociedad Cooperativa de Logística y Transporte de los Barrios, y por la otra el Usuario en su carácter de Socio Conductor, bajo las siguientes cláusulas:\n\nPRIMERA: ASOCIACIÓN COMUNITARIA. El Usuario aporta su trabajo personal y se adhiere formalmente a las Bases Constitutivas vigentes, bajo el régimen de Responsabilidad Limitada amparado por la Ley General de Sociedades Cooperativas (LGSC).\n\nSEGUNDA: RETENCIONES Y COK. El Socio acepta registrar cada viaje en la aplicación de control analítico Streamlit de la A.C., deduciendo el Costo de Operación por Kilómetro (COK), el Factor de Retorno Vacío, el 4% de retención de ISR y aportando de forma síncrona el 6% para el fondo de amortiguación de diésel fronterizo.\n\nTERCERA: EXCEDENTES. El Socio Conductor reconoce que los excedentes netos de fletes calculados en la plataforma se inyectarán de forma legal a la Caja de Ahorro común, teniendo derecho a retiros de rendimientos sociales según los acuerdos de la Asamblea General.",
            "Acta Constitutiva Notarial Oficial": "INSCRIPCIÓN REGISTRAL MERCANTIL | FOJA: [XXX]\nBASES CONSTITUTIVAS DE SOCIEDAD COOPERATIVA DE RESPONSABILIDAD LIMITADA (S.C. DE R.L.)\n\nEn la Ciudad de Agua Prieta, Sonora, se formaliza el Acta de Asamblea Constitutiva de la Sociedad Cooperativa que se organiza de conformidad con la Ley General de Sociedades Cooperativas (LGSC) y el Código Comercio de México:\n\nCLÁUSULA PRIMERA: RÉGIMEN, DENOMINACIÓN Y JURISDICCIÓN.\nLa sociedad se denominará 'COOPERATIVA DE LOGÍSTICA Y TRANSPORTE TRANSFRONTERIZO DE AGUA PRIETA', operando obligatoriamente con las siglas 'S.C. DE R.L. DE C.V.'. Su responsabilidad frente a terceros queda estrictamente LIMITADA al monto de los certificados de aportación de sus miembros, bajo el amparo patrimonial de JACOB ZUMAYA PRIANTI, A.C.\n\nCLÁUSULA SEGUNDA: OBJETO COMERCIAL Y CADENA DE VALOR B2B.\nEl objeto exclusivo consiste en prestar servicios integrales de transporte terrestre, carga pesada, distribución aduanal y fletes logísticos industriales B2B para las plantas maquiladoras de la zona norte del país. La sociedad se obliga a facturar conforme a las leyes fiscales mexicanas, aceptando la aplicación de la retención del 4% de ISR sobre fletes terrestres mandada por el SAT.\n\nCLÁUSULA TERCERA: CERTIFICADOS DE APORTACIÓN Y EXCEDENTES COOPERATIVOS.\nEl capital social se representa por certificados de aportación nominativos, indivisibles y de igual valor. Queda estrictamente establecido que al término de cada ejercicio contable mensual calibrado en el software Streamlit, se deducirá un 6% bruto de ingresos para blindar el fondo de reserva contra volatilidad de diésel y un 5% neto de excedentes que se inyectará de forma transparente a la cuenta de orden de la Asociación Civil central para sufragar el sostenimiento técnico del ecosistema."
        },
# ==============================================================================
# PARTE 10 DE 28: MATRIZ DOCUMENTAL JZPAC - AGENCIA DE MICROSEGUROS (TOMOS 1-3)
# ==============================================================================
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE CONTROL DE RIESGOS COMERCIAL\n\nEntidad financiera controlada y fiscalizada para blindar y proteger los activos mecánicos pesados de los talleres populares integrados. Mitiga vulnerabilidades por accidentes operacionales o fallecimiento de líderes comunitarios en Agua Prieta, absorbiendo el riesgo mediante un fondo técnico mutual.",
            "Marco legal": "LEY DE INSTITUCIONES DE SEGUROS Y DE FIANZAS (LISF)\n\nSociedad Anónima de Capital Variable regulada de forma estricta por la Comisión Nacional de Seguros y Fianzas (CNSF). Para mantener la legalidad contable del ecosistema, transfiere contractualmente el 20% de las primas brutas captadas a la A.C. matriz bajo el rubro deducible de Honorarios por Capacitación en Prevención de Riesgos.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS Y ATENCIÓN DE SINIESTROS (MAP-SA-03)\n\n1. Reporte técnico inmediato de avería mecánica, siniestro vial o accidente dentro de las colonias.\n2. Evaluación social expedita del riesgo y dictamen pericial por parte del Asociado Director técnico.\n3. Liquidación y pago directo de las reparaciones con cargo al fondo de reserva técnico depositado en la Caja.",
# ==============================================================================
# PARTE 11 DE 28: MATRIZ DOCUMENTAL JZPAC - AGENCIA DE MICROSEGUROS (TOMOS 4-6)
# ==============================================================================
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE RESERVAS TÉCNICAS Y RECAUDACIÓN (MAR-SA-03)\n\nRegula el proceso de cobranza mensual automatizada de las primas mediante la plataforma digital Streamlit y el resguardo seguro del capital de reserva técnico en instrumentos financieros de renta fija de bajo riesgo.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS ACTUARIALES EN MICROSEGUROS (MTC-SA-03)\n\nMide estadísticamente la tasa de siniestralidad de los talleres de barrio, los índices de renovación de pólizas solidarias y proyecta modelos de vulnerabilidad ante fallas mecánicas catastróficas en maquinaria pesada depreciada.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - PERCEPCIÓN DE SEGURIDAD PATRIMONIAL\n\nVARIABLE LATENTE CENTRAL: 'Aversión al Riesgo y Confianza en la Póliza Solidaria de la Red JACOB ZUMAYA PRIANTI, A.C.'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Puntualidad exacta en el pago de la prima mensual simulada en el Módulo 3 de la plataforma.\n2. [X2] Grado de conocimiento de los talleres sobre el alcance real de las coberturas de siniestralidad de maquinaria.\n3. [X3] Nivel de tranquilidad manifestada por el micro-empresario respecto a la continuidad de su negocio ante una falla mecánica.\n4. [X4] Frecuencia con la que el micro-taller reporta de forma preventiva riesgos de infraestructura al Asociado Director.\n5. [X5] Confianza declarada en la velocidad de respuesta del fondo de reserva de la A.C. ante accidentes viales o de taller.",
# ==============================================================================
# PARTE 12 DE 28: MATRIZ DOCUMENTAL JZPAC - AGENCIA DE MICROSEGUROS (TOMOS 7-8)
# ==============================================================================
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO COLECTIVO DE ADHESIÓN A LA PÓLIZA DE MICROSEGUROS FRONTERIZOS (S.A.)\n\nCONTRATO que celebran la Agencia de Protección Solidaria Fronteriza, S.A. de C.V., y por la otra el Usuario Inscrito en su carácter de Titular de Unidad Productiva Popular Asegurada, al tenor de las siguientes cláusulas:\n\nPRIMERA: COBERTURA INTEGRAL. El Usuario se adhiere a la póliza comunitaria colectiva para proteger sus activos mecánicos y herramientas de taller (soldadoras, tornos, cortadoras de cuero) contra averías técnicas graves, incendios o accidentes de operación en Agua Prieta.\n\nSEGUNDA: PRIMA SOCIAL Y RETORNO. El Asegurado se obliga a cubrir la prima mensual calculada dinámicamente en el Módulo 3. Reconoce que el 20% de dicha recaudación es transferido a la A.C. matriz por concepto de Honorarios de Capacitación en Prevención de Siniestros, libre de IVA comercial.\n\nTERCERA: RECLAMACIÓN JUSTA. En caso de ocurrencia de un siniestro, el Usuario se compromete a no iniciar litigios mercantiles ordinarios, sometiéndose al Manual de Procedimientos interno de la A.C., el cual dictaminará el pago y liquidación de daños con cargo al fondo de reserva técnico de forma inmediata.",
            "Acta Constitutiva Notarial Oficial": "ESCRITURA PÚBLICA NÚMERO: [YYYY] | VOLUMEN: [XXX]\nCONSTITUCIÓN DE SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE (RAMO RIESGOS CNSF)\n\nEn la Ciudad de Agua Prieta, Estado de Sonora, ante mí, Titular de la Notaría Pública Asociada, se formaliza la constitución de una SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE que se regirá bajo la Ley General de Sociedades Mercantiles (LGSM) y la Ley de Instituciones de Seguros y de Fianzas (LISF):\n\nCLÁUSULA PRIMERA: DENOMINACIÓN, DURACIÓN Y OBJETO REGULADO.\nLa denominación corporativa oficial será 'AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA', seguida de las siglas 'S.A. DE C.V.'. Su objeto exclusivo consiste en actuar como Agente de Seguros Persona Moral regulado por la CNSF, intermediando pólizas de microseguros colectivos de vida, accidentes de trabajo y daños estructurales mecánicos, bajo el auspicio de JACOB ZUMAYA PRIANTI, A.C.\n\nCLÁUSULA SEGUNDA: CAPITAL SOCIAL Y DOMINIO DE LA ASOCIACIÓN CIVIL MATRIZ.\nEl capital social es variable, fijándose un monto mínimo obligatorio de capitalización de $50,000.00 MXN totalmente suscrito y pagado. Para blindar el patrimonio comunitario e impedir desvíos capitalistas privados, la Asociación Civil central del ecosistema retiene la titularidad del 99% de las acciones Clase 'A', teniendo el voto mayoritario absoluto en cualquier asamblea.\n\nCLÁUSULA TERCERA: GOBERNANZA, DEDUCCIONES Y CONTRATO DE RETORNO CORRETAJE.\nLa administración estará a cargo de un Administrador Único designado de forma directa por la Asamblea de la A.C. (Asociado Director). Para salvaguardar la deducibilidad de egresos mercantiles y fondeo de la Caja de Ahorro, la sociedad se obliga por estipulación estatutaria invulnerable a transferir el 20% de las primas brutas capturadas mensuales a la A.C. matriz bajo la figura de Honorarios de Corretaje Social y Docencia en Prevención de Accidentes."
        },
# ==============================================================================
# PARTE 13 DE 28: MATRIZ DOCUMENTAL JZPAC - EQUIPO CIENTÍFICO APSON (TOMOS 1-3)
# ==============================================================================
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE INVESTIGACIÓN, DESARROLLO E INNOVACIÓN (I+D)\n\nCélula avanzada de transferencia tecnológica encargada de realizar estudios econométricos de densidad microeconómica, análisis de ciclo de vida metalúrgico para el reciclaje (Upcycling) de las mermas industriales desechadas por las maquiladoras fronterizas y optimización de los algoritmos predictivos de crédito social comunitarios.",
            "Marco legal": "LEY GENERAL DE HUMANIDADES, CIENCIAS, TECNOLOGÍAS E INNOVACIÓN\n\nOpera bajo el amparo de la Cláusula Estatutaria de Autonomía de los Asociados Directores de JACOB ZUMAYA PRIANTI, A.C. Los fondos y recursos captados para la investigación científica a través de aportaciones de fomento se consideran estímulos exentos del traslado de IVA conforme al marco fiscal de la Federación.",
            "Manual de procedimientos": "MANUAL DE PROCEDIMIENTOS EN RECOLECCIÓN Y PROCESAMIENTO (MAP-ID-04)\n\n1. Recolección protocolizada de muestras de mermas industriales (cueros, maderas, polímeros) en los parques maquiladores de Agua Prieta.\n2. Pruebas de fatiga y resistencia de materiales en los laboratorios comunitarios.\n3. Transferencia inmediata de patentes sociales de costo cero a los talleres productivos barriales.",
# ==============================================================================
# PARTE 14 DE 28: MATRIZ DOCUMENTAL JZPAC - EQUIPO CIENTÍFICO APSON (TOMOS 4-6)
# ==============================================================================
            "Manual administrativo": "MANUAL ADMINISTRATIVO DE PROYECTOS Y FIDEICOMISOS CIENTÍFICOS (MAC-ID-04)\n\nCoordina la gobernanza presupuestal de los laboratorios populares, la asignación de becas de investigación y estímulos económicos a estudiantes universitarios de Agua Prieta y el inventario técnico de reactivos de análisis.",
            "Manual de Tendencias criticas": "MANUAL DE TENDENCIAS CRÍTICAS EN INNOVACIÓN INDUSTRIAL (MTC-ID-04)\n\nMapea las tecnologías emergentes de manufactura esbelta automatizada, el volumen y tipología mensual de desperdicios industriales utilizables por sector y las proyecciones geo-económicas de crecimiento del nearshoring real.",
            "Manual de Variables latentes con items observables": "MANUAL DE VARIABLES LATENTES - EFICIENCIA DE LA TRANSFERENCIA TECNOLÓGICA I+D\n\nVARIABLE LATENTE CENTRAL: 'Capacidad de Absorción del Saber Científico en Talleres de Barrio del Ecosistema JZPAC'\n\nÍTEMS OBSERVABLES DE CAMPO (Evaluación Escala Likert 1-5):\n1. [X1] Tasa de adopción de manuales Lean-Barrio y diagramas de flujo técnicos dentro de los procesos diarios del taller.\n2. [X2] Cantidad de mermas industriales recolectadas (cuero, madera) efectivamente transformadas en productos comerciales de alta gama.\n3. [X3] Frecuencia de asistencia de los artesanos y operarios populares a las células de co-diseño del Equipo Científico.\n4. [X4] Reducción porcentual de costos de materia prima lograda por el taller al sustituir insumos comerciales por materiales reciclados de la maquila.\n5. [X5] Nivel de comprensión técnica manifestada por el micro-productor sobre el uso y cuidado de la maquinaria pesada financiada.\n6. [X6] Cantidad de nuevos prototipos funcionales o innovaciones locales de producto generadas de forma autónoma por la comunidad.\n7. [X7] Incremento reportado en la calidad final de la proveeduría indirecta entregada a las plantas maquiladoras transnacionales.",
# ==============================================================================
# PARTE 15 DE 28: MATRIZ DOCUMENTAL JZPAC - EQUIPO CIENTÍFICO APSON (TOMOS 7-8)
# ==============================================================================
            "Contrato de Incorporación y Adhesión Individual": "CONTRATO INDIVIDUAL DE ASIGNACIÓN CIENTÍFICA Y PROPIEDAD INTELECTUAL SOCIAL (ID-APSON)\n\nCONTRATO que celebran la Asociación Civil e Investigación Científica APSON, y por la otra el Usuario en su carácter de Investigador o Técnico de Laboratorio Comunitario, al tenor de las siguientes cláusulas:\n\nPRIMERA: OBJETO DE TRANSFERENCIA. El Investigador se compromete a ejecutar análisis de densidad económica, estudios metalúrgicos de mermas industriales de maquiladoras y modelado de variables latentes en Agua Prieta.\n\nSEGUNDA: PATENTES SOCIALES Y CONFIDENCIALIDAD. El Usuario acepta que toda propiedad intelectual, diseño de upcycling o código computacional desarrollado en las células de I+D pertenece al patrimonio común de la A.C. Queda prohibido el acaparamiento privado, licenciándose a tasa cero para el beneficio de los talleres populares.\n\nTERCERA: CONDICIÓN DE REMUNERACIÓN. Las retribuciones se canalizarán a través del fondo de fideicomisos científicos autónomos administrado por la Caja de Ahorro de la A.C., justificando la materialidad docente libre de IVA ante las autoridades hacendarias.",
            "Acta Constitutiva Notarial Oficial": "PROTOCOLO NOTARIAL DE NOMBRAMIENTO Y APERTURA DE CONSEJO DE INVESTIGACIÓN CIENTÍFICA\n\nEn la Ciudad de Agua Prieta, Sonora, ante la fe del Notario Público adscrito al protocolo estatal, se formaliza el Acta de Establecimiento y Gobierno de la célula científica con base en la Ley General de Ciencias y el Código Civil vigente:\n\nCLÁUSULA PRIMERA: AUTONOMÍA OPERATIVA Y DENOMINACIÓN DE NODO.\nEl subsistema científico operará bajo el nombre de 'EQUIPO DE INVESTIGACIÓN CIENTÍFICA APSON'. Goza de una Cláusula de Autonomía de Gestión delegada por la A.C. nodriza, permitiéndole al Asociado Director celebrar minutas, convenios y acuerdos técnicos con universidades y parques industriales sin requerir autorizaciones burocráticas previas.\n\nCLÁUSULA SEGUNDA: FINES CIENTÍFICOS Y MODELADO PATRIMONIAL SOCIAL.\nEl objeto primordial consiste en ejecutar investigación econométrica de variables latentes, mapear densidades de mermas industriales y realizar ingeniería inversa metalmecánica para el diseño de productos de reciclaje. Toda patente, secreto industrial o marca colectiva resultante se registrará ante el IMPI a nombre de la Asociación Civil matriz JACOB ZUMAYA PRIANTI, A.C., quedando etiquetada bajo un fideicomiso de 'Uso Social Común' perpetuo a tasa cero para beneficio de los barrios de Agua Prieta.\n\nCLÁUSULA TERCERA: GOBERNANZA PRESUPUESTAL Y CUENTAS DE ORDEN EN CAJA.\nLa dirección científica recaerá en el Asociado Director electo por el consejo. Los fondos de fomento económico o becas captadas se depositarán directamente en la cuenta de orden de la Caja de Ahorro de la A.C., amparando la completa materialidad de las investigaciones para fines científicos exentos de IVA, prohibiéndose el uso especulativo o financiero mercantil ajeno a la economía popular."
        }
    }
# ==============================================================================
# PARTE 16 DE 28: FUNCIONES COMPLEMENTARIAS DE LOG Y AUDITORÍA CONTABLE CENTRAL
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
# ==============================================================================
# PARTE 17 DE 28: PANTALLA DE ACCESO RESTRINGIDO E INTERRUPCIÓN PREVENTIVA JZPAC
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
# PARTE 18 DE 28: MOTOR DE COMPILACIÓN VANGUARDISTA CORREGIDO (PDF INDIVIDUAL)
# ==============================================================================
def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto, lang_en=False):
    """Compila estados contables en un formato PDF de vanguardia con logotipo y firmas sin tags conflictivos."""
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
    
    # --- CONSTRUCCIÓN SEGURA DEL ENCABEZADO ASIMÉTRICO ---
    from reportlab.platypus import Image as RLImage
    logo_flowable = ""
    try:
        logo_flowable = [RLImage("JZPACLOGOREDONDO.png", width=42, height=42)]
    except Exception:
        logo_flowable = [Paragraph("<b>🦅 JZPAC</b>", ParagraphStyle('Fb', fontSize=10, textColor=color_primario, alignment=2))]

    sub_lbl = "<b>JACOB ZUMAYA PRIANTI, A.C.</b> • Popular Economy Ecosystem AP-AC" if lang_en else "<b>JACOB ZUMAYA PRIANTI, A.C.</b> • Ecosistema de Economía Popular AP-AC"
    header_text = [
        [Paragraph(f"<b>{titulo_modulo.upper()}</b>", estilo_titulo), logo_flowable],
        [Paragraph(sub_lbl, estilo_sub), ""]
    ]
    
    header_table = Table(header_text, colWidths=[380.0, 100.0])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (1,0), (1,1)), 
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
    
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    story.append(Spacer(1, 8))
    
    # Matriz con colWidths explícito
    tabla_pdf = Table(datos_tabla, colWidths=[240.0, 240.0])
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), color_primario), ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(tabla_pdf)
    story.append(Spacer(1, 30))
    
    # --- CONSTRUCCIÓN SEGURA DEL CUADRO DE TRIPLES FIRMAS (REPARADO SIN <BR> CONFLICTIVOS) ---
    lbl_f1 = "<b>Central Capacitator Agent</b>" if lang_en else "<b>Agente Capacitador Central</b>"
    lbl_f2 = "<b>Subsystem Director</b>" if lang_en else "<b>Director de Subsistema</b>"
    lbl_f3 = "<b>SAT Control Delegation</b>" if lang_en else "<b>Delegación de Control SAT</b>"
    lbl_m1 = "Jacob Zumaya Prianti, A.C."
    lbl_m2 = "Neighborhood Cell Governance" if lang_en else "Gobernanza de Célula de Barrio"
    lbl_m3 = "Materiality & Fiscal Inclusion" if lang_en else "Materialidad e Inclusión Fiscal"
    
    datos_firmas = [
        ["____________________________", "____________________________", "____________________________"],
        [Paragraph(lbl_f1, estilo_firmas), Paragraph(lbl_f2, estilo_firmas), Paragraph(lbl_f3, estilo_firmas)],
        [Paragraph(lbl_m1, estilo_firmas), Paragraph(lbl_m2, estilo_firmas), Paragraph(lbl_m3, estilo_firmas)]
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
# PARTE 19 DE 28: CANVAS DE PORTADA COLOR FORESTAL Y PAGINACIÓN EJECUTIVA APA 7
# ==============================================================================
class CanvasLibroVanguardia(io.BytesIO.__class__):
    def __init__(self, *args, **kwargs):
        pass

def dibujar_decoracion_libro(canvas, doc):
    """Subrutina que inyecta la portada color forestal y la paginación secuencial en esquina superior."""
    canvas.saveState()
    color_primario = colors.HexColor("#1e4620")
    
    # PÁGINA 1: Dibujar el lienzo de fondo de color institucional para la portada de vanguardia
    if doc.page == 1:
        canvas.setFillColor(color_primario)
        canvas.rect(0, 0, 612, 792, fill=True, stroke=False)
        # Filete de acento ejecutivo color oro mate blanco lateral
        canvas.setFillColor(colors.HexColor("#f8f9fa"))
        canvas.rect(30, 0, 15, 792, fill=True, stroke=False)
    else:
        # PÁGINAS SIGUIENTES: Inyectar numeración formal en la esquina superior derecha (Estilo APA 7)
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor("#495057"))
        canvas.drawRightString(540, 738, f"{doc.page}")
        
        # Mini pie de página institucional de control cruzado
        canvas.drawString(72, 45, "Jacob Zumaya Prianti, A.C. — Ecosistema Fronterizo de Agua Prieta, Sonora.")
        
    canvas.restoreState()
# ==============================================================================
# PARTE 20 DE 28: ENCUADERNADOR MAESTRO DE COMPENDIOS BILINGÜES EN APA 7
# ==============================================================================
def generar_libro_apa7(nombre_entidad, diccionario_marcos, lang_en=False):
    """Compila y encuaderna los 7 manuales y contratos en un libro APA 7 bilingüe con portada a color e índice."""
    buffer_libro = io.BytesIO()
    doc = SimpleDocTemplate(buffer_libro, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    color_corporativo = colors.white if lang_en else colors.white # El texto de portada va en blanco sobre el fondo forestal
    color_texto_interno = colors.HexColor("#212529")
    
    # Diccionario transaccional de equivalencias bilingües en caliente
    traducciones_apa = {
        "titulo_compendio": "INTEGRATED CORPORATIVE COMPENDIUM OF AUTONOMOUS SUBSYSTEMS" if lang_en else "COMPENDIO INSTITUCIONAL INTEGRAL DE CONTROL VINCULADO",
        "linea_inv": "Research Line: Endogenous Growth & Border Value Retention" if lang_en else "Línea de Investigación: Crecimiento Endógeno y Retención de Valor Fronterizo",
        "autor_corp": "Corporate Author: Central Board JZPAC — Capacitator Agent" if lang_en else "Autor Corporativo: Consejo Directivo Central JZPAC — Agente Capacitador",
        "jurisdiccion": "Jurisdiction: Agua Prieta, Sonora, Mexico" if lang_en else "Jurisdicción de la Materia: Agua Prieta, Sonora, México",
        "fecha_lbl": "Certification Date:" if lang_en else "Fecha de Certificación y Cierre:",
        "nota_pie": "Executive Monograph for the Materiality Validation of the Distributable Remnant under LISR Title II" if lang_en else "Monografía Ejecutiva de Organización interna para Validación del Remanente Distribuible conforme al Título II",
        "indice_title": "GENERAL TABLE OF CONTENTS" if lang_en else "ÍNDICE GENERAL DE CAPÍTULOS",
        "cap_lbl": "Chapter" if lang_en else "Capítulo",
        "ver_sec": "[See Section]" if lang_en else "[Ver Sección]"
    }
# ==============================================================================
# PARTE 21 DE 28: CONFIGURACIÓN DE TIPOGRAFÍAS APA 7 Y FRONTISPICIO DE PORTADA
# ==============================================================================
    estilo_portada_matriz = ParagraphStyle('CoverAC', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor("#d4edda"), alignment=1, spaceAfter=20)
    estilo_portada_titulo = ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=color_corporativo, alignment=1, spaceAfter=15)
    estilo_portada_meta = ParagraphStyle('CoverMeta', fontName='Helvetica', fontSize=10, leading=16, textColor=colors.HexColor("#e9ecef"), alignment=1, spaceAfter=10)
    
    estilo_apa_h1 = ParagraphStyle('APAH1', fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.black, alignment=1, spaceBefore=24, spaceAfter=12)
    estilo_apa_h2 = ParagraphStyle('APAH2', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.black, alignment=0, spaceBefore=16, spaceAfter=6)
    estilo_apa_parrafo = ParagraphStyle('APABody', fontName='Helvetica', fontSize=11, leading=22, textColor=color_texto_interno, spaceAfter=14, firstLineIndent=36)
    estilo_indice = ParagraphStyle('DocIndex', fontName='Helvetica', fontSize=10, textColor=colors.black, spaceAfter=8)
    
    story = []
    story.append(Spacer(1, 40))
    
    # Inyección Controlada del Logotipo en el ala superior de la portada forestal
    from reportlab.platypus import Image as RLImage
    try:
        story.append(RLImage("JZPACLOGOREDONDO.png", width=65, height=65))
        story.append(Spacer(1, 15))
    except Exception:
        story.append(Paragraph("<b>🦅 JZPAC</b>", ParagraphStyle('Pld', fontName='Helvetica-Bold', fontSize=20, textColor=colors.white, alignment=1)))
        story.append(Spacer(1, 15))
        
    story.append(Paragraph("<b>JACOB ZUMAYA PRIANTI, A.C.</b>", estilo_portada_matriz))
    story.append(Paragraph(f"<b>{traducciones_apa['titulo_compendio']}</b>", estilo_portada_titulo))
    story.append(Paragraph(f"<b>{nombre_entidad.upper()}</b>", ParagraphStyle('SubC', parent=estilo_portada_titulo, fontSize=14, textColor=colors.white)))
    story.append(Spacer(1, 40))
    story.append(Paragraph(f"{traducciones_apa['linea_inv']}", estilo_portada_meta))
    story.append(Paragraph(f"{traducciones_apa['autor_corp']}", estilo_portada_meta))
    story.append(Paragraph(f"{traducciones_apa['jurisdiccion']}", estilo_portada_meta))
    
    fecha_str = datetime.now().strftime("%B %d, %Y") if lang_en else datetime.now().strftime("%d de %B de %Y")
    story.append(Paragraph(f"<b>{traducciones_apa['fecha_lbl']}</b> {fecha_str}", estilo_portada_meta))
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"<i>{traducciones_apa['nota_pie']}</i>", estilo_portada_meta))
    
    story.append(PageBreak())
# ==============================================================================
# PARTE 22 DE 28: COMPILACIÓN DEL ÍNDICE GENERAL Y DETONACIÓN DEL CONSTRUCTOR
# ==============================================================================
    # RENDERIZADO DEL ÍNDICE ACADÉMICO CON RELACIÓN DE PUNTOS
    story.append(Paragraph(f"<b>{traducciones_apa['indice_title']}</b>", estilo_apa_h1))
    story.append(Spacer(1, 15))
    
    num_capitulo = 1
    for titulo_manual in diccionario_marcos.keys():
        linea_puntos = ". " * 30
        renglon_indice = f"<b>{traducciones_apa['cap_lbl']} {num_capitulo}:</b> {titulo_manual} {linea_puntos} {traducciones_apa['ver_sec']}"
        story.append(Paragraph(renglon_indice, estilo_indice))
        num_capitulo += 1
        
    story.append(PageBreak())
    
    # Despliegue de los Tomos de Manuales Internos
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
        
    # Construcción final del documento amarrando los eventos del canvas de la portada y paginación
    doc.build(story, onFirstPage=dibujar_decoracion_libro, onLaterPages=dibujar_decoracion_libro)
    buffer_libro.seek(0)
    return buffer_libro
# ==============================================================================
# PARTE 23 DE 28: CONTROLES DEL SIDEBAR JZPAC Y PARTICIÓN ARQUITECTÓNICA MAESTRA
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

# SOLUCIÓN DEFINITIVA AL NAMEERROR: Inicialización obligatoria de las columnas antes de su invocación lineal
col_izquierda_matriz, col_derecha_documental = st.columns([0.70, 0.30])

num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_calculado = 0.0
# ==============================================================================
# PARTE 24 DE 28: COLUMNA DERECHA - SELECTOR BILINGÜE Y SELECTBOX DE ENTIDAD
# ==============================================================================
with col_derecha_documental:
    # 1. Selector de conmutación de lenguajes colocado en la parte alta del panel derecho
    st.markdown("#### 🌐 Idioma de Descarga / Language Output")
    idioma_elegido = st.radio(
        "Selecciona el idioma para compilar tus PDFs y Words:",
        ["Español (ES)", "English (EN)"],
        horizontal=True,
        key="selector_idioma_global"
    )
    
    # Declaración inmediata de la variable para evitar NameErrors en cascada
    is_english = (idioma_elegido == "English (EN)")
    
    st.markdown("---")
    st.markdown("<b style='font-size:13px; color:#495057;'>🗂️ Almacén Documental Autónomo:</b>", unsafe_allow_html=True)
    
    # CORRECCIÓN MAESTRA: Se declara y asigna formalmente la variable en memoria de forma lineal
    lista_entidades = list(st.session_state["repositorio_institucional"].keys())
    seleccion_entidad = st.selectbox(
        "🏢 1. Selecciona la Entidad / Subsistema:", 
        ["-- Elige una Entidad --"] + lista_entidades
    )

# ==============================================================================
# PARTE 25 DE 28: COLUMNA DERECHA - DISPARADOR DE LIBROS COMPENDIOS EN APA 7
# ==============================================================================
    # Ahora la condición es 100% segura porque 'seleccion_entidad' ya existe en el paso anterior
    if seleccion_entidad != "-- Elige una Entidad --":
        st.markdown("#### 📘 Compilar Libro Unificado (APA 7)")
        st.caption("Encuaderna la totalidad de manuales, formatos y contratos con Índice y Paginación en un solo click.")
        
        dict_marcos_libro = st.session_state["repositorio_institucional"][seleccion_entidad]
        
        # Inyección de la variable bilingüe evaluada en la Parte 24 al motor de ReportLab
        pdf_libro_completo = generar_libro_apa7(seleccion_entidad, dict_marcos_libro, lang_en=is_english)
        
        label_btn_libro = "📥 Download Complete Compendium (PDF)" if is_english else "📥 Descargar Libro Compendio (PDF)"
        if st.download_button(label=label_btn_libro, data=pdf_libro_completo, file_name=f"Compendio_{seleccion_entidad.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True):
            registrar_descarga(seleccion_entidad, f"Compendio_{seleccion_entidad.replace(' ', '_')}.pdf")
            
        st.markdown("---")
# ==============================================================================
# PARTE 26 DE 28: COLUMNA DERECHA - VISOR INDIVIDUAL Y BOTONERA DE GOBERNANZA
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
# PARTE 27 DE 28: COLUMNA DERECHA - GESTOR DE CARGA RECONVERTIDO CON AUTO-INYECCIÓN
# ==============================================================================
    st.markdown("---")
    label_upload = "📥 Upload Complementary Deeds (.txt)" if is_english else "📥 Uploading de Nuevas Actas (.txt)"
    archivo_cargado = st.file_uploader(label_upload, type=["txt"])
    
    if archivo_cargado is not None:
        nombre_archivo_crudo = archivo_cargado.name.replace(".txt", "")
        if nombre_archivo_crudo not in st.session_state["repositorio_institucional"]:
            try:
                contenido_texto = archivo_cargado.read().decode("utf-8", errors="ignore")
                
                # Auto-inyección obligatoria de las 8 carpetas operativas de la organización
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
                st.error("Error de decodificación o indexación del archivo txt.")
# ==============================================================================
# PARTE 28 DE 28: PIE DE PÁGINA - INFOGRAFÍA DE LA MATRIZ DEL VÍNCOLO FINANCIERO
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
        <p style='color: #9e7e1a; font-size: 12px; margin-bottom:0;'><b>Vínculo CNSF:</b> Intermediario de Pólizas Colectivas de Maquinaria.<br><b>Impacto:</b> Transforma utilidades de la S.A. en fondos de fomento social mediante Corretaje Social Docente.</p>
    </div>
    """, unsafe_allow_html=True)
