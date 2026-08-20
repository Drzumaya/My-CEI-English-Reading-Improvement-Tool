import streamlit as st
import io
from datetime import datetime
# Motores ReportLab puros para asegurar renderizado de PDFs en la nube
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# PARTE 1 DE 3: CONFIGURACIÓN, SEGURIDAD E INICIALIZACIÓN DOCUMENTAL
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

# VARIABLE DE CONTROL DE VENTANA FLOTANTE LEGAL
if "ver_visor_legal" not in st.session_state:
    st.session_state["ver_visor_legal"] = False
if "doc_seleccionado" not in st.session_state:
    st.session_state["doc_seleccionado"] = ""

# BASE DE DATOS DOCUMENTAL EDITABLE EN MEMORIA ACTIVA DE SESIÓN
if "documentos_sistema" not in st.session_state:
    st.session_state["documentos_sistema"] = {
        "Sub-Acta 1: Agencia de Seguros (S.A.)": """ESCRITURA PÚBLICA NÚMERO: [XXXX] | VOLUMEN: [XX]\nCONSTITUCIÓN DE SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE\n\nEn la ciudad de Agua Prieta, Sonora, a 20 de agosto de 2026, ante mí, el Notario Público Número [X], comparece el Asociado Director en representación del Subsistema de Riesgos, para constituir una SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE, sujeta a los siguientes estatutos:\n\nARTÍCULO PRIMERO: DENOMINACIÓN.\nLa sociedad se denominará "AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA", S.A. DE C.V. Esta entidad funciona como un subsistema autónomo de la Asociación Civil matriz.\n\nARTÍCULO SEGUNDO: OBJETO SOCIAL.\nLa sociedad tendrá por objeto exclusivo la intermediación de contratos de seguros en los ramos de vida, accidentes y daños ante la CNSF.""",
        
        "Sub-Acta 2: Cooperativa de Logística (S.C.)": """ACTA DE ASAMBLEA CONSTITUTIVA DE SOCIEDAD COOPERATIVA\nREGISTRO COMERCIAL: SC-AP-2026-02\n\nEn la periferia urbana de Agua Prieta, Sonora, siendo las 10:00 horas del día 20 de agosto de 2026, se reúnen de manera voluntaria los trabajadores de los barrios de la localidad para constituir una SOCIEDAD COOPERATIVA DE PRODUCCIÓN DE SERVICIOS, al tenor de las siguientes bases:\n\nARTÍCULO 1: DENOMINACIÓN Y RÉGIMEN.\nLa sociedad se denominará "COOPERATIVA DE TRANSPORTE Y LOGÍSTICA DE LOS BARRIOS DE AGUA PRIETA", S.C. DE R.L. DE C.V.\n\nARTÍCULO 2: OBJETO SOCIAL.\nCoordinar y ejecutar servicios de flete y logística de última milla para la proveeduría indirecta de las plantas maquiladoras fronterizas.""",
        
        "Contrato 1: Corretaje Social (A.C. - S.A.)": """CONTRATO DE PRESTACIÓN DE SERVICIOS DE CAPACITACIÓN Y PROMOCIÓN DE RIESGOS\n\nContrato que celebran por una parte la "Asociación Civil Matriz", representada por su Apoderado Legal, en lo sucesivo "LA MATRIZ"; y por la otra parte "AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA, S.A. DE C.V.", representada por su Administrador Único, en lo sucesivo "EL SUBSISTEMA DE SEGUROS", al tenor de las siguientes cláusulas:\n\nPRIMERA: RETORNO DE VALOR. "EL SUBSISTEMA DE SEGUROS" pagará mensualmente a "LA MATRIZ" una cantidad equivalente al 20% de las primas totales recaudadas.\n\nSEGUNDA: EXENCIÓN DE IVA. Ambas partes reconocen que los ingresos encuadran en el supuesto de EXENCIÓN de IVA contemplado en el Artículo 15 de la Ley del IVA.""",
        
        "Contrato 2: Fideicomiso Privado (A.C. - Caja)": """CONTRATO DE MANDATO Y ADJUDICACIÓN DE FIDEICOMISO DE ADMINISTRACIÓN PATRIMONIAL PRIVADO\n\nContrato de fideicomiso privado que celebran por una parte "LA MATRIZ" (Asociación Civil), en su carácter de Fideicomitente; y por la otra parte, el Asociado Director de la Caja de Ahorro, en su carácter de Administrador Técnico, bajo el amparo de las siguientes estipulaciones:\n\nPRIMERA: PATRIMONIO AUTÓNOMO. Los recursos depositados por los trabajadores constituyen un patrimonio autónomo separado del gasto corriente de "LA MATRIZ".\n\nSEGUNDA: REGISTRO EN CUENTAS DE ORDEN. El contador registrará el flujo en Cuentas de Orden amparando ante el SAT que el capital pertenece al fondo mutualista y no representa un ingreso acumulable de la A.C. (Pulverización del 30% de ISR)."""
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
    
    estilo_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, textColor=color_primario, spaceAfter=15)
    estilo_sub = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, textColor=colors.gray, spaceAfter=15)
    estilo_cuerpo = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=15)
    
    story = []
    story.append(Paragraph(f"<b>{titulo_modulo}</b>", estilo_titulo))
    story.append(Paragraph("Ecosistema de Economía Popular AP-AC | Documentación Oficial", estilo_sub))
    story.append(Spacer(1, 10))
    story.append(Paragraph(resumen_texto, estilo_cuerpo))
    story.append(Spacer(1, 15))
    
    tabla_pdf = Table(datos_tabla, colWidths=[240, 240])
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
# PARTE 2 DE 3: COLUMNA DE LA IZQUIERDA - SIMULADORES FISCALES Y DE SUBSISTEMAS
# ==============================================================================

# División de pantalla: 70% Simuladores Operativos (Izquierda), 30% Panel Documental (Derecha)
col_izquierda_matriz, col_derecha_documental = st.columns([7, 3])

num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_global = 35000.0

with col_izquierda_matriz:
    # Si la ventana flotante legal está activa, ocultamos los simuladores para simular la nueva página
    if st.session_state["ver_visor_legal"]:
        st.info(f"📁 Ventana de Trabajo Activa: {st.session_state['doc_seleccionado']}")
        st.markdown("---")
        
        # El cuadro de texto carga los datos desde el diccionario de la sesión y permite la EDICIÓN EN VIVO
        texto_editable_actual = st.text_area(
            label="Editor Legal de Cláusulas (Cambios en Caliente):",
            value=st.session_state["documentos_sistema"][st.session_state["doc_seleccionado"]],
            height=400
        )
        
        # FILA INTERACTIVA DE TRES BOTONES DENTRO DE LA VENTANA
        b1, b2, b3, b4 = st.columns(4)
        
        with b1:
            # BOTÓN 1: Guardar Cambios en la base de datos de la sesión
            if st.button("💾 Guardar Ajustes", use_container_width=True, type="secondary"):
                st.session_state["documentos_sistema"][st.session_state["doc_seleccionado"]] = texto_editable_actual
                st.success("✓ Estatuto guardado.")
                
        with b2:
            # BOTÓN 2: Descargar en PDF
            tabla_legal_dummy = [["Estatus del Instrumento", "Validación Legal de la A.C."], ["Fecha de Compilación", "20 de agosto de 2026"], ["Ubicación de Jurisdicción", "Agua Prieta, Sonora"]]
            pdf_legal = generar_informe_pdf(st.session_state["doc_seleccionado"], tabla_legal_dummy, texto_editable_actual)
            st.download_button(label="📥 Descargar PDF", data=pdf_legal, file_name=f"{st.session_state['doc_seleccionado'].replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
            
        with b3:
            # BOTÓN 3: Descargar en Word
            buffer_word = io.BytesIO(texto_editable_actual.encode('utf-8'))
            st.download_button(label="📝 Descargar Word", data=buffer_word, file_name=f"{st.session_state['doc_seleccionado'].replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            
        with b4:
            # BOTÓN 4: Cierre de la ventana flotante y retorno a la principal
            if st.button("🛑 Cerrar Visor", use_container_width=True, type="primary"):
                st.session_state["ver_visor_legal"] = False
                st.rerun()
                
    else:
        # RENDERIZADO DE LAS PESTAÑAS OPERATIVAS ORDINARIAS
        tabs = st.tabs(["🛡️ IVA e ISR", "📊 Microseguros", "🏦 Caja de Ahorro", "📈 Estadísticas Anuales", "📑 Historial de Descargas"])
        tab1, tab4, tab5, tab_stats, tab_log = tabs
        
        # ----- PESTAÑA 1: GESTIÓN DE IVA E ISR -----
        with tab1:
            st.header("Control Fiscal de Operaciones de la Base Social")
            num_talleres = st.slider("Talleres Populares Integrados", min_value=5, max_value=300, value=num_talleres_global)
            num_talleres_global = num_talleres
            cuota_calculada = float(presupuesto_total / num_talleres)
            st.metric("Cuota Extraordinaria de Recuperación", f"${cuota_calculada:,.2f} MXN", "0% IVA (Exento)")
            
            tabla_datos_t1 = [["Concepto", "Monto (MXN)"], ["Bolsa Inyectada", f"${float(presupuesto_total):,.2f}"], ["Talleres", f"{num_talleres}"], ["Escudo Fiscal (30% ISR)", f"${float(presupuesto_total * 0.30):,.2f}"]]
            pdf_t1 = generar_informe_pdf("Informe de Blindaje Fiscal", tabla_datos_t1, st.session_state["reporte_fiscal_texto"])
            if st.download_button(label="📥 Descargar Reporte Fiscal (PDF)", data=pdf_t1, file_name="Reporte_Fiscal.pdf", mime="application/pdf"):
                registrar_descarga("🛡️ IVA e ISR", "Reporte_Fiscal.pdf")

        # ----- PESTAÑA 4: MICROSEGUROS (S.A.) -----
        with tab4:
            st.header("Subsistema de Gestión de Riesgos de la Célula Mercantil")
            prima_mensual = st.number_input("Prima Mensual por Taller (MXN)", min_value=50.0, value=prima_individual_global)
            prima_individual_global = prima_mensual
            retorno_pct = st.slider("Porcentaje de Retorno Pactado para la A.C.", min_value=5, max_value=40, value=comision_retorno_global)
            comision_retorno_global = retorno_pct
            
            prima_anual = float(num_talleres_global * prima_mensual * 12)
            retorno_anual_ac = prima_anual * (retorno_pct / 100)
            st.metric("Retorno de Comisión Anual para la A.C.", f"${retorno_anual_ac:,.2f} MXN")

        # ----- PESTAÑA 5: CAJA DE AHORRO -----
        with tab5:
            st.header("Caja de Ahorro (El Brazo Fuerte Financiero)")
            ahorrio_mensual = st.number_input("Ahorros Directos de los Trabajadores", min_value=0.0, value=55000.0)
            comision_seguros_mensual = float(retorno_anual_ac / 12)
            excedente_cooperativa = st.number_input("Inyección de la Cooperativa", min_value=0.0, value=excedente_coop_global)
            
            capital_mensual_total = ahorrio_mensual + comision_seguros_mensual + excedente_cooperativa
            st.metric("Fondo de Emprendimiento Mensual Consolidado", f"${capital_mensual_total:,.2f} MXN")

        # ----- PESTAÑA: ESTADÍSTICAS POR AÑO -----
        with tab_stats:
            st.header("📈 Proyección Histórica de Crecimiento")
            st.markdown("Métricas acumuladas del circuito cerrado de riqueza de Agua Prieta.")
            st.metric("PIB Local - Impacto Estimado de Retención (2026)", "8.2% del Producto Municipal")

        # ----- PESTAÑA: HISTORIAL DE DESCARGAS -----
        with tab_log:
            st.header("📑 Historial de Auditoría de Descargas")
            if len(st.session_state["historial_descargas"]) == 0:
                st.info("No se registran descargas en el ciclo actual.")
            else:
                st.table(st.session_state["historial_descargas"])
# ==============================================================================
# PARTE 3 DE 3: COLUMNA DE LA DERECHA - MENÚ DESPLEGABLE OFICIAL Y UPLOADING
# ==============================================================================
with col_derecha_documental:
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 12px; border-radius: 6px; border: 1px solid #dee2e6; margin-bottom: 15px;'>
        <h3 style='color: #1e4620; margin-top:0; font-size:16px; font-weight:bold;'>📜 Repositorio de Archivos Oficiales</h3>
        <p style='color: #6c757d; font-size:12px; margin-bottom:5px;'>Subsistemas Autónomos y Contratos de Enlace</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. MENÚ DESPLEGABLE INTERACTIVO DE ARCHIVOS OFICIALES
    lista_documentos_disponibles = list(st.session_state["documentos_sistema"].keys())
    seleccion_archivo = st.selectbox("📁 Selecciona el Instrumento Jurídico:", ["-- Elige un Archivo --"] + lista_documentos_disponibles)
    
    if seleccion_archivo != "-- Elige un Archivo --":
        # Activar la bandera de la ventana flotante en la columna izquierda con un solo clic
        st.session_state["ver_visor_legal"] = True
        st.session_state["doc_seleccionado"] = seleccion_archivo
        st.button("⚡ Abrir Ventana de Trabajo", key="trigger_open_visor")

    st.markdown("---")
    
    # 2. SISTEMA DE UPLOADING PARA NUEVOS ARCHIVOS / ACTAS DEL CONSEJO
    st.markdown("#### 📤 Uploading de Nuevas Actas")
    archivo_cargado = st.file_uploader("Sube un nuevo estatuto (Formato .txt o .docx):", type=["txt", "docx"])
    
    if archivo_cargado is not None:
        nombre_nuevo_doc = f"Nueva Acta: {archivo_cargado.name}"
        # Leer el contenido del buffer cargado por el usuario
        if nombre_nuevo_doc not in st.session_state["documentos_sistema"]:
            try:
                contenido_bytes = archivo_cargado.read()
                contenido_texto = contenido_bytes.decode("utf-8", errors="ignore")
                # Guardar de forma inmediata en la base de datos de la sesión
                st.session_state["documentos_sistema"][nombre_nuevo_doc] = contenido_texto
                st.success(f"✓ '{archivo_cargado.name}' guardado e indexado en la lista desplegable.")
                st.button("🔄 Actualizar Repositorio", key="btn_refresh_upload")
            except Exception as e:
                st.error("Error al procesar el archivo cargado.")

# MATRIZ INDUSTRIAL DE CIERRE AL PIE DE LA INTERFAZ
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 12px; border-radius: 6px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0; font-size:14px;'>🟢 Nodo Central: Asociación Civil</h4><p style='color: #1c7430; font-size: 12px;'><b>Estatus:</b> 0% IVA / Escudo 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 12px; border-radius: 6px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0; font-size:14px;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 12px;'><b>Impacto:</b> Resguarda el capital de Agua Prieta libre de base gravable.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0; font-size:14px;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 12px;'><b>Impacto:</b> Transforma utilidades de la S.A. en fondos de fomento.</p></div>", unsafe_allow_html=True)
