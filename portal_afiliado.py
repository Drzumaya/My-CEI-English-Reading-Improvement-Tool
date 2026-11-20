# ==============================================================================
# portal_afiliado.py — PARTE 1 DE 2: CONEXIÓN, QR CON ID OFICIAL Y PROYECCIÓN ZOOM
# ==============================================================================
import base64
import io
import urllib.parse
import pandas as pd
import psycopg
import qrcode
import streamlit as st
import streamlit.components.v1 as components

if hasattr(st, "iframe"):
    components.html = lambda html_str, height=None, scrolling=False, width=None: st.iframe(
        html_str, height=height or 150, width=width or "stretch"
    )

DEFAULT_INSCRIPTION_URL_AFF = "https://streamlit.app"


def _find_secret_portal(key_name: str) -> str:
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


def _get_conn_portal():
    pg_host = _find_secret_portal("PG_HOST") or _find_secret_portal("DB_HOST") or _find_secret_portal("HOST")
    pg_user = _find_secret_portal("PG_USER") or _find_secret_portal("DB_USER") or _find_secret_portal("USER")
    pg_pass = _find_secret_portal("PG_PASSWORD") or _find_secret_portal("DB_PASSWORD") or _find_secret_portal("PASSWORD")
    pg_port = int(_find_secret_portal("PG_PORT") or _find_secret_portal("DB_PORT") or 6543)
    pg_db = _find_secret_portal("PG_DBNAME") or _find_secret_portal("DB_NAME") or "postgres"

    if pg_host and pg_user and pg_pass:
        return psycopg.connect(
            host=pg_host, port=pg_port, dbname=pg_db,
            user=pg_user, password=pg_pass, sslmode="require",
            connect_timeout=10, prepare_threshold=None
        )
    db_url = _find_secret_portal("SUPABASE_DB_URL") or _find_secret_portal("DATABASE_URL")
    if db_url and db_url.startswith("postgres"):
        if "sslmode=" not in db_url:
            db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
        return psycopg.connect(db_url, connect_timeout=10, prepare_threshold=None)
    return None


def _obtener_url_inscripcion_vigente() -> str:
    """Lee la URL oficial de inscripción publicada por Owner/Admin en Supabase."""
    fallback = str(_find_secret_portal("STUDENT_INSCRIPTION_URL") or DEFAULT_INSCRIPTION_URL_AFF).strip().rstrip("/")
    conn = _get_conn_portal()
    if not conn:
        return fallback
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT contenido FROM cei_configuracion_legal WHERE clave = 'url_inscripcion_estudiantes' LIMIT 1;")
            row = cur.fetchone()
            if row and str(row[0] or "").strip():
                return str(row[0]).strip().rstrip("/")
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return fallback


def _cargar_perfil_afiliado(usuario_afiliado: str) -> dict:
    """Obtiene el expediente e ID oficial del Socio Afiliado desde affiliate_partners."""
    u_clean = str(usuario_afiliado or "").strip()
    perfil = {
        "affiliate_id": u_clean,
        "usuario_login": u_clean,
        "nombre_completo": u_clean,
        "rfc": "",
        "estatus": "Activo",
        "porcentaje": 0.0
    }
    conn = _get_conn_portal()
    if not conn:
        return perfil
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(NULLIF(TRIM(affiliate_id), ''), usuario_login),
                       usuario_login,
                       COALESCE(NULLIF(TRIM(nombre || ' ' || apellido_paterno), ''), usuario_login),
                       COALESCE(rfc, ''),
                       COALESCE(estatus, 'Activo'),
                       COALESCE(porcentaje_default, 0.0)
                FROM affiliate_partners
                WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                   OR LOWER(TRIM(affiliate_id)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (u_clean, u_clean))
            row = cur.fetchone()
            if row:
                perfil["affiliate_id"] = str(row[0]).strip()
                perfil["usuario_login"] = str(row[1]).strip()
                perfil["nombre_completo"] = str(row[2]).strip()
                perfil["rfc"] = str(row[3]).strip()
                perfil["estatus"] = str(row[4]).strip()
                perfil["porcentaje"] = float(row[5] or 0.0)
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return perfil

# ==============================================================================
# portal_afiliado.py — PARTE 2 DE 2 (FINAL): PANEL FINANCIERO Y MODO STANDALONE
# ==============================================================================
def render_portal_socio_afiliado(usuario_afiliado: str):
    """Renderiza el Portal del Socio Afiliado con QR oficial, métricas, alumnos y comisiones."""
    perfil = _cargar_perfil_afiliado(usuario_afiliado)
    aff_id_oficial = perfil["affiliate_id"]
    aff_login = perfil["usuario_login"]
    aff_nombre = perfil["nombre_completo"]
    url_base_ins = _obtener_url_inscripcion_vigente()
    url_qr_referido = f"{url_base_ins}/?ref_aff={urllib.parse.quote(aff_id_oficial)}"

    buf_qr = io.BytesIO()
    qrcode.make(url_qr_referido).save(buf_qr, format="PNG")
    qr_bytes = buf_qr.getvalue()
    zoom_key = f"portal_standalone_qr_zoom_{aff_id_oficial}"

    # MODO PROYECCIÓN CENTRAL EN ZOOM (OCULTA TODA LA VENTANA AL DOBLE CLIC)
    if st.session_state.get(zoom_key, False):
        st.markdown(
            "<div style='text-align:center; padding-top:10px;'>"
            "<h2>📲 Escanea para Inscribirte en Career English Institute (CEI)</h2>"
            "</div>",
            unsafe_allow_html=True
        )
        _, col_ctr, _ = st.columns([1.0, 1.4, 1.0])
        with col_ctr:
            st.image(qr_bytes, width=420)
            st.info(
                f"🤝 **Socio Afiliado Anfitrión:** {aff_nombre}\n\n"
                f"🆔 **ID Oficial Ligado al QR:** `{aff_id_oficial}`\n\n"
                f"🔗 `{url_qr_referido}`"
            )
            if st.button("✖️ CERRAR QR", type="primary", width="stretch", key=f"btn_close_fs_{aff_id_oficial}"):
                st.session_state[zoom_key] = False
                st.rerun()
        st.stop()

    # FICHA FISCAL Y DE COMISIÓN VIGENTE
    st.info(
        f"🤝 **Socio Afiliado:** {aff_nombre}  |  🆔 **ID Oficial:** `{aff_id_oficial}`  |  "
        f"🧾 **RFC:** `{perfil['rfc'] or 'Pendiente'}`  |  💼 **Comisión Asignada:** **`{perfil['porcentaje']:.1f}%`**\n\n"
        "📄 *Recordatorio Fiscal: Expedir factura electrónica (CFDI) de honorarios/comisiones dentro de los primeros 5 días hábiles del mes siguiente.*"
    )

    # TARJETA DE CÓDIGO QR OFICIAL PARA INVITAR ESTUDIANTES
    with st.container(border=True):
        c_q1, c_q2 = st.columns([1.1, 2.4])
        with c_q1:
            qr_b64 = base64.b64encode(qr_bytes).decode("ascii")
            if st.button("🖥️ Ampliar QR", key=f"btn_trig_dbl_{aff_id_oficial}", width="stretch"):
                st.session_state[zoom_key] = True
                st.rerun()

            components.html(
                f"""
                <div style="text-align:center;font-family:sans-serif;cursor:pointer;"
                     ondblclick="
                       const btns = window.parent.document.querySelectorAll('button');
                       for (const b of btns) {{
                         if (b.innerText && b.innerText.includes('Ampliar QR')) {{
                           b.click();
                           break;
                         }}
                       }}
                     "
                     title="Haz doble clic sobre el QR para abrirlo en el centro">
                  <img src="data:image/png;base64,{qr_b64}" style="width:155px;height:155px;border-radius:10px;border:2px solid #0284c7;" />
                  <div style="font-size:11px;color:#0284c7;font-weight:bold;margin-top:4px;">🖱️ Doble clic en el QR para proyectar</div>
                </div>
                """,
                height=190
            )
        with c_q2:
            st.markdown("#### 📲 Tu Código QR Oficial de Inscripción de Alumnos")
            st.caption(
                "Muestra este código QR en tus **reuniones de Zoom** o descárgalo para enviarlo por WhatsApp. "
                "Al escanearlo, el formulario mostrará automáticamente tu **ID Oficial (`" + aff_id_oficial + "`)**."
            )
            st.code(url_qr_referido, language=None)
            b1, b2 = st.columns(2)
            with b1:
                st.download_button(
                    "⬇️ Descargar QR Inscripción (PNG)",
                    data=qr_bytes,
                    file_name=f"QR_Inscripcion_CEI_{aff_id_oficial}.png",
                    mime="image/png",
                    type="primary",
                    width="stretch",
                    key=f"btn_dl_qr_{aff_id_oficial}"
                )
            with b2:
                if st.button("🖥️ Proyectar QR en Centro", type="secondary", width="stretch", key=f"btn_open_fs_{aff_id_oficial}"):
                    st.session_state[zoom_key] = True
                    st.rerun()

    # CONSULTA DE ESTUDIANTES REFERIDOS Y COMISIONES EN POSTGRESQL
    conn = _get_conn_portal()
    estudiantes_rows = []
    comisiones_rows = []
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(matricula, ''), usuario, COALESCE(nivel, 'A1'),
                           COALESCE(estatus, 'Activo'), COALESCE(fecha_inscripcion::text, '')
                    FROM users_padron
                    WHERE LOWER(TRIM(COALESCE(socio_afiliado, ''))) IN (LOWER(TRIM(%s)), LOWER(TRIM(%s)))
                    ORDER BY id DESC;
                """, (aff_login, aff_id_oficial))
                estudiantes_rows = cur.fetchall()

                cur.execute("""
                    SELECT COALESCE(student_user, ''), COALESCE(monto_base, 0),
                           COALESCE(porcentaje, 0), COALESCE(monto_comision, 0),
                           COALESCE(estatus_pago, 'Pendiente'), COALESCE(fecha_registro::text, '')
                    FROM affiliate_commissions
                    WHERE LOWER(TRIM(COALESCE(affiliate_user, ''))) IN (LOWER(TRIM(%s)), LOWER(TRIM(%s)))
                    ORDER BY id DESC;
                """, (aff_login, aff_id_oficial))
                comisiones_rows = cur.fetchall()
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    total_ganado = sum(float(r[3] or 0.0) for r in comisiones_rows)
    total_pagado = sum(float(r[3] or 0.0) for r in comisiones_rows if str(r[4]).strip().lower() == "pagado")
    total_pendiente = max(0.0, total_ganado - total_pagado)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎓 Alumnos Referidos", f"{len(estudiantes_rows)}")
    m2.metric("💰 Total Comisiones", f"${total_ganado:,.2f} MXN")
    m3.metric("⏳ Pendiente de Cobro", f"${total_pendiente:,.2f} MXN")
    m4.metric("✅ Ya Liquidado", f"${total_pagado:,.2f} MXN")

    if estudiantes_rows:
        st.markdown("##### 🎓 Estudiantes Inscritos con tu Código / QR")
        df_est = pd.DataFrame(
            estudiantes_rows,
            columns=["Matrícula", "Estudiante", "Nivel CEFR", "Estatus", "Fecha Inscripción"]
        )
        st.dataframe(df_est, width="stretch", hide_index=True)

    if comisiones_rows:
        st.markdown("##### 💵 Detalle de Comisiones Generadas")
        df_com = pd.DataFrame(
            comisiones_rows,
            columns=["Estudiante", "Monto Base ($)", "% Comisión", "Comisión ($ MXN)", "Estatus Pago", "Fecha"]
        )
        st.dataframe(df_com, width="stretch", hide_index=True)


# ==============================================================================
# portal_afiliado.py — PARTE 3 DE 3 (FINAL): MODO INDEPENDIENTE (STANDALONE)
# ==============================================================================
if __name__ == "__main__":
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
                            finally:
                                try:
                                    conn_l.close()
                                except Exception:
                                    pass
    else:
        col_top1, col_top2 = st.columns([5, 1])
        with col_top1:
            st.caption(f"Sesión activa: **{st.session_state.aff_logged_user}** | Portal de Socios Afiliados CEI")
        with col_top2:
            if st.button("🚪 Cerrar Sesión", width="stretch"):
                st.session_state.aff_logged_user = ""
                st.rerun()

        render_portal_socio_afiliado(st.session_state.aff_logged_user)
