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
import urllib.parse
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
import pandas as pd
from streamlit_js_eval import streamlit_js_eval
from google.oauth2.service_account import Credentials


# --- 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO) ---
st.set_page_config(
    page_title="CEFR Academic Grammar & Discourse System - Career English Institute",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CONFIGURACIÓN SEGURA DESDE SECRETS ---
DEFAULT_ADDRESS = st.secrets.get(
    "INSTITUTE_ADDRESS",
    "Dirección no configurada | Tel. / Contacto: No disponible"
)

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

# --- 3. CLIENTES EN CACHÉ (GEMINI Y GOOGLE SHEETS) ---
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
    """Inicializa el cliente oficial de Google Gemini leyendo la clave desde cualquier nivel de Secrets."""
    from google import genai
    api_key = str(
        st.secrets.get("GEMINI_API_KEY", "")
        or next((sec["GEMINI_API_KEY"] for sec in st.secrets.values() if isinstance(sec, dict) and "GEMINI_API_KEY" in sec), "")
    ).strip()
    if not api_key:
        st.warning("⚠️ GEMINI_API_KEY no configurada en Secrets.")
        return None
    return genai.Client(api_key=api_key)

client = init_gemini_client()



@st.cache_resource
def get_gspread_client():
    if "gcp_service_account" not in st.secrets:
        st.error("Falta configurar [gcp_service_account] en los Secrets de Streamlit.")
        st.stop()
    creds_dict = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(creds_dict)

@st.cache_resource
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
    except gspread.WorksheetNotFound:
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
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title="Matriz_Permisos", rows=50, cols=9)
        ws.append_row(["Perfil_Permiso"] + CAPABILITY_COLS)
        for fila in DEFAULT_PERMISSIONS_MATRIX:
            fila_sheets = [fila[0]] + ["SI" if val is True or str(val).upper() == "SI" else "NO" for val in fila[1:]]
            ws.append_row(fila_sheets)
        return ws


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


# --- 4. COMPRESIÓN Y GESTIÓN DE IMÁGENES ---
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

def save_permanent_config(logo_b64: str, mime_type: str, width: int, shape: str, direccion: str):
    """Guarda el logotipo en Base64 (sin límite de 50k caracteres) y la dirección oficial en PostgreSQL."""
    conn = get_pg_conn()
    if not conn:
        raise RuntimeError("Sin conexión activa a PostgreSQL.")
    with conn:
        with conn.cursor() as cur:
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
                str(direccion or DEFAULT_INSTITUTE_ADDRESS)
            ))
    load_permanent_logo.clear()


@st.cache_resource(show_spinner=False)
def get_google_workbook():
    """Conecta con Google Sheets forzando el endpoint oficial OAuth2."""
    from google.oauth2 import service_account
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
    sheet_url = str(st.secrets.get("GOOGLE_SHEET_URL", "")).strip()
    if sheet_url:
        return gc.open_by_url(sheet_url)
    sheet_name = str(st.secrets.get("GOOGLE_SHEET_NAME", "CEI_Database")).strip()
    return gc.open(sheet_name)



def get_google_sheet():
    """Devuelve la Hoja 1 (Folios y Lecciones) del libro de Google Sheets."""
    return get_google_workbook().sheet1


def get_pg_conn():
    """Conecta a PostgreSQL (Supabase) buscando credenciales en cualquier nivel de Secrets."""
    import psycopg

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
    if db_url.startswith("postgres") and "@" in db_url and "://supabase.com" in db_url:
        return psycopg.connect(db_url, sslmode="require", prepare_threshold=None)

    raise ValueError(
        f"No se encontraron las credenciales de Supabase en Secrets "
        f"(PG_HOST={'OK' if pg_host else 'VACIO'}, PG_USER={'OK' if pg_user else 'VACIO'}, PG_PASSWORD={'OK' if pg_pass else 'VACIO'})."
    )



@st.cache_data(ttl=60, show_spinner=False)
def load_permanent_logo():
    """Carga la configuración institucional desde PostgreSQL."""
    from psycopg.rows import dict_row
    try:
        conn = get_pg_conn()
        if conn:
            with conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("SELECT * FROM institute_config WHERE id = 1;")
                    row = cur.fetchone()
                    if row:
                        return {
                            "Logo_Base64": row.get("logo_base64") or "",
                            "Mime_Type": row.get("mime_type") or "image/png",
                            "Width": row.get("logo_width") or 115,
                            "Shape": row.get("logo_shape") or "Circular",
                            "Direccion": row.get("direccion") or DEFAULT_INSTITUTE_ADDRESS
                        }
    except Exception:
        pass
    return None


@st.cache_data(ttl=60, show_spinner=False)
def load_permissions_matrix() -> dict:
    """Carga la matriz RBAC desde PostgreSQL (Supabase) con respaldo seguro."""
    from psycopg.rows import dict_row
    fallback_matrix = {
        "Total": {c: True for c in CAPABILITY_COLS},
        "Docente": {
            "Generar_Leccion": True, "Resolver_Quiz": True, "Grabar_Audio": True,
            "Emitir_Certificados": True, "Revocar_Certificados": True,
            "Registrar_Usuarios": True, "Gestionar_Usuarios": True,
            "Ver_Panel_Admin": True, "Editar_Permisos": False, "Editar_Instituto_Logo": False
        },
        "Basico": {
            "Generar_Leccion": True, "Resolver_Quiz": True, "Grabar_Audio": True,
            "Emitir_Certificados": False, "Revocar_Certificados": False,
            "Registrar_Usuarios": False, "Gestionar_Usuarios": False,
            "Ver_Panel_Admin": False, "Editar_Permisos": False, "Editar_Instituto_Logo": False
        }
    }
    try:
        conn = get_pg_conn()
        if conn:
            with conn:
                with conn.cursor(row_factory=dict_row) as cur:
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
                                matrix[prof] = {k: bool(v) for k, v in caps_j.items()}
                            else:
                                matrix[prof] = {
                                    "Generar_Leccion": bool(r.get("generar_leccion", True)),
                                    "Resolver_Quiz": bool(r.get("resolver_quiz", True)),
                                    "Grabar_Audio": bool(r.get("grabar_audio", True)),
                                    "Emitir_Certificados": bool(r.get("emitir_certificados", False)),
                                    "Revocar_Certificados": bool(r.get("emitir_certificados", False)),
                                    "Registrar_Usuarios": bool(r.get("gestionar_usuarios", False)),
                                    "Gestionar_Usuarios": bool(r.get("gestionar_usuarios", False)),
                                    "Ver_Panel_Admin": bool(r.get("gestionar_usuarios", False)),
                                    "Editar_Permisos": bool(r.get("editar_instituto_logo", False)),
                                    "Editar_Instituto_Logo": bool(r.get("editar_instituto_logo", False))
                                }
                        if matrix:
                            return matrix
    except Exception:
        pass
    return fallback_matrix


    if isinstance(DEFAULT_PERMISSIONS_MATRIX, dict):
        return DEFAULT_PERMISSIONS_MATRIX.copy()
    return {
        "Total": {"Generar_Leccion": True, "Resolver_Quiz": True, "Grabar_Audio": True, "Emitir_Certificados": True, "Gestionar_Usuarios": True, "Editar_Instituto_Logo": True},
        "Docente": {"Generar_Leccion": True, "Resolver_Quiz": True, "Grabar_Audio": True, "Emitir_Certificados": True, "Gestionar_Usuarios": True, "Editar_Instituto_Logo": False},
        "Basico": {"Generar_Leccion": True, "Resolver_Quiz": True, "Grabar_Audio": True, "Emitir_Certificados": False, "Gestionar_Usuarios": False, "Editar_Instituto_Logo": False},
        "Solo_Lectura": {"Generar_Leccion": False, "Resolver_Quiz": True, "Grabar_Audio": False, "Emitir_Certificados": False, "Gestionar_Usuarios": False, "Editar_Instituto_Logo": False}
    }


@st.cache_data(ttl=60)
def load_padron_records() -> list[dict]:
    from psycopg.rows import dict_row
    conn = get_pg_conn()
    if not conn:
        return []
    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
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
                    COALESCE(aff.matricula || ' — ' || aff.usuario, 'Directo / Sin afiliador') AS afiliador_nombre
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



    # 2. Intentar Google Sheets (Respaldo)
    try:
        ws_pad = get_google_workbook().worksheet("Padron")
        recs = ws_pad.get_all_records()
        if recs:
            return recs
        st.session_state["db_auth_diag"] += "Google Sheets: pestaña Padron vacía."
    except Exception as e_gs:
        st.session_state["db_auth_diag"] += f"Google Sheets Error: {e_gs}"

    return []



    # Respaldo automático en Google Sheets mientras se completa la migración a Supabase
    try:
        ws_pad = get_google_workbook().worksheet("Padron")
        return ws_pad.get_all_records()
    except Exception:
        return []


def fetch_lesson_by_folio(folio_code: str) -> dict | None:
    """Recupera una lección, su quiz y su mejor calificación desde PostgreSQL."""
    from psycopg.rows import dict_row
    folio_clean = str(folio_code or "").strip().upper()
    if not folio_clean:
        return None
    try:
        conn = get_pg_conn()
        if conn:
            with conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("""
                        SELECT f.*, u.usuario
                        FROM lessons_folios f
                        JOIN users_padron u ON f.user_id = u.id
                        WHERE UPPER(f.folio) = %s;
                    """, (folio_clean,))
                    r = cur.fetchone()
                    if r:
                        q_raw = r.get("quiz_data")
                        ans_raw = r.get("best_quiz_answers")
                        spk_raw = r.get("speaking_eval_json")
                        c_at = r.get("created_at")
                        return {
                            "Folio": r.get("folio"),
                            "Usuario": r.get("usuario"),
                            "Tema": r.get("tema"),
                            "CEFR": r.get("cefr_level"),
                            "Grade": r.get("academic_grade"),
                            "Text": r.get("lesson_text"),
                            "Quiz": q_raw if isinstance(q_raw, list) else (json.loads(q_raw) if q_raw else None),
                            "Best_Score": r.get("best_quiz_score") or "",
                            "Best_Answers": ans_raw if isinstance(ans_raw, dict) else (json.loads(ans_raw) if ans_raw else {}),
                            "Speaking_Score": float(r.get("best_speaking_score")) if r.get("best_speaking_score") is not None else -1.0,
                            "Speaking_Eval": spk_raw if isinstance(spk_raw, dict) else (json.loads(spk_raw) if spk_raw else None),
                            "PDF_Link": r.get("pdf_link") or "",
                            "Created_At": c_at.strftime("%Y-%m-%d %H:%M:%S") if c_at else ""
                        }
    except Exception:
        pass
    return None


def get_default_logo_b64():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "LOGO CEI APP.png")
    try:
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8"), "image/png"
    except Exception:
        return None, None
        
# --- 5. MOTOR DE TIMBRADO CRIPTOGRÁFICO (HMAC-SHA256) Y CERTIFICADO PDF ---
def fetch_student_gradebook_pg(target_usuario: str) -> dict:
    """Calcula en tiempo real el promedio general, desglose por Grammar Topic e historial de lecciones desde Supabase."""
    import re
    from psycopg.rows import dict_row

    conn = get_pg_conn()
    if not conn:
        return {"records": [], "topic_summary": [], "overall_avg": 0.0, "quiz_avg": 0.0, "oral_avg": 0.0}

    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    l.folio,
                    l.tema,
                    COALESCE(NULLIF(TRIM(l.grammar_topic), ''), 'General Applied Grammar') AS grammar_topic,
                    l.nivel_cefr,
                    l.best_score,
                    COALESCE(l.speaking_score, 0) AS speaking_score,
                    TO_CHAR(l.created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS fecha
                FROM lessons_archive l
                JOIN users_padron u ON l.user_id = u.id
                WHERE LOWER(TRIM(u.usuario)) = LOWER(TRIM(%s))
                ORDER BY l.created_at DESC;
            """, (target_usuario.strip(),))
            rows = cur.fetchall()

    def _parse_quiz_pct(score_str: str) -> float | None:
        m = re.search(r"\((\d+(?:\.\d+)?)%\)", str(score_str or ""))
        return float(m.group(1)) if m else None

    registros_procesados = []
    por_tema = {}
    todas_quiz = []
    todas_oral = []
    todas_combinadas = []

    for r in rows:
        q_pct = _parse_quiz_pct(r.get("best_score"))
        o_raw = float(r.get("speaking_score") or 0)
        o_pct = o_raw if o_raw > 0 else None

        notas_item = [x for x in [q_pct, o_pct] if x is not None]
        prom_leccion = round(sum(notas_item) / len(notas_item), 1) if notas_item else None

        if q_pct is not None:
            todas_quiz.append(q_pct)
        if o_pct is not None:
            todas_oral.append(o_pct)
        if prom_leccion is not None:
            todas_combinadas.append(prom_leccion)

        g_topic = str(r.get("grammar_topic") or "General Applied Grammar").strip()
        if g_topic not in por_tema:
            por_tema[g_topic] = {"scores": [], "lecciones": 0}
        por_tema[g_topic]["lecciones"] += 1
        if prom_leccion is not None:
            por_tema[g_topic]["scores"].append(prom_leccion)

        registros_procesados.append({
            "Folio": r.get("folio", ""),
            "Fecha": r.get("fecha", ""),
            "Nivel": r.get("nivel_cefr", ""),
            "Grammar_Topic": g_topic,
            "Tema_Leccion": r.get("tema", ""),
            "Quiz_Pct": f"{q_pct}%" if q_pct is not None else "Pendiente",
            "Oral_Pct": f"{o_pct}%" if o_pct is not None else "Pendiente",
            "Promedio_Leccion": f"{prom_leccion}%" if prom_leccion is not None else "Sin evaluar"
        })

    resumen_temas = []
    for topic_name, info in por_tema.items():
        avg_t = round(sum(info["scores"]) / len(info["scores"]), 1) if info["scores"] else 0.0
        resumen_temas.append({
            "Grammar Topic": topic_name,
            "Dominio (%)": avg_t,
            "Lecciones": info["lecciones"]
        })

    resumen_temas.sort(key=lambda x: x["Dominio (%)"], reverse=True)

    return {
        "records": registros_procesados,
        "topic_summary": resumen_temas,
        "overall_avg": round(sum(todas_combinadas) / len(todas_combinadas), 1) if todas_combinadas else 0.0,
        "quiz_avg": round(sum(todas_quiz) / len(todas_quiz), 1) if todas_quiz else 0.0,
        "oral_avg": round(sum(todas_oral) / len(todas_oral), 1) if todas_oral else 0.0
    }

        
def fetch_certificate_public_pg(folio_cert: str) -> dict | None:
    """Busca un certificado por su folio directamente en PostgreSQL para verificación QR sin login."""
    from psycopg.rows import dict_row
    conn = get_pg_conn()
    if not conn:
        return None
    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM certificates WHERE UPPER(folio_cert) = %s LIMIT 1;",
                (str(folio_cert).strip().upper(),)
            )
            return cur.fetchone()

def save_quiz_and_best_score_pg(folio: str, nota_actual: str, quiz_items: list, user_ans: dict) -> tuple[bool, str, str]:
    """Guarda el quiz y conserva la mejor calificación del folio directamente en Supabase PostgreSQL."""
    import re
    conn = get_pg_conn()
    if not conn:
        return False, "Sin conexión activa a PostgreSQL.", nota_actual

    def _extract_pct(txt: str) -> float:
        m = re.search(r"\((\d+(?:\.\d+)?)%\)", str(txt or ""))
        return float(m.group(1)) if m else -1.0

    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT quiz_json, best_score FROM lessons_archive WHERE folio = %s LIMIT 1;", (folio.strip(),))
            row = cur.fetchone()
            nota_previa = str(row[1] or "").strip() if row else ""

            pct_nuevo = _extract_pct(nota_actual)
            pct_previo = _extract_pct(nota_previa)

            if pct_nuevo >= pct_previo:
                mejor_final = nota_actual
                es_record = True
                msg = f"🏆 ¡Nueva mejor calificación guardada en Supabase para el folio `{folio}`: **{mejor_final}**!"
            else:
                mejor_final = nota_previa
                es_record = False
                msg = f"ℹ️ Se conserva tu calificación más alta previa en Supabase: **{mejor_final}** (intento actual: {nota_actual})."

            payload_quiz = json.dumps({"questions": quiz_items, "user_answers": user_ans}, ensure_ascii=False)
            cur.execute(
                "UPDATE lessons_archive SET quiz_json = %s, best_score = %s WHERE folio = %s;",
                (payload_quiz, mejor_final, folio.strip())
            )
    return es_record, msg, mejor_final

def save_best_speaking_pg(folio: str, score_pct: int):
    """Guarda o actualiza la mejor calificación de pronunciación oral en Supabase PostgreSQL."""
    conn = get_pg_conn()
    if not conn:
        return
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE lessons_archive
                SET speaking_score = GREATEST(COALESCE(speaking_score, 0), %s)
                WHERE folio = %s;
            """, (int(score_pct), folio.strip()))


def load_lessons_history_pg() -> list[dict]:
    """Carga el historial de lecciones, folios y calificaciones desde Supabase PostgreSQL."""
    from psycopg.rows import dict_row
    conn = get_pg_conn()
    if not conn:
        return []
    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    l.folio AS "Folio",
                    COALESCE(u.usuario, 'Usuario') AS "Usuario",
                    l.tema AS "Tema",
                    l.nivel_cefr AS "Nivel_CEFR",
                    l.grado_academico AS "Grado_Academico",
                    l.lesson_text AS "Texto",
                    l.quiz_json AS "Quiz_JSON",
                    l.best_score AS "Mejor_Calificacion_PDF",
                    l.speaking_score AS "Speaking_Score",
                    l.pdf_link AS "PDF_Link",
                    TO_CHAR(l.created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS "Fecha_de_subida"
                FROM lessons_archive l
                LEFT JOIN users_padron u ON l.user_id = u.id
                ORDER BY l.created_at DESC
                LIMIT 100;
            """)
            return cur.fetchall()


def clean_pdf_text(text: str) -> str:
    """Normaliza comillas, guiones y caracteres especiales para compatibilidad segura con FPDF."""
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

def generar_sello_digital(folio_cert: str, clave_est: str, nombre_est: str, nivel_cefr: str, fecha_emision: str):
    llave_secreta = str(
        st.secrets.get("HMAC_SECRET_KEY", st.secrets.get("spreadsheet_key", "CEI-2026-MASTER-SEAL"))
    ).encode("utf-8")
    cadena_original = f"||CEI|{folio_cert}|{clave_est}|{nombre_est}|{nivel_cefr}|{fecha_emision}|JACOB-ZUMAYA-PRIANTI||"
    sello_hex = hmac.new(llave_secreta, cadena_original.encode("utf-8"), hashlib.sha256).hexdigest().upper()
    return cadena_original, sello_hex

def _safe_latin1(text: str) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")

class AcademicPDF(FPDF):
    """Plantilla editorial de Alta Escuela con encabezado institucional y numeración Page X of Y."""
    def __init__(self, folio_doc: str, cefr_doc: str, grado_doc: str, address_str: str):
        super().__init__()
        self.folio_doc = folio_doc
        self.cefr_doc = cefr_doc
        self.grado_doc = grado_doc
        self.address_str = address_str

    def header(self):
        # Línea superior institucional en todas las páginas
        self.set_y(10)
        self.set_font("Times", "B", 8.5)
        self.set_text_color(11, 37, 69)
        self.cell(self.epw * 0.65, 5, text=_safe_latin1("CAREER ENGLISH INSTITUTE  |  APPLIED LINGUISTICS & DISCOURSE"), align="L")
        self.set_font("Times", "I", 8.5)
        self.set_text_color(100, 100, 100)
        cefr_short = next(iter(self.cefr_doc.split()), "CEFR") if self.cefr_doc else "CEFR"
        self.cell(self.epw * 0.35, 5, text=_safe_latin1(f"Folio: {self.folio_doc}  |  CEFR {cefr_short}"), new_x="LMARGIN", new_y="NEXT", align="R")
        
        # Doble filete editorial (azul marino + dorado)
        y_line = self.get_y() + 1
        self.set_draw_color(11, 37, 69)
        self.set_line_width(0.6)
        self.line(self.l_margin, y_line, self.w - self.r_margin, y_line)
        self.set_draw_color(184, 134, 11)
        self.set_line_width(0.25)
        self.line(self.l_margin, y_line + 1.2, self.w - self.r_margin, y_line + 1.2)
        self.set_y(y_line + 5)

    def footer(self):
        # Pie de página institucional con numeración Page X of Y
        self.set_y(-16)
        y_f = self.get_y()
        self.set_draw_color(184, 134, 11)
        self.set_line_width(0.3)
        self.line(self.l_margin, y_f, self.w - self.r_margin, y_f)
        self.ln(2)
        
        self.set_font("Times", "I", 8)
        self.set_text_color(90, 90, 90)
        self.cell(self.epw * 0.75, 4, text=_safe_latin1("© 2026 CAREER ENGLISH INSTITUTE  |  Author: Jacob Zumaya Prianti  |  APA 7th Ed. Standard"), align="L")
        self.set_font("Times", "B", 8.5)
        self.set_text_color(11, 37, 69)
        self.cell(self.epw * 0.25, 4, text=f"Page {self.page_no()} of {{nb}}", new_x="LMARGIN", new_y="NEXT", align="R")
        
        self.set_x(self.l_margin)
        self.set_font("Times", "", 7.5)
        self.set_text_color(110, 110, 110)
        self.cell(self.epw, 4, text=_safe_latin1(self.address_str), align="C")


def create_lesson_pdf(text: str, quiz_items=None, user_ans=None, score=None, speaking_eval=None) -> bytes:
    """Genera un documento académico de Alta Escuela con numeración de páginas, ilustración y examen."""
    folio_doc = st.session_state.current_folio or "SIN-FOLIO"
    base_url = st.secrets.get("APP_BASE_URL", "https://streamlit.app").rstrip("/")
    link_doc = st.session_state.current_pdf_link or f"{base_url}/?folio={urllib.parse.quote(folio_doc)}"
    
    ahora_local = datetime.now(ZoneInfo("America/Hermosillo"))
    fecha_doc = st.session_state.current_creation_date or ahora_local.strftime("%Y-%m-%d %H:%M:%S")
    grado_doc = st.session_state.selected_academic_grade
    usuario_doc = st.session_state.current_user
    rol_doc = st.session_state.user_role
    cefr_doc = st.session_state.selected_cefr
    
    pdf = AcademicPDF(folio_doc, cefr_doc, grado_doc, institute_address)
    pdf.alias_nb_pages()  # Activa el conteo total de páginas {nb}
    pdf.set_margins(left=18, top=22, right=18)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_author("Jacob Zumaya Prianti")
    pdf.set_creator("Career English Institute - Academic Press")
    pdf.add_page()
    
    # --- PORTADA / MEMBRETE DE ALTA ESCUELA EN PÁGINA 1 ---
    y_box_start = pdf.get_y()
    pdf.set_fill_color(244, 247, 251)
    pdf.set_draw_color(11, 37, 69)
    pdf.set_line_width(0.4)
    pdf.rect(pdf.l_margin, y_box_start, pdf.epw, 42, style="FD")
    
    # Barra lateral dorada decorativa en la ficha técnica
    pdf.set_fill_color(184, 134, 11)
    pdf.rect(pdf.l_margin, y_box_start, 2.5, 42, style="F")

    # Logotipo institucional dentro de la ficha si está disponible
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
    pdf.cell(w_meta, 5, text=_safe_latin1(f"CEFR {cefr_doc}  |  {grado_doc.upper()}  |  ACADEMIC MONOGRAPH"), new_x="LMARGIN", new_y="NEXT", align="L")
    
    pdf.set_x(x_meta)
    pdf.set_font("Times", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(w_meta, 5, text=_safe_latin1("Author & Senior Applied Linguist: Jacob Zumaya Prianti"), new_x="LMARGIN", new_y="NEXT", align="L")
    
    pdf.set_x(x_meta)
    pdf.cell(w_meta, 5, text=_safe_latin1(f"Student / Candidate: {usuario_doc} ({rol_doc})  |  Date: {fecha_doc}"), new_x="LMARGIN", new_y="NEXT", align="L")
    
    pdf.set_x(x_meta)
    pdf.set_font("Times", "U", 8)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(w_meta, 5, text=_safe_latin1(f"Digital Verification & Recovery: {link_doc}"), new_x="LMARGIN", new_y="NEXT", align="L", link=link_doc)

    pdf.set_y(y_box_start + 48)

    pdf.set_y(y_box_start + 48)

    # --- CUADRO DE CALIFICACIÓN DE LA LECCIÓN, TÓPICO Y PROMEDIO GENERAL ---
    try:
        topico_lec_pdf = (
            st.session_state.get("selected_grammar_topic")
            or (gramatica_b1 if "gramatica_b1" in globals() else "Applied Grammar")
        )
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

        # Acento dorado izquierdo a juego con el membrete
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
        pdf.cell(pdf.epw - 8, 7, text=_safe_latin1(resumen_notas_txt), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_y(y_perf + 17)
    except Exception:
        pass


    # --- ILUSTRACIÓN ESCÉNICA CON MARCO EDITORIAL ---
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
            pdf.image(img_buf, x=x_img, y=y_img, w=img_w)
            pdf.set_draw_color(11, 37, 69)
            pdf.set_line_width(0.5)
            pdf.rect(x_img, y_img, img_w, img_h)
            pdf.set_y(y_img + img_h + 2)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Times", "I", 8.5)
            pdf.set_text_color(90, 90, 90)
            pdf.cell(pdf.epw, 4, text=_safe_latin1(f"Figure 1. Visual Discourse Context & Situational Dialogue — Folio {folio_doc}."), new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(4)
        except Exception:
            pdf.ln(3)

    # --- CUERPO ACADÉMICO DE LA LECCIÓN ---
    pdf.set_text_color(25, 25, 25)
    for parrafo in text.split("\n"):
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
            pdf.multi_cell(pdf.epw, 6.5, text=_safe_latin1(titulo_limpio), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")
            pdf.set_text_color(25, 25, 25)
        else:
            pdf.set_font("Times", size=11)
            pdf.multi_cell(pdf.epw, 6.2, text=_safe_latin1(p_clean), new_x="LMARGIN", new_y="NEXT", align="J", wrapmode="CHAR")

    # --- SECCIÓN DE EVALUACIÓN Y CALIFICACIÓN ---
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
        pdf.cell(pdf.epw - 6, 6, text=_safe_latin1(f"OFFICIAL ASSESSMENT & GRAMMAR EVALUATION  |  FOLIO: {folio_doc}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        if score:
            y_sc = pdf.get_y()
            pdf.set_fill_color(253, 248, 232)
            pdf.set_draw_color(184, 134, 11)
            pdf.rect(pdf.l_margin, y_sc, pdf.epw, 8, style="FD")
            pdf.set_xy(pdf.l_margin + 3, y_sc + 1.5)
            pdf.set_font("Times", "B", 10.5)
            pdf.set_text_color(11, 37, 69)
            pdf.cell(pdf.epw - 6, 5, text=_safe_latin1(f"FINAL EVALUATION SCORE / CALIFICACION OBTENIDA: {score}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        pdf.set_text_color(25, 25, 25)
        for i, q in enumerate(quiz_items):
            if pdf.get_y() > pdf.h - 45:
                pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Times", "B", 10.5)
            pdf.multi_cell(pdf.epw, 6, text=_safe_latin1(f"{i+1}. {q.get('question', '')}"), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")
            
            pdf.set_font("Times", size=10)
            for opt in q.get("options", []):
                pdf.set_x(pdf.l_margin + 6)
                pdf.multi_cell(pdf.epw - 6, 5.2, text=_safe_latin1(str(opt)), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")
                
            u_choice = user_ans.get(i) if user_ans else "None"
            ans_line = f"Candidate Response: {u_choice or 'None'}   |   Verified Key: {q.get('answer', '')}"
            pdf.set_x(pdf.l_margin + 6)
            pdf.set_font("Times", "I", 9.5)
            pdf.set_text_color(11, 37, 69)
            pdf.multi_cell(pdf.epw - 6, 5.5, text=_safe_latin1(ans_line), new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR")
            pdf.set_text_color(25, 25, 25)
            pdf.ln(3)
    # --- SECCIÓN DE EVALUACIÓN ORAL Y ANÁLISIS FONÉTICO (SI EXISTE) ---
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
        pdf.cell(pdf.epw - 6, 6, text=_safe_latin1(f"ORAL PROFICIENCY & PHONETIC ASSESSMENT REPORT  |  FOLIO: {folio_doc}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Recuadro con calificación oral y nivel CEFR alcanzado
        y_sp_sc = pdf.get_y()
        pdf.set_fill_color(253, 248, 232)
        pdf.set_draw_color(184, 134, 11)
        pdf.rect(pdf.l_margin, y_sp_sc, pdf.epw, 8, style="FD")
        pdf.set_xy(pdf.l_margin + 3, y_sp_sc + 1.5)
        pdf.set_font("Times", "B", 10.5)
        pdf.set_text_color(11, 37, 69)
        spk_pct = speaking_eval.get("score_percent", 0)
        spk_perf = speaking_eval.get("cefr_performance", "")
        pdf.cell(pdf.epw - 6, 5, text=_safe_latin1(f"SPEAKING SCORE: {spk_pct}%  |  CEFR BENCHMARK: {spk_perf}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        pdf.set_text_color(25, 25, 25)
        campos_orales = [
            ("Detected Speech Transcription:", f"\"{speaking_eval.get('transcription', '')}\""),
            ("Phonetics & Articulation Feedback:", speaking_eval.get("phonetic_feedback", "")),
            ("Fluency & Prosody:", speaking_eval.get("fluency_prosody", "")),
            ("Oral Grammar Accuracy:", speaking_eval.get("grammar_accuracy", ""))
        ]

        for etiqueta, contenido in campos_orales:
            if not contenido.strip():
                continue
            if pdf.get_y() > pdf.h - 30:
                pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Times", "B", 10)
            pdf.set_text_color(11, 37, 69)
            pdf.cell(pdf.epw, 5.5, text=_safe_latin1(etiqueta), new_x="LMARGIN", new_y="NEXT")

            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("Times", "I" if "Transcription" in etiqueta else "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(pdf.epw - 4, 5.5, text=_safe_latin1(contenido), new_x="LMARGIN", new_y="NEXT", align="J", wrapmode="CHAR")
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
                pdf.multi_cell(pdf.epw - 6, 5.2, text=_safe_latin1(f"- {tip}"), new_x="LMARGIN", new_y="NEXT", align="J", wrapmode="CHAR")
            pdf.ln(3)

    return bytes(pdf.output())

def _extract_numeric_score(score_str: str) -> float:
    """Extrae el porcentaje numérico de una cadena como '4/5 (80.0%)' para comparaciones."""
    import re
    if not score_str:
        return -1.0
    m = re.search(r"\((\d+(?:\.\d+)?)%\)", str(score_str))
    if m:
        return float(m.group(1))
    m2 = re.search(r"(\d+(?:\.\d+)?)", str(score_str))
    return float(m2.group(1)) if m2 else -1.0


def verify_certificate_by_folio_pg(folio_cert: str) -> dict | None:
    """Consulta y valida un certificado oficial directamente desde PostgreSQL usando APP_PUBLIC_URL desde Secrets."""
    from psycopg.rows import dict_row
    f_clean = str(folio_cert or "").strip().upper()
    if not f_clean:
        return None
    try:
        conn = get_pg_conn()
        if conn:
            with conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("SELECT * FROM certificates WHERE UPPER(folio_cert) = %s;", (f_clean,))
                    row = cur.fetchone()
                    if row:
                        app_pub = str(st.secrets.get("APP_PUBLIC_URL", "")).strip().rstrip("/")
                        url_db = f"{app_pub}/?verify_cert={row['folio_cert']}" if app_pub else str(row.get("verify_url") or "")

                        return {
                            "Folio_Certificado": row["folio_cert"],
                            "Clave_Alumno": row["clave_alumno"],
                            "Titular": row["titular"],
                            "Nivel_CEFR": row["nivel_cefr"],
                            "Grado_Academico": row["grado_academico"],
                            "Programa": row["programa"],
                            "Calificacion": row["calificacion"],
                            "Fecha_Emision": row["fecha_emision"],
                            "Firma_HMAC": row["firma_hmac"],
                            "Estatus": row["estatus"],
                            "URL_Verificacion": url_db
                        }
    except Exception:
        pass
    return None
    
def update_certificate_link_pg(folio_cert: str, new_url: str = "") -> bool:
    """Guarda o actualiza directamente la URL de verificación del certificado en Supabase PostgreSQL."""
    f_clean = str(folio_cert or "").strip().upper()
    if not f_clean:
        return False

    app_pub = str(st.secrets.get("APP_PUBLIC_URL", "")).strip().rstrip("/")
    url_final = str(new_url or "").strip() or (f"{app_pub}/?verify_cert={f_clean}" if app_pub else "")

    conn = get_pg_conn()
    if not conn:
        return False

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE certificates
                    SET verify_url = %s
                    WHERE UPPER(TRIM(folio_cert)) = %s;
                """, (url_final, f_clean))
        return True
    except Exception:
        return False


def save_lesson_to_postgres(folio: str, usuario_name: str, tema: str, cefr: str, grado: str, texto: str, pdf_link: str):
    """Registra una nueva lección generada directamente en PostgreSQL (Supabase)."""
    conn = get_pg_conn()
    if not conn:
        return
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users_padron WHERE LOWER(usuario) = LOWER(%s) LIMIT 1;", (usuario_name.strip(),))
            u_row = cur.fetchone()
            uid = next(iter(u_row), None) if u_row else None
            if uid is None:
                cur.execute("""
                    INSERT INTO users_padron (usuario, clave_hash, rol, permisos, estatus)
                    VALUES (%s, 'AUTO_SESSION', 'Estudiante', 'Basico', 'Activo')
                    RETURNING id;
                """, (usuario_name.strip(),))
                uid = next(iter(cur.fetchone()), 1)

            cur.execute("""
                INSERT INTO lessons_folios (folio, user_id, tema, cefr_level, academic_grade, lesson_text, pdf_link)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (folio) DO UPDATE SET
                    lesson_text = EXCLUDED.lesson_text,
                    pdf_link = EXCLUDED.pdf_link,
                    updated_at = NOW();
            """, (folio.strip().upper(), uid, tema, cefr, grado, texto, pdf_link))


def save_best_quiz_result_to_sheet(folio: str, new_score_str: str, quiz_items, user_ans_dict):
    """Evalúa, compara atómicamente en PostgreSQL y conserva la calificación más alta del Folio."""
    from psycopg.rows import dict_row
    if not folio:
        return False, "Folio no asignado.", new_score_str

    conn = get_pg_conn()
    if not conn:
        return False, "Sin conexión a PostgreSQL.", new_score_str

    f_clean = str(folio).strip().upper()
    new_num = _extract_numeric_score(new_score_str)

    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT best_quiz_score, best_quiz_numeric
                FROM lessons_folios WHERE UPPER(folio) = %s;
            """, (f_clean,))
            row = cur.fetchone()
            if not row:
                return False, "Folio no encontrado en PostgreSQL.", new_score_str

            prev_best_str = str(row["best_quiz_score"] or "").strip()
            prev_num = float(row["best_quiz_numeric"] if row["best_quiz_numeric"] is not None else -1.0)

            if prev_num < 0 or new_num > prev_num:
                serializable_ans = {str(k): v for k, v in (user_ans_dict or {}).items()}
                cur.execute("""
                    UPDATE lessons_folios
                    SET quiz_data = %s::jsonb,
                        best_quiz_score = %s,
                        best_quiz_numeric = %s,
                        best_quiz_answers = %s::jsonb,
                        updated_at = NOW()
                    WHERE UPPER(folio) = %s;
                """, (
                    json.dumps(quiz_items),
                    new_score_str,
                    new_num,
                    json.dumps(serializable_ans),
                    f_clean
                ))
                msg = (
                    f"🏆 ¡Nueva mejor calificación registrada en PostgreSQL: **{new_score_str}**! (Superaste tu intento anterior de {prev_best_str})."
                    if prev_num >= 0
                    else f"✅ Calificación inicial registrada en PostgreSQL: **{new_score_str}**."
                )
                return True, msg, new_score_str
            else:
                msg = f"ℹ️ Obtuviste **{new_score_str}**, pero conservamos tu nota más alta (**{prev_best_str}**) en PostgreSQL y en tu PDF."
                return False, msg, prev_best_str


def save_best_speaking_to_sheet(folio: str, new_score_pct: int):
    """Guarda en PostgreSQL la calificación más alta de evaluación oral y su reporte."""
    if not folio:
        return
    try:
        conn = get_pg_conn()
        if not conn:
            return
        eval_json = json.dumps(st.session_state.get("speaking_eval_result")) if st.session_state.get("speaking_eval_result") else None
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE lessons_folios
                    SET best_speaking_score = GREATEST(COALESCE(best_speaking_score, -1), %s),
                        speaking_eval_json = COALESCE(%s::jsonb, speaking_eval_json),
                        updated_at = NOW()
                    WHERE UPPER(folio) = %s;
                """, (float(new_score_pct), eval_json, str(folio).strip().upper()))
    except Exception:
        pass
def upsert_user_padron_pg(usuario: str, clave: str, rol: str, grado: str, nivel: str, permisos: str, estatus: str) -> str:
    """Inserta o actualiza un usuario en Supabase y genera/devuelve su Matrícula Oficial (CEI-AÑO-ID)."""
    conn = get_pg_conn()
    if not conn:
        raise RuntimeError("Sin conexión activa a PostgreSQL.")
    anio_actual = datetime.now(ZoneInfo("America/Hermosillo")).year
    with conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO roles_permissions (profile_name) VALUES (%s) ON CONFLICT DO NOTHING;", (permisos.strip(),))
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
                RETURNING id, matricula;
            """, (
                usuario.strip(),
                clave.strip(),
                rol.strip(),
                grado.strip(),
                normalize_cefr(nivel),
                permisos.strip(),
                "Activo" if estatus.strip().lower() == "activo" else "Inactivo"
            ))
            row_ret = cur.fetchone()
            user_id_db = row_ret[0]
            mat_actual = row_ret[1]

            if not mat_actual:
                mat_actual = f"CEI-{anio_actual}-{int(user_id_db):04d}"
                cur.execute("UPDATE users_padron SET matricula = %s WHERE id = %s;", (mat_actual, user_id_db))

    load_padron_records.clear()
    return mat_actual

def upsert_user_padron_pg(
    usuario: str, clave: str, rol: str, grado: str, nivel: str, permisos: str, estatus: str,
    afiliador_id: int | None = None
) -> str:
    """Inserta o actualiza un usuario en Supabase, asigna su Matrícula Oficial y vincula su Socio Afiliado."""
    conn = get_pg_conn()
    if not conn:
        raise RuntimeError("Sin conexión activa a PostgreSQL.")
    anio_actual = datetime.now(ZoneInfo("America/Hermosillo")).year
    with conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO roles_permissions (profile_name) VALUES (%s) ON CONFLICT DO NOTHING;", (permisos.strip(),))
            cur.execute("""
                INSERT INTO users_padron (usuario, clave_hash, rol, grado_academico, nivel_cefr, permisos, estatus, afiliador_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (usuario) DO UPDATE SET
                    clave_hash = EXCLUDED.clave_hash,
                    rol = EXCLUDED.rol,
                    grado_academico = EXCLUDED.grado_academico,
                    nivel_cefr = EXCLUDED.nivel_cefr,
                    permisos = EXCLUDED.permisos,
                    estatus = EXCLUDED.estatus,
                    afiliador_id = COALESCE(EXCLUDED.afiliador_id, users_padron.afiliador_id)
                RETURNING id, matricula;
            """, (
                usuario.strip(),
                clave.strip(),
                rol.strip(),
                grado.strip(),
                normalize_cefr(nivel),
                permisos.strip(),
                "Activo" if estatus.strip().lower() == "activo" else "Inactivo",
                afiliador_id
            ))
            row_ret = cur.fetchone()
            user_id_db = row_ret
            mat_actual = row_ret

            if not mat_actual:
                mat_actual = f"CEI-{anio_actual}-{int(user_id_db):04d}"
                cur.execute("UPDATE users_padron SET matricula = %s WHERE id = %s;", (mat_actual, user_id_db))

    load_padron_records.clear()
    return mat_actual


def set_student_affiliate_pg(student_id: int, afiliador_id: int | None):
    """Guarda el ID del socio afiliador directamente en la columna afiliador_id del estudiante."""
    conn = get_pg_conn()
    if not conn:
        raise RuntimeError("Sin conexión activa a PostgreSQL.")
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users_padron SET afiliador_id = %s WHERE id = %s;",
                (afiliador_id, int(student_id))
            )
    load_padron_records.clear()

        
def upsert_permission_profile_pg(perfil_name: str, caps_dict: dict):
    """Guarda o actualiza un perfil de permisos RBAC directamente en Supabase PostgreSQL."""
    conn = get_pg_conn()
    if not conn:
        raise RuntimeError("Sin conexión activa a PostgreSQL.")
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO roles_permissions (
                    profile_name, generar_leccion, resolver_quiz, grabar_audio,
                    emitir_certificados, gestionar_usuarios, editar_instituto_logo, capabilities_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (profile_name) DO UPDATE SET
                    generar_leccion = EXCLUDED.generar_leccion,
                    resolver_quiz = EXCLUDED.resolver_quiz,
                    grabar_audio = EXCLUDED.grabar_audio,
                    emitir_certificados = EXCLUDED.emitir_certificados,
                    gestionar_usuarios = EXCLUDED.gestionar_usuarios,
                    editar_instituto_logo = EXCLUDED.editar_instituto_logo,
                    capabilities_json = EXCLUDED.capabilities_json,
                    updated_at = NOW();
            """, (
                perfil_name.strip(),
                bool(caps_dict.get("Generar_Leccion", True)),
                bool(caps_dict.get("Resolver_Quiz", True)),
                bool(caps_dict.get("Grabar_Audio", True)),
                bool(caps_dict.get("Emitir_Certificados", False)),
                bool(caps_dict.get("Registrar_Usuarios", caps_dict.get("Gestionar_Usuarios", False))),
                bool(caps_dict.get("Editar_Instituto_Logo", False)),
                json.dumps(caps_dict)
            ))
    load_permissions_matrix.clear()
    
def insert_certificate_pg(folio_c: str, clave_sel: str, nombre_sel: str, nivel_sel: str, grado_sel: str, programa_c: str, calif_c: str, fecha_c: str, sello_h: str):
    """Guarda un certificado oficial timbrado directamente en Supabase PostgreSQL."""
    conn = get_pg_conn()
    if not conn:
        raise RuntimeError("Sin conexión activa a PostgreSQL.")
    base_url = str(st.secrets.get("APP_BASE_URL", "https://streamlit.app")).rstrip("/")
    verify_url = f"{base_url}/?verify={urllib.parse.quote(folio_c)}"
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users_padron WHERE LOWER(usuario) = LOWER(%s) LIMIT 1;", (nombre_sel.strip(),))
            u_row = cur.fetchone()
            uid = next(iter(u_row), None) if u_row else None
            if uid is None:
                cur.execute("""
                    INSERT INTO users_padron (usuario, clave_hash, rol, permisos, estatus)
                    VALUES (%s, %s, 'Estudiante', 'Basico', 'Activo')
                    RETURNING id;
                """, (nombre_sel.strip(), clave_sel.strip()))
                uid = next(iter(cur.fetchone()), 1)
                
            app_pub_cert = str(
                st.secrets.get("APP_PUBLIC_URL")
                or "https://streamlit.app"
            ).rstrip("/")
            verify_url = f"{app_pub_cert}/?verify_cert={folio_c.strip().upper()}"

            cur.execute("""
                INSERT INTO certificates (
                    folio_cert, user_id, clave_alumno, titular, nivel_cefr,
                    grado_academico, programa, calificacion, fecha_emision,
                    firma_hmac, estatus, verify_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Valido', %s)
                ON CONFLICT (folio_cert) DO NOTHING;
            """, (
                folio_c.strip().upper(), uid, clave_sel.strip(), nombre_sel.strip(),
                nivel_sel.strip(), grado_sel.strip(), programa_c.strip(),
                calif_c.strip(), fecha_c.strip(), sello_h.strip(), verify_url
            ))


def load_certificates_pg() -> list[dict]:
    """Carga el historial de certificados emitidos desde Supabase PostgreSQL."""
    from psycopg.rows import dict_row
    conn = get_pg_conn()
    if not conn:
        return []
    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
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


def update_certificate_status_pg(folio_cert: str, nuevo_estatus_ui: str):
    """Actualiza el estatus (Vigente/Revocado) de un certificado en Supabase PostgreSQL."""
    conn = get_pg_conn()
    if not conn:
        raise RuntimeError("Sin conexión activa a PostgreSQL.")
    db_status = "Valido" if str(nuevo_estatus_ui).strip().lower() in ["vigente", "valido"] else "Revocado"
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE certificates SET estatus = %s WHERE UPPER(folio_cert) = %s;",
                (db_status, str(folio_cert).strip().upper())
            )

 
# --- 6. DETECCIÓN DE DISPOSITIVO Y ESTADOS ---
try:
    user_agent = st.context.headers.get("User-Agent", "").lower()
except Exception:
    user_agent = ""
is_mobile = any(device in user_agent for device in ["iphone", "android", "ipad", "mobile"])

CEFR_MAP = {
    "A1": "A1 (Beginner)",
    "A2": "A2 (Elementary)",
    "B1": "B1 (Intermediate)",
    "B2": "B2 (Upper-Intermediate)",
    "C1": "C1 (Advanced)",
    "C2": "C2 (Proficiency)"
}

def evaluar_pronunciacion_ia(audio_bytes: bytes, mime_type: str, texto_objetivo: str, gramatica_obj: str, nivel_cefr: str, grado_acad: str) -> dict:
    """Evalúa fonética, fluidez y gramática oral usando gemini-3.1-pro-preview con respaldo a gemini-2.5-flash."""
    from google.genai import types

    gm_client = init_gemini_client()
    if not gm_client:
        raise RuntimeError("Cliente Gemini no inicializado. Verifica GEMINI_API_KEY en Secrets.")

    prompt_eval = f"""
    You are an expert English Phonetics & Applied Linguistics Evaluator at Career English Institute.
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


@st.cache_data(ttl=3600, show_spinner=False)
def analyze_lesson_for_study_mode(lesson_text: str, cefr_level: str) -> dict:
    """Tokeniza la lección completa y obtiene traducciones EN->ES reales por palabra."""
    import re
    from google.genai import types

    texto_sin_bib = str(lesson_text or "")
    for marcador in ["**Bibliography", "Bibliography ("]:
        if marcador in texto_sin_bib:
            texto_sin_bib = texto_sin_bib.split(marcador, 1)[0]

    lineas_limpias = []
    for linea in texto_sin_bib.splitlines():
        l_strip = linea.strip()
        if not l_strip:
            continue
        if re.match(r"^\*\*(Folio|Creation Date|Author|Institution|CEFR Level|Academic Level|Campus & Contact):", l_strip, flags=re.IGNORECASE):
            continue
        lineas_limpias.append(l_strip)

    solo_titulo_y_cuerpo = "\n\n".join(lineas_limpias)[:2800]

    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "have", "has", "had",
        "are", "was", "were", "been", "being", "will", "would", "could", "should",
        "into", "about", "than", "then", "them", "they", "their", "there", "here",
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
        "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
        "not", "only", "own", "same", "too", "very", "can", "just", "don", "now"
    }
    conjunciones = {"and", "but", "or", "so", "because", "although", "while", "if", "when", "since", "unless", "whereas", "however", "therefore", "yet", "nor"}

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

                if low.isalpha() and len(low) >= 3 and low not in stopwords and low not in vistas:
                    vistas.add(low)
                    palabras_clave.append(low)
            oraciones_base.append({"sentence_es": "", "tokens": toks})

    vocab_target = palabras_clave[:55]
    dict_final = {}

    if vocab_target:
        prompt_dict = f"""
        Translate these English words (from a CEFR {cefr_level} lesson) into natural Spanish for a bilingual dictionary.
        Words: {json.dumps(vocab_target)}
        Context: {solo_titulo_y_cuerpo[:1200]}

        Return ONLY a JSON object where each key is the lowercase English word and its value is:
        {{
          "pos": "verb"|"noun"|"adjective"|"conjunction"|"other",
          "ipa": "/US_IPA/",
          "pos_es": "Verbo"|"Sustantivo"|"Adjetivo"|"Conjunción"|"Adverbio",
          "es": "traducción principal exacta en español",
          "alt_es": "sinónimo 1, sinónimo 2",
          "def_es": "definición breve en español (máximo 12 palabras)",
          "ex_en": "Short English example sentence.",
          "ex_es": "Traducción corta al español."
        }}
        """
        try:
            gm_client = init_gemini_client()
            if gm_client:
                res_d = gm_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_dict,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                        temperature=0.1
                    )
                )
                raw_d = str(res_d.text or "").strip()
                raw_d = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_d, flags=re.MULTILINE).strip()
                parsed_d = json.loads(raw_d)
                if isinstance(parsed_d, dict):
                    for k_w, v_info in parsed_d.items():
                        if isinstance(v_info, dict):
                            # Normaliza ejemplos para compatibilidad con el visor
                            if "examples" not in v_info and v_info.get("ex_en"):
                                v_info["examples"] = [{"en": v_info.get("ex_en", ""), "es": v_info.get("ex_es", "")}]
                            dict_final[k_w.lower().strip()] = v_info

                    for s_obj in oraciones_base:
                        for tk in s_obj["tokens"]:
                            info_w = dict_final.get(tk["w"].lower())
                            if isinstance(info_w, dict) and info_w.get("pos") in ["verb", "noun", "adjective", "conjunction", "other"]:
                                tk["pos"] = info_w["pos"]
        except Exception:
            pass

    return {"sentences": oraciones_base, "dictionary": dict_final}


def normalizar_entradas_apa(client, contexto_raw: str, personas_raw: str, asunto_raw: str) -> tuple[str, str, str]:
    """Traduce al inglés y corrige ortografía/estilo académico de las entradas del usuario para la bibliografía APA."""
    try:
        prompt_norm = f"""
        You are an academic copyeditor specializing in APA 7th Edition style.
        Translate to natural, grammatically accurate English (if in Spanish or mixed) and fix any spelling, capitalization, or punctuation errors in these three user inputs:
        1. Context/Setting: "{contexto_raw}"
        2. Characters/Participants: "{personas_raw}"
        3. Subject/Topic (format in proper English Title Case for an academic publication title): "{asunto_raw}"

        Return ONLY a valid JSON object with exact keys:
        {{
            "context_en": "...",
            "characters_en": "...",
            "subject_apa_title": "..."
        }}
        """
        raw_norm, _ = generar_con_maxima_potencia(client, prompt_norm, as_json=True)
        cleaned = raw_norm.strip()
        if cleaned.startswith("```"):
            cleaned = next(iter(cleaned.split("\n", 1)[-1].rsplit("```", 1)), "")
        data = json.loads(cleaned)
        return (
            str(data.get("context_en", contexto_raw)).strip() or contexto_raw,
            str(data.get("characters_en", personas_raw)).strip() or personas_raw,
            str(data.get("subject_apa_title", asunto_raw)).strip() or asunto_raw
        )
    except Exception:
        return contexto_raw.strip(), personas_raw.strip(), asunto_raw.strip().title()

def migrar_sheets_a_supabase() -> dict:
    """Transfiere de forma segura los datos de Google Sheets a PostgreSQL (Supabase)."""
    import psycopg
    db_url = str(st.secrets.get("DATABASE_URL", "")).strip()
    if not db_url:
        raise ValueError("No se encontró DATABASE_URL en los Secrets de Streamlit.")

    resumen = {"permisos": 0, "usuarios": 0, "folios": 0, "certificados": 0, "config": 0}
    book = get_google_workbook()

    with psycopg.connect(db_url, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            # 1. Migrar Matriz de Permisos
            try:
                ws_perm = book.worksheet("Matriz_Permisos")
                for r in ws_perm.get_all_records():
                    prof = str(r.get("Perfil", "")).strip()
                    if not prof:
                        continue
                    cur.execute("""
                        INSERT INTO roles_permissions (
                            profile_name, generar_leccion, resolver_quiz, grabar_audio,
                            emitir_certificados, gestionar_usuarios, editar_instituto_logo
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (profile_name) DO UPDATE SET
                            generar_leccion = EXCLUDED.generar_leccion,
                            resolver_quiz = EXCLUDED.resolver_quiz,
                            grabar_audio = EXCLUDED.grabar_audio,
                            emitir_certificados = EXCLUDED.emitir_certificados,
                            gestionar_usuarios = EXCLUDED.gestionar_usuarios,
                            editar_instituto_logo = EXCLUDED.editar_instituto_logo,
                            updated_at = NOW();
                    """, (
                        prof,
                        str(r.get("Generar_Leccion", "SI")).upper() == "SI",
                        str(r.get("Resolver_Quiz", "SI")).upper() == "SI",
                        str(r.get("Grabar_Audio", "SI")).upper() == "SI",
                        str(r.get("Emitir_Certificados", "NO")).upper() == "SI",
                        str(r.get("Gestionar_Usuarios", "NO")).upper() == "SI",
                        str(r.get("Editar_Instituto_Logo", "NO")).upper() == "SI",
                    ))
                    resumen["permisos"] += 1
            except Exception:
                pass

            # 2. Migrar Padrón de Usuarios
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
                row_id = cur.fetchone()
                mapa_user_ids[u_name.lower()] = row_id
                resumen["usuarios"] += 1
            # 3. Migrar Lecciones y Folios (Hoja1)
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
                    uid = cur.fetchone()
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

            # 4. Migrar Certificados
            try:
                ws_cert = book.worksheet("Certificados")
                for r in ws_cert.get_all_records():
                    f_cert = str(r.get("Folio_Certificado", "")).strip().upper()
                    titular_c = str(r.get("Titular", "")).strip()
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
                        str(r.get("Programa", "")), str(r.get("Calificacion", "")),
                        str(r.get("Fecha_Emision", "")), str(r.get("Firma_HMAC", "")),
                        "Valido" if str(r.get("Estatus", "Valido")).strip().lower() == "valido" else "Revocado",
                        str(r.get("URL_Verificacion", ""))
                    ))
                    resumen["certificados"] += 1
            except Exception:
                pass
            # 5. Migrar Configuración Institucional
            cfg_actual = load_permanent_logo()
            if cfg_actual:
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
                    cfg_actual.get("Logo_Base64", ""),
                    cfg_actual.get("Mime_Type", "image/png"),
                    int(cfg_actual.get("Ancho", 120) or 120),
                    cfg_actual.get("Forma", "Circular"),
                    cfg_actual.get("Direccion", institute_address)
                ))
                resumen["config"] = 1

        conn.commit()
    return resumen



def save_best_speaking_to_sheet(folio: str, new_score_pct: int):
    """Guarda en Google Sheets la calificación más alta de pronunciación obtenida en el Folio."""
    if not folio:
        return
    try:
        s1 = get_google_sheet()
        celda_f = s1.find(str(folio).strip().upper(), in_column=1)
        if not celda_f:
            return
        headers = s1.row_values(1)
        if "Mejor_Speaking_Nota" not in headers:
            col_spk = len(headers) + 1
            s1.update_cell(1, col_spk, "Mejor_Speaking_Nota")
        else:
            col_spk = headers.index("Mejor_Speaking_Nota") + 1

        prev_val = str(s1.cell(celda_f.row, col_spk).value or "").strip()
        prev_num = _extract_numeric_score(prev_val)
        if prev_num < 0 or float(new_score_pct) > prev_num:
            s1.update_cell(celda_f.row, col_spk, f"{new_score_pct}%")
    except Exception:
        pass


def normalize_cefr(raw_val):
    code = str(raw_val).strip().upper()[:2]
    return CEFR_MAP.get(code, "B1 (Intermediate)")

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
    ("quiz_audio_bytes", None)
 
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

# --- 7. PORTAL PÚBLICO DE VERIFICACIÓN DE CERTIFICADOS (ACCESO POR QR SIN LOGIN) ---
verify_folio = st.query_params.get("verify", "").strip().upper()
if verify_folio:
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
                certs = get_certificados_sheet().get_all_records()
                cert_encontrado = next(
                    (c for c in certs if str(c.get("Folio_Certificado", "")).strip().upper() == verify_folio),
                    None
                )

                if cert_encontrado:
                    estatus_c = str(cert_encontrado.get("Estatus", "Vigente")).strip()
                    clave_c = str(cert_encontrado.get("Clave_Alumno", "")).strip()
                    nombre_c = str(cert_encontrado.get("Nombre_Estudiante", "")).strip()
                    nivel_c = str(cert_encontrado.get("Nivel_CEFR", "")).strip()
                    prog_c = str(cert_encontrado.get("Programa_Curso", "")).strip()
                    calif_c = str(cert_encontrado.get("Calificacion", "")).strip()
                    fecha_c = str(cert_encontrado.get("Fecha_Emision", "")).strip()
                    sello_bd = str(cert_encontrado.get("Sello_Digital_SHA256", "")).strip().upper()

                    _, sello_recalculado = generar_sello_digital(verify_folio, clave_c, nombre_c, nivel_c, fecha_c)
                    firma_valida = hmac.compare_digest(sello_bd, sello_recalculado)

                    if firma_valida and estatus_c.lower() == "vigente":
                        st.success("✅ **CERTIFICADO AUTÉNTICO Y VERIFICADO CRIPTOGRÁFICAMENTE**")
                        with st.container(border=True):
                            st.markdown(f"**🔖 Folio Oficial:** `{verify_folio}`")
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
        if st.button("🏛️ Ir a la Plataforma Principal", width="stretch"):
            st.query_params.clear()
            st.rerun()
    st.stop()
    
# --- 8. AUTENTICACIÓN, LOCALSTORAGE FIRMADO Y CAPTURA DE FOLIO ---
def fetch_student_gradebook_pg(target_usuario: str) -> dict:
    """Calcula promedios en tiempo real y desglose completo por todos los Grammar Topics del nivel CEFR del alumno."""
    import re
    from psycopg.rows import dict_row

    conn = get_pg_conn()
    if not conn:
        return {"records": [], "topic_summary": [], "overall_avg": 0.0, "quiz_avg": 0.0, "oral_avg": 0.0, "matricula": "N/A", "nivel_cefr": "B1", "grado": ""}

    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, COALESCE(matricula, 'CEI-2026-' || LPAD(id::text, 4, '0')) AS matricula,
                       COALESCE(nivel_cefr, 'B1') AS nivel_cefr,
                       COALESCE(grado_academico, 'Licenciatura / Universidad') AS grado_academico
                FROM users_padron
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (target_usuario.strip(),))
            u_row = cur.fetchone() or {}

            cur.execute("""
                SELECT
                    l.folio,
                    l.tema,
                    COALESCE(NULLIF(TRIM(l.grammar_topic), ''), 'General Applied Grammar') AS grammar_topic,
                    l.nivel_cefr,
                    l.best_score,
                    COALESCE(l.speaking_score, 0) AS speaking_score,
                    TO_CHAR(l.created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS fecha
                FROM lessons_archive l
                JOIN users_padron u ON l.user_id = u.id
                WHERE LOWER(TRIM(u.usuario)) = LOWER(TRIM(%s))
                ORDER BY l.created_at DESC;
            """, (target_usuario.strip(),))
            rows = cur.fetchall()
    def _parse_quiz_pct(score_str: str) -> float | None:
        m = re.search(r"\((\d+(?:\.\d+)?)%\)", str(score_str or ""))
        return float(m.group(1)) if m else None

    nivel_alumno = normalize_cefr(u_row.get("nivel_cefr", "B1"))
    catalogo_nivel = CEFR_GRAMMAR_TOPICS.get(nivel_alumno, CEFR_GRAMMAR_TOPICS["B1"])

    por_tema = {t: {"scores": [], "lecciones": 0} for t in catalogo_nivel}
    registros_procesados = []
    todas_quiz, todas_oral, todas_combinadas = [], [], []

    for r in rows:
        q_pct = _parse_quiz_pct(r.get("best_score"))
        o_raw = float(r.get("speaking_score") or 0)
        o_pct = o_raw if o_raw > 0 else None

        notas_item = [x for x in [q_pct, o_pct] if x is not None]
        prom_leccion = round(sum(notas_item) / len(notas_item), 1) if notas_item else None

        if q_pct is not None:
            todas_quiz.append(q_pct)
        if o_pct is not None:
            todas_oral.append(o_pct)
        if prom_leccion is not None:
            todas_combinadas.append(prom_leccion)

        g_topic = str(r.get("grammar_topic") or "General Applied Grammar").strip()
        if g_topic not in por_tema:
            por_tema[g_topic] = {"scores": [], "lecciones": 0}
        por_tema[g_topic]["lecciones"] += 1
        if prom_leccion is not None:
            por_tema[g_topic]["scores"].append(prom_leccion)

        registros_procesados.append({
            "Folio": r.get("folio", ""),
            "Fecha": r.get("fecha", ""),
            "Nivel": r.get("nivel_cefr", ""),
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


def stamp_and_save_transcript_pg(student_name: str, gb_data: dict, topic_filter: str) -> dict:
    """Timbra criptográficamente el Boletín Oficial con HMAC-SHA256, fecha exacta y lo guarda en Supabase."""
    import hashlib
    import hmac

    ahora_sonora = datetime.now(ZoneInfo("America/Hermosillo"))
    fecha_str = ahora_sonora.strftime("%Y-%m-%d %H:%M:%S MST")
    folio_bol = f"BOL-{ahora_sonora.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    matricula = str(gb_data.get("matricula") or "CEI-2026-0000").strip()
    nivel_c = str(gb_data.get("nivel_cefr") or "B1").strip()
    ov_avg = float(gb_data.get("overall_avg") or 0.0)
    qz_avg = float(gb_data.get("quiz_avg") or 0.0)
    or_avg = float(gb_data.get("oral_avg") or 0.0)
    tot_lec = len(gb_data.get("records") or [])

    # Llave secreta institucional para firma HMAC-SHA256
    secret_hmac = str(st.secrets.get("CERT_HMAC_SECRET", "CEI_AGUA_PRIETA_2026_OFFICIAL_SEAL")).encode("utf-8")
    cadena_original = (
        f"{folio_bol}|{matricula}|{student_name.strip().upper()}|{nivel_c}|"
        f"{topic_filter}|{ov_avg:.2f}|{qz_avg:.2f}|{or_avg:.2f}|{tot_lec}|{fecha_str}"
    )
    sello_hmac = hmac.new(secret_hmac, cadena_original.encode("utf-8"), hashlib.sha256).hexdigest().upper()

    conn = get_pg_conn()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO transcripts_archive (
                            folio_boletin, matricula, student_name, nivel_cefr, topic_filter,
                            overall_avg, quiz_avg, oral_avg, total_lessons, hmac_seal, issued_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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


def create_official_gradebook_pdf(student_name: str, gb_data: dict, topic_filter: str = "Vista General") -> tuple[bytes, dict]:
    """Genera y timbra el Boletín Oficial de Calificaciones en formato APA 7a Ed. con logo dinámico, QR y sello HMAC-SHA256."""
    import tempfile
    import qrcode
    from fpdf import FPDF

    timbre = stamp_and_save_transcript_pg(student_name, gb_data, topic_filter)
    folio_bol = timbre["folio_boletin"]
    fecha_gen = timbre["fecha_generacion"]
    sello_hmac = timbre["sello_hmac"]

    app_base_url = str(
        st.secrets.get("APP_PUBLIC_URL")
        or st.secrets.get("APP_BASE_URL")
        or "https://streamlit.app"
    ).rstrip("/")
    verify_url = f"{app_base_url}/?verify_transcript={folio_bol}"
    qr_img = qrcode.make(verify_url)
    tmp_qr = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    qr_img.save(tmp_qr.name)

    # Logotipo dinámico sincronizado con la pantalla principal (con respaldo LOGO CEI APP.png)
    logo_src = None
    perm_logo = load_permanent_logo() if "load_permanent_logo" in globals() else None
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
            self.cell(186, 4, f"© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti | APA 7th Ed. Standard | Page {self.page_no()}", new_x="LMARGIN", new_y="NEXT", align="C")
            self.set_x(12)
            self.cell(186, 4, clean_pdf_text(institute_address), new_x="LMARGIN", new_y="NEXT", align="C")

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
        pdf.cell(124, 6.2, clean_pdf_text(t_row["Grammar Topic"]), align="L")
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

    pdf.image(tmp_qr.name, x=15, y=y_seal + 2.5, w=25)
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

    try:
        os.unlink(tmp_qr.name)
    except Exception:
        pass

    return bytes(pdf.output()), timbre




#A quí estaba la Parte 8.
def _sign_session_token(usuario: str, clave: str) -> str:
    secret = str(st.secrets.get("HMAC_SECRET_KEY", "CEI-SESSION-KEY")).encode("utf-8")
    raw_data = f"{usuario}|{clave}"
    sig = hmac.new(secret, raw_data.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    payload = json.dumps({"u": usuario, "c": clave, "s": sig}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")

def _verify_session_token(token_str: str):
    decoded_json = base64.urlsafe_b64decode(token_str.encode("utf-8")).decode("utf-8")
    token_data = json.loads(decoded_json)
    u_tok = token_data.get("u", "")
    c_tok = token_data.get("c", "")
    s_tok = token_data.get("s", "")
    if not (u_tok and c_tok and s_tok):
        return None, None
    secret = str(st.secrets.get("HMAC_SECRET_KEY", "CEI-SESSION-KEY")).encode("utf-8")
    expected_sig = hmac.new(secret, f"{u_tok}|{c_tok}".encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    if hmac.compare_digest(s_tok, expected_sig):
        return u_tok, c_tok
    return None, None

url_folio = st.query_params.get("folio", "")
if url_folio and not st.session_state.current_folio:
    st.session_state.current_folio = str(url_folio).strip().upper()

PERMISSIONS_MATRIX = load_permissions_matrix()
PERMISOS_LISTA = list(PERMISSIONS_MATRIX.keys())

if st.session_state.pending_ls_token is not None:
    if st.session_state.pending_ls_token == "REMOVE":
        streamlit_js_eval(js_expressions="localStorage.removeItem('cei_auth_token')", key="rm_ls_init")
    else:
        safe_js_token = json.dumps(st.session_state.pending_ls_token)
        streamlit_js_eval(js_expressions=f"localStorage.setItem('cei_auth_token', {safe_js_token})", key="sv_ls_init")
    st.session_state.pending_ls_token = None


# --- VERIFICACIÓN PÚBLICA DE BOLETÍN OFICIAL TIMBRADO (VÍA QR) ---
verify_bol_param = st.query_params.get("verify_transcript", "")
if isinstance(verify_bol_param, list):
    verify_bol_param = verify_bol_param[0] if verify_bol_param else ""
verify_bol_param = str(verify_bol_param).strip().upper()

if verify_bol_param:
    st.markdown("### 🛡️ Verificación Oficial de Boletín Académico — Career English Institute")
    try:
        conn_vb = get_pg_conn()
        row_vb = None
        if conn_vb:
            from psycopg.rows import dict_row
            with conn_vb:
                with conn_vb.cursor(row_factory=dict_row) as cur:
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

    if st.button("🔐 Ir al Acceso Institucional de la Plataforma"):
        st.query_params.clear()
        st.rerun()
    st.stop()

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
            input_user = st.text_input("👤 Usuario registrado:")
            input_pass = st.text_input("🔑 Clave de Acceso:", type="password")
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
                                if u_db.lower() == input_user.strip().lower() and c_db == input_pass.strip():
                                    usuario_encontrado = reg
                                    break
                            
                            # Respaldo de acceso maestro del Propietario desde Secrets
                            if usuario_encontrado is None:
                                m_user = str(st.secrets.get("OWNER_MASTER_USER", "")).strip()
                                m_key = str(st.secrets.get("OWNER_MASTER_KEY", "")).strip()
                                if m_user and m_key and input_user.strip().lower() == m_user.lower() and input_pass.strip() == m_key:
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
                                st.error(
                                    "🚨 **Credenciales Incorrectas:** El **Usuario** o la **Clave de Acceso** no coinciden con nuestros registros.\n\n"
                                    "Verifica que no tengas activado el bloqueo de mayúsculas o solicita asistencia a tu Teacher / Administrador."
                                )
                                if st.session_state.get("db_auth_diag"):
                                    st.caption(f"🔍 Diagnóstico de conexión: {st.session_state['db_auth_diag']}")

                                
                            else:
                                e_db = str(usuario_encontrado.get("Estatus", "Activo")).strip().lower()
                                if e_db != "activo":
                                    st.toast("Cuenta inactiva.", icon="⛔")
                                    st.error("⛔ **Acceso Restringido:** Tu cuenta existe, pero se encuentra **Inactiva**. Contacta a la administración del instituto.")
                                else:
                                    u_db = str(usuario_encontrado.get("Usuario", "")).strip()
                                    c_db = str(usuario_encontrado.get("Clave", "")).strip()
                                    r_db = str(usuario_encontrado.get("Rol", "Estudiante")).strip()
                                    p_db = resolve_permission_profile(usuario_encontrado.get("Permisos", ""), r_db, PERMISSIONS_MATRIX)
                                    n_db = normalize_cefr(usuario_encontrado.get("Nivel", "B1"))
                                    g_db = str(usuario_encontrado.get("Grado_Academico", "Licenciatura / Universidad")).strip() or "Licenciatura / Universidad"
                                    
                                    st.session_state.authenticated = True
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
                        st.error(f"❌ Error de conexión al verificar credenciales en la base de datos: {e}")
        st.markdown(
            f"<div style='text-align: center; color: #777; font-size: 12px; margin-top: 15px;'>📍 {institute_address}<br>© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti</div>",
            unsafe_allow_html=True
        )
    st.stop()

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
    """Genera el Certificado Oficial en formato Carta horizontal (Letter Landscape) con timbre HMAC-SHA256 y QR."""
    import qrcode
    from fpdf.enums import XPos, YPos

    # Tamaño Carta horizontal: 279.4 mm x 215.9 mm
    pdf = FPDF(orientation="L", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # Marco doble institucional (Azul Marino y Dorado) calibrado a Carta (279.4 x 215.9 mm)
    pdf.set_draw_color(26, 42, 68)
    pdf.set_line_width(1.6)
    pdf.rect(10, 10, 259.4, 195.9)
    pdf.set_draw_color(184, 142, 67)
    pdf.set_line_width(0.6)
    pdf.rect(13, 13, 253.4, 189.9)

    # Logotipo institucional centrado (centro de 279.4 mm = 139.7 mm)
    cfg_logo = load_permanent_logo()
    if cfg_logo and cfg_logo.get("Logo_Base64"):
        try:
            raw_img = base64.b64decode(cfg_logo["Logo_Base64"])
            tmp_logo = io.BytesIO(raw_img)
            pdf.image(tmp_logo, x=127.2, y=16, w=25)
            pdf.set_y(44)
        except Exception:
            pdf.set_y(24)
    else:
        pdf.set_y(24)

    # Encabezado Institucional
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

    # Nombre del Titular
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 12, clean_pdf_text(titular.upper()), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Línea dorada centrada bajo el nombre (de 65 mm a 214.4 mm)
    pdf.set_draw_color(184, 142, 67)
    pdf.set_line_width(0.5)
    pdf.line(65, pdf.get_y(), 214.4, pdf.get_y())
    pdf.ln(4)

    # Detalles del programa y calificación
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

    # Firma del Director Académico centrada
    pdf.set_y(148)
    pdf.set_draw_color(40, 45, 55)
    pdf.line(100, 148, 179.4, 148)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(0, 5, clean_pdf_text("Jacob Zumaya Prianti"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 95, 105)
    pdf.cell(0, 4, clean_pdf_text("Academic Director & Principal Author — Career English Institute"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Código QR de Verificación Pública (Esquina inferior izquierda)
    base_url = str(st.secrets.get("APP_BASE_URL", "https://streamlit.app")).rstrip("/")
    verify_link = f"{base_url}/?verify={urllib.parse.quote(folio_c)}"
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(verify_link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1a2a44", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    pdf.image(qr_buf, x=18, y=161, w=28)

    # Bloque de Timbre Digital Criptográfico HMAC-SHA256
    pdf.set_xy(49, 162)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(0, 4, clean_pdf_text(f"OFFICIAL CERTIFICATE FOLIO: {folio_c}   |   ISSUED: {fecha_c}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(49)
    pdf.set_font("Courier", "", 6.5)
    pdf.set_text_color(70, 75, 85)
    pdf.multi_cell(210, 3.2, clean_pdf_text(f"ORIGINAL STRING: {cadena_original}\nHMAC-SHA256 DIGITAL SIGNATURE: {sello_hmac}"))

    pdf.set_xy(49, 179)
    pdf.set_font("Helvetica", "I", 6.8)
    pdf.set_text_color(100, 105, 115)
    pdf.multi_cell(
        212,
        3.2,
        clean_pdf_text(f"Scan QR code or visit {verify_link} to verify authenticity.\n{direccion_inst}")
    )

    return bytes(pdf.output())


# --- 9. MOTOR DE IA MULTIMODAL ---
def render_interactive_study_viewer(study_payload: dict):
    """Visor interactivo con voz US English y diccionario/traductor EN->ES pre-cargado por IA."""
    sentences_list = study_payload.get("sentences", []) if isinstance(study_payload, dict) else []
    dict_map = study_payload.get("dictionary", {}) if isinstance(study_payload, dict) else {}

    sentences_json = json.dumps(sentences_list, ensure_ascii=False).replace("</script>", "<\\/script>")
    dict_json = json.dumps(dict_map, ensure_ascii=False).replace("</script>", "<\\/script>")

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      html, body {{
        font-family: 'Segoe UI', Roboto, system-ui, sans-serif;
        margin: 0; padding: 12px; background: #f8fafc; color: #1e293b;
        position: relative; min-height: 480px;
      }}
      .toolbar {{
        display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
        justify-content: space-between; background: #ffffff; padding: 10px 14px;
        border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 14px;
      }}
      .legend {{ display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; font-weight: 600; }}
      .badge {{ padding: 3px 9px; border-radius: 6px; }}
      .pos-verb {{ background: #fee2e2; color: #991b1b; border-bottom: 2px solid #ef4444; }}
      .pos-noun {{ background: #dbeafe; color: #1e40af; border-bottom: 2px solid #3b82f6; }}
      .pos-adjective {{ background: #dcfce7; color: #166534; border-bottom: 2px solid #22c55e; }}
      .pos-conjunction {{ background: #fef3c7; color: #92400e; border-bottom: 2px solid #f59e0b; }}
      .pos-other {{ background: #f1f5f9; color: #334155; }}
      .title-box {{
        background: #1a2a44; color: #ffffff; padding: 14px 18px;
        border-radius: 10px; margin-bottom: 14px; font-size: 20px; font-weight: 700;
      }}
      .title-box .word-token {{ color: #1e293b; font-size: 18px; }}
      .title-box .sentence-tr {{ color: #cbd5e1; border-top-color: #334155; }}
      .sentence-box {{
        background: #ffffff; border-left: 4px solid #1a2a44;
        padding: 12px 16px; margin-bottom: 10px; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06); line-height: 2.1; font-size: 17px;
      }}
      .word-token {{
        display: inline-block; padding: 1px 6px; margin: 2px 2px;
        border-radius: 5px; cursor: pointer; transition: transform 0.1s, box-shadow 0.1s;
      }}
      .word-token:hover {{ transform: translateY(-2px); box-shadow: 0 3px 8px rgba(0,0,0,0.16); }}
      .word-active {{ outline: 2px solid #1a73e8; transform: translateY(-2px); }}
      .sentence-tr {{
        display: block; font-size: 13px; color: #64748b; margin-top: 6px;
        border-top: 1px dashed #e2e8f0; padding-top: 5px; font-style: italic;
      }}
      #gt-bubble {{
        display: none; position: absolute; z-index: 9999; width: 350px;
        background: #ffffff; border: 1.5px solid #1a73e8; border-radius: 12px;
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.28); overflow: hidden;
      }}
      .gt-topbar {{
        display: flex; justify-content: space-between; align-items: center;
        background: #e8f0fe; padding: 8px 12px; border-bottom: 1px solid #d2e3fc;
        font-size: 12px; font-weight: 700; color: #1a73e8;
      }}
      .gt-panel-en {{ padding: 10px 14px; background: #ffffff; border-bottom: 1px solid #e2e8f0; }}
      .gt-panel-es {{ padding: 10px 14px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
      .gt-word {{ font-size: 20px; font-weight: 700; color: #202124; }}
      .gt-ipa {{ font-size: 13px; color: #5f6368; margin-left: 6px; }}
      .gt-translation {{ font-size: 19px; font-weight: 700; color: #1a73e8; margin-top: 2px; }}
      .gt-alt {{ font-size: 12px; color: #475569; margin-top: 4px; }}
      .gt-def {{ font-size: 13px; color: #334155; margin-top: 6px; line-height: 1.4; }}
      .gt-scroll {{ max-height: 175px; overflow-y: auto; padding: 10px 14px; background: #ffffff; }}
      .ex-item {{
        margin-bottom: 8px; padding: 7px 9px; background: #f8fafc;
        border-left: 3px solid #1a73e8; border-radius: 6px; font-size: 13px;
      }}
      .ex-en {{ font-weight: 600; color: #202124; }}
      .ex-es {{ color: #475569; margin-top: 2px; }}
      .btn-mini {{
        border: 1px solid #cbd5e1; background: #ffffff; border-radius: 6px;
        padding: 4px 8px; cursor: pointer; font-size: 12px; font-weight: 600; color: #334155;
      }}
      .btn-mini:hover {{ background: #e2e8f0; }}
    </style>
    </head>
    <body>
      <div class="toolbar">
        <div class="legend">
          <span class="badge pos-verb">Verbos</span>
          <span class="badge pos-noun">Sustantivos</span>
          <span class="badge pos-adjective">Adjetivos</span>
          <span class="badge pos-conjunction">Conjunciones</span>
          <span class="badge pos-other">Otros</span>
        </div>
        <div style="display:flex; gap:8px; align-items:center;">
          <label style="font-size:12px; font-weight:600; cursor:pointer;">
            <input type="checkbox" id="hoverAudioToggle" checked> 🇺🇸 Voz US al pasar cursor
          </label>
          <button class="btn-mini" onclick="toggleSpeed()" id="speedBtn">1.0x</button>
        </div>
      </div>
      <div id="lesson-container"></div>

      <div id="gt-bubble" onclick="event.stopPropagation()">
        <div class="gt-topbar">
          <span>🇺🇸 INGLÉS (US) ➔ 🇪🇸 ESPAÑOL</span>
          <div>
            <button class="btn-mini" onclick="speakCurrent(1.0)" title="Voz US normal">🔊</button>
            <button class="btn-mini" onclick="speakCurrent(0.65)" title="Voz US lenta">🐢</button>
            <button class="btn-mini" onclick="closeBubble()" title="Cerrar">✖</button>
          </div>
        </div>
        <div class="gt-panel-en">
          <span class="gt-word" id="b-word"></span>
          <span class="gt-ipa" id="b-ipa"></span>
          <div id="b-pos" style="font-size:11px; text-transform:uppercase; color:#1a73e8; font-weight:700; margin-top:3px;"></div>
        </div>
        <div class="gt-panel-es">
          <div class="gt-translation" id="b-es"></div>
          <div class="gt-alt" id="b-alt"></div>
          <div class="gt-def" id="b-def"></div>
        </div>
        <div class="gt-scroll">
          <div style="font-size:11px; font-weight:700; color:#5f6368; margin-bottom:6px; text-transform:uppercase;">
            Ejemplos de traducción en contexto:
          </div>
          <div id="b-examples"></div>
        </div>
      </div>
      <script>
        const sentences = {sentences_json};
        const vocabDict = {dict_json};
        const posLabelsEs = {{ verb: 'Verbo', noun: 'Sustantivo', adjective: 'Adjetivo', conjunction: 'Conjunción', other: 'Expresión / Partícula' }};
        let speechRate = 1.0;
        let lastHovered = "";
        let currentBubbleWord = "";
        let usEnglishVoice = null;

        function loadUSVoice() {{
          if (!('speechSynthesis' in window)) return;
          const voices = window.speechSynthesis.getVoices();
          usEnglishVoice =
            voices.find(v => v.lang === 'en-US' && (v.name.includes('Google US') || v.name.includes('Aria') || v.name.includes('Jenny') || v.name.includes('Samantha'))) ||
            voices.find(v => v.lang === 'en-US') ||
            voices.find(v => v.lang.startsWith('en-'));
        }}
        if ('speechSynthesis' in window) {{
          loadUSVoice();
          window.speechSynthesis.onvoiceschanged = loadUSVoice;
        }}

        function speakWordUS(text, rateOverride = null) {{
          if (!('speechSynthesis' in window) || !text) return;
          window.speechSynthesis.cancel();
          const utter = new SpeechSynthesisUtterance(text);
          utter.lang = 'en-US';
          if (usEnglishVoice) utter.voice = usEnglishVoice;
          utter.rate = rateOverride || speechRate;
          window.speechSynthesis.speak(utter);
        }}

        function toggleSpeed() {{
          speechRate = (speechRate === 1.0) ? 0.7 : 1.0;
          document.getElementById('speedBtn').innerText = speechRate + 'x';
        }}

        function speakCurrent(rate) {{
          if (currentBubbleWord) speakWordUS(currentBubbleWord, rate);
        }}

        function closeBubble() {{
          document.getElementById('gt-bubble').style.display = 'none';
          document.querySelectorAll('.word-active').forEach(el => el.classList.remove('word-active'));
        }}

        function openBubbleAtElement(event, el, token, fullSentence) {{
          event.stopPropagation();
          document.querySelectorAll('.word-active').forEach(x => x.classList.remove('word-active'));
          el.classList.add('word-active');

          const cleanW = (token.w || '').trim();
          const keyLow = cleanW.toLowerCase().replace(/^[^a-z0-9'-]+|[^a-z0-9'-]+$/g, '');
          const basicWordsEs = {{
            "between": {{ ipa: "/bɪˈtwiːn/", pos_es: "Preposición", es: "entre", alt_es: "en medio de", def_es: "Indica relación o espacio que separa dos elementos." }},
            "and": {{ ipa: "/ænd/", pos_es: "Conjunción", es: "y / e", alt_es: "además", def_es: "Une palabras u oraciones." }},
            "the": {{ ipa: "/ðə/", pos_es: "Artículo", es: "el / la / los / las", alt_es: "lo", def_es: "Artículo definido en inglés." }},
            "with": {{ ipa: "/wɪð/", pos_es: "Preposición", es: "con", alt_es: "junto a, mediante", def_es: "Indica compañía, medio o instrumento." }},
            "from": {{ ipa: "/frʌm/", pos_es: "Preposición", es: "de / desde", alt_es: "a partir de", def_es: "Indica origen o procedencia." }},
            "for": {{ ipa: "/fɔːr/", pos_es: "Preposición", es: "para / por / durante", alt_es: "debido a", def_es: "Indica propósito, destinatario o duración." }}
          }};
          const entry = vocabDict[keyLow] || basicWordsEs[keyLow] || {{}};


          currentBubbleWord = cleanW;
          speakWordUS(cleanW, 1.0);

          document.getElementById('b-word').innerText = cleanW;
          document.getElementById('b-ipa').innerText = entry.ipa || '';
          document.getElementById('b-pos').innerText = entry.pos_es || posLabelsEs[token.pos] || 'Inglés (US)';
          document.getElementById('b-es').innerText = entry.es || cleanW;
          document.getElementById('b-alt').innerText = entry.alt_es ? ('Otras traducciones: ' + entry.alt_es) : '';
          document.getElementById('b-def').innerText = entry.def_es || '';

          const exContainer = document.getElementById('b-examples');
          exContainer.innerHTML = '';

          if (fullSentence) {{
            const ctxDiv = document.createElement('div');
            ctxDiv.className = 'ex-item';
            const ctxEn = document.createElement('div');
            ctxEn.className = 'ex-en';
            ctxEn.textContent = '📖 En esta lección: "' + fullSentence + '"';
            ctxDiv.appendChild(ctxEn);
            exContainer.appendChild(ctxDiv);
          }}

          (entry.examples || []).forEach(ex => {{
            const div = document.createElement('div');
            div.className = 'ex-item';
            const dEn = document.createElement('div');
            dEn.className = 'ex-en';
            dEn.textContent = '🇺🇸 ' + (ex.en || '');
            const dEs = document.createElement('div');
            dEs.className = 'ex-es';
            dEs.textContent = '🇪🇸 ' + (ex.es || '');
            div.appendChild(dEn);
            div.appendChild(dEs);
            exContainer.appendChild(div);
          }});

          const bubble = document.getElementById('gt-bubble');
          bubble.style.display = 'block';

          const rect = el.getBoundingClientRect();
          const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
          const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

          const leftPos = Math.min(rect.left + scrollLeft, document.body.clientWidth - 365);
          const topPos = rect.bottom + scrollTop + 6;
          bubble.style.left = Math.max(10, leftPos) + 'px';
          bubble.style.top = topPos + 'px';
        }}

        const container = document.getElementById('lesson-container');
        sentences.forEach((s, idx) => {{
          const box = document.createElement('div');
          box.className = (idx === 0) ? 'title-box' : 'sentence-box';
          const fullSentence = (s.tokens || []).map(t => t.w).join(' ');

          (s.tokens || []).forEach(tok => {{
            const isPunct = /^[.,!?;:"'()—-]+$/.test(tok.w.trim());
            if (isPunct) {{
              box.appendChild(document.createTextNode(tok.w + ' '));
              return;
            }}
            const span = document.createElement('span');
            const posClass = ['verb','noun','adjective','conjunction'].includes(tok.pos) ? 'pos-' + tok.pos : 'pos-other';
            span.className = 'word-token ' + posClass;
            span.textContent = tok.w;

            span.onmouseenter = () => {{
              if (document.getElementById('hoverAudioToggle').checked && lastHovered !== tok.w) {{
                lastHovered = tok.w;
                speakWordUS(tok.w);
              }}
            }};
            span.onmouseleave = () => {{ lastHovered = ""; }};
            span.onclick = (e) => openBubbleAtElement(e, span, tok, fullSentence);
            box.appendChild(span);
          }});

          if (s.sentence_es) {{
            const tr = document.createElement('div');
            tr.className = 'sentence-tr';
            tr.textContent = '🇪🇸 ' + s.sentence_es;
            box.appendChild(tr);
          }}
          container.appendChild(box);
        }});

        document.body.onclick = () => closeBubble();
      </script>
    </body>
    </html>
    """
    altura_dinamica = max(480, min(820, len(sentences_list) * 115 + 160))
    st.iframe(html_code, height=altura_dinamica)

    

def generar_con_maxima_potencia(client, prompt_contenido: str, instruccion_sistema: str = None, as_json: bool = False):
    modelos_potentes = [
        "gemini-3.8-flash",
        "gemini-3.5-pro",
        "gemini-3.1-pro-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash"
    ]
    # Añade automáticamente cualquier otro modelo Gemini activo en tu cuenta como respaldo
    try:
        for m in client.models.list():
            nombre = m.name.replace("models/", "")
            if "gemini" in nombre and not any(x in nombre for x in ["embedding", "imagen", "aqa", "tts", "audio", "2.0"]):
                if nombre not in modelos_potentes:
                    modelos_potentes.append(nombre)
    except Exception:
        pass

    ultimo_error = None
    for modelo in modelos_potentes:
        try:
            cfg_kwargs = {"temperature": 0.65}
            if instruccion_sistema:
                cfg_kwargs["system_instruction"] = instruccion_sistema
            if as_json:
                cfg_kwargs["response_mime_type"] = "application/json"
            config = types.GenerateContentConfig(**cfg_kwargs)
            respuesta = client.models.generate_content(
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

def generar_imagen_garantizada(client_gm, scene_prompt: str, folio_tag: str, cefr_lvl: str, academic_gr: str) -> bytes:
    """Genera ilustración educativa con Hugging Face (FLUX / SDXL) o tarjeta visual académica en Pillow."""
    import re
    import requests
    from PIL import Image, ImageDraw, ImageFont

    st.session_state["last_img_error"] = None
    escena_limpia = re.sub(r'[^a-zA-Z0-9 ,.-]+', ' ', str(scene_prompt or "")).strip()
    escena_limpia = re.sub(r'\s+', ' ', escena_limpia)
    full_prompt = (
        f"Educational textbook illustration, clean digital comic art style, "
        f"bright natural lighting, expressive characters. {escena_limpia}"
    )[:360]

    # Busca HF_TOKEN en cualquier nivel de Secrets
    hf_token = ""
    for k, v in st.secrets.items():
        if isinstance(v, str) and ("HF" in k.upper() or v.strip().startswith("hf_")):
            hf_token = v.strip()
            break
        elif isinstance(v, dict):
            for sub_k, sub_v in v.items():
                if isinstance(sub_v, str) and ("HF" in sub_k.upper() or sub_v.strip().startswith("hf_")):
                    hf_token = sub_v.strip()
                    break
            if hf_token:
                break

    errores = []
    if hf_token:
        headers_hf = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json",
            "User-Agent": "CareerEnglishInstituteApp/1.0"
        }
        modelos_hf = [
            "https://huggingface.co",
            "https://huggingface.co"
        ]
        for url_hf in modelos_hf:
            try:
                r_hf = requests.post(url_hf, headers=headers_hf, json={"inputs": full_prompt}, timeout=28)
                if r_hf.status_code == 200 and len(r_hf.content) > 2000:
                    st.session_state["last_img_error"] = None
                    return r_hf.content
                errores.append(f"HF ({url_hf.split('/')[-1]}) HTTP {r_hf.status_code}")
            except Exception as e_hf:
                errores.append(f"HF error: {e_hf}")
    else:
        errores.append("HF_TOKEN no detectado en Secrets")

    st.session_state["last_img_error"] = " | ".join(errores)

    # Respaldo visual institucional de alta calidad en Pillow (siempre disponible)
    w, h = 800, 420
    img = Image.new("RGB", (w, h), color=(18, 36, 66))
    draw = ImageDraw.Draw(img)
    draw.rectangle([14, 14, w - 14, h - 14], outline=(212, 175, 55), width=4)
    draw.rectangle([28, 28, w - 28, 92], fill=(30, 56, 98))

    font_std = ImageFont.load_default()
    draw.text((46, 50), f"CAREER ENGLISH INSTITUTE  |  {folio_tag}  |  CEFR {cefr_lvl}", fill=(255, 223, 128), font=font_std)

    words = escena_limpia.split()
    lines, curr = [], ""
    for wd in words:
        if len(curr) + len(wd) + 1 <= 76:
            curr = f"{curr} {wd}".strip()
        else:
            lines.append(curr)
            curr = wd
    if curr:
        lines.append(curr)

    y_cursor = 122
    for ln in lines[:8]:
        draw.text((46, y_cursor), ln, fill=(242, 246, 252), font=font_std)
        y_cursor += 28

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()




def generar_quiz_leccion(texto_leccion: str, tema_gramatical: str, nivel_cefr: str, grado_acad: str, evitar_preguntas=None):
    client = init_gemini_client()
    evitar_txt = f"IMPORTANT: Create COMPLETELY DIFFERENT questions from: {evitar_preguntas}" if evitar_preguntas else ""
    prompt_quiz = f"""
    Based on this CEFR Level {nivel_cefr} English lesson tailored for {grado_acad} students, create a 5-question multiple-choice quiz in English calibrated strictly to level {nivel_cefr} and {grado_acad} cognitive level, evaluating comprehension and target grammar ({tema_gramatical}).
    {evitar_txt}
    LESSON TEXT:
    {texto_leccion}
    RETURN ONLY A VALID JSON ARRAY WITH THIS EXACT SCHEMA:
    [{{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A) ..."}}]
    """
    raw_resp, _ = generar_con_maxima_potencia(
        client,
        prompt_quiz,
        instruccion_sistema="Output strictly a valid JSON array only.",
        as_json=True
    )
    cleaned = raw_resp.strip()
    if cleaned.startswith("```"):
        cleaned = next(iter(cleaned.split("\n", 1)[-1].rsplit("```", 1)), "")
    return json.loads(cleaned.strip())

def _serialize_lesson_package(text_val: str, quiz_val, cefr_val: str, grade_val: str, created_val: str) -> str:
    safe_text = text_val[:42000] if len(text_val) > 42000 else text_val
    return json.dumps({
        "text": safe_text,
        "quiz": quiz_val,
        "cefr": cefr_val,
        "grade": grade_val,
        "created_at": created_val
    }, ensure_ascii=False)
    
# --- 10. EVALUACIÓN DINÁMICA DE CAPACIDADES ---
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


# --- 11. BARRA IZQUIERDA (PARÁMETROS ACADÉMICOS) ---
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

    if is_owner:
        st.subheader("🎯 Target Calibration (Owner / Admin)")
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
    
    st.subheader(f"3. Grammar Topics ({next(iter(cefr_level.split()), 'B1')})")
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
    

# --- 12. CABECERA INSTITUCIONAL ---
try:
    default_width = int(saved_cfg["Width"]) if (saved_cfg and saved_cfg.get("Width")) else 115
except (ValueError, TypeError):
    default_width = 115

default_shape = saved_cfg["Shape"] if (saved_cfg and saved_cfg.get("Shape")) else "Circular"
shape_options = ["Original", "Redondeado", "Circular"]
default_shape_idx = shape_options.index(default_shape) if default_shape in shape_options else 2

col_logo, col_title, col_qr, col_exit = st.columns([1.6, 4.9, 2, 1.5])

with col_logo:
    if is_owner and (not is_mobile):
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
    st.title(f"🎓 CEFR {next(iter(cefr_level.split()), 'B1')} ACADEMIC GRAMMAR & DISCOURSE SYSTEM")
    st.caption("Author: Jacob Zumaya Prianti | Applied Linguistics & Proficiency Assessment | APA Style")

with col_qr:
    if is_owner and (not is_mobile):
        btn_qr_txt = "🙈 Ocultar QR" if st.session_state.show_qr else "📱 Mostrar QR"
        if st.button(btn_qr_txt, width="stretch", key="toggle_qr_btn"):
            st.session_state.show_qr = not st.session_state.show_qr
            st.rerun()

        if st.session_state.show_qr:
            app_url = st.secrets.get("APP_BASE_URL", "https://streamlit.app").rstrip("/")
            if st.session_state.current_folio:
                app_url = f"{app_url}/?folio={urllib.parse.quote(st.session_state.current_folio)}"
            
            qr = qrcode.QRCode(version=1, box_size=4, border=1)
            qr.add_data(app_url)
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
# --- 13. BUSCADOR DE FOLIOS Y BOLETÍN DE CALIFICACIONES EN TIEMPO REAL ---
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

# PANEL DESPLEGABLE: CALIFICACIONES, PROMEDIOS Y GRÁFICA POR GRAMMAR TOPIC
if st.session_state.show_gradebook_panel:
    with st.container(border=True):
        st.subheader("📊 Boletín Académico Integral y Desempeño por Grammar Topic")

        if is_owner:
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

        # Selector de Vista General o Filtro por Tópico Gramatical + Descarga PDF Timbrado
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
            pdf_boletin_bytes, timbre_info = create_official_gradebook_pdf(
                alumno_objetivo_gb,
                gb_data,
                topico_seleccionado_gb
            )
            st.download_button(
                label=f"📥 Descargar Boletín Timbrado ({timbre_info['folio_boletin']})",
                data=pdf_boletin_bytes,
                file_name=f"{timbre_info['folio_boletin']}_{gb_data['matricula']}_{alumno_objetivo_gb.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
                width="stretch",
                key="btn_dl_official_gradebook_pdf"
            )
            st.caption(f"🛡️ Timbrado: `{timbre_info['folio_boletin']}` | 📅 `{timbre_info['fecha_generacion']}`")

        # Cálculo de métricas según vista elegida (General o Tópico específico)
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
            conn_f = get_pg_conn()
            row_f = None
            if conn_f:
                from psycopg.rows import dict_row
                with conn_f:
                    with conn_f.cursor(row_factory=dict_row) as cur:
                        cur.execute("""
                            SELECT
                                folio, tema, nivel_cefr, grado_academico, lesson_text,
                                quiz_json, pdf_link,
                                TO_CHAR(created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS fecha
                            FROM lessons_archive
                            WHERE UPPER(TRIM(folio)) = %s
                            LIMIT 1;
                        """, (folio_buscado,))
                        row_f = cur.fetchone()

            if not row_f:
                st.warning(f"⚠️ No se encontró ningún registro con el Folio `{folio_buscado}` en Supabase.")
            else:
                st.session_state.generated_text = str(row_f.get("lesson_text", ""))
                st.session_state.selected_cefr = str(row_f.get("nivel_cefr", "B1 (Intermediate)"))
                st.session_state.selected_academic_grade = str(row_f.get("grado_academico", "Licenciatura / Universidad"))
                st.session_state.current_folio = folio_buscado
                st.session_state.current_pdf_link = str(row_f.get("pdf_link") or "")
                st.session_state.current_creation_date = str(row_f.get("fecha") or "")
                st.session_state.study_mode_active = False
                st.session_state.quiz_graded = False
                st.session_state.quiz_score = None
                st.session_state.quiz_user_answers = {}
                st.session_state.image_bytes = None
                st.session_state.audio_bytes = None

                raw_qz = str(row_f.get("quiz_json") or "").strip()
                if raw_qz:
                    try:
                        qz_obj = json.loads(raw_qz)
                        st.session_state.quiz_data = qz_obj.get("questions") if isinstance(qz_obj, dict) else qz_obj
                    except Exception:
                        st.session_state.quiz_data = None
                else:
                    st.session_state.quiz_data = None

                if st.session_state.generated_text:
                    try:
                        clean_tts = st.session_state.generated_text.replace("*", "").replace("#", "")
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



# --- 14. PANEL DESPLEGABLE DE ADMINISTRACIÓN, CERTIFICADOS Y MATRIZ RBAC ---
if is_owner or is_faculty_desktop:
    btn_txt_admin = (
        "🔼 Cerrar Panel de Administración"
        if st.session_state.get("show_teacher_registry", False)
        else "🛡️ Abrir Panel de Administración, Certificados y Padrón"
    )
    if st.button(btn_txt_admin, type="secondary", width="stretch", key="btn_admin_panel_owner"):
        st.session_state["show_teacher_registry"] = not st.session_state.get("show_teacher_registry", False)
        st.rerun()

if (is_owner or is_faculty_desktop) and st.session_state.get("show_teacher_registry", False):
    with st.container(border=True):
        col_head_reg, col_close_reg = st.columns([4.5, 1])
        with col_head_reg:
            st.markdown("### 🛡️ PANEL DE ADMINISTRACIÓN, CERTIFICADOS Y MATRIZ GLOBAL RBAC")
        with col_close_reg:
            if st.button("🔼 Cerrar Panel", width="stretch", key="btn_close_admin_inner"):
                st.session_state["show_teacher_registry"] = False
                st.rerun()

        tab_certificados, tab_reg_usuarios, tab_matriz_perm, tab_datos_inst = st.tabs([
            "🏅 Certificados (Timbre y QR)",
            "👥 Inscripción y Padrón",
            "🔐 Matriz Global de Permisos",
            "🏛️ Datos del Instituto"
        ])

# 14.1 PESTAÑA CERTIFICADOS
        with tab_certificados:
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
                            grado_sel = ""
                            st.info(
                                f"**Titular:** {nombre_sel}\n\n"
                                f"**Matrícula:** `{clave_sel}` | **Nivel CEFR:** {nivel_sel}"
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
                            base_url = str(st.secrets.get("APP_BASE_URL", "https://streamlit.app")).rstrip("/")
                            link_cert_directo = f"{base_url}/?verify={urllib.parse.quote(f_actual)}"

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


        # 14.2 PESTAÑA INSCRIPCIÓN Y PADRÓN
        with tab_reg_usuarios:
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

        # 14.3 PESTAÑA MATRIZ GLOBAL DE PERMISOS RBAC
        with tab_matriz_perm:

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

    st.divider()

# --- 15. PROCESAMIENTO Y GENERACIÓN DE LECCIÓN CON GEMINI Y POSTGRESQL ---

if generar_btn:
    campos_faltantes = []
    if not str(locals().get("contexto", "")).strip():
        campos_faltantes.append("Contexto / Escenario")
    if not str(locals().get("personas", "")).strip():
        campos_faltantes.append("Personajes / Participantes")
    if not str(locals().get("asunto", "")).strip():
        campos_faltantes.append("Tema / Asunto")
 
    gemini_key_ok = bool(
        st.secrets.get("GEMINI_API_KEY", "")
        or next((sec["GEMINI_API_KEY"] for sec in st.secrets.values() if isinstance(sec, dict) and "GEMINI_API_KEY" in sec), "")
    )
    if not gemini_key_ok:
        st.sidebar.error("⚠️ GEMINI_API_KEY no configurada.")
        st.error("⚠️ Error de configuración: falta GEMINI_API_KEY.")
    elif campos_faltantes:
        lista_faltantes = ", ".join(campos_faltantes)
        st.toast(f"Faltan datos por completar: {lista_faltantes}", icon="⚠️")
        st.sidebar.warning(f"⚠️ Completa los siguientes campos antes de generar:\n\n**{lista_faltantes}**")
        st.warning(f"⚠️ **Datos incompletos:** Por favor llena **{lista_faltantes}** en el panel izquierdo.")
    else:
        # Oculta inmediatamente el panel de administración si estaba abierto
        st.session_state.show_teacher_registry = False

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

        client = init_gemini_client()
        with st.spinner(f"🧠 Normalizing inputs, translating & generating CEFR {cefr_level} ({academic_grade}) Lesson..."):
            try:

                # 1. Traduce y corrige ortográficamente las entradas del usuario para APA
                contexto_en, personas_en, asunto_apa = normalizar_entradas_apa(
                    client, contexto, personas, asunto
                )

                ahora_local = datetime.now(ZoneInfo("America/Hermosillo"))
                nuevo_folio = f"CEI-{ahora_local.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                fecha_creacion = ahora_local.strftime("%Y-%m-%d %H:%M:%S")

                base_url = str(st.secrets.get("APP_BASE_URL", "https://streamlit.app")).rstrip("/")
                pdf_url_directo = f"{base_url}/?folio={urllib.parse.quote(nuevo_folio)}"

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

                texto_gen, mod_usado = generar_con_maxima_potencia(client, prompt_texto, sys_prompt)
                st.session_state.generated_text = texto_gen
                st.session_state.study_mode_active = False
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
                st.session_state.audio_bytes = None
                st.session_state.image_bytes = None

                # 2. Síntesis de audio completo de la lección
                try:
                    clean_tts = texto_gen.replace("*", "").replace("#", "")
                    tts = gTTS(text=clean_tts, lang="en", slow=False)
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.session_state.audio_bytes = audio_fp.getvalue()
                except Exception:
                    st.warning("⚠️ Lección generada, pero el audio no pudo sintetizarse en este momento.")

                # 2b. Generación automática de ilustración educativa con IA
                try:
                    prompt_escena_auto = f"""
                    Write a vivid, friendly visual scene description (45 words) for an educational textbook illustration:
                    Setting: {contexto_en}. Characters: {personas_en}. Topic: {asunto_apa}.
                    Include bright warm lighting, natural interaction, and two short English speech bubbles from the lesson.
                    """
                    desc_escena, _ = generar_con_maxima_potencia(client, prompt_escena_auto)
                    st.session_state.image_bytes = generar_imagen_garantizada(
                        client,
                        desc_escena,
                        f"Folio {nuevo_folio}",
                        cefr_level,
                        academic_grade
                    )
                except Exception:
                    pass

                # 3. Persistencia directa en Supabase PostgreSQL
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

                # Colapsa la barra lateral y recarga para mostrar la lección en pantalla completa
                st.session_state.sidebar_state = "collapsed"
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error al generar lección: {e}")


# --- 16. PANEL CENTRAL (CONTENIDO, MODO ESTUDIO IA, QUIZ Y CONTEXTO VISUAL) ---
if "selected_academic_grade" not in st.session_state:
    st.session_state.selected_academic_grade = st.session_state.get("user_academic_grade", "Licenciatura / Universidad")
if "study_mode_active" not in st.session_state:
    st.session_state.study_mode_active = False

col_main_center, col_tools_right = st.columns([7, 3.5])

with col_main_center:
    col_sub_t, col_badge, col_mode_btn = st.columns([2.6, 1.1, 1.8])
    with col_sub_t:
        st.subheader("📄 Generated Content (APA Format)")
    with col_badge:
        if st.session_state.current_folio:
            st.caption(f"🔖 Folio: `{st.session_state.current_folio}`")
    with col_mode_btn:
        if st.session_state.get("generated_text"):
            btn_study_label = (
                "🖨️ Edición Impresión / PDF"
                if st.session_state.study_mode_active
                else "🧠 Modo Estudio Interactivo (IA)"
            )
            if st.button(
                btn_study_label,
                type="primary" if not st.session_state.study_mode_active else "secondary",
                width="stretch",
                key="btn_toggle_study_mode"
            ):
                st.session_state.study_mode_active = not st.session_state.study_mode_active
                st.rerun()

    if st.session_state.get("generated_text") and st.session_state.study_mode_active:
        with st.spinner("🧠 Preparando análisis sintáctico, pronunciación y diccionario contextual..."):
            estudio_data = analyze_lesson_for_study_mode(
                st.session_state.generated_text,
                st.session_state.get("selected_cefr", "B1")
            )
        if estudio_data:
            render_interactive_study_viewer(estudio_data)
        else:
            st.warning("⚠️ No se pudo generar el análisis interactivo. Mostrando edición de impresión.")
            with st.container(height=420, border=True):
                st.markdown(st.session_state.generated_text)
    else:
        top_container = st.container(height=420, border=True)
        with top_container:
            if st.session_state.get("generated_text"):
                st.markdown(st.session_state.generated_text)
            else:
                st.info("👈 Escribe los datos en Español o Inglés en la barra izquierda y presiona **Generate Lesson**, o busca un **Folio** arriba.")

    # QUIZ INTERACTIVO DE LA LECCIÓN (INTACTO EN AMBOS MODOS)
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
                            st.session_state.generated_text, gramatica_b1,
                            st.session_state.selected_cefr, st.session_state.selected_academic_grade
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
                                    st.session_state.generated_text, gramatica_b1,
                                    st.session_state.selected_cefr, st.session_state.selected_academic_grade, prev_qs
                                )
                                st.session_state.quiz_data = q_new
                                st.session_state.quiz_graded = False
                                st.session_state.quiz_score = None
                                st.session_state.quiz_user_answers = {}
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

with col_tools_right:
    st.subheader(f"🖼️ Visual Context ({st.session_state.selected_academic_grade})")
    if st.session_state.get("generated_text"):
        col_vis_in, col_vis_btn = st.columns([2.8, 1.2])
        with col_vis_in:
            custom_img_prompt = st.text_input(
                "🎨 Descripción personalizada de la escena (Opcional - Español/English):",
                placeholder="Ej: Una oficina con libros, el investigador y el padre sentados hablando...",
                key="input_custom_visual_prompt",
                label_visibility="collapsed"
            )
        with col_vis_btn:
            if st.button("🔄 Generar Nueva Imagen", key="btn_regen_visual", width="stretch"):
                with st.spinner("🎨 Dibujando ilustración con Nano Banana..."):
                    try:
                        client_vis = init_gemini_client()
                        instruccion_usuario = (
                            f"USER CUSTOM VISUAL REQUEST (Translate to English and prioritize this exact setting/characters): {custom_img_prompt.strip()}"
                            if custom_img_prompt.strip()
                            else "Create a fresh, different visual scene angle based on the lesson."
                        )
                        prompt_nueva_escena = f"""
                        Read the English lesson below and write a vivid visual scene description (45-55 words) for an educational comic illustration:
                        {instruccion_usuario}
                        1. SETTING & FURNITURE: Describe the physical background, furniture, and atmosphere in warm detail.
                        2. CHARACTERS & ACTION: Describe the characters interacting naturally in that setting.
                        3. SPEECH BUBBLES: Include two short, clear English dialogue lines from the lesson in double quotes.
                        
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
                None, st.session_state.generated_text[:120],
                f"Folio {st.session_state.current_folio}", st.session_state.selected_cefr, st.session_state.selected_academic_grade
            )
            st.image(fallback_img, width="stretch")
        else:
            st.caption("La imagen ilustrativa aparecerá aquí / The illustrative image will appear here.")



# --- 17. PANEL DERECHO (AUDIO, VIDEO, EXPORTACIÓN PDF E HISTORIAL) ---
with col_tools_right:
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
        st.iframe(video_recorder_html, height=320)

        st.write("")
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
                            if speaking_row is not None and int(speaking_row) > 0:
                                st.caption(f"🎙️ **Mejor Evaluación Oral:** `{speaking_row}%`")

                            # Botón para cargar esta lección directamente en pantalla (y usar Modo Estudio IA)
                            if st.button(f"📖 Cargar Lección ({folio_item})", key=f"load_fol_{folio_item}_{idx_h}", width="stretch"):
                                st.session_state.generated_text = str(row.get("Texto", ""))
                                st.session_state.current_folio = folio_item
                                st.session_state.selected_cefr = str(row.get("Nivel_CEFR", "B1"))
                                st.session_state.selected_academic_grade = str(row.get("Grado_Academico", "Licenciatura / Universidad"))
                                st.session_state.study_mode_active = False
                                st.session_state.quiz_graded = False
                                st.session_state.quiz_score = None
                                st.session_state.quiz_user_answers = {}
                                raw_qz = str(row.get("Quiz_JSON") or "").strip()
                                if raw_qz:
                                    try:
                                        qz_obj = json.loads(raw_qz)
                                        st.session_state.quiz_data = qz_obj.get("questions")
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
        st.query_params.clear()
        st.session_state.sidebar_state = "expanded"
        st.rerun()


# --- 18. PIE DE PÁGINA INSTITUCIONAL ---
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
