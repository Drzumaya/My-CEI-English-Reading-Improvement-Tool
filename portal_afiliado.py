import base64
from datetime import datetime, timedelta
import hmac
import io
import os
import urllib.parse
import psycopg
import qrcode
import streamlit as st

st.set_page_config(
    page_title="Portal Oficial de Socios Afiliados — CEI",
    page_icon="🤝",
    layout="centered"
)

st.markdown(
    """
    <style>
    /* Ocultar cabecera, menú, botón Deploy y pie/insignia de Streamlit y GitHub */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    #MainMenu,
    footer,
    .viewerBadge_container__1QSob,
    .styles_viewerBadge__CvC9N,
    div[class*="viewerBadge"],
    div[class*="StatusWidget"],
    a[href*="streamlit.io/cloud"],
    a[href*="github.com"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    /* Ajustar espacio superior limpio tras ocultar la cabecera */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)



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


def _open_pg_conn():
    pg_host = _find_secret("PG_HOST") or _find_secret("DB_HOST")
    pg_user = _find_secret("PG_USER") or _find_secret("DB_USER")
    pg_pass = _find_secret("PG_PASSWORD") or _find_secret("DB_PASSWORD")
    pg_port = int(_find_secret("PG_PORT") or _find_secret("DB_PORT") or 6543)
    pg_db = _find_secret("PG_DBNAME") or _find_secret("DB_NAME") or "postgres"

    if pg_host and pg_user and pg_pass:
        puertos = [pg_port, 6543] if pg_port != 6543 else [6543]
        for p_try in puertos:
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
            except Exception:
                pass
    return None


def _get_logo_b64():
    for path_try in ["static/LOGO CEI APP.png", "LOGO CEI APP.png"]:
        if os.path.exists(path_try):
            with open(path_try, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8"), "image/png"
    return "", ""


def _calcular_racha_y_categoria(usuario_est: str, conn) -> dict:
    total_folios = 0
    prom_global = 0.0
    semanas_activas = set()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_at, COALESCE(calificacion_global, 0.0)
                FROM lessons_folios
                WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                ORDER BY created_at DESC;
            """, (usuario_est,))
            rows = cur.fetchall()
            total_folios = len(rows)
            if total_folios > 0:
                suma_c = 0.0
                for fecha_dt, calif_val in rows:
                    suma_c += float(calif_val or 0.0)
                    if fecha_dt:
                        iso_y, iso_w, _ = fecha_dt.isocalendar()
                        semanas_activas.add((iso_y, iso_w))
                prom_global = round(suma_c / total_folios, 1)
    except Exception:
        pass

    hoy = datetime.now().date()
    hoy_y, hoy_w, _ = hoy.isocalendar()
    activo_semana = (hoy_y, hoy_w) in semanas_activas

    racha = 0
    cursor_d = hoy if activo_semana else (hoy - timedelta(days=7))
    while True:
        cy, cw, _ = cursor_d.isocalendar()
        if (cy, cw) in semanas_activas:
            racha += 1
            cursor_d -= timedelta(days=7)
        else:
            break

    if total_folios >= 15 and prom_global >= 90.0:
        cat_lbl = "🥇 Categoría Oro"
    elif total_folios >= 6 and prom_global >= 80.0:
        cat_lbl = "🥈 Categoría Plata"
    else:
        cat_lbl = "🥉 Categoría Bronce"

    return {
        "total_folios": total_folios,
        "promedio": prom_global,
        "racha_semanas": racha,
        "activo_esta_semana": activo_semana,
        "categoria_label": cat_lbl
    }


# ==============================================================================
# 1. LOGIN EXCLUSIVO DE SOCIOS AFILIADOS
# ==============================================================================
if "aff_portal_auth" not in st.session_state:
    st.session_state["aff_portal_auth"] = False
    st.session_state["aff_portal_user"] = ""
    st.session_state["aff_portal_role"] = ""

if not st.session_state["aff_portal_auth"]:
    b64_l, mime_l = _get_logo_b64()
    if b64_l:
        st.markdown(
            f'<div style="text-align:center;"><img src="data:{mime_l};base64,{b64_l}" style="width:105px;border-radius:20px;"></div>',
            unsafe_allow_html=True
        )
    st.markdown("<h4 style='text-align:center;margin-bottom:0;'>🏛️ CAREER ENGLISH INSTITUTE</h4>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:#0b2545;margin-top:4px;'>🤝 PORTAL DE SOCIOS AFILIADOS</h2>", unsafe_allow_html=True)
    st.divider()

    with st.form("form_login_portal_socios"):
        u_in = st.text_input("👤 Usuario de Socio Afiliado:")
        p_in = st.text_input("🔑 Clave de Acceso:", type="password")
        if st.form_submit_button("Ingresar a mi Portal", type="primary", width="stretch"):
            if not u_in.strip() or not p_in.strip():
                st.warning("⚠️ Ingresa tu usuario y clave de acceso.")
            else:
                m_u = _find_secret("OWNER_MASTER_USER")
                m_k = _find_secret("OWNER_MASTER_KEY")
                if m_u and m_k and u_in.strip().lower() == m_u.lower() and hmac.compare_digest(m_k, p_in.strip()):
                    st.session_state["aff_portal_auth"] = True
                    st.session_state["aff_portal_user"] = m_u
                    st.session_state["aff_portal_role"] = "Propietario"
                    st.rerun()

                conn_l = _open_pg_conn()
                if not conn_l:
                    st.error("❌ Sin conexión temporal con la base de datos institucional.")
                else:
                    try:
                        with conn_l.cursor() as cur:
                            cur.execute("""
                                SELECT usuario, clave_hash, rol, estatus
                                FROM users_padron
                                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s))
                                LIMIT 1;
                            """, (u_in.strip(),))
                            r_u = cur.fetchone()
                            if r_u:
                                usr_db, clv_db, rol_db, est_db = [str(x or "").strip() for x in r_u]
                                if hmac.compare_digest(clv_db, p_in.strip()):
                                    if est_db.lower() != "activo":
                                        st.error("⛔ Tu cuenta se encuentra Inactiva.")
                                    elif rol_db.lower() not in ["socio afiliado", "afiliado", "socio", "partner", "propietario", "owner", "administrador", "admin"]:
                                        st.error("⛔ Este portal es exclusivo para Socios Afiliados.")
                                    else:
                                        st.session_state["aff_portal_auth"] = True
                                        st.session_state["aff_portal_user"] = usr_db
                                        st.session_state["aff_portal_role"] = rol_db
                                        st.rerun()
                                else:
                                    st.error("🚨 Usuario o clave incorrectos.")
                            else:
                                st.error("🚨 Usuario o clave incorrectos.")
                    finally:
                        conn_l.close()
    st.stop()
# ==============================================================================
# 2. CABECERA INSTITUCIONAL Y PORTAL DE SOCIO AFILIADO (BLOQUE 2A DE 2)
# ==============================================================================
u_actual = st.session_state["aff_portal_user"]
rol_actual = st.session_state["aff_portal_role"]
es_admin_view = rol_actual.lower() in ["propietario", "owner", "administrador", "admin"]

c_h1, c_h2, c_h3 = st.columns([0.9, 4.2, 1.1])
with c_h1:
    b64_h, mime_h = _get_logo_b64()
    if b64_h:
        st.markdown(f'<img src="data:{mime_h};base64,{b64_h}" style="width:88px;border-radius:16px;">', unsafe_allow_html=True)
with c_h2:
    st.markdown("#### 🏛️ CAREER ENGLISH INSTITUTE — RED DE SOCIOS AFILIADOS")
    st.title("🤝 Portal Oficial de Socio Afiliado")
    st.caption(f"👤 Sesión Activa: **{u_actual}** • 🏷️ Rol: **{rol_actual}**")
with c_h3:
    if st.button("🚪 Salir", type="secondary", width="stretch"):
        st.session_state["aff_portal_auth"] = False
        st.session_state["aff_portal_user"] = ""
        st.rerun()

st.divider()

conn = _open_pg_conn()
if not conn:
    st.error("❌ Sin conexión con la base de datos institucional.")
    st.stop()

try:
    aff_objetivo = u_actual
    if es_admin_view:
        with conn.cursor() as cur:
            cur.execute("SELECT usuario_login FROM affiliate_partners ORDER BY nombre ASC;")
            lista_s = [str(row_s[0]).strip() for row_s in cur.fetchall() if row_s and row_s[0]]
        if lista_s:
            aff_objetivo = st.selectbox("Seleccionar Socio Afiliado a visualizar:", lista_s)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT affiliate_id, usuario_login, nombre, apellido_paterno, apellido_materno,
                   COALESCE(rfc, ''), COALESCE(telefono, ''), COALESCE(email, ''),
                   COALESCE(domicilio, ''), COALESCE(estatus, 'Activo'),
                   COALESCE(porcentaje_default, 0.0), terminos_aceptados_at
            FROM affiliate_partners
            WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
            LIMIT 1;
        """, (aff_objetivo,))
        s_dat = cur.fetchone()

    if not s_dat:
        st.warning("ℹ️ No se encontró expediente de Socio Afiliado para este usuario.")
        st.stop()

    (
        aff_id_v, _aff_usr_v, aff_nom_v, aff_pat_v, aff_mat_v,
        aff_rfc_v, aff_tel_v, aff_mail_v, aff_dom_v,
        aff_est_v, aff_pct_v, _aff_terms_v
    ) = (list(s_dat) + ["", "", "", "", "", "", "", "", "", "Activo", 0.0, None])[:12]

    st.info(
        f"🆔 **ID Afiliado:** `{aff_id_v}`  |  👤 **Titular:** **{aff_nom_v} {aff_pat_v} {aff_mat_v or ''}**\n\n"
        f"🧾 **RFC:** `{aff_rfc_v or 'No registrado'}`  |  📞 **Tel:** `{aff_tel_v or '—'}`  |  ✉️ **Email:** `{aff_mail_v or '—'}`\n\n"
        f"📍 **Domicilio:** {aff_dom_v or 'No registrado'}\n\n"
        f"💼 **Comisión Asignada:** **`{float(aff_pct_v or 0.0):.1f}%`**  |  🏷️ **Estatus:** `{aff_est_v}`\n\n"
        "📄 *Recordatorio Fiscal: Expedir factura electrónica (CFDI) vigente para cobro de comisiones.*"
    )

    raw_ins_base = str(_find_secret("STUDENT_REG_URL") or "").strip().rstrip("/")
    url_ins_base = (
        raw_ins_base
        if "inscripcioncei.streamlit.app" in raw_ins_base
        else ("https://" + "inscripcioncei.streamlit.app")
    )
    sep_q = "&" if "?" in url_ins_base else "?"
    url_qr_alumnos = f"{url_ins_base}{sep_q}ref_aff={urllib.parse.quote(str(aff_id_v).strip())}"

    raw_app_qr = str(_find_secret("APP_INSTALL_QR_URL") or "").strip()
    url_qr_app = (
        raw_app_qr
        if "drzumaya.github.io" in raw_app_qr
        else ("https://" + "drzumaya.github.io/My-CEI-English-Reading-Improvement-Tool/")
    )

    buf_q1 = io.BytesIO()
    qrcode.make(url_qr_alumnos).save(buf_q1, format="PNG")
    buf_q2 = io.BytesIO()
    qrcode.make(url_qr_app).save(buf_q2, format="PNG")


    c_qr_left, c_qr_right = st.columns(2)
    with c_qr_left:
        with st.container(border=True):
            st.markdown("##### 📲 Tu QR Oficial de Inscripción de Alumnos")
            st.caption(f"Ligado automáticamente a tu ID **`{aff_id_v}`** para acreditar tus comisiones.")
            st.image(buf_q1.getvalue(), width=175)
            st.code(url_qr_alumnos, language="text")
            st.download_button(
                "⬇️ Descargar QR Inscripción (PNG)",
                data=buf_q1.getvalue(),
                file_name=f"QR_Inscripcion_{aff_id_v}.png",
                mime="image/png",
                width="stretch"
            )
    with c_qr_right:
        with st.container(border=True):
            st.markdown("##### 📱 QR Oficial de Descarga de App Estudiantes")
            st.caption("Compártelo con tus alumnos inscritos para instalar la App CEI en su celular o Mac.")
            st.image(buf_q2.getvalue(), width=175)
            st.link_button(
                "📲 Abrir Instalador Oficial App CEI",
                url=url_qr_app,
                width="stretch"
            )
            st.download_button(
                "⬇️ Descargar QR App CEI (PNG)",
                data=buf_q2.getvalue(),
                file_name="QR_Instalar_App_CEI.png",
                mime="image/png",
                width="stretch"
            )

    # ==========================================================================
    # BLOQUE 2B DE 2 (FINAL): ALUMNOS INSCRITOS, RACHAS ORO, PAGOS Y WHATSAPP
    # ==========================================================================
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE users_padron
            ADD COLUMN IF NOT EXISTS telefono TEXT DEFAULT '',
            ADD COLUMN IF NOT EXISTS socio_afiliado TEXT DEFAULT '';
        """)
        cur.execute("SELECT * FROM users_padron ORDER BY id DESC;")
        col_names = [desc for desc in cur.description]
        all_rows = cur.fetchall()

    referidos = []
    targets_aff = {str(aff_objetivo or "").strip().lower(), str(aff_id_v or "").strip().lower()} - {""}
    for row_raw in all_rows:
        r_dict = dict(zip(col_names, row_raw))
        rol_val = str(r_dict.get("rol") or "").strip().lower()
        aff_val = str(r_dict.get("socio_afiliado") or r_dict.get("afiliado") or "").strip().lower()
        if rol_val in ("estudiante", "student", "alumno") and aff_val in targets_aff:
            u_val = str(r_dict.get("usuario") or "").strip()
            nom_val = str(r_dict.get("nombre_completo") or r_dict.get("nombre") or u_val).strip()
            mat_val = str(r_dict.get("matricula") or "").strip()
            niv_val = str(r_dict.get("nivel") or r_dict.get("nivel_cefr") or r_dict.get("cefr") or "B1").strip()
            tel_val = str(r_dict.get("telefono") or r_dict.get("whatsapp") or "").strip()
            referidos.append((u_val, nom_val, mat_val, niv_val, tel_val))

    pagos_map = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM student_payments;")
            pay_cols = [desc for desc in cur.description]
            pay_rows = cur.fetchall()
            for pr_raw in pay_rows:
                pd = dict(zip(pay_cols, pr_raw))
                u_pay = str(pd.get("usuario_estudiante") or pd.get("usuario") or pd.get("student_user") or "").strip().lower()
                est_p = str(pd.get("estatus") or "pagado").strip().lower()
                if u_pay and est_p in ("pagado", "completado", "activo"):
                    monto_p = float(pd.get("monto_total") or pd.get("monto") or pd.get("importe") or 0.0)
                    fecha_p = str(pd.get("fecha_pago") or pd.get("created_at") or "")[:10]
                    if u_pay not in pagos_map:
                        pagos_map[u_pay] = {"bloques": 0, "monto": 0.0, "ultimo": ""}
                    pagos_map[u_pay]["bloques"] += 1
                    pagos_map[u_pay]["monto"] += monto_p
                    if fecha_p > pagos_map[u_pay]["ultimo"]:
                        pagos_map[u_pay]["ultimo"] = fecha_p
    except Exception:
        pass


    pct_com = float(aff_pct_v or 0.0)
    total_recaudado = 0.0
    gam_cache = {}
    oro_count = 0

    for est_u_raw, _nom, _mat, _niv, _tel in referidos:
        est_key = str(est_u_raw or "").strip()
        total_recaudado += pagos_map.get(est_key.lower(), {}).get("monto", 0.0)
        g_e = _calcular_racha_y_categoria(est_key, conn)
        gam_cache[est_key] = g_e
        if "oro" in g_e["categoria_label"].lower():
            oro_count += 1

    comision_total = round(total_recaudado * (pct_com / 100.0), 2)

    st.divider()
    k1, k2 = st.columns(2)
    k1.metric("🎓 Alumnos Inscritos", f"{len(referidos)}")
    k2.metric("🥇 En Categoría Oro", f"{oro_count} / {len(referidos)}")
    k3, k4 = st.columns(2)
    k3.metric("💼 Tasa Comisión", f"{pct_com:.1f}%")
    k4.metric("💰 Comisión Generada", f"${comision_total:,.2f}")

    with st.container(border=True):
        st.markdown("##### 🔥 Seguimiento 200%: Rachas Oro, Pagos (9 Bloques) y WhatsApp Directo")
        if not referidos:
            st.info("ℹ️ Aún no tienes estudiantes inscritos con tu Código QR oficial.")
        else:
            app_pub = str(_find_secret("PUBLIC_APP_URL") or ("https://" + "myceigrammarly.streamlit.app")).strip()
            for r_est in referidos:
                est_u, est_nom, est_mat, est_niv, est_tel = [str(x or "").strip() for x in r_est]
                g_est = gam_cache[est_u]
                p_est = pagos_map.get(est_u.lower(), {"bloques": 0, "monto": 0.0, "ultimo": ""})
                bloq = min(9, p_est["bloques"])
                com_ind = round(p_est["monto"] * (pct_com / 100.0), 2)

                semaforo = (
                    "🏆 Liquidado (9/9)" if bloq >= 9
                    else (f"🟢 Al Corriente ({bloq}/9)" if bloq >= 1 else "🟡 Pendiente 1er Bloque (0/9)")
                )

                digs = "".join(c for c in est_tel if c.isdigit())
                if len(digs) == 10:
                    digs = f"52{digs}"

                msg_mot = (
                    f"¡Hola {est_nom}! 👋 Te saluda tu asesor de *Career English Institute (CEI)*. "
                    f"¡Excelente avance! Llevas *{g_est['racha_semanas']} semana(s)* de racha, *{g_est['total_folios']} lecciones* "
                    f"y estás en *{g_est['categoria_label']}*. ¡Sigue practicando esta semana para alcanzar la *Categoría Oro*! 🚀 {app_pub}"
                )
                msg_pag = (
                    f"¡Hola {est_nom}! 👋 Te saluda tu asesor de *Career English Institute (CEI)*. "
                    f"Vas en *{bloq}/9 bloques* y categoría *{g_est['categoria_label']}*. "
                    f"Recuerda mantener al corriente tu siguiente bloque para conservar tus beneficios y seguir sumando hacia *Oro*. {app_pub}"
                )
                wa_mot = f"https://wa.me{digs}?text={urllib.parse.quote(msg_mot)}" if digs else f"https://wa.me?text={urllib.parse.quote(msg_mot)}"
                wa_pag = f"https://wa.me{digs}?text={urllib.parse.quote(msg_pag)}" if digs else f"https://wa.me?text={urllib.parse.quote(msg_pag)}"

                with st.container(border=True):
                    st.markdown(
                        f"**🎓 {est_nom}** (`{est_u}`)"
                        + (f" • 🆔 `{est_mat}`" if est_mat else "")
                        + f" • Nivel **{est_niv}**"
                    )
                    fuego_txt = "🔥 Activa" if g_est["activo_esta_semana"] else "⏳ Pendiente"
                    st.markdown(
                        f"🏅 **{g_est['categoria_label']}** | 🔥 Racha: **{g_est['racha_semanas']} sem.** ({fuego_txt}) | "
                        f"📚 Folios: **{g_est['total_folios']}**\n\n"
                        f"💳 **Pagos:** {semaforo} | 💰 **Comisión generada:** **`${com_ind:,.2f}`**"
                        + (f" *(Último pago: `{p_est['ultimo']}`)*" if p_est["ultimo"] else "")
                    )
                    cb1, cb2 = st.columns(2)
                    with cb1:
                        st.link_button("🔥 Motivar Meta Oro (WhatsApp)", url=wa_mot, width="stretch")
                    with cb2:
                        st.link_button("💳 Seguimiento Pago (WhatsApp)", url=wa_pag, width="stretch")
finally:
    conn.close()
