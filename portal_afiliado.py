import pandas as pd
import psycopg
from psycopg.rows import dict_row
import streamlit as st


def _get_conn_portal():
    db_url = ""
    if "SUPABASE_DB_URL" in st.secrets:
        db_url = str(st.secrets["SUPABASE_DB_URL"]).strip()
    elif "postgres" in st.secrets and "url" in st.secrets["postgres"]:
        db_url = str(st.secrets["postgres"]["url"]).strip()
    if not db_url:
        return None
    if "sslmode=" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
    return psycopg.connect(db_url)


def render_portal_socio_afiliado(affiliate_user: str):
    """Panel completo del Socio Afiliado: alumnos inscritos, comisiones cobradas/por cobrar y calculadora."""
    conn = _get_conn_portal()
    if not conn:
        st.error("❌ Sin conexión activa a Supabase PostgreSQL.")
        return

    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM affiliate_partners WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s)) LIMIT 1;",
                (affiliate_user,)
            )
            perfil = cur.fetchone()

            cur.execute("""
                SELECT usuario AS "Estudiante", nivel AS "Nivel CEFR",
                       fecha_inicio_curso AS "Fecha Inicio",
                       mensualidad_base AS "Mensualidad Base ($)",
                       aplicar_iva AS "Con IVA",
                       porcentaje_comision AS "Comisión Asignada (%)",
                       estatus AS "Estatus Alumno"
                FROM users_padron
                WHERE LOWER(TRIM(afiliado_usuario)) = LOWER(TRIM(%s))
                ORDER BY usuario ASC;
            """, (affiliate_user,))
            estudiantes = [dict(r) for r in cur.fetchall()]

            cur.execute("""
                SELECT student_user AS "Estudiante", ciclo_numero AS "Ciclo",
                       monto_pagado AS "Monto Pagado ($)", porcentaje_aplicado AS "Comisión (%)",
                       comision_ganada AS "Comisión ($)", estatus_pago_comision AS "Estatus",
                       TO_CHAR(created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD') AS "Fecha Registro"
                FROM affiliate_commissions
                WHERE LOWER(TRIM(affiliate_user)) = LOWER(TRIM(%s))
                ORDER BY created_at DESC;
            """, (affiliate_user,))
            comisiones = [dict(r) for r in cur.fetchall()]

    pct_asignado = (
        float(perfil["porcentaje_default"])
        if perfil and perfil.get("porcentaje_default") is not None
        else (float(estudiantes[0]["Comisión Asignada (%)"]) if estudiantes else 10.0)
    )
    total_cobradas = round(sum(float(c["Comisión ($)"]) for c in comisiones if str(c["Estatus"]).lower() in ["pagado", "cobrada", "liquidado"]), 2)
    total_por_cobrar = round(sum(float(c["Comisión ($)"]) for c in comisiones if str(c["Estatus"]).lower() not in ["pagado", "cobrada", "liquidado"]), 2)
    total_historico = round(total_cobradas + total_por_cobrar, 2)

    st.markdown(f"## 🤝 Portal Oficial del Socio Afiliado: `{affiliate_user}`")
    if perfil:
        st.caption(
            f"**Titular:** {perfil.get('nombre', '')} {perfil.get('apellido_paterno', '')} {perfil.get('apellido_materno', '')}  |  "
            f"**Estatus:** `{perfil.get('estatus', 'Activo')}`  |  **Ingreso:** `{perfil.get('fecha_ingreso', '')}`  |  "
            f"**Comisión Base Asignada:** `{pct_asignado:.2f}%`"
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎓 Estudiantes Inscritos", len(estudiantes))
    m2.metric("⏳ Comisiones Por Cobrar", f"${total_por_cobrar:,.2f} MXN")
    m3.metric("✅ Comisiones Cobradas", f"${total_cobradas:,.2f} MXN")
    m4.metric("💰 Acumulado Histórico", f"${total_historico:,.2f} MXN")

    st.divider()
    tab_est, tab_com, tab_calc = st.tabs([
        "🎓 Mis Estudiantes Inscritos",
        "💵 Estado de Comisiones (Cobradas / Por Cobrar)",
        "🧮 Calculadora de Proyección de Comisiones"
    ])

    with tab_est:
        if estudiantes:
            st.dataframe(pd.DataFrame(estudiantes), width="stretch", hide_index=True)
        else:
            st.info("Aún no tienes estudiantes inscritos bajo tu código de afiliado.")

    with tab_com:
        if comisiones:
            df_c = pd.DataFrame(comisiones)
            filtro_st = st.radio("Filtrar por estatus:", ["Todas", "Por Cobrar (Pendiente)", "Cobradas (Pagado)"], horizontal=True)
            if filtro_st == "Por Cobrar (Pendiente)":
                df_c = df_c[df_c["Estatus"].str.lower() == "pendiente"]
            elif filtro_st == "Cobradas (Pagado)":
                df_c = df_c[df_c["Estatus"].str.lower() != "pendiente"]
            st.dataframe(df_c, width="stretch", hide_index=True)
        else:
            st.info("Aún no hay movimientos de comisiones registrados.")

    with tab_calc:
        st.markdown("#### 🧮 Simulador de Ingresos por Estudiantes Inscritos")
        st.caption("Calcula tus comisiones proyectadas con base en tu porcentaje asignado por el instituto y la mensualidad vigente.")
        cc1, cc2, cc3 = st.columns(3)
        cant_alumnos = cc1.number_input("Cantidad de Estudiantes Inscritos:", min_value=1, max_value=500, value=max(1, len(estudiantes)), step=1)
        mensualidad_vig = cc2.number_input("Mensualidad Vigente por Estudiante ($ MXN):", min_value=100.0, value=1500.0, step=100.0)
        pct_sim = cc3.number_input("Tu Porcentaje Asignado (%):", min_value=0.0, max_value=100.0, value=pct_asignado, step=0.5, disabled=True)

        comision_por_alumno = round(mensualidad_vig * (pct_sim / 100.0), 2)
        ingreso_mensual_est = round(comision_por_alumno * cant_alumnos, 2)
        ingreso_semestral_est = round(ingreso_mensual_est * 6, 2)

        r1, r2, r3 = st.columns(3)
        r1.metric("💵 Comisión por Estudiante / Mes", f"${comision_por_alumno:,.2f} MXN")
        r2.metric("📅 Proyección Mensual Total", f"${ingreso_mensual_est:,.2f} MXN")
        r3.metric("🏆 Proyección Semestral (6 Meses)", f"${ingreso_semestral_est:,.2f} MXN")


if __name__ == "__main__":
    import hashlib

    st.set_page_config(page_title="Portal Socio Afiliado — CEI", page_icon="🤝", layout="wide")

    if "aff_logged_user" not in st.session_state:
        st.session_state.aff_logged_user = ""

    if not st.session_state.aff_logged_user:
        col_l1, col_l2, col_l3 = st.columns([1, 1.4, 1])
        with col_l2:
            st.markdown("## 🤝 Career English Institute")
            st.markdown("#### 🔐 Acceso Exclusivo — Portal de Socios Afiliados")
            st.caption("Ingresa con tu usuario y contraseña asignados por la administración.")

            with st.form("login_aff_standalone", clear_on_submit=False):
                u_in = st.text_input("👤 Usuario de Afiliado:", placeholder="Ej. Carlos Mendoza")
                p_in = st.text_input("🔑 Contraseña:", type="password", placeholder="••••••••")
                entrar = st.form_submit_button("Ingresar al Portal", type="primary", width="stretch")

                if entrar:
                    if not u_in.strip() or not p_in.strip():
                        st.warning("⚠️ Ingresa tu usuario y contraseña.")
                    else:
                        conn_l = _get_conn_portal()
                        if not conn_l:
                            st.error("❌ Sin conexión con la base de datos institucional.")
                        else:
                            try:
                                p_sha = hashlib.sha256(p_in.strip().encode("utf-8")).hexdigest()
                                with conn_l:
                                    with conn_l.cursor() as cur:
                                        cur.execute("""
                                            SELECT usuario FROM users_padron
                                            WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s))
                                              AND (clave_hash = %s OR clave_hash = %s)
                                              AND LOWER(TRIM(rol)) IN ('socio afiliado', 'afiliado', 'affiliate')
                                              AND LOWER(TRIM(estatus)) = 'activo'
                                            LIMIT 1;
                                        """, (u_in, p_in.strip(), p_sha))
                                        row_u = cur.fetchone()
                                        if row_u:
                                            st.session_state.aff_logged_user = next(iter(row_u), u_in.strip())
                                            st.rerun()
                                        else:
                                            st.error("❌ Credenciales incorrectas o cuenta de Socio Afiliado inactiva.")
                            except Exception as e_log:
                                st.error(f"Error al validar acceso: {e_log}")
    else:
        col_top1, col_top2 = st.columns([5, 1])
        with col_top1:
            st.caption(f"Sesión activa: **{st.session_state.aff_logged_user}** | Portal de Socios Afiliados CEI")
        with col_top2:
            if st.button("🚪 Cerrar Sesión", width="stretch"):
                st.session_state.aff_logged_user = ""
                st.rerun()

        render_portal_socio_afiliado(st.session_state.aff_logged_user)

