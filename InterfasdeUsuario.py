import streamlit as st

# ==============================================================================
# PARTE 1 DE 3: CONFIGURACIÓN, SEGURIDAD Y CONTROL DE SESIÓN EDITABLE
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

# TEXTOS LEGALES EN MEMORIA: Inicializar la base de datos editable del Título II
if "doc_seguros" not in st.session_state:
    st.session_state["doc_seguros"] = """ESCRITURA PÚBLICA NÚMERO: [XXXX] | VOLUMEN: [XX]
CONSTITUCIÓN DE SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE

En la ciudad de Agua Prieta, Sonora, a 20 de agosto de 2026, ante mí, el Notario Público Número [X], comparece el Asociado Director en representación del Subsistema de Riesgos, para constituir una SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE, sujeta a los siguientes estatutos:

ARTÍCULO PRIMERO: DENOMINACIÓN Y BRAZO DE CONEXIÓN.
La sociedad se denominará "AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA", seguida de las palabras SOCIEDAD ANÓNIMA DE CAPITAL VARIABLE o de sus siglas "S.A. DE C.V.". Esta entidad funciona como un subsistema autónomo de la Asociación Civil matriz.

ARTÍCULO SEGUNDO: OBJETO SOCIAL CORPORATIVO.
La sociedad tendrá por objeto exclusivo: 
a) Realizar actividades de intermediación de contratos de seguros en los ramos de vida, accidentes, enfermedades y daños, de conformidad con la Ley de Instituciones de Seguros y de Fianzas (LISF).
b) Tramitar y mantener la cédula de Agente de Seguros Persona Moral ante la Comisión Nacional de Seguros y Fianzas (CNSF)."""

if "doc_cooperativa" not in st.session_state:
    st.session_state["doc_cooperativa"] = """ACTA DE ASAMBLEA CONSTITUTIVA DE SOCIEDAD COOPERATIVA
REGISTRO COMERCIAL: SC-AP-2026-02

En la periferia urbana de Agua Prieta, Sonora, siendo las 10:00 horas del día 20 de agosto de 2026, se reúnen de manera voluntaria los trabajadores choferes, transportistas y micro-comerciantes de los barrios de la localidad para constituir una SOCIEDAD COOPERATIVA DE PRODUCCIÓN DE SERVICIOS, al tenor de las siguientes bases constitutivas:

BASES CONSTITUTIVAS
ARTÍCULO 1: DENOMINACIÓN Y RÉGIMEN.
La sociedad se denominará "COOPERATIVA DE TRANSPORTE Y LOGÍSTICA DE LOS BARRIOS DE AGUA PRIETA", seguida de sus siglas "S.C. DE R.L. DE C.V." (Sociedad Cooperativa de Responsabilidad Limitada de Capital Variable)."""

if "doc_corretaje" not in st.session_state:
    st.session_state["doc_corretaje"] = """CONTRATO DE PRESTACIÓN DE SERVICIOS DE CAPACITACIÓN Y PROMOCIÓN DE RIESGOS

Contrato que celebran por una parte la "Asociación Civil Matriz", representada por su Apoderado Legal, en lo sucesivo "LA MATRIZ"; y por la otra parte "AGENCIA DE PROTECCIÓN SOLIDARIA FRONTERIZA, S.A. DE C.V.", representada por su Administrador Único, en lo sucesivo "EL SUBSISTEMA DE SEGUROS", al tenor de las siguientes cláusulas:

C L Á U S U L A S
PRIMERA: OBJETO. "LA MATRIZ" se obliga a prestar a "EL SUBSISTEMA DE SEGUROS" los servicios profesionales de educación, fomento y capacitación para el trabajo enfocados en la prevención de riesgos laborales y salvaguarda de maquinaria en las colonias de Agua Prieta, Sonora.

SEGUNDA: RETORNO DE VALOR (EL VÍNCULO FINANCIERO). Como contraprestación por los servicios de promoción y educación, "EL SUBSISTEMA DE SEGUROS" pagará mensualmente a "LA MATRIZ" una cantidad equivalente al 20% (veinte por ciento) de las primas totales recaudadas por la venta de pólizas de microseguros colectivos."""

if "doc_fideicomiso" not in st.session_state:
    st.session_state["doc_fideicomiso"] = """CONTRATO DE MANDATO Y ADJUDICACIÓN DE FIDEICOMISO DE ADMINISTRACIÓN PATRIMONIAL PRIVADO

Contrato de fideicomiso privado que celebran por una parte "LA MATRIZ" (Asociación Civil), en su carácter de Fideicomitente; y por la otra parte, el Asociado Director de la Caja de Ahorro, en su carácter de Fideicomisario y Administrador Técnico, bajo el amparo de las siguientes estipulaciones:

C L Á U S U L A S
PRIMERA: PATRIMONIO AUTÓNOMO (EL BRAZO FUERTE). Las partes acuerdan la constitución de un fondo de capital social denominado "Caja de Ahorro y Préstamo Digital de Agua Prieta". Los recursos depositados por los trabajadores populares, así como las inyecciones de utilidades de la cooperativa y seguros, constituyen un patrimonio autónomo separado del gasto corriente de "LA MATRIZ"."""


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
        
        st.text_input(
            "Introduce la contraseña institucional de acceso:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        
        if st.session_state.get("show_login_error", False):
            st.error("❌ Credenciales inválidas. Intento bloqueado por el protocolo de seguridad.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("ℹ️ ¿No tienes acceso? Soporte del Ecosistema"):
            st.caption("Nota: Las claves de acceso son administradas de forma directa por el Agente Capacitador.")
            
    return False

if not check_password():
    st.stop()

def logout():
    st.session_state["password_correct"] = False
    st.session_state["show_login_error"] = False
    st.rerun()

# Encabezado Principal
with st.sidebar:
    st.header("📋 Monitoreo de Red")
    st.success("🔒 Conexión Encriptada")
    st.markdown("**Organización:** Asociación Civil (Título II)")
    st.markdown("**Ubicación:** Agua Prieta, Sonora")
    st.header("🛑 Seguridad Corporativa")
    if st.button("❌ Cerrar Aplicación (Logout)", use_container_width=True, type="primary"):
        logout()
    st.markdown("---")
    st.header("⚙️ Presupuesto Global")
    presupuesto_total = st.number_input("Bolsa Económica Mensual Operativa (MXN)", min_value=10000, value=250000, step=10000)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛡️ Módulo 1: Blindaje IVA", "🧮 Módulo 2: Prorrateo IVA", "👥 Módulo 3: Nómina Asimilada",
    "📊 Módulo 4: Microseguros (S.A.)", "🏦 Módulo 5: Caja de Ahorro (Brazo Fuerte)", "📝 Módulo 6: Repositorio Editable"
])
# ==============================================================================
# PARTE 2 DE 3: MÓDULOS FISCALES (COMPORTAMIENTO DE IVA E ISR)
# ==============================================================================
num_talleres_global = 65
prima_individual_global = 120.0
comision_retorno_global = 20
excedente_coop_global = 35000.0

# ----- PESTAÑA 1: BLINDAJE DE IVA -----
with tab1:
    st.header("Estructuración de Ingresos mediante Cuotas Estatutarias")
    col_t1_l, col_t1_r = st.columns(2)
    with col_t1_l:
        num_talleres = st.slider("Talleres Populares Integrados (Miembros Adherentes)", min_value=5, max_value=300, value=num_talleres_global)
        num_talleres_global = num_talleres 
        cuota_calculada = float(presupuesto_total / num_talleres)
        
        c1, c2 = st.columns(2)
        c1.metric("Cuota Mensual Promedio", f"${cuota_calculada:,.2f} MXN")
        c2.metric("Tasa de IVA del Esquema", "0% (Exento)")
    with col_t1_r:
        st.info("💡 **Acción Legal del Asociado Director:**")
        st.markdown("Sustituir facturación de servicios comerciales por la emisión del **Formato de Recibo de Cuota Estatutaria** bajo el Art. 15-XII de la LIVA.")

# ----- PESTAÑA 2: PRORRATEO DE IVA -----
with tab2:
    st.header("Optimizador de Prorrateo de IVA (Art. 5-C LIVA)")
    col_t2_l, col_t2_r = st.columns(2)
    with col_t2_l:
        ing_exentos = st.number_input("Ingresos por Cursos y Capacitación (Exentos)", min_value=0.0, value=180000.0)
        ing_gravados = st.number_input("Ingresos Comerciales Gravados (Estímulo Fronterizo 8%)", min_value=0.0, value=50000.0)
    with col_t2_r:
        iva_gastos = st.number_input("IVA total pagado a proveedores en Agua Prieta", min_value=0.0, value=22000.0)
    
    factor = (ing_gravados / (ing_exentos + ing_gravados)) if (ing_exentos + ing_gravados) > 0 else 0.0
    iva_recuperable = iva_gastos * factor
    iva_costo = iva_gastos - iva_recuperable
    
    res1, res2, res3 = st.columns(3)
    res1.metric("Factor de Acreditamiento", f"{factor * 100:.2f}%")
    res2.metric("IVA Recuperable", f"${iva_recuperable:,.2f} MXN")
    res3.metric("IVA al Gasto (Costo Directo)", f"${iva_costo:,.2f} MXN", delta_color="inverse")

# ----- PESTAÑA 3: NÓMINA ASIMILADA -----
with tab3:
    st.header("Simulador de Retribución por Asimilados a Salarios")
    num_promotores = st.slider("Número de Líderes de Barrio a Retribuir", min_value=1, max_value=50, value=15)
    monto_bruto = float(presupuesto_total / num_promotores)
    isr_retenido = monto_bruto * 0.08 
    monto_neto = monto_bruto - isr_retenido
    ahorrado_isr_ac = float(presupuesto_total * 0.30)
    
    r_as1, r_as2, r_as3 = st.columns(3)
    r_as1.metric("Honorario Neto / Líder", f"${monto_neto:,.2f} MXN")
    r_as2.metric("Retención Total ISR a Enterar", f"${isr_retenido * num_promotores:,.2f} MXN")
    r_as3.metric("Ahorro en ISR Corporativo A.C.", f"${ahorrado_isr_ac:,.2f} MXN", delta="Gasto Justificado")
# ==============================================================================
# PARTE 3 DE 3: SUBSISTEMAS, CAJA DE AHORRO Y REPOSITORIO LEGAL EDITABLE
# ==============================================================================

# ----- PESTAÑA 4: MICROSEGUROS -----
with tab4:
    st.header("Gestión Financiera de la Agencia de Microseguros (S.A.)")
    col_t4_l, col_t4_r = st.columns(2)
    with col_t4_l:
        prima_mensual = st.number_input("Prima Mensual Cobrada por Taller (MXN)", min_value=50.0, value=prima_individual_global)
        prima_individual_global = prima_mensual
        retorno_pct = st.slider("Porcentaje de Comisión Pactado para Devolución a la A.C.", min_value=5, max_value=40, value=comision_retorno_global)
        comision_retorno_global = retorno_pct
    with col_t4_r:
        tasa_siniestros = st.slider("Tasa de Accidentes / Siniestros Proyectada (%)", min_value=1, max_value=20, value=5)
    
    prima_anual = float(num_talleres_global * prima_mensual * 12)
    retorno_anual_ac = prima_anual * (retorno_pct / 100)
    fondo_siniestros = prima_anual * (tasa_siniestros / 100)
    
    m_s1, m_s2, m_s3 = st.columns(3)
    m_s1.metric("Primas Anuales Capturadas (S.A.)", f"${prima_anual:,.2f} MXN")
    m_s2.metric("Comisión Retornada a la A.C.", f"${retorno_anual_ac:,.2f} MXN", delta="Ingreso de Fomento")
    m_s3.metric("Fondo de Reserva para Siniestros", f"${fondo_siniestros:,.2f} MXN")

# ----- PESTAÑA 5: CAJA DE AHORRO -----
with tab5:
    st.header("🏦 El Brazo Fuerte: Caja de Ahorro y Consolidación de Vínculos Financieros")
    col_t5_l, col_t5_r = st.columns(2)
    with col_t5_l:
        st.subheader("📥 Fuentes de Inyección de Capital Social (Mensual)")
        ahorrio_barrio_mensual = st.number_input("Ahorros Directos de los Trabajadores de Agua Prieta", min_value=0.0, value=55000.0)
        comision_seguros_mensual = float(retorno_anual_ac / 12)
        st.markdown(f"➕ **Inyección Automatizada desde Agencia de Seguros:** `${comision_seguros_mensual:,.2f} MXN/mes` *(Pestaña 4)*")
        excedente_cooperativa = st.number_input("Inyección de Utilidades desde la Cooperativa de Logística", min_value=0.0, value=excedente_coop_global)
    with col_t5_r:
        st.subheader("📐 Colocación de Crédito para Maquinaria")
        monto_credito = st.number_input("Monto por Microcrédito de Emprendimiento Popular", min_value=5000.0, value=35000.0, step=5000.0)
        tasa_social = st.slider("Tasa de Interés Activa Social Anual (%)", min_value=3, max_value=20, value=7)

    capital_mensual_total = ahorrio_barrio_mensual + comision_seguros_mensual + excedente_cooperativa
    capital_anual_total = capital_mensual_total * 12
    creditos_otorgados = int(capital_anual_total // monto_credito)
    interes_retornado_fondo = (capital_anual_total * 0.80) * (tasa_social / 100)

    f1, f2, f3 = st.columns(3)
    f1.metric("Flujo de Entrada Mensual Unificado", f"${capital_mensual_total:,.2f} MXN", delta="Tránsito Limpio de IVA")
    f2.metric("Capacidad Total del Brazo Fuerte (Anual)", f"${capital_anual_total:,.2f} MXN", delta="Independencia Bancaria")
    f3.metric("Microcréditos de Maquinaria Viables", f"{creditos_otorgados} Préstamos", delta=f"+${interes_retornado_fondo:,.2f} Crecimiento de Caja")

# ----- PESTAÑA 6: REPOSITORIO LEGAL TOTALMENTE EDITABLE -----
with tab6:
    st.header("📜 Gestor Legal de Instrumentos Jurídicos Autónomos")
    st.caption("Selecciona, consulta, edita y consolida los estatutos y contratos del ecosistema con un solo clic.")
    
    # 1. Menú interactivo de un solo clic
    opciones_docs = [
        "Sub-Acta 1: Agencia de Seguros (S.A. de C.V.)",
        "Sub-Acta 2: Cooperativa de Logística (S.C. de R.L.)",
        "Contrato 1: Corretaje Social (A.C. ── Agencia Seguros)",
        "Contrato 2: Fideicomiso Privado (A.C. ── Caja de Ahorro)"
    ]
    doc_seleccionado = st.selectbox("⚡ Selecciona el documento que deseas trabajar:", opciones_docs)
    
    # 2. Mapear la selección con las variables editables de st.session_state
    if doc_seleccionado == "Sub-Acta 1: Agencia de Seguros (S.A. de C.V.)":
        texto_inicial = st.session_state["doc_seguros"]
        key_memoria = "doc_seguros"
    elif doc_seleccionado == "Sub-Acta 2: Cooperativa de Logística (S.C. de R.L.)":
        texto_inicial = st.session_state["doc_cooperativa"]
        key_memoria = "doc_cooperativa"
    elif doc_seleccionado == "Contrato 1: Corretaje Social (A.C. ── Agencia Seguros)":
        texto_inicial = st.session_state["doc_corretaje"]
        key_memoria = "doc_corretaje"
    else:
        texto_inicial = st.session_state["doc_fideicomiso"]
        key_memoria = "doc_fideicomiso"
        
    st.markdown("### 🛠️ Editor Legal Activo")
    
    # 3. El cuadro de texto ahora es editable y actualiza la memoria del servidor de forma reactiva
    texto_editado = st.text_area(
        label=f"Modifica las cláusulas de: {doc_seleccionado}",
        value=texto_inicial,
        height=400,
        help="Cualquier cambio que realices aquí se actualizará de inmediato en los reportes del tablero."
    )
    
    # 4. Botón de guardado definitivo con un clic
    if st.button("💾 Consolidar y Guardar Cambios en el Estatuto", type="secondary"):
        st.session_state[key_memoria] = texto_editado
        st.success(f"✓ El documento '{doc_seleccionado}' ha sido actualizado con éxito en la memoria institucional de la A.C.")

# MATRIZ FINAL DE COMPORTAMIENTO CORPORATIVO
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("<div style='background-color: #d4edda; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745;'><h4 style='color: #155724; margin-top:0;'>🟢 Nodo Central: Asociación Civil</h4><p style='color: #1c7430; font-size: 14px;'><b>Función:</b> Absorción de flujos indirectos y dispersión de nómina barrial.<br><b>Estatus Fiscal:</b> 0% IVA Trasladado / Escudo del 30% ISR vía Asimilados.</p></div>", unsafe_allow_html=True)
with col_v2:
    st.markdown("<div style='background-color: #d1ecf1; padding: 15px; border-radius: 8px; border-left: 5px solid #17a2b8;'><h4 style='color: #0c5460; margin-top:0;'>🔵 Brazo Fuerte: Caja de Ahorro</h4><p style='color: #117a8b; font-size: 14px;'><b>Contrato Blanco:</b> Fideicomiso y Cuenta de Orden.<br><b>Impacto:</b> Resguarda el capital de Agua Prieta sin acumular base gravable corporativa.</p></div>", unsafe_allow_html=True)
with col_v3:
    st.markdown("<div style='background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107;'><h4 style='color: #856404; margin-top:0;'>💛 Riesgos: Agencia de Seguros</h4><p style='color: #9e7e1a; font-size: 14px;'><b>Contrato Rojo:</b> Corretaje Social (Retorno del 20%).<br><b>Impacto:</b> Transforma primas comerciales de la S.A. en fondos limpios para el desarrollo popular.</p></div>", unsafe_allow_html=True)
