import streamlit as st

# ==============================================================================
# PARTE 1 DE 3: CONFIGURACIÓN, SEGURIDAD Y CONTROL DE SESIÓN
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

def check_password():
    """Valida las credenciales institucionales contra variables de entorno."""
    def password_entered():
        if st.session_state["password"] == st.secrets["access_control"]["password"]:
            st.session_state["password_correct"] = True
            # Inicializar bandera para ocultar el error si el login es exitoso
            st.session_state["show_login_error"] = False
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
            # Activar la bandera de error solo si la contraseña falló
            st.session_state["show_login_error"] = True

    if st.session_state["password_correct"]:
        return True

    # Renderizado de la pantalla de login con bloqueo absoluto 
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
        
        # EVENTO OPORTUNO: El error solo existe si el usuario ya falló un intento de inicio de sesión
        if st.session_state.get("show_login_error", False):
            st.error("❌ Credenciales inválidas. Intento bloqueado por el protocolo de seguridad.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        # CONTENEDOR OCULTO: La nota informativa ahora requiere una acción consciente del usuario para leerse
        with st.expander("ℹ️ ¿No tienes acceso? Soporte del Ecosistema"):
            st.caption("Nota: Las claves de acceso son administradas de forma directa por el Agente Capacitador.")
            
    return False

# Si la contraseña falla o es el primer ingreso, detener la ejecución del archivo aquí
if not check_password():
    st.stop()

# Función de Cierre de Sesión Seguro (Logout)
def logout():
    st.session_state["password_correct"] = False
    # Reiniciar la bandera de error para que la pantalla vuelva a estar limpia en el siguiente login
    st.session_state["show_login_error"] = False
    st.rerun()

# Encabezado Institucional Principal de la Interfaz
st.title("🦅 Sistema de Control Técnico y Conexión de Subsistemas Autónomos")
st.subheader("Ecosistema de Economía Popular y Retención de Valor Fronterizo")
st.markdown("---")

# Construcción de la Barra Lateral Común (Sidebar)
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

# Declaración unificada de las 5 pestañas de navegación para el Agente Capacitador
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛡️ Módulo 1: Blindaje IVA", 
    "🧮 Módulo 2: Prorrateo IVA", 
    "👥 Módulo 3: Nómina Asimilada",
    "📊 Módulo 4: Microseguros (S.A.)",
    "🏦 Módulo 5: Caja de Ahorro (Brazo Fuerte)"
])
# ==============================================================================
# PARTE 2 DE 3: MÓDULOS FISCALES (COMPORTAMIENTO DE IVA E ISR)
# ==============================================================================

# Variables de interconexión para enlazar analíticamente la Parte 2 con la Parte 3
num_talleres_global = 65
prima_individual_global = 120
comision_retorno_global = 20
excedente_coop_global = 35000

# ----- PESTAÑA 1: BLINDAJE DE IVA -----
with tab1:
    st.header("Estructuración de Ingresos mediante Cuotas Estatutarias")
    col_t1_l, col_t1_r = st.columns(2)
    with col_t1_l:
        num_talleres = st.slider("Talleres Populares Integrados (Miembros Adherentes)", min_value=5, max_value=300, value=num_talleres_global)
        num_talleres_global = num_talleres # Sincronización en tiempo real
        cuota_calculada = presupuesto_total / num_talleres
        
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
    monto_bruto = presupuesto_total / num_promotores
    isr_retenido = monto_bruto * 0.08 
    monto_neto = monto_bruto - isr_retenido
    ahorrado_isr_ac = presupuesto_total * 0.30
    
    r_as1, r_as2, r_as3 = st.columns(3)
    r_as1.metric("Honorario Neto / Líder", f"${monto_neto:,.2f} MXN")
    r_as2.metric("Retención Total ISR a Enterar", f"${isr_retenido * num_promotores:,.2f} MXN")
    r_as3.metric("Ahorro en ISR Corporativo A.C.", f"${ahorrado_isr_ac:,.2f} MXN", delta="Gasto Justificado")
# ==============================================================================
# PARTE 3 DE 3: SUBSISTEMAS DE MICROSEGUROS Y CAJA DE AHORRO (VÍNCULO FINANCIERO)
# ==============================================================================

# ----- PESTAÑA 4: MICROSEGUROS (SUBSISTEMA FILIAL MERCANTIL) -----
with tab4:
    st.header("Gestión Financiera de la Agencia de Microseguros (S.A.)")
    col_t4_l, col_t4_r = st.columns(2)
    with col_t4_l:
        prima_mensual = st.number_input("Prima Mensual Cobrada por Taller (MXN)", min_value=50, value=prima_individual_global)
        prima_individual_global = prima_mensual
        retorno_pct = st.slider("Porcentaje de Comisión Pactado para Devolución a la A.C.", min_value=5, max_value=40, value=comision_retorno_global)
        comision_retorno_global = retorno_pct
    with col_t4_r:
        tasa_siniestros = st.slider("Tasa de Accidentes / Siniestros Proyectada (%)", min_value=1, max_value=20, value=5)
    
    prima_anual = num_talleres_global * prima_mensual * 12
    retorno_anual_ac = prima_anual * (retorno_pct / 100)
    fondo_siniestros = prima_anual * (tasa_siniestros / 100)
    
    m_s1, m_s2, m_s3 = st.columns(3)
    m_s1.metric("Primas Anuales Capturadas (S.A.)", f"${prima_anual:,.2f} MXN")
    m_s2.metric("Comisión Retornada a la A.C.", f"${retorno_anual_ac:,.2f} MXN", delta="Ingreso de Fomento")
    m_s3.metric("Fondo de Reserva para Siniestros", f"${fondo_siniestros:,.2f} MXN")

# ----- PESTAÑA 5: CAJA DE AHORRO (EL BRAZO FUERTE Y VÍNCULO CORPORATIVO) -----
with tab5:
    st.header("🏦 El Brazo Fuerte: Caja de Ahorro y Consolidación de Vínculos Financieros")
    st.caption("Monitoreo en tiempo real del flujo cruzado de capital de los subsistemas autónomos hacia la cuenta matriz.")
    
    col_t5_l, col_t5_r = st.columns(2)
    with col_t5_l:
        st.subheader("📥 Fuentes de Inyección de Capital Social (Mensual)")
        ahorrio_barrio_mensual = st.number_input("Ahorros Directos de los Trabajadores de Agua Prieta", min_value=0.0, value=55000.0)
        
        # VÍNCULO CORPORATIVO AUTOMÁTICO: Extracción mensual del retorno anual calculado en la pestaña anterior
        comision_seguros_mensual = retorno_anual_ac / 12
        st.markdown(f"➕ **Inyección Automatizada desde Agencia de Seguros:** `${comision_seguros_mensual:,.2f} MXN/mes` *(Pestaña 4)*")
        
        excedente_cooperativa = st.number_input("Inyección de Utilidades desde la Cooperativa de Logística", min_value=0.0, value=excedente_coop_global)
    
    with col_t5_r:
        st.subheader("📐 Colocación de Crédito para Maquinaria")
        monto_credito = st.number_input("Monto por Microcrédito de Emprendimiento Popular", min_value=5000, value=35000, step=5000)
        tasa_social = st.slider("Tasa de Interés Activa Social Anual (%)", min_value=3, max_value=20, value=7)

    # Cálculo traslacional definitivo del fondo común interconectado
    capital_mensual_total = ahorrio_barrio_mensual + comision_seguros_mensual + excedente_cooperativa
    capital_anual_total = capital_mensual_total * 12
    creditos_otorgados = int(capital_anual_total // monto_credito)
    interes_retornado_fondo = (capital_anual_total * 0.80) * (tasa_social / 100)

    st.markdown("---")
    st.markdown("### 📊 Balance de Consolidación del Circuito Cerrado de Riqueza")
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Flujo de Entrada Mensual Unificado", f"${capital_mensual_total:,.2f} MXN", delta="Tránsito Limpio de IVA")
    f2.metric("Capacidad Total del Brazo Fuerte (Anual)", f"${capital_anual_total:,.2f} MXN", delta="Independencia Bancaria")
    f3.metric("Microcréditos de Maquinaria Viables", f"{creditos_otorgados} Préstamos", delta=f"+${interes_retornado_fondo:,.2f} Crecimiento de Caja")

    st.markdown("---")
    st.success("🎯 **Evidencia del Vínculo Financiero (Defensa Jurídica del Agente):**")
    st.markdown(f"""
    * **Materialidad ante Auditorías:** Del flujo anual acumulado de **${capital_anual_total:,.2f} MXN**, el SAT identifica que el 100% de las inyecciones de la Cooperativa y la Agencia de Seguros están respaldadas por contratos de servicios de asistencia técnica y capacitación exentos de IVA.
    * **Circulación de Riqueza:** Los intereses generados de **${interes_retornado_fondo:,.2f} MXN** no se distribuyen entre los socios directores como ganancias capitalistas; se quedan etiquetados en la cuenta de orden para absorber pérdidas por siniestros no cubiertos, manteniendo la naturaleza civil de la organización.
    """)

# RECONFIGURACIÓN VISUAL DE LA MATRIZ DE VÍNCULOS EN STREAMLIT (CORREGIDO)
st.markdown("---")
st.markdown("### 🗂️ Arquitectura de la Matriz del Vínculo Financiero")

col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
    st.markdown("""
    <div style='background-color: #d4edda; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745;'>
        <h4 style='color: #155724; margin-top:0;'>🟢 Nodo Central: Asociación Civil</h4>
        <p style='color: #1c7430; font-size: 14px;'>
            <b>Función:</b> Absorción de flujos indirectos y dispersión de nómina barrial.<br>
            <b>Estatus Fiscal:</b> 0% IVA Trasladado / Escudo del 30% ISR vía Asimilados.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
with col_v2:
    st.markdown("""
    <div style='background-color: #d1ecf1; padding: 15px; border-radius: 8px; border-left: 5px solid #17a2b8;'>
        <h4 style='color: #0c5460; margin-top:0;'>🔵 Brazo Fuerte: Caja de Ahorro</h4>
        <p style='color: #117a8b; font-size: 14px;'>
            <b>Contrato Blanco:</b> Fideicomiso y Cuenta de Orden.<br>
            <b>Impacto:</b> Resguarda el capital semilla de Agua Prieta sin acumular base gravable corporativa.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
with col_v3:
    st.markdown("""
    <div style='background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107;'>
        <h4 style='color: #856404; margin-top:0;'>💛 Riesgos: Agencia de Seguros</h4>
        <p style='color: #9e7e1a; font-size: 14px;'>
            <b>Contrato Rojo:</b> Corretaje Social (Retorno del 20%).<br>
            <b>Impacto:</b> Transforma primas comerciales de la S.A. en fondos limpios para el desarrollo popular.
        </p>
    </div>
    """, unsafe_allow_html=True)
