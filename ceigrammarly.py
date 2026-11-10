import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import qrcode
from PIL import Image, ImageDraw
from fpdf import FPDF
import io
import os
import json
import random
import base64
import hashlib
import hmac
import tempfile
import urllib.parse
import requests
from datetime import datetime
import gspread
import pandas as pd
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="CEFR Academic Grammar & Discourse System - Career English Institute",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_ADDRESS = "Calle 34, Av. 27, S/N, D2, Col. Buenos Aires, Agua Prieta, Son. C.P. 84269. | Tel. / Contacto: 6331349339"
ROLES_LISTA = ["Estudiante", "Teacher", "Propietario", "Administrador", "Empleado"]
GRADOS_ACADEMICOS = [
    "Preescolar",
    "Primaria",
    "Secundaria",
    "Preparatoria / Bachillerato",
    "Licenciatura / Universidad",
    "Maestría / Posgrado",
    "Doctorado / Investigación"
]

CAPABILITY_COLS = [
    "Ver_Panel_Admin",
    "Registrar_Usuarios",
    "Editar_Permisos",
    "Emitir_Certificados",
    "Revocar_Certificados",
    "Editar_Instituto_Logo",
    "Previsualizar_A1_C2",
    "Reuso_Ilimitado_Folios"
]

DEFAULT_PERMISSIONS_MATRIX = [
    ["Total",        "SI", "SI", "SI", "SI", "SI", "SI", "SI", "SI"],
    ["Academico",    "SI", "SI", "NO", "SI", "NO", "NO", "SI", "SI"],
    ["Certificador", "SI", "NO", "NO", "SI", "SI", "NO", "NO", "SI"],
    ["Auditoria",    "SI", "NO", "NO", "NO", "NO", "NO", "SI", "SI"],
    ["Basico",       "NO", "NO", "NO", "NO", "NO", "NO", "NO", "NO"]
]

# --- CLIENTE GLOBAL DE GOOGLE SHEETS ---
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(creds_dict)

def get_spreadsheet():
    return get_gspread_client().open_by_key(st.secrets["spreadsheet_key"])

def get_google_sheet():
    return get_spreadsheet().sheet1

def get_padron_sheet():
    return get_spreadsheet().worksheet("Padron_Estudiantes")

def get_certificados_sheet():
    ss = get_spreadsheet()
    try:
        return ss.worksheet("Certificados")
    except Exception:
        ws = ss.add_worksheet(title="Certificados", rows=200, cols=9)
        ws.append_row([
            "Folio_Certificado", "Clave_Alumno", "Nombre_Estudiante", "Nivel_CEFR",
            "Programa_Curso", "Calificacion", "Fecha_Emision", "Sello_Digital_SHA256", "Estatus"
        ])
        return ws

def get_permisos_sheet():
    ss = get_spreadsheet()
    try:
        return ss.worksheet("Matriz_Permisos")
    except Exception:
        ws = ss.add_worksheet(title="Matriz_Permisos", rows=50, cols=9)
        ws.append_row(["Perfil_Permiso"] + CAPABILITY_COLS)
        for fila in DEFAULT_PERMISSIONS_MATRIX:
            ws.append_row(fila)
        return ws

@st.cache_data(ttl=120)
def load_permissions_matrix():
    try:
        records = get_permisos_sheet().get_all_records()
        matrix = {}
        for r in records:
            perfil = str(r.get("Perfil_Permiso", "")).strip()
            if perfil:
                matrix[perfil] = {
                    cap: (str(r.get(cap, "NO")).strip().upper() == "SI")
                    for cap in CAPABILITY_COLS
                }
        if matrix:
            return matrix
    except Exception:
        pass
    return {
        row[0]: {cap: (row[i + 1] == "SI") for i, cap in enumerate(CAPABILITY_COLS)}
        for row in DEFAULT_PERMISSIONS_MATRIX
    }

def resolve_permission_profile(raw_perm, raw_role, matrix_dict):
    p = str(raw_perm or "").strip()
    for k in matrix_dict.keys():
        if k.lower() == p.lower():
            return k
    r = str(raw_role or "").strip().lower()
    if r in ["propietario", "administrador", "admin"] and "Total" in matrix_dict:
        return "Total"
    if r == "teacher" and "Academico" in matrix_dict:
        return "Academico"
    return "Basico" if "Basico" in matrix_dict else list(matrix_dict.keys())[-1]
# --- COMPRESIÓN DE IMÁGENES ---
def compress_bytes_image(raw_bytes, max_size=(640, 400), quality=75):
    try:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return raw_bytes

def compress_logo_to_base64(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img.thumbnail((240, 240), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        if len(b64_str) <= 40000:
            return b64_str, "image/png"
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg

    img = img.convert("RGB")
    img.thumbnail((240, 240), Image.Resampling.LANCZOS)
    quality = 80
    while quality >= 30:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        if len(b64_str) <= 40000:
            return b64_str, "image/jpeg"
        quality -= 10
    return b64_str, "image/jpeg"

@st.cache_data(ttl=300)
def load_permanent_logo():
    try:
        sheet_logo = get_spreadsheet().worksheet("Config_Logo")
        records = sheet_logo.get_all_records()
        if records:
            return records[-1]
    except Exception:
        pass
    return None

def save_permanent_config(b64_str, mime, width, shape, address_str):
    ss = get_spreadsheet()
    try:
        sheet_logo = ss.worksheet("Config_Logo")
    except Exception:
        sheet_logo = ss.add_worksheet(title="Config_Logo", rows=10, cols=5)
    sheet_logo.clear()
    sheet_logo.append_row(["Logo_Base64", "Mime_Type", "Width", "Shape", "Direccion"])
    sheet_logo.append_row([b64_str, mime, width, shape, address_str])
    load_permanent_logo.clear()

def get_default_logo_b64():
    try:
        with open("LOGO CEI APP.png", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8"), "image/png"
    except Exception:
        return None, None

# --- MOTOR DE TIMBRADO CRIPTOGRÁFICO (HMAC-SHA256) Y CERTIFICADO PDF ---
def generar_sello_digital(folio_cert, clave_est, nombre_est, nivel_cefr, fecha_emision):
    llave_maestra = str(st.secrets.get("spreadsheet_key", "CEI-2026-MASTER-SEAL")).encode("utf-8")
    cadena_original = f"||CEI|{folio_cert}|{clave_est}|{nombre_est}|{nivel_cefr}|{fecha_emision}|JACOB-ZUMAYA-PRIANTI||"
    sello_hex = hmac.new(llave_maestra, cadena_original.encode("utf-8"), hashlib.sha256).hexdigest().upper()
    return cadena_original, sello_hex

def generar_pdf_certificado(folio_cert, clave_est, nombre_est, nivel_cefr, programa, calificacion, fecha_emision, cadena_orig, sello_sha256, address_str):
    verify_url = f"https://streamlit.app{folio_cert}"
    qr = qrcode.QRCode(version=2, box_size=5, border=1)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#0b2545", back_color="white")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_qr:
        img_qr.save(tmp_qr.name, format="PNG")
        qr_path = tmp_qr.name

    logo_path = "LOGO CEI APP.png" if os.path.exists("LOGO CEI APP.png") else None

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_author("Jacob Zumaya Prianti")
    pdf.set_creator("Career English Institute - Digital Credentialing System")
    pdf.add_page()

    pdf.set_draw_color(11, 37, 69)
    pdf.set_line_width(1.5)
    pdf.rect(8, 8, 281, 194)
    pdf.set_draw_color(184, 134, 11)
    pdf.set_line_width(0.6)
    pdf.rect(11, 11, 275, 188)

    if logo_path:
        try:
            pdf.image(logo_path, x=18, y=16, w=26)
        except Exception:
            pass

    pdf.image(qr_path, x=250, y=16, w=28)
    pdf.set_xy(242, 45)
    pdf.set_font("Helvetica", "B", 6.5)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(44, 4, txt="SCAN TO VERIFY AUTHENTICITY", align="C")

    pdf.set_xy(10, 17)
    pdf.set_font("Times", "B", 20)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(277, 9, txt="CAREER ENGLISH INSTITUTE", ln=True, align="C")
    
    pdf.set_font("Times", "I", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(277, 5, txt=address_str.encode("latin-1", "replace").decode("latin-1"), ln=True, align="C")

    pdf.ln(3)
    pdf.set_font("Times", "B", 15)
    pdf.set_text_color(184, 134, 11)
    pdf.cell(277, 8, txt="CERTIFICATE OF ACADEMIC PROFICIENCY & CEFR ACHIEVEMENT", ln=True, align="C")

    pdf.ln(2)
    pdf.set_font("Times", "I", 12)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(277, 7, txt="This official credential is proudly awarded to:", ln=True, align="C")

    pdf.ln(2)
    pdf.set_font("Times", "B", 24)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(277, 12, txt=nombre_est.upper().encode("latin-1", "replace").decode("latin-1"), ln=True, align="C")

    pdf.set_font("Times", "B", 11)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(277, 6, txt=f"Student Registry ID / Clave: {clave_est}  |  Certified Proficiency Level: {nivel_cefr}", ln=True, align="C")

    pdf.ln(2)
    pdf.set_font("Times", "", 11.5)
    pdf.set_text_color(30, 30, 30)
    cuerpo_cert = (
        f"For having successfully completed the academic requirements, applied grammar, and discourse assessments of:\n"
        f"{programa} (Final Evaluation Score: {calificacion}), aligned with the Common European Framework of Reference for Languages (CEFR)."
    )
    pdf.multi_cell(240, 6, txt=cuerpo_cert.encode("latin-1", "replace").decode("latin-1"), align="C")

    pdf.ln(8)
    y_firma = pdf.get_y()
    pdf.set_draw_color(50, 50, 50)
    pdf.set_line_width(0.4)
    pdf.line(45, y_firma + 8, 125, y_firma + 8)
    pdf.line(170, y_firma + 8, 250, y_firma + 8)

    pdf.set_xy(45, y_firma + 9)
    pdf.set_font("Times", "B", 10.5)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(80, 5, txt="Jacob Zumaya Prianti", align="C")
    pdf.set_xy(45, y_firma + 14)
    pdf.set_font("Times", "I", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(80, 4, txt="Director & Senior Applied Linguist", align="C")

    pdf.set_xy(170, y_firma + 9)
    pdf.set_font("Times", "B", 10.5)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(80, 5, txt="Academic Board & Registry", align="C")
    pdf.set_xy(170, y_firma + 14)
    pdf.set_font("Times", "I", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(80, 4, txt=f"Issued: {fecha_emision} | Folio: {folio_cert}", align="C")

    pdf.set_xy(15, 166)
    pdf.set_fill_color(242, 245, 249)
    pdf.rect(15, 165, 267, 29, style="F")
    
    pdf.set_xy(18, 166.5)
    pdf.set_font("Courier", "B", 7.5)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(260, 4, txt=f"TIMBRE DIGITAL INSTITUCIONAL | FOLIO: {folio_cert} | VALIDATION URL: {verify_url}", ln=True)
    
    pdf.set_x(18)
    pdf.set_font("Courier", "", 6.8)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(260, 3.5, txt=f"Cadena Original: {cadena_orig.encode('latin-1', 'replace').decode('latin-1')}")
    
    pdf.set_x(18)
    pdf.set_font("Courier", "B", 7)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(260, 4, txt=f"Sello Digital Criptografico (HMAC-SHA256): {sello_sha256}", ln=True)

    pdf_out = pdf.output(dest="S").encode("latin-1")
    try:
        os.remove(qr_path)
    except Exception:
        pass
    return pdf_out
# --- DETECCIÓN DE DISPOSITIVO ---
user_agent = st.context.headers.get("User-Agent", "").lower()
is_mobile = any(device in user_agent for device in ["iphone", "android", "ipad", "mobile"])

CEFR_MAP = {
    "A1": "A1 (Beginner)",
    "A2": "A2 (Elementary)",
    "B1": "B1 (Intermediate)",
    "B2": "B2 (Upper-Intermediate)",
    "C1": "C1 (Advanced)",
    "C2": "C2 (Proficiency)"
}

def normalize_cefr(raw_val):
    code = str(raw_val).strip().upper()[:2]
    return CEFR_MAP.get(code, "B1 (Intermediate)")

# --- INICIALIZACIÓN DE ESTADOS ---
for key, default in [
    ("authenticated", False), ("current_user", ""), ("user_role", "Estudiante"),
    ("user_permissions", "Basico"), ("user_assigned_level", "B1 (Intermediate)"),
    ("user_academic_grade", "Licenciatura / Universidad"),
    ("selected_academic_grade", "Licenciatura / Universidad"),
    ("generated_text", ""), ("image_bytes", None), ("audio_bytes", None),
    ("app_exited", False), ("show_saved_audios", False), ("quiz_data", None),
    ("quiz_graded", False), ("quiz_score", None), ("quiz_user_answers", {}),
    ("pending_ls_token", None), ("selected_cefr", "B1 (Intermediate)"),
    ("show_teacher_registry", False), ("current_folio", ""),
    ("current_pdf_link", ""), ("current_creation_date", "")
]:
    if key not in st.session_state:
        st.session_state[key] = default
    if "show_qr" not in st.session_state:
       st.session_state.show_qr = True


# --- CARGAR CONFIGURACIÓN DEL INSTITUTO ---
saved_cfg = load_permanent_logo()
institute_address = str(saved_cfg.get("Direccion", "")).strip() if (saved_cfg and saved_cfg.get("Direccion")) else DEFAULT_ADDRESS

# --- PORTAL PÚBLICO DE VERIFICACIÓN DE CERTIFICADOS (ACCESO POR QR SIN LOGIN) ---
verify_folio = st.query_params.get("verify", "").strip().upper()
if verify_folio:
    col_vl, col_vc, col_vr = st.columns([1, 2.2, 1])
    with col_vc:
        b64_l, mime_l = (saved_cfg["Logo_Base64"], saved_cfg["Mime_Type"]) if (saved_cfg and saved_cfg.get("Logo_Base64")) else get_default_logo_b64()
        if b64_l:
            st.markdown(f'<div style="text-align: center;"><img src="data:{mime_l};base64,{b64_l}" style="width: 110px; border-radius: 50%;"></div>', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>🏛️ CAREER ENGLISH INSTITUTE</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #555; font-size: 12px;'>📍 {institute_address}</p>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🛡️ DIGITAL CREDENTIAL VERIFICATION PORTAL</h2>", unsafe_allow_html=True)
        st.divider()

        try:
            with st.spinner(f"Validando sello criptográfico del certificado {verify_folio}..."):
                certs = get_certificados_sheet().get_all_records()
                cert_encontrado = next((c for c in certs if str(c.get("Folio_Certificado", "")).strip().upper() == verify_folio), None)

                if cert_encontrado:
                    estatus_c = str(cert_encontrado.get("Estatus", "Vigente")).strip()
                    clave_c = str(cert_encontrado.get("Clave_Alumno", "")).strip()
                    nombre_c = str(cert_encontrado.get("Nombre_Estudiante", "")).strip()
                    nivel_c = str(cert_encontrado.get("Nivel_CEFR", "")).strip()
                    prog_c = str(cert_encontrado.get("Programa_Curso", "")).strip()
                    calif_c = str(cert_encontrado.get("Calificacion", "")).strip()
                    fecha_c = str(cert_encontrado.get("Fecha_Emision", "")).strip()
                    sello_bd = str(cert_encontrado.get("Sello_Digital_SHA256", "")).strip()

                    _, sello_recalculado = generar_sello_digital(verify_folio, clave_c, nombre_c, nivel_c, fecha_c)

                    if sello_bd == sello_recalculado and estatus_c.lower() == "vigente":
                        st.success("✅ **CERTIFICADO AUTÉNTICO Y VERIFICADO CRIPTOGRÁFICAMENTE**")
                        with st.container(border=True):
                            st.markdown(f"**🔖 Folio Oficial:** `{verify_folio}`")
                            st.markdown(f"**👤 Titular / Student:** {nombre_c}")
                            st.markdown(f"**🔑 Clave de Registro:** `{clave_c}`")
                            st.markdown(f"**🎯 Nivel Certificado (CEFR):** {nivel_c}")
                            st.markdown(f"**📚 Programa / Módulo:** {prog_c}")
                            st.markdown(f"**🏆 Calificación Final:** {calif_c}")
                            st.markdown(f"**📅 Fecha de Timbrado:** {fecha_c}")
                            st.markdown(f"**✍️ Autoridad Emisora:** Jacob Zumaya Prianti (Career English Institute)")
                            st.divider()
                            st.caption("**Sello Digital HMAC-SHA256 Verificado:**")
                            st.code(sello_bd, language="text")
                    else:
                        st.error("⛔ **ALERTA DE SEGURIDAD:** El sello digital no coincide o el certificado fue revocado.")
                else:
                    st.error(f"❌ No existe ningún certificado registrado con el Folio `{verify_folio}`.")
        except Exception as e:
            st.error(f"Error al verificar certificado: {e}")

        st.write("")
        if st.button("🏛️ Ir a la Plataforma Principal", width="stretch"):
            st.query_params.clear()
            st.rerun()
    st.stop()

# --- CAPTURA DE FOLIO DE LECCIÓN DESDE URL ---
url_folio = st.query_params.get("folio", "")
if url_folio and not st.session_state.current_folio:
    st.session_state.current_folio = str(url_folio).strip().upper()
# --- CARGAR MATRIZ GLOBAL DE PERMISOS ---
PERMISSIONS_MATRIX = load_permissions_matrix()
PERMISOS_LISTA = list(PERMISSIONS_MATRIX.keys())

# --- ESCRITURA INVISIBLE EN LOCALSTORAGE ---
if st.session_state.pending_ls_token is not None:
    if st.session_state.pending_ls_token == "REMOVE":
        streamlit_js_eval(js_expressions="localStorage.removeItem('cei_auth_token')", key="rm_ls_init")
    else:
        streamlit_js_eval(js_expressions=f"localStorage.setItem('cei_auth_token', '{st.session_state.pending_ls_token}')", key="sv_ls_init")
    st.session_state.pending_ls_token = None

# --- RECUPERACIÓN INVISIBLE DE SESIÓN ---
if not st.session_state.authenticated and not st.session_state.app_exited:
    saved_token = streamlit_js_eval(js_expressions="localStorage.getItem('cei_auth_token')", key="get_ls_token")
    if saved_token and isinstance(saved_token, str):
        try:
            decoded_json = base64.urlsafe_b64decode(saved_token.encode("utf-8")).decode("utf-8")
            token_data = json.loads(decoded_json)
            u_tok, c_tok = token_data.get("u", ""), token_data.get("c", "")
            if u_tok and c_tok:
                for reg in get_padron_sheet().get_all_records():
                    if (str(reg.get("Usuario", "")).strip().lower() == u_tok.lower() and
                        str(reg.get("Clave", "")).strip() == c_tok and
                        str(reg.get("Estatus", "Activo")).strip().lower() == "activo"):
                        r_db = str(reg.get("Rol", "Estudiante")).strip()
                        p_db = resolve_permission_profile(reg.get("Permisos", ""), r_db, PERMISSIONS_MATRIX)
                        lvl_norm = normalize_cefr(reg.get("Nivel", "B1"))
                        g_db = str(reg.get("Grado_Academico", "Licenciatura / Universidad")).strip() or "Licenciatura / Universidad"
                        
                        st.session_state.authenticated = True
                        st.session_state.current_user = str(reg.get("Usuario", "")).strip()
                        st.session_state.user_role = r_db
                        st.session_state.user_permissions = p_db
                        st.session_state.user_assigned_level = lvl_norm
                        st.session_state.selected_cefr = lvl_norm
                        st.session_state.user_academic_grade = g_db
                        st.session_state.selected_academic_grade = g_db
                        st.rerun()
        except Exception:
            pass

# --- PANTALLA DE SALIDA ---
if st.session_state.app_exited:
    streamlit_js_eval(js_expressions="localStorage.removeItem('cei_auth_token')", key="exit_rm_ls")
    st.title("👋 Academic Session Ended")
    st.info("Thank you for using the CEFR Academic Grammar & Discourse System by CAREER ENGLISH INSTITUTE.")
    st.caption(f"📍 {institute_address} | © 2026 CAREER ENGLISH INSTITUTE. Author: Jacob Zumaya Prianti.")
    if st.button("Volver al Inicio de Sesión"):
        st.session_state.app_exited = False
        st.session_state.authenticated = False
        st.rerun()
    st.stop()

# --- PANTALLA DE LOGIN ---
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        b64_l, mime_l = (saved_cfg["Logo_Base64"], saved_cfg["Mime_Type"]) if (saved_cfg and saved_cfg.get("Logo_Base64")) else get_default_logo_b64()
        if b64_l:
            st.markdown(f'<div style="text-align: center;"><img src="data:{mime_l};base64,{b64_l}" style="width: 115px; border-radius: 50%;"></div>', unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center;'>🏛️ CAREER ENGLISH INSTITUTE</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #555; font-size: 13px;'>📍 {institute_address}</p>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🎓 CEFR ACADEMIC GRAMMAR & DISCOURSE SYSTEM</h2>", unsafe_allow_html=True)
        st.divider()
        
        with st.form("login_form"):
            st.subheader("🔐 Control de Acceso Académico")
            input_user = st.text_input("👤 Usuario registrado:")
            input_pass = st.text_input("🔑 Clave de Acceso:", type="password")
            remember_me = st.checkbox("💾 Recordar mi usuario y contraseña en este navegador", value=True)
            submit_login = st.form_submit_button("Ingresar a la Plataforma", type="primary", width="stretch")
            
            if submit_login:
                if not input_user or not input_pass:
                    st.warning("⚠️ Ingresa tu Usuario y Clave de Acceso.")
                else:
                    try:
                        with st.spinner("Verificando credenciales, grado académico y permisos..."):
                            registros = get_padron_sheet().get_all_records()
                            acceso_valido = False
                            for reg in registros:
                                u_db = str(reg.get("Usuario", "")).strip()
                                c_db = str(reg.get("Clave", "")).strip()
                                e_db = str(reg.get("Estatus", "Activo")).strip().lower()
                                r_db = str(reg.get("Rol", "Estudiante")).strip()
                                p_db = resolve_permission_profile(reg.get("Permisos", ""), r_db, PERMISSIONS_MATRIX)
                                n_db = normalize_cefr(reg.get("Nivel", "B1"))
                                g_db = str(reg.get("Grado_Academico", "Licenciatura / Universidad")).strip() or "Licenciatura / Universidad"
                                
                                if u_db.lower() == input_user.strip().lower() and c_db == input_pass.strip():
                                    if e_db == "activo":
                                        st.session_state.authenticated = True
                                        st.session_state.current_user = u_db
                                        st.session_state.user_role = r_db
                                        st.session_state.user_permissions = p_db
                                        st.session_state.user_assigned_level = n_db
                                        st.session_state.selected_cefr = n_db
                                        st.session_state.user_academic_grade = g_db
                                        st.session_state.selected_academic_grade = g_db
                                        if remember_me:
                                            payload = json.dumps({"u": u_db, "c": c_db}).encode("utf-8")
                                            st.session_state.pending_ls_token = base64.urlsafe_b64encode(payload).decode("utf-8")
                                        else:
                                            st.session_state.pending_ls_token = "REMOVE"
                                        acceso_valido = True
                                        break
                                    else:
                                        st.error("⛔ Tu cuenta se encuentra inactiva.")
                                        acceso_valido = None
                                        break
                            if acceso_valido is True:
                                st.rerun()
                            elif acceso_valido is False:
                                st.error("❌ Usuario o Clave incorrectos.")
                    except Exception as e:
                        st.error(f"Error al conectar con 'Padron_Estudiantes': {e}")
        st.markdown(f"<div style='text-align: center; color: #777; font-size: 12px; margin-top: 15px;'>📍 {institute_address}<br>© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti</div>", unsafe_allow_html=True)
    st.stop()
# --- EVALUACIÓN DINÁMICA DE CAPACIDADES ---
user_caps = PERMISSIONS_MATRIX.get(st.session_state.user_permissions, {})
def can(capability_name):
    return bool(user_caps.get(capability_name, False))

is_faculty_desktop = can("Ver_Panel_Admin") and (not is_mobile)
has_faculty_access = can("Reuso_Ilimitado_Folios")

cefr_options = list(CEFR_MAP.values())

# --- BARRA IZQUIERDA (INPUTS DEL ALGORITMO) ---
with st.sidebar:
    st.markdown("### 🏛️ CAREER ENGLISH INSTITUTE")
    st.caption(f"📍 {institute_address}")
    st.success(f"👤 **{st.session_state.current_user}**\n\n🏷️ *{st.session_state.user_role}* | 🛡️ Perfil: **{st.session_state.user_permissions}**")
    st.divider()

    st.header("⚙️ Academic Parameters")
    usuario = st.session_state.current_user

    if can("Previsualizar_A1_C2") and (not is_mobile):
        st.subheader("🎯 Target Calibration (Faculty)")
        default_idx = cefr_options.index(st.session_state.user_assigned_level) if st.session_state.user_assigned_level in cefr_options else 2
        cefr_level = st.selectbox("Select CEFR Level (A1 - C2):", cefr_options, index=default_idx)
        
        g_idx = GRADOS_ACADEMICOS.index(st.session_state.user_academic_grade) if st.session_state.user_academic_grade in GRADOS_ACADEMICOS else 4
        academic_grade = st.selectbox("Select Academic Grade:", GRADOS_ACADEMICOS, index=g_idx)
    else:
        cefr_level = st.session_state.user_assigned_level
        academic_grade = st.session_state.user_academic_grade
        st.info(f"🎯 **CEFR Level:** {cefr_level}\n\n🎓 **Academic Grade:** {academic_grade}")

    st.subheader("1. Context & Characters (Español / English)")
    contexto = st.text_input("Contexto / Lugar / Tema:", placeholder="Ej: En un aeropuerto en Londres / At an airport")
    personas = st.text_input("Personas / Personajes:", placeholder="Ej: Un turista y una azafata / A tourist and a pilot")
    
    st.subheader("2. Subject Matter (Español / English)")
    asunto = st.text_input("Asunto / Materia:", placeholder="Ej: Equipaje perdido / Lost luggage")
    
    st.subheader(f"3. Grammar Topics ({cefr_level.split()[0]})")
    gramatica_b1 = st.selectbox(
        "Selecciona el tema gramatical:",
        [
            "Present Simple & Continuous / Verb To Be",
            "Past Simple & Past Continuous",
            "Present Perfect vs. Past Simple",
            "Future Forms (Will, Going to, Present Continuous)",
            "First, Second & Third Conditionals (If clauses)",
            "Modal Verbs (can, must, have to, might, should, could)",
            "Passive Voice (All Tenses)",
            "Relative Clauses (who, which, that, where, whose)",
            "Used to / Would for past habits",
            "Reported Speech (Statements, Questions & Commands)",
            "Comparatives, Superlatives & Inversion"
        ],
        index=2
    )
    
    st.subheader("4. Discourse Mode")
    tipo_texto = st.selectbox(
        "Formato de generación para el estudiante:",
        [
            "Preguntas (Comprehension & Grammar Questions)",
            "Descripción (Detailed Description)",
            "Narración (Narration)",
            "Juicio (Critical Judgment / Opinion)",
            "Explicación (Clear Explanation)",
            "Historia (Short Story)",
            "Storytelling (Engaging Narrative)"
        ]
    )
    
    st.markdown("---")
    generar_btn = st.button(f"🚀 Generate {cefr_level.split()[0]} Lesson", type="primary", width="stretch")

# --- CABECERA INSTITUCIONAL ---
default_width = int(saved_cfg["Width"]) if saved_cfg and saved_cfg.get("Width") else 115
default_shape = saved_cfg["Shape"] if saved_cfg and saved_cfg.get("Shape") else "Circular"
shape_options = ["Original", "Redondeado", "Circular"]
default_shape_idx = shape_options.index(default_shape) if default_shape in shape_options else 2

col_logo, col_title, col_qr, col_exit = st.columns([1.6, 4.9, 2, 1.5])

with col_logo:
    if can("Editar_Instituto_Logo") and (not is_mobile):
        with st.popover("✏️ Editar Logo", width="stretch"):
            logo_file = st.file_uploader("Subir imagen (PNG/JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
            logo_width = st.slider("Tamaño (px):", min_value=60, max_value=220, value=default_width, step=5)
            logo_shape = st.radio("Forma:", shape_options, index=default_shape_idx, horizontal=True)
            
            if st.button("💾 Guardar Logo Permanente", type="primary", width="stretch"):
                b64_to_save, mime_to_save = None, None
                if logo_file is not None:
                    b64_to_save, mime_to_save = compress_logo_to_base64(logo_file)
                elif saved_cfg and saved_cfg.get("Logo_Base64"):
                    b64_to_save, mime_to_save = saved_cfg["Logo_Base64"], saved_cfg["Mime_Type"]
                else:
                    b64_to_save, mime_to_save = get_default_logo_b64()
                    
                if b64_to_save:
                    try:
                        with st.spinner("Guardando logo..."):
                            save_permanent_config(b64_to_save, mime_to_save, logo_width, logo_shape, institute_address)
                            st.success("✅ ¡Logo guardado!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        logo_file = None
        logo_width = default_width
        logo_shape = default_shape

    if logo_file is not None:
        active_b64, active_mime = compress_logo_to_base64(logo_file)
    elif saved_cfg and saved_cfg.get("Logo_Base64"):
        active_b64, active_mime = saved_cfg["Logo_Base64"], saved_cfg["Mime_Type"]
    else:
        active_b64, active_mime = get_default_logo_b64()

    if active_b64:
        radius = "15px" if logo_shape == "Redondeado" else ("50%" if logo_shape == "Circular" else "0px")
        st.markdown(
            f'<div style="text-align: center;"><img src="data:{active_mime};base64,{active_b64}" style="width: {logo_width}px; height: auto; border-radius: {radius}; object-fit: cover;"></div>',
            unsafe_allow_html=True
        )
with col_title:
    st.markdown("#### 🏛️ CAREER ENGLISH INSTITUTE")
    st.caption(f"📍 {institute_address}")
    st.title(f"🎓 CEFR {cefr_level.split()[0]} ACADEMIC GRAMMAR & DISCOURSE SYSTEM")
    st.caption("Author: Jacob Zumaya Prianti | Applied Linguistics & Proficiency Assessment | APA Style")

with col_qr:
    if not is_mobile:
        btn_qr_txt = "🙈 Ocultar QR" if st.session_state.show_qr else "📱 Mostrar QR"
        if st.button(btn_qr_txt, use_container_width=True, key="toggle_qr_btn"):
            st.session_state.show_qr = not st.session_state.show_qr
            st.rerun()

        if st.session_state.show_qr:
            qr = qrcode.QRCode(version=1, box_size=4, border=1)
            qr.add_data("https://streamlit.app")
            qr.make(fit=True)
            buf = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
            st.image(buf.getvalue(), caption="📱 Scan for Mobile View", width=110)

with col_exit:
    if is_faculty_desktop:
        btn_label = "✖️ Ocultar Panel" if st.session_state.show_teacher_registry else "🛡️ Admin y Certificados"
        if st.button(btn_label, type="primary" if not st.session_state.show_teacher_registry else "secondary", width="stretch"):
            st.session_state.show_teacher_registry = not st.session_state.show_teacher_registry
            st.rerun()

    if st.button("🚪 Salir", type="secondary", width="stretch"):
        st.session_state.app_exited = True
        st.session_state.authenticated = False
        st.rerun()

# --- BUSCADOR DE FOLIOS ---
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns([2.5, 1.2, 2.3])
    with col_f1:
        folio_input = st.text_input(
            "🔍 Buscador de Folio Académico:",
            value=st.session_state.current_folio,
            placeholder="Ej: CEI-20261110-4821",
            label_visibility="collapsed"
        )
    with col_f2:
        buscar_folio_btn = st.button("🔍 Buscar Folio", width="stretch")
    with col_f3:
        if st.session_state.current_folio:
            st.info(f"📄 **Folio:** `{st.session_state.current_folio}` | 📅 `{st.session_state.current_creation_date}`")
        else:
            st.caption("Ingresa un Folio para recuperar una lección o presentar su examen.")

if buscar_folio_btn and folio_input.strip():
    folio_buscado = folio_input.strip().upper()
    try:
        with st.spinner(f"Buscando Folio {folio_buscado} en Hoja 1..."):
            sheet1 = get_google_sheet()
            registros_h1 = sheet1.get_all_records()
            encontrado = False
            for idx_fila, row in enumerate(registros_h1, start=2):
                if str(row.get("Folio", "")).strip().upper() == folio_buscado:
                    encontrado = True
                    usos_actuales = int(row.get("Usos_Estudiante") or 0)
                    
                    if (not has_faculty_access) and (usos_actuales >= 1):
                        st.error(f"⛔ El Folio **{folio_buscado}** ya alcanzó el límite de 1 reúso permitido. Solicita un nuevo folio a tu Teacher.")
                    else:
                        raw_json = str(row.get("Contenido_JSON", "")).strip()
                        if not raw_json:
                            st.warning("⚠️ Este folio corresponde solo a una grabación de audio antigua.")
                        else:
                            paquete = json.loads(raw_json)
                            st.session_state.generated_text = paquete.get("text", "")
                            st.session_state.quiz_data = paquete.get("quiz", None)
                            st.session_state.selected_cefr = paquete.get("cefr", "B1 (Intermediate)")
                            st.session_state.selected_academic_grade = paquete.get("grade", "Licenciatura / Universidad")
                            st.session_state.current_folio = folio_buscado
                            st.session_state.current_pdf_link = str(row.get("PDF_Link", ""))
                            st.session_state.current_creation_date = paquete.get("created_at") or str(row.get("Fecha_de_subida", ""))
                            st.session_state.quiz_graded = False
                            st.session_state.quiz_score = None
                            st.session_state.quiz_user_answers = {}
                            st.session_state.image_bytes = None
                            
                            if st.session_state.generated_text:
                                tts = gTTS(text=st.session_state.generated_text.replace("*", "").replace("#", ""), lang='en', slow=False)
                                afp = io.BytesIO()
                                tts.write_to_fp(afp)
                                st.session_state.audio_bytes = afp.getvalue()
                            
                            if not has_faculty_access:
                                sheet1.update_cell(idx_fila, 7, usos_actuales + 1)
                                st.success(f"✅ Folio **{folio_buscado}** recuperado (Reúso único activado).")
                            else:
                                st.success(f"✅ Folio **{folio_buscado}** recuperado (Acceso ilimitado).")
                            st.rerun()
                    break
            if not encontrado:
                st.warning(f"⚠️ No se encontró ningún registro con el Folio `{folio_buscado}` en Hoja 1.")
    except Exception as e:
        st.error(f"Error al buscar folio: {e}")

st.divider()
# --- PANEL DESPLEGABLE DE ADMINISTRACIÓN, CERTIFICADOS Y MATRIZ GLOBAL DE PERMISOS ---
if is_faculty_desktop and st.session_state.show_teacher_registry:
    with st.container(border=True):
        col_head_reg, col_close_reg = st.columns([4.5, 1])
        with col_head_reg:
            st.markdown("### 🛡️ PANEL DE ADMINISTRACIÓN, CERTIFICADOS Y MATRIZ GLOBAL RBAC")
        with col_close_reg:
            if st.button("🔼 Cerrar Panel", width="stretch"):
                st.session_state.show_teacher_registry = False
                st.rerun()

        tab_certificados, tab_reg_usuarios, tab_matriz_perm, tab_datos_inst = st.tabs([
            "🏅 Certificados (Timbre y QR)",
            "👥 Inscripción y Padrón",
            "🔐 Matriz Global de Permisos",
            "🏛️ Datos del Instituto"
        ])

        # 1. PESTAÑA EMISIÓN, HISTORIAL Y REVOCACIÓN DE CERTIFICADOS
        with tab_certificados:
            if not can("Emitir_Certificados"):
                st.warning("⛔ Tu perfil actual no tiene capacidad habilitada para emitir certificados.")
            else:
                st.markdown("#### 🏅 Emisión Oficial de Certificados con Firma Criptográfica (HMAC-SHA256) y Sello QR")
                try:
                    regs_cert = get_padron_sheet().get_all_records()
                    opciones_claves = {
                        f"{str(r.get('Clave', '')).strip()} — {str(r.get('Usuario', '')).strip()} ({str(r.get('Nivel', 'B1')).strip()})": r
                        for r in regs_cert if str(r.get("Clave", "")).strip()
                    }
                    if not opciones_claves:
                        st.warning("No hay claves de estudiantes registradas en el padrón.")
                    else:
                        col_c1, col_c2 = st.columns([1.3, 1.7])
                        with col_c1:
                            sel_label = st.selectbox("🔑 Seleccionar Clave de la Base de Datos:", list(opciones_claves.keys()), key="cert_select_clave")
                            datos_alumno = opciones_claves[sel_label]
                            clave_sel = str(datos_alumno.get("Clave", "")).strip()
                            nombre_sel = str(datos_alumno.get("Usuario", "")).strip()
                            nivel_sel = normalize_cefr(datos_alumno.get("Nivel", "B1"))
                            grado_sel = str(datos_alumno.get("Grado_Academico", "Licenciatura / Universidad")).strip()
                            st.info(f"**Titular:** {nombre_sel}\n\n**Clave:** `{clave_sel}` | **Nivel:** {nivel_sel}\n\n**Grado:** {grado_sel}")

                        with col_c2:
                            programa_cert = st.text_input(
                                "📚 Programa / Curso Acreditado:",
                                value=f"CEFR {nivel_sel} ({grado_sel}) Academic English Grammar & Applied Discourse",
                                key="cert_prog_input"
                            )
                            calif_cert = st.text_input(
                                "🏆 Calificación / Resultado Final:",
                                value="98.0% — Passed with Academic Distinction",
                                key="cert_grade_input"
                            )
                            if st.button("🔏 Timbrar y Generar Certificado Oficial (PDF + QR)", type="primary", width="stretch"):
                                with st.spinner("Generando timbrado criptográfico HMAC-SHA256 y sello QR..."):
                                    folio_c = f"CERT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                                    fecha_c = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    cadena_o, sello_h = generar_sello_digital(folio_c, clave_sel, nombre_sel, nivel_sel, fecha_c)
                                    
                                    get_certificados_sheet().append_row([
                                        folio_c, clave_sel, nombre_sel, nivel_sel,
                                        programa_cert.strip(), calif_cert.strip(), fecha_c, sello_h, "Vigente"
                                    ])
                                    pdf_cert_bytes = generar_pdf_certificado(
                                        folio_c, clave_sel, nombre_sel, nivel_sel,
                                        programa_cert.strip(), calif_cert.strip(), fecha_c,
                                        cadena_o, sello_h, institute_address
                                    )
                                    st.session_state["last_cert_pdf"] = pdf_cert_bytes
                                    st.session_state["last_cert_name"] = f"Certificado_{folio_c}_{nombre_sel.replace(' ', '_')}.pdf"
                                    st.session_state["last_cert_folio"] = folio_c
                                    st.success(f"✅ ¡Certificado timbrado! Folio: **{folio_c}**")

                        if st.session_state.get("last_cert_pdf"):
                            st.download_button(
                                label=f"📥 Descargar Certificado Oficial Timbrado ({st.session_state['last_cert_folio']})",
                                data=st.session_state["last_cert_pdf"],
                                file_name=st.session_state["last_cert_name"],
                                mime="application/pdf",
                                type="primary",
                                width="stretch"
                            )

                    st.divider()
                    st.markdown("#### 📜 Historial de Certificados Emitidos y Control de Vigencia")
                    cert_ws = get_certificados_sheet()
                    certs_hist = cert_ws.get_all_records()
                    if certs_hist:
                        df_certs = pd.DataFrame(certs_hist)
                        cols_c_ver = [c for c in ["Folio_Certificado", "Clave_Alumno", "Nombre_Estudiante", "Nivel_CEFR", "Fecha_Emision", "Estatus"] if c in df_certs.columns]
                        st.dataframe(df_certs[cols_c_ver], height=160, width="stretch", hide_index=True)

                        if can("Revocar_Certificados"):
                            c_rev1, c_rev2, c_rev3 = st.columns([2, 1.2, 1.2])
                            with c_rev1:
                                cert_to_mod = st.selectbox("Seleccionar Folio de Certificado:", df_certs["Folio_Certificado"].tolist(), key="sel_cert_rev")
                            with c_rev2:
                                nuevo_est_cert = st.selectbox("Estatus:", ["Vigente", "Revocado"], key="sel_est_cert")
                            with c_rev3:
                                st.write("")
                                if st.button("🔄 Aplicar Estatus", width="stretch"):
                                    celda_c = cert_ws.find(cert_to_mod)
                                    if celda_c:
                                        cert_ws.update_cell(celda_c.row, 9, nuevo_est_cert)
                                        st.success(f"✅ Certificado {cert_to_mod} actualizado a '{nuevo_est_cert}'.")
                                        st.rerun()
                except Exception as e:
                    st.error(f"Error en módulo de certificados: {e}")

        # 2. PESTAÑA INSCRIPCIÓN, NIVEL ACADÉMICO, ROLES Y PERMISOS
        with tab_reg_usuarios:
            if not can("Registrar_Usuarios"):
                st.warning("⛔ Tu perfil actual no tiene capacidad habilitada para registrar o modificar usuarios.")
            else:
                permisos_disponibles = PERMISOS_LISTA if can("Editar_Permisos") else ["Basico"]
                col_form_reg, col_tabla_reg = st.columns([1.2, 2.0])
                with col_form_reg:
                    st.markdown("#### ➕ Formulario de Inscripción")
                    with st.form("form_registro_estudiante", clear_on_submit=True):
                        reg_usuario = st.text_input("👤 Nombre Completo / Usuario:", placeholder="Ej: Carlos Mendoza")
                        reg_clave = st.text_input("🔑 Clave de Acceso asignada:", placeholder="Ej: CEI-2026-05")
                        c_r1, c_r2 = st.columns(2)
                        with c_r1:
                            reg_rol = st.selectbox("Rol:", ROLES_LISTA, index=0)
                        with c_r2:
                            reg_nivel = st.selectbox("Nivel CEFR:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2)
                        
                        reg_grado = st.selectbox("🎓 Nivel Académico:", GRADOS_ACADEMICOS, index=1)
                        reg_permiso = st.selectbox("🛡️ Perfil de Permiso:", PERMISOS_LISTA, index=0)
                        
                        if st.form_submit_button("💾 Guardar Inscripción", type="primary", width="stretch"):
                            if reg_usuario.strip() and reg_clave.strip():
                                try:
                                    p_sheet = get_padron_sheet()
                                    existentes = [str(r.get("Usuario", "")).strip().lower() for r in p_sheet.get_all_records()]
                                    if reg_usuario.strip().lower() in existentes:
                                        st.error("⚠️ El usuario ya está registrado.")
                                    else:
                                        p_sheet.append_row([reg_usuario.strip(), reg_clave.strip(), reg_rol, "Activo", reg_nivel, reg_permiso, reg_grado])
                                        st.success(f"✅ {reg_usuario.strip()} inscrito en {reg_grado} ({reg_nivel}).")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            else:
                                st.warning("Completa usuario y clave.")
                with col_tabla_reg:
                    st.markdown("#### 📋 Tabla de Registros Activos")
                    try:
                        p_sheet = get_padron_sheet()
                        records_p = p_sheet.get_all_records()
                        if records_p:
                            df_p = pd.DataFrame(records_p)
                            cols_mostrar = [c for c in ["Usuario", "Clave", "Rol", "Nivel", "Grado_Academico", "Permisos", "Estatus"] if c in df_p.columns]
                            st.dataframe(df_p[cols_mostrar], height=205, width="stretch", hide_index=True)
                            
                            c_ed1, c_ed2, c_ed3 = st.columns([1.4, 1.2, 1.4])
                            with c_ed1:
                                user_to_edit = st.selectbox("Usuario:", df_p["Usuario"].tolist(), key="edit_u_sel")
                            with c_ed2:
                                new_rol_edit = st.selectbox("Rol:", ROLES_LISTA, key="edit_rl_sel")
                            with c_ed3:
                                new_grado_edit = st.selectbox("Nivel Académico:", GRADOS_ACADEMICOS, index=1, key="edit_gr_sel")

                            c_ed4, c_ed5, c_ed6 = st.columns([1, 1.2, 1])
                            with c_ed4:
                                new_lvl_edit = st.selectbox("CEFR:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2, key="edit_lv_sel")
                            with c_ed5:
                                new_perm_edit = st.selectbox("Permiso:", PERMISOS_LISTA, key="edit_pm_sel")
                            with c_ed6:
                                new_status = st.selectbox("Estatus:", ["Activo", "Inactivo"], key="edit_st_sel")
                                
                            if st.button("🔄 Actualizar Registro", width="stretch"):
                                cell = p_sheet.find(user_to_edit)
                                if cell:
                                    p_sheet.update_cell(cell.row, 3, new_rol_edit)
                                    p_sheet.update_cell(cell.row, 4, new_status)
                                    p_sheet.update_cell(cell.row, 5, new_lvl_edit)
                                    p_sheet.update_cell(cell.row, 6, new_perm_edit)
                                    p_sheet.update_cell(cell.row, 7, new_grado_edit)
                                    st.success(f"✅ Registro de {user_to_edit} actualizado.")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Error al cargar padrón: {e}")

        # 3. PESTAÑA MATRIZ GLOBAL DE PERMISOS RBAC
        with tab_matriz_perm:
            st.markdown("#### 🔐 Matriz Estándar RBAC (Crea o ajusta perfiles de permisos en tiempo real)")
            df_mat = pd.DataFrame([
                {"Perfil_Permiso": k, **{cap: ("SI" if v.get(cap) else "NO") for cap in CAPABILITY_COLS}}
                for k, v in PERMISSIONS_MATRIX.items()
            ])
            st.dataframe(df_mat, width="stretch", hide_index=True)

            if can("Editar_Permisos"):
                with st.form("form_nuevo_perfil_permiso", clear_on_submit=True):
                    st.markdown("**➕ Crear o Actualizar Perfil de Permisos:**")
                    nombre_perfil = st.text_input("Nombre del Perfil (Ej: Coordinador, Recepcion, Supervisor):", placeholder="Ej: Coordinador")
                    cols_chk = st.columns(4)
                    checks_vals = {}
                    for i, cap in enumerate(CAPABILITY_COLS):
                        with cols_chk[i % 4]:
                            checks_vals[cap] = st.checkbox(cap.replace("_", " "), value=False, key=f"chk_{cap}")
                    
                    if st.form_submit_button("💾 Guardar Perfil en Matriz Global", type="primary"):
                        if nombre_perfil.strip():
                            try:
                                m_sheet = get_permisos_sheet()
                                fila_nueva = [nombre_perfil.strip()] + [("SI" if checks_vals[c] else "NO") for c in CAPABILITY_COLS]
                                celda_p = m_sheet.find(nombre_perfil.strip())
                                if celda_p and celda_p.col == 1:
                                    for col_i, val in enumerate(fila_nueva, start=1):
                                        m_sheet.update_cell(celda_p.row, col_i, val)
                                else:
                                    m_sheet.append_row(fila_nueva)
                                load_permissions_matrix.clear()
                                st.success(f"✅ Perfil '{nombre_perfil.strip()}' guardado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.warning("Escribe un nombre para el perfil.")

        # 4. PESTAÑA DATOS DEL INSTITUTO
        with tab_datos_inst:
            if not can("Editar_Instituto_Logo"):
                st.warning("⛔ Tu perfil actual no tiene capacidad habilitada para editar la información oficial.")
            else:
                st.markdown("#### 🏛️ Dirección y Teléfono Oficial de CAREER ENGLISH INSTITUTE")
                with st.form("form_editar_direccion"):
                    nueva_direccion = st.text_area("📍 Dirección y Contacto Oficial:", value=institute_address, height=80)
                    if st.form_submit_button("💾 Guardar Información Institucional", type="primary"):
                        if nueva_direccion.strip():
                            try:
                                b64_c = saved_cfg["Logo_Base64"] if (saved_cfg and saved_cfg.get("Logo_Base64")) else (get_default_logo_b64() or "")
                                mime_c = saved_cfg["Mime_Type"] if (saved_cfg and saved_cfg.get("Mime_Type")) else "image/png"
                                w_c = int(saved_cfg["Width"]) if (saved_cfg and saved_cfg.get("Width")) else 115
                                s_c = saved_cfg["Shape"] if (saved_cfg and saved_cfg.get("Shape")) else "Circular"
                                save_permanent_config(b64_c, mime_c, w_c, s_c, nueva_direccion.strip())
                                st.success("✅ ¡Información institucional actualizada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
    st.divider()
# --- MOTOR DE IA DE MÁXIMA POTENCIA ---
def generar_con_maxima_potencia(client, prompt_contenido, instruccion_sistema=None):
    modelos_potentes = [
        "gemini-3.1-pro-preview", "gemini-3.5-pro", "gemini-3.8-flash",
        "gemini-3.1-flash-lite-preview", "gemini-2.5-pro", "gemini-2.5-flash"
    ]
    try:
        pro_det, otros_det = [], []
        for m in client.models.list():
            nombre = m.name.replace("models/", "")
            if "gemini" in nombre and not any(x in nombre for x in ["embedding", "imagen", "aqa", "tts", "audio"]):
                if nombre not in modelos_potentes:
                    (pro_det if ("pro" in nombre or "ultra" in nombre) else otros_det).append(nombre)
        modelos_potentes += sorted(pro_det, reverse=True) + sorted(otros_det, reverse=True)
    except Exception:
        pass

    ultimo_error = None
    for modelo in modelos_potentes:
        try:
            config = types.GenerateContentConfig(system_instruction=instruccion_sistema, temperature=0.65) if instruccion_sistema else types.GenerateContentConfig(temperature=0.65)
            respuesta = client.models.generate_content(model=modelo, contents=prompt_contenido, config=config)
            if respuesta and respuesta.text:
                return respuesta.text, modelo
        except Exception as e:
            ultimo_error = e
            continue
    raise ultimo_error

# --- VISUAL CONTEXT DE TRIPLE RESPALDO GARANTIZADO ---
def generar_imagen_garantizada(client, prompt_ingles, titulo_tema, nivel_cefr, grado_acad):
    clean_p = "".join(c for c in prompt_ingles if c.isalnum() or c in " ,.-").strip()
    
    # NIVEL 1: Gemini Imagen API
    if client is not None:
        try:
            res_img = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=f"Educational illustration for {grado_acad} students: {clean_p}. Colorful, clear, no text.",
                config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9")
            )
            if res_img and res_img.generated_images:
                raw_b = res_img.generated_images.image.image_bytes
                return compress_bytes_image(raw_b)
        except Exception:
            pass

    # NIVEL 2: Servidores externos de respaldo
    encoded = urllib.parse.quote(f"{clean_p}, educational illustration, flat vector, no text")
    keywords = urllib.parse.quote(clean_p.split(",")[:25].replace(" ", ","))
    for url_ext in [
        f"https://pollinations.ai{encoded}?model=turbo&width=640&height=360&nologo=true&seed={random.randint(1, 999)}",
        f"https://loremflickr.com{keywords}"
    ]:
        try:
            resp = requests.get(url_ext, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 4000:
                return compress_bytes_image(resp.content)
        except Exception:
            continue

    # NIVEL 3: Tarjeta Visual Educativa Generada Localmente (100% Infalible)
    img_card = Image.new("RGB", (640, 360), color=(15, 44, 89))
    draw = ImageDraw.Draw(img_card)
    draw.rectangle((15, 15, 625, 345), outline=(218, 165, 32), width=3)
    draw.rectangle((18, 18, 622, 85), fill=(25, 65, 125))
    draw.text((35, 38), f"CAREER ENGLISH INSTITUTE | CEFR {nivel_cefr.split()} | {grado_acad.upper()}", fill=(255, 215, 0))
    draw.text((35, 115), "VISUAL CONTEXT & LESSON TOPIC:", fill=(180, 210, 255))
    
    palabras = titulo_tema.upper().split()
    lineas, linea_act = [], ""
    for p in palabras:
        if len(linea_act + " " + p) <= 38:
            linea_act = (linea_act + " " + p).strip()
        else:
            lineas.append(linea_act)
            linea_act = p
    if linea_act:
        lineas.append(linea_act)
    
    y_txt = 150
    for l in lineas[:4]:
        draw.text((35, y_txt), l, fill=(255, 255, 255))
        y_txt += 30

    draw.text((35, 310), "Applied Linguistics & Visual Support - Jacob Zumaya Prianti", fill=(160, 190, 220))
    buf_card = io.BytesIO()
    img_card.save(buf_card, format="JPEG", quality=85)
    return buf_card.getvalue()

def generar_quiz_leccion(texto_leccion, tema_gramatical, nivel_cefr, grado_acad, evitar_preguntas=None):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    evitar_txt = f"IMPORTANT: Create COMPLETELY DIFFERENT questions from: {evitar_preguntas}" if evitar_preguntas else ""
    prompt_quiz = f"""
    Based on this CEFR Level {nivel_cefr} English lesson tailored for {grado_acad} students, create a 5-question multiple-choice quiz in English calibrated strictly to level {nivel_cefr} and {grado_acad} cognitive level, evaluating comprehension and target grammar ({tema_gramatical}).
    {evitar_txt}
    LESSON TEXT:
    {texto_leccion}
    RETURN ONLY VALID JSON array:
    [{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A) ..."}}]
    """
    raw_resp, _ = generar_con_maxima_potencia(client, prompt_quiz, "Output strictly valid JSON array only.")
    cleaned = raw_resp.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)
    return json.loads(cleaned.strip())
# --- EJECUCIÓN DE GENERACIÓN ---
if generar_btn:
    if "GEMINI_API_KEY" not in st.secrets:
        st.sidebar.error("⚠️ GEMINI_API_KEY no configurada.")
    elif not contexto or not asunto:
        st.sidebar.warning("⚠️ Completa Contexto y Asunto.")
    else:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        with st.spinner(f"🧠 Generating CEFR {cefr_level} ({academic_grade}) Lesson, Visual & Audio..."):
            try:
                nuevo_folio = f"CEI-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pdf_url_directo = f"https://streamlit.app{nuevo_folio}"
                
                cefr_guidelines = {
                    "A1": "Use very basic everyday vocabulary, short simple sentences (5-8 words), present simple/continuous, and concrete familiar topics.",
                    "A2": "Use simple, clear sentences, basic connectors (and, but, because, so), past simple, and everyday routine vocabulary.",
                    "B1": "Use clear standard English, connected paragraphs, intermediate vocabulary, and a mix of simple and complex clauses.",
                    "B2": "Use fluent, detailed academic/semi-formal English, complex sentence structures, nuanced connectors, and abstract concepts.",
                    "C1": "Use sophisticated, advanced academic English, idiomatic expressions, complex subordinate clauses, and high lexical precision.",
                    "C2": "Use near-native, scholarly English with subtle rhetorical devices, advanced syntax, and specialized academic vocabulary."
                }
                nivel_corto = cefr_level.split()
                guia_nivel = cefr_guidelines.get(nivel_corto, cefr_guidelines["B1"])

                grade_pedagogy = {
                    "Preescolar": "Adapt tone for early childhood (ages 4-6): playful, warm, concrete sensory imagery, friendly characters, and joyful storytelling.",
                    "Primaria": "Adapt tone for elementary school children (ages 6-12): engaging, imaginative, clear visual descriptions, everyday school/family situations, and encouraging tone.",
                    "Secundaria": "Adapt tone for middle school teenagers (ages 12-15): relatable, dynamic, practical real-world situations, and clear explanations.",
                    "Preparatoria / Bachillerato": "Adapt tone for high school students (ages 15-18): analytical, communicative, real-life scenarios, and structured arguments.",
                    "Licenciatura / Universidad": "Adapt tone for university undergraduate students: formal academic register, critical thinking, professional contexts, and analytical depth.",
                    "Maestría / Posgrado": "Adapt tone for graduate/Master's students: advanced scholarly discourse, theoretical frameworks, research-oriented examples, and formal academic style.",
                    "Doctorado / Investigación": "Adapt tone for Doctoral/PhD researchers: rigorous academic prose, epistemological precision, scholarly critique, and specialized terminology."
                }
                guia_grado = grade_pedagogy.get(academic_grade, grade_pedagogy["Licenciatura / Universidad"])

                sys_prompt = (
                    f"You are a Senior Applied Linguist at CAREER ENGLISH INSTITUTE. "
                    f"Translate any Spanish inputs and write 100% in natural English calibrated STRICTLY to CEFR Level {cefr_level} AND Academic Level: {academic_grade}. "
                    f"CEFR RULE: {guia_nivel} "
                    f"PEDAGOGICAL ADAPTATION RULE: {guia_grado} "
                    f"Follow strict APA Style. The official author of every generated academic document MUST be Jacob Zumaya Prianti. "
                    f"Zero Spanish words allowed."
                )
                prompt_texto = f"""
                Create a CEFR Level {cefr_level} English lesson artifact tailored for {academic_grade} students, authored by Jacob Zumaya Prianti:
                - Folio ID: {nuevo_folio} | Creation Date: {fecha_creacion}
                - Academic Level: {academic_grade} | CEFR Level: {cefr_level}
                - Context: {contexto} | Characters: {personas} | Subject: {asunto}
                - Target Grammar: {gramatica_b1} | Discourse Mode: {tipo_texto}
                
                STRICT RULES:
                1. 100% English only. Calibrate vocabulary and grammar strictly to CEFR {cefr_level} and pedagogical tone to {academic_grade}. Highlight all {gramatica_b1} structures in **bold**.
                2. APA Header & Byline: Include the academic title in bold, followed immediately by:
                   **Folio:** {nuevo_folio} | **Creation Date:** {fecha_creacion}  
                   **Author:** Jacob Zumaya Prianti | **Institution:** Career English Institute (2026)  
                   **CEFR Level:** {cefr_level} | **Academic Level:** {academic_grade}  
                   **Campus & Contact:** {institute_address}
                3. Bibliography / APA References Section: At the end of the lesson, include a formal section titled **Bibliography (Consulted Academic & Linguistic Sources)** formatted in strict APA 7th edition. List:
                   - Primary instructional module: Zumaya Prianti, J. (2026). *{asunto.title()}: CEFR {nivel_corto} ({academic_grade}) Applied Grammar & Discourse Module* (Folio {nuevo_folio}). Career English Institute.
                   - 3 to 4 real, authoritative linguistic, pedagogical, or subject-matter reference works directly relevant to "{asunto}", "{gramatica_b1}", and {academic_grade} education.
                """
                texto_gen, mod_usado = generar_con_maxima_potencia(client, prompt_texto, sys_prompt)
                st.session_state.generated_text = texto_gen
                st.session_state.active_model_name = mod_usado
                st.session_state.selected_cefr = cefr_level
                st.session_state.selected_academic_grade = academic_grade
                st.session_state.current_folio = nuevo_folio
                st.session_state.current_pdf_link = pdf_url_directo
                st.session_state.current_creation_date = fecha_creacion
                st.session_state.quiz_data = None
                st.session_state.quiz_graded = False
                st.session_state.quiz_score = None
                st.session_state.quiz_user_answers = {}
                
                img_desc, _ = generar_con_maxima_potencia(
                    client,
                    f"Simple 10-word English visual illustration description for {academic_grade}: {contexto}, {personas}, {asunto}. No text."
                )
                st.session_state.image_bytes = generar_imagen_garantizada(
                    client, img_desc, f"{asunto} - {contexto}", cefr_level, academic_grade
                )
                
                tts = gTTS(text=texto_gen.replace("*", "").replace("#", ""), lang='en', slow=False)
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.session_state.audio_bytes = audio_fp.getvalue()
                
                paquete_guardado = json.dumps({
                    "text": texto_gen,
                    "quiz": None,
                    "cefr": cefr_level,
                    "grade": academic_grade,
                    "created_at": fecha_creacion
                }, ensure_ascii=False)
                
                tema_reg = f"[{nivel_corto} | {academic_grade}] {asunto} ({gramatica_b1})"
                get_google_sheet().append_row([
                    nuevo_folio, usuario, tema_reg, "", fecha_creacion, paquete_guardado[:48000], 0, pdf_url_directo
                ])
            except Exception as e:
                st.error(f"⚠️ Error al generar lección: {e}")
# --- PANEL CENTRAL Y DERECHO ---
if "selected_academic_grade" not in st.session_state:
    st.session_state.selected_academic_grade = st.session_state.get("user_academic_grade", "Licenciatura / Universidad")

col_main_center, col_tools_right = st.columns([7, 3.5])

with col_main_center:
    col_sub_t, col_badge = st.columns([3, 1.5])
    with col_sub_t:
        st.subheader("📄 Generated Content (APA Format - 100% English)")
    with col_badge:
        if st.session_state.current_folio:
            st.caption(f"🔖 Folio: `{st.session_state.current_folio}`")

    top_container = st.container(height=420, border=True)
    with top_container:
        if st.session_state.generated_text:
            st.markdown(st.session_state.generated_text)
        else:
            st.info("👈 Escribe los datos en Español o Inglés en la barra izquierda y presiona **Generate Lesson**, o busca un **Folio** arriba.")

    # --- QUIZ INTERACTIVO DE LA LECCIÓN ---
    if st.session_state.generated_text:
        if st.session_state.quiz_data is None:
            if st.button(f"📝 Generar Quiz ({st.session_state.selected_cefr.split()} - {st.session_state.selected_academic_grade})", type="primary", width="stretch"):
                with st.spinner("Generando preguntas de evaluación y vinculando al Folio..."):
                    try:
                        q_gen = generar_quiz_leccion(
                            st.session_state.generated_text, gramatica_b1,
                            st.session_state.selected_cefr, st.session_state.selected_academic_grade
                        )
                        st.session_state.quiz_data = q_gen
                        
                        if st.session_state.current_folio:
                            s1 = get_google_sheet()
                            celda_f = s1.find(st.session_state.current_folio)
                            if celda_f:
                                paq_act = json.dumps({
                                    "text": st.session_state.generated_text,
                                    "quiz": q_gen,
                                    "cefr": st.session_state.selected_cefr,
                                    "grade": st.session_state.selected_academic_grade,
                                    "created_at": st.session_state.current_creation_date
                                }, ensure_ascii=False)
                                s1.update_cell(celda_f.row, 6, paq_act[:48000])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al generar quiz: {e}")
        else:
            with st.container(border=True):
                st.subheader(f"📝 Lesson Comprehension & Grammar Quiz (Folio: {st.session_state.current_folio})")
                for idx, item in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**{idx + 1}. {item['question']}**")
                    choice = st.radio(f"q_{idx}", item["options"], key=f"radio_quiz_{idx}", label_visibility="collapsed", index=None)
                    st.session_state.quiz_user_answers[idx] = choice
                    if st.session_state.quiz_graded:
                        if choice == item["answer"]:
                            st.success(f"✅ Correct! ({item['answer']})")
                        else:
                            st.error(f"❌ Incorrect. Your answer: {choice or 'None'} | **Correct answer:** {item['answer']}")
                    st.write("")

                col_btn_grade, col_btn_new = st.columns(2)
                with col_btn_grade:
                    if st.button("✅ Calificar Quiz", type="primary", width="stretch"):
                        correctas = sum(1 for i, it in enumerate(st.session_state.quiz_data) if st.session_state.quiz_user_answers.get(i) == it["answer"])
                        total = len(st.session_state.quiz_data)
                        st.session_state.quiz_score = f"{correctas}/{total} ({round((correctas / total) * 100, 1)}%)"
                        st.session_state.quiz_graded = True
                        st.rerun()
                with col_btn_new:
                    if st.button("🔄 Nuevo Quiz (Cambiar Preguntas)", type="secondary", width="stretch"):
                        with st.spinner("Generando nuevas preguntas..."):
                            try:
                                prev_qs = [q["question"] for q in st.session_state.quiz_data]
                                q_new = generar_quiz_leccion(
                                    st.session_state.generated_text, gramatica_b1,
                                    st.session_state.selected_cefr, st.session_state.selected_academic_grade, prev_qs
                                )
                                st.session_state.quiz_data = q_new
                                st.session_state.quiz_graded = False
                                st.session_state.quiz_score = None
                                st.session_state.quiz_user_answers = {}
                                
                                if st.session_state.current_folio:
                                    s1 = get_google_sheet()
                                    celda_f = s1.find(st.session_state.current_folio)
                                    if celda_f:
                                        paq_act = json.dumps({
                                            "text": st.session_state.generated_text,
                                            "quiz": q_new,
                                            "cefr": st.session_state.selected_cefr,
                                            "grade": st.session_state.selected_academic_grade,
                                            "created_at": st.session_state.current_creation_date
                                        }, ensure_ascii=False)
                                        s1.update_cell(celda_f.row, 6, paq_act[:48000])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al renovar quiz: {e}")

                if st.session_state.quiz_graded and st.session_state.quiz_score:
                    st.info(f"🏆 **Calificación Obtenida / Final Score:** {st.session_state.quiz_score}")

    st.subheader(f"🖼️ Visual Context ({st.session_state.selected_academic_grade})")
    bottom_container = st.container(height=280, border=True)
    with bottom_container:
        if st.session_state.image_bytes:
            st.image(st.session_state.image_bytes, width="stretch")
        elif st.session_state.generated_text:
            fallback_img = generar_imagen_garantizada(
                None, st.session_state.generated_text[:60],
                f"Folio {st.session_state.current_folio}", st.session_state.selected_cefr, st.session_state.selected_academic_grade
            )
            st.image(fallback_img, width="stretch")
        else:
            st.caption("La imagen ilustrativa aparecerá aquí / The illustrative image will appear here.")
# --- PANEL DERECHO EN ORDEN PROFESIONAL ---
with col_tools_right:
    st.subheader("🎧 1. Model Pronunciation")
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        st.download_button(
            label="📥 Descargar Audio (MP3)",
            data=st.session_state.audio_bytes,
            file_name=f"CEI_Audio_{st.session_state.current_folio or usuario.replace(' ', '_')}.mp3",
            mime="audio/mp3",
            width="stretch"
        )
    else:
        st.caption("Audio available after generating lesson.")
        
    st.divider()

    st.subheader("🎙️ 2. Speaking & Video Practice")
    tab_rec_audio, tab_rec_video = st.tabs(["🎤 Grabar Audio", "📹 Grabar Video (MP4)"])
    
    with tab_rec_audio:
        student_audio = st.audio_input("Graba tu voz leyendo el texto:")
        
    with tab_rec_video:
        st.caption("Activa tu cámara, graba tu lectura y descárgala en formato MP4:")
        safe_user_filename = f"CEI_Video_{st.session_state.current_folio or usuario.replace(' ', '_')}.mp4"
        video_recorder_html = f"""
        <div style="font-family: sans-serif; text-align: center; border: 1px solid #ddd; border-radius: 10px; padding: 10px; background: #fafafa;">
            <video id="preview" width="100%" height="175" autoplay muted playsinline style="border-radius: 8px; background: #000; object-fit: cover;"></video>
            <div style="margin-top: 8px; display: flex; gap: 6px; justify-content: center; flex-wrap: wrap;">
                <button id="btnStartCam" style="background:#0d6efd; color:white; border:none; padding:7px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">📷 Activar Cámara</button>
                <button id="btnRec" disabled style="background:#dc3545; color:white; border:none; padding:7px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">⏺️ Grabar</button>
                <button id="btnStop" disabled style="background:#6c757d; color:white; border:none; padding:7px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">⏹️ Detener</button>
            </div>
            <p id="statusTxt" style="font-size: 12px; color: #555; margin: 6px 0;">Presiona "Activar Cámara" para iniciar</p>
            <a id="downloadLink" style="display:none; background:#198754; color:white; text-decoration:none; padding:8px 14px; border-radius:6px; font-weight:bold; font-size:13px; margin-top:4px;">📥 Descargar Video MP4</a>
        </div>

        <script>
        let stream = null;
        let mediaRecorder = null;
        let recordedChunks = [];

        const preview = document.getElementById('preview');
        const btnStartCam = document.getElementById('btnStartCam');
        const btnRec = document.getElementById('btnRec');
        const btnStop = document.getElementById('btnStop');
        const statusTxt = document.getElementById('statusTxt');
        const downloadLink = document.getElementById('downloadLink');

        function getSupportedMp4MimeType() {{
            const types = [
                'video/mp4;codecs=avc1,mp4a.40.2',
                'video/mp4;codecs=h264,aac',
                'video/mp4',
                'video/webm;codecs=h264',
                'video/webm'
            ];
            for (const t of types) {{
                if (MediaRecorder.isTypeSupported(t)) return t;
            }}
            return '';
        }}

        btnStartCam.onclick = async () => {{
            try {{
                stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                preview.srcObject = stream;
                preview.muted = true;
                preview.controls = false;
                btnRec.disabled = false;
                btnStartCam.disabled = true;
                statusTxt.innerText = "Cámara activa. Listo para grabar en MP4.";
            }} catch (err) {{
                statusTxt.innerText = "⚠️ Permiso de cámara/micrófono denegado o no disponible.";
            }}
        }};

        btnRec.onclick = () => {{
            recordedChunks = [];
            downloadLink.style.display = 'none';
            const mime = getSupportedMp4MimeType();
            const options = mime ? {{ mimeType: mime }} : {{}};
            mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorder.ondataavailable = (e) => {{
                if (e.data.size > 0) recordedChunks.push(e.data);
            }};
            mediaRecorder.onstop = () => {{
                const blob = new Blob(recordedChunks, {{ type: 'video/mp4' }});
                const url = URL.createObjectURL(blob);
                preview.srcObject = null;
                preview.src = url;
                preview.muted = false;
                preview.controls = true;
                downloadLink.href = url;
                downloadLink.download = "{safe_user_filename}";
                downloadLink.style.display = 'inline-block';
                statusTxt.innerText = "✅ Video MP4 grabado. Haz clic abajo para descargarlo.";
                stream.getTracks().forEach(track => track.stop());
                btnStartCam.disabled = false;
                btnStartCam.innerText = "🔄 Grabar Otro";
            }};
            mediaRecorder.start();
            btnRec.disabled = true;
            btnStop.disabled = false;
            statusTxt.innerText = "🔴 Grabando lectura en MP4...";
        }};

        btnStop.onclick = () => {{
            mediaRecorder.stop();
            btnStop.disabled = true;
        }};
        </script>
        """
        st.iframe(video_recorder_html, height=310)

    st.write("")
    if st.button("☁️ Guardar Audio en Google Sheets", type="primary", width="stretch", disabled=(student_audio is None)):
        try:
            with st.spinner("Guardando audio vinculado al Folio..."):
                sheet = get_google_sheet()
                audio_b64 = base64.b64encode(student_audio.getvalue()).decode("utf-8")
                if len(audio_b64) > 45000:
                    st.error("⚠️ El audio supera los 14 seg. Graba un fragmento más corto.")
                else:
                    folio_act = st.session_state.current_folio
                    celda_existente = sheet.find(folio_act) if folio_act else None
                    
                    if celda_existente:
                        sheet.update_cell(celda_existente.row, 4, audio_b64)
                        st.success(f"✅ ¡Audio guardado y vinculado al Folio {folio_act}!")
                    else:
                        folio_nuevo = folio_act or f"CEI-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                        tema_completo = f"[{st.session_state.selected_cefr.split()} | {st.session_state.selected_academic_grade}] {asunto} ({gramatica_b1})" if asunto else gramatica_b1
                        fecha_subida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        link_pdf = f"https://streamlit.app{folio_nuevo}"
                        sheet.append_row([folio_nuevo, usuario, tema_completo, audio_b64, fecha_subida, "", 0, link_pdf])
                        st.success(f"✅ ¡Audio guardado con Folio {folio_nuevo}!")
        except Exception as e:
            st.error(f"Error al guardar audio: {e}")

    def create_pdf(text, quiz_items=None, user_ans=None, score=None):
        folio_doc = st.session_state.current_folio or "SIN-FOLIO"
        link_doc = st.session_state.current_pdf_link or f"https://streamlit.app{folio_doc}"
        fecha_doc = st.session_state.current_creation_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        grado_doc = st.session_state.selected_academic_grade
        
        pdf = FPDF()
        pdf.set_author("Jacob Zumaya Prianti")
        pdf.set_creator("Career English Institute")
        pdf.add_page()
        
        pdf.set_font("Times", "B", 14)
        pdf.cell(0, 8, txt="CAREER ENGLISH INSTITUTE", ln=True, align="C")
        pdf.set_font("Times", "I", 9)
        pdf.cell(0, 6, txt=institute_address.encode("latin-1", "replace").decode("latin-1"), ln=True, align="C")
        pdf.set_font("Times", "B", 11)
        pdf.cell(0, 7, txt=f"CEFR {st.session_state.selected_cefr} ({grado_doc}) Academic Grammar & Discourse System", ln=True, align="C")
        pdf.set_font("Times", "B", 11)
        pdf.cell(0, 7, txt=f"FOLIO DE REGISTRO: {folio_doc}", ln=True, align="C")
        pdf.set_font("Times", "B", 10)
        pdf.cell(0, 6, txt="Author: Jacob Zumaya Prianti", ln=True, align="C")
        pdf.set_font("Times", "I", 9)
        pdf.cell(0, 6, txt=f"Creation Date / Fecha de Creacion: {fecha_doc}", ln=True, align="C")
        pdf.cell(0, 6, txt=f"Student / User: {usuario} ({st.session_state.user_role}) | Grade: {grado_doc} | Level: {st.session_state.selected_cefr}", ln=True, align="C")
        pdf.set_font("Times", "U", 9)
        pdf.cell(0, 6, txt=f"Recovery Link: {link_doc}", ln=True, align="C", link=link_doc)
        pdf.ln(5)
        
        pdf.set_font("Times", size=12)
        pdf.multi_cell(0, 8, txt=text.encode("latin-1", "replace").decode("latin-1"))
        
        if quiz_items:
            pdf.ln(8)
            pdf.set_font("Times", "B", 13)
            pdf.cell(0, 10, txt=f"LESSON COMPREHENSION & GRAMMAR QUIZ (FOLIO: {folio_doc})", ln=True)
            if score:
                pdf.set_font("Times", "B", 11)
                pdf.cell(0, 8, txt=f"Final Grade / Calificacion Obtenida: {score}", ln=True)
            pdf.ln(3)
            for i, q in enumerate(quiz_items):
                pdf.set_font("Times", "B", 11)
                pdf.multi_cell(0, 7, txt=f"{i+1}. {q['question']}".encode("latin-1", "replace").decode("latin-1"))
                pdf.set_font("Times", size=10)
                for opt in q["options"]:
                    pdf.multi_cell(0, 6, txt=f"   {opt}".encode("latin-1", "replace").decode("latin-1"))
                u_choice = user_ans.get(i) if user_ans else "None"
                ans_line = f"   -> Student Answer: {u_choice or 'None'} | Correct: {q['answer']}"
                pdf.set_font("Times", "I", 10)
                pdf.multi_cell(0, 6, txt=ans_line.encode("latin-1", "replace").decode("latin-1"))
                pdf.ln(3)

        pdf.ln(10)
        pdf.set_font("Times", "I", 9)
        pdf.cell(0, 6, txt=institute_address.encode("latin-1", "replace").decode("latin-1"), ln=True, align="C")
        pdf.set_font("Times", "I", 10)
        pdf.cell(0, 7, txt="© 2026 CAREER ENGLISH INSTITUTE. Todos los derechos reservados. Author: Jacob Zumaya Prianti.", ln=True, align="C")
        return pdf.output(dest="S").encode("latin-1")
    if st.session_state.generated_text:
        pdf_bytes = create_pdf(
            st.session_state.generated_text.replace("*", ""),
            quiz_items=st.session_state.quiz_data,
            user_ans=st.session_state.quiz_user_answers,
            score=st.session_state.quiz_score
        )
        st.download_button(
            label=f"📥 Descargar PDF ({st.session_state.current_folio or 'Tiempo Real'})",
            data=pdf_bytes,
            file_name=f"{st.session_state.current_folio or 'CEI_Lesson'}_{usuario.replace(' ', '_')}.pdf",
            mime="application/pdf",
            width="stretch"
        )
    else:
        st.button("📥 Descargar PDF (Tiempo Real)", disabled=True, width="stretch")

    if st.button("📂 Ver Audios y Folios Guardados", width="stretch"):
        st.session_state.show_saved_audios = not st.session_state.show_saved_audios

    if st.session_state.show_saved_audios:
        with st.container(height=260, border=True):
            st.markdown("**Historial de Folios y Grabaciones:**")
            try:
                records = get_google_sheet().get_all_records()
                if not records:
                    st.info("Aún no hay registros guardados.")
                else:
                    df = pd.DataFrame(records)
                    if not has_faculty_access:
                        df = df[df["Usuario"].astype(str).str.lower() == usuario.lower()]
                    if df.empty:
                        st.warning(f"Sin registros para '{usuario}'.")
                    else:
                        for _, row in df.tail(5).iloc[::-1].iterrows():
                            st.caption(f"🔖 **{row.get('Folio', 'S/F')}** | 👤 **{row['Usuario']}** | 📅 {row['Fecha_de_subida']}")
                            st.caption(f"📘 *{row['Tema']}*")
                            if row.get("PDF_Link"):
                                st.markdown(f"🔗 [Abrir Lección / PDF por Folio]({row['PDF_Link']})")
                            if row.get("Audio"):
                                st.audio(base64.b64decode(row["Audio"]), format="audio/wav")
                            st.divider()
            except Exception as e:
                st.error(f"Error al cargar historial: {e}")

    st.divider()

    if st.button("🗑️ Borrar Todo", type="secondary", width="stretch"):
        st.session_state.generated_text = ""
        st.session_state.image_bytes = None
        st.session_state.audio_bytes = None
        st.session_state.show_saved_audios = False
        st.session_state.quiz_data = None
        st.session_state.quiz_graded = False
        st.session_state.quiz_score = None
        st.session_state.quiz_user_answers = {}
        st.session_state.current_folio = ""
        st.session_state.current_pdf_link = ""
        st.session_state.current_creation_date = ""
        st.rerun()

# --- PIE DE PÁGINA INSTITUCIONAL ---
st.divider()
st.markdown(
    f"""
    <div style="text-align: center; color: #666; font-size: 13px; padding: 10px;">
        📍 <b>{institute_address}</b><br>
        © 2026 <b>CAREER ENGLISH INSTITUTE</b> | Todos los derechos reservados.<br>
        Author / Creado y desarrollado por: <b>Jacob Zumaya Prianti</b>
    </div>
    """,
    unsafe_allow_html=True
)
