# ==============================================================================
# PARTE 1 DE 15: IMPORTACIONES, CONFIGURACIÓN DE PÁGINA Y AUTO-ACTUALIZADOR
# ==============================================================================
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta
import hashlib
import hmac
import html as html_lib
from importlib.metadata import PackageNotFoundError, version as pkg_version
import io
import json
import os
import random
import re
import subprocess
import sys
import urllib.parse
from zoneinfo import ZoneInfo

from deep_translator import GoogleTranslator
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from google import genai
from google.genai import types
from google.oauth2 import service_account
import gspread
from gtts import gTTS
import pandas as pd
from PIL import Image
import psycopg
from psycopg.rows import dict_row
import qrcode
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval

try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
except ImportError:
    try:
        from streamlit.runtime.scriptrunner_utils.script_run_context import add_script_run_ctx, get_script_run_ctx
    except ImportError:
        add_script_run_ctx = None
        get_script_run_ctx = None


# --- 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO) ---
st.set_page_config(
    page_title="CEFR Academic Grammar & Discourse System - Career English Institute",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1B. MOTOR DE AUTOACTUALIZACIÓN DE LIBRERÍAS (SIN REVISAR CÓDIGO) ---
MANAGED_PACKAGES = [
    "streamlit",
    "google-genai",
    "gtts",
    "qrcode",
    "pillow",
    "fpdf2",
    "gspread",
    "google-auth",
    "pandas",
    "streamlit-js-eval",
    "psycopg[binary]",
    "deep-translator",
    "requests",
    "pypdfium2",
    "pydub",
    "static-ffmpeg"
]


@st.cache_data(ttl=1800, show_spinner=False)
def check_libraries_updates() -> list[dict]:
    """Compara las versiones instaladas localmente contra las últimas disponibles en PyPI."""
    resultados = []
    for pkg in MANAGED_PACKAGES:
        pkg_clean = pkg.split("[")[0].strip()
        try:
            ver_local = pkg_version(pkg_clean)
        except PackageNotFoundError:
            ver_local = "No instalada"

        ver_pypi = "Desconocida"
        estado = "⚠️ Sin verificar"
        try:
            resp = requests.get(f"https://pypi.org{pkg_clean}/json", timeout=3.0)
            if resp.status_code == 200:
                ver_pypi = str(resp.json().get("info", {}).get("version", "Desconocida")).strip()
                if ver_local == "No instalada":
                    estado = "📥 Pendiente de instalar"
                elif ver_local == ver_pypi:
                    estado = "✅ Actualizada"
                else:
                    estado = "🔄 Nueva versión disponible"
        except Exception:
            estado = "⚠️ Error de red PyPI"

        resultados.append({
            "Paquete": pkg_clean,
            "Instalada": ver_local,
            "Última PyPI": ver_pypi,
            "Estado": estado,
            "pip_spec": pkg
        })
    return resultados

def upgrade_managed_libraries(paquetes: list[str] | None = None) -> tuple[bool, str]:
    """Ejecuta pip install --upgrade sobre las librerías integradas sin modificar código."""
    objetivos = paquetes or MANAGED_PACKAGES
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", *objetivos]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        check_libraries_updates.clear()
        if proc.returncode == 0:
            return True, "✅ Todas las librerías seleccionadas se actualizaron correctamente. Reiniciando entorno..."
        err_msg = (proc.stderr or proc.stdout or "Error desconocido en pip").strip()[-600:]
        return False, f"⚠️ Algunas librerías reportaron advertencias:\n{err_msg}"
    except Exception as e:
        return False, f"❌ No se pudo ejecutar la actualización automática: {e}"
# ==============================================================================
# PARTE 2 DE 15: CONFIGURACIÓN SEGURA, CATÁLOGOS CEFR Y CLIENTES EN CACHÉ
# ==============================================================================
DEFAULT_ADDRESS = st.secrets.get(
    "INSTITUTE_ADDRESS",
    "Dirección no configurada | Tel. / Contacto: No disponible"
)

ROLES_LISTA = [
    "Estudiante",
    "Teacher",
    "Propietario",
    "Administrador",
    "Empleado",
    "Socio Afiliado"
]

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
    "Gestionar_Usuarios",
    "Editar_Permisos",
    "Emitir_Certificados",
    "Revocar_Certificados",
    "Editar_Instituto_Logo",
    "Previsualizar_A1_C2",
    "Reuso_Ilimitado_Folios",
    "Editar_Fecha_Inicio_Curso",
    "Gestionar_Comisiones_Afiliados",
    "Gestionar_IVA_Mensualidad"
]

DEFAULT_PERMISSIONS_MATRIX = {
    "Total": {c: True for c in CAPABILITY_COLS},
    "Academico": {
        "Ver_Panel_Admin": True,
        "Registrar_Usuarios": True,
        "Gestionar_Usuarios": True,
        "Editar_Permisos": False,
        "Emitir_Certificados": True,
        "Revocar_Certificados": False,
        "Editar_Instituto_Logo": False,
        "Previsualizar_A1_C2": True,
        "Reuso_Ilimitado_Folios": True,
        "Editar_Fecha_Inicio_Curso": False,
        "Gestionar_Comisiones_Afiliados": False,
        "Gestionar_IVA_Mensualidad": False
    },
    "Certificador": {
        "Ver_Panel_Admin": True,
        "Registrar_Usuarios": False,
        "Gestionar_Usuarios": False,
        "Editar_Permisos": False,
        "Emitir_Certificados": True,
        "Revocar_Certificados": True,
        "Editar_Instituto_Logo": False,
        "Previsualizar_A1_C2": False,
        "Reuso_Ilimitado_Folios": True,
        "Editar_Fecha_Inicio_Curso": False,
        "Gestionar_Comisiones_Afiliados": False,
        "Gestionar_IVA_Mensualidad": False
    },
    "Auditoria": {
        "Ver_Panel_Admin": True,
        "Registrar_Usuarios": False,
        "Gestionar_Usuarios": False,
        "Editar_Permisos": False,
        "Emitir_Certificados": False,
        "Revocar_Certificados": False,
        "Editar_Instituto_Logo": False,
        "Previsualizar_A1_C2": True,
        "Reuso_Ilimitado_Folios": True,
        "Editar_Fecha_Inicio_Curso": False,
        "Gestionar_Comisiones_Afiliados": False,
        "Gestionar_IVA_Mensualidad": False
    },
    "Basico": {c: False for c in CAPABILITY_COLS}
}

CEFR_MAP = {
    "A1": "A1 (Beginner)",
    "A2": "A2 (Elementary)",
    "B1": "B1 (Intermediate)",
    "B2": "B2 (Upper-Intermediate)",
    "C1": "C1 (Advanced)",
    "C2": "C2 (Proficiency)"
}

def normalize_cefr(raw_val) -> str:
    code = str(raw_val or "").strip().upper()[:2]
    return CEFR_MAP.get(code, "B1 (Intermediate)")

CEFR_GRAMMAR_TOPICS = {
    "A1": [
        "Verb To Be & Personal Pronouns",
        "Present Simple (Affirmative, Negative & Questions)",
        "Articles (a, an, the) & Plurals",
        "There is / There are & Prepositions of Place",
        "Possessive Adjectives & Saxon Genitive ('s)",
        "Can / Can't for Ability & Permission",
        "Present Continuous (Actions Happening Now)"
    ],
    "A2": [
        "Past Simple (Regular & Irregular Verbs)",
        "Past Continuous vs. Past Simple",
        "Going to & Will for Future Plans/Predictions",
        "Comparatives & Superlatives",
        "Countable & Uncountable Nouns (some, any, much, many)",
        "Modal Verbs of Obligation (must, have to, should)",
        "Present Perfect Simple (ever, never, just, already, yet)",
        "Adverbs of Frequency & Manner"
    ],
    "B1": [
        "Present Perfect vs. Past Simple",
        "First & Second Conditionals (If / Unless)",
        "Modal Verbs of Deduction & Possibility (might, may, could, must)",
        "Passive Voice (Present & Past Simple)",
        "Relative Clauses (who, which, that, where, whose)",
        "Used to / Would for Past Habits",
        "Reported Speech (Statements & Questions)",
        "Gerunds vs. Infinitives",
        "Connectors of Contrast, Cause & Result"
    ],
    "B2": [
        "Third Conditional & Mixed Conditionals",
        "Passive Voice (All Tenses & Causative Have/Get)",
        "Modal Perfects (must have, should have, could have)",
        "Narrative Tenses (Past Simple, Continuous & Perfect)",
        "Reported Speech (Commands, Reporting Verbs & Indirect Questions)",
        "Defining & Non-Defining Relative Clauses",
        "Future Continuous & Future Perfect",
        "Phrasal Verbs & Collocations in Academic Contexts",
        "Wish / If Only for Regrets & Hypothetical Situations"
    ],
    "C1": [
        "Inversion after Negative & Restrictive Adverbials",
        "Cleft Sentences for Emphasis (It-clefts & Wh-clefts)",
        "Subjunctive Mood & Unreal Past",
        "Participle Clauses (Present, Past & Perfect Participles)",
        "Advanced Passive Structures (It is said that / He is believed to)",
        "Mixed Conditionals & Ellipsis in If-Clauses",
        "Nuanced Modality & Epistemic Stance",
        "Nominalization & Academic Cohesion",
        "Discourse Markers for Argumentation & Concession",
        "Hedging & Academic Register Precision"
    ],
    "C2": [
        "Complex Syntactic Inversion & Fronting",
        "Advanced Ellipsis, Substitution & Parallelism",
        "Subtlety in Modality, Counterfactuals & Subjunctive",
        "Rhetorical Clefting & Information Packaging",
        "Lexical Precision, Idiomaticity & Register Shifts",
        "Nominalized Academic Discourse & Dense Clause Embedding",
        "Pragmatic Hedging & Critical Stance",
        "Cohesive Devices in High-Level Academic Prose",
        "Stylistic Variation & Syntactic Economy",
        "Cross-Clause Referencing & Advanced Conjunctions"
    ]
}

@st.cache_resource
def init_gemini_client():
    api_key = str(
        st.secrets.get("GEMINI_API_KEY", "")
        or next((sec["GEMINI_API_KEY"] for sec in st.secrets.values() if isinstance(sec, dict) and "GEMINI_API_KEY" in sec), "")
    ).strip()
    if not api_key:
        st.warning("⚠️ GEMINI_API_KEY no configurada en Secrets.")
        return None
    return genai.Client(api_key=api_key)

client = init_gemini_client()

@st.cache_resource(show_spinner=False)
def get_google_workbook():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("Falta configurar [gcp_service_account] en Secrets.")
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["token_uri"] = "https://googleapis.com"
    if "private_key" in creds_dict:
        creds_dict["private_key"] = str(creds_dict["private_key"]).replace("\\n", "\n")

    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://googleapis.com",
            "https://googleapis.com"
        ]
    )
    gc = gspread.authorize(creds)
    sheet_key = str(st.secrets.get("spreadsheet_key", "")).strip()
    if sheet_key:
        return gc.open_by_key(sheet_key)
    sheet_url = str(st.secrets.get("GOOGLE_SHEET_URL", "")).strip()
    if sheet_url:
        return gc.open_by_url(sheet_url)
    sheet_name = str(st.secrets.get("GOOGLE_SHEET_NAME", "CEI_Database")).strip()
    return gc.open(sheet_name)

def get_google_sheet():
    return get_google_workbook().sheet1

def get_certificados_sheet():
    ss = get_google_workbook()
    try:
        return ss.worksheet("Certificados")
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title="Certificados", rows=200, cols=9)
        ws.append_row([
            "Folio_Certificado", "Clave_Alumno", "Nombre_Estudiante", "Nivel_CEFR",
            "Programa_Curso", "Calificacion", "Fecha_Emision", "Sello_Digital_SHA256", "Estatus"
        ])
        return ws

def get_pg_conn():
    def _find_secret(key_name: str) -> str:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
        for sec in st.secrets.values():
            if isinstance(sec, dict) and key_name in sec:
                return str(sec[key_name]).strip()
        return ""

    pg_host = _find_secret("PG_HOST")
    pg_user = _find_secret("PG_USER")
    pg_pass = _find_secret("PG_PASSWORD")
    pg_port = int(_find_secret("PG_PORT") or 6543)
    pg_db = _find_secret("PG_DBNAME") or "postgres"

    if pg_host and pg_user and pg_pass:
        return psycopg.connect(
            host=pg_host,
            port=pg_port,
            dbname=pg_db,
            user=pg_user,
            password=pg_pass,
            sslmode="require",
            prepare_threshold=None
        )

    db_url = _find_secret("DATABASE_URL")
    if db_url.startswith("postgres") and "@" in db_url:
        return psycopg.connect(db_url, sslmode="require", prepare_threshold=None)

    raise ValueError(
        f"No se encontraron credenciales de Supabase en Secrets "
        f"(PG_HOST={'OK' if pg_host else 'VACIO'}, PG_USER={'OK' if pg_user else 'VACIO'}, PG_PASSWORD={'OK' if pg_pass else 'VACIO'})."
    )

@contextmanager
def pg_session(dict_rows: bool = False):
    """Abre una conexión a PostgreSQL, confirma la transacción y la cierra siempre al salir."""
    conn = get_pg_conn()
    try:
        with conn:
            cur_kwargs = {"row_factory": dict_row} if dict_rows else {}
            with conn.cursor(**cur_kwargs) as cur:
                yield cur
    finally:
        try:
            conn.close()
        except Exception:
            pass
# ==============================================================================
# PARTE 3A: GESTIÓN DE IMÁGENES, LOGOTIPO INSTITUCIONAL Y MATRIZ RBAC
# ==============================================================================
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
    b64_str = ""
    while quality >= 30:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        if len(b64_str) <= 40000:
            return b64_str, "image/jpeg"
        quality -= 10
    return b64_str, "image/jpeg"

def get_default_logo_b64():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "LOGO CEI APP.png")
    try:
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8"), "image/png"
    except Exception:
        return None, None

@st.cache_data(ttl=60, show_spinner=False)
def load_permanent_logo():
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("SELECT * FROM institute_config WHERE id = 1;")
            row = cur.fetchone()
            if row:
                return {
                    "Logo_Base64": row.get("logo_base64") or "",
                    "Mime_Type": row.get("mime_type") or "image/png",
                    "Width": row.get("logo_width") or 115,
                    "Shape": row.get("logo_shape") or "Circular",
                    "Direccion": row.get("direccion") or DEFAULT_ADDRESS
                }
    except Exception:
        pass
    return None

def save_permanent_config(logo_b64: str, mime_type: str, width: int, shape: str, direccion: str):
    with pg_session() as cur:
        cur.execute("""
            INSERT INTO institute_config (id, logo_base64, mime_type, logo_width, logo_shape, direccion, updated_at)
            VALUES (1, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                logo_base64 = EXCLUDED.logo_base64,
                mime_type = EXCLUDED.mime_type,
                logo_width = EXCLUDED.logo_width,
                logo_shape = EXCLUDED.logo_shape,
                direccion = EXCLUDED.direccion,
                updated_at = NOW();
        """, (
            str(logo_b64 or ""),
            str(mime_type or "image/png"),
            int(width or 115),
            str(shape or "Circular"),
            str(direccion or DEFAULT_ADDRESS)
        ))
    load_permanent_logo.clear()

@st.cache_data(ttl=60, show_spinner=False)
def load_permissions_matrix() -> dict:
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("SELECT * FROM roles_permissions;")
            rows = cur.fetchall()
            if rows:
                matrix = {}
                for r in rows:
                    prof = str(r.get("profile_name", "")).strip()
                    if not prof:
                        continue
                    caps_j = r.get("capabilities_json")
                    if isinstance(caps_j, str):
                        caps_j = json.loads(caps_j)
                    if isinstance(caps_j, dict) and caps_j:
                        matrix[prof] = {c: bool(caps_j.get(c, False)) for c in CAPABILITY_COLS}
                    else:
                        base_prof = DEFAULT_PERMISSIONS_MATRIX.get(prof, DEFAULT_PERMISSIONS_MATRIX["Basico"]).copy()
                        base_prof["Emitir_Certificados"] = bool(r.get("emitir_certificados", base_prof["Emitir_Certificados"]))
                        base_prof["Registrar_Usuarios"] = bool(r.get("gestionar_usuarios", base_prof["Registrar_Usuarios"]))
                        base_prof["Gestionar_Usuarios"] = bool(r.get("gestionar_usuarios", base_prof["Gestionar_Usuarios"]))
                        base_prof["Ver_Panel_Admin"] = bool(r.get("gestionar_usuarios", base_prof["Ver_Panel_Admin"]))
                        base_prof["Editar_Instituto_Logo"] = bool(r.get("editar_instituto_logo", base_prof["Editar_Instituto_Logo"]))
                        matrix[prof] = base_prof
                if matrix:
                    return matrix
    except Exception:
        pass
    return {k: v.copy() for k, v in DEFAULT_PERMISSIONS_MATRIX.items()}
# ==============================================================================
# PARTE 3B: RESOLUCIÓN RBAC, PADRÓN DE USUARIOS Y ASIGNACIÓN DE AFILIADOS
# ==============================================================================
def resolve_permission_profile(raw_perm, raw_role, matrix_dict):
    if not matrix_dict or not isinstance(matrix_dict, dict):
        return "Total" if str(raw_role or "").strip().lower() in ["propietario", "administrador", "admin"] else "Basico"
    p = str(raw_perm or "").strip()
    for k in matrix_dict.keys():
        if k.lower() == p.lower():
            return k
    r = str(raw_role or "").strip().lower()
    if r in ["propietario", "administrador", "admin"] and "Total" in matrix_dict:
        return "Total"
    if r in ["teacher", "docente"]:
        if "Academico" in matrix_dict:
            return "Academico"
        if "Docente" in matrix_dict:
            return "Docente"
    return "Basico" if "Basico" in matrix_dict else next(iter(matrix_dict.keys()), "Basico")

def upsert_permission_profile_pg(perfil_name: str, caps_dict: dict):
    with pg_session() as cur:
        cur.execute("""
            INSERT INTO roles_permissions (
                profile_name, generar_leccion, resolver_quiz, grabar_audio,
                emitir_certificados, gestionar_usuarios, editar_instituto_logo, capabilities_json
            ) VALUES (%s, TRUE, TRUE, TRUE, %s, %s, %s, %s::jsonb)
            ON CONFLICT (profile_name) DO UPDATE SET
                emitir_certificados = EXCLUDED.emitir_certificados,
                gestionar_usuarios = EXCLUDED.gestionar_usuarios,
                editar_instituto_logo = EXCLUDED.editar_instituto_logo,
                capabilities_json = EXCLUDED.capabilities_json,
                updated_at = NOW();
        """, (
            perfil_name.strip(),
            bool(caps_dict.get("Emitir_Certificados", False)),
            bool(caps_dict.get("Registrar_Usuarios", caps_dict.get("Gestionar_Usuarios", False))),
            bool(caps_dict.get("Editar_Instituto_Logo", False)),
            json.dumps({c: bool(caps_dict.get(c, False)) for c in CAPABILITY_COLS})
        ))
    load_permissions_matrix.clear()

@st.cache_data(ttl=60)
def load_padron_records() -> list[dict]:
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT
                    u.id,
                    u.matricula,
                    u.usuario,
                    u.clave_hash,
                    u.rol,
                    u.grado_academico,
                    u.nivel_cefr,
                    u.permisos,
                    u.estatus,
                    u.afiliador_id,
                    COALESCE(aff.matricula || ' — ' || aff.usuario, NULLIF(TRIM(u.afiliado_usuario), ''), 'Directo / Sin afiliador') AS afiliador_nombre
                FROM users_padron u
                LEFT JOIN users_padron aff ON u.afiliador_id = aff.id
                ORDER BY u.id ASC;
            """)
            rows = cur.fetchall()
            return [
                {
                    "ID": r.get("id"),
                    "Matricula": r.get("matricula") or f"CEI-2026-{int(r.get('id', 0)):04d}",
                    "Usuario": r.get("usuario", ""),
                    "Clave": r.get("clave_hash", ""),
                    "Rol": r.get("rol", "Estudiante"),
                    "Grado_Academico": r.get("grado_academico", "Licenciatura / Universidad"),
                    "Nivel": r.get("nivel_cefr", "B1"),
                    "Permisos": r.get("permisos", "Basico"),
                    "Estatus": r.get("estatus", "Activo"),
                    "Afiliador_ID": r.get("afiliador_id"),
                    "Socio_Afiliador": r.get("afiliador_nombre", "Directo / Sin afiliador")
                }
                for r in rows
            ]
    except Exception as e_pg:
        st.session_state["db_auth_diag"] = f"PostgreSQL Error: {e_pg}"
        try:
            ws_pad = get_google_workbook().worksheet("Padron")
            return ws_pad.get_all_records()
        except Exception:
            return []

def upsert_user_padron_pg(
    usuario: str, clave: str, rol: str, grado: str, nivel: str, permisos: str, estatus: str,
    afiliador_id: int | None = None
) -> str:
    anio_actual = datetime.now(ZoneInfo("America/Hermosillo")).year
    with pg_session() as cur:
        cur.execute("INSERT INTO roles_permissions (profile_name) VALUES (%s) ON CONFLICT DO NOTHING;", (permisos.strip(),))
        aff_user_name = None
        if afiliador_id is not None:
            cur.execute("SELECT usuario FROM users_padron WHERE id = %s LIMIT 1;", (int(afiliador_id),))
            r_aff = cur.fetchone()
            aff_user_name = r_aff[0] if r_aff else None

        cur.execute("""
            INSERT INTO users_padron (usuario, clave_hash, rol, grado_academico, nivel_cefr, permisos, estatus, afiliador_id, afiliado_usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (usuario) DO UPDATE SET
                clave_hash = EXCLUDED.clave_hash,
                rol = EXCLUDED.rol,
                grado_academico = EXCLUDED.grado_academico,
                nivel_cefr = EXCLUDED.nivel_cefr,
                permisos = EXCLUDED.permisos,
                estatus = EXCLUDED.estatus,
                afiliador_id = COALESCE(EXCLUDED.afiliador_id, users_padron.afiliador_id),
                afiliado_usuario = COALESCE(EXCLUDED.afiliado_usuario, users_padron.afiliado_usuario)
            RETURNING id, matricula;
        """, (
            usuario.strip(),
            clave.strip(),
            rol.strip(),
            grado.strip(),
            normalize_cefr(nivel),
            permisos.strip(),
            "Activo" if estatus.strip().lower() == "activo" else "Inactivo",
            afiliador_id,
            aff_user_name
        ))
        row_ret = cur.fetchone()
        user_id_db = row_ret[0]
        mat_actual = row_ret[1]

        if not mat_actual:
            mat_actual = f"CEI-{anio_actual}-{int(user_id_db):04d}"
            cur.execute("UPDATE users_padron SET matricula = %s WHERE id = %s;", (mat_actual, user_id_db))

    load_padron_records.clear()
    return mat_actual

def set_student_affiliate_pg(student_id: int, afiliador_id: int | None):
    with pg_session() as cur:
        aff_nom = ""
        if afiliador_id is not None:
            cur.execute("SELECT usuario FROM users_padron WHERE id = %s LIMIT 1;", (int(afiliador_id),))
            r_a = cur.fetchone()
            aff_nom = str(r_a[0] or "").strip() if r_a else ""
        cur.execute(
            "UPDATE users_padron SET afiliador_id = %s, afiliado_usuario = %s WHERE id = %s;",
            (afiliador_id, aff_nom, int(student_id))
        )
    load_padron_records.clear()
# ==============================================================================
# PARTE 4A: PERSISTENCIA UNIFICADA DE LECCIONES, QUIZZES Y ORAL (lessons_folios)
# ==============================================================================
def _extract_numeric_score(score_str: str) -> float:
    if not score_str:
        return -1.0
    m = re.search(r"\((\d+(?:\.\d+)?)%\)", str(score_str))
    if m:
        return float(m.group(1))
    m2 = re.search(r"(\d+(?:\.\d+)?)", str(score_str))
    return float(m2.group(1)) if m2 else -1.0

def save_lesson_to_postgres(folio: str, usuario_name: str, tema: str, cefr: str, grado: str, texto: str, pdf_link: str):
    with pg_session() as cur:
        cur.execute("SELECT id FROM users_padron WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) LIMIT 1;", (usuario_name.strip(),))
        u_row = cur.fetchone()
        uid = u_row if u_row else None
        if uid is None:
            cur.execute("""
                INSERT INTO users_padron (usuario, clave_hash, rol, permisos, estatus)
                VALUES (%s, 'AUTO_SESSION', 'Estudiante', 'Basico', 'Activo')
                RETURNING id;
            """, (usuario_name.strip(),))
            uid = cur.fetchone()

        cur.execute("""
            INSERT INTO lessons_folios (folio, user_id, tema, cefr_level, academic_grade, lesson_text, pdf_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (folio) DO UPDATE SET
                lesson_text = EXCLUDED.lesson_text,
                pdf_link = EXCLUDED.pdf_link,
                updated_at = NOW();
        """, (folio.strip().upper(), uid, tema, cefr, grado, texto, pdf_link))

def save_quiz_and_best_score_pg(folio: str, nota_actual: str, quiz_items: list, user_ans: dict) -> tuple[bool, str, str]:
    f_clean = str(folio or "").strip().upper()
    if not f_clean:
        return False, "Folio no asignado.", nota_actual

    new_num = _extract_numeric_score(nota_actual)
    serializable_ans = {str(k): v for k, v in (user_ans or {}).items()}

    with pg_session(dict_rows=True) as cur:
        cur.execute("""
            SELECT best_quiz_score, best_quiz_numeric
            FROM lessons_folios WHERE UPPER(TRIM(folio)) = %s LIMIT 1;
        """, (f_clean,))
        row = cur.fetchone()
        if not row:
            return False, "Folio no encontrado en Supabase.", nota_actual

        prev_best_str = str(row.get("best_quiz_score") or "").strip()
        prev_num = float(row["best_quiz_numeric"]) if row.get("best_quiz_numeric") is not None else _extract_numeric_score(prev_best_str)

        if new_num < 0:
            cur.execute("""
                UPDATE lessons_folios
                SET quiz_data = %s::jsonb, updated_at = NOW()
                WHERE UPPER(TRIM(folio)) = %s;
            """, (json.dumps(quiz_items, ensure_ascii=False), f_clean))
            return False, "", prev_best_str

        if prev_num < 0 or new_num >= prev_num:
            cur.execute("""
                UPDATE lessons_folios
                SET quiz_data = %s::jsonb,
                    best_quiz_score = %s,
                    best_quiz_numeric = %s,
                    best_quiz_answers = %s::jsonb,
                    updated_at = NOW()
                WHERE UPPER(TRIM(folio)) = %s;
            """, (
                json.dumps(quiz_items, ensure_ascii=False),
                nota_actual,
                new_num,
                json.dumps(serializable_ans, ensure_ascii=False),
                f_clean
            ))
            msg = f"🏆 ¡Nueva mejor calificación guardada en Supabase para `{f_clean}`: **{nota_actual}**!"
            return True, msg, nota_actual
        else:
            msg = f"ℹ️ Se conserva tu calificación más alta previa en Supabase: **{prev_best_str}** (intento actual: {nota_actual})."
            return False, msg, prev_best_str

def save_best_speaking_pg(folio: str, score_pct: int):
    f_clean = str(folio or "").strip().upper()
    if not f_clean:
        return
    try:
        eval_obj = st.session_state.get("speaking_eval_result")
        eval_json = json.dumps(eval_obj, ensure_ascii=False) if isinstance(eval_obj, dict) else None
        with pg_session() as cur:
            cur.execute("""
                UPDATE lessons_folios
                SET best_speaking_score = GREATEST(COALESCE(best_speaking_score, -1), %s),
                    speaking_eval_json = COALESCE(%s::jsonb, speaking_eval_json),
                    updated_at = NOW()
                WHERE UPPER(TRIM(folio)) = %s;
            """, (float(score_pct), eval_json, f_clean))
    except Exception:
        pass
# ==============================================================================
# PARTE 4B: CONSULTA DE FOLIOS, HISTORIAL Y LIBRETA POR GRAMMAR TOPIC (PG)
# ==============================================================================
def fetch_lesson_by_folio(folio_code: str) -> dict | None:
    folio_clean = str(folio_code or "").strip().upper()
    if not folio_clean:
        return None
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT
                    f.*,
                    COALESCE(u.usuario, 'Usuario') AS usuario,
                    TO_CHAR(f.created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI:SS') AS fecha_fmt
                FROM lessons_folios f
                LEFT JOIN users_padron u ON f.user_id = u.id
                WHERE UPPER(TRIM(f.folio)) = %s
                LIMIT 1;
            """, (folio_clean,))
            r = cur.fetchone()
            if r:
                q_raw = r.get("quiz_data")
                ans_raw = r.get("best_quiz_answers")
                spk_raw = r.get("speaking_eval_json")
                spk_val = r.get("best_speaking_score")
                return {
                    "Folio": r.get("folio"),
                    "Usuario": r.get("usuario"),
                    "Tema": r.get("tema"),
                    "CEFR": r.get("cefr_level"),
                    "Grade": r.get("academic_grade"),
                    "Text": r.get("lesson_text"),
                    "Quiz": q_raw if isinstance(q_raw, (list, dict)) else (json.loads(q_raw) if q_raw else None),
                    "Best_Score": r.get("best_quiz_score") or "",
                    "Best_Answers": ans_raw if isinstance(ans_raw, dict) else (json.loads(ans_raw) if ans_raw else {}),
                    "Speaking_Score": float(spk_val) if spk_val is not None else -1.0,
                    "Speaking_Eval": spk_raw if isinstance(spk_raw, dict) else (json.loads(spk_raw) if spk_raw else None),
                    "PDF_Link": r.get("pdf_link") or "",
                    "Created_At": r.get("fecha_fmt") or ""
                }
    except Exception:
        pass
    return None

def load_lessons_history_pg() -> list[dict]:
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT
                    f.folio AS "Folio",
                    COALESCE(u.usuario, 'Usuario') AS "Usuario",
                    f.tema AS "Tema",
                    f.cefr_level AS "Nivel_CEFR",
                    f.academic_grade AS "Grado_Academico",
                    f.lesson_text AS "Texto",
                    f.quiz_data AS "Quiz_JSON",
                    f.best_quiz_score AS "Mejor_Calificacion_PDF",
                    f.best_speaking_score AS "Speaking_Score",
                    f.speaking_eval_json AS "Speaking_Eval",
                    f.pdf_link AS "PDF_Link",
                    TO_CHAR(f.created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS "Fecha_de_subida"
                FROM lessons_folios f
                LEFT JOIN users_padron u ON f.user_id = u.id
                ORDER BY f.created_at DESC
                LIMIT 120;
            """)
            return cur.fetchall()
    except Exception:
        return []

def fetch_student_gradebook_pg(target_usuario: str) -> dict:
    """Calcula promedios y desglose por Grammar Topic del nivel CEFR desde lessons_folios."""
    default_res = {
        "matricula": "CEI-2026-0000",
        "nivel_cefr": "B1 (Intermediate)",
        "grado": "",
        "records": [],
        "topic_summary": [],
        "overall_avg": 0.0,
        "quiz_avg": 0.0,
        "oral_avg": 0.0
    }
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT id,
                       COALESCE(matricula, 'CEI-2026-' || LPAD(id::text, 4, '0')) AS matricula,
                       COALESCE(nivel_cefr, 'B1') AS nivel_cefr,
                       COALESCE(grado_academico, 'Licenciatura / Universidad') AS grado_academico
                FROM users_padron
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (target_usuario.strip(),))
            u_row = cur.fetchone() or {}

            cur.execute("""
                SELECT
                    f.folio,
                    f.tema,
                    f.cefr_level,
                    f.best_quiz_score,
                    COALESCE(f.best_speaking_score, -1) AS speaking_score,
                    TO_CHAR(f.created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS fecha
                FROM lessons_folios f
                JOIN users_padron u ON f.user_id = u.id
                WHERE LOWER(TRIM(u.usuario)) = LOWER(TRIM(%s))
                ORDER BY f.created_at DESC;
            """, (target_usuario.strip(),))
            rows = cur.fetchall()
    except Exception:
        return default_res

    def _parse_quiz_pct(score_str: str) -> float | None:
        m = re.search(r"\((\d+(?:\.\d+)?)%\)", str(score_str or ""))
        if m:
            return float(m.group(1))
        m2 = re.search(r"(\d+(?:\.\d+)?)%", str(score_str or ""))
        return float(m2.group(1)) if m2 else None

    def _extract_grammar_from_tema(tema_raw: str) -> str:
        t_str = str(tema_raw or "").strip()
        m_par = re.search(r"\(([^()]+)\)\s*$", t_str)
        if m_par:
            return m_par.group(1).strip()
        return t_str or "General Applied Grammar"

    nivel_alumno = normalize_cefr(u_row.get("nivel_cefr", "B1"))
    cefr_short_key = nivel_alumno[:2]
    catalogo_nivel = CEFR_GRAMMAR_TOPICS.get(cefr_short_key, CEFR_GRAMMAR_TOPICS["B1"])

    por_tema = {t: {"scores": [], "lecciones": 0} for t in catalogo_nivel}
    registros_procesados = []
    todas_quiz, todas_oral, todas_combinadas = [], [], []

    for r in rows:
        q_pct = _parse_quiz_pct(r.get("best_quiz_score"))
        o_raw = float(r.get("speaking_score") if r.get("speaking_score") is not None else -1)
        o_pct = o_raw if o_raw > 0 else None

        notas_item = [x for x in [q_pct, o_pct] if x is not None]
        prom_leccion = round(sum(notas_item) / len(notas_item), 1) if notas_item else None

        if q_pct is not None:
            todas_quiz.append(q_pct)
        if o_pct is not None:
            todas_oral.append(o_pct)
        if prom_leccion is not None:
            todas_combinadas.append(prom_leccion)

        g_topic = _extract_grammar_from_tema(r.get("tema"))
        if g_topic not in por_tema:
            por_tema[g_topic] = {"scores": [], "lecciones": 0}
        por_tema[g_topic]["lecciones"] += 1
        if prom_leccion is not None:
            por_tema[g_topic]["scores"].append(prom_leccion)

        registros_procesados.append({
            "Folio": r.get("folio", ""),
            "Fecha": r.get("fecha", ""),
            "Nivel": r.get("cefr_level", ""),
            "Grammar_Topic": g_topic,
            "Tema_Leccion": r.get("tema", ""),
            "Quiz_Pct": f"{q_pct}%" if q_pct is not None else "Pendiente",
            "Oral_Pct": f"{o_pct}%" if o_pct is not None else "Pendiente",
            "Promedio_Leccion": f"{prom_leccion}%" if prom_leccion is not None else "Sin evaluar"
        })

    resumen_temas = []
    for topic_name, info in por_tema.items():
        avg_t = round(sum(info["scores"]) / len(info["scores"]), 1) if info["scores"] else 0.0
        estado_t = "Acreditado" if avg_t >= 70.0 else ("En progreso" if info["lecciones"] > 0 else "Pendiente")
        resumen_temas.append({
            "Grammar Topic": topic_name,
            "Dominio (%)": avg_t,
            "Lecciones": info["lecciones"],
            "Estatus": estado_t
        })

    return {
        "matricula": u_row.get("matricula", "CEI-2026-0000"),
        "nivel_cefr": nivel_alumno,
        "grado": u_row.get("grado_academico", ""),
        "records": registros_procesados,
        "topic_summary": resumen_temas,
        "overall_avg": round(sum(todas_combinadas) / len(todas_combinadas), 1) if todas_combinadas else 0.0,
        "quiz_avg": round(sum(todas_quiz) / len(todas_quiz), 1) if todas_quiz else 0.0,
        "oral_avg": round(sum(todas_oral) / len(todas_oral), 1) if todas_oral else 0.0
    }
# ==============================================================================
# PARTE 5: MOTOR CRIPTOGRÁFICO (HMAC-SHA256), CERTIFICADOS Y BOLETINES (PG)
# ==============================================================================
def clean_pdf_text(text: str) -> str:
    if not text:
        return ""
    reemplazos = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "*"
    }
    res = str(text)
    for orig, dest in reemplazos.items():
        res = res.replace(orig, dest)
    return res.encode("latin-1", "replace").decode("latin-1")

def _get_hmac_secret_bytes() -> bytes:
    key_val = (
        st.secrets.get("HMAC_SECRET_KEY")
        or st.secrets.get("CERT_HMAC_SECRET")
        or st.secrets.get("spreadsheet_key")
        or "CEI-2026-MASTER-SEAL"
    )
    return str(key_val).strip().encode("utf-8")

def generar_sello_digital(folio_cert: str, clave_est: str, nombre_est: str, nivel_cefr: str, fecha_emision: str):
    llave_secreta = _get_hmac_secret_bytes()
    cadena_original = f"||CEI|{folio_cert}|{clave_est}|{nombre_est}|{nivel_cefr}|{fecha_emision}|JACOB-ZUMAYA-PRIANTI||"
    sello_hex = hmac.new(llave_secreta, cadena_original.encode("utf-8"), hashlib.sha256).hexdigest().upper()
    return cadena_original, sello_hex

def _build_cert_verify_url(folio_cert: str) -> str:
    base_url = str(st.secrets.get("APP_PUBLIC_URL") or st.secrets.get("APP_BASE_URL") or "").strip().rstrip("/")
    f_clean = urllib.parse.quote(str(folio_cert).strip().upper())
    return f"{base_url}/?verify_cert={f_clean}" if base_url else f"/?verify_cert={f_clean}"

def insert_certificate_pg(folio_c: str, clave_sel: str, nombre_sel: str, nivel_sel: str, grado_sel: str, programa_c: str, calif_c: str, fecha_c: str, sello_h: str):
    f_upper = folio_c.strip().upper()
    verify_url = _build_cert_verify_url(f_upper)

    with pg_session() as cur:
        cur.execute("SELECT id FROM users_padron WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) LIMIT 1;", (nombre_sel.strip(),))
        u_row = cur.fetchone()
        uid = u_row if u_row else None
        if uid is None:
            cur.execute("""
                INSERT INTO users_padron (usuario, clave_hash, rol, permisos, estatus)
                VALUES (%s, %s, 'Estudiante', 'Basico', 'Activo')
                RETURNING id;
            """, (nombre_sel.strip(), clave_sel.strip()))
            uid = cur.fetchone()

        cur.execute("""
            INSERT INTO certificates (
                folio_cert, user_id, clave_alumno, titular, nivel_cefr,
                grado_academico, programa, calificacion, fecha_emision,
                firma_hmac, estatus, verify_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Valido', %s)
            ON CONFLICT (folio_cert) DO NOTHING;
        """, (
            f_upper, uid, clave_sel.strip(), nombre_sel.strip(),
            nivel_sel.strip(), grado_sel.strip(), programa_c.strip(),
            calif_c.strip(), fecha_c.strip(), sello_h.strip(), verify_url
        ))

def verify_certificate_by_folio_pg(folio_cert: str) -> dict | None:
    folio_norm = str(folio_cert or "").strip().upper().replace("-", "").replace(" ", "")
    if not folio_norm:
        return None
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT
                    folio_cert AS "Folio_Certificado",
                    clave_alumno AS "Clave_Alumno",
                    titular AS "Nombre_Estudiante",
                    nivel_cefr AS "Nivel_CEFR",
                    grado_academico AS "Grado_Academico",
                    programa AS "Programa_Curso",
                    calificacion AS "Calificacion",
                    fecha_emision AS "Fecha_Emision",
                    firma_hmac AS "Sello_Digital_SHA256",
                    estatus AS "Estatus",
                    verify_url AS "URL_Verificacion"
                FROM certificates
                WHERE REPLACE(UPPER(TRIM(folio_cert)), '-', '') = %s
                LIMIT 1;
            """, (folio_norm,))
            return cur.fetchone()
    except Exception:
        return None

def update_certificate_link_pg(folio_cert: str, new_url: str = "") -> bool:
    f_clean = str(folio_cert or "").strip().upper()
    if not f_clean:
        return False
    url_final = str(new_url or "").strip() or _build_cert_verify_url(f_clean)
    try:
        with pg_session() as cur:
            cur.execute("""
                UPDATE certificates
                SET verify_url = %s
                WHERE UPPER(TRIM(folio_cert)) = %s;
            """, (url_final, f_clean))
        return True
    except Exception:
        return False

def load_certificates_pg() -> list[dict]:
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("SELECT * FROM certificates ORDER BY created_at DESC;")
            rows = cur.fetchall()
            return [
                {
                    "Folio_Certificado": r.get("folio_cert", ""),
                    "Clave_Alumno": r.get("clave_alumno", ""),
                    "Nombre_Estudiante": r.get("titular", ""),
                    "Nivel_CEFR": r.get("nivel_cefr", ""),
                    "Grado_Academico": r.get("grado_academico", ""),
                    "Programa": r.get("programa", ""),
                    "Calificacion": r.get("calificacion", ""),
                    "Fecha_Emision": r.get("fecha_emision", ""),
                    "Firma_HMAC": r.get("firma_hmac", ""),
                    "Estatus": "Vigente" if str(r.get("estatus", "")).lower() == "valido" else "Revocado"
                }
                for r in rows
            ]
    except Exception:
        return []

def update_certificate_status_pg(folio_cert: str, nuevo_estatus_ui: str):
    db_status = "Valido" if str(nuevo_estatus_ui).strip().lower() in ["vigente", "valido"] else "Revocado"
    with pg_session() as cur:
        cur.execute(
            "UPDATE certificates SET estatus = %s WHERE UPPER(TRIM(folio_cert)) = %s;",
            (db_status, str(folio_cert).strip().upper())
        )

def stamp_and_save_transcript_pg(student_name: str, gb_data: dict, topic_filter: str) -> dict:
    ahora_sonora = datetime.now(ZoneInfo("America/Hermosillo"))
    fecha_str = ahora_sonora.strftime("%Y-%m-%d %H:%M:%S MST")
    folio_bol = f"BOL-{ahora_sonora.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    matricula = str(gb_data.get("matricula") or "CEI-2026-0000").strip()
    nivel_c = str(gb_data.get("nivel_cefr") or "B1").strip()
    ov_avg = float(gb_data.get("overall_avg") or 0.0)
    qz_avg = float(gb_data.get("quiz_avg") or 0.0)
    or_avg = float(gb_data.get("oral_avg") or 0.0)
    tot_lec = len(gb_data.get("records") or [])

    secret_hmac = _get_hmac_secret_bytes()
    cadena_original = (
        f"{folio_bol}|{matricula}|{student_name.strip().upper()}|{nivel_c}|"
        f"{topic_filter}|{ov_avg:.2f}|{qz_avg:.2f}|{or_avg:.2f}|{tot_lec}|{fecha_str}"
    )
    sello_hmac = hmac.new(secret_hmac, cadena_original.encode("utf-8"), hashlib.sha256).hexdigest().upper()

    try:
        with pg_session() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transcripts_archive (
                    folio_boletin TEXT PRIMARY KEY,
                    matricula TEXT,
                    student_name TEXT NOT NULL,
                    nivel_cefr TEXT,
                    topic_filter TEXT,
                    overall_avg NUMERIC(5,2),
                    quiz_avg NUMERIC(5,2),
                    oral_avg NUMERIC(5,2),
                    total_lessons INT,
                    hmac_seal TEXT NOT NULL,
                    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            cur.execute("""
                INSERT INTO transcripts_archive (
                    folio_boletin, matricula, student_name, nivel_cefr, topic_filter,
                    overall_avg, quiz_avg, oral_avg, total_lessons, hmac_seal, issued_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                folio_bol, matricula, student_name.strip(), nivel_c, topic_filter,
                ov_avg, qz_avg, or_avg, tot_lec, sello_hmac, ahora_sonora
            ))
    except Exception:
        pass

    return {
        "folio_boletin": folio_bol,
        "fecha_generacion": fecha_str,
        "sello_hmac": sello_hmac,
        "cadena_original": cadena_original
    }
# ==============================================================================
# PARTE 6A: GENERADOR DE MONOGRAFÍA ACADÉMICA EN PDF (create_lesson_pdf)
# ==============================================================================
class AcademicPDF(FPDF):
    def __init__(self, folio_doc: str, cefr_doc: str, grado_doc: str, address_str: str):
        super().__init__()
        self.folio_doc = folio_doc
        self.cefr_doc = cefr_doc
        self.grado_doc = grado_doc
        self.address_str = address_str

    def header(self):
        self.set_y(10)
        self.set_font("Times", "B", 8.5)
        self.set_text_color(11, 37, 69)
        self.cell(self.epw * 0.65, 5, text=clean_pdf_text("CAREER ENGLISH INSTITUTE  |  APPLIED LINGUISTICS & DISCOURSE"), align="L")
        self.set_font("Times", "I", 8.5)
        self.set_text_color(100, 100, 100)
        cefr_short = next(iter(self.cefr_doc.split()), "CEFR") if self.cefr_doc else "CEFR"
        self.cell(self.epw * 0.35, 5, text=clean_pdf_text(f"Folio: {self.folio_doc}  |  CEFR {cefr_short}"), new_x="LMARGIN", new_y="NEXT", align="R")

        y_line = self.get_y() + 1
        self.set_draw_color(11, 37, 69)
        self.set_line_width(0.6)
        self.line(self.l_margin, y_line, self.w - self.r_margin, y_line)
        self.set_draw_color(184, 134, 11)
        self.set_line_width(0.25)
        self.line(self.l_margin, y_line + 1.2, self.w - self.r_margin, y_line + 1.2)
        self.set_y(y_line + 5)

    def footer(self):
        self.set_y(-16)
        y_f = self.get_y()
        self.set_draw_color(184, 134, 11)
        self.set_line_width(0.3)
        self.line(self.l_margin, y_f, self.w - self.r_margin, y_f)
        self.ln(2)

        self.set_font("Times", "I", 8)
        self.set_text_color(90, 90, 90)
        self.cell(self.epw * 0.75, 4, text=clean_pdf_text("© 2026 CAREER ENGLISH INSTITUTE  |  Author: Jacob Zumaya Prianti  |  APA 7th Ed. Standard"), align="L")
        self.set_font("Times", "B", 8.5)
        self.set_text_color(11, 37, 69)
        self.cell(self.epw * 0.25, 4, text=f"Page {self.page_no()} of {{nb}}", new_x="LMARGIN", new_y="NEXT", align="R")

        self.set_x(self.l_margin)
        self.set_font("Times", "", 7.5)
        self.set_text_color(110, 110, 110)
        self.cell(self.epw, 4, text=clean_pdf_text(self.address_str), align="C")



def create_lesson_pdf(text: str, quiz_items=None, user_ans=None, score=None, speaking_eval=None) -> bytes:
    folio_doc = st.session_state.get("current_folio") or "SIN-FOLIO"
    base_url = str(st.secrets.get("APP_PUBLIC_URL") or st.secrets.get("APP_BASE_URL") or "").strip().rstrip("/")
    default_link = f"{base_url}/?folio={urllib.parse.quote(folio_doc)}" if base_url else f"/?folio={urllib.parse.quote(folio_doc)}"
    link_doc = st.session_state.get("current_pdf_link") or default_link

    ahora_local = datetime.now(ZoneInfo("America/Hermosillo"))
    fecha_doc = st.session_state.get("current_creation_date") or ahora_local.strftime("%Y-%m-%d %H:%M:%S")
    grado_doc = st.session_state.get("selected_academic_grade") or "Licenciatura / Universidad"
    usuario_doc = st.session_state.get("current_user") or "Estudiante"
    rol_doc = st.session_state.get("user_role") or "Estudiante"
    cefr_doc = st.session_state.get("selected_cefr") or "B1 (Intermediate)"
    addr_doc = st.session_state.get("institute_address") or DEFAULT_ADDRESS

    pdf = AcademicPDF(folio_doc, cefr_doc, grado_doc, addr_doc)
    pdf.alias_nb_pages()
    pdf.set_margins(left=18, top=22, right=18)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_author("Jacob Zumaya Prianti")
    pdf.set_creator("Career English Institute - Academic Press")
    pdf.add_page()

    # Portada / Membrete
    y_box_start = pdf.get_y()
    pdf.set_fill_color(244, 247, 251)
    pdf.set_draw_color(11, 37, 69)
    pdf.set_line_width(0.4)
    pdf.rect(pdf.l_margin, y_box_start, pdf.epw, 42, style="FD")

    pdf.set_fill_color(184, 134, 11)
    pdf.rect(pdf.l_margin, y_box_start, 2.5, 42, style="F")

    logo_src = None
    perm_logo = load_permanent_logo()
    if perm_logo and perm_logo.get("Logo_Base64"):
        try:
            logo_src = io.BytesIO(base64.b64decode(perm_logo["Logo_Base64"]))
        except Exception:
            logo_src = None
    if logo_src is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_logo = os.path.join(base_dir, "LOGO CEI APP.png")
        if os.path.exists(local_logo):
            logo_src = local_logo
    if logo_src:
        try:
            pdf.image(logo_src, x=pdf.l_margin + 6, y=y_box_start + 6, w=26)
        except Exception:
            pass

    x_meta = pdf.l_margin + 36
    w_meta = pdf.epw - 40
    pdf.set_xy(x_meta, y_box_start + 4)
    pdf.set_font("Times", "B", 13)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(w_meta, 6, text="CAREER ENGLISH INSTITUTE", new_x="LMARGIN", new_y="NEXT", align="L")

    pdf.set_x(x_meta)
    pdf.set_font("Times", "B", 9.5)
    pdf.set_text_color(184, 134, 11)
    pdf.cell(w_meta, 5, text=clean_pdf_text(f"CEFR {cefr_doc}  |  {grado_doc.upper()}  |  ACADEMIC MONOGRAPH"), new_x="LMARGIN", new_y="NEXT", align="L")

    pdf.set_x(x_meta)
    pdf.set_font("Times", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(w_meta, 5, text=clean_pdf_text("Author & Senior Applied Linguist: Jacob Zumaya Prianti"), new_x="LMARGIN", new_y="NEXT", align="L")

    pdf.set_x(x_meta)
    pdf.cell(w_meta, 5, text=clean_pdf_text(f"Student / Candidate: {usuario_doc} ({rol_doc})  |  Date: {fecha_doc}"), new_x="LMARGIN", new_y="NEXT", align="L")

    pdf.set_x(x_meta)
    pdf.set_font("Times", "U", 8)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(w_meta, 5, text=clean_pdf_text(f"Digital Verification & Recovery: {link_doc}"), new_x="LMARGIN", new_y="NEXT", align="L", link=link_doc)

    pdf.set_y(y_box_start + 48)

    # Cuadro de desempeño
    try:
        topico_lec_pdf = st.session_state.get("selected_grammar_topic") or "Applied Grammar"
        gb_lec_actual = fetch_student_gradebook_pg(usuario_doc) if usuario_doc else {}
        t_match = next(
            (t for t in gb_lec_actual.get("topic_summary", []) if t["Grammar Topic"] == topico_lec_pdf),
            {}
        )
        nota_leccion_str = str(score or "Pendiente")
        nota_topico_str = f"{t_match.get('Dominio (%)', 0.0)}%"
        nota_general_str = f"{gb_lec_actual.get('overall_avg', 0.0)}%"

        y_perf = pdf.get_y()
        pdf.set_fill_color(244, 247, 251)
        pdf.set_draw_color(11, 37, 69)
        pdf.set_line_width(0.35)
        pdf.rect(pdf.l_margin, y_perf, pdf.epw, 13, style="FD")

        pdf.set_fill_color(184, 134, 11)
        pdf.rect(pdf.l_margin, y_perf, 2.5, 13, style="F")

        pdf.set_xy(pdf.l_margin + 5, y_perf + 3)
        pdf.set_font("Times", "B", 9.2)
        pdf.set_text_color(11, 37, 69)
        resumen_notas_txt = (
            f"Lesson Score: {nota_leccion_str}   |   "
            f"Topic Avg ({topico_lec_pdf[:26]}): {nota_topico_str}   |   "
            f"Overall Student Avg: {nota_general_str}"
        )
        pdf.cell(pdf.epw - 8, 7, text=clean_pdf_text(resumen_notas_txt), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_y(y_perf + 17)
    except Exception:
        pass
# ==============================================================================
# PARTE 6B: CUERPO, ILUSTRACIÓN, EXAMEN Y REPORTE ORAL EN PDF (create_lesson_pdf)
# ==============================================================================
    img_to_embed = st.session_state.get("image_bytes")
    if img_to_embed:
        try:
            img_buf = io.BytesIO(img_to_embed)
            img_w = 136
            img_h = 76.5
            x_img = pdf.l_margin + (pdf.epw - img_w) / 2
            y_img = pdf.get_y()
            if y_img + img_h + 10 > pdf.h - 22:
                pdf.add_page()
                y_img = pdf.get_y()
            pdf.image(img_buf, x=x_img, y=y_img, w=img_w, h=img_h)
            pdf.set_draw_color(11, 37, 69)
            pdf.set_line_width(0.5)
            pdf.rect(x_img, y_img, img_w, img_h)
            pdf.set_y(y_img + img_h + 2)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Times", "I", 8.5)
            pdf.set_text_color(90, 90, 90)
            pdf.cell(pdf.epw, 4, text=clean_pdf_text(f"Figure 1. Visual Discourse Context & Situational Dialogue - Folio {folio_doc}."), new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(4)
        except Exception:
            pdf.ln(3)

    pdf.set_text_color(25, 25, 25)
    for parrafo in str(text or "").split("\n"):
        p_clean = parrafo.strip()
        if not p_clean:
            pdf.ln(3)
            continue
        pdf.set_x(pdf.l_margin)
        if p_clean.startswith("#") or p_clean.startswith("Bibliography"):
            titulo_limpio = p_clean.lstrip("#").strip()
            pdf.ln(2)
            pdf.set_font("Times", "B", 12)
            pdf.set_text_color(11, 37, 69)
            pdf.multi_cell(pdf.epw, 6.5, text=clean_pdf_text(titulo_limpio), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")
            pdf.set_text_color(25, 25, 25)
        else:
            pdf.set_font("Times", size=11)
            pdf.multi_cell(pdf.epw, 6.2, text=clean_pdf_text(p_clean), new_x="LMARGIN", new_y="NEXT", align="J", wrapmode="CHAR")

    if quiz_items:
        pdf.ln(6)
        if pdf.get_y() > pdf.h - 55:
            pdf.add_page()

        y_q_head = pdf.get_y()
        pdf.set_fill_color(11, 37, 69)
        pdf.rect(pdf.l_margin, y_q_head, pdf.epw, 9, style="F")
        pdf.set_xy(pdf.l_margin + 3, y_q_head + 1.5)
        pdf.set_font("Times", "B", 11)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(pdf.epw - 6, 6, text=clean_pdf_text(f"OFFICIAL ASSESSMENT & GRAMMAR EVALUATION  |  FOLIO: {folio_doc}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        if score:
            y_sc = pdf.get_y()
            pdf.set_fill_color(253, 248, 232)
            pdf.set_draw_color(184, 134, 11)
            pdf.rect(pdf.l_margin, y_sc, pdf.epw, 8, style="FD")
            pdf.set_xy(pdf.l_margin + 3, y_sc + 1.5)
            pdf.set_font("Times", "B", 10.5)
            pdf.set_text_color(11, 37, 69)
            pdf.cell(pdf.epw - 6, 5, text=clean_pdf_text(f"FINAL EVALUATION SCORE / CALIFICACION OBTENIDA: {score}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        pdf.set_text_color(25, 25, 25)
        for i, q in enumerate(quiz_items):
            if pdf.get_y() > pdf.h - 45:
                pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Times", "B", 10.5)
            pdf.multi_cell(pdf.epw, 6, text=clean_pdf_text(f"{i+1}. {q.get('question', '')}"), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")

            pdf.set_font("Times", size=10)
            for opt in q.get("options", []):
                pdf.set_x(pdf.l_margin + 6)
                pdf.multi_cell(pdf.epw - 6, 5.2, text=clean_pdf_text(str(opt)), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")

            u_choice = (user_ans.get(i) or user_ans.get(str(i))) if isinstance(user_ans, dict) else "None"
            ans_line = f"Candidate Response: {u_choice or 'None'}   |   Verified Key: {q.get('answer', '')}"
            pdf.set_x(pdf.l_margin + 6)
            pdf.set_font("Times", "I", 9.5)
            pdf.set_text_color(11, 37, 69)
            pdf.multi_cell(pdf.epw - 6, 5.5, text=clean_pdf_text(ans_line), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")
            pdf.set_text_color(25, 25, 25)
            pdf.ln(3)

    if speaking_eval and isinstance(speaking_eval, dict):
        pdf.ln(6)
        if pdf.get_y() > pdf.h - 65:
            pdf.add_page()

        y_sp_head = pdf.get_y()
        pdf.set_fill_color(11, 37, 69)
        pdf.rect(pdf.l_margin, y_sp_head, pdf.epw, 9, style="F")
        pdf.set_xy(pdf.l_margin + 3, y_sp_head + 1.5)
        pdf.set_font("Times", "B", 11)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(pdf.epw - 6, 6, text=clean_pdf_text(f"ORAL PROFICIENCY & PHONETIC ASSESSMENT REPORT  |  FOLIO: {folio_doc}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        y_sp_sc = pdf.get_y()
        pdf.set_fill_color(253, 248, 232)
        pdf.set_draw_color(184, 134, 11)
        pdf.rect(pdf.l_margin, y_sp_sc, pdf.epw, 8, style="FD")
        pdf.set_xy(pdf.l_margin + 3, y_sp_sc + 1.5)
        pdf.set_font("Times", "B", 10.5)
        pdf.set_text_color(11, 37, 69)
        spk_pct = speaking_eval.get("score_percent", 0)
        spk_perf = speaking_eval.get("cefr_performance", "")
        pdf.cell(pdf.epw - 6, 5, text=clean_pdf_text(f"SPEAKING SCORE: {spk_pct}%  |  CEFR BENCHMARK: {spk_perf}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        pdf.set_text_color(25, 25, 25)
        campos_orales = [
            ("Detected Speech Transcription:", f"\"{speaking_eval.get('transcription', '')}\""),
            ("Phonetics & Articulation Feedback:", speaking_eval.get("phonetic_feedback", "")),
            ("Fluency & Prosody:", speaking_eval.get("fluency_prosody", "")),
            ("Oral Grammar Accuracy:", speaking_eval.get("grammar_accuracy", ""))
        ]

        for etiqueta, contenido in campos_orales:
            if not str(contenido).strip():
                continue
            if pdf.get_y() > pdf.h - 30:
                pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Times", "B", 10)
            pdf.set_text_color(11, 37, 69)
            pdf.cell(pdf.epw, 5.5, text=clean_pdf_text(etiqueta), new_x="LMARGIN", new_y="NEXT")

            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Times", "I" if "Transcription" in etiqueta else "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(pdf.epw - 4, 5.5, text=clean_pdf_text(contenido), new_x="LMARGIN", new_y="NEXT", align="J", wrapmode="CHAR")
            pdf.ln(2)

        tips_orales = speaking_eval.get("actionable_tips", [])
        if tips_orales:
            if pdf.get_y() > pdf.h - 30:
                pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Times", "B", 10)
            pdf.set_text_color(11, 37, 69)
            pdf.cell(pdf.epw, 5.5, text="Pedagogical Actionable Recommendations:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Times", size=9.8)
            pdf.set_text_color(30, 30, 30)
            for tip in tips_orales:
                pdf.set_x(pdf.l_margin + 6)
                pdf.multi_cell(pdf.epw - 6, 5.2, text=clean_pdf_text(f"- {tip}"), new_x="LMARGIN", new_y="NEXT", align="J", wrapmode="CHAR")
            pdf.ln(3)

    return bytes(pdf.output())
# ==============================================================================
# PARTE 7A: GENERADOR DE BOLETÍN OFICIAL EN PDF (APA 7a ED. + TIMBRE HMAC)
# ==============================================================================
def create_official_gradebook_pdf(student_name: str, gb_data: dict, topic_filter: str = "Vista General") -> tuple[bytes, dict]:
    timbre = stamp_and_save_transcript_pg(student_name, gb_data, topic_filter)
    folio_bol = timbre["folio_boletin"]
    fecha_gen = timbre["fecha_generacion"]
    sello_hmac = timbre["sello_hmac"]

    app_base_url = str(st.secrets.get("APP_PUBLIC_URL") or st.secrets.get("APP_BASE_URL") or "").strip().rstrip("/")
    verify_url = f"{app_base_url}/?verify_transcript={urllib.parse.quote(folio_bol)}" if app_base_url else f"/?verify_transcript={urllib.parse.quote(folio_bol)}"

    qr_buf = io.BytesIO()
    qrcode.make(verify_url).save(qr_buf, format="PNG")
    qr_buf.seek(0)

    logo_src = None
    perm_logo = load_permanent_logo()
    if perm_logo and perm_logo.get("Logo_Base64"):
        try:
            logo_src = io.BytesIO(base64.b64decode(perm_logo["Logo_Base64"]))
        except Exception:
            logo_src = None
    if logo_src is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_logo = os.path.join(base_dir, "LOGO CEI APP.png")
        if os.path.exists(local_logo):
            logo_src = local_logo

    addr_doc = st.session_state.get("institute_address") or DEFAULT_ADDRESS

    class GradebookPDF(FPDF):
        def header(self):
            self.set_fill_color(246, 248, 252)
            self.set_draw_color(26, 42, 68)
            self.set_line_width(0.7)
            self.rect(12, 10, 186, 28, style="FD")

            if logo_src:
                try:
                    if isinstance(logo_src, io.BytesIO):
                        logo_src.seek(0)
                    self.image(logo_src, x=15, y=13, w=22)
                except Exception:
                    pass

            self.set_xy(38, 13)
            self.set_font("Times", "B", 13.5)
            self.set_text_color(26, 42, 68)
            self.cell(154, 6, "CAREER ENGLISH INSTITUTE", new_x="LMARGIN", new_y="NEXT", align="C")

            self.set_x(38)
            self.set_font("Times", "I", 9.5)
            self.set_text_color(60, 60, 60)
            self.cell(154, 5, "Official Stamped Academic Transcript & CEFR Applied Grammar Report", new_x="LMARGIN", new_y="NEXT", align="C")

            self.set_x(38)
            self.set_font("Times", "B", 8.5)
            self.set_text_color(150, 110, 20)
            self.cell(154, 5, "APA 7th Edition Academic Standard  |  Author: Jacob Zumaya Prianti", new_x="LMARGIN", new_y="NEXT", align="C")
            self.set_y(42)

        def footer(self):
            self.set_y(-16)
            self.set_draw_color(180, 180, 180)
            self.line(12, self.get_y(), 198, self.get_y())
            self.ln(1.5)
            self.set_font("Times", "I", 8)
            self.set_text_color(90, 90, 90)
            self.set_x(12)
            self.cell(186, 4, clean_pdf_text(f"© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti | APA 7th Ed. Standard | Page {self.page_no()}"), new_x="LMARGIN", new_y="NEXT", align="C")
            self.set_x(12)
            self.cell(186, 4, clean_pdf_text(addr_doc), new_x="LMARGIN", new_y="NEXT", align="C")

    pdf = GradebookPDF()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    pdf.set_font("Times", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 7, clean_pdf_text(f"OFFICIAL ACADEMIC TRANSCRIPT: {student_name.upper()}"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Times", "B", 9.5)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(0, 5, clean_pdf_text(f"Transcript Folio: {folio_bol}   |   Generation Date: {fecha_gen}"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Times", "I", 9.5)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 5, clean_pdf_text(f"Registration ID: {gb_data.get('matricula')}  |  CEFR Level: {gb_data.get('nivel_cefr')}  |  View: {topic_filter}"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)

    pdf.set_fill_color(242, 245, 250)
    pdf.set_draw_color(26, 42, 68)
    pdf.rect(12, pdf.get_y(), 186, 15, style="DF")
    y_box = pdf.get_y() + 3.5
    pdf.set_xy(15, y_box)
    pdf.set_font("Times", "B", 10.5)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(46, 8, f"Overall Avg: {gb_data['overall_avg']}%", align="C")
    pdf.cell(46, 8, f"Written (Quiz): {gb_data['quiz_avg']}%", align="C")
    pdf.cell(46, 8, f"Oral (Speaking): {gb_data['oral_avg']}%", align="C")
    pdf.cell(44, 8, f"Total Lessons: {len(gb_data['records'])}", align="C")
    pdf.ln(15)

    pdf.set_font("Times", "B", 11)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 6, "Table 1", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "I", 10.5)
    pdf.cell(0, 6, clean_pdf_text(f"Applied Grammar Competency Breakdown by CEFR {gb_data.get('nivel_cefr')} Topic"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Times", "B", 9.5)
    pdf.set_draw_color(20, 20, 20)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.cell(124, 7, "Grammar Topic", align="L")
    pdf.cell(18, 7, "Lessons", align="C")
    pdf.cell(22, 7, "Mastery", align="C")
    pdf.cell(22, 7, "Status", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())

    pdf.set_font("Times", "", 9.2)
    temas_pdf = gb_data.get("topic_summary", [])
    if topic_filter != "Vista General":
        temas_pdf = [t for t in temas_pdf if t["Grammar Topic"] == topic_filter]

    for t_row in temas_pdf:
        pdf.cell(124, 6.2, clean_pdf_text(t_row["Grammar Topic"])[:68], align="L")
        pdf.cell(18, 6.2, str(t_row["Lecciones"]), align="C")
        pdf.cell(22, 6.2, f"{t_row['Dominio (%)']}%", align="C")
        pdf.cell(22, 6.2, clean_pdf_text(t_row["Estatus"]), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Times", "B", 11)
    pdf.cell(0, 6, "Table 2", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "I", 10.5)
    pdf.cell(0, 6, "Chronological Archive of Assessed Lessons and Folios", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Times", "B", 9)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.cell(38, 7, "Folio", align="L")
    pdf.cell(82, 7, "Grammar Topic", align="L")
    pdf.cell(22, 7, "Quiz", align="C")
    pdf.cell(22, 7, "Oral", align="C")
    pdf.cell(22, 7, "Lesson Avg", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())

    pdf.set_font("Times", "", 8.8)
    recs_pdf = gb_data.get("records", [])
    if topic_filter != "Vista General":
        recs_pdf = [r for r in recs_pdf if r["Grammar_Topic"] == topic_filter]

    for r_item in recs_pdf:
        pdf.cell(38, 6, clean_pdf_text(r_item["Folio"]), align="L")
        pdf.cell(82, 6, clean_pdf_text(r_item["Grammar_Topic"])[:55], align="L")
        pdf.cell(22, 6, clean_pdf_text(r_item["Quiz_Pct"]), align="C")
        pdf.cell(22, 6, clean_pdf_text(r_item["Oral_Pct"]), align="C")
        pdf.cell(22, 6, clean_pdf_text(r_item["Promedio_Leccion"]), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(6)

    if pdf.get_y() > 235:
        pdf.add_page()
    y_seal = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(26, 42, 68)
    pdf.rect(12, y_seal, 186, 30, style="DF")

    pdf.image(qr_buf, x=15, y=y_seal + 2.5, w=25)
    pdf.set_xy(43, y_seal + 3)
    pdf.set_font("Times", "B", 9.5)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(152, 5, clean_pdf_text(f"DIGITAL INSTITUTIONAL STAMP (HMAC-SHA256)  |  FOLIO: {folio_bol}"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(43)
    pdf.set_font("Courier", "", 7.0)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(152, 3.5, clean_pdf_text(f"SHA-256 SEAL: {sello_hmac}\nISSUED AT: {fecha_gen}"))
    pdf.set_x(43)
    pdf.set_font("Courier", "", 6.2)
    pdf.cell(152, 3.5, clean_pdf_text(f"VERIFY: {verify_url}"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(43, y_seal + 22)
    pdf.set_font("Times", "B", 8.5)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(152, 5, clean_pdf_text("Signed digitally by: Jacob Zumaya Prianti - Academic Director, Career English Institute"), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output()), timbre
# ==============================================================================
# PARTE 7B1: GENERADOR DE CERTIFICADO OFICIAL EN PDF (CARTA HORIZONTAL)
# ==============================================================================
def generar_pdf_certificado(
    folio_c: str,
    clave_alumno: str,
    titular: str,
    nivel_cefr: str,
    programa: str,
    calificacion: str,
    fecha_c: str,
    cadena_original: str,
    sello_hmac: str,
    direccion_inst: str
) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    pdf.set_draw_color(26, 42, 68)
    pdf.set_line_width(1.6)
    pdf.rect(10, 10, 259.4, 195.9)
    pdf.set_draw_color(184, 142, 67)
    pdf.set_line_width(0.6)
    pdf.rect(13, 13, 253.4, 189.9)

    logo_src = None
    cfg_logo = load_permanent_logo()
    if cfg_logo and cfg_logo.get("Logo_Base64"):
        try:
            logo_src = io.BytesIO(base64.b64decode(cfg_logo["Logo_Base64"]))
        except Exception:
            logo_src = None
    if logo_src is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_logo = os.path.join(base_dir, "LOGO CEI APP.png")
        if os.path.exists(local_logo):
            logo_src = local_logo

    if logo_src:
        try:
            pdf.image(logo_src, x=127.2, y=16, w=25)
            pdf.set_y(44)
        except Exception:
            pdf.set_y(24)
    else:
        pdf.set_y(24)

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(0, 9, clean_pdf_text("CAREER ENGLISH INSTITUTE"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(0, 6, clean_pdf_text("Official Academic Certification & Linguistic Proficiency Authority"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(184, 142, 67)
    pdf.cell(0, 8, clean_pdf_text("CERTIFICATE OF ACADEMIC ACHIEVEMENT"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 55, 65)
    pdf.cell(0, 6, clean_pdf_text("This official credential is proudly conferred upon:"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 12, clean_pdf_text(titular.upper()), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_draw_color(184, 142, 67)
    pdf.set_line_width(0.5)
    pdf.line(65, pdf.get_y(), 214.4, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(45, 50, 60)
    pdf.cell(0, 6, clean_pdf_text(f"Student ID: {clave_alumno}   |   Accredited CEFR Level: {nivel_cefr}"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(0, 7, clean_pdf_text(programa), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(35, 115, 70)
    pdf.cell(0, 6, clean_pdf_text(f"Final Evaluation & Standing: {calificacion}"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(148)
    pdf.set_draw_color(40, 45, 55)
    pdf.line(100, 148, 179.4, 148)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(0, 5, clean_pdf_text("Jacob Zumaya Prianti"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 95, 105)
    pdf.cell(0, 4, clean_pdf_text("Academic Director & Principal Author - Career English Institute"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    verify_link = _build_cert_verify_url(folio_c)
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(verify_link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1a2a44", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    pdf.image(qr_buf, x=18, y=161, w=28)

    pdf.set_xy(49, 162)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(0, 4, clean_pdf_text(f"OFFICIAL CERTIFICATE FOLIO: {folio_c}   |   ISSUED: {fecha_c}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(49)
    pdf.set_font("Courier", "", 6.3)
    pdf.set_text_color(70, 75, 85)
    pdf.multi_cell(210, 3.1, clean_pdf_text(f"ORIGINAL STRING: {cadena_original}\nHMAC-SHA256 DIGITAL SIGNATURE: {sello_hmac}"))

    pdf.set_xy(49, max(pdf.get_y() + 1.0, 180))
    pdf.set_font("Helvetica", "I", 6.8)
    pdf.set_text_color(100, 105, 115)
    pdf.multi_cell(
        212,
        3.2,
        clean_pdf_text(f"Scan QR code or visit {verify_link} to verify authenticity.\n{direccion_inst}")
    )

    return bytes(pdf.output())
# ==============================================================================
# PARTE 7B2: MOTORES DE IA CON GEMINI (TEXTO, QUIZ, PRONUNCIACIÓN E IMAGEN)
# ==============================================================================
def generar_con_maxima_potencia(client_obj, prompt_contenido: str, instruccion_sistema: str = None, as_json: bool = False):
    gm = client_obj or init_gemini_client()
    if not gm:
        raise RuntimeError("Cliente Gemini no inicializado. Verifica GEMINI_API_KEY en Secrets.")

    modelos_preferidos = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.1-pro-preview",
        "gemini-2.0-flash"
    ]
    excluidos = ("embedding", "imagen", "tts", "audio", "robotics", "computer-use", "lyria")
    try:
        for m in gm.models.list():
            m_name = str(getattr(m, "name", "")).replace("models/", "").strip()
            metodos = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or []
            if "gemini" in m_name and not any(ex in m_name for ex in excluidos):
                if not metodos or "generateContent" in metodos:
                    if m_name not in modelos_preferidos:
                        modelos_preferidos.append(m_name)
    except Exception:
        pass

    ultimo_error = None
    for modelo in modelos_preferidos:
        try:
            cfg_kwargs = {"temperature": 0.65}
            if instruccion_sistema:
                cfg_kwargs["system_instruction"] = instruccion_sistema
            if as_json:
                cfg_kwargs["response_mime_type"] = "application/json"
            config = types.GenerateContentConfig(**cfg_kwargs)
            respuesta = gm.models.generate_content(
                model=modelo,
                contents=prompt_contenido,
                config=config
            )
            if respuesta and respuesta.text:
                return respuesta.text, modelo
        except Exception as e:
            ultimo_error = e
            continue

    if ultimo_error:
        raise ultimo_error
    raise RuntimeError("No se obtuvo respuesta válida de los modelos Gemini.")

def generar_quiz_leccion(texto_leccion: str, tema_gramatical: str, nivel_cefr: str, grado_acad: str, evitar_preguntas=None, client_obj=None):
    gm = client_obj or init_gemini_client()
    evitar_txt = ("IMPORTANT: Create COMPLETELY DIFFERENT questions from: " + str(evitar_preguntas) + "\n") if evitar_preguntas else ""
    prompt_quiz = (
        f"Based on this CEFR Level {nivel_cefr} English lesson tailored for {grado_acad} students, "
        f"create a 5-question multiple-choice quiz in English calibrated strictly to level {nivel_cefr} and {grado_acad} cognitive level, "
        f"evaluating comprehension and target grammar ({tema_gramatical}).\n"
        f"{evitar_txt}"
        f"LESSON TEXT:\n{texto_leccion}\n"
        "RETURN ONLY A VALID JSON ARRAY WITH THIS EXACT SCHEMA:\n"
        '[{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A) ..."}]'
    )
    raw_resp, _ = generar_con_maxima_potencia(
        gm,
        prompt_quiz,
        instruccion_sistema="Output strictly a valid JSON array only.",
        as_json=True
    )
    cleaned = raw_resp.strip()
    if cleaned.startswith("```"):
        cleaned = next(iter(cleaned.split("\n", 1)[-1].rsplit("```", 1)), "")
    return json.loads(cleaned.strip())

def evaluar_pronunciacion_ia(audio_bytes: bytes, mime_type: str, texto_objetivo: str, gramatica_obj: str, nivel_cefr: str, grado_acad: str) -> dict:
    gm_client = init_gemini_client()
    if not gm_client:
        raise RuntimeError("Cliente Gemini no inicializado. Verifica GEMINI_API_KEY en Secrets.")

    prompt_eval = f"""
    Listen carefully to the student's audio reading the target lesson below (CEFR {nivel_cefr}, Academic Level: {grado_acad}, Target Grammar: {gramatica_obj}).

    Target text:
    {texto_objetivo[:2500]}

    Evaluate pronunciation, articulation, fluency, prosody, and grammatical accuracy.
    Respond in Spanish for the feedback fields, keeping the detected transcription in English.
    Return ONLY a valid JSON object with these exact keys:
    {{
      "score_percent": 88,
      "cefr_performance": "B1 Solid / Proficient",
      "transcription": "Exact English words spoken by the student",
      "phonetic_feedback": "Análisis claro en español sobre pronunciación de vocales, consonantes y acentuación.",
      "fluency_prosody": "Evaluación en español de ritmo, pausas y entonación natural.",
      "grammar_accuracy": "Evaluación en español sobre la correcta pronunciación y uso de las estructuras objetivo.",
      "actionable_tips": [
        "Consejo práctico 1 con ejemplos de palabras del texto",
        "Consejo práctico 2"
      ]
    }}
    """

    ultimo_error = ""
    for modelo_oral in ["gemini-3.1-pro-preview", "gemini-2.5-flash"]:
        try:
            response = gm_client.models.generate_content(
                model=modelo_oral,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    prompt_eval
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            raw_json = str(response.text or "").strip()
            raw_json = raw_json.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(raw_json)
        except Exception as e_mod:
            ultimo_error = f"{modelo_oral}: {e_mod}"

    raise RuntimeError(f"No se pudo completar el análisis fonético: {ultimo_error}")

try:
    from media_generator import generar_imagen_garantizada
except ImportError:
    def generar_imagen_garantizada(*args, **kwargs):
        return None
# ==============================================================================
# PARTE 8A: MOTOR LEXICOGRÁFICO HÍBRIDO Y NORMALIZADOR APA 7a EDICIÓN
# ==============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def analyze_lesson_for_study_mode(lesson_text: str, cefr_level: str, cache_version: str = "v16_fixed_dict") -> dict:
    texto_sin_bib = str(lesson_text or "")
    for marcador in ["**Bibliography", "Bibliography ("]:
        if marcador in texto_sin_bib:
            texto_sin_bib = next(iter(texto_sin_bib.split(marcador, 1)), texto_sin_bib)

    lineas_limpias = []
    for linea in texto_sin_bib.splitlines():
        l_strip = linea.strip()
        if not l_strip:
            continue
        if re.match(r"^\*\*(Folio|Creation Date|Author|Institution|CEFR Level|Academic Level|Campus & Contact):", l_strip, flags=re.IGNORECASE):
            continue
        lineas_limpias.append(l_strip)

    conjunciones = {
        "and", "but", "or", "so", "because", "although", "while", "if",
        "when", "since", "unless", "whereas", "however", "therefore", "yet", "nor"
    }
    oraciones_base = []
    palabras_clave = []
    vistas = set()

    for idx_linea, bloque in enumerate(lineas_limpias):
        sub_oraciones = [bloque] if idx_linea == 0 else re.split(r"(?<=[.!?])\s+", bloque)
        for orac in sub_oraciones:
            orac_limpia = orac.replace("**", "").replace("#", "").strip()
            if not orac_limpia:
                continue
            tokens_raw = re.findall(r"[A-Za-z0-9'-]+|[^\w\s]", orac_limpia)
            toks = []
            for tk in tokens_raw:
                low = tk.lower()
                if low in conjunciones:
                    pos = "conjunction"
                elif low.endswith(("ing", "ed")) and len(low) > 4:
                    pos = "verb"
                elif low.endswith(("ous", "ful", "able", "ible", "al", "ive", "ic", "ly")) and len(low) > 4:
                    pos = "adjective"
                elif len(low) > 3 and low.isalpha():
                    pos = "noun"
                else:
                    pos = "other"
                toks.append({"w": tk, "pos": pos})

                if low.isalpha() and len(low) >= 2 and low not in vistas:
                    vistas.add(low)
                    palabras_clave.append(low)
            oraciones_base.append({"sentence_es": "", "tokens": toks})

    dict_final = {}

    if palabras_clave:
        try:
            with pg_session() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cei_lexicon_cache (
                        word_en TEXT PRIMARY KEY,
                        es TEXT NOT NULL,
                        alt_es TEXT DEFAULT '',
                        ipa TEXT DEFAULT '',
                        pos TEXT DEFAULT 'other',
                        pos_es TEXT DEFAULT 'Inglés (US)',
                        def_es TEXT DEFAULT ''
                    );
                """)
                cur.execute(
                    "SELECT word_en, es, alt_es, ipa, pos, pos_es, def_es FROM cei_lexicon_cache WHERE word_en = ANY(%s);",
                    (palabras_clave[:300],)
                )
                for row in cur.fetchall():
                    w_key = str(row[0]).lower().strip()
                    dict_final[w_key] = {
                        "es": row[1] or "",
                        "alt_es": row[2] or "",
                        "ipa": row[3] or "",
                        "pos": row[4] or "other",
                        "pos_es": row[5] or "Inglés (US)",
                        "def_es": row[6] or "",
                        "examples": []
                    }
        except Exception:
            pass

    faltantes = [w for w in palabras_clave[:300] if w not in dict_final]
    nuevas_para_guardar = []

    if faltantes:
        try:
            traductor = GoogleTranslator(source="en", target="es")
            bloque_es = traductor.translate("\n".join(faltantes))
            lista_tr = [x.strip() for x in str(bloque_es or "").splitlines()]
            if len(lista_tr) != len(faltantes):
                lista_tr = traductor.translate_batch(faltantes)

            for w_orig, w_es in zip(faltantes, lista_tr):
                tr_limpia = str(w_es or w_orig).strip()
                ipa_val = ""
                def_val = ""
                pos_code = "other"
                pos_label = "Vocabulario Inglés (US)"

                if len(nuevas_para_guardar) < 35 and len(w_orig) > 3:
                    try:
                        r_fd = requests.get(f"https://dictionaryapi.dev{urllib.parse.quote(w_orig)}", timeout=2.5)
                        if r_fd.status_code == 200:
                            jd_list = r_fd.json()
                            if isinstance(jd_list, list) and jd_list:
                                jd = jd_list[0]
                                ipa_val = str(jd.get("phonetic") or "").strip()
                                if not ipa_val:
                                    for ph in jd.get("phonetics", []):
                                        if isinstance(ph, dict) and ph.get("text"):
                                            ipa_val = str(ph["text"]).strip()
                                            break
                                meanings = jd.get("meanings", [])
                                if isinstance(meanings, list) and meanings:
                                    first_m = meanings[0]
                                    pos_en = str(first_m.get("partOfSpeech", "")).lower()
                                    mapa_pos = {
                                        "verb": ("verb", "Verbo"),
                                        "noun": ("noun", "Sustantivo"),
                                        "adjective": ("adjective", "Adjetivo"),
                                        "conjunction": ("conjunction", "Conjunción"),
                                        "adverb": ("other", "Adverbio"),
                                        "preposition": ("other", "Preposición")
                                    }
                                    pos_code, pos_label = mapa_pos.get(pos_en, ("other", pos_en.capitalize() or "Inglés (US)"))
                                    defs = first_m.get("definitions", [])
                                    if isinstance(defs, list) and defs and isinstance(defs[0], dict) and defs[0].get("definition"):
                                        def_val = str(traductor.translate(str(defs[0]["definition"])[:160]) or "").strip()
                    except Exception:
                        pass

                entry = {
                    "es": tr_limpia,
                    "alt_es": "",
                    "ipa": ipa_val,
                    "pos": pos_code,
                    "pos_es": pos_label,
                    "def_es": def_val,
                    "examples": []
                }
                dict_final[w_orig] = entry
                nuevas_para_guardar.append((w_orig, tr_limpia, "", ipa_val, pos_code, pos_label, def_val))
        except Exception:
            pass

    if nuevas_para_guardar:
        try:
            with pg_session() as cur:
                for item in nuevas_para_guardar:
                    cur.execute("""
                        INSERT INTO cei_lexicon_cache (word_en, es, alt_es, ipa, pos, pos_es, def_es)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (word_en) DO UPDATE SET
                            es = EXCLUDED.es,
                            ipa = COALESCE(NULLIF(EXCLUDED.ipa, ''), cei_lexicon_cache.ipa),
                            pos = EXCLUDED.pos,
                            pos_es = EXCLUDED.pos_es,
                            def_es = COALESCE(NULLIF(EXCLUDED.def_es, ''), cei_lexicon_cache.def_es);
                    """, item)
        except Exception:
            pass

    for s_obj in oraciones_base:
        for tk in s_obj["tokens"]:
            info_w = dict_final.get(tk["w"].lower())
            if isinstance(info_w, dict) and info_w.get("pos") in ["verb", "noun", "adjective", "conjunction", "other"]:
                tk["pos"] = info_w["pos"]

    return {"sentences": oraciones_base, "dictionary": dict_final}

@st.cache_data(ttl=86400, show_spinner=False)
def _fast_translate_to_en(txt: str) -> str:
    clean_t = str(txt or "").strip()
    if not clean_t:
        return ""
    try:
        tr = GoogleTranslator(source="auto", target="en").translate(clean_t)
        return str(tr or clean_t).strip()
    except Exception:
        return clean_t

@st.cache_data(ttl=86400, show_spinner=False)
def _fast_translate_to_es(txt: str) -> str:
    clean_t = str(txt or "").strip()
    if not clean_t:
        return ""
    try:
        tr = GoogleTranslator(source="en", target="es").translate(clean_t)
        return str(tr or clean_t).strip()
    except Exception:
        return clean_t

def normalizar_entradas_apa(client_obj, contexto_raw: str, personas_raw: str, asunto_raw: str) -> tuple[str, str, str]:
    ctx_en = _fast_translate_to_en(contexto_raw) or str(contexto_raw or "").strip()
    per_en = _fast_translate_to_en(personas_raw) or str(personas_raw or "").strip()
    asu_en = _fast_translate_to_en(asunto_raw) or str(asunto_raw or "").strip()

    palabras_menores = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "in", "of", "with"}
    palabras = asu_en.split()
    asu_apa = " ".join(
        w.capitalize() if (i == 0 or i == len(palabras) - 1 or w.lower() not in palabras_menores) else w.lower()
        for i, w in enumerate(palabras)
    ) if palabras else "Academic English Discourse"

    return ctx_en, per_en, asu_apa
# ==============================================================================
# PARTE 8B: VISOR INTERACTIVO DE ESTUDIO — BOTONES NATIVOS REALES (MAC + MÓVIL)
# ==============================================================================
@st.cache_data(show_spinner=False, max_entries=500)
def _synthesize_word_mp3(word_clean: str, slow_mode: bool = False) -> bytes | None:
    """Genera y cachea en memoria la pronunciación MP3 nativa (US) de una palabra."""
    if not word_clean:
        return None
    try:
        tts = gTTS(text=word_clean, lang="en", tld="com", slow=slow_mode)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


def render_interactive_study_viewer(study_payload: dict):
    """Visor interactivo con botones nativos de Streamlit por palabra: 1 clic = Voz US + Diccionario."""
    if not study_payload or not study_payload.get("sentences"):
        st.warning("No se pudo estructurar el modo estudio para este texto.")
        return

    sentences = study_payload.get("sentences", [])
    dictionary = study_payload.get("dictionary", {})

    # 1. Leyenda de colores y control de velocidad
    col_leg, col_spd = st.columns([2.8, 1.0])
    with col_leg:
        st.markdown(
            """
            <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;background:#fff;padding:9px 12px;border-radius:10px;border:1px solid #cbd5e1;font-size:12px;font-weight:700;">
                <span style="background:#fee2e2;color:#991b1b;padding:2px 7px;border-radius:5px;border-bottom:2px solid #ef4444;">🔴 Verbo</span>
                <span style="background:#dbeafe;color:#1e40af;padding:2px 7px;border-radius:5px;border-bottom:2px solid #3b82f6;">🔵 Sustantivo</span>
                <span style="background:#dcfce7;color:#166534;padding:2px 7px;border-radius:5px;border-bottom:2px solid #22c55e;">🟢 Adjetivo</span>
                <span style="background:#fef3c7;color:#92400e;padding:2px 7px;border-radius:5px;border-bottom:2px solid #f59e0b;">🟡 Conjunción</span>
                <span style="background:#f1f5f9;color:#334155;padding:2px 7px;border-radius:5px;">⚪ Otro</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_spd:
        velocidad_lenta = st.toggle("🐢 Voz Lenta", value=False, key="study_native_slow_tgl")

    active_w = str(st.session_state.get("active_study_word", "")).strip()
    active_p = str(st.session_state.get("active_study_pos", "other")).strip().lower()
    active_s = str(st.session_state.get("active_study_sentence", "")).strip()

    # 2. Tarjeta de Audio y Diccionario (aparece arriba en cuanto pulsas cualquier palabra)
    if active_w:
        k_low = active_w.lower()
        info_dic = dictionary.get(k_low)
        if not info_dic:
            for stem in (
                re.sub(r"ed$", "", k_low),
                re.sub(r"ed$", "e", k_low),
                re.sub(r"ing$", "", k_low),
                re.sub(r"ing$", "e", k_low),
                re.sub(r"ies$", "y", k_low),
                re.sub(r"s$", "", k_low),
            ):
                if len(stem) > 2 and stem in dictionary:
                    info_dic = dictionary[stem]
                    break
        info_dic = info_dic or {}

        pos_es_map = {
            "verb": "Verbo (Verb)",
            "noun": "Sustantivo (Noun)",
            "adjective": "Adjetivo (Adjective)",
            "conjunction": "Conjunción (Conjunction)",
            "other": "Preposición / Adverbio / Otro"
        }

        with st.container(border=True):
            h_d1, h_d2 = st.columns([3.2, 1.0])
            with h_d1:
                st.markdown(f"#### 🌐 Diccionario y Pronunciación US: **{active_w}** ➔ **{info_dic.get('es') or active_w}**")
            with h_d2:
                if st.button("✖ Cerrar", key="btn_close_study_card", width="stretch"):
                    st.session_state["active_study_word"] = ""
                    st.rerun()

            c_d1, c_d2 = st.columns([1.2, 1.4])
            with c_d1:
                st.caption(f"**Categoría:** {info_dic.get('pos') or pos_es_map.get(active_p, 'Vocabulario')}")
                if info_dic.get("ipa"):
                    st.markdown(f"**Fonética (IPA):** `{info_dic['ipa']}`")
                mp3_word = _synthesize_word_mp3(active_w, slow_mode=velocidad_lenta)
                if mp3_word:
                    st.audio(mp3_word, format="audio/mp3", autoplay=True)

            with c_d2:
                if info_dic.get("alt"):
                    st.markdown(f"**Sinónimos / Acepciones:** {info_dic['alt']}")
                if info_dic.get("def"):
                    st.info(f"📖 **Definición:** {info_dic['def']}")
                if active_s:
                    st.caption(f"💬 *\"{active_s}\"*")
                q_url = urllib.parse.quote(k_low)
                st.markdown(
                    f"🔗 [WordReference ↗](https://wordreference.com{q_url})  |  "
                    f"[Google Translate ↗](https://google.com{q_url}&op=translate)"
                )

    # 3. Botones Nativos Reales de Palabras agrupados por oración
    pos_dot = {
        "verb": "🔴",
        "noun": "🔵",
        "adjective": "🟢",
        "conjunction": "🟡",
        "other": "⚪"
    }

    st.caption("👆 **Haz clic o toca cualquier botón de palabra** para escuchar su pronunciación (US) y ver su significado:")
    with st.container(height=460, border=True):
        for s_idx, sent in enumerate(sentences):
            tokens = sent.get("tokens", [])
            full_s = str(sent.get("full_sentence", "")).strip()
            valid_tokens = []
            for t_idx, tok in enumerate(tokens):
                w_raw = str(tok.get("w", "")).strip()
                w_clean = re.sub(r"^[^a-zA-Z0-9'-]+|[^a-zA-Z0-9'-]+$", "", w_raw)
                if w_clean:
                    valid_tokens.append((t_idx, w_raw, w_clean, str(tok.get("pos", "other")).lower()))

            if not valid_tokens:
                continue

            # Renderiza en filas de hasta 7 palabras por fila para mantener lectura fluida y táctil
            cols_per_row = 7
            for start_i in range(0, len(valid_tokens), cols_per_row):
                chunk = valid_tokens[start_i:start_i + cols_per_row]
                cols_w = st.columns(cols_per_row)
                for c_i, (t_idx, w_raw, w_clean, pos_k) in enumerate(chunk):
                    is_sel = bool(active_w and w_clean.lower() == active_w.lower())
                    badge = pos_dot.get(pos_k, "⚪")
                    btn_label = f"{badge} {w_raw}"
                    with cols_w[c_i]:
                        if st.button(
                            btn_label,
                            key=f"wbtn_{s_idx}_{t_idx}_{w_clean}",
                            type="primary" if is_sel else "secondary",
                            width="stretch"
                        ):
                            st.session_state["active_study_word"] = w_clean
                            st.session_state["active_study_pos"] = pos_k
                            st.session_state["active_study_sentence"] = full_s
                            st.rerun()

# ==============================================================================
# PARTE 9A: MIGRACIÓN SHEETS -> SUPABASE (PERMISOS, PADRÓN Y FOLIOS)
# ==============================================================================
def migrar_sheets_a_supabase() -> dict:
    resumen = {"permisos": 0, "usuarios": 0, "folios": 0, "certificados": 0, "config": 0}
    book = get_google_workbook()

    with pg_session() as cur:
        try:
            ws_perm = book.worksheet("Matriz_Permisos")
            for r in ws_perm.get_all_records():
                prof = str(r.get("Perfil_Permiso") or r.get("Perfil") or "").strip()
                if not prof:
                    continue
                caps_mig = {c: str(r.get(c, "NO")).upper() == "SI" for c in CAPABILITY_COLS}
                cur.execute("""
                    INSERT INTO roles_permissions (
                        profile_name, generar_leccion, resolver_quiz, grabar_audio,
                        emitir_certificados, gestionar_usuarios, editar_instituto_logo, capabilities_json
                    ) VALUES (%s, TRUE, TRUE, TRUE, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (profile_name) DO UPDATE SET
                        emitir_certificados = EXCLUDED.emitir_certificados,
                        gestionar_usuarios = EXCLUDED.gestionar_usuarios,
                        editar_instituto_logo = EXCLUDED.editar_instituto_logo,
                        capabilities_json = EXCLUDED.capabilities_json,
                        updated_at = NOW();
                """, (
                    prof,
                    caps_mig.get("Emitir_Certificados", False),
                    caps_mig.get("Registrar_Usuarios", caps_mig.get("Gestionar_Usuarios", False)),
                    caps_mig.get("Editar_Instituto_Logo", False),
                    json.dumps(caps_mig)
                ))
                resumen["permisos"] += 1
        except Exception:
            pass

        mapa_user_ids = {}
        ws_pad = book.worksheet("Padron")
        for r in ws_pad.get_all_records():
            u_name = str(r.get("Usuario", "")).strip()
            c_pass = str(r.get("Clave", "")).strip()
            if not u_name or not c_pass:
                continue
            perm_val = str(r.get("Permisos", "Basico")).strip() or "Basico"
            cur.execute("INSERT INTO roles_permissions (profile_name) VALUES (%s) ON CONFLICT DO NOTHING;", (perm_val,))
            cur.execute("""
                INSERT INTO users_padron (usuario, clave_hash, rol, grado_academico, nivel_cefr, permisos, estatus)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (usuario) DO UPDATE SET
                    clave_hash = EXCLUDED.clave_hash,
                    rol = EXCLUDED.rol,
                    grado_academico = EXCLUDED.grado_academico,
                    nivel_cefr = EXCLUDED.nivel_cefr,
                    permisos = EXCLUDED.permisos,
                    estatus = EXCLUDED.estatus
                RETURNING id;
            """, (
                u_name,
                c_pass,
                str(r.get("Rol", "Estudiante")).strip() or "Estudiante",
                str(r.get("Grado_Academico", "Licenciatura / Universidad")).strip() or "Licenciatura / Universidad",
                normalize_cefr(r.get("Nivel", "B1")),
                perm_val,
                "Activo" if str(r.get("Estatus", "Activo")).strip().lower() == "activo" else "Inactivo"
            ))
            row_id = next(iter(cur.fetchone()), None)
            mapa_user_ids[u_name.lower()] = row_id
            resumen["usuarios"] += 1

        ws_h1 = book.sheet1
        for r in ws_h1.get_all_records():
            folio_val = str(r.get("Folio", "")).strip().upper()
            u_folio = str(r.get("Usuario", "")).strip()
            if not folio_val or not u_folio:
                continue
            uid = mapa_user_ids.get(u_folio.lower())
            if not uid:
                cur.execute("""
                    INSERT INTO users_padron (usuario, clave_hash, rol, permisos, estatus)
                    VALUES (%s, 'MIGRATED_LEGACY', 'Estudiante', 'Basico', 'Inactivo')
                    ON CONFLICT (usuario) DO UPDATE SET usuario = EXCLUDED.usuario
                    RETURNING id;
                """, (u_folio,))
                uid = next(iter(cur.fetchone()), None)
                mapa_user_ids[u_folio.lower()] = uid

            raw_j = str(r.get("Contenido_JSON", "")).strip()
            paq = {}
            if raw_j:
                try:
                    paq = json.loads(raw_j)
                except Exception:
                    paq = {}

            texto_lec = paq.get("text", str(r.get("Tema", "")))
            cefr_lec = paq.get("cefr", "B1")
            grado_lec = paq.get("grade", "Licenciatura / Universidad")
            mejor_str = str(r.get("Mejor_Calificacion_PDF", "") or paq.get("best_score", "")).strip()
            mejor_num = _extract_numeric_score(mejor_str)
            spk_str = str(r.get("Mejor_Speaking_Nota", "")).strip()
            spk_num = _extract_numeric_score(spk_str)

            cur.execute("""
                INSERT INTO lessons_folios (
                    folio, user_id, tema, cefr_level, academic_grade, lesson_text,
                    quiz_data, best_quiz_score, best_quiz_numeric, best_quiz_answers,
                    best_speaking_score, pdf_link
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (folio) DO UPDATE SET
                    best_quiz_score = EXCLUDED.best_quiz_score,
                    best_quiz_numeric = GREATEST(lessons_folios.best_quiz_numeric, EXCLUDED.best_quiz_numeric),
                    best_speaking_score = GREATEST(lessons_folios.best_speaking_score, EXCLUDED.best_speaking_score),
                    updated_at = NOW();
            """, (
                folio_val, uid, str(r.get("Tema", "")), cefr_lec, grado_lec, texto_lec,
                json.dumps(paq.get("quiz")) if paq.get("quiz") else None,
                mejor_str or None, mejor_num,
                json.dumps(paq.get("best_answers")) if paq.get("best_answers") else None,
                spk_num, str(r.get("PDF_Link", ""))
            ))
            resumen["folios"] += 1
# ==============================================================================
# PARTE 9B: MIGRACIÓN (CERTIFICADOS / CONFIG) Y AJUSTES GLOBALES DE COBRANZA
# ==============================================================================
        try:
            ws_cert = book.worksheet("Certificados")
            for r in ws_cert.get_all_records():
                f_cert = str(r.get("Folio_Certificado", "")).strip().upper()
                titular_c = str(r.get("Titular") or r.get("Nombre_Estudiante") or "").strip()
                if not f_cert or not titular_c:
                    continue
                uid_c = mapa_user_ids.get(titular_c.lower()) or next(iter(mapa_user_ids.values()), 1)
                cur.execute("""
                    INSERT INTO certificates (
                        folio_cert, user_id, clave_alumno, titular, nivel_cefr,
                        grado_academico, programa, calificacion, fecha_emision,
                        firma_hmac, estatus, verify_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (folio_cert) DO NOTHING;
                """, (
                    f_cert, uid_c, str(r.get("Clave_Alumno", "")), titular_c,
                    str(r.get("Nivel_CEFR", "B1")), str(r.get("Grado_Academico", "")),
                    str(r.get("Programa") or r.get("Programa_Curso") or ""), str(r.get("Calificacion", "")),
                    str(r.get("Fecha_Emision", "")), str(r.get("Firma_HMAC") or r.get("Sello_Digital_SHA256") or ""),
                    "Valido" if str(r.get("Estatus", "Valido")).strip().lower() in ("valido", "vigente") else "Revocado",
                    str(r.get("URL_Verificacion", "")) or _build_cert_verify_url(f_cert)
                ))
                resumen["certificados"] += 1
        except Exception:
            pass

        try:
            ws_cfg = book.worksheet("Config_Logo")
            recs_cfg = ws_cfg.get_all_records()
            if recs_cfg:
                c0 = recs_cfg[0]
                cur.execute("""
                    INSERT INTO institute_config (id, logo_base64, mime_type, logo_width, logo_shape, direccion)
                    VALUES (1, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        logo_base64 = EXCLUDED.logo_base64,
                        mime_type = EXCLUDED.mime_type,
                        logo_width = EXCLUDED.logo_width,
                        logo_shape = EXCLUDED.logo_shape,
                        direccion = EXCLUDED.direccion,
                        updated_at = NOW();
                """, (
                    str(c0.get("Logo_Base64", "")),
                    str(c0.get("Mime_Type", "image/png")),
                    int(c0.get("Ancho") or c0.get("Width") or 115),
                    str(c0.get("Forma") or c0.get("Shape") or "Circular"),
                    str(c0.get("Direccion") or DEFAULT_ADDRESS)
                ))
                resumen["config"] = 1
        except Exception:
            pass

    load_permissions_matrix.clear()
    load_padron_records.clear()
    load_permanent_logo.clear()
    return resumen

def get_billing_global_settings_pg() -> bool:
    try:
        with pg_session() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS billing_global_settings ("
                "id INT PRIMARY KEY DEFAULT 1, "
                "activar_incentivo_recargo BOOLEAN DEFAULT FALSE, "
                "updated_by TEXT, "
                "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());"
            )
            cur.execute("SELECT activar_incentivo_recargo FROM billing_global_settings WHERE id = 1;")
            row = cur.fetchone()
            return bool(next(iter(row), False)) if row else False
    except Exception:
        return False

def set_billing_global_settings_pg(activo: bool, usuario_op: str) -> tuple[bool, str]:
    try:
        with pg_session() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS billing_global_settings ("
                "id INT PRIMARY KEY DEFAULT 1, "
                "activar_incentivo_recargo BOOLEAN DEFAULT FALSE, "
                "updated_by TEXT, "
                "updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());"
            )
            cur.execute(
                "INSERT INTO billing_global_settings (id, activar_incentivo_recargo, updated_by, updated_at) "
                "VALUES (1, %s, %s, NOW()) "
                "ON CONFLICT (id) DO UPDATE "
                "SET activar_incentivo_recargo = EXCLUDED.activar_incentivo_recargo, "
                "updated_by = EXCLUDED.updated_by, updated_at = NOW();",
                (bool(activo), str(usuario_op))
            )
        return True, f"Esquema {'ACTIVADO' if activo else 'DESACTIVADO'} correctamente."
    except Exception as e:
        return False, f"Error en base de datos: {e}"
# ==============================================================================
# PARTE 10A: EVALUACIÓN FINANCIERA INDIVIDUAL (CICLOS DE 28 DÍAS E IVA)
# ==============================================================================
def evaluar_estado_financiero_alumno(student_user: str) -> dict:
    hoy = datetime.now(ZoneInfo("America/Hermosillo")).date()
    reglas_activas = get_billing_global_settings_pg()

    info = {
        "fecha_inicio": hoy,
        "mensualidad_base": 1500.00,
        "aplicar_iva": False,
        "subtotal_ajustado": 1500.00,
        "iva_monto": 0.00,
        "reglas_incentivo_activas": reglas_activas,
        "afiliado_usuario": "",
        "porcentaje_comision": 0.0,
        "ciclo_actual": 1,
        "ciclo_a_cobrar": 1,
        "semana_ciclo": 1,
        "ventana_pago_inicio": hoy,
        "ventana_pago_fin": hoy + timedelta(days=27),
        "ajuste_label": "Tarifa Base (Incentivos/Recargos desactivados)",
        "ajuste_monto": 0.00,
        "monto_a_pagar": 1500.00,
        "ciclo_pagado": False,
        "descarga_permitida": True,
        "dias_retraso": 0,
        "mensaje_estado": "Al corriente"
    }

    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT rol, fecha_inicio_curso, mensualidad_base, aplicar_iva, afiliado_usuario, porcentaje_comision
                FROM users_padron WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) LIMIT 1;
            """, (student_user,))
            u = cur.fetchone()
            if not u:
                return info

            if str(u.get("rol", "")).lower() not in ["estudiante", "student", "alumno"]:
                return info

            f_ini = u.get("fecha_inicio_curso") or hoy
            base = float(u.get("mensualidad_base") or 1500.0)
            con_iva = bool(u.get("aplicar_iva") or False)

            dias_transcurridos = max(0, (hoy - f_ini).days)
            ciclo_vigente = (dias_transcurridos // 28) + 1
            dia_en_ciclo = (dias_transcurridos % 28) + 1
            semana_en_ciclo = ((dia_en_ciclo - 1) // 7) + 1

            cur.execute("""
                SELECT ciclo_numero FROM tuition_payments
                WHERE LOWER(TRIM(student_user)) = LOWER(TRIM(%s)) AND estatus = 'Pagado';
            """, (student_user,))
            ciclos_pagados = {int(r["ciclo_numero"]) for r in cur.fetchall() if r.get("ciclo_numero") is not None}

            ciclos_vencidos = [c for c in range(1, ciclo_vigente) if c not in ciclos_pagados]

            if ciclos_vencidos:
                ciclo_objetivo = next(iter(ciclos_vencidos))
                es_moratorio = True
                esta_pagado = False
            else:
                ciclo_objetivo = ciclo_vigente
                es_moratorio = False
                esta_pagado = ciclo_vigente in ciclos_pagados

            inicio_ciclo_obj = f_ini + timedelta(days=(ciclo_objetivo - 1) * 28)
            fin_sem4_obj = inicio_ciclo_obj + timedelta(days=27)
            dias_retraso_calc = max(0, (hoy - fin_sem4_obj).days) if es_moratorio else 0

            if not reglas_activas:
                ajuste_lbl = "Mensualidad Estándar (Incentivos/Recargos desactivados)"
                ajuste_mto = 0.0
            elif es_moratorio:
                ajuste_lbl = f"Recargo Moratorio Mes {ciclo_objetivo} Vencido (+5%)"
                ajuste_mto = round(base * 0.05, 2)
            else:
                ajuste_lbl = f"Incentivo Pago en Tiempo Sem. {semana_en_ciclo}/4 (-7%)"
                ajuste_mto = round(-base * 0.07, 2)

            subtotal_mes = round(base + ajuste_mto, 2)
            iva_mto = round(subtotal_mes * 0.16, 2) if con_iva else 0.0
            monto_calc = round(subtotal_mes + iva_mto, 2)
            bloqueado = es_moratorio

            info.update({
                "fecha_inicio": f_ini,
                "mensualidad_base": base,
                "aplicar_iva": con_iva,
                "subtotal_ajustado": subtotal_mes,
                "iva_monto": iva_mto,
                "reglas_incentivo_activas": reglas_activas,
                "afiliado_usuario": str(u.get("afiliado_usuario") or ""),
                "porcentaje_comision": float(u.get("porcentaje_comision") or 0.0),
                "ciclo_actual": ciclo_objetivo,
                "ciclo_a_cobrar": ciclo_objetivo,
                "semana_ciclo": semana_en_ciclo,
                "ventana_pago_inicio": inicio_ciclo_obj,
                "ventana_pago_fin": fin_sem4_obj,
                "ajuste_label": ajuste_lbl,
                "ajuste_monto": ajuste_mto,
                "monto_a_pagar": monto_calc,
                "ciclo_pagado": esta_pagado,
                "descarga_permitida": not bloqueado,
                "dias_retraso": dias_retraso_calc,
                "mensaje_estado": (
                    f"✅ Mes/Ciclo {ciclo_vigente} Pagado (Al corriente)" if esta_pagado
                    else (
                        f"⛔ Descarga bloqueada: Mes {ciclo_objetivo} vencido ({dias_retraso_calc} {'día' if dias_retraso_calc == 1 else 'días'} de retraso — Recargo +5%: ${monto_calc:,.2f})"
                        if bloqueado
                        else f"⏳ Mes {ciclo_vigente} — Sem. {semana_en_ciclo}/4 ({ajuste_lbl}: ${monto_calc:,.2f})"
                    )
                )
            })
    except Exception:
        pass
    return info
# ==============================================================================
# PARTE 10B1: BALANCE FINANCIERO GLOBAL OPTIMIZADO (SIN CONSULTAS N+1)
# ==============================================================================
def generar_estado_financiero_global_pg() -> dict:
    hoy = datetime.now(ZoneInfo("America/Hermosillo")).date()
    reglas_activas = get_billing_global_settings_pg()

    filas = []
    ingresos_cobrados_hist = 0.0
    comisiones_generadas_hist = 0.0
    estudiantes_db = []
    pagos_por_alumno = {}

    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("SELECT COALESCE(SUM(monto_final), 0) AS total_ing FROM tuition_payments WHERE estatus = 'Pagado';")
            row_ing = cur.fetchone()
            ingresos_cobrados_hist = float(row_ing["total_ing"]) if row_ing else 0.0

            cur.execute("SELECT COALESCE(SUM(comision_ganada), 0) AS total_com FROM affiliate_commissions;")
            row_com = cur.fetchone()
            comisiones_generadas_hist = float(row_com["total_com"]) if row_com else 0.0

            cur.execute("""
                SELECT id, COALESCE(matricula, 'CEI-2026-' || LPAD(id::text, 4, '0')) AS matricula,
                       usuario, rol, fecha_inicio_curso, mensualidad_base, aplicar_iva,
                       afiliado_usuario, porcentaje_comision
                FROM users_padron
                WHERE LOWER(TRIM(rol)) IN ('estudiante', 'student', 'alumno')
                ORDER BY id ASC;
            """)
            estudiantes_db = cur.fetchall()

            cur.execute("""
                SELECT LOWER(TRIM(student_user)) AS u_key, ciclo_numero
                FROM tuition_payments
                WHERE estatus = 'Pagado' AND ciclo_numero IS NOT NULL;
            """)
            for p_row in cur.fetchall():
                pagos_por_alumno.setdefault(p_row["u_key"], set()).add(int(p_row["ciclo_numero"]))
    except Exception:
        pass

    cartera_por_cobrar_vigente = 0.0
    cartera_vencida_moratoria = 0.0
    conteo_al_corriente = 0
    conteo_moratorios = 0

    for u in estudiantes_db:
        u_nom = str(u.get("usuario") or "").strip()
        mat_id = str(u.get("matricula") or "SIN-ID").strip()
        f_ini = u.get("fecha_inicio_curso") or hoy
        base = float(u.get("mensualidad_base") or 1500.0)
        con_iva = bool(u.get("aplicar_iva") or False)
        afiliado_u = str(u.get("afiliado_usuario") or "").strip()

        dias_trans = max(0, (hoy - f_ini).days)
        ciclo_vig = (dias_trans // 28) + 1
        ciclos_pag = pagos_por_alumno.get(u_nom.lower(), set())
        ciclos_venc = [c for c in range(1, ciclo_vig) if c not in ciclos_pag]

        if ciclos_venc:
            ciclo_obj = next(iter(ciclos_venc))
            es_moratorio = True
            esta_pagado = False
        else:
            ciclo_obj = ciclo_vig
            es_moratorio = False
            esta_pagado = ciclo_vig in ciclos_pag

        fin_sem4_obj = f_ini + timedelta(days=(ciclo_obj * 28) - 1)
        dias_retraso = max(0, (hoy - fin_sem4_obj).days) if es_moratorio else 0

        if not reglas_activas:
            ajuste_mto = 0.0
        elif es_moratorio:
            ajuste_mto = round(base * 0.05, 2)
        else:
            ajuste_mto = round(-base * 0.07, 2)

        subtotal_mes = round(base + ajuste_mto, 2)
        iva_mto = round(subtotal_mes * 0.16, 2) if con_iva else 0.0
        monto_calc = round(subtotal_mes + iva_mto, 2)

        if es_moratorio:
            estatus_fin = "🔴 Moratorio (Vencido)"
            cartera_vencida_moratoria += monto_calc
            conteo_moratorios += 1
        elif esta_pagado:
            estatus_fin = "🟢 Pagado (Al Corriente)"
            conteo_al_corriente += 1
        else:
            estatus_fin = "🟡 Pendiente (En Tiempo)"
            cartera_por_cobrar_vigente += monto_calc
            conteo_al_corriente += 1

        filas.append({
            "ID / Matrícula": mat_id,
            "Estudiante": u_nom,
            "Estatus Financiero": estatus_fin,
            "Mes/Ciclo": int(ciclo_obj),
            "Días Retraso": int(dias_retraso),
            "Base ($)": float(base),
            "Subtotal ($)": float(subtotal_mes),
            "IVA 16% ($)": float(iva_mto),
            "Monto Ciclo ($)": float(monto_calc),
            "Boletín": "✅ Activo" if not es_moratorio else "🔒 Bloqueado",
            "Afiliado": afiliado_u or "Directo"
        })

    total_alumnos = len(filas)
    facturacion_esperada_ciclo = sum(f["Monto Ciclo ($)"] for f in filas)
    pagado_ciclo_actual = sum(f["Monto Ciclo ($)"] for f in filas if "Pagado" in f["Estatus Financiero"])
    tasa_cobranza_pct = round((pagado_ciclo_actual / facturacion_esperada_ciclo) * 100, 1) if facturacion_esperada_ciclo > 0 else 0.0
    indice_morosidad_pct = round((cartera_vencida_moratoria / facturacion_esperada_ciclo) * 100, 1) if facturacion_esperada_ciclo > 0 else 0.0
    ingreso_neto_post_comision = round(ingresos_cobrados_hist - comisiones_generadas_hist, 2)

    return {
        "rows": filas,
        "total_alumnos": total_alumnos,
        "conteo_al_corriente": conteo_al_corriente,
        "conteo_moratorios": conteo_moratorios,
        "ingresos_cobrados_hist": round(ingresos_cobrados_hist, 2),
        "comisiones_generadas_hist": round(comisiones_generadas_hist, 2),
        "ingreso_neto_post_comision": ingreso_neto_post_comision,
        "cartera_por_cobrar_vigente": round(cartera_por_cobrar_vigente, 2),
        "cartera_vencida_moratoria": round(cartera_vencida_moratoria, 2),
        "tasa_cobranza_pct": tasa_cobranza_pct,
        "indice_morosidad_pct": indice_morosidad_pct
    }
# ==============================================================================
# PARTE 10B2: REGISTRO DE PAGOS, CONFIGURACIÓN FINANCIERA Y DATOS DE AFILIADOS
# ==============================================================================
def registrar_pago_mensual_y_comision_pg(student_user: str, registrado_por: str) -> dict:
    est = evaluar_estado_financiero_alumno(student_user)
    if est["ciclo_pagado"]:
        return {"ok": False, "msg": f"El Ciclo {est['ciclo_actual']} ya está pagado."}

    try:
        with pg_session() as cur:
            cur.execute("""
                INSERT INTO tuition_payments (
                    student_user, ciclo_numero, fecha_vencimiento,
                    monto_base, ajuste_tipo, monto_final, estatus, registrado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, 'Pagado', %s)
                ON CONFLICT (student_user, ciclo_numero) DO UPDATE
                SET estatus = 'Pagado', monto_final = EXCLUDED.monto_final,
                    ajuste_tipo = EXCLUDED.ajuste_tipo, fecha_pago = NOW(), registrado_por = EXCLUDED.registrado_por;
            """, (
                student_user.strip(), est["ciclo_actual"], est["ventana_pago_fin"],
                est["mensualidad_base"], est["ajuste_label"], est["monto_a_pagar"], registrado_por
            ))

            afiliado = str(est.get("afiliado_usuario") or "").strip()
            pct_com = float(est.get("porcentaje_comision") or 0.0)
            comision_calc = 0.0

            if afiliado and pct_com > 0:
                comision_calc = round(est["monto_a_pagar"] * (pct_com / 100.0), 2)
                cur.execute("""
                    INSERT INTO affiliate_commissions (
                        affiliate_user, student_user, ciclo_numero,
                        monto_pagado, porcentaje_aplicado, comision_ganada, estatus_pago_comision
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente')
                    ON CONFLICT (affiliate_user, student_user, ciclo_numero) DO UPDATE
                    SET monto_pagado = EXCLUDED.monto_pagado,
                        porcentaje_aplicado = EXCLUDED.porcentaje_aplicado,
                        comision_ganada = EXCLUDED.comision_ganada;
                """, (
                    afiliado, student_user.strip(), est["ciclo_actual"],
                    est["monto_a_pagar"], pct_com, comision_calc
                ))

        return {
            "ok": True,
            "msg": f"✅ Pago registrado: ${est['monto_a_pagar']:,.2f} ({est['ajuste_label']})."
                   + (f" Comisión generada para {afiliado}: ${comision_calc:,.2f} ({pct_com}%)." if comision_calc > 0 else "")
        }
    except Exception as e:
        return {"ok": False, "msg": f"Error al registrar pago: {e}"}

def actualizar_config_financiera_alumno_pg(student_user: str, fecha_inicio_val, mensualidad_val: float, aplicar_iva_val: bool, afiliado_user: str, pct_comision: float) -> bool:
    try:
        with pg_session() as cur:
            aff_clean = afiliado_user.strip()
            aff_id_val = None
            if aff_clean:
                cur.execute("SELECT id FROM users_padron WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) LIMIT 1;", (aff_clean,))
                r_id = cur.fetchone()
                aff_id_val = int(r_id) if r_id else None

            cur.execute("""
                UPDATE users_padron
                SET fecha_inicio_curso = %s,
                    mensualidad_base = %s,
                    aplicar_iva = %s,
                    afiliado_usuario = %s,
                    afiliador_id = %s,
                    porcentaje_comision = %s
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s));
            """, (
                fecha_inicio_val, float(mensualidad_val), bool(aplicar_iva_val),
                aff_clean, aff_id_val, float(pct_comision), student_user.strip()
            ))
        load_padron_records.clear()
        return True
    except Exception:
        return False

def fetch_affiliate_dashboard_pg(affiliate_user: str) -> dict:
    res = {"students": [], "commissions": [], "total_ganado": 0.0, "total_pendiente": 0.0, "total_pagado": 0.0}
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT usuario, nivel_cefr AS nivel, fecha_inicio_curso, mensualidad_base, porcentaje_comision, estatus
                FROM users_padron
                WHERE LOWER(TRIM(afiliado_usuario)) = LOWER(TRIM(%s))
                ORDER BY usuario ASC;
            """, (affiliate_user,))
            res["students"] = [dict(r) for r in cur.fetchall()]

            cur.execute("""
                SELECT student_user AS "Estudiante", ciclo_numero AS "Ciclo (4 Sem)",
                       monto_pagado AS "Colegiatura Pagada ($)", porcentaje_aplicado AS "Comisión (%)",
                       comision_ganada AS "Comisión Generada ($)", estatus_pago_comision AS "Estatus Pago",
                       TO_CHAR(created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD') AS "Fecha"
                FROM affiliate_commissions
                WHERE LOWER(TRIM(affiliate_user)) = LOWER(TRIM(%s))
                ORDER BY created_at DESC;
            """, (affiliate_user,))
            comms = [dict(r) for r in cur.fetchall()]
            res["commissions"] = comms
            res["total_ganado"] = round(sum(float(c["Comisión Generada ($)"]) for c in comms), 2)
            res["total_pendiente"] = round(sum(float(c["Comisión Generada ($)"]) for c in comms if c["Estatus Pago"] == "Pendiente"), 2)
            res["total_pagado"] = round(sum(float(c["Comisión Generada ($)"]) for c in comms if c["Estatus Pago"] != "Pendiente"), 2)
    except Exception:
        pass
    return res
# ==============================================================================
# PARTE 11A: INICIALIZACIÓN DE SESIÓN Y VERIFICACIÓN PÚBLICA DE CERTIFICADOS (QR)
# ==============================================================================
DEFAULT_SESSION_STATES = [
    ("authenticated", False), ("current_user", ""), ("user_role", "Estudiante"),
    ("user_permissions", "Basico"), ("user_assigned_level", "B1 (Intermediate)"),
    ("user_academic_grade", "Licenciatura / Universidad"),
    ("selected_academic_grade", "Licenciatura / Universidad"),
    ("generated_text", ""), ("image_bytes", None), ("audio_bytes", None),
    ("app_exited", False), ("show_saved_audios", False), ("quiz_data", None),
    ("quiz_graded", False), ("quiz_score", None), ("quiz_user_answers", {}),
    ("pending_ls_token", None), ("selected_cefr", "B1 (Intermediate)"),
    ("show_teacher_registry", False), ("current_folio", ""),
    ("current_pdf_link", ""), ("current_creation_date", ""),
    ("show_qr", True), ("url_folio_checked", False),
    ("quiz_audio_bytes", None), ("study_mode_active", False),
    ("speaking_eval_result", None), ("just_logged_out", False)
]

for key, default in DEFAULT_SESSION_STATES:
    if key not in st.session_state:
        st.session_state[key] = default

saved_cfg = load_permanent_logo()
institute_address = (
    str(saved_cfg.get("Direccion", "")).strip()
    if (saved_cfg and saved_cfg.get("Direccion"))
    else DEFAULT_ADDRESS
)
st.session_state["institute_address"] = institute_address

ua_str = str(st.context.headers.get("User-Agent", "")).lower()
is_mobile = any(k in ua_str for k in ["iphone", "android", "mobile", "ipad", "ipod"])

url_folio = st.query_params.get("folio", "")
if url_folio and not st.session_state.current_folio:
    st.session_state.current_folio = str(url_folio).strip().upper()

PERMISSIONS_MATRIX = load_permissions_matrix()
PERMISOS_LISTA = list(PERMISSIONS_MATRIX.keys())

# --- PORTAL PÚBLICO DE VERIFICACIÓN DE CERTIFICADOS (ACCESO POR QR SIN LOGIN) ---
verify_folio = str(st.query_params.get("verify") or st.query_params.get("verify_cert") or "").strip().upper()
if verify_folio:
    if st.session_state.get("portal_verificacion_cerrado", False):
        components.html("<script>window.parent.close(); window.close();</script>", height=0)
        st.markdown("<h4 style='text-align:center; color:#555;'>🔒 Sesión finalizada. Ya puedes cerrar esta pestaña.</h4>", unsafe_allow_html=True)
        st.stop()

    col_vl, col_vc, col_vr = st.columns([1, 2.2, 1])
    with col_vc:
        b64_l, mime_l = (
            (saved_cfg["Logo_Base64"], saved_cfg["Mime_Type"])
            if (saved_cfg and saved_cfg.get("Logo_Base64"))
            else get_default_logo_b64()
        )
        if b64_l:
            st.markdown(
                f'<div style="text-align: center;"><img src="data:{mime_l};base64,{b64_l}" style="width: 110px; border-radius: 50%;"></div>',
                unsafe_allow_html=True
            )
        st.markdown("<h3 style='text-align: center;'>🏛️ CAREER ENGLISH INSTITUTE</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #555; font-size: 12px;'>📍 {institute_address}</p>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🛡️ DIGITAL CREDENTIAL VERIFICATION PORTAL</h2>", unsafe_allow_html=True)
        st.divider()

        try:
            with st.spinner(f"Validando sello criptográfico del certificado {verify_folio}..."):
                folio_norm = verify_folio.replace("-", "").replace(" ", "")
                cert_encontrado = verify_certificate_by_folio_pg(verify_folio)

                if not cert_encontrado:
                    certs = get_certificados_sheet().get_all_records()
                    cert_encontrado = next(
                        (c for c in certs if str(c.get("Folio_Certificado", "")).strip().upper().replace("-", "") == folio_norm),
                        None
                    )

                if cert_encontrado:
                    folio_oficial = str(cert_encontrado.get("Folio_Certificado", verify_folio)).strip().upper()
                    estatus_c = str(cert_encontrado.get("Estatus", "Valido")).strip()
                    clave_c = str(cert_encontrado.get("Clave_Alumno", "")).strip()
                    nombre_c = str(cert_encontrado.get("Nombre_Estudiante", "")).strip()
                    nivel_c = str(cert_encontrado.get("Nivel_CEFR", "")).strip()
                    prog_c = str(cert_encontrado.get("Programa_Curso", "")).strip()
                    calif_c = str(cert_encontrado.get("Calificacion", "")).strip()
                    fecha_c = str(cert_encontrado.get("Fecha_Emision", "")).strip()
                    sello_bd = str(cert_encontrado.get("Sello_Digital_SHA256", "")).strip().upper()

                    _, sello_recalculado = generar_sello_digital(folio_oficial, clave_c, nombre_c, nivel_c, fecha_c)
                    firma_valida = hmac.compare_digest(sello_bd, sello_recalculado) if sello_recalculado else bool(sello_bd)

                    if firma_valida and estatus_c.lower() in ("vigente", "valido", "válido"):
                        st.success("✅ **CERTIFICADO AUTÉNTICO Y VERIFICADO CRIPTOGRÁFICAMENTE**")
                        with st.container(border=True):
                            st.markdown(f"**🔖 Folio Oficial:** `{folio_oficial}`")
                            st.markdown(f"**👤 Titular / Student:** {nombre_c}")
                            st.markdown(f"**🔑 Clave de Registro:** `{clave_c}`")
                            st.markdown(f"**🎯 Nivel Certificado (CEFR):** {nivel_c}")
                            st.markdown(f"**📚 Programa / Módulo:** {prog_c}")
                            st.markdown(f"**🏆 Calificación Final:** {calif_c}")
                            st.markdown(f"**📅 Fecha de Timbrado:** {fecha_c}")
                            st.markdown("**✍️ Autoridad Emisora:** Jacob Zumaya Prianti (Career English Institute)")
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
        if st.button("✖️ Cerrar Verificación", type="primary", width="stretch", key="btn_close_verify_cert"):
            st.session_state["portal_verificacion_cerrado"] = True
            st.rerun()
    st.stop()
# ==============================================================================
# PARTE 11B1: VERIFICACIÓN DE BOLETINES (QR) Y TOKENS DE SESIÓN PERSISTENTE
# ==============================================================================
verify_bol_param = st.query_params.get("verify_transcript", "")
if isinstance(verify_bol_param, list):
    verify_bol_param = verify_bol_param[0] if verify_bol_param else ""
verify_bol_param = str(verify_bol_param).strip().upper()

if verify_bol_param:
    if st.session_state.get("portal_verificacion_cerrado", False):
        components.html("<script>window.parent.close(); window.close();</script>", height=0)
        st.markdown("<h4 style='text-align:center; color:#555;'>🔒 Sesión finalizada. Ya puedes cerrar esta pestaña.</h4>", unsafe_allow_html=True)
        st.stop()

    st.markdown("### 🛡️ Verificación Oficial de Boletín Académico — Career English Institute")
    try:
        row_vb = None
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT
                    folio_boletin, matricula, student_name, nivel_cefr, topic_filter,
                    overall_avg, quiz_avg, oral_avg, total_lessons, hmac_seal,
                    TO_CHAR(issued_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI:SS') AS fecha_emision
                FROM transcripts_archive
                WHERE UPPER(TRIM(folio_boletin)) = %s
                LIMIT 1;
            """, (verify_bol_param,))
            row_vb = cur.fetchone()

        if row_vb:
            st.success(f"✅ **DOCUMENTO AUTÉNTICO Y VIGENTE** — Folio Oficial: `{row_vb['folio_boletin']}`")
            with st.container(border=True):
                c_v1, c_v2 = st.columns(2)
                with c_v1:
                    st.markdown(f"**👤 Estudiante:** {row_vb['student_name']}")
                    st.markdown(f"**🎓 Matrícula Oficial:** `{row_vb['matricula']}`")
                    st.markdown(f"**📘 Nivel CEFR:** {row_vb['nivel_cefr']} ({row_vb['topic_filter']})")
                    st.markdown(f"**📅 Fecha y Hora de Emisión:** {row_vb['fecha_emision']} MST")
                with c_v2:
                    st.metric("🏆 Promedio General Oficial", f"{row_vb['overall_avg']}%")
                    st.markdown(
                        f"**📝 Escrito (Quiz):** {row_vb['quiz_avg']}%  |  "
                        f"**🎙️ Oral:** {row_vb['oral_avg']}%  |  "
                        f"**📚 Lecciones:** {row_vb['total_lessons']}"
                    )
                st.divider()
                st.caption(f"🔐 **Sello Criptográfico HMAC-SHA256:** `{row_vb['hmac_seal']}`")
                st.caption("🏛️ Emitido por **CAREER ENGLISH INSTITUTE** | Director Académico: **Jacob Zumaya Prianti**")
        else:
            st.error(f"⛔ No se encontró ningún Boletín Oficial registrado con el folio `{verify_bol_param}`.")
    except Exception as e_vb:
        st.error(f"Error al verificar boletín en Supabase: {e_vb}")

    st.write("")
    if st.button("✖️ Cerrar Verificación", type="primary", width="stretch", key="btn_close_verify_bol"):
        st.session_state["portal_verificacion_cerrado"] = True
        st.rerun()
    st.stop()

def _sign_session_token(usuario: str, clave: str) -> str:
    secret = _get_hmac_secret_bytes()
    raw_data = f"{usuario}|{clave}"
    sig = hmac.new(secret, raw_data.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    payload = json.dumps({"u": usuario, "c": clave, "s": sig}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")

def _verify_session_token(token_str: str):
    try:
        decoded_json = base64.urlsafe_b64decode(token_str.encode("utf-8")).decode("utf-8")
        token_data = json.loads(decoded_json)
        u_tok = token_data.get("u", "")
        c_tok = token_data.get("c", "")
        s_tok = token_data.get("s", "")
        if not (u_tok and c_tok and s_tok):
            return None, None
        secret = _get_hmac_secret_bytes()
        expected_sig = hmac.new(secret, f"{u_tok}|{c_tok}".encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        if hmac.compare_digest(s_tok, expected_sig):
            return u_tok, c_tok
    except Exception:
        pass
    return None, None

if st.session_state.get("pending_ls_token"):
    tok_act = st.session_state.pop("pending_ls_token")
    if tok_act == "REMOVE":
        js_ck = (
            "<script>try{window.parent.document.cookie='cei_session_token=; "
            "max-age=0; path=/; SameSite=Lax; Secure';}catch(e){"
            "document.cookie='cei_session_token=; max-age=0; path=/; SameSite=Lax; Secure';}</script>"
        )
    else:
        tok_safe = urllib.parse.quote(str(tok_act))
        js_ck = (
            f"<script>try{{window.parent.document.cookie='cei_session_token={tok_safe}; "
            "max-age=2592000; path=/; SameSite=Lax; Secure';}catch(e){"
            f"document.cookie='cei_session_token={tok_safe}; max-age=2592000; path=/; SameSite=Lax; Secure';}}</script>"
        )
    components.html(js_ck, height=0)
# ==============================================================================
# PARTE 11B2: AUTO-LOGIN DESDE COOKIE Y PANTALLA DE CONTROL DE ACCESO (LOGIN)
# ==============================================================================
if not st.session_state.authenticated and not st.session_state.get("just_logged_out"):
    ck_raw = urllib.parse.unquote(str(st.context.cookies.get("cei_session_token", "") or "")).strip()
    if ck_raw:
        try:
            registros_auto = load_padron_records()
            usuario_auto = None
            for reg in registros_auto:
                u_db = str(reg.get("Usuario", "")).strip()
                c_db = str(reg.get("Clave", "")).strip()
                if u_db and c_db and hmac.compare_digest(ck_raw, _sign_session_token(u_db, c_db)):
                    usuario_auto = reg
                    break

            if usuario_auto is None:
                m_user = str(st.secrets.get("OWNER_MASTER_USER", "")).strip()
                m_key = str(st.secrets.get("OWNER_MASTER_KEY", "")).strip()
                if m_user and m_key and hmac.compare_digest(ck_raw, _sign_session_token(m_user, m_key)):
                    usuario_auto = {
                        "Usuario": m_user,
                        "Clave": m_key,
                        "Rol": "Propietario",
                        "Permisos": "Total",
                        "Nivel": "C2",
                        "Grado_Academico": "Doctorado / Posgrado",
                        "Estatus": "Activo"
                    }

            if usuario_auto and str(usuario_auto.get("Estatus", "Activo")).strip().lower() == "activo":
                u_db = str(usuario_auto.get("Usuario", "")).strip()
                r_db = str(usuario_auto.get("Rol", "Estudiante")).strip()
                p_db = resolve_permission_profile(usuario_auto.get("Permisos", ""), r_db, PERMISSIONS_MATRIX)
                n_db = normalize_cefr(usuario_auto.get("Nivel", "B1"))
                g_db = str(usuario_auto.get("Grado_Academico", "Licenciatura / Universidad")).strip() or "Licenciatura / Universidad"

                st.session_state.authenticated = True
                st.session_state.current_user = u_db
                st.session_state.user_role = r_db
                st.session_state.user_permissions = p_db
                st.session_state.user_assigned_level = n_db
                st.session_state.selected_cefr = n_db
                st.session_state.user_academic_grade = g_db
                st.session_state.selected_academic_grade = g_db
                st.rerun()
        except Exception:
            pass

# --- PANTALLA DE LOGIN ---
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        b64_l, mime_l = (
            (saved_cfg["Logo_Base64"], saved_cfg["Mime_Type"])
            if (saved_cfg and saved_cfg.get("Logo_Base64"))
            else get_default_logo_b64()
        )
        if b64_l:
            st.markdown(
                f'<div style="text-align: center;"><img src="data:{mime_l};base64,{b64_l}" style="width: 115px; border-radius: 50%;"></div>',
                unsafe_allow_html=True
            )

        st.markdown("<h3 style='text-align: center;'>🏛️ CAREER ENGLISH INSTITUTE</h3>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🎓 CEFR ACADEMIC GRAMMAR & DISCOURSE SYSTEM</h2>", unsafe_allow_html=True)
        st.divider()

        with st.form("login_form"):
            st.subheader("🔐 Control de Acceso Académico")
            input_user = st.text_input("👤 Usuario registrado:", autocomplete="username")
            input_pass = st.text_input("🔑 Clave de Acceso:", type="password", autocomplete="current-password")
            remember_me = st.checkbox("💾 Recordar mi usuario y contraseña en este navegador", value=True)
            submit_login = st.form_submit_button("Ingresar a la Plataforma", type="primary", width="stretch")

            if submit_login:
                if not input_user.strip() or not input_pass.strip():
                    st.warning("⚠️ Por favor, ingresa tanto tu **Usuario** como tu **Clave de Acceso**.")
                else:
                    try:
                        with st.spinner("Verificando credenciales, grado académico y permisos..."):
                            load_padron_records.clear()
                            registros = load_padron_records()
                            usuario_encontrado = None

                            for reg in registros:
                                u_db = str(reg.get("Usuario", "")).strip()
                                c_db = str(reg.get("Clave", "")).strip()
                                if u_db.lower() == input_user.strip().lower() and hmac.compare_digest(c_db, input_pass.strip()):
                                    usuario_encontrado = reg
                                    break

                            if usuario_encontrado is None:
                                m_user = str(st.secrets.get("OWNER_MASTER_USER", "")).strip()
                                m_key = str(st.secrets.get("OWNER_MASTER_KEY", "")).strip()
                                if m_user and m_key and input_user.strip().lower() == m_user.lower() and hmac.compare_digest(m_key, input_pass.strip()):
                                    usuario_encontrado = {
                                        "Usuario": m_user,
                                        "Clave": m_key,
                                        "Rol": "Propietario",
                                        "Permisos": "Total",
                                        "Nivel": "C2",
                                        "Grado_Academico": "Doctorado / Posgrado",
                                        "Estatus": "Activo"
                                    }

                            if usuario_encontrado is None:
                                st.toast("Acceso denegado: credenciales incorrectas.", icon="🚨")
                                st.error("🚨 **Credenciales Incorrectas:** Verifica tu **Usuario** o **Clave de Acceso**.")
                                if st.session_state.get("db_auth_diag"):
                                    st.caption(f"🔍 Diagnóstico: {st.session_state['db_auth_diag']}")
                            else:
                                e_db = str(usuario_encontrado.get("Estatus", "Activo")).strip().lower()
                                if e_db != "activo":
                                    st.toast("Cuenta inactiva.", icon="⛔")
                                    st.error("⛔ **Acceso Restringido:** Tu cuenta se encuentra **Inactiva**.")
                                else:
                                    u_db = str(usuario_encontrado.get("Usuario", "")).strip()
                                    c_db = str(usuario_encontrado.get("Clave", "")).strip()
                                    r_db = str(usuario_encontrado.get("Rol", "Estudiante")).strip()
                                    p_db = resolve_permission_profile(usuario_encontrado.get("Permisos", ""), r_db, PERMISSIONS_MATRIX)
                                    n_db = normalize_cefr(usuario_encontrado.get("Nivel", "B1"))
                                    g_db = str(usuario_encontrado.get("Grado_Academico", "Licenciatura / Universidad")).strip() or "Licenciatura / Universidad"

                                    st.session_state.authenticated = True
                                    st.session_state.just_logged_out = False
                                    st.session_state.current_user = u_db
                                    st.session_state.user_role = r_db
                                    st.session_state.user_permissions = p_db
                                    st.session_state.user_assigned_level = n_db
                                    st.session_state.selected_cefr = n_db
                                    st.session_state.user_academic_grade = g_db
                                    st.session_state.selected_academic_grade = g_db

                                    if remember_me:
                                        st.session_state.pending_ls_token = _sign_session_token(u_db, c_db)
                                    else:
                                        st.session_state.pending_ls_token = "REMOVE"
                                    st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error de conexión al verificar credenciales: {e}")

        st.markdown(
            f"<div style='text-align: center; color: #777; font-size: 12px; margin-top: 15px;'>📍 {institute_address}<br>© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti</div>",
            unsafe_allow_html=True
        )
    st.stop()
# ==============================================================================
# PARTE 12A: EVALUACIÓN DE CAPACIDADES RBAC Y BARRA LATERAL DE PARÁMETROS
# ==============================================================================
user_caps = PERMISSIONS_MATRIX.get(st.session_state.user_permissions, {})
def can(capability_name: str) -> bool:
    return bool(user_caps.get(capability_name, False))

curr_u_clean = str(st.session_state.get("current_user", "")).strip().lower()
curr_r_clean = str(st.session_state.get("user_role", "")).strip().lower()
curr_p_clean = str(st.session_state.get("user_permissions", "")).strip().lower()
master_u_clean = str(st.secrets.get("OWNER_MASTER_USER", "")).strip().lower()

is_owner = (
    (bool(master_u_clean) and curr_u_clean == master_u_clean)
    or curr_r_clean in ["propietario", "administrador", "admin", "owner"]
    or curr_p_clean == "total"
)

is_faculty_desktop = is_owner or (can("Ver_Panel_Admin") and (not is_mobile))
has_faculty_access = is_owner or can("Reuso_Ilimitado_Folios") or (curr_r_clean in ["teacher", "docente"])
cefr_options = list(CEFR_MAP.values())

# --- BARRA IZQUIERDA (PARÁMETROS ACADÉMICOS) ---
with st.sidebar:
    st.markdown("### 🏛️ CAREER ENGLISH INSTITUTE")
    st.caption(f"📍 {institute_address}")
    st.success(
        f"👤 **{st.session_state.current_user}**\n\n"
        f"🏷️ *{st.session_state.user_role}* | 🛡️ Perfil: **{st.session_state.user_permissions}**"
    )
    st.divider()

    st.header("⚙️ Academic Parameters")
    usuario = st.session_state.current_user

    if is_owner or can("Previsualizar_A1_C2"):
        st.subheader("🎯 Target Calibration (A1 - C2)")
        default_idx = (
            cefr_options.index(st.session_state.user_assigned_level)
            if st.session_state.user_assigned_level in cefr_options else 2
        )
        cefr_level = st.selectbox("Select CEFR Level (A1 - C2):", cefr_options, index=default_idx)

        g_idx = (
            GRADOS_ACADEMICOS.index(st.session_state.user_academic_grade)
            if st.session_state.user_academic_grade in GRADOS_ACADEMICOS else 4
        )
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

    cefr_short_sb = next(iter(cefr_level.split()), "B1")
    st.subheader(f"3. Grammar Topics ({cefr_short_sb})")
    temas_nivel_actual = CEFR_GRAMMAR_TOPICS.get(cefr_short_sb, CEFR_GRAMMAR_TOPICS["B1"])
    gramatica_b1 = st.selectbox(
        "Selecciona el tema gramatical:",
        temas_nivel_actual,
        index=0,
        key="selected_grammar_topic"
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
    generar_btn = st.button(f"🚀 Generate {cefr_short_sb} Lesson", type="primary", width="stretch")
# ==============================================================================
# PARTE 12B: CABECERA INSTITUCIONAL Y BARRA DE COMANDO SPA (CON AUTO-UPDATE)
# ==============================================================================
try:
    default_width = int(saved_cfg["Width"]) if (saved_cfg and saved_cfg.get("Width")) else 115
except (ValueError, TypeError):
    default_width = 115

default_shape = saved_cfg["Shape"] if (saved_cfg and saved_cfg.get("Shape")) else "Circular"
shape_options = ["Original", "Redondeado", "Circular"]
default_shape_idx = shape_options.index(default_shape) if default_shape in shape_options else 2

col_logo, col_title, col_qr, col_exit = st.columns([1.6, 4.7, 1.9, 1.8])

with col_logo:
    if (is_owner or can("Editar_Instituto_Logo")) and (not is_mobile):
        with st.popover("✏️ Editar Logo", width="stretch"):
            logo_file = st.file_uploader("Subir imagen (PNG/JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
            logo_width = st.slider("Tamaño (px):", min_value=60, max_value=220, value=default_width, step=5, key="logo_width_slider")
            logo_shape = st.radio("Forma:", shape_options, index=default_shape_idx, horizontal=True, key="logo_shape_radio")

            if st.button("💾 Guardar Logo Permanente", type="primary", width="stretch", key="btn_save_logo_perm"):
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
    cefr_badge = next(iter(str(cefr_level).split()), "B1") if cefr_level else "B1"
    st.markdown("#### 🏛️ CAREER ENGLISH INSTITUTE")
    st.title(f"🎓 CEFR {cefr_badge} ACADEMIC GRAMMAR & DISCOURSE SYSTEM")
    st.caption("Author: Jacob Zumaya Prianti | Applied Linguistics & Proficiency Assessment | APA Style")

with col_qr:
    if is_owner and (not is_mobile):
        show_qr_now = bool(st.session_state.get("show_qr", False))
        btn_qr_txt = "🙈 Ocultar QR" if show_qr_now else "📱 Mostrar QR"
        if st.button(btn_qr_txt, width="stretch", key="toggle_qr_btn"):
            st.session_state.show_qr = not show_qr_now
            st.rerun()

        if st.session_state.get("show_qr", False):
            app_url = str(st.secrets.get("APP_BASE_URL") or st.secrets.get("APP_PUBLIC_URL") or "https://streamlit.app").strip().rstrip("/")
            if st.session_state.get("current_folio"):
                app_url = f"{app_url}/?folio={urllib.parse.quote(str(st.session_state.current_folio))}"

            qr = qrcode.QRCode(version=1, box_size=4, border=1)
            qr.add_data(app_url)
            qr.make(fit=True)
            buf = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
            st.image(buf.getvalue(), caption="📱 Scan for Mobile View", width=110)

with col_exit:
    if st.button("🚪 Salir", type="secondary", width="stretch", key="btn_header_exit_app"):
        st.session_state.app_exited = True
        st.session_state.authenticated = False
        st.session_state.just_logged_out = True
        st.session_state.pending_ls_token = "REMOVE"
        st.rerun()

# --- BARRA DE COMANDO INSTITUCIONAL FIJA (SPA WORKSPACE SWITCHER) ---
es_socio_afiliado = curr_r_clean in ["socio afiliado", "afiliado", "affiliate"]
if is_owner or is_faculty_desktop or es_socio_afiliado:
    if "active_admin_workspace" not in st.session_state:
        st.session_state["active_admin_workspace"] = None

    if es_socio_afiliado:
        opciones_menu_inst = ["🤝 Portal Socio Afiliado"]
    else:
        opciones_menu_inst = []
        if is_owner or can("Editar_Fecha_Inicio_Curso") or can("Gestionar_Comisiones_Afiliados") or can("Gestionar_IVA_Mensualidad"):
            opciones_menu_inst.append("💳 Cobranza Mensual e IVA")
        if is_owner or can("Ver_Panel_Admin"):
            opciones_menu_inst.append("📊 Estados Financieros")
        if is_owner or can("Gestionar_Comisiones_Afiliados"):
            opciones_menu_inst.extend(["🤝 Alta de Socios Afiliados", "🤝 Portal Socio Afiliado"])
        if is_owner or can("Registrar_Usuarios") or can("Gestionar_Usuarios"):
            opciones_menu_inst.append("👥 Inscripción y Padrón")
        if is_owner or can("Editar_Permisos"):
            opciones_menu_inst.append("🔐 Matriz Global de Permisos")
        if is_owner or can("Emitir_Certificados") or can("Revocar_Certificados"):
            opciones_menu_inst.append("🏅 Certificados (Timbre y QR)")
        if is_owner or can("Editar_Instituto_Logo"):
            opciones_menu_inst.append("🏛️ Datos del Instituto")
        if is_owner:
            opciones_menu_inst.append("🔄 Autoactualización de Librerías")
        if not opciones_menu_inst:
            opciones_menu_inst = ["🏅 Certificados (Timbre y QR)"]

    idx_ws_actual = (
        opciones_menu_inst.index(st.session_state["active_admin_workspace"])
        if st.session_state["active_admin_workspace"] in opciones_menu_inst else 0
    )

    with st.container(border=True):
        c_nav1, c_nav2, c_nav3 = st.columns([3.2, 1.0, 1.2])
        with c_nav1:
            mod_elegido = st.selectbox(
                "🧭 Centro de Mando Institucional:",
                options=opciones_menu_inst,
                index=idx_ws_actual,
                label_visibility="collapsed",
                key="sb_centro_mando_inst"
            )
        with c_nav2:
            if st.button("🚀 IR", type="primary", width="stretch", key="btn_go_workspace"):
                st.session_state["active_admin_workspace"] = mod_elegido
                st.rerun()
        with c_nav3:
            if st.session_state["active_admin_workspace"]:
                if st.button("✖️ CERRAR", type="secondary", width="stretch", key="btn_close_workspace_top"):
                    st.session_state["active_admin_workspace"] = None
                    st.rerun()
# ==============================================================================
# PARTE 13A1: BUSCADOR DE FOLIOS Y BOLETÍN TIMBRADO EN TIEMPO REAL
# ==============================================================================
if "show_gradebook_panel" not in st.session_state:
    st.session_state.show_gradebook_panel = False

with st.container(border=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns([2.1, 1.1, 1.5, 2.0])
    with col_f1:
        folio_input = st.text_input(
            "🔍 Buscador de Folio Académico:",
            value=st.session_state.current_folio,
            placeholder="Ej: CEI-20261113-4821",
            label_visibility="collapsed"
        )
    with col_f2:
        buscar_folio_btn = st.button("🔍 Buscar Folio", width="stretch")
    with col_f3:
        if st.button("📊 Calificaciones", type="primary", width="stretch", key="btn_toggle_gradebook"):
            st.session_state.show_gradebook_panel = not st.session_state.show_gradebook_panel
    with col_f4:
        if st.session_state.current_folio and st.session_state.generated_text:
            st.info(f"📄 **Folio:** `{st.session_state.current_folio}` | 📅 `{st.session_state.current_creation_date}`")
        else:
            st.caption("Busca un Folio o consulta tu Boletín en Tiempo Real.")

if st.session_state.show_gradebook_panel:
    with st.container(border=True):
        st.subheader("📊 Boletín Académico Integral y Desempeño por Grammar Topic")

        if is_owner or can("Ver_Panel_Admin"):
            padron_gb = load_padron_records()
            opciones_gb = {}
            for r_u in padron_gb:
                mat_u = str(r_u.get("Matricula", "")).strip()
                nom_u = str(r_u.get("Usuario", "")).strip()
                niv_u = str(r_u.get("Nivel", "")).strip()
                if nom_u:
                    opciones_gb[f"{mat_u} — {nom_u} (CEFR {niv_u})"] = nom_u

            if opciones_gb:
                sel_gb_label = st.selectbox(
                    "🔎 Buscar Estudiante por Matrícula Oficial o Nombre (Vista Propietario / Admin):",
                    list(opciones_gb.keys()),
                    key="sel_owner_gradebook_matricula"
                )
                alumno_objetivo_gb = opciones_gb[sel_gb_label]
            else:
                alumno_objetivo_gb = st.session_state.current_user
        else:
            alumno_objetivo_gb = st.session_state.current_user
            st.info(f"🎓 **Expediente Académico de:** {alumno_objetivo_gb}")

        gb_data = fetch_student_gradebook_pg(alumno_objetivo_gb)

        lista_topicos_disp = ["Vista General"] + [t["Grammar Topic"] for t in gb_data["topic_summary"]]
        col_f_top, col_f_pdf = st.columns([2.1, 1.4])
        with col_f_top:
            topico_seleccionado_gb = st.selectbox(
                f"🎯 Filtrar Desempeño por Grammar Topic (Nivel CEFR {gb_data['nivel_cefr']}):",
                lista_topicos_disp,
                key="sel_filtro_topico_gradebook"
            )

        with col_f_pdf:
            st.write("")
            fin_alumno = evaluar_estado_financiero_alumno(alumno_objetivo_gb)
            d_ret = int(fin_alumno.get("dias_retraso", 0))
            if is_owner or fin_alumno["descarga_permitida"]:
                cache_key_bol = f"{alumno_objetivo_gb}|{topico_seleccionado_gb}|{gb_data['overall_avg']}|{len(gb_data['records'])}"
                if st.session_state.get("_bol_cache_key") != cache_key_bol:
                    pdf_bol_bytes, timbre_bol = create_official_gradebook_pdf(
                        alumno_objetivo_gb,
                        gb_data,
                        topico_seleccionado_gb
                    )
                    st.session_state["_bol_cache_key"] = cache_key_bol
                    st.session_state["_bol_cache_pdf"] = pdf_bol_bytes
                    st.session_state["_bol_cache_timbre"] = timbre_bol
                else:
                    pdf_bol_bytes = st.session_state["_bol_cache_pdf"]
                    timbre_bol = st.session_state["_bol_cache_timbre"]

                st.download_button(
                    label=f"📥 Descargar Boletín Timbrado ({timbre_bol['folio_boletin']})",
                    data=pdf_bol_bytes,
                    file_name=f"{timbre_bol['folio_boletin']}_{gb_data['matricula']}_{alumno_objetivo_gb.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    width="stretch",
                    key="btn_dl_official_gradebook_pdf"
                )
                if not fin_alumno["descarga_permitida"] and is_owner:
                    st.warning(
                        f"⚠️ **Vista de Propietario:** El estudiante tiene **{d_ret} {'día' if d_ret == 1 else 'días'} de retraso** "
                        f"en el Mes/Ciclo {fin_alumno['ciclo_a_cobrar']} (Para el alumno este boletín está **🔒 BLOQUEADO** — Adeudo: `${fin_alumno['monto_a_pagar']:,.2f} MXN`)."
                    )
                else:
                    st.caption(f"🛡️ Timbrado: `{timbre_bol['folio_boletin']}` | {fin_alumno['mensaje_estado']}")
            else:
                st.error(
                    f"🔒 **Descarga de Boletín Suspendida — {d_ret} {'día' if d_ret == 1 else 'días'} de retraso**\n\n"
                    f"Tu **Mes/Ciclo {fin_alumno['ciclo_a_cobrar']}** venció el `{fin_alumno['ventana_pago_fin']}`.\n"
                    f"• **Días de retraso acumulados:** **{d_ret} {'día' if d_ret == 1 else 'días'}**\n"
                    f"• **Total a cubrir ({fin_alumno['ajuste_label']}):** `${fin_alumno['monto_a_pagar']:,.2f} MXN`\n\n"
                    f"Realiza tu pago mensual para desbloquear la descarga oficial."
                )
# ==============================================================================
# PARTE 13A2: MÉTRICAS DEL BOLETÍN Y RECUPERACIÓN DIRECTA DE FOLIOS
# ==============================================================================
        if topico_seleccionado_gb == "Vista General":
            prom_vista = gb_data["overall_avg"]
            recs_filtrados = gb_data["records"]
            temas_filtrados = gb_data["topic_summary"]
        else:
            t_info = next((t for t in gb_data["topic_summary"] if t["Grammar Topic"] == topico_seleccionado_gb), {})
            prom_vista = t_info.get("Dominio (%)", 0.0)
            recs_filtrados = [r for r in gb_data["records"] if r["Grammar_Topic"] == topico_seleccionado_gb]
            temas_filtrados = [t_info] if t_info else []

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏆 Promedio General", f"{gb_data['overall_avg']}%")
        m2.metric("🎯 Promedio Vista Actual", f"{prom_vista}%")
        m3.metric("📝 Escrito / 🎙️ Oral", f"{gb_data['quiz_avg']}% / {gb_data['oral_avg']}%")
        m4.metric("📚 Lecciones Evaluadas", len(recs_filtrados))

        if temas_filtrados:
            st.markdown("#### 📈 Porcentaje de Dominio por Grammar Topic")
            df_chart = pd.DataFrame(temas_filtrados).set_index("Grammar Topic")
            st.bar_chart(df_chart[["Dominio (%)"]], height=260)
            st.dataframe(pd.DataFrame(temas_filtrados), width="stretch", hide_index=True)

        st.markdown("#### 📋 Historial Completo de Lecciones Evaluadas")
        if recs_filtrados:
            st.dataframe(pd.DataFrame(recs_filtrados), width="stretch", hide_index=True)
        else:
            st.warning("Aún no hay lecciones registradas para este filtro en Supabase.")

auto_fetch_url_folio = bool(
    st.session_state.current_folio
    and not st.session_state.generated_text
    and not st.session_state.get("url_folio_checked", False)
)

if (buscar_folio_btn or auto_fetch_url_folio) and folio_input.strip():
    if auto_fetch_url_folio:
        st.session_state.url_folio_checked = True

    folio_buscado = folio_input.strip().upper()
    try:
        with st.spinner(f"Buscando Folio {folio_buscado} en Supabase PostgreSQL..."):
            row_f = fetch_lesson_by_folio(folio_buscado)

            if not row_f:
                st.warning(f"⚠️ No se encontró ningún registro con el Folio `{folio_buscado}` en Supabase.")
            else:
                st.session_state.generated_text = str(row_f.get("Text", ""))
                st.session_state.selected_cefr = normalize_cefr(row_f.get("CEFR", "B1"))
                st.session_state.selected_academic_grade = str(row_f.get("Grade", "Licenciatura / Universidad"))
                st.session_state.current_folio = folio_buscado
                st.session_state.current_pdf_link = str(row_f.get("PDF_Link") or "")
                st.session_state.current_creation_date = str(row_f.get("Created_At") or "")
                st.session_state.study_mode_active = False
                st.session_state.quiz_graded = False
                st.session_state.quiz_score = None
                st.session_state.quiz_user_answers = {}
                st.session_state.image_bytes = None
                st.session_state.audio_bytes = None
                st.session_state.quiz_audio_bytes = None
                st.session_state.speaking_eval_result = row_f.get("Speaking_Eval")
                st.session_state["best_stored_score"] = str(row_f.get("Best_Score") or "")

                qz_obj = row_f.get("Quiz")
                if isinstance(qz_obj, list):
                    st.session_state.quiz_data = qz_obj
                elif isinstance(qz_obj, dict):
                    st.session_state.quiz_data = qz_obj.get("questions")
                else:
                    st.session_state.quiz_data = None

                if st.session_state.generated_text:
                    try:
                        clean_tts = re.split(
                            r"\bBibliography\b",
                            st.session_state.generated_text.replace("*", "").replace("#", ""),
                            maxsplit=1
                        )
                        tts = gTTS(text=clean_tts, lang="en", slow=False)
                        afp = io.BytesIO()
                        tts.write_to_fp(afp)
                        st.session_state.audio_bytes = afp.getvalue()
                    except Exception:
                        st.warning("⚠️ Lección recuperada, pero el audio no pudo sintetizarse en este momento.")

                st.success(f"✅ Folio **{folio_buscado}** recuperado desde Supabase.")
                st.rerun()
    except Exception as e:
        st.error(f"Error al buscar folio en Supabase: {e}")

st.divider()
# ==============================================================================
# PARTE 14: CENTRO DE MANDO SPA — CERTIFICADOS (EMISIÓN Y VISTA PREVIA)
# ==============================================================================
if (is_owner or is_faculty_desktop or es_socio_afiliado) and st.session_state.get("active_admin_workspace"):
    seccion_inst_sel = st.session_state["active_admin_workspace"]

    with st.container(border=True):
        col_ws_t, col_ws_x = st.columns([4.0, 1.5])
        with col_ws_t:
            st.markdown(f"### {seccion_inst_sel}")
        with col_ws_x:
            if st.button("✖️ CERRAR Y VOLVER A LA LECCIÓN", type="primary", width="stretch", key="btn_close_workspace_header"):
                st.session_state["active_admin_workspace"] = None
                st.rerun()

        st.divider()

        puede_editar_inicio = is_owner or can("Editar_Fecha_Inicio_Curso")
        puede_gestionar_afiliados = is_owner or can("Gestionar_Comisiones_Afiliados")
        puede_gestionar_iva = is_owner or can("Gestionar_IVA_Mensualidad")

        # 14.1 PESTAÑA CERTIFICADOS
        if seccion_inst_sel == "🏅 Certificados (Timbre y QR)":
            if not (is_owner or can("Emitir_Certificados")):
                st.warning("⛔ Tu perfil actual no tiene capacidad habilitada para emitir certificados.")
            else:
                st.markdown("#### 🏅 Emisión Oficial de Certificados con Firma Criptográfica (HMAC-SHA256) y Sello QR")
                try:
                    regs_cert = load_padron_records()
                    opciones_claves = {
                        f"{str(r.get('Matricula', '')).strip()} — {str(r.get('Usuario', '')).strip()} ({str(r.get('Nivel', 'B1')).strip()})": r
                        for r in regs_cert if str(r.get("Matricula", "")).strip()
                    }

                    if not opciones_claves:
                        st.warning("No hay matrículas de estudiantes registradas en el padrón.")
                    else:
                        col_c1, col_c2 = st.columns([1.3, 1.7])
                        with col_c1:
                            sel_label = st.selectbox(
                                "🎓 Seleccionar Matrícula Oficial:",
                                list(opciones_claves.keys()),
                                key="cert_select_clave"
                            )
                            datos_alumno = opciones_claves[sel_label]
                            clave_sel = str(datos_alumno.get("Matricula", "")).strip()
                            nombre_sel = str(datos_alumno.get("Usuario", "")).strip()
                            nivel_sel = normalize_cefr(datos_alumno.get("Nivel", "B1"))
                            grado_sel = str(datos_alumno.get("Grado_Academico", "Licenciatura / Universidad")).strip()
                            st.info(
                                f"**Titular:** {nombre_sel}\n\n"
                                f"**Matrícula:** `{clave_sel}` | **Nivel CEFR:** {nivel_sel}\n\n"
                                f"**Grado:** {grado_sel}"
                            )

                        with col_c2:
                            programa_cert = st.text_input(
                                "📚 Programa / Curso Acreditado:",
                                value=f"CEFR {nivel_sel} Academic English Grammar & Applied Discourse",
                                key="cert_prog_input"
                            )
                            calif_cert = st.text_input(
                                "🏆 Calificación / Resultado Final:",
                                value="98.0% — Passed with Academic Distinction",
                                key="cert_grade_input"
                            )
                            if st.button("🔏 Timbrar y Generar Certificado Oficial (PDF + QR)", type="primary", width="stretch"):
                                with st.spinner("Generando timbrado criptográfico HMAC-SHA256 y guardando en Supabase..."):
                                    ahora_local = datetime.now(ZoneInfo("America/Hermosillo"))
                                    folio_c = f"CERT-{ahora_local.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                                    fecha_c = ahora_local.strftime("%Y-%m-%d %H:%M:%S")

                                    cadena_o, sello_h = generar_sello_digital(folio_c, clave_sel, nombre_sel, nivel_sel, fecha_c)

                                    insert_certificate_pg(
                                        folio_c=folio_c,
                                        clave_sel=clave_sel,
                                        nombre_sel=nombre_sel,
                                        nivel_sel=nivel_sel,
                                        grado_sel=grado_sel,
                                        programa_c=programa_cert.strip(),
                                        calif_c=calif_cert.strip(),
                                        fecha_c=fecha_c,
                                        sello_h=sello_h
                                    )
                                    pdf_cert_bytes = generar_pdf_certificado(
                                        folio_c, clave_sel, nombre_sel, nivel_sel,
                                        programa_cert.strip(), calif_cert.strip(), fecha_c,
                                        cadena_o, sello_h, institute_address
                                    )
                                    st.session_state["last_cert_pdf"] = pdf_cert_bytes
                                    st.session_state["last_cert_name"] = f"Certificado_{folio_c}_{nombre_sel.replace(' ', '_')}.pdf"
                                    st.session_state["last_cert_folio"] = folio_c
                                    st.success(f"✅ ¡Certificado timbrado y guardado en Supabase! Folio: **{folio_c}**")

                        if st.session_state.get("last_cert_pdf"):
                            f_actual = st.session_state["last_cert_folio"]
                            link_cert_directo = _build_cert_verify_url(f_actual)

                            st.markdown(f"##### 👁️ Vista Previa del Certificado Oficial (`{f_actual}`)")
                            try:
                                import pypdfium2 as pdfium
                                pdf_doc = pdfium.PdfDocument(st.session_state["last_cert_pdf"])
                                page = pdf_doc[0]
                                bitmap = page.render(scale=2.0)
                                pil_image = bitmap.to_pil()
                                st.image(pil_image, caption=f"Certificado Oficial Tamaño Carta — {f_actual}", width="stretch")
                            except Exception:
                                st.info("📄 Documento PDF listo. Usa el botón inferior para descargarlo o abrirlo en tu visor.")

                            col_b1, col_b2, col_b3 = st.columns([1.3, 1.4, 1.0])
                            with col_b1:
                                st.download_button(
                                    label="📥 Descargar PDF",
                                    data=st.session_state["last_cert_pdf"],
                                    file_name=st.session_state["last_cert_name"],
                                    mime="application/pdf",
                                    type="primary",
                                    width="stretch",
                                    key="btn_dl_cert_preview"
                                )
                            with col_b2:
                                if st.button("🔗 Guardar Link en Base de Datos", width="stretch", key="btn_save_link_cert"):
                                    try:
                                        update_certificate_link_pg(f_actual, link_cert_directo)
                                        st.success(f"✅ Enlace guardado en Supabase: `{link_cert_directo}`")
                                    except Exception as e_lk:
                                        st.error(f"Error al guardar enlace: {e_lk}")
                            with col_b3:
                                if st.button("✖️ Cerrar Ventana", width="stretch", key="btn_close_cert_preview"):
                                    st.session_state["last_cert_pdf"] = None
                                    st.session_state["last_cert_folio"] = None
                                    st.session_state["last_cert_name"] = None
                                    st.rerun()
# ==============================================================================
# PARTE 14A: CENTRO DE MANDO SPA — HISTORIAL Y REVOCACIÓN DE CERTIFICADOS
# ==============================================================================
                    st.divider()
                    st.markdown("#### 📜 Historial de Certificados Emitidos y Control de Vigencia")
                    certs_hist = load_certificates_pg()

                    if not certs_hist:
                        st.info("ℹ️ Aún no hay certificados guardados en la tabla `certificates` de Supabase.")
                    else:
                        df_certs = pd.DataFrame(certs_hist).rename(columns={"Clave_Alumno": "Matricula"})
                        cols_c_ver = [
                            c for c in ["Folio_Certificado", "Matricula", "Nombre_Estudiante", "Nivel_CEFR", "Fecha_Emision", "Estatus"]
                            if c in df_certs.columns
                        ]
                        st.dataframe(df_certs[cols_c_ver], height=160, width="stretch", hide_index=True)

                        st.markdown("##### 🖨️ Reimprimir o Descargar Certificado Emitido")
                        c_imp1, c_imp2 = st.columns([2.2, 1.3])
                        with c_imp1:
                            opciones_reimp = {
                                f"{row['Folio_Certificado']} — {row['Nombre_Estudiante']} ({row['Nivel_CEFR']}) [{row['Estatus']}]": row
                                for row in certs_hist
                            }
                            sel_reimp_label = st.selectbox(
                                "Seleccionar Certificado del Historial:",
                                list(opciones_reimp.keys()),
                                key="sel_cert_reimprimir"
                            )
                        with c_imp2:
                            st.write("")
                            if st.button("👁️ Cargar Vista Previa / Descargar", width="stretch", key="btn_prep_reimp"):
                                c_obj = opciones_reimp[sel_reimp_label]
                                f_rep = str(c_obj.get("Folio_Certificado", "")).strip()
                                cl_rep = str(c_obj.get("Clave_Alumno", "")).strip()
                                nom_rep = str(c_obj.get("Nombre_Estudiante", "")).strip()
                                niv_rep = str(c_obj.get("Nivel_CEFR", "")).strip()
                                fec_rep = str(c_obj.get("Fecha_Emision", "")).strip()
                                prog_rep = str(c_obj.get("Programa", "")).strip()
                                cal_rep = str(c_obj.get("Calificacion", "")).strip()

                                cad_rep, sello_calc = generar_sello_digital(f_rep, cl_rep, nom_rep, niv_rep, fec_rep)
                                sello_final = str(c_obj.get("Firma_HMAC", "")).strip() or sello_calc

                                st.session_state["last_cert_pdf"] = generar_pdf_certificado(
                                    f_rep, cl_rep, nom_rep, niv_rep,
                                    prog_rep, cal_rep, fec_rep,
                                    cad_rep, sello_final, institute_address
                                )
                                st.session_state["last_cert_folio"] = f_rep
                                st.session_state["last_cert_name"] = f"Certificado_{f_rep}_{nom_rep.replace(' ', '_')}.pdf"
                                st.rerun()

                        if is_owner or can("Revocar_Certificados"):
                            st.divider()
                            c_rev1, c_rev2, c_rev3 = st.columns([2, 1.2, 1.2])
                            with c_rev1:
                                cert_to_mod = st.selectbox(
                                    "Seleccionar Folio de Certificado:",
                                    df_certs["Folio_Certificado"].tolist(),
                                    key="sel_cert_rev"
                                )
                            with c_rev2:
                                nuevo_est_cert = st.selectbox("Estatus:", ["Vigente", "Revocado"], key="sel_est_cert")
                            with c_rev3:
                                st.write("")
                                if st.button("🔄 Aplicar Estatus", width="stretch", key="btn_apply_cert_stat"):
                                    update_certificate_status_pg(str(cert_to_mod), nuevo_est_cert)
                                    st.success(f"✅ Certificado {cert_to_mod} actualizado a '{nuevo_est_cert}' en Supabase.")
                                    st.rerun()
                except Exception as e:
                    st.error(f"Error en módulo de certificados: {e}")
# ==============================================================================
# PARTE 14B1: CENTRO DE MANDO SPA — INSCRIPCIÓN DE USUARIOS EN EL PADRÓN
# ==============================================================================
        elif seccion_inst_sel == "👥 Inscripción y Padrón":
            if not (is_owner or can("Registrar_Usuarios") or can("Gestionar_Usuarios")):
                st.warning("⛔ Tu perfil actual no tiene capacidad habilitada para registrar o modificar usuarios.")
            else:
                permisos_disponibles = PERMISOS_LISTA if (is_owner or can("Editar_Permisos")) else ["Basico"]
                default_perm_idx = permisos_disponibles.index("Basico") if "Basico" in permisos_disponibles else 0

                col_form_reg, col_tabla_reg = st.columns([1.2, 2.0])
                with col_form_reg:
                    st.markdown("#### ➕ Formulario de Inscripción")
                    records_afiliadores = load_padron_records()
                    opciones_afiliadores = {"Sin afiliador (Inscripción directa)": None}
                    for r_aff in records_afiliadores:
                        if r_aff.get("ID"):
                            etiqueta_aff = f"ID #{r_aff['ID']} — {r_aff['Matricula']} ({r_aff['Usuario']})"
                            opciones_afiliadores[etiqueta_aff] = int(r_aff["ID"])

                    with st.form("form_registro_estudiante", clear_on_submit=True):
                        reg_usuario = st.text_input("👤 Nombre Completo / Usuario:", placeholder="Ej: Carlos Mendoza")
                        reg_clave = st.text_input("🔑 Clave de Acceso asignada:", placeholder="Ej: CEI-2026-05")
                        c_r1, c_r2 = st.columns(2)
                        with c_r1:
                            reg_rol = st.selectbox("Rol:", ROLES_LISTA, index=0)
                        with c_r2:
                            reg_nivel = st.selectbox("Nivel CEFR:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2)

                        reg_grado = st.selectbox("🎓 Nivel Académico:", GRADOS_ACADEMICOS, index=1)
                        reg_permiso = st.selectbox("🛡️ Perfil de Permiso:", permisos_disponibles, index=default_perm_idx)
                        reg_afiliador_label = st.selectbox(
                            "🤝 Socio Afiliado / Recomendado por:",
                            list(opciones_afiliadores.keys()),
                            index=0
                        )
                        reg_afiliador_id = opciones_afiliadores[reg_afiliador_label]

                        if st.form_submit_button("💾 Guardar Inscripción", type="primary", width="stretch"):
                            if reg_usuario.strip() and reg_clave.strip():
                                try:
                                    existentes_u = [str(r.get("Usuario", "")).strip().lower() for r in records_afiliadores]
                                    existentes_c = [str(r.get("Clave", "")).strip().lower() for r in records_afiliadores]

                                    if reg_usuario.strip().lower() in existentes_u:
                                        st.error("⚠️ Ese nombre de usuario ya está registrado.")
                                    elif reg_clave.strip().lower() in existentes_c:
                                        st.error("⚠️ Esa clave de acceso ya está asignada a otro usuario.")
                                    else:
                                        matricula_nueva = upsert_user_padron_pg(
                                            usuario=reg_usuario.strip(),
                                            clave=reg_clave.strip(),
                                            rol=reg_rol,
                                            grado=reg_grado,
                                            nivel=reg_nivel,
                                            permisos=reg_permiso,
                                            estatus="Activo",
                                            afiliador_id=reg_afiliador_id
                                        )
                                        st.success(f"✅ {reg_usuario.strip()} inscrito con Matrícula Oficial **{matricula_nueva}**.")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error al registrar en Supabase: {e}")
                            else:
                                st.warning("⚠️ Completa tanto el usuario como la clave.")
# ==============================================================================
# PARTE 14B2: TABLA DE REGISTROS ACTIVOS, EDICIÓN Y ASIGNACIÓN DE AFILIADOS
# ==============================================================================
                with col_tabla_reg:
                    st.markdown("#### 📋 Tabla de Registros Activos")
                    try:
                        records_p = load_padron_records()
                        if records_p:
                            df_p = pd.DataFrame(records_p)
                            cols_mostrar = [
                                c for c in ["ID", "Matricula", "Usuario", "Rol", "Nivel", "Socio_Afiliador", "Permisos", "Estatus"]
                                if c in df_p.columns
                            ]
                            st.dataframe(df_p[cols_mostrar], height=205, width="stretch", hide_index=True)

                            c_ed1, c_ed2, c_ed3 = st.columns([1.4, 1.2, 1.4])
                            with c_ed1:
                                user_to_edit = st.selectbox("Usuario:", df_p["Usuario"].tolist(), key="edit_u_sel")

                            filas_filtradas = df_p[df_p["Usuario"] == user_to_edit].to_dict(orient="records")
                            fila_sel = next(iter(filas_filtradas), {})

                            curr_rol = str(fila_sel.get("Rol", next(iter(ROLES_LISTA), "Estudiante"))).strip()
                            curr_grado = str(fila_sel.get("Grado_Academico", next(iter(GRADOS_ACADEMICOS), "Licenciatura / Universidad"))).strip()
                            curr_lvl = str(fila_sel.get("Nivel", "B1")).strip().upper()[:2]
                            curr_perm = str(fila_sel.get("Permisos", next(iter(permisos_disponibles), "Basico"))).strip()
                            curr_stat = str(fila_sel.get("Estatus", "Activo")).strip()

                            idx_rol = ROLES_LISTA.index(curr_rol) if curr_rol in ROLES_LISTA else 0
                            idx_grado = GRADOS_ACADEMICOS.index(curr_grado) if curr_grado in GRADOS_ACADEMICOS else 1
                            niveles_cefr = ["A1", "A2", "B1", "B2", "C1", "C2"]
                            idx_lvl = niveles_cefr.index(curr_lvl) if curr_lvl in niveles_cefr else 2
                            idx_perm = permisos_disponibles.index(curr_perm) if curr_perm in permisos_disponibles else 0
                            estatus_opts = ["Activo", "Inactivo"]
                            idx_stat = estatus_opts.index(curr_stat) if curr_stat in estatus_opts else 0

                            with c_ed2:
                                new_rol_edit = st.selectbox("Rol:", ROLES_LISTA, index=idx_rol, key="edit_rl_sel")
                            with c_ed3:
                                new_grado_edit = st.selectbox("Nivel Académico:", GRADOS_ACADEMICOS, index=idx_grado, key="edit_gr_sel")

                            c_ed4, c_ed5, c_ed6 = st.columns([1, 1.2, 1])
                            with c_ed4:
                                new_lvl_edit = st.selectbox("CEFR:", niveles_cefr, index=idx_lvl, key="edit_lv_sel")
                            with c_ed5:
                                new_perm_edit = st.selectbox("Permiso:", permisos_disponibles, index=idx_perm, key="edit_pm_sel")
                            with c_ed6:
                                new_status = st.selectbox("Estatus:", estatus_opts, index=idx_stat, key="edit_st_sel")

                            if st.button("🔄 Actualizar Registro", width="stretch"):
                                try:
                                    upsert_user_padron_pg(
                                        usuario=str(user_to_edit),
                                        clave=str(fila_sel.get("Clave", "")),
                                        rol=new_rol_edit,
                                        grado=new_grado_edit,
                                        nivel=new_lvl_edit,
                                        permisos=new_perm_edit,
                                        estatus=new_status
                                    )
                                    st.success(f"✅ Registro de {user_to_edit} actualizado en Supabase.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al actualizar en Supabase: {e}")

                            st.divider()
                            st.markdown("##### 🤝 Asignar, Cambiar o Registrar Socio Afiliado")
                            c_af1, c_af2, c_af3 = st.columns([1.4, 1.6, 1.1])
                            with c_af1:
                                est_af_label = st.selectbox(
                                    "Estudiante:",
                                    [f"ID #{r['ID']} — {r['Usuario']}" for r in records_p if r.get("ID")],
                                    key="sel_est_afiliar"
                                )
                                est_af_id = int(est_af_label.split(" — ")[0].replace("ID #", ""))
                            with c_af2:
                                soc_opts = {"Sin afiliador (Ninguno)": None}
                                for r_s in records_p:
                                    if r_s.get("ID") and int(r_s["ID"]) != est_af_id:
                                        soc_opts[f"ID #{r_s['ID']} — {r_s['Matricula']} ({r_s['Usuario']})"] = int(r_s["ID"])
                                soc_af_label = st.selectbox(
                                    "Socio Afiliado:",
                                    list(soc_opts.keys()),
                                    key="sel_soc_afiliar"
                                )
                            with c_af3:
                                st.write("")
                                if st.button("🤝 Afiliar ID", type="primary", width="stretch", key="btn_save_afiliacion"):
                                    try:
                                        set_student_affiliate_pg(est_af_id, soc_opts[soc_af_label])
                                        st.success(f"✅ Afiliación guardada en PostgreSQL para el estudiante ID #{est_af_id}.")
                                        st.rerun()
                                    except Exception as e_af:
                                        st.error(f"Error al guardar afiliación: {e_af}")

                            with st.expander("➕ Registrar Nuevo Socio Afiliador en el Sistema"):
                                c_ns1, c_ns2, c_ns3 = st.columns([1.6, 1.3, 1.1])
                                with c_ns1:
                                    nuevo_soc_nombre = st.text_input(
                                        "Nombre del Socio Afiliador:",
                                        placeholder="Ej: Lic. Roberto Ruiz",
                                        key="in_nuevo_socio_nom"
                                    )
                                with c_ns2:
                                    nuevo_soc_clave = st.text_input(
                                        "Clave de Acceso:",
                                        placeholder="Ej: SOC-2026-01",
                                        key="in_nuevo_socio_clv"
                                    )
                                with c_ns3:
                                    st.write("")
                                    if st.button("💾 Registrar Socio", type="secondary", width="stretch", key="btn_reg_nuevo_socio"):
                                        if nuevo_soc_nombre.strip() and nuevo_soc_clave.strip():
                                            try:
                                                exist_u = [str(r.get("Usuario", "")).strip().lower() for r in records_p]
                                                exist_c = [str(r.get("Clave", "")).strip().lower() for r in records_p]
                                                if nuevo_soc_nombre.strip().lower() in exist_u:
                                                    st.error("⚠️ Ese nombre ya está registrado.")
                                                elif nuevo_soc_clave.strip().lower() in exist_c:
                                                    st.error("⚠️ Esa clave ya está asignada.")
                                                else:
                                                    mat_socio = upsert_user_padron_pg(
                                                        usuario=nuevo_soc_nombre.strip(),
                                                        clave=nuevo_soc_clave.strip(),
                                                        rol="Socio Afiliado",
                                                        grado="Licenciatura / Universidad",
                                                        nivel="B1",
                                                        permisos="Basico",
                                                        estatus="Activo",
                                                        afiliador_id=None
                                                    )
                                                    st.success(f"✅ Socio Afiliador **{nuevo_soc_nombre.strip()}** registrado con Matrícula **{mat_socio}**.")
                                                    st.rerun()
                                            except Exception as e_ns:
                                                st.error(f"Error al registrar socio: {e_ns}")
                                        else:
                                            st.warning("⚠️ Completa el nombre y la clave del socio.")
                    except Exception as e:
                        st.error(f"Error al cargar padrón: {e}")
# ==============================================================================
# PARTE 14C: MATRIZ RBAC, DATOS DEL INSTITUTO Y AUTOACTUALIZACIÓN DE LIBRERÍAS
# ==============================================================================
        # 14.3 PESTAÑA MATRIZ GLOBAL DE PERMISOS RBAC
        if seccion_inst_sel == "🔐 Matriz Global de Permisos":
            st.markdown("#### 🔐 Matriz Estándar RBAC (Crea o ajusta perfiles de permisos en tiempo real)")
            df_mat = pd.DataFrame([
                {"Perfil_Permiso": k, **{cap: ("SI" if v.get(cap) else "NO") for cap in CAPABILITY_COLS}}
                for k, v in PERMISSIONS_MATRIX.items()
            ])
            st.dataframe(df_mat, width="stretch", hide_index=True)

            if is_owner or can("Editar_Permisos"):
                with st.form("form_nuevo_perfil_permiso", clear_on_submit=True):
                    st.markdown("**➕ Crear o Actualizar Perfil de Permisos:**")
                    nombre_perfil = st.text_input(
                        "Nombre del Perfil (Ej: Coordinador, Recepcion, Supervisor):",
                        placeholder="Ej: Coordinador"
                    )
                    cols_chk = st.columns(4)
                    checks_vals = {}
                    for i, cap in enumerate(CAPABILITY_COLS):
                        with cols_chk[i % 4]:
                            checks_vals[cap] = st.checkbox(cap.replace("_", " "), value=False, key=f"chk_{cap}")

                    if st.form_submit_button("💾 Guardar Perfil en Supabase", type="primary"):
                        perfil_limpio = nombre_perfil.strip()
                        if perfil_limpio:
                            if perfil_limpio.lower() == "total" and (
                                not checks_vals.get("Ver_Panel_Admin") or not checks_vals.get("Editar_Permisos")
                            ):
                                st.error("⛔ Por seguridad, el perfil 'Total' debe conservar 'Ver Panel Admin' y 'Editar Permisos'.")
                            else:
                                try:
                                    upsert_permission_profile_pg(perfil_limpio, checks_vals)
                                    st.success(f"✅ Perfil '{perfil_limpio}' guardado correctamente en Supabase.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar perfil en Supabase: {e}")
                        else:
                            st.warning("⚠️ Escribe un nombre para el perfil.")

        # 14.4 PESTAÑA DATOS DEL INSTITUTO
        if seccion_inst_sel == "🏛️ Datos del Instituto":
            if not (is_owner or can("Editar_Instituto_Logo")):
                st.warning("⛔ Tu perfil actual no tiene capacidad habilitada para editar la información oficial.")
            else:
                st.markdown("#### 🏛️ Dirección y Teléfono Oficial de CAREER ENGLISH INSTITUTE")
                with st.form("form_editar_direccion"):
                    nueva_direccion = st.text_area("📍 Dirección y Contacto Oficial:", value=institute_address, height=80)
                    if st.form_submit_button("💾 Guardar Información Institucional", type="primary"):
                        if nueva_direccion.strip():
                            try:
                                def_b64, def_mime = get_default_logo_b64()
                                b64_c = saved_cfg["Logo_Base64"] if (saved_cfg and saved_cfg.get("Logo_Base64")) else (def_b64 or "")
                                mime_c = saved_cfg["Mime_Type"] if (saved_cfg and saved_cfg.get("Mime_Type")) else (def_mime or "image/png")
                                try:
                                    w_c = int(saved_cfg["Width"]) if (saved_cfg and saved_cfg.get("Width")) else 115
                                except (ValueError, TypeError):
                                    w_c = 115
                                s_c = saved_cfg["Shape"] if (saved_cfg and saved_cfg.get("Shape")) else "Circular"
                                save_permanent_config(b64_c, mime_c, w_c, s_c, nueva_direccion.strip())
                                st.success("✅ ¡Información institucional actualizada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar información: {e}")
                        else:
                            st.warning("⚠️ La dirección institucional no puede quedar vacía.")

            if is_owner:
                st.divider()
                st.markdown("#### 🐘 Migración a PostgreSQL (Supabase)")
                if st.button("🚀 Sincronizar y Migrar Todo a Supabase PostgreSQL", type="primary", width="stretch"):
                    with st.spinner("Migrando permisos, padrón, folios, certificados y configuración a Supabase..."):
                        try:
                            stats_mig = migrar_sheets_a_supabase()
                            st.success(
                                f"✅ **¡Migración Exitosa a PostgreSQL!**\n\n"
                                f"- **Perfiles RBAC:** {stats_mig['permisos']}\n"
                                f"- **Usuarios del Padrón:** {stats_mig['usuarios']}\n"
                                f"- **Lecciones y Folios:** {stats_mig['folios']}\n"
                                f"- **Certificados Oficiales:** {stats_mig['certificados']}\n"
                                f"- **Configuración Institucional:** {stats_mig['config']}"
                            )
                        except Exception as e:
                            st.error(f"❌ Error durante la migración a Supabase: {e}")

        # 14.4B PESTAÑA AUTOACTUALIZACIÓN DE LIBRERÍAS (SIN REVISAR CÓDIGO)
        if seccion_inst_sel == "🔄 Autoactualización de Librerías":
            if not is_owner:
                st.warning("⛔ Solo el Propietario / Administrador Principal puede actualizar las librerías del servidor.")
            else:
                st.markdown("#### 🔄 Gestor Automático de Librerías y Dependencias (PyPI)")
                st.caption("Verifica las versiones activas en tu servidor y actualiza todas las librerías integradas con un solo clic.")

                c_upd1, c_upd2 = st.columns([1.2, 2.0])
                with c_upd1:
                    if st.button("🔍 Comprobar Actualizaciones", width="stretch", key="btn_check_pypi_updates"):
                        check_libraries_updates.clear()
                        st.rerun()

                estado_pkgs = check_libraries_updates()
                pendientes = [p["pip_spec"] for p in estado_pkgs if "Nueva versión" in p["Estado"] or "Pendiente" in p["Estado"]]

                with c_upd2:
                    label_btn_upd = (
                        f"⚡ Autoactualizar {len(pendientes)} Librería(s) Pendiente(s)"
                        if pendientes
                        else "⚡ Reinstalar / Actualizar Todas las Librerías"
                    )
                    if st.button(label_btn_upd, type="primary", width="stretch", key="btn_run_auto_upgrade"):
                        with st.spinner("Actualizando librerías desde PyPI (esto puede tardar 30-60 segundos)..."):
                            ok_up, msg_up = upgrade_managed_libraries(pendientes or None)
                            if ok_up:
                                st.success(msg_up)
                                st.rerun()
                            else:
                                st.error(msg_up)

                df_pkgs = pd.DataFrame(estado_pkgs)[["Paquete", "Instalada", "Última PyPI", "Estado"]]
                st.dataframe(df_pkgs, width="stretch", hide_index=True)
# ==============================================================================
# PARTE 14D1: MÓDULOS FINANCIEROS SPA — COBRANZA MENSUAL E IVA
# ==============================================================================
        # 14.5 PESTAÑA COBRANZA MENSUAL E IVA
        if seccion_inst_sel == "💳 Cobranza Mensual e IVA":
            if not (is_owner or puede_editar_inicio or puede_gestionar_afiliados or puede_gestionar_iva):
                st.warning("⛔ Sin permisos financieros habilitados.")
            else:
                if is_owner:
                    st.markdown("##### 🎛️ Control Global de Incentivos (-7%) y Recargos (+5%)")
                    est_glob = get_billing_global_settings_pg()
                    c_sw1, c_sw2 = st.columns([2.4, 1.0])
                    nuevo_glob = c_sw1.toggle(
                        "Activar Incentivo (-7% hasta Sem. 4) y Recargo (+5% mes siguiente)",
                        value=est_glob,
                        key="tgl_glob_bill"
                    )
                    if c_sw2.button("💾 Guardar Cambio", type="primary", width="stretch", key="btn_glob_bill"):
                        ok_g, msg_g = set_billing_global_settings_pg(nuevo_glob, st.session_state.current_user)
                        if ok_g:
                            st.success(f"✅ {msg_g}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg_g}")
                    st.caption(
                        f"Estado guardado en base de datos: **{'🟢 ACTIVADO (Incentivo -7% / Recargo +5%)' if est_glob else '⚪ DESACTIVADO (Tarifa Base sin incentivos ni recargos)'}**"
                    )
                    st.divider()

                padron_fin = load_padron_records()
                estudiantes_fin = [r for r in padron_fin if str(r.get("Rol", "")).lower() in ["estudiante", "student", "alumno"]]
                afiliados_fin = [str(r.get("Usuario", "")).strip() for r in padron_fin if str(r.get("Rol", "")).lower() in ["socio afiliado", "afiliado", "affiliate"]]

                if estudiantes_fin:
                    mapa_est_fin = {f"{r.get('Matricula', '')} — {r.get('Usuario', '')}": str(r.get("Usuario", "")).strip() for r in estudiantes_fin}
                    sel_est_lbl = st.selectbox("Seleccionar Estudiante:", list(mapa_est_fin.keys()), key="sel_fin_student")
                    est_objetivo = mapa_est_fin[sel_est_lbl]
                    estado_f = evaluar_estado_financiero_alumno(est_objetivo)

                    metrics_placeholder = st.container()
                    col_cfg1, col_cfg2 = st.columns(2)
                    with col_cfg1:
                        st.markdown("##### ⚙️ Configuración de Curso, IVA y Comisión")
                        nueva_fecha_ini = st.date_input("Fecha de Inicio:", value=estado_f["fecha_inicio"], disabled=not puede_editar_inicio, key="inp_f_ini")
                        nueva_mensualidad = st.number_input("Mensualidad Base ($):", min_value=0.0, value=float(estado_f["mensualidad_base"]), step=100.0, disabled=not puede_editar_inicio, key="inp_m_base")
                        nuevo_aplicar_iva = st.checkbox("Aplicar +16% de IVA sobre subtotal", value=bool(estado_f["aplicar_iva"]), disabled=not puede_gestionar_iva, key="chk_iva_al")
                        opciones_aff = ["Sin Afiliado"] + afiliados_fin
                        idx_aff = opciones_aff.index(estado_f["afiliado_usuario"]) if estado_f["afiliado_usuario"] in opciones_aff else 0
                        sel_aff_user = st.selectbox("Socio Afiliado:", opciones_aff, index=idx_aff, disabled=not puede_gestionar_afiliados, key="sel_aff_as")
                        nuevo_pct_com = st.number_input("Comisión Afiliado (%):", min_value=0.0, max_value=100.0, value=float(estado_f["porcentaje_comision"]), step=1.0, disabled=not puede_gestionar_afiliados, key="inp_pct_af")

                        ajuste_vivo = 0.0 if not estado_f["reglas_incentivo_activas"] else (round(nueva_mensualidad * 0.05, 2) if "Recargo" in estado_f["ajuste_label"] else round(-nueva_mensualidad * 0.07, 2))
                        subtotal_vivo = round(nueva_mensualidad + ajuste_vivo, 2)
                        iva_vivo = round(subtotal_vivo * 0.16, 2) if nuevo_aplicar_iva else 0.0
                        total_vivo = round(subtotal_vivo + iva_vivo, 2)

                        if st.button("💾 Guardar Configuración", type="primary", key="btn_save_fin"):
                            aff_s = "" if sel_aff_user == "Sin Afiliado" else sel_aff_user
                            if actualizar_config_financiera_alumno_pg(est_objetivo, nueva_fecha_ini, nueva_mensualidad, nuevo_aplicar_iva, aff_s, nuevo_pct_com):
                                st.success(f"✅ Guardado. Total: ${total_vivo:,.2f} MXN")
                                st.rerun()
                        st.caption(f"🧮 **Cálculo Total:** Base `${nueva_mensualidad:,.2f}` | Subtotal `${subtotal_vivo:,.2f}` | IVA `${iva_vivo:,.2f}` ➔ **Total: `${total_vivo:,.2f}`**")

                    with metrics_placeholder:
                        f1, f2, f3, f4 = st.columns(4)
                        f1.metric("📅 Ciclo", f"Mes {estado_f['ciclo_a_cobrar']}", delta=f"Sem. {estado_f['semana_ciclo']}/4")
                        f2.metric("💵 Subtotal", f"${subtotal_vivo:,.2f}", delta=f"Base: ${nueva_mensualidad:,.2f}")
                        f3.metric("🧾 Total" + (" (+IVA)" if nuevo_aplicar_iva else ""), f"${total_vivo:,.2f}", delta=f"IVA: +${iva_vivo:,.2f}" if nuevo_aplicar_iva else "Sin IVA")
                        d_ret_m = int(estado_f.get("dias_retraso", 0))
                        f4.metric(
                            "📄 Boletín",
                            "✅ Activo" if estado_f["descarga_permitida"] else "🔒 Bloqueado",
                            delta="Al corriente" if estado_f["descarga_permitida"] else f"{d_ret_m} {'día' if d_ret_m == 1 else 'días'} de retraso (Mes {estado_f['ciclo_a_cobrar']})"
                        )

                    with col_cfg2:
                        st.markdown("##### 🧾 Desglose y Cobro Mensual")
                        st.info(
                            f"- **Base:** `${nueva_mensualidad:,.2f}` | **Ajuste:** `${ajuste_vivo:+,.2f}`\n"
                            f"- **Subtotal:** `${subtotal_vivo:,.2f}` | **IVA (16%):** `${iva_vivo:,.2f}`\n"
                            f"- **TOTAL A PAGAR:** **`${total_vivo:,.2f} MXN`**"
                        )
                        if estado_f["ciclo_pagado"]:
                            st.success(f"✅ Mes {estado_f['ciclo_a_cobrar']} pagado.")
                        else:
                            if st.button(f"✅ Registrar Pago (${total_vivo:,.2f})", type="primary", width="stretch", key="btn_reg_pay"):
                                aff_s = "" if sel_aff_user == "Sin Afiliado" else sel_aff_user
                                actualizar_config_financiera_alumno_pg(est_objetivo, nueva_fecha_ini, nueva_mensualidad, nuevo_aplicar_iva, aff_s, nuevo_pct_com)
                                res_p = registrar_pago_mensual_y_comision_pg(est_objetivo, st.session_state.current_user)
                                if res_p["ok"]:
                                    st.success(res_p["msg"])
                                    st.rerun()
                                else:
                                    st.error(res_p["msg"])
# ==============================================================================
# PARTE 14D2: ESTADOS FINANCIEROS CONSOLIDADOS, ALTA Y PORTAL SOCIO AFILIADO
# ==============================================================================
        # 14.5B PESTAÑA ESTADOS FINANCIEROS Y AUDITORÍA DE CARTERA
        if seccion_inst_sel == "📊 Estados Financieros":
            if not (is_owner or can("Ver_Panel_Admin")):
                st.warning("⛔ Tu perfil actual no tiene acceso a los Estados Financieros institucionales.")
            else:
                st.markdown("#### 📊 Estado Financiero Consolidado y Control de Cartera")
                ef_data = generar_estado_financiero_global_pg()

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("💰 Ingreso Bruto Recaudado", f"${ef_data['ingresos_cobrados_hist']:,.2f} MXN")
                k2.metric("🤝 Provisión Comisiones Afiliados", f"-${ef_data['comisiones_generadas_hist']:,.2f} MXN")
                k3.metric("🏦 Ingreso Neto Operativo", f"${ef_data['ingreso_neto_post_comision']:,.2f} MXN")
                k4.metric("📈 Eficiencia de Cobranza (Ciclo)", f"{ef_data['tasa_cobranza_pct']}%", delta=f"Morosidad: {ef_data['indice_morosidad_pct']}%", delta_color="inverse")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🎓 Matrícula Activa Evaluada", f"{ef_data['total_alumnos']} alumnos")
                c2.metric("🟡 Por Cobrar en Tiempo (Sem. 1-4)", f"${ef_data['cartera_por_cobrar_vigente']:,.2f} MXN")
                c3.metric("🔴 Cartera Vencida (Moratorios)", f"${ef_data['cartera_vencida_moratoria']:,.2f} MXN", delta=f"{ef_data['conteo_moratorios']} en mora", delta_color="inverse")
                c4.metric("🟢 Al Corriente / Pagados", f"{ef_data['conteo_al_corriente']} alumnos")

                st.divider()

                col_f1, col_f2 = st.columns([1.4, 1.6])
                busqueda_id = col_f1.text_input(
                    "🔍 Buscar por ID / Matrícula o Nombre:",
                    placeholder="Ej. CEI-2026-001 o Juan...",
                    key="inp_search_ef_id"
                ).strip().lower()

                filtro_tipo_ef = col_f2.radio(
                    "Filtrar Estado de Cuenta:",
                    options=["Todos", "Moratorios", "Pagos realizados", "Pendientes en tiempo"],
                    horizontal=True,
                    key="rad_filter_ef_status"
                )

                df_ef = pd.DataFrame(ef_data["rows"])
                if not df_ef.empty:
                    if busqueda_id:
                        mask_id = (
                            df_ef["ID / Matrícula"].str.lower().str.contains(busqueda_id, regex=False, na=False)
                            | df_ef["Estudiante"].str.lower().str.contains(busqueda_id, regex=False, na=False)
                        )
                        df_ef = df_ef[mask_id]

                    if filtro_tipo_ef == "Moratorios":
                        df_ef = df_ef[df_ef["Estatus Financiero"].str.contains("Moratorio", na=False)]
                    elif filtro_tipo_ef == "Pagos realizados":
                        df_ef = df_ef[df_ef["Estatus Financiero"].str.contains("Pagado", na=False)]
                    elif filtro_tipo_ef == "Pendientes en tiempo":
                        df_ef = df_ef[df_ef["Estatus Financiero"].str.contains("Pendiente", na=False)]

                    st.dataframe(df_ef, width="stretch", hide_index=True)

                    csv_ef = df_ef.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="📥 Exportar Reporte Financiero (CSV / Excel)",
                        data=csv_ef,
                        file_name=f"Estado_Financiero_CEI_{datetime.now(ZoneInfo('America/Hermosillo')).strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="btn_dl_ef_csv"
                    )
                else:
                    st.info("No hay registros financieros de estudiantes para mostrar.")

        # 14.5C PESTAÑA DEDICADA: ALTA DE SOCIOS AFILIADOS Y QR DE REGISTRO
        if seccion_inst_sel == "🤝 Alta de Socios Afiliados":
            if not (is_owner or puede_gestionar_afiliados):
                st.warning("⛔ Tu perfil actual no tiene permisos habilitados para dar de alta Socios Afiliados.")
            else:
                try:
                    from registro_afiliados import render_formulario_registro_afiliado
                    render_formulario_registro_afiliado(
                        registrado_por=st.session_state.current_user,
                        key_prefix="panel_admin_aff_main",
                        mostrar_qr_dinamico=True
                    )
                except ModuleNotFoundError:
                    st.warning("⚠️ Crea el archivo `registro_afiliados.py` en la raíz del proyecto para activar este formulario.")

        # 14.6 PESTAÑA PORTAL SOCIO AFILIADO
        if seccion_inst_sel == "🤝 Portal Socio Afiliado":
            url_portal_aff = str(st.secrets.get("AFFILIATE_PORTAL_URL", "")).strip().rstrip("/")
            aff_objetivo_portal = st.session_state.current_user

            if is_owner or puede_gestionar_afiliados:
                padron_aff_view = load_padron_records()
                lista_aff_view = [str(r.get("Usuario", "")).strip() for r in padron_aff_view if str(r.get("Rol", "")).lower() in ["socio afiliado", "afiliado", "affiliate"]]
                col_p_sel, col_p_qr = st.columns([2.6, 1.0])
                with col_p_sel:
                    if lista_aff_view:
                        aff_objetivo_portal = st.selectbox("Portal del Socio Afiliado:", lista_aff_view, key="sel_prev_aff")
                    else:
                        aff_objetivo_portal = None
                        st.info("Aún no hay Socios Afiliados registrados.")
                with col_p_qr:
                    if url_portal_aff:
                        buf_qp = io.BytesIO()
                        qrcode.make(url_portal_aff).save(buf_qp, format="PNG")
                        st.image(buf_qp.getvalue(), caption="📲 QR Portal Afiliados", width=120)
                        st.download_button(
                            "⬇️ Descargar QR Portal",
                            data=buf_qp.getvalue(),
                            file_name="QR_Portal_Afiliados_CEI.png",
                            mime="image/png",
                            width="stretch",
                            key="btn_dl_qrportal_main"
                        )

            if aff_objetivo_portal:
                try:
                    from portal_afiliado import render_portal_socio_afiliado
                    render_portal_socio_afiliado(aff_objetivo_portal)
                except ModuleNotFoundError:
                    dash_aff = fetch_affiliate_dashboard_pg(aff_objetivo_portal)
                    ka1, ka2, ka3 = st.columns(3)
                    ka1.metric("💰 Total Ganado", f"${dash_aff['total_ganado']:,.2f} MXN")
                    ka2.metric("⏳ Pendiente de Pago", f"${dash_aff['total_pendiente']:,.2f} MXN")
                    ka3.metric("✅ Ya Pagado", f"${dash_aff['total_pagado']:,.2f} MXN")
                    if dash_aff["students"]:
                        st.markdown("##### 🎓 Estudiantes Referidos")
                        st.dataframe(pd.DataFrame(dash_aff["students"]), width="stretch", hide_index=True)
                    if dash_aff["commissions"]:
                        st.markdown("##### 💵 Historial de Comisiones")
                        st.dataframe(pd.DataFrame(dash_aff["commissions"]), width="stretch", hide_index=True)

    st.stop()
# ==============================================================================
# PARTE 15: PROCESAMIENTO Y GENERACIÓN DE LECCIÓN (VALIDACIÓN Y PROMPT GEMINI)
# ==============================================================================
if generar_btn:
    campos_faltantes = []
    if not str(locals().get("contexto", "")).strip():
        campos_faltantes.append("Contexto / Escenario")
    if not str(locals().get("personas", "")).strip():
        campos_faltantes.append("Personajes / Participantes")
    if not str(locals().get("asunto", "")).strip():
        campos_faltantes.append("Tema / Asunto")

    gm_active = client or init_gemini_client()
    if gm_active is None:
        st.sidebar.error("⚠️ GEMINI_API_KEY no configurada.")
        st.error("⚠️ Error de configuración: falta GEMINI_API_KEY.")
    elif campos_faltantes:
        lista_faltantes = ", ".join(campos_faltantes)
        st.toast(f"Faltan datos por completar: {lista_faltantes}", icon="⚠️")
        st.sidebar.warning(f"⚠️ Completa los siguientes campos antes de generar:\n\n**{lista_faltantes}**")
        st.warning(f"⚠️ **Datos incompletos:** Por favor llena **{lista_faltantes}** en el panel izquierdo.")
    else:
        st.session_state.show_teacher_registry = False
        st.session_state["active_admin_workspace"] = None

        stop_box = st.empty()
        with stop_box.container():
            col_sp1, col_sp2 = st.columns([3.2, 1.0])
            with col_sp1:
                st.info(f"🧠 Normalizing inputs, translating & generating CEFR {cefr_level} ({academic_grade}) Lesson...")
            with col_sp2:
                if st.button("🛑 Detener", type="secondary", width="stretch", key="btn_stop_lesson_gen"):
                    stop_box.empty()
                    st.warning("⏹️ Generación detenida por el usuario.")
                    st.stop()

        with st.spinner(f"🧠 Normalizing inputs, translating & generating CEFR {cefr_level} ({academic_grade}) Lesson..."):
            try:
                contexto_en, personas_en, asunto_apa = normalizar_entradas_apa(
                    gm_active, contexto, personas, asunto
                )

                ahora_local = datetime.now(ZoneInfo("America/Hermosillo"))
                nuevo_folio = f"CEI-{ahora_local.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                fecha_creacion = ahora_local.strftime("%Y-%m-%d %H:%M:%S")

                base_url = str(st.secrets.get("APP_PUBLIC_URL") or st.secrets.get("APP_BASE_URL") or "").strip().rstrip("/")
                pdf_url_directo = f"{base_url}/?folio={urllib.parse.quote(nuevo_folio)}" if base_url else f"/?folio={urllib.parse.quote(nuevo_folio)}"

                cefr_guidelines = {
                    "A1": "Use very basic everyday vocabulary, short simple sentences (5-8 words), present simple/continuous, and concrete familiar topics.",
                    "A2": "Use simple, clear sentences, basic connectors (and, but, because, so), past simple, and everyday routine vocabulary.",
                    "B1": "Use clear standard English, connected paragraphs, intermediate vocabulary, and a mix of simple and complex clauses.",
                    "B2": "Use fluent, detailed academic/semi-formal English, complex sentence structures, nuanced connectors, and abstract concepts.",
                    "C1": "Use sophisticated, advanced academic English, idiomatic expressions, complex subordinate clauses, and high lexical precision.",
                    "C2": "Use near-native, scholarly English with subtle rhetorical devices, advanced syntax, and specialized academic vocabulary."
                }
                nivel_corto = next(iter(cefr_level.split()), "B1")
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
                - Context: {contexto_en} | Characters: {personas_en} | Subject: {asunto_apa}
                - Target Grammar: {gramatica_b1} | Discourse Mode: {tipo_texto}

                STRICT RULES:
                1. 100% English only. Calibrate vocabulary and grammar strictly to CEFR {cefr_level} and pedagogical tone to {academic_grade}. Highlight all {gramatica_b1} structures in **bold**.
                2. APA Header & Byline: Include the academic title in bold, followed immediately by:
                   **Folio:** {nuevo_folio} | **Creation Date:** {fecha_creacion}  
                   **Author:** Jacob Zumaya Prianti | **Institution:** Career English Institute (2026)  
                   **CEFR Level:** {cefr_level} | **Academic Level:** {academic_grade}  
                   **Campus & Contact:** {institute_address}
                3. Bibliography / APA References Section: At the end of the lesson, include a formal section titled **Bibliography (Consulted Academic & Linguistic Sources)** formatted in strict APA 7th edition. List:
                   - Primary instructional module: Zumaya Prianti, J. (2026). *{asunto_apa}: CEFR {nivel_corto} ({academic_grade}) Applied Grammar & Discourse Module* (Folio {nuevo_folio}). Career English Institute.
                   - 3 to 4 real, authoritative linguistic, pedagogical, or subject-matter reference works directly relevant to "{asunto_apa}", "{gramatica_b1}", and {academic_grade} education, sorted alphabetically by author surname.
                """
# ==============================================================================
# PARTE 15A: EJECUCIÓN PARALELA (QUIZ + IMAGEN), AUDIO Y PERSISTENCIA EN PG
# ==============================================================================
                texto_gen, mod_usado = generar_con_maxima_potencia(gm_active, prompt_texto, sys_prompt)
                st.session_state.generated_text = texto_gen
                st.session_state.study_mode_active = False
                st.session_state.active_model_name = mod_usado
                st.session_state.selected_cefr = cefr_level
                st.session_state.selected_academic_grade = academic_grade
                st.session_state.current_folio = nuevo_folio
                st.session_state.current_pdf_link = pdf_url_directo
                st.session_state.current_creation_date = fecha_creacion
                st.session_state.current_topic = asunto_apa
                st.session_state.quiz_data = None
                st.session_state.quiz_graded = False
                st.session_state.quiz_score = None
                st.session_state.quiz_user_answers = {}
                st.session_state.audio_bytes = None
                st.session_state.image_bytes = None
                st.session_state.current_motivational_quote = None
                st.session_state.speaking_eval_result = None
                st.session_state["best_stored_score"] = ""

                escena_visual = f"Setting: {contexto_en}. Characters: {personas_en}. Topic: {asunto_apa}."

                ctx_st = get_script_run_ctx() if callable(get_script_run_ctx) else None

                def _run_with_ctx(fn, *args):
                    if ctx_st and callable(add_script_run_ctx):
                        add_script_run_ctx(ctx=ctx_st)
                    return fn(*args)

                with ThreadPoolExecutor(max_workers=2) as pool:
                    fut_quiz = pool.submit(
                        _run_with_ctx,
                        generar_quiz_leccion,
                        texto_gen,
                        gramatica_b1,
                        cefr_level,
                        academic_grade,
                        None,
                        gm_active
                    )
                    fut_img = pool.submit(
                        _run_with_ctx,
                        generar_imagen_garantizada,
                        gm_active,
                        escena_visual,
                        f"Folio {nuevo_folio}",
                        cefr_level,
                        academic_grade
                    )
                    try:
                        st.session_state.quiz_data = fut_quiz.result(timeout=20)
                    except Exception:
                        st.session_state.quiz_data = None
                    try:
                        st.session_state.image_bytes = fut_img.result(timeout=20)
                    except Exception:
                        st.session_state.image_bytes = None

                try:
                    clean_tts = re.split(r"\bBibliography\b", texto_gen.replace("*", "").replace("#", ""), maxsplit=1)[0]
                    tts = gTTS(text=clean_tts, lang="en", slow=False)
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.session_state.audio_bytes = audio_fp.getvalue()
                except Exception:
                    st.warning("⚠️ Lección generada, pero el audio no pudo sintetizarse en este momento.")

                try:
                    tema_reg = f"[{nivel_corto} | {academic_grade}] {asunto_apa} ({gramatica_b1})"
                    save_lesson_to_postgres(
                        folio=nuevo_folio,
                        usuario_name=st.session_state.get("current_user", usuario),
                        tema=tema_reg,
                        cefr=cefr_level,
                        grado=academic_grade,
                        texto=texto_gen,
                        pdf_link=pdf_url_directo
                    )
                    if st.session_state.quiz_data:
                        save_quiz_and_best_score_pg(nuevo_folio, "", st.session_state.quiz_data, {})
                except Exception as e_db:
                    st.warning(f"⚠️ Lección generada, pero hubo un aviso al guardar en Supabase: {e_db}")

                st.session_state.sidebar_state = "collapsed"
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error al generar lección: {e}")

# ==============================================================================
# PARTE 16: ÁREA DE LECTURA / MODO ESTUDIO INTERACTIVO Y QUIZ (PARTE 1)
# ==============================================================================
if st.query_params.get("study_w"):
    st.session_state["study_mode_active"] = True

col_lesson_left, col_tools_right = st.columns([2.2, 1.3])

with col_lesson_left:
    hdr_l1, hdr_l2 = st.columns([2.4, 1.4])
    with hdr_l1:
        st.subheader(f"📖 Generated Lesson ({st.session_state.selected_cefr})")
    with hdr_l2:
        if st.session_state.get("generated_text"):
            lbl_modo = (
                "📄 Volver a Lectura Clásica"
                if st.session_state.get("study_mode_active")
                else "🧠 Activar Modo Estudio IA"
            )
            if st.button(lbl_modo, type="secondary", width="stretch", key="btn_toggle_study_mode"):
                st.session_state.study_mode_active = not st.session_state.get("study_mode_active", False)
                if not st.session_state.study_mode_active:
                    st.session_state["active_study_word"] = ""
                    if "study_w" in st.query_params:
                        del st.query_params["study_w"]
                    if "study_p" in st.query_params:
                        del st.query_params["study_p"]
                st.rerun()

    if st.session_state.get("generated_text"):
        if st.session_state.get("study_mode_active"):
            with st.spinner("Analizando estructuras gramaticales, fonética y definiciones..."):
                payload_estudio = analyze_lesson_for_study_mode(
                    st.session_state.generated_text,
                    st.session_state.selected_cefr
                )
            render_interactive_study_viewer(payload_estudio)
        else:
            with st.container(height=540, border=True):
                st.markdown(st.session_state.generated_text)
    else:
        with st.container(height=280, border=True):
            st.info(
                "👈 Configura los parámetros en el panel izquierdo y presiona **Generate Lesson**, "
                "o busca un **Folio** existente en la barra superior."
            )


    # QUIZ INTERACTIVO DE LA LECCIÓN
    if st.session_state.get("generated_text"):
        if st.session_state.quiz_data is None:
            cefr_tag = next(iter(st.session_state.selected_cefr.split()), "CEFR") if st.session_state.selected_cefr else "CEFR"
            if st.button(
                f"📝 Generar Quiz ({cefr_tag} - {st.session_state.selected_academic_grade})",
                type="primary",
                width="stretch"
            ):
                with st.spinner("Generando preguntas de evaluación y vinculando al Folio en Supabase..."):
                    try:
                        q_gen = generar_quiz_leccion(
                            st.session_state.generated_text,
                            gramatica_b1,
                            st.session_state.selected_cefr,
                            st.session_state.selected_academic_grade
                        )
                        st.session_state.quiz_data = q_gen
                        if st.session_state.current_folio:
                            save_quiz_and_best_score_pg(
                                st.session_state.current_folio,
                                "",
                                q_gen,
                                {}
                            )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al generar quiz: {e}")
        else:
            with st.container(border=True):
                st.subheader(f"📝 Lesson Comprehension & Grammar Quiz (Folio: {st.session_state.current_folio})")
                for idx, item in enumerate(st.session_state.quiz_data):
                    st.markdown(f"**{idx + 1}. {item['question']}**")
                    choice = st.radio(
                        f"q_{idx}",
                        item["options"],
                        key=f"radio_quiz_{idx}",
                        label_visibility="collapsed",
                        index=None
                    )
                    st.session_state.quiz_user_answers[idx] = choice
                    if st.session_state.quiz_graded:
                        if choice == item["answer"]:
                            st.success(f"✅ Correct! ({item['answer']})")
                        else:
                            st.error(f"❌ Incorrect. Your answer: {choice or 'None'} | **Correct answer:** {item['answer']}")
                    st.write("")
# ==============================================================================
# PARTE 16A: CALIFICACIÓN DEL QUIZ, NUEVAS PREGUNTAS Y AUDIO DEL EXAMEN
# ==============================================================================
                col_btn_grade, col_btn_new = st.columns(2)
                with col_btn_grade:
                    if st.button("✅ Calificar Quiz", type="primary", width="stretch"):
                        correctas = sum(
                            1 for i, it in enumerate(st.session_state.quiz_data)
                            if st.session_state.quiz_user_answers.get(i) == it["answer"]
                        )
                        total = len(st.session_state.quiz_data)
                        nota_actual = f"{correctas}/{total} ({round((correctas / total) * 100, 1)}%)"
                        st.session_state.quiz_score = nota_actual
                        st.session_state.quiz_graded = True

                        if st.session_state.current_folio:
                            with st.spinner("Evaluando y guardando mejor calificación en Supabase..."):
                                _, msg_comp, mejor_nota_final = save_quiz_and_best_score_pg(
                                    st.session_state.current_folio,
                                    nota_actual,
                                    st.session_state.quiz_data,
                                    st.session_state.quiz_user_answers
                                )
                                st.session_state["best_score_feedback"] = msg_comp
                                st.session_state["best_stored_score"] = mejor_nota_final
                        st.rerun()

                with col_btn_new:
                    if st.button("🔄 Nuevo Quiz (Cambiar Preguntas)", type="secondary", width="stretch"):
                        with st.spinner("Generando nuevas preguntas..."):
                            try:
                                prev_qs = [q["question"] for q in st.session_state.quiz_data]
                                q_new = generar_quiz_leccion(
                                    st.session_state.generated_text,
                                    gramatica_b1,
                                    st.session_state.selected_cefr,
                                    st.session_state.selected_academic_grade,
                                    prev_qs
                                )
                                st.session_state.quiz_data = q_new
                                st.session_state.quiz_graded = False
                                st.session_state.quiz_score = None
                                st.session_state.quiz_user_answers = {}
                                for k_r in range(10):
                                    st.session_state.pop(f"radio_quiz_{k_r}", None)
                                if st.session_state.current_folio:
                                    save_quiz_and_best_score_pg(
                                        st.session_state.current_folio,
                                        st.session_state.get("best_stored_score", ""),
                                        q_new,
                                        {}
                                    )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al renovar quiz: {e}")

                if st.session_state.quiz_graded and st.session_state.quiz_score:
                    st.info(f"🏆 **Calificación de este intento:** {st.session_state.quiz_score}")
                    if st.session_state.get("best_score_feedback"):
                        st.success(st.session_state["best_score_feedback"])

                    nota_para_pdf = st.session_state.get("best_stored_score") or st.session_state.quiz_score
                    pdf_quiz_bytes = create_lesson_pdf(
                        st.session_state.generated_text.replace("*", ""),
                        quiz_items=st.session_state.quiz_data,
                        user_ans=st.session_state.quiz_user_answers,
                        score=nota_para_pdf,
                        speaking_eval=st.session_state.get("speaking_eval_result")
                    )

                    st.download_button(
                        label=f"📥 Descargar PDF Oficial con Mejor Calificación ({nota_para_pdf})",
                        data=pdf_quiz_bytes,
                        file_name=f"{st.session_state.current_folio or 'CEI_Exam'}_{usuario.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        type="primary",
                        key="btn_dl_pdf_from_quiz",
                        width="stretch"
                    )

                st.divider()
                col_q_aud1, col_q_aud2 = st.columns(2)
                with col_q_aud1:
                    if st.button("🔊 Generar Audio del Quiz", key="btn_gen_quiz_audio", width="stretch"):
                        with st.spinner("Sintetizando audio del cuestionario en inglés..."):
                            try:
                                lineas_audio = [
                                    f"Lesson Comprehension and Grammar Quiz. Folio {st.session_state.current_folio or ''}."
                                ]
                                for idx_q, q_item in enumerate(st.session_state.quiz_data, start=1):
                                    lineas_audio.append(f"Question {idx_q}: {q_item['question']}")
                                    for opt_txt in q_item["options"]:
                                        lineas_audio.append(opt_txt)
                                    if st.session_state.quiz_graded:
                                        lineas_audio.append(f"Correct answer: {q_item['answer']}.")

                                guion_quiz = " ".join(lineas_audio).replace("*", "").replace("#", "")
                                tts_q = gTTS(text=guion_quiz, lang="en", slow=False)
                                buf_q = io.BytesIO()
                                tts_q.write_to_fp(buf_q)
                                st.session_state.quiz_audio_bytes = buf_q.getvalue()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al generar audio del quiz: {e}")

                with col_q_aud2:
                    if st.session_state.get("quiz_audio_bytes"):
                        st.download_button(
                            label="📥 Descargar Audio del Quiz (MP3)",
                            data=st.session_state.quiz_audio_bytes,
                            file_name=f"CEI_Quiz_Audio_{st.session_state.current_folio or 'Practice'}.mp3",
                            mime="audio/mp3",
                            width="stretch"
                        )
                    else:
                        st.button("📥 Descargar Audio del Quiz (MP3)", disabled=True, width="stretch")

                if st.session_state.get("quiz_audio_bytes"):
                    st.audio(st.session_state.quiz_audio_bytes, format="audio/mp3")
# ==============================================================================
# PARTE 17: COLUMNA DERECHA — CONTEXTO VISUAL Y AUDIO MODELO
# ==============================================================================
with col_tools_right:
    st.subheader(f"🖼️ Visual Context & Quote ({st.session_state.selected_academic_grade})")
    if st.session_state.get("generated_text"):
        col_vis_in, col_vis_btn = st.columns([2.6, 1.4])
        with col_vis_in:
            custom_img_prompt = st.text_input(
                "🎨 Descripción personalizada de la escena (Opcional - Español/English):",
                placeholder="Ej: Una oficina con libros, el investigador y el padre sentados hablando...",
                key="input_custom_visual_prompt",
                label_visibility="collapsed"
            )

        with col_vis_btn:
            if st.button("✨ Imagen y Frase", key="btn_regen_visual", width="stretch"):
                with st.spinner("🎨 Generando imagen temática y frase célebre..."):
                    try:
                        client_vis = init_gemini_client()
                        instruccion_usuario = (
                            f"USER CUSTOM VISUAL REQUEST (Translate to English and prioritize this exact setting/characters): {custom_img_prompt.strip()}"
                            if custom_img_prompt.strip()
                            else "Create a fresh, different visual scene angle based on the lesson."
                        )
                        prompt_nueva_escena = f"""
                        Read the English lesson below and write a vivid visual scene description (45-55 words) for an educational illustration:
                        {instruccion_usuario}
                        1. SETTING & FURNITURE: Describe the physical background, furniture, and atmosphere in warm detail.
                        2. CHARACTERS & ACTION: Describe the characters interacting naturally in that setting.

                        LESSON:
                        {st.session_state.generated_text[:2500]}
                        """
                        nueva_desc, _ = generar_con_maxima_potencia(client_vis, prompt_nueva_escena)
                        st.session_state.image_bytes = generar_imagen_garantizada(
                            client_vis,
                            nueva_desc,
                            f"Folio {st.session_state.current_folio or 'Lesson'}",
                            st.session_state.selected_cefr,
                            st.session_state.selected_academic_grade
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al generar imagen: {e}")

    bottom_container = st.container(height=280, border=True)
    with bottom_container:
        if st.session_state.get("last_img_error"):
            with st.expander("ℹ️ Detalle técnico del motor de imagen"):
                st.caption(st.session_state["last_img_error"])

        if st.session_state.get("image_bytes"):
            st.image(st.session_state.image_bytes, width="stretch")
        elif st.session_state.get("generated_text"):
            fallback_img = generar_imagen_garantizada(
                None,
                st.session_state.generated_text[:120],
                f"Folio {st.session_state.current_folio}",
                st.session_state.selected_cefr,
                st.session_state.selected_academic_grade
            )
            if fallback_img:
                st.session_state.image_bytes = fallback_img
                st.image(fallback_img, width="stretch")
            else:
                st.caption("Imagen ilustrativa no disponible.")
        else:
            st.caption("La imagen ilustrativa aparecerá aquí / The illustrative image will appear here.")

    if st.session_state.get("current_motivational_quote"):
        mq = st.session_state["current_motivational_quote"]
        st.info(
            f"✨ ***“{mq.get('quote_en', '')}”*** — **{mq.get('author', '')}**\n\n"
            f"🇲🇽 *{mq.get('quote_es', '')}*\n\n"
            f"🎯 **Reflection:** {mq.get('reflection', '')}"
        )

    st.divider()
    st.subheader("🎧 1. Model Pronunciation")
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        safe_audio_name = f"CEI_Audio_{st.session_state.current_folio or usuario.replace(' ', '_')}.mp3"
        st.download_button(
            label="📥 Descargar Audio (MP3)",
            data=st.session_state.audio_bytes,
            file_name=safe_audio_name,
            mime="audio/mp3",
            width="stretch"
        )
    else:
        st.caption("Audio available after generating lesson.")
# ==============================================================================
# PARTE 17A: GRABADORA DE AUDIO Y VIDEO EN NAVEGADOR
# ==============================================================================
    st.divider()
    st.subheader("🎙️ 2. Speaking & Video Practice")
    tab_rec_audio, tab_rec_video = st.tabs(["🎤 Grabar Audio", "📹 Grabar Video"])

    with tab_rec_audio:
        student_audio = st.audio_input("Graba tu voz leyendo el texto:")

    with tab_rec_video:
        st.caption("Activa tu cámara, graba tu lectura y descárgala:")
        safe_base_filename = f"CEI_Video_{st.session_state.current_folio or usuario.replace(' ', '_')}"
        video_recorder_html = f"""
        <div style="font-family: sans-serif; text-align: center; border: 1px solid #ddd; border-radius: 10px; padding: 10px; background: #fafafa;">
            <video id="preview" width="100%" height="175" autoplay muted playsinline style="border-radius: 8px; background: #000; object-fit: cover;"></video>
            <div style="margin-top: 8px; display: flex; gap: 6px; justify-content: center; flex-wrap: wrap;">
                <button id="btnStartCam" style="background:#0d6efd; color:white; border:none; padding:7px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">📷 Activar Cámara</button>
                <button id="btnRec" disabled style="background:#dc3545; color:white; border:none; padding:7px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">⏺️ Grabar</button>
                <button id="btnStop" disabled style="background:#6c757d; color:white; border:none; padding:7px 12px; border-radius:6px; cursor:pointer; font-weight:bold;">⏹️ Detener</button>
            </div>
            <p id="statusTxt" style="font-size: 12px; color: #555; margin: 6px 0;">Presiona "Activar Cámara" para iniciar</p>
            <a id="downloadLink" style="display:none; background:#198754; color:white; text-decoration:none; padding:8px 14px; border-radius:6px; font-weight:bold; font-size:13px; margin-top:4px;">📥 Descargar Video</a>
        </div>

        <script>
        let stream = null;
        let mediaRecorder = null;
        let recordedChunks = [];
        let activeMime = '';

        const preview = document.getElementById('preview');
        const btnStartCam = document.getElementById('btnStartCam');
        const btnRec = document.getElementById('btnRec');
        const btnStop = document.getElementById('btnStop');
        const statusTxt = document.getElementById('statusTxt');
        const downloadLink = document.getElementById('downloadLink');

        function getSupportedVideoMimeType() {{
            const types = [
                'video/mp4;codecs=avc1,mp4a.40.2',
                'video/mp4;codecs=h264,aac',
                'video/mp4',
                'video/webm;codecs=vp9,opus',
                'video/webm;codecs=h264',
                'video/webm'
            ];
            for (const t of types) {{
                if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(t)) return t;
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
                statusTxt.innerText = "Cámara activa. Listo para grabar.";
            }} catch (err) {{
                statusTxt.innerText = "⚠️ Permiso de cámara/micrófono denegado o bloqueado por el navegador.";
            }}
        }};

        btnRec.onclick = () => {{
            recordedChunks = [];
            downloadLink.style.display = 'none';
            activeMime = getSupportedVideoMimeType();
            const options = activeMime ? {{ mimeType: activeMime }} : {{}};
            mediaRecorder = new MediaRecorder(stream, options);

            mediaRecorder.ondataavailable = (e) => {{
                if (e.data.size > 0) recordedChunks.push(e.data);
            }};

            mediaRecorder.onstop = () => {{
                const finalMime = activeMime || 'video/webm';
                const ext = finalMime.includes('mp4') ? 'mp4' : 'webm';
                const blob = new Blob(recordedChunks, {{ type: finalMime }});
                const url = URL.createObjectURL(blob);

                preview.srcObject = null;
                preview.src = url;
                preview.muted = false;
                preview.controls = true;

                downloadLink.href = url;
                downloadLink.download = "{safe_base_filename}." + ext;
                downloadLink.innerText = "📥 Descargar Video (" + ext.toUpperCase() + ")";
                downloadLink.style.display = 'inline-block';
                statusTxt.innerText = "✅ Video grabado. Haz clic abajo para descargarlo.";

                stream.getTracks().forEach(track => track.stop());
                btnStartCam.disabled = false;
                btnStartCam.innerText = "🔄 Grabar Otro";
            }};

            mediaRecorder.start();
            btnRec.disabled = true;
            btnStop.disabled = false;
            statusTxt.innerText = "🔴 Grabando lectura...";
        }};

        btnStop.onclick = () => {{
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            btnStop.disabled = true;
        }};
        </script>
        """
        components.html(video_recorder_html, height=320)
        st.write("")
# ==============================================================================
# PARTE 18: DESCARGA DE AUDIO/PDF Y EVALUACIÓN ORAL CON IA
# ==============================================================================
    if student_audio is not None:
        safe_rec_name = f"CEI_Speaking_{st.session_state.current_folio or usuario.replace(' ', '_')}.mp3"
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
            from pydub import AudioSegment

            wav_buf = io.BytesIO(student_audio.getvalue())
            audio_seg = AudioSegment.from_file(wav_buf, format="wav")
            mp3_buf = io.BytesIO()
            audio_seg.export(mp3_buf, format="mp3", bitrate="128k")
            mp3_data = mp3_buf.getvalue()
            dl_mime = "audio/mp3"
        except Exception:
            mp3_data = student_audio.getvalue()
            safe_rec_name = safe_rec_name.replace(".mp3", ".wav")
            dl_mime = "audio/wav"

        st.download_button(
            label="📥 Descargar Audio Grabado (MP3)",
            data=mp3_data,
            file_name=safe_rec_name,
            mime=dl_mime,
            type="primary",
            width="stretch"
        )

    if st.session_state.get("generated_text"):
        nota_actual_pdf = st.session_state.get("best_stored_score") or st.session_state.get("quiz_score")
        pdf_bytes = create_lesson_pdf(
            st.session_state.generated_text.replace("*", ""),
            quiz_items=st.session_state.quiz_data,
            user_ans=st.session_state.quiz_user_answers,
            score=nota_actual_pdf,
            speaking_eval=st.session_state.get("speaking_eval_result")
        )
        st.download_button(
            label=f"📥 Descargar PDF Oficial ({st.session_state.current_folio or 'Lección'})",
            data=pdf_bytes,
            file_name=f"{st.session_state.current_folio or 'CEI_Lesson'}_{usuario.replace(' ', '_')}.pdf",
            mime="application/pdf",
            width="stretch",
            key="btn_dl_pdf_sidebar_right"
        )
    else:
        st.button("📥 Descargar PDF Oficial", disabled=True, width="stretch", key="btn_dl_pdf_disabled")

    if student_audio is not None:
        if st.button("🧠 Evaluar Pronunciación y Gramática Oral con IA", type="secondary", width="stretch"):
            if not st.session_state.generated_text:
                st.warning("⚠️ Primero genera o carga una lección para comparar tu lectura.")
            else:
                with st.spinner("🎙️ Analizando fonética, entonación y gramática oral..."):
                    try:
                        eval_res = evaluar_pronunciacion_ia(
                            audio_bytes=student_audio.getvalue(),
                            mime_type="audio/wav",
                            texto_objetivo=st.session_state.generated_text,
                            gramatica_obj=gramatica_b1,
                            nivel_cefr=st.session_state.selected_cefr,
                            grado_acad=st.session_state.selected_academic_grade
                        )
                        st.session_state["speaking_eval_result"] = eval_res
                        if st.session_state.current_folio and "score_percent" in eval_res:
                            save_best_speaking_pg(st.session_state.current_folio, int(eval_res["score_percent"]))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en evaluación oral: {e}")

    if st.session_state.get("speaking_eval_result"):
        ev = st.session_state["speaking_eval_result"]
        with st.container(border=True):
            st.markdown(f"#### 🎯 Evaluación Oral: **{ev.get('score_percent', 0)}%** ({ev.get('cefr_performance', '')})")
            st.caption(f"🗣️ **Transcripción detectada:** *\"{ev.get('transcription', '')}\"*")
            st.markdown(f"**🔤 Fonética y Articulación:** {ev.get('phonetic_feedback', '')}")
            st.markdown(f"**🎵 Fluidez y Prosodia:** {ev.get('fluency_prosody', '')}")
            st.markdown(f"**📐 Precisión Gramatical Oral:** {ev.get('grammar_accuracy', '')}")
            tips = ev.get("actionable_tips", [])
            if tips:
                st.markdown("**💡 Recomendaciones de Mejora:**")
                for t in tips:
                    st.markdown(f"- {t}")
# ==============================================================================
# PARTE 18A (FINAL): HISTORIAL DE FOLIOS, BORRAR TODO Y PIE DE PÁGINA
# ==============================================================================
    st.divider()
    if st.button("📂 Ver Folios y Calificaciones Guardadas", width="stretch"):
        st.session_state.show_saved_audios = not st.session_state.show_saved_audios

    if st.session_state.show_saved_audios:
        with st.container(height=360, border=True):
            st.markdown("**Historial de Folios y Calificaciones (Supabase):**")
            try:
                records = load_lessons_history_pg()
                if not records:
                    st.info("Aún no hay registros guardados en Supabase.")
                else:
                    df = pd.DataFrame(records)

                    if has_faculty_access or is_owner:
                        padron_regs = load_padron_records()
                        inscritos_padron = [
                            str(r.get("Usuario", "")).strip()
                            for r in padron_regs if str(r.get("Usuario", "")).strip()
                        ]
                        usuarios_en_folios = [
                            str(u).strip() for u in df["Usuario"].dropna().unique().tolist() if str(u).strip()
                        ]
                        lista_inscritos = sorted(list(set(inscritos_padron + usuarios_en_folios)))

                        alumno_filtro = st.selectbox(
                            "👤 Filtrar por Estudiante / Inscrito:",
                            ["Todos los inscritos"] + lista_inscritos,
                            key="sel_filtro_inscrito_historial"
                        )
                        if alumno_filtro != "Todos los inscritos":
                            df = df[df["Usuario"].astype(str).str.strip().str.lower() == alumno_filtro.lower()]
                    else:
                        df = df[df["Usuario"].astype(str).str.strip().str.lower() == usuario.strip().lower()]

                    if df.empty:
                        st.warning("No se encontraron folios registrados para este usuario.")
                    else:
                        limite_ver = 10 if ((has_faculty_access or is_owner) and alumno_filtro != "Todos los inscritos") else 5
                        for idx_h, row in df.head(limite_ver).iterrows():
                            folio_item = str(row.get("Folio", "S/F")).strip()
                            st.caption(f"🔖 **{folio_item}** | 👤 **{row.get('Usuario', '')}** | 📅 {row.get('Fecha_de_subida', '')}")
                            st.caption(f"📘 *{row.get('Tema', '')}*")

                            mejor_nota_row = str(row.get("Mejor_Calificacion_PDF") or "").strip()
                            speaking_row = row.get("Speaking_Score")
                            if mejor_nota_row:
                                st.caption(f"🏆 **Mejor Quiz:** `{mejor_nota_row}`")
                            if speaking_row is not None and float(speaking_row) > 0:
                                st.caption(f"🎙️ **Mejor Evaluación Oral:** `{int(float(speaking_row))}%`")

                            if st.button(f"📖 Cargar Lección ({folio_item})", key=f"load_fol_{folio_item}_{idx_h}", width="stretch"):
                                st.session_state.generated_text = str(row.get("Texto", ""))
                                st.session_state.current_folio = folio_item
                                st.session_state.selected_cefr = normalize_cefr(row.get("Nivel_CEFR", "B1"))
                                st.session_state.selected_academic_grade = str(row.get("Grado_Academico", "Licenciatura / Universidad"))
                                st.session_state.study_mode_active = False
                                st.session_state.quiz_graded = False
                                st.session_state.quiz_score = None
                                st.session_state.quiz_user_answers = {}
                                st.session_state.image_bytes = None
                                st.session_state.current_motivational_quote = None
                                st.session_state.speaking_eval_result = row.get("Speaking_Eval")
                                st.session_state["best_stored_score"] = mejor_nota_row

                                raw_qz = row.get("Quiz_JSON")
                                if isinstance(raw_qz, list):
                                    st.session_state.quiz_data = raw_qz
                                elif isinstance(raw_qz, dict):
                                    st.session_state.quiz_data = raw_qz.get("questions")
                                elif isinstance(raw_qz, str) and raw_qz.strip():
                                    try:
                                        qz_obj = json.loads(raw_qz)
                                        st.session_state.quiz_data = qz_obj if isinstance(qz_obj, list) else qz_obj.get("questions")
                                    except Exception:
                                        st.session_state.quiz_data = None
                                else:
                                    st.session_state.quiz_data = None
                                st.rerun()

                            st.divider()
            except Exception as e:
                st.error(f"Error al cargar historial desde Supabase: {e}")

    st.divider()

    if st.button("🗑️ Borrar Todo", type="secondary", width="stretch"):
        st.session_state.generated_text = ""
        st.session_state.study_mode_active = False
        st.session_state.image_bytes = None
        st.session_state.current_lesson_image = None
        st.session_state.current_motivational_quote = None
        st.session_state.last_img_error = None
        st.session_state.audio_bytes = None
        st.session_state.quiz_audio_bytes = None
        st.session_state.speaking_eval_result = None
        st.session_state.show_saved_audios = False
        st.session_state.quiz_data = None
        st.session_state.quiz_graded = False
        st.session_state.quiz_score = None
        st.session_state.quiz_user_answers = {}
        st.session_state.current_folio = ""
        st.session_state.current_pdf_link = ""
        st.session_state.current_creation_date = ""
        st.session_state.url_folio_checked = False
        st.session_state["best_stored_score"] = ""
        st.query_params.clear()
        st.session_state.sidebar_state = "expanded"
        st.rerun()

# --- 18. PIE DE PÁGINA INSTITUCIONAL ---
st.divider()
footer_html = (
    "<div style='text-align: center; color: #777; font-size: 13px; margin-top: 20px;'>"
    "📍 <b>" + str(institute_address) + "</b><br>"
    "© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti"
    "</div>"
)
st.markdown(footer_html, unsafe_allow_html=True)
