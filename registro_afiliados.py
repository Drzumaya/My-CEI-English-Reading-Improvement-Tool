import base64
from datetime import date
import hashlib
import hmac
import io
import random
import time
import urllib.parse
import psycopg
import qrcode
import streamlit as st
import streamlit.components.v1 as components


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


def _get_hmac_secret() -> bytes:
    raw = str(st.secrets.get("HMAC_SECRET_KEY") or st.secrets.get("SUPABASE_DB_URL") or "CEI_AFF_KEY").strip()
    return raw.encode("utf-8")


def generar_token_qr_7min() -> tuple[str, int]:
    """Token dinámico rotativo cada 7 minutos (420s) para generar el QR."""
    ventana = 420
    ahora = int(time.time())
    slot = ahora // ventana
    restante = ventana - (ahora % ventana)
    sig = hmac.new(_get_hmac_secret(), f"CEI_AFF_SLOT_{slot}".encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    return f"{slot}.{sig}", restante


def validar_token_qr_7min(token_str: str) -> tuple[bool, str]:
    """Valida el token del QR (o autoriza sesión única de 20 min si entra directo) y verifica que no haya sido usado."""
    if not token_str:
        # Si entra por el enlace directo sin parámetro, genera un token de sesión única válido por 20 min
        return True, "Sesión directa autorizada (20 min)"

    if "." not in token_str:
        return False, "Enlace QR inválido o incompleto."
    try:
        slot_str, sig_in = token_str.strip().split(".", 1)
        slot_num = int(slot_str)
    except ValueError:
        return False, "Formato de token QR incorrecto."

    slot_actual = int(time.time()) // 420
    if slot_num not in (slot_actual, slot_actual - 1, slot_actual - 2):
        return False, "⏳ Este código QR ha expirado. Escanea el nuevo código QR vigente."

    sig_esperada = hmac.new(_get_hmac_secret(), f"CEI_AFF_SLOT_{slot_num}".encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    if not hmac.compare_digest(sig_in, sig_esperada):
        return False, "Firma de seguridad del QR no válida."

    conn = _get_conn_afiliados()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS affiliate_used_tokens (
                            token_hash TEXT PRIMARY KEY,
                            used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """)
                    t_hash = hashlib.sha256(token_str.strip().encode("utf-8")).hexdigest()
                    cur.execute("SELECT 1 FROM affiliate_used_tokens WHERE token_hash = %s LIMIT 1;", (t_hash,))
                    if cur.fetchone():
                        return False, "🔒 Este enlace de registro ya fue utilizado y ha quedado inhabilitado."
        except Exception:
            pass
    return True, "Token válido"


def _consumir_token_qr(token_str: str):
    """Inhabilita el token tras el envío del formulario."""
    if not token_str:
        return
    conn = _get_conn_afiliados()
    if not conn:
        return
    try:
        t_hash = hashlib.sha256(token_str.strip().encode("utf-8")).hexdigest()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS affiliate_used_tokens (
                        token_hash TEXT PRIMARY KEY,
                        used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                cur.execute("INSERT INTO affiliate_used_tokens (token_hash) VALUES (%s) ON CONFLICT DO NOTHING;", (t_hash,))
    except Exception:
        pass
def _render_cuenta_regresiva_20min(segundos_restantes: int):
    """Muestra la nota oficial y la cuenta regresiva en vivo de 20 minutos."""
    html_timer = f"""
    <div style="background:#FFF8E7; border:1px solid #F59E0B; border-radius:10px; padding:12px 16px; font-family:sans-serif; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <strong style="color:#92400E; font-size:15px;">⏳ Este formulario se inhabilitará en 20 min</strong><br>
            <span style="color:#78350F; font-size:13px;">Completa tus datos antes de que termine el tiempo (también se cerrará al enviar).</span>
        </div>
        <div id="cei_timer_box" style="background:#B45309; color:#FFFFFF; font-weight:bold; font-size:20px; padding:8px 14px; border-radius:8px; min-width:85px; text-align:center;">
            20:00
        </div>
    </div>
    <script>
        let totalSec = {int(segundos_restantes)};
        const box = document.getElementById("cei_timer_box");
        function tick() {{
            if (totalSec <= 0) {{
                box.innerText = "00:00";
                box.style.background = "#DC2626";
                return;
            }}
            const m = Math.floor(totalSec / 60);
            const s = totalSec % 60;
            box.innerText = String(m).padStart(2, '0') + ":" + String(s).padStart(2, '0');
            totalSec -= 1;
        }}
        tick();
        setInterval(tick, 1000);
    </script>
    """
    components.html(html_timer, height=82)


def render_formulario_registro_afiliado(
    registrado_por: str = "Sistema",
    key_prefix: str = "aff_reg",
    mostrar_qr_dinamico: bool = True,
    token_sesion_externa: str = "",
    tiempo_inicio_escaneo: float | None = None
):
    """Formulario vertical responsivo con QR rotativo, temporizador de 20 min y bloqueo al enviar."""
    st.markdown("#### 🤝 Registro Oficial de Socio Afiliado")

    state_submitted_key = f"{key_prefix}_submitted_done"
    state_id_key = f"{key_prefix}_assigned_id"
    state_name_key = f"{key_prefix}_assigned_name"

    if state_submitted_key not in st.session_state:
        st.session_state[state_submitted_key] = False

    if tiempo_inicio_escaneo is not None and not st.session_state.get(state_submitted_key, False):
        transcurrido = time.time() - float(tiempo_inicio_escaneo)
        restante_20m = int(max(0, 1200 - transcurrido))
        if restante_20m <= 0:
            if token_sesion_externa:
                _consumir_token_qr(token_sesion_externa)
            st.error("🔒 **Tiempo Agotado (20 minutos) — Formulario Inhabilitado.** Escanea nuevamente el QR vigente.")
            return
        _render_cuenta_regresiva_20min(restante_20m)

    if mostrar_qr_dinamico:
        base_url_aff = str(st.secrets.get("AFFILIATE_REG_URL", "")).strip().rstrip("/")
        token_actual, seg_restantes = generar_token_qr_7min()
        min_rest, sec_rest = divmod(seg_restantes, 60)

        st.info(f"📲 **QR de Auto-Registro (Rotación cada 7 min | Ventana de llenado: 20 min)** — Próximo cambio en `{min_rest}m {sec_rest:02d}s`.")
        if base_url_aff:
            url_dinamica = f"{base_url_aff}/?reg_token={urllib.parse.quote(token_actual)}"
            buf_qr = io.BytesIO()
            qrcode.make(url_dinamica).save(buf_qr, format="PNG")
            st.image(buf_qr.getvalue(), caption="📲 Escanear para Auto-Registro", width=140)
            if st.button("🔄 Renovar QR Ahora", key=f"{key_prefix}_refresh_qr"):
                st.rerun()
        else:
            st.warning("⚠️ Configura `AFFILIATE_REG_URL` en Secrets para activar el QR.")
        st.divider()

    if st.session_state.get(state_submitted_key, False):
        id_asignado = st.session_state.get(state_id_key, "AFIL-CEI")
        nom_asignado = st.session_state.get(state_name_key, "Socio Afiliado")
        st.balloons()
        st.success(f"🎉 **¡Felicitaciones, {nom_asignado}! Tu Registro Oficial se completó con éxito.**")
        st.info(f"• **🆔 ID Oficial Asignado:** `{id_asignado}`\n• **🔒 Estado:** **Formulario cerrado e inhabilitado**.")
        if tiempo_inicio_escaneo is not None:
            st.caption("✅ Ya puedes cerrar esta ventana.")
        elif st.button("➕ Habilitar Nuevo Registro", key=f"{key_prefix}_reset_admin"):
            st.session_state[state_submitted_key] = False
            st.rerun()
        return

    id_sugerido = f"AFIL-CEI-{date.today().year}-{random.randint(1000, 9999)}"
    es_externo = tiempo_inicio_escaneo is not None

    with st.form(f"{key_prefix}_form", clear_on_submit=False):
        affiliate_id = st.text_input("🆔 ID de Socio Afiliado *", value=id_sugerido, disabled=es_externo)
        usuario_login = st.text_input("👤 Usuario de Acceso *", placeholder="Ej. Carlos Mendoza")
        nombre = st.text_input("Nombre(s) *", placeholder="Ej. Carlos Alberto")
        ap_paterno = st.text_input("Apellido Paterno *", placeholder="Ej. Mendoza")
        ap_materno = st.text_input("Apellido Materno", placeholder="Ej. Ruiz")
        telefono = st.text_input("Teléfono / WhatsApp *", placeholder="Ej. 633-123-4567")
        email = st.text_input("Correo Electrónico *", placeholder="afiliado@correo.com")
        clave_acceso = st.text_input("Contraseña Inicial *", type="password", placeholder="Mínimo 6 caracteres")
        domicilio = st.text_input("Domicilio Completo *", placeholder="Calle, Número, Colonia, Ciudad, Estado, C.P.")

        if es_externo:
            pct_default, fecha_ingreso, estatus, fecha_inact, fecha_baja = 10.0, date.today(), "Activo", None, None
        else:
            pct_default = st.number_input("Porcentaje Comisión Base (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
            fecha_ingreso = st.date_input("Fecha de Ingreso *", value=date.today())
            estatus = st.selectbox("Estado del Afiliado *", ["Activo", "Inactivo", "Baja"])
            fecha_inact = st.date_input("Fecha Inactividad (si aplica)", value=None)
            fecha_baja = st.date_input("Fecha de Baja (si aplica)", value=None)

        st.markdown("##### 🪪 Identificación Oficial Vigente (INE / IFE) — Ambos Lados")
        ine_frente = st.file_uploader("INE Anverso (Frente) *", type=["png", "jpg", "jpeg", "pdf"], key=f"{key_prefix}_ine_f")
        ine_reverso = st.file_uploader("INE Reverso (Vuelta) *", type=["png", "jpg", "jpeg", "pdf"], key=f"{key_prefix}_ine_r")

        submitted = st.form_submit_button("💾 Enviar Registro y Finalizar", type="primary", width="stretch")
        if submitted:
            if es_externo and (time.time() - float(tiempo_inicio_escaneo)) > 1200:
                st.error("🔒 El límite de 20 minutos expiró antes de enviar. Escanea el QR vigente nuevamente.")
                return
            if not affiliate_id.strip() or not nombre.strip() or not ap_paterno.strip() or not usuario_login.strip() or not clave_acceso.strip():
                st.error("⚠️ Completa ID, Nombre, Apellido Paterno, Usuario y Contraseña.")
                return
            if not ine_frente or not ine_reverso:
                st.error("⚠️ Adjunta ambos lados de la Identificación Oficial (INE).")
                return

            ine_f_b64 = base64.b64encode(ine_frente.read()).decode("utf-8")
            ine_r_b64 = base64.b64encode(ine_reverso.read()).decode("utf-8")
            u_clean = usuario_login.strip()
            id_clean = affiliate_id.strip().upper()
            nombre_completo = f"{nombre.strip()} {ap_paterno.strip()}".strip()

            conn = _get_conn_afiliados()
            if not conn:
                st.error("❌ Sin conexión a Supabase PostgreSQL.")
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

                if token_sesion_externa:
                    _consumir_token_qr(token_sesion_externa)

                st.session_state[state_id_key] = id_clean
                st.session_state[state_name_key] = nombre_completo
                st.session_state[state_submitted_key] = True
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar expediente: {e}")


if __name__ == "__main__":
    st.set_page_config(page_title="Registro de Socios Afiliados — CEI", page_icon="🤝", layout="centered")
    q_token = str(st.query_params.get("reg_token", "")).strip()

    if "aff_ext_authorized" not in st.session_state:
        st.session_state["aff_ext_authorized"] = False
        st.session_state["aff_ext_token"] = ""
        st.session_state["aff_ext_scan_ts"] = None
        st.session_state["aff_ext_err"] = ""

    if not st.session_state["aff_ext_authorized"]:
        ok_tok, msg_tok = validar_token_qr_7min(q_token)
        if ok_tok:
            st.session_state["aff_ext_authorized"] = True
            st.session_state["aff_ext_token"] = q_token
            st.session_state["aff_ext_scan_ts"] = time.time()
        else:
            st.session_state["aff_ext_err"] = msg_tok

    if st.session_state["aff_ext_authorized"]:
        render_formulario_registro_afiliado(
            registrado_por="Auto-Registro QR Aspirante",
            key_prefix="ext_qr_aff",
            mostrar_qr_dinamico=False,
            token_sesion_externa=st.session_state["aff_ext_token"],
            tiempo_inicio_escaneo=st.session_state["aff_ext_scan_ts"]
        )
    else:
        st.markdown("### 🤝 Career English Institute — Auto-Registro de Socios Afiliados")
        st.error(
            f"🔒 **Acceso Restringido al Formulario de Registro**\n\n"
            f"{st.session_state['aff_ext_err']}\n\n"
            "Solicita y escanea nuevamente el **Código QR vigente** para iniciar tu registro."
        )
