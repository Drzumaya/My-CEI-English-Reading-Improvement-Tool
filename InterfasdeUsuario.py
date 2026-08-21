import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado estable de PDFs en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# PARTE 1 DE 3: CONFIGURACIÓN, SEGURIDAD E INICIALIZACIÓN DE LA MATRIZ DOCUMENTAL
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - Agua Prieta",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# MATRIZ JURÍDICO-OPERATIVA DE DOS NIVELES (Inicialización en session_state para permitir EDICIÓN)
if "repositorio_institucional" not in st.session_state:
    st.session_state["repositorio_institucional"] = {
        "1. Asociación Civil Matriz (A.C.)": {
            "Marco conceptual y descriptivo": "ORGANIZACIÓN MATRIZ Y DE CONTENCIÓN SOCIAL\n\nFunciona como la sociedad controladora social (Holding) que coordina los subsistemas autónomos en Agua Prieta. Diseña los planes de capacitación para el trabajo e inclusión financiera de la periferia urbana.",
            "Marco legal": "FUNDAMENTACIÓN FISCAL TÍTULO II LISR\n\nTributa en Régimen General corporativo (30% ISR). Blinda sus egresos comunitarios al 100% como deducciones mediante Nómina Asimilada (Art. 94 LISR). Exenta de trasladar el 16% de IVA en educación y cuotas extraordinarias según el Art. 15 Fracc. IV y XII de la LIVA.",
            "Manual de procedimientos": "MANUAL DE GOBERNANZA CENTRAL (MGC-01)\n\n1. Recepción de comisiones de la S.A. y aportaciones cooperativas.\n2. Validación de listas de asistencia de talleres.\n3. Dispersión mensual y timbrado de CFDI de asimilados a salarios."
        },
        "2. Cooperativa de Logística (S.C.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA OPERATIVO DE TRANSPORTE BARRIAL\n\nAsociación de choferes y transportistas de base popular organizados para competir en el mercado de fletes industriales B2B y última milla, absorbiendo la demanda indirecta del nearshoring maquilador.",
            "Marco legal": "LEY GENERAL DE SOCIEDADES COOPERATIVAS (LGSC)\n\nSociedad Cooperativa de Producción de Servicios de Responsabilidad Limitada (S.C. de R.L. de C.V.). Las plantas maquiladoras contratantes efectúan de forma obligatoria la retención del 4% de ISR sobre fletes terrestres.",
            "Manual de procedimientos": "MANUAL DE OPERACIONES LOGÍSTICAS (MOL-02)\n\n1. Asignación de rutas comerciales en Agua Prieta.\n2. Auditoría física del Factor de Retorno Vacío (Deadhead).\n3. Retención automática del 6% para el fondo de amortiguación de diésel."
        },
        "3. Agencia de Microseguros (S.A.)": {
            "Marco conceptual y descriptivo": "SUBSISTEMA DE CONTROL DE RIESGOS COMERCIAL\n\nEntidad financiera diseñada para proteger los activos mecánicos de los talleres populares y mitigar vulnerabilidades por accidentes de trabajo o fallecimiento de líderes comunitarios.",
            "Marco legal": "LEY DE INSTITUCIONES DE SEGUROS Y DE FIANZAS (LISF)\n\nSociedad Anónima regulada por la CNSF. Transfiere legalmente el 20% de las primas a la A.C. mediante contratos de Corretaje Social y capacitación en prevención de accidentes laborales.",
            "Manual de procedimientos": "MANUAL DE ATENCIÓN DE SINIESTROS (MAS-03)\n\n1. Reporte técnico de avería mecánica o accidente en las colonias.\n2. Evaluación social del riesgo y dictamen del Asociado Director.\n3. Liquidación inmediata de la reparación con cargo al fondo de reserva."
        },
        "4. Equipo de Investigación Científica APSON": {
            "Marco conceptual y descriptivo": "NUEVO BRAZO DE INVESTIGACIÓN, DESARROLLO E INNOVACIÓN (I+D)\n\nCélula científica encargada de realizar estudios de densidad económica, análisis metalúrgicos para el reciclaje (Upcycling) de las mermas de las maquiladoras y optimización de modelos predictivos de crédito social.",
            "Marco legal": "LEY GENERAL DE HUMANIDADES, CIENCIAS, TECNOLOGÍAS E INNOVACIÓN\n\nOpera bajo el amparo de la Cláusula Estatutaria de Autonomía de los Asociados Directores. Los fondos de investigación científica captados de fideicomisos públicos o privados se consideran aportaciones de fomento exentas de IVA.",
            "Manual de procedimientos": "MANUAL DE TRANSFERENCIA TECNOLÓGICA (MIT-04)\n\n1. Recolección de muestras de mermas industriales (cueros, maderas, polímeros) en los parques industriales de Agua Prieta.\n2. Pruebas de resistencia y diseño industrial en laboratorios comunitarios.\n3. Transferencia de patentes sociales de costo cero a los talleres de barrio."
        }
    }

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
        st.caption("Asociación Civil en Régimen General (Título II LISR) • Agua Prieta, Sonora")
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

def registrar_descarga(modulo, archivo):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["historial_descargas"].append({
        "Fecha y Hora": now, "Módulo": modulo, "Archivo Descargado": archivo, "Estatus": "Éxito (Generado en Servidor)"
    })

def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    color_primario = colors.HexColor("#1e4620")
    
    estilo_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, textColor=color_primario, spaceAfter=12)
    estilo_sub = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, textColor=colors.gray, spaceAfter=12)
    estilo_cuerpo = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=12)
    
    story = []
    story.append(Paragraph(f"<b>{titulo_modulo}</b>", estilo_titulo))
    story.append(Paragraph("Ecosistema de Economía Popular AP-AC | Validación Documental", estilo_sub))
    story.append(Spacer(1, 10))
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    story.append(Spacer(1, 15))
    
    tabla_pdf = Table(datos_tabla, colWidths=)
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

st.sidebar.header("📋 Operaciones")
if st.sidebar.button("❌ Cerrar Sesión (Logout)", use_container_width=True, type="primary"):
    logout()
presupuesto_total = st.sidebar.number_input("Bolsa Económica Mensual Operativa (MXN)", min_value=10000, value=250000, step=10000)
# ==============================================================================
# PARTE 2 DE 3: COLUMNA DE LA IZQUIERDA - SIMULADORES Y VENTANA EDITABLE FLOTANTE
# ==============================================================================
col_izquierda_matriz, col_derecha_documental = st.columns([0.70, 0.30])

num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_calculado = 0.0

with col_izquierda_matriz:
    if st.session_state["ver_visor_legal"]:
        ent = st.session_state["entidad_seleccionada"]
        tdoc = st.session_state["tipo_doc_seleccionado"]
        
        st.info(f"📁 Ventana de Trabajo Activa: {ent} ➔ {tdoc}")
        st.markdown("---")
        
        # Carga el borrador editable desde la matriz anidada de la sesión
        texto_editable_actual = st.text_area(
            label="Editor Oficial de Cláusulas e Instructivos (Cambios en Caliente):",
            value=st.session_state["repositorio_institucional"][ent][tdoc],
            height=380
        )
        
        # FILA COMPACTA DE MANDATOS Y BOTONES
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("💾 Guardar Ajustes", use_container_width=True):
                st.session_state["repositorio_institucional"][ent][tdoc] = texto_editable_actual
                st.success("✓ Cambios guardados.")
        with b2:
            tabla_legal_dummy = [["Validación de Consistencia", "Aprobado por el Consejo"], ["Fecha de Auditoría", "2026-08-20"], ["Estatus Regulatorio", "Vigente Exento"]]
            pdf_legal = generar_informe_pdf(f"{ent} - {tdoc}", tabla_legal_dummy, texto_editable_actual)
            if st.download_button(label="📥 Descargar PDF", data=pdf_legal, file_name=f"{tdoc.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True):
                registrar_descarga(ent, f"{tdoc}.pdf")
        with b3:
            buffer_word = io.BytesIO(texto_editable_actual.encode('utf-8'))
            st.download_button(label="📝 Descargar Word", data=buffer_word, file_name=f"{tdoc.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with b4:
            if st.button("🛑 Cerrar Visor", use_container_width=True, type="primary"):
                st.session_state["ver_visor_legal"] = False
                st.rerun()
                
    else:
        # PESTAÑAS ORDINARIAS DE TRABAJO CONTABLE Y LOGÍSTICO
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
            costo_operativo_total = App_km_gastados = kilometros_gastados_reales * costo_operacion_km
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
# PARTE 3 DE 3: COLUMNA DE LA DERECHA - DOBLE MENÚ DESPLEGABLE Y UPLOADING
# ==============================================================================
with col_derecha_documental:
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 15px;'>
        <h3 style='color: #1e4620; margin-top:0; font-size:15px; font-weight:bold;'>📜 Almacén Documental Autónomo</h3>
        <p style='color: #6c757d; font-size:11px; margin-bottom:5px;'>Gobierno Corporativo y Estructura de Subsistemas</p>
    </div>
    """, unsafe_allow_html=True)
    
    # MENÚ DESPLEGABLE NIVEL 1: Selección de la Entidad Institucional
    lista_entidades = list(st.session_state["repositorio_institucional"].keys())
    seleccion_entidad = st.selectbox("🏢 1. Selecciona la Entidad / Subsistema:", ["-- Elige una Entidad --"] + lista_entidades)
    
    # MENÚ DESPLEGABLE NIVEL 2: Despliegue Secuencial de sus Marcos
    if seleccion_entidad != "-- Elige una Entidad --":
        lista_marcos = list(st.session_state["repositorio_institucional"][seleccion_entidad].keys())
        seleccion_marco = st.selectbox("📋 2. Selecciona el Tipo de Documento:", ["-- Elige el Marco --"] + lista_marcos)
        
        if seleccion_marco != "-- Elige el Marco --":
            # Activar el gatillo para levantar el visor editable en la columna de la izquierda
            st.session_state["ver_visor_legal"] = True
            st.session_state["entidad_seleccionada"] = seleccion_entidad
            st.session_state["tipo_doc_seleccionado"] = seleccion_marco
            st.button("⚡ Abrir Documento en Visor", key="btn_trigger_open_nested")
            
    st.markdown("---")
    
    # SISTEMA DE UPLOADING PARA NUEVAS UNIDADES ECONÓMICAS
    st.markdown("#### 📤 Uploading de Nuevas Estructuras")
    archivo_cargado = st.file_uploader("Sube un acta o instructivo complementario (.txt):", type=["txt"])
    
    if archivo_cargado is not None:
        nombre_archivo_crudo = archivo_cargado.name.replace(".txt", "")
        if nombre_archivo_crudo not in st.session_state["repositorio_institucional"]:
            try:
                contenido_texto = archivo_cargado.read().decode("utf-8", errors="ignore")
                # Se crea de forma automática la entidad con sus tres carpetas obligatorias por default
                st.session_state["repositorio_institucional"][nombre_archivo_crudo] = {
                    "Marco conceptual y descriptivo": contenido_texto,
                    "Marco legal": "Borrador de marco legal en espera de adición por el Asociado Director.",
                    "Manual de procedimientos": "Borrador de manual de procedimientos en espera de calibración contable."
                }
                st.success(f"✓ '{nombre_archivo_crudo}' indexado con su matriz obligatoria de 3 marcos.")
                st.button("🔄 Actualizar Menú", key="refresh_uploader_nested")
            except Exception as e:
                st.error("Error de decodificación.")

# MATRIZ DE CIERRE VISUAL AL PIE DE LA INTERFAZ
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0; font-size:14px;'>🟢 Nodo Central: Asociación Civil</h4><p style='color: #1c7430; font-size: 12px;'><b>Estatus:</b> 0% IVA / Escudo 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 12px; border-radius: 6px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0; font-size:14px;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 12px;'><b>Impacto:</b> Capitaliza excedentes netos de fletes e intermediación libre de ISR.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0; font-size:14px;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 12px;'><b>Impacto:</b> Transforma primas comerciales de la S.A. en fondos de fomento.</p></div>", unsafe_allow_html=True)
