import streamlit as st

# 1. Configuración de página obligatoria al inicio
st.set_page_config(page_title="Sistema de Control - Agua Prieta", page_icon="🔐", layout="centered")

# 2. Función de verificación de contraseña
def check_password():
    """Devuelve True si el usuario ingresó la contraseña correcta."""
    def password_entered():
        """Comprueba si la contraseña ingresada coincide con el secreto guardado."""
        # Se compara el texto del input con los Secrets internos de Streamlit
        if st.session_state["password"] == st.secrets["access_control"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Elimina la contraseña de la memoria por seguridad
        else:
            st.session_state["password_correct"] = False

    # Si ya se validó previamente en la sesión, saltar el login
    if st.session_state.get("password_correct", False):
        return True

    # Renderizar el formulario de inicio de sesión
    st.title("🔐 Acceso Restringido - Agente Capacitador")
    st.subheader("Sistema Integral de Desarrollo Económico Popular (Agua Prieta)")
    st.caption("Esta plataforma contiene datos fiscales y estratégicos de la A.C. en Régimen General.")
    
    st.text_input(
        "Introduce la contraseña de acceso institucional:",
        type="password",
        on_change=password_entered,
        key="password",
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("❌ Contraseña incorrecta. Por favor, verifica tus credenciales institucionales.")
    
    return False

# 3. Interrumpir la ejecución si la contraseña no es válida
if not check_password():
    st.stop()  # Detiene el script aquí. Nada de abajo se mostrará.

# ==============================================================================
# EL CÓDIGO ANTERIOR DE TU APLICACIÓN CONTINÚA AQUÍ ABAJO (A partir de st.title, etc.)
# ==============================================================================
st.title("🛡️ Sistema de Gestión de Cuotas Estatutarias (Exención IVA)")
# ... (deja el resto de tu código exactamente igual)
import streamlit as st

st.set_page_config(page_title="Asimilados Comunitarios", page_icon="👥")

st.title("👥 Simulador de Asimilados a Salarios con Impacto Comunitario")
st.caption("Intervención 3: Blindaje de Egresos y Pulverización del 30% de ISR Corporativo")

st.markdown("""
Las A.C. en Régimen General pagan 30% de ISR sobre remanentes. Este módulo calcula cómo formalizar los pagos 
a capacitadores barriales sin CFDI propio, convirtiéndolos en **Deducciones Autorizadas al 100%**.
""")

# Tarifa simplificada ISR mensual 2026 (Abstracción analítica para simulación)
def calcular_isr_asimilado(monto):
    # Lógica simplificada de cálculo de impuesto retenido sobre la base popular
    if monto <= 8000:
        return monto * 0.05
    elif monto <= 15000:
        return 400 + (monto - 8000) * 0.10
    else:
        return 1100 + (monto - 15000) * 0.17

st.subheader("💼 Datos del Fondo de Retribución Popular")
monto_total_repartir = st.number_input("Bolsa Económica Mensual para Promotores Populares (MXN)", min_value=10000, value=80000, step=5000)
num_promotores = st.slider("Número de Asesores de Barrio a Contratar", min_value=1, max_value=30, value=8)

pago_bruto_individual = monto_total_repartir / num_promotores
isr_retener_individual = calcular_isr_asimilado(pago_bruto_individual)
pago_neto_individual = pago_bruto_individual - isr_retener_individual
isr_total_retencion = isr_retener_individual * num_promotores

# Impacto en la AC
impuesto_ahorrado_ac = monto_total_repartir * 0.30

st.subheader("📉 Impacto Financiero y Social de la Nómina Asimilada")

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Pago Neto / Líder de Barrio", f"${pago_neto_individual:,.2f} MXN")
with col_b:
    st.metric("ISR Retenido (Enterar al SAT)", f"${isr_total_retencion:,.2f} MXN")
with col_c:
    st.metric("ISR Corporativo Reducido (30%)", f"${impuesto_ahorrado_ac:,.2f} MXN", delta="Ahorro Fiscal A.C.")

st.subheader("🛠️ Estructuración Legal Recomendada")
st.markdown(f"""
Al ejecutar esta estrategia, el agente capacitador consolida un **escudo fiscal perfecto**:
* **Cero Riesgo de Discrepancia:** Los **${monto_total_repartir:,.2f} MXN** salen de la cuenta bancaria de la A.C. amparados por un CFDI de nómina (asimilados) timbrado internamente.
* **Reducción de Utilidad Artificial:** Al reportar este gasto, evitas pagar **${impuesto_ahorrado_ac:,.2f} MXN** directos de impuesto sobre la renta corporativo al final del año.
* **Gobernanza:** Es indispensable recabar las firmas del contrato de prestación de servicios asimilables y las listas de asistencia firmadas por los alumnos de los barrios de Agua Prieta para demostrar la materialidad del gasto.
""")
