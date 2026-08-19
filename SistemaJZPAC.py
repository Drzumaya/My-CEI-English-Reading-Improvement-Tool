import streamlit as st

st.set_page_config(page_title="Blindaje de IVA - AC", page_icon="🛡️")

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
