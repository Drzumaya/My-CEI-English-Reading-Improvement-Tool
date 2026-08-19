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

st.set_page_config(page_title="Mantenimiento - AC", page_icon="🛡️")

st.title("🛡️ Sistema de Gestión de Cuotas Estatutarias (Exención IVA)")
st.caption("Intervención 1: Estructuración de Ingresos de Base Popular - Nivel Doctoral")

st.markdown("""
Este módulo evalúa la transición fiscal de cobros comerciales (riesgo de IVA 16%) 
a **Cuotas de Recuperación de Miembros Adherentes** (Exentas de IVA Art. 15-XII LIVA), 
aplicado a los talleres populares de Agua Prieta.
""")

with st.sidebar:
    st.header("⚙️ Parámetros de Operación")
    ingreso_mensual = st.number_input("Ingreso Proyectado Mensual (MXN)", min_value=10000, value=150000, step=10000)
    num_miembros = st.slider("Número de Talleres/Miembros Adherentes", min_value=5, max_value=200, value=45)
    riesgo_auditoria = st.checkbox("¿Existen contratos comerciales previos?", value=True)

# Cálculos Fiscales
iva_comercial_mensual = ingreso_mensual * 0.16
iva_anual_riesgo = iva_comercial_mensual * 12
cuota_promedio = ingreso_mensual / num_miembros

st.subheader("📊 Análisis de Riesgo y Optimización Fiscal")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Cuota Promedio / Miembro", f"${cuota_promedio:,.2f} MXN")
with col2:
    st.metric("IVA Contingente Evitado (Anual)", f"${iva_anual_riesgo:,.2f} MXN", delta="Protegido", delta_color="inverse")
with col3:
    st.metric("Tasa de IVA Bajo Esquema AC", "0% (Exento)")

st.subheader("📋 Acciones de Implementación para el Agente Capacitador")
st.info("Para validar legalmente este esquema ante el SAT, el agente debe generar de inmediato:")

st.markdown(f"""
1. **Acta de Asamblea Extraordinaria:** Modificación del reglamento interno de la A.C. para admitir la figura de *Miembros Adherentes Cooperativos* de Agua Prieta.
2. **Contrato de Adhesión Social:** Sustituir toda factura comercial por la emisión de comprobantes de aportación institucional (sin desglose de IVA).
3. **Estructura de Costeo:** Las cuotas mensuales promedio de **${cuota_promedio:,.2f} MXN** deben estar estrictamente vinculadas al presupuesto de egresos de capacitación y fomento económico, garantizando remanente distribuible igual a cero.
""")
