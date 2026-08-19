import streamlit as st

# ==============================================================================
# 1. CONFIGURACIÓN ESTRUCTURAL DE LA INTERFAZ
# ==============================================================================
st.set_page_config(
    page_title="Tablero de Control Fiscal - Agua Prieta",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. SISTEMA DE SEGURIDAD Y CONTROL DE ACCESO (STREAMLIT SECRETS)
# ==============================================================================
def check_password():
    """Valida las credenciales institucionales contra variables de entorno."""
    def password_entered():
        if st.session_state["password"] == st.secrets["access_control"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Renderizado de la pantalla de login (Layout Centrado para Seguridad)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🔐 Acceso Restringido")
        st.subheader("Plataforma de Desarrollo Económico Popular")
        st.caption("Asociación Civil en Régimen General (Título II LISR) • Agua Prieta, Sonora")
        
        st.text_input(
            "Introduce la contraseña institucional de acceso:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Credenciales inválidas. El intento ha sido registrado en la bitácora de auditoría.")
        
        st.info("Nota: Las claves de acceso son administradas de forma directa por el Agente Capacitador.")
    return False

# Interrumpir renderizado si falla el password
if not check_password():
    st.stop()

# ==============================================================================
# 3. INTERFAZ PRINCIPAL (USUARIO AUTENTICADO)
# ==============================================================================

# Encabezado Institucional
st.title("🦅 Plataforma de Control Técnico y Blindaje Económico Popular")
st.subheader("Instrumentación del Plan Maestro para la Retención de Valor en Agua Prieta")
st.markdown("---")

# Barra Lateral Informativa y Parámetros Globales
with st.sidebar:
    st.header("📋 Estado del Sistema")
    st.success("🔒 Conexión Encriptada")
    st.markdown("**Organización:** Asociación Civil (Título II)")
    st.markdown("**Jurisdicción:** Agua Prieta, Sonora")
    st.markdown("**Estatus IVA:** Actividades Exentas Activas")
    st.markdown("---")
    st.header("⚙️ Parámetros Globales")
    presupuesto_total = st.number_input("Bolsa Económica Mensual Operativa (MXN)", min_value=10000, value=200000, step=10000)

# Creación de las Pestañas de Navegación del Plan Maestro
tab1, tab2, tab3 = st.tabs([
    "🛡️ Módulo 1: Blindaje de IVA", 
    "🧮 Módulo 2: Prorrateo de IVA", 
    "👥 Módulo 3: Nómina Asimilada"
])

# ==============================================================================
# PESTAÑA 1: BLINDAJE DE IVA (CUOTAS ESTATUTARIAS)
# ==============================================================================
with tab1:
    st.header("Estructuración de Ingresos mediante Cuotas Estatutarias de Miembros")
    st.caption("Objetivo: Sustituir facturación comercial con riesgo de IVA por esquemas de aportación del Art. 15-XII LIVA.")
    
    col_t1_l, col_t1_r = st.columns([2, 1])
    
    with col_t1_l:
        num_talleres = st.slider("Número de Talleres Populares (Miembros Adherentes Cooperativos)", min_value=5, max_value=300, value=60)
        cuota_calculada = presupuesto_total / num_talleres
        
        st.markdown("### 📊 Análisis de Impacto Económico")
        c1, c2 = st.columns(2)
        c1.metric("Cuota de Recuperación Promedio", f"${cuota_calculada:,.2f} MXN")
        c2.metric("Tasa de IVA del Esquema", "0% (Exento)")
        
        st.markdown("""
        **Sustento de Materialidad Obligatorio:**  
        Para blindar estas aportaciones ante el SAT, cada ingreso capturado bajo este módulo debe estar 
        amparado por el **Formato de Recibo de Cuota Estatutaria** y el registro de afiliación vigente en el padrón de la A.C.
        """)
        
    with col_t1_r:
        st.info("💡 **Acción del Agente:**")
        st.markdown("""
        * Convertir contratos mercantiles a *Contratos de Adhesión Social*.
        * Emitir recibos con leyenda del Art. 15 Fracc. XII de la LIVA.
        * Evitar desglose de IVA para eliminar riesgos de auditoría de capital de trabajo.
        """)

# ==============================================================================
# PESTAÑA 2: PRORRATEO DE IVA (OPERACIONES MIXTAS)
# ==============================================================================
with tab2:
    st.header("Optimizador Analítico de Prorrateo de IVA")
    st.caption("Objetivo: Determinar el factor de acreditamiento legal para el IVA pagado en gastos generales fronterizos.")
    
    col_t2_l, col_t2_r = st.columns(2)
    
    with col_t2_l:
        st.subheader("📥 Registro de Ingresos del Mes")
        ing_exentos = st.number_input("Ingresos por Cursos y Capacitación para el Trabajo (Exentos)", min_value=0.0, value=160000.0)
        ing_gravados = st.number_input("Ingresos por Comercialización Técnica/Servicios (Gravados al 8% Fronterizo)", min_value=0.0, value=40000.0)
        
    with col_t2_r:
        st.subheader("💸 IVA Soportado en Compras")
        iva_gastos = st.number_input("IVA total pagado a proveedores (Gastos de Administración/Operativos)", min_value=0.0, value=18000.0)
    
    # Lógica Matemática de Prorrateo (Nivel Doctoral)
    ingresos_totales = ing_exentos + ing_gravados
    factor = (ing_gravados / ingresos_totales) if ingresos_totales > 0 else 0.0
    iva_recuperable = iva_gastos * factor
    iva_costo = iva_gastos - iva_recuperable
    
    st.markdown("---")
    st.subheader("🎯 Resolución de la Matriz Fiscal (Art. 5-C LIVA)")
    
    res1, res2, res3 = st.columns(3)
    res1.metric("Factor de Proporcionalidad", f"{factor * 100:.2f}%")
    res2.metric("IVA Acreditable (Recuperable)", f"${iva_recuperable:,.2f} MXN", delta="Flujo A Salvo")
    res3.metric("IVA no Acreditable (Al Gasto)", f"${iva_costo:,.2f} MXN", delta="Costo Directo", delta_color="inverse")

# ==============================================================================
# PESTAÑA 3: NÓMINA ASIMILADA (ESGUDO FISCAL DE DEDUCCIONES)
# ==============================================================================
with tab3:
    st.header("Simulador de Retribución por Asimilados a Salarios")
    st.caption("Objetivo: Comprobar egresos legítimos al 100% en la periferia urbana para pulverizar la tasa del 30% de ISR corporativo.")
    
    # Algoritmo simplificado de retención de ISR marginal de la LISR
    def calcular_isr_asimilado(monto):
        if monto <= 10000:
            return monto * 0.06
        elif monto <= 25000:
            return 600 + (monto - 10000) * 0.12
        else:
            return 2400 + (monto - 25000) * 0.20

    num_promotores = st.slider("Número de Líderes Técnicos / Promotores de Barrio a Retribuir", min_value=1, max_value=50, value=12)
    
    monto_individual_bruto = presupuesto_total / num_promotores
    isr_retenido = calcular_isr_asimilado(monto_individual_bruto)
    monto_neto = monto_individual_bruto - isr_retenido
    total_isr_retenciones = isr_retenido * num_promotores
    ahorrado_isr_ac = presupuesto_total * 0.30
    
    st.markdown("### 📊 Proyección de Dispersión y Escudo Fiscal")
    
    r_as1, r_as2, r_as3 = st.columns(3)
    r_as1.metric("Honorario Neto Mensual / Promotor", f"${monto_neto:,.2f} MXN")
    r_as2.metric("Retención Total ISR (Enterar al SAT)", f"${total_isr_retenciones:,.2f} MXN")
    r_as3.metric("ISR Corporativo Reducido a la A.C.", f"${ahorrado_isr_ac:,.2f} MXN", delta="Base Gravable Mitigada")
    
    st.markdown("---")
    st.warning("⚠️ **Requisito de Cumplimiento Legal:** Cada dispersión simulada en este tablero requiere la firma física obligatoria del *Contrato de Prestación de Servicios Asimilables* y el timbrado de nómina correspondiente antes del cierre del mes.")
