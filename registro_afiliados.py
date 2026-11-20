# ==============================================================================
# registro_afiliados.py — PARTE 1 DE 4: CONEXIÓN, TOKENS QR Y TÉRMINOS LEGALES
# ==============================================================================
import base64
from datetime import date, datetime
import hashlib
import hmac
import io
import random
import time
import urllib.parse
from zoneinfo import ZoneInfo
import psycopg
import qrcode
import streamlit as st
import streamlit.components.v1 as components

if hasattr(st, "iframe"):
    components.html = lambda html_str, height=None, scrolling=False, width=None: st.iframe(
        html_str, height=height or 150, width=width or "stretch"
    )

DEFAULT_AFFILIATE_TERMS_FALLBACK = """TÉRMINOS Y CONDICIONES DEL PROGRAMA DE SOCIOS AFILIADOS — CAREER ENGLISH INSTITUTE (CEI)

1. OBJETO DE LA AFILIACIÓN: El Socio Afiliado actúa como promotor independiente de los programas académicos de Career English Institute (CEI), sin que ello constituya relación laboral, subordinación o representación legal.
2. COMISIONES Y LIQUIDACIÓN: Las comisiones aplicables se calcularán exclusivamente sobre inscripciones y mensualidades efectivamente cobradas y validadas por la administración de CEI, conforme al porcentaje vigente asignado al Socio.
3. USO DE MARCA Y MATERIALES: El Socio se compromete a utilizar únicamente los materiales oficiales aprobados por CEI y a no alterar precios, certificaciones ni condiciones académicas sin autorización escrita.
4. CONFIDENCIALIDAD Y PROTECCIÓN DE DATOS: Toda información de prospectos y estudiantes deberá tratarse bajo estricta confidencialidad y conforme a la normativa de protección de datos personales vigente.
5. VIGENCIA Y TERMINACIÓN: CEI se reserva el derecho de suspender o cancelar la afiliación ante incumplimiento de estos términos o uso indebido de la marca institucional."""


def _find_secret(key_name: str) -> str:
    if key_name in st.secrets:
        return str(st.secrets[key_name]).strip()
    key_low = key_name.lower()
    for k, v in st.secrets.items():
        if str(k).lower() == key_low and not isinstance(v, dict):
            return str(v).strip()
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                if str(sub_k).lower() == key_low:
                    return str(sub_v).strip()
    return ""


def _get_conn_afiliados():
    st.session_state["_aff_db_last_err"] = ""
    pg_host = _find_secret("PG_HOST") or _find_secret("DB_HOST") or _find_secret("HOST")
    pg_user = _find_secret("PG_USER") or _find_secret("DB_USER") or _find_secret("USER") or _find_secret("USERNAME")
    pg_pass = _find_secret("PG_PASSWORD") or _find_secret("DB_PASSWORD") or _find_secret("PASSWORD")
    pg_port = int(_find_secret("PG_PORT") or _find_secret("DB_PORT") or _find_secret("PORT") or 6543)
    pg_db = _find_secret("PG_DBNAME") or _find_secret("DB_NAME") or _find_secret("DATABASE") or "postgres"

    if pg_host and pg_user and pg_pass:
        for p_try in ([pg_port, 6543] if pg_port != 6543 else [6543]):
            try:
                return psycopg.connect(
                    host=pg_host,
                    port=p_try,
                    dbname=pg_db,
                    user=pg_user,
                    password=pg_pass,
                    sslmode="require",
                    connect_timeout=10,
                    prepare_threshold=None
                )
            except Exception as e:
                st.session_state["_aff_db_last_err"] = str(e)

    db_url = (
        _find_secret("SUPABASE_DB_URL")
        or _find_secret("DATABASE_URL")
        or _find_secret("POSTGRES_URL")
        or _find_secret("DB_URL")
        or _find_secret("URL")
    )
    if db_url and db_url.startswith("postgres"):
        if "sslmode=" not in db_url:
            db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
        try:
            return psycopg.connect(db_url, connect_timeout=10, prepare_threshold=None)
        except Exception as e:
            st.session_state["_aff_db_last_err"] = str(e)

    if not st.session_state.get("_aff_db_last_err"):
        st.session_state["_aff_db_last_err"] = "Faltan los secretos PG_HOST / SUPABASE_DB_URL en Settings -> Secrets de esta app en Streamlit Cloud."
    return None


def obtener_terminos_afiliacion_pg() -> dict:
    """Lee desde Supabase PostgreSQL los Términos y Condiciones de Afiliación vigentes."""
    conn = _get_conn_afiliados()
    if not conn:
        return {"texto": DEFAULT_AFFILIATE_TERMS_FALLBACK, "updated_by": "CEI", "updated_at": ""}
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cei_configuracion_legal (
                        clave TEXT PRIMARY KEY,
                        contenido TEXT NOT NULL,
                        updated_by TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute(
                    "SELECT contenido, updated_by, updated_at FROM cei_configuracion_legal WHERE clave = 'terminos_afiliacion' LIMIT 1;"
                )
                row = cur.fetchone()
                if row and str(row[0] or "").strip():
                    return {
                        "texto": str(row[0]).strip(),
                        "updated_by": str(row[1] or "CEI"),
                        "updated_at": str(row[2] or "")[:19]
                    }
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return {"texto": DEFAULT_AFFILIATE_TERMS_FALLBACK, "updated_by": "CEI", "updated_at": ""}


def generar_token_qr_7min() -> tuple[str, int]:
    """Genera un token único de QR con vigencia de 7 min (420s) y lo registra en PostgreSQL."""
    import secrets
    ventana = 420
    ahora = int(time.time())
    restante = ventana - (ahora % ventana)

    tok_cache = str(st.session_state.get("_last_qr_tok") or "")
    ts_cache = int(st.session_state.get("_last_qr_ts") or 0)
    if tok_cache and (ahora - ts_cache) < 300:
        return tok_cache, 420 - (ahora - ts_cache)

    nuevo_tok = secrets.token_urlsafe(14)
    conn = _get_conn_afiliados()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS affiliate_qr_sessions (
                            token TEXT PRIMARY KEY,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            scanned_at TIMESTAMP WITH TIME ZONE,
                            used BOOLEAN DEFAULT FALSE
                        );
                    """)
                    cur.execute(
                        "INSERT INTO affiliate_qr_sessions (token, created_at, used) VALUES (%s, NOW(), FALSE);",
                        (nuevo_tok,)
                    )
            st.session_state["_last_qr_tok"] = nuevo_tok
            st.session_state["_last_qr_ts"] = ahora
            return nuevo_tok, 420
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
    return nuevo_tok, restante


def validar_token_qr_7min(token_str: str) -> tuple[bool, str]:
    """Valida el token del QR directamente contra PostgreSQL (7 min para escanear + 20 min de llenado)."""
    tok = urllib.parse.unquote(str(token_str or "").strip())
    if not tok:
        return True, "Sesión directa autorizada (20 min)"

    conn = _get_conn_afiliados()
    if not conn:
        return False, "No hay conexión con la base de datos para verificar el QR."
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS affiliate_qr_sessions (
                        token TEXT PRIMARY KEY,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        scanned_at TIMESTAMP WITH TIME ZONE,
                        used BOOLEAN DEFAULT FALSE
                    );
                """)
                cur.execute("""
                    SELECT EXTRACT(EPOCH FROM (NOW() - created_at)),
                           EXTRACT(EPOCH FROM (NOW() - COALESCE(scanned_at, NOW()))),
                           used,
                           scanned_at IS NOT NULL
                    FROM affiliate_qr_sessions
                    WHERE token = %s
                    LIMIT 1;
                """, (tok,))
                row = cur.fetchone()
                if not row:
                    return False, "El código QR no fue reconocido o pertenece a una sesión anterior. Genera y escanea un QR nuevo."

                edad_creacion, edad_escaneo, ya_usado, ya_escaneado = float(row[0]), float(row[1]), bool(row[2]), bool(row[3])
                if ya_usado:
                    return False, "🔒 Este formulario ya fue enviado y el enlace quedó inhabilitado."

                if not ya_escaneado:
                    if edad_creacion > 450:
                        return False, "⏳ Este código QR expiró (límite de 7 minutos para escanear). Solicita uno nuevo."
                    cur.execute("UPDATE affiliate_qr_sessions SET scanned_at = NOW() WHERE token = %s;", (tok,))
                else:
                    if edad_escaneo > 1200:
                        return False, "⏳ El tiempo de 20 minutos para llenar el formulario ha expirado."
        return True, "Token válido"
    except Exception as e:
        return False, f"Error verificando QR: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ==============================================================================
# registro_afiliados.py — PARTE 2 DE 4: TEMPORIZADOR Y CABECERA DEL FORMULARIO
# ==============================================================================
def _consumir_token_qr(token_str: str):
    """Inhabilita el token en PostgreSQL tras el envío del formulario."""
    tok = urllib.parse.unquote(str(token_str or "").strip())
    if not tok:
        return
    conn = _get_conn_afiliados()
    if not conn:
        return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS affiliate_qr_sessions (
                        token TEXT PRIMARY KEY,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        scanned_at TIMESTAMP WITH TIME ZONE,
                        used BOOLEAN DEFAULT FALSE
                    );
                """)
                cur.execute("UPDATE affiliate_qr_sessions SET used = TRUE WHERE token = %s;", (tok,))
    except Exception:
        pass
    finally:
        try:
            conn.close()
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
        base_url_aff = str(_find_secret("AFFILIATE_REG_URL")).strip().rstrip("/")
        token_actual, seg_restantes = generar_token_qr_7min()
        min_rest, sec_rest = divmod(seg_restantes, 60)

        if base_url_aff:
            url_dinamica = f"{base_url_aff}/?reg_token={urllib.parse.quote(token_actual)}"
            buf_qr = io.BytesIO()
            qrcode.make(url_dinamica).save(buf_qr, format="PNG")
            qr_aff_bytes = buf_qr.getvalue()
            zoom_aff_key = f"{key_prefix}_qr_zoom_center"

            if st.session_state.get(zoom_aff_key, False):
                st.markdown(
                    "<div style='text-align:center; padding-top:8px;'>"
                    "<h2>📲 Escanea para Registrarte como Socio Afiliado CEI</h2>"
                    "</div>",
                    unsafe_allow_html=True
                )
                _, col_q_ctr, _ = st.columns([1.0, 1.4, 1.0])
                with col_q_ctr:
                    st.image(qr_aff_bytes, width=420)
                    st.info(f"⏳ **QR Dinámico (Rotación cada 7 min | Ventana de llenado: 20 min)** — Cambia en `{min_rest}m {sec_rest:02d}s`.")
                    if st.button("✖️ CERRAR QR", type="primary", width="stretch", key=f"{key_prefix}_close_qr_center"):
                        st.session_state[zoom_aff_key] = False
                        st.rerun()
                st.stop()

            st.info(f"📲 **QR de Auto-Registro (Rotación cada 7 min | Ventana de llenado: 20 min)** — Próximo cambio en `{min_rest}m {sec_rest:02d}s`.")
            c_q1, c_q2 = st.columns([1.1, 2.3])
            with c_q1:
                qr_aff_b64 = base64.b64encode(qr_aff_bytes).decode("ascii")
                if st.button("🖥️ Proyectar QR", key=f"{key_prefix}_trigger_zoom_qr", width="stretch"):
                    st.session_state[zoom_aff_key] = True
                    st.rerun()

                components.html(
                    f"""
                    <div style="text-align:center;font-family:sans-serif;cursor:pointer;"
                         ondblclick="
                           const btns = window.parent.document.querySelectorAll('button');
                           for (const b of btns) {{
                             if (b.innerText && b.innerText.includes('Proyectar QR')) {{
                               b.click();
                               break;
                             }}
                           }}
                         "
                         title="Haz doble clic en el QR para abrirlo en el centro">
                      <img src="data:image/png;base64,{qr_aff_b64}" style="width:150px;height:150px;border-radius:10px;border:2px solid #0284c7;" />
                      <div style="font-size:11px;color:#0284c7;font-weight:bold;margin-top:4px;">🖱️ Doble clic en el QR para proyectar</div>
                    </div>
                    """,
                    height=185
                )
            with c_q2:
                st.download_button(
                    "⬇️ Descargar QR de Afiliación (PNG)",
                    data=qr_aff_bytes,
                    file_name="QR_Alta_Socio_Afiliado_CEI.png",
                    mime="image/png",
                    type="primary",
                    width="stretch",
                    key=f"{key_prefix}_dl_qr_aff"
                )
                if st.button("🔄 Renovar QR Ahora", key=f"{key_prefix}_refresh_qr", width="stretch"):
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
# ==============================================================================
# registro_afiliados.py — PARTE 3A: CAMPOS DEL FORMULARIO, RFC Y TÉRMINOS
# ==============================================================================
    anio_actual = date.today().year
    id_sugerido = f"AFIL-CEI-{anio_actual}-{random.randint(1000, 9999)}"
    es_externo = tiempo_inicio_escaneo is not None
    datos_terminos = obtener_terminos_afiliacion_pg()

    with st.form(f"{key_prefix}_form", clear_on_submit=False):
        affiliate_id = st.text_input("🆔 ID de Socio Afiliado *", value=id_sugerido, disabled=es_externo)
        usuario_login = st.text_input("👤 Usuario de Acceso *", placeholder="Ej. Carlos Mendoza")
        nombre = st.text_input("Nombre(s) *", placeholder="Ej. Carlos Alberto")
        ap_paterno = st.text_input("Apellido Paterno *", placeholder="Ej. Mendoza")
        ap_materno = st.text_input("Apellido Materno", placeholder="Ej. Ruiz")
        rfc = st.text_input(
            "🧾 RFC (Registro Federal de Contribuyentes — 12 o 13 caracteres) *",
            placeholder="Ej. MERC850101ABC",
            max_chars=13
        )
        telefono = st.text_input("Teléfono / WhatsApp *", placeholder="Ej. 633-123-4567")
        email = st.text_input("Correo Electrónico *", placeholder="afiliado@correo.com")
        clave_acceso = st.text_input("Contraseña Inicial *", type="password", placeholder="Mínimo 6 caracteres")
        domicilio = st.text_input("Domicilio Completo *", placeholder="Calle, Número, Colonia, Ciudad, Estado, C.P.")

        if es_externo:
            pct_default, fecha_ingreso, estatus, fecha_inact, fecha_baja = 0.0, date.today(), "Activo", None, None
            st.info(
                "💼 **Porcentaje de Comisión:** Será asignado oficialmente por el **Owner o Administrador** de CEI "
                "una vez validado tu expediente (INE y RFC)."
            )
        else:
            pct_default = st.number_input(
                "💼 Porcentaje Comisión Base (% — Asignado por Owner / Admin) *",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=1.0
            )
            fecha_ingreso = st.date_input("Fecha de Ingreso *", value=date.today())
            estatus = st.selectbox("Estado del Afiliado *", ["Activo", "Inactivo", "Baja"])
            fecha_inact = st.date_input("Fecha Inactividad (si aplica)", value=None)
            fecha_baja = st.date_input("Fecha de Baja (si aplica)", value=None)

        st.markdown("##### 🪪 Identificación Oficial Vigente (INE / IFE) — Ambos Lados")
        ine_frente = st.file_uploader("INE Anverso (Frente) *", type=["png", "jpg", "jpeg", "pdf"], key=f"{key_prefix}_ine_f")
        ine_reverso = st.file_uploader("INE Reverso (Vuelta) *", type=["png", "jpg", "jpeg", "pdf"], key=f"{key_prefix}_ine_r")

        st.divider()
        st.markdown("##### 📜 Términos y Condiciones de la Afiliación")
        if datos_terminos.get("updated_at"):
            st.caption(f"Versión vigente actualizada el `{datos_terminos['updated_at']}`")
        with st.container(height=210, border=True):
            st.markdown(datos_terminos["texto"])

        acepta_terminos = st.checkbox(
            "✅ He leído, comprendo y acepto los Términos y Condiciones del Programa de Socios Afiliados de Career English Institute *",
            key=f"{key_prefix}_chk_terminos"
        )

        submitted = st.form_submit_button("💾 Enviar Registro y Finalizar", type="primary", width="stretch")
# ==============================================================================
# registro_afiliados.py — PARTE 3B: VALIDACIÓN Y GUARDADO TRANSACCIONAL
# ==============================================================================
        if submitted:
            if es_externo and (time.time() - float(tiempo_inicio_escaneo)) > 1200:
                st.error("🔒 El límite de 20 minutos expiró antes de enviar. Escanea el QR vigente nuevamente.")
                return
            if not affiliate_id.strip() or not nombre.strip() or not ap_paterno.strip() or not usuario_login.strip() or not clave_acceso.strip():
                st.error("⚠️ Completa ID, Nombre, Apellido Paterno, Usuario y Contraseña.")
                return
            rfc_clean = rfc.strip().upper()
            if len(rfc_clean) not in (12, 13) or not rfc_clean.isalnum():
                st.error("⚠️ Ingresa un RFC válido de 12 (Persona Moral) o 13 (Persona Física) caracteres alfanuméricos.")
                return
            if not ine_frente or not ine_reverso:
                st.error("⚠️ Adjunta ambos lados de la Identificación Oficial (INE).")
                return
            if not acepta_terminos:
                st.error("⚠️ Debes leer y marcar la casilla de aceptación de los Términos y Condiciones para continuar.")
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
                            ALTER TABLE affiliate_partners
                            ADD COLUMN IF NOT EXISTS rfc TEXT DEFAULT '',
                            ADD COLUMN IF NOT EXISTS terminos_aceptados BOOLEAN DEFAULT TRUE,
                            ADD COLUMN IF NOT EXISTS terminos_aceptados_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                        """)
                        cur.execute("""
                            INSERT INTO affiliate_partners (
                                affiliate_id, usuario_login, nombre, apellido_paterno, apellido_materno,
                                rfc, telefono, email, domicilio, ine_anverso_b64, ine_reverso_b64,
                                fecha_ingreso, estatus, fecha_inactividad, fecha_baja,
                                porcentaje_default, registrado_por,
                                terminos_aceptados, terminos_aceptados_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
                            ON CONFLICT (usuario_login) DO UPDATE SET
                                affiliate_id = EXCLUDED.affiliate_id,
                                nombre = EXCLUDED.nombre,
                                apellido_paterno = EXCLUDED.apellido_paterno,
                                apellido_materno = EXCLUDED.apellido_materno,
                                rfc = EXCLUDED.rfc,
                                telefono = EXCLUDED.telefono,
                                email = EXCLUDED.email,
                                domicilio = EXCLUDED.domicilio,
                                ine_anverso_b64 = EXCLUDED.ine_anverso_b64,
                                ine_reverso_b64 = EXCLUDED.ine_reverso_b64,
                                fecha_ingreso = EXCLUDED.fecha_ingreso,
                                estatus = EXCLUDED.estatus,
                                fecha_inactividad = EXCLUDED.fecha_inactividad,
                                fecha_baja = EXCLUDED.fecha_baja,
                                porcentaje_default = CASE
                                    WHEN %s THEN affiliate_partners.porcentaje_default
                                    ELSE EXCLUDED.porcentaje_default
                                END,
                                terminos_aceptados = TRUE,
                                terminos_aceptados_at = NOW();
                        """, (
                            id_clean, u_clean, nombre.strip(), ap_paterno.strip(), ap_materno.strip(),
                            rfc_clean, telefono.strip(), email.strip(), domicilio.strip(),
                            ine_f_b64, ine_r_b64, fecha_ingreso, estatus,
                            fecha_inact if estatus == "Inactivo" else None,
                            fecha_baja if estatus == "Baja" else None,
                            float(pct_default), registrado_por,
                            es_externo
                        ))

                        estatus_padron = "Activo" if estatus == "Activo" else "Inactivo"
                        cur.execute("""
                            INSERT INTO users_padron (usuario, clave_hash, rol, permisos, estatus, porcentaje_comision)
                            VALUES (%s, %s, 'Socio Afiliado', 'Basico', %s, %s)
                            ON CONFLICT (usuario) DO UPDATE SET
                                rol = 'Socio Afiliado',
                                estatus = EXCLUDED.estatus,
                                porcentaje_comision = CASE
                                    WHEN %s THEN users_padron.porcentaje_comision
                                    ELSE EXCLUDED.porcentaje_comision
                                END
                            RETURNING id, matricula;
                        """, (u_clean, clave_acceso.strip(), estatus_padron, float(pct_default), es_externo))
                        row_pad = cur.fetchone()
                        if row_pad and not row_pad:
                            mat_gen = f"CEI-{anio_actual}-{int(row_pad):04d}"
                            cur.execute("UPDATE users_padron SET matricula = %s WHERE id = %s;", (mat_gen, row_pad))

                if token_sesion_externa:
                    _consumir_token_qr(token_sesion_externa)

                st.cache_data.clear()
                st.session_state[state_id_key] = id_clean
                st.session_state[state_name_key] = nombre_completo
                st.session_state[state_submitted_key] = True
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar expediente: {e}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass


# ==============================================================================
# registro_afiliados.py — PARTE 4 DE 4 (FINAL): MODO INDEPENDIENTE (STANDALONE)
# ==============================================================================
if __name__ == "__main__":
    st.set_page_config(page_title="Registro de Socios Afiliados — CEI", page_icon="🤝", layout="centered")
    q_token = str(st.query_params.get("reg_token", "")).strip()

    if "aff_ext_authorized" not in st.session_state:
        st.session_state["aff_ext_authorized"] = False
        st.session_state["aff_ext_token"] = ""
        st.session_state["aff_ext_scan_ts"] = None
        st.session_state["aff_ext_err"] = ""

    # Si se escaneó un token diferente al de la sesión previa, revalidar al instante
    if q_token and st.session_state.get("aff_ext_token") != q_token:
        st.session_state["aff_ext_authorized"] = False
        st.session_state["aff_ext_err"] = ""

    if not st.session_state["aff_ext_authorized"]:
        ok_tok, msg_tok = validar_token_qr_7min(q_token)
        if ok_tok:
            st.session_state["aff_ext_authorized"] = True
            st.session_state["aff_ext_token"] = q_token
            st.session_state["aff_ext_scan_ts"] = time.time()
            st.session_state["aff_ext_err"] = ""
        else:
            st.session_state["aff_ext_err"] = msg_tok

    if st.session_state["aff_ext_authorized"]:
        render_formulario_registro_afiliado(
            registrado_por="Auto-Registro QR Aspirante",
            key_prefix="ext_qr_aff",
            mostrar_qr_dinamico=False,
            token_sesion_externa=st.session_state["aff_ext_token"],
            tiempo_inicio_escaneo=float(st.session_state["aff_ext_scan_ts"] or time.time())
        )
    else:
        st.markdown("### 🤝 Career English Institute — Auto-Registro de Socios Afiliados")
        st.error(
            f"🔒 **Acceso Restringido al Formulario de Registro**\n\n"
            f"{st.session_state['aff_ext_err']}\n\n"
            "Solicita y escanea nuevamente el **Código QR vigente** para iniciar tu registro."
        )
