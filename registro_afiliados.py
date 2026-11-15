import base64
from datetime import date
import random
import psycopg
import streamlit as st


def _get_conn_afiliados():
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


def render_formulario_registro_afiliado(registrado_por: str = "Sistema", key_prefix: str = "aff_reg"):
    """Formulario completo de expediente de Socio Afiliado con ID único vinculado a Supabase PostgreSQL."""
    st.markdown("### 🤝 Registro Oficial de Socio Afiliado — Career English Institute")
    st.caption("Expediente institucional vinculado en tiempo real a Supabase PostgreSQL.")

    id_sugerido = f"AFIL-CEI-{date.today().year}-{random.randint(1000, 9999)}"

    with st.form(f"{key_prefix}_form", clear_on_submit=True):
        c_id1, c_id2 = st.columns([1.2, 1.8])
        affiliate_id = c_id1.text_input("🆔 ID de Socio Afiliado *", value=id_sugerido, help="Identificador único institucional del socio afiliado.")
        usuario_login = c_id2.text_input("👤 Usuario de Acceso a Plataforma *", placeholder="Ej. Carlos Mendoza")

        c1, c2, c3 = st.columns(3)
        nombre = c1.text_input("Nombre(s) *", placeholder="Ej. Carlos Alberto")
        ap_paterno = c2.text_input("Apellido Paterno *", placeholder="Ej. Mendoza")
        ap_materno = c3.text_input("Apellido Materno", placeholder="Ej. Ruiz")

        c4, c5, c6 = st.columns(3)
        telefono = c4.text_input("Teléfono / WhatsApp *", placeholder="Ej. 633-123-4567")
        email = c5.text_input("Correo Electrónico *", placeholder="afiliado@correo.com")
        clave_acceso = c6.text_input("Contraseña Inicial *", type="password", placeholder="Mínimo 6 caracteres")

        domicilio = st.text_input("Domicilio Completo *", placeholder="Calle, Número, Colonia, Ciudad, Estado, C.P.")

        c7, c8, c9 = st.columns(3)
        pct_default = c7.number_input("Porcentaje de Comisión Base (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
        fecha_ingreso = c8.date_input("Fecha de Ingreso *", value=date.today())
        estatus = c9.selectbox("Estado del Afiliado *", ["Activo", "Inactivo", "Baja"])

        c10, c11 = st.columns(2)
        fecha_inact = c10.date_input("Fecha de Inactividad (si aplica)", value=None)
        fecha_baja = c11.date_input("Fecha de Baja (si aplica)", value=None)

        st.markdown("##### 🪪 Identificación Oficial Vigente (INE / IFE) — Ambos Lados")
        col_ine1, col_ine2 = st.columns(2)
        ine_frente = col_ine1.file_uploader("Subir INE Anverso (Frente) *", type=["png", "jpg", "jpeg", "pdf"], key=f"{key_prefix}_ine_f")
        ine_reverso = col_ine2.file_uploader("Subir INE Reverso (Vuelta) *", type=["png", "jpg", "jpeg", "pdf"], key=f"{key_prefix}_ine_r")

        submitted = st.form_submit_button("💾 Guardar Expediente y Crear Cuenta de Socio Afiliado", type="primary", width="stretch")

        if submitted:
            if not affiliate_id.strip() or not nombre.strip() or not ap_paterno.strip() or not usuario_login.strip() or not clave_acceso.strip():
                st.error("⚠️ Completa ID de Afiliado, Nombre, Apellido Paterno, Usuario de Acceso y Contraseña.")
                return
            if not ine_frente or not ine_reverso:
                st.error("⚠️ Es obligatorio adjuntar ambos lados de la Identificación Oficial (INE Anverso y Reverso).")
                return

            ine_f_b64 = base64.b64encode(ine_frente.read()).decode("utf-8")
            ine_r_b64 = base64.b64encode(ine_reverso.read()).decode("utf-8")
            u_clean = usuario_login.strip()
            id_clean = affiliate_id.strip().upper()

            conn = _get_conn_afiliados()
            if not conn:
                st.error("❌ Sin conexión a Supabase PostgreSQL. Verifica SUPABASE_DB_URL en Secrets.")
                return

            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO affiliate_partners (
                                affiliate_id, usuario_login, nombre, apellido_paterno, apellido_materno,
                                telefono, email, domicilio, ine_anverso_b64, ine_reverso_b64,
                                fecha_ingreso, estatus, fecha_inactividad, fecha_baja,
                                porcentaje_default, registrado_por
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (usuario_login) DO UPDATE SET
                                affiliate_id = EXCLUDED.affiliate_id,
                                nombre = EXCLUDED.nombre,
                                apellido_paterno = EXCLUDED.apellido_paterno,
                                apellido_materno = EXCLUDED.apellido_materno,
                                telefono = EXCLUDED.telefono,
                                email = EXCLUDED.email,
                                domicilio = EXCLUDED.domicilio,
                                ine_anverso_b64 = EXCLUDED.ine_anverso_b64,
                                ine_reverso_b64 = EXCLUDED.ine_reverso_b64,
                                fecha_ingreso = EXCLUDED.fecha_ingreso,
                                estatus = EXCLUDED.estatus,
                                fecha_inactividad = EXCLUDED.fecha_inactividad,
                                fecha_baja = EXCLUDED.fecha_baja,
                                porcentaje_default = EXCLUDED.porcentaje_default;
                        """, (
                            id_clean, u_clean, nombre.strip(), ap_paterno.strip(), ap_materno.strip(),
                            telefono.strip(), email.strip(), domicilio.strip(),
                            ine_f_b64, ine_r_b64, fecha_ingreso, estatus,
                            fecha_inact if estatus == "Inactivo" else None,
                            fecha_baja if estatus == "Baja" else None,
                            float(pct_default), registrado_por
                        ))

                        estatus_padron = "Activo" if estatus == "Activo" else "Inactivo"
                        cur.execute("""
                            INSERT INTO users_padron (usuario, clave_hash, rol, permisos, estatus, porcentaje_comision)
                            VALUES (%s, %s, 'Socio Afiliado', 'Basico', %s, %s)
                            ON CONFLICT (usuario) DO UPDATE SET
                                rol = 'Socio Afiliado',
                                estatus = EXCLUDED.estatus,
                                porcentaje_comision = EXCLUDED.porcentaje_comision;
                        """, (u_clean, clave_acceso.strip(), estatus_padron, float(pct_default)))

                st.success(f"✅ Expediente guardado con **ID: `{id_clean}`** y cuenta de **Socio Afiliado** (`{u_clean}`) activa en Supabase.")
            except Exception as e:
                st.error(f"Error al guardar expediente: {e}")


if __name__ == "__main__":
    st.set_page_config(page_title="Registro de Socios Afiliados — CEI", page_icon="🤝", layout="wide")
    render_formulario_registro_afiliado(registrado_por="Portal Registro Afiliados", key_prefix="standalone_aff")
