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
    st.caption("Gestión estratégica de JZPAC.")
    
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
st.title("🛡️ Sistema de Gestión de Cuotas Estatutarias)")
# ... (deja el resto de tu código exactamente igual)
import streamlit as st

st.set_page_config(page_title="Matriz Prorrateo IVA", page_icon="🧮")

st.title("🧮 Optimizador de Prorrateo de IVA (Art. 5-C LIVA)")
st.caption("Intervención 2: Maximización de Deducciones en Operaciones Mixtas - Región Fronteriza")

st.markdown("""
Cuando la A.C. factura servicios exentos y gravados (estímulo del 8% norte), el IVA de los gastos generales 
debe prorratearse. Este sistema determina qué porcentaje del IVA pagado en Agua Prieta puedes recuperar.
""")

col_in1, col_in2 = st.columns(2)

with col_in1:
    st.subheader("📥 Ingresos del Período")
    ing_exentos = st.number_input("Ingresos por Capacitación (Exentos)", min_value=0.0, value=120000.0)
    ing_gravados = st.number_input("Ingresos por Venta de Productos (Gravados 8%)", min_value=0.0, value=30000.0)

with col_in2:
    st.subheader("💸 IVA Pagado en Gastos (Gastos Generales)")
    iva_gastos_generales = st.number_input("IVA total pagado a proveedores (16% o 8%)", min_value=0.0, value=15000.0)

# Algoritmo de Prorrateo (Nivel Doctoral)
ingresos_totales = ing_exentos + ing_gravados

if ingresos_totales > 0:
    factor_proporcionalidad = ing_gravados / ingresos_totales
else:
    factor_proporcionalidad = 0.0

iva_acreditable_directo = iva_gastos_generales * factor_proporcionalidad
iva_absorbido_como_gasto = iva_gastos_generales - iva_acreditable_directo

st.subheader("🎯 Resultados de la Determinación de IVA")

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.metric("Factor de Acreditamiento", f"{factor_proporcionalidad * 100:.2f}%")
with col_r2:
    st.metric("IVA Recuperable/Acreditable", f"${iva_acreditable_directo:,.2f} MXN")
with col_r3:
    st.metric("IVA al Gasto (Deducible ISR)", f"${iva_absorbido_como_gasto:,.2f} MXN")

st.subheader("💡 Recomendación de Gobernanza Financiera")
if factor_proporcionalidad < 0.20:
    st.warning(f"Tu factor es bajo ({factor_proporcionalidad*100:.1f}%). El IVA pagado se está convirtiendo en costo operativo directo. El agente debe acelerar proyectos productivos gravados para equilibrar la balanza de flujo.")
else:
    st.success("Proporcionalidad óptima. Estás logrando recuperar una parte significativa del flujo de efectivo a través del acreditamiento fiscal.")
