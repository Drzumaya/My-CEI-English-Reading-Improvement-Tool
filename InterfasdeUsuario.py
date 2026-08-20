import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado exitoso en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# PARTE 1 DE 3: CONFIGURACIÓN, SEGURIDAD E INICIALIZACIÓN DE REPORTES EDITABLES
# ==============================================================================
st.set_page_config(
    page_title="Tablero Integrado - Agua Prieta",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar estados de sesión críticos para la seguridad de la A.C.
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if "historial_descargas" not in st.session_state:
    st.session_state["historial_descargas"] = []

# INICIALIZACIÓN DE TEXTOS DE INFORMES EDITABLES (Independientes para cada módulo)
if "reporte_fiscal_texto" not in st.session_state:
    st.session_state["reporte_fiscal_texto"] = "Informe contable de validacion para la Asociacion Civil que ampara la captacion de cuotas extraordinarias de recuperacion exentas de IVA y la retribucion de lideres tecnicos de Agua Prieta Sonora."

if "reporte_seguros_texto" not in st.session_state:
    st.session_state["reporte_seguros_texto"] = "Certificado anual expedido por el Subsistema de Gestion de Riesgos que detalla la captacion de primas comerciales y el retorno legal de utilidades hacia el fondo de desarrollo de la Asociacion Civil."

if "reporte_caja_texto" not in st.session_state:
    st.session_state["reporte_caja_texto"] = "Balance consolidador del circuito cerrado de riqueza de Agua Prieta Sonora. Valida el capital semilla disponible para financiamientos de activos fijos de baja escala sin intermediacion bancaria tradicional."

# Inicializar textos estatutarios del repositorio legal
if "doc_seguros" not in st.session_state:
    st.session_state["doc_seguros"] = "ESCRITURA PÚBLICA: [CONSTITUCIÓN S.A. DE C.V.] - RAMO MICROSEGUROS AGUA PRIETA..."
if "doc_cooperativa" not in st.session_state:
    st.session_state["doc_cooperativa"] = "ACTA CONSTITUTIVA DE SOCIEDAD COOPERATIVA S.C. DE R.L. DE C.V. - TRANSPORTE BARRIAL..."
if "doc_corretaje" not in st.session_state:
    st.session_state["doc_corretaje"] = "CONTRATO DE CORRETAJE SOCIAL Y CAPACITACIÓN EN PREVENCION DE RIESGOS..."
if "doc_fideicomiso" not in st.session_state:
    st.session_state["doc_fideicomiso"] = "CONTRATO DE FIDEICOMISO PRIVADO Y CUENTA DE ORDEN DE LA CAJA DE AHORRO..."

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

# Generador de Informes Técnicos en PDF (Nivel Doctoral)
def generar_informe_pdf(titulo_modulo, datos_tabla, resumen_texto):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    color_primario = colors.HexColor("#1e4620")
    
    estilo_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=color_primario, spaceAfter=15)
    estilo_sub = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.gray, spaceAfter=20)
    estilo_cuerpo = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=11, leading=16, spaceAfter=15)
    
    story = []
    story.append(Paragraph(f"<b>{titulo_modulo}</b>", estilo_titulo))
    story.append(Paragraph("Ecosistema de Economía Popular AP-AC | Documentación Operativa Oficial", estilo_sub))
    story.append(Spacer(1, 10))
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    story.append(Spacer(1, 15))
    
    tabla_pdf = Table(datos_tabla, colWidths=)
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), color_primario), ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(tabla_pdf)
    doc.build(story)
    buffer.seek(0)
    return buffer

st.sidebar.header("📋 Operaciones")
if st.sidebar.button("❌ Cerrar Sesión (Logout)", use_container_width=True, type="primary"):
    logout()
presupuesto_total = st.sidebar.number_input("Bolsa Económica Mensual Operativa (MXN)", min_value=10000, value=250000, step=10000)

tabs = st.tabs(["🛡️ IVA e ISR", "📊 Microseguros", "🏦 Caja de Ahorro", "📈 Estadísticas Anuales", "📝 Editor Estatutario", "📑 Historial de Descargas"])
tab1, tab4, tab5, tab_stats, tab6, tab_log = tabs
# ==============================================================================
# PARTE 2 DE 3: MÓDULOS DE SIMULACIÓN CON GESTORES PDF INDEPENDIENTES
# ==============================================================================
num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_global = 35000.0

# ----- PESTAÑA 1: GESTIÓN DE IVA E ISR -----
with tab1:
    st.header("Control Fiscal de Operaciones de la Base Social")
    col1, col2 = st.columns(2)
    with col1:
        num_talleres = st.slider("Talleres Populares Integrados", min_value=5, max_value=300, value=num_talleres_global)
        num_talleres_global = num_talleres
        cuota_calculada = float(presupuesto_total / num_talleres)
        st.metric("Cuota Extraordinaria de Recuperación", f"${cuota_calculada:,.2f} MXN", "0% IVA (Exento)")
    
    with col2:
        st.subheader("📑 Centro de Edición y Compilación del Informe Fiscal")
        
        # Sistema de Edición y Guardado de Cambios
        with st.expander("📝 Botón: Editar Cuerpo del Reporte"):
            txt_fiscal_editado = st.text_area("Modifica el texto introductorio del PDF:", value=st.session_state["reporte_fiscal_texto"], key="edit_t1_area")
            if st.button("💾 Guardar Cambios en Reporte Fiscal", key="save_t1_btn"):
                st.session_state["reporte_fiscal_texto"] = txt_fiscal_editado
                st.success("✓ Cambios consolidados en el borrador fiscal.")

        # Recalcular la matriz de datos en tiempo real para el PDF
        tabla_datos_t1 = [
            ["Indicador Técnico / Concepto", "Monto Calculado (MXN)"],
            ["Bolsa Operativa Mensual Inyectada", f"${float(presupuesto_total):,.2f}"],
            ["Número de Talleres Incorporados", f"{num_talleres} Miembros Adherentes"],
            ["Cuota Estatutaria Promedio", f"${cuota_calculada:,.2f}"],
            ["Escudo Fiscal Generado (30% ISR Mitigado)", f"${float(presupuesto_total * 0.30):,.2f}"]
        ]
        
        # Botón de consulta y descarga final compilandose con las ediciones guardadas
        pdf_t1 = generar_informe_pdf("Informe de Blindaje Fiscal y Remanentes", tabla_datos_t1, st.session_state["reporte_fiscal_texto"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.download_button(label="📥 Descargar Reporte de Blindaje Fiscal (PDF)", data=pdf_t1, file_name="Reporte_Fiscal_AC.pdf", mime="application/pdf", key="dl_t1"):
            registrar_descarga("🛡️ IVA e ISR", "Reporte_Fiscal_AC.pdf")

# ----- PESTAÑA 4: MICROSEGUROS (S.A.) -----
with tab4:
    st.header("Subsistema de Gestión de Riesgos de la Célula Mercantil")
    col_t4_l, col_t4_r = st.columns(2)
    with col_t4_l:
        prima_mensual = st.number_input("Prima Mensual por Taller (MXN)", min_value=50.0, value=prima_individual_global)
        prima_individual_global = prima_mensual
        retorno_pct = st.slider("Porcentaje de Retorno Pactado para la A.C.", min_value=5, max_value=40, value=comision_retorno_global)
        comision_retorno_global = retorno_pct
    
    prima_anual = float(num_talleres_global * prima_mensual * 12)
    retorno_anual_ac = prima_anual * (retorno_pct / 100)
    
    with col_t4_r:
        st.subheader("📑 Centro de Edición y Compilación de Certificados")
        
        with st.expander("📝 Botón: Editar Cuerpo del Certificado"):
            txt_seguros_editado = st.text_area("Modifica las cláusulas de riesgo del PDF:", value=st.session_state["reporte_seguros_texto"], key="edit_t4_area")
            if st.button("💾 Guardar Cambios en Certificado de Seguros", key="save_t4_btn"):
                st.session_state["reporte_seguros_texto"] = txt_seguros_editado
                st.success("✓ Cambios consolidados en el borrador de seguros.")

        tabla_datos_t4 = [
            ["Rubro de Control de Riesgos", "Valor Proyectado Anual"],
            ["Volumen Global de Primas Recaudadas", f"${prima_anual:,.2f} MXN"],
            ["Retorno por Comisión a la A.C.", f"${retorno_anual_ac:,.2f} MXN"],
            ["Fondo Comunitario de Siniestralidad (5%)", f"${float(prima_anual * 0.05):,.2f} MXN"]
        ]
        
        pdf_t4 = generar_informe_pdf("Certificado Patrimonial de Microseguros", tabla_datos_t4, st.session_state["reporte_seguros_texto"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.download_button(label="📥 Descargar Certificado de Pólizas (PDF)", data=pdf_t4, file_name="Certificado_Microseguros.pdf", mime="application/pdf", key="dl_t4"):
            registrar_descarga("📊 Microseguros", "Certificado_Microseguros.pdf")

# ----- PESTAÑA 5: CAJA DE AHORRO -----
with tab5:
    st.header("Caja de Ahorro y Consolidación de Fondos Mutuos")
    col_t5_l, col_t5_r = st.columns(2)
    with col_t5_l:
        ahorrio_mensual = st.number_input("Ahorros Directos de los Trabajadores", min_value=0.0, value=55000.0)
        comision_seguros_mensual = float(retorno_anual_ac / 12)
        excedente_cooperativa = st.number_input("Inyección desde la Cooperativa de Logística", min_value=0.0, value=excedente_coop_global)
        monto_credito = st.number_input("Monto por Microcrédito de Maquinaria", min_value=5000.0, value=35000.0, step=5000.0)
    
    capital_mensual_total = ahorrio_mensual + comision_seguros_mensual + excedente_cooperativa
    capital_anual_total = capital_mensual_total * 12
    creditos_otorgados = int(capital_anual_total // monto_credito)
    
    with col_t5_r:
        st.subheader("📑 Centro de Edición y Compilación del Balance")
        
        with st.expander("📝 Botón: Editar Resumen de Estados de Cuenta"):
            txt_caja_editado = st.text_area("Modifica las notas de balance del PDF:", value=st.session_state["reporte_caja_texto"], key="edit_t5_area")
            if st.button("💾 Guardar Cambios en Balance General", key="save_t5_btn"):
                st.session_state["reporte_caja_texto"] = txt_caja_editado
                st.success("✓ Cambios consolidados en el borrador de la caja.")

        tabla_datos_t5 = [
            ["Estructura de Capital Social", "Flujo Consolidado (MXN)"],
            ["Inyecciones Mensuales Consolidadas", f"${capital_mensual_total:,.2f}"],
            ["Capacidad Financiera Anual Recurrente", f"${capital_anual_total:,.2f}"],
            ["Microcréditos de Maquinaria Viables / Año", f"{creditos_otorgados} Otorgamientos"]
        ]
        
        pdf_t5 = generar_informe_pdf("Balance Analítico de la Caja de Ahorro", tabla_datos_t5, st.session_state["reporte_caja_texto"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.download_button(label="📥 Descargar Balance de Fondos Mutuos (PDF)", data=pdf_t5, file_name="Balance_Caja_Ahorro.pdf", mime="application/pdf", key="dl_t5"):
            registrar_descarga("🏦 Caja de Ahorro", "Balance_Caja_Ahorro.pdf")
# ==============================================================================
# PARTE 3 DE 3: TENDENCIAS ANUALES, REPOSITORIO E HISTORIAL DE AUDITORÍA
# ==============================================================================

# ----- PESTAÑA: ESTADÍSTICAS POR AÑO -----
with tab_stats:
    st.header("📈 Proyección Histórica y Crecimiento Macroeconómico")
    datos_historicos = {
        "2024 (Base Histórica)": {"capital": 450000.0, "creditos": 12, "pib_impacto": "1.2%"},
        "2025 (Fase de Campo)": {"capital": 780000.0, "creditos": 22, "pib_impacto": "4.5%"},
        "2026 (Ejercicio Actual)": {"capital": capital_anual_total, "creditos": creditos_otorgados, "pib_impacto": "8.2%"},
        "2027 (Proyección Alta)": {"capital": capital_anual_total * 1.35, "creditos": int((capital_anual_total * 1.35) // monto_credito), "pib_impacto": "11.4%"}
    }
    
    col_sel, col_down = st.columns(2)
    with col_sel:
        anio_seleccionado = st.selectbox("📊 Selecciona el Ejercicio Fiscal a Evaluar:", list(datos_historicos.keys()))
    with col_down:
        texto_resumen_stats = f"Informe de auditoria historica comparativa que consolida el crecimiento del ecosistema popular para el ano fiscal {anio_seleccionado}."
        tabla_datos_stats = [
            ["Indicador Macroeconómico Local", f"Métricas del Ejercicio {anio_seleccionado}"],
            ["Capital Social Anualizado", f"${datos_historicos[anio_seleccionado]['capital']:,.2f} MXN"],
            ["Capacidad de Concesión de Activos", f"{datos_historicos[anio_seleccionado]['creditos']} Créditos"],
            ["Incremento Proyectado en el PIB Real", f"{datos_historicos[anio_seleccionado]['pib_impacto']} de Retención Local"]
        ]
        pdf_stats = generar_informe_pdf(f"Auditoría Histórica - Ejercicio {anio_seleccionado}", tabla_datos_stats, texto_resumen_stats)
        st.markdown("<div style='padding-top:25px;'></div>", unsafe_allow_html=True)
        
        nombre_pdf_stats = f"Auditoria_{anio_seleccionado.split()[0]}.pdf"
        if st.download_button(label=f"📥 Descargar Reporte Histórico {anio_seleccionado} (PDF)", data=pdf_stats, file_name=nombre_pdf_stats, mime="application/pdf", key="dl_stats"):
            registrar_descarga("📈 Estadísticas Anuales", nombre_pdf_stats)

    st.markdown("#### 🕒 Serie de Tiempo del Incremento de Capital Comunitario")
    col_y1, col_y2, col_y3, col_y4 = st.columns(4)
    col_y1.metric("Año 2024", f"${datos_historicos['2024 (Base Histórica)']['capital']:,.0f} MXN", "Línea de Origen")
    col_y2.metric("Año 2025", f"${datos_historicos['2025 (Fase de Campo)']['capital']:,.0f} MXN", "+73.3% Crecimiento")
    col_y3.metric("Año 2026 (Actual)", f"${datos_historicos['2026 (Ejercicio Actual)']['capital']:,.0f} MXN", "Dinámico", delta_color="inverse")
    col_y4.metric("Año 2027 (Proyectado)", f"${datos_historicos['2027 (Proyección Alta)']['capital']:,.0f} MXN", "+35.0% Tendencia")

# ----- PESTAÑA: EDITOR ESTATUTARIO -----
with tab6:
    st.header("📜 Gestor Legal de Instrumentos Jurídicos Autónomos")
    opciones_docs = [
        "Sub-Acta 1: Agencia de Seguros (S.A. de C.V.)", "Sub-Acta 2: Cooperativa de Logística (S.C. de R.L.)",
        "Contrato 1: Corretaje Social (A.C. ── Agencia Seguros)", "Contrato 2: Fideicomiso Privado (A.C. ── Caja de Ahorro)"
    ]
    doc_seleccionado = st.selectbox("⚡ Selecciona el documento que deseas trabajar:", opciones_docs)
    
    if doc_seleccionado == "Sub-Acta 1: Agencia de Seguros (S.A. de C.V.)":
        texto_inicial, key_memoria = st.session_state["doc_seguros"], "doc_seguros"
    elif doc_seleccionado == "Sub-Acta 2: Cooperativa de Logística (S.C. de R.L.)":
        texto_inicial, key_memoria = st.session_state["doc_cooperativa"], "doc_cooperativa"
    elif doc_seleccionado == "Contrato 1: Corretaje Social (A.C. ── Agencia Seguros)":
        texto_inicial, key_memoria = st.session_state["doc_corretaje"], "doc_corretaje"
    else:
        texto_inicial, key_memoria = st.session_state["doc_fideicomiso"], "doc_fideicomiso"
        
    texto_editado = st.text_area(label=f"Modifica las cláusulas de: {doc_seleccionado}", value=texto_inicial, height=250)
    
    if st.button("💾 Consolidar y Guardar Cambios en el Estatuto", type="secondary", key="save_statutes_btn"):
        st.session_state[key_memoria] = texto_editado
        st.success("✓ Estatuto actualizado correctamente en la memoria de la A.C.")

# ----- PESTAÑA: CONSULTA DEL HISTORIAL DE DESCARGAS -----
with tab_log:
    st.header("📑 Bitácora de Auditoría e Historial de Descargas")
    if len(st.session_state["historial_descargas"]) == 0:
        st.info("ℹ️ No se registran descargas de archivos en el presente ciclo operativo.")
    else:
        st.warning("⚠️ Control de Auditoría Interna Activo.")
        st.table(st.session_state["historial_descargas"])

# MATRIZ INDUSTRIAL DE CIERRE
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0;'>🟢 Nodo Central: Asociación Civil</h4><p style='color: #1c7430; font-size: 14px;'><b>Función:</b> Absorción de flujos indirectos y dispersión de nómina barrial.<br><b>Estatus:</b> 0% IVA / Escudo 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 15px; border-radius: 8px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 14px;'><b>Contrato Blanco:</b> Fideicomiso / Cuenta de Orden.<br><b>Impacto:</b> Resguarda el capital de Agua Prieta libre de base gravable.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 14px;'><b>Contrato Rojo:</b> Corretaje Social (Retorno 20%).<br><b>Impacto:</b> Transforma utilidades de la S.A. en fondos limpios de fomento.</p></div>", unsafe_allow_html=True)
