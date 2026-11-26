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
import time
import subprocess
import sys
import urllib.parse
import urllib.request
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

st.set_page_config(
    page_title="CEI English Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if hasattr(st, "iframe"):
    components.html = lambda html_str, height=None, scrolling=False, width=None: st.iframe(
        html_str, height=height or 150, width=width or "stretch"
    )
from streamlit_js_eval import streamlit_js_eval

try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
except ImportError:
    try:
        from streamlit.runtime.scriptrunner_utils.script_run_context import add_script_run_ctx, get_script_run_ctx
    except ImportError:
        add_script_run_ctx = None
        get_script_run_ctx = None

from core.database import (
    _open_legal_pg_conn,
    get_user_delegated_caps_pg,
    save_user_delegated_caps_pg,
)
from modules.franchises import (
    DEFAULT_CAMPUS_ID,
    ensure_multicampus_schema_pg,
    list_campuses_pg,
    upsert_campus_pg,
)

from modules.pedagogy import (
    CEFR_DESCRIPTIONS,
    CEFR_LEVELS_ORDER,
    build_whatsapp_motivation_link,
    calcular_categoria_automatica_estudiante,
    calcular_racha_semanal,
    normalize_cefr_code,
)

rol_main_low = str(st.session_state.get("user_role") or "").strip().lower()
is_owner_o_admin_main = bool(
    st.session_state.get("authenticated", False)
    and (
        st.session_state.get("is_owner", False)
        or rol_main_low in ["propietario", "owner", "administrador", "admin"]
    )
)


if not is_owner_o_admin_main:
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="manage-app-button"],
        #MainMenu,
        footer,
        div[class*="viewerBadge"],
        div[class*="profileContainer"],
        div[class*="profilePreview"],
        a[href*="streamlit.io/cloud"],
        a[href*="share.streamlit.io"],
        a[href*="github.com"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    components.html(
        """
        <script>
        (function ocultarBadgesCEI() {
            const selectors = [
                '[data-testid="manage-app-button"]',
                '[data-testid="stStatusWidget"]',
                'div[class*="viewerBadge"]',
                'div[class*="profileContainer"]',
                'div[class*="profilePreview"]',
                'a[href*="streamlit.io/cloud"]',
                'a[href*="share.streamlit.io"]',
                'a[href*="github.com"]'
            ];
            function limpiar(doc) {
                if (!doc) return;
                selectors.forEach(sel => {
                    doc.querySelectorAll(sel).forEach(el => {
                        el.style.setProperty('display', 'none', 'important');
                        el.style.setProperty('visibility', 'hidden', 'important');
                        el.style.setProperty('opacity', '0', 'important');
                    });
                });
            }
            const run = () => {
                limpiar(document);
                try { limpiar(window.parent.document); } catch (e) {}
                try { limpiar(window.top.document); } catch (e) {}
            };
            run();
            setInterval(run, 800);
        })();
        </script>
        """,
        height=0
    )
else:
    components.html(
        """
        <script>
        (function restaurarBadgesOwnerAdmin() {
            const selectors = [
                '[data-testid="manage-app-button"]',
                '[data-testid="stStatusWidget"]',
                'div[class*="viewerBadge"]',
                'div[class*="profileContainer"]',
                'div[class*="profilePreview"]',
                'a[href*="streamlit.io/cloud"]',
                'a[href*="share.streamlit.io"]',
                'a[href*="github.com"]'
            ];
            function restaurar(doc) {
                if (!doc) return;
                selectors.forEach(sel => {
                    doc.querySelectorAll(sel).forEach(el => {
                        el.style.removeProperty('display');
                        el.style.removeProperty('visibility');
                        el.style.removeProperty('opacity');
                    });
                });
            }
            try { restaurar(window.parent.document); } catch (e) {}
            try { restaurar(window.top.document); } catch (e) {}
        })();
        </script>
        """,
        height=0
    )


# ==============================================================================
# PANTALLA DE INSTALACIÓN INTELIGENTE POR DISPOSITIVO (QR DE DESCARGA APP CEI)
# ==============================================================================
def render_install_app_landing():
    """Muestra la tarjeta oficial de instalación de la App CEI 100% ajustada a pantalla móvil."""
    st.markdown(
        """
        <style>
            html, body, [data-testid="stAppViewContainer"] {
                overflow-x: hidden !important;
                max-width: 100vw !important;
            }
            #MainMenu, footer, header[data-testid="stHeader"],
            [data-testid="stToolbar"], [data-testid="stDecoration"],
            [data-testid="manage-app-button"],
            div[class*="viewerBadge"], div[class*="StatusWidget"],
            div[class*="_profileContainer"], div[class*="_profilePreview"],
            a[href*="streamlit.io"], a[href*="github.com"],
            iframe[title="streamlit_badge"] {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    logo_path = "static/LOGO CEI APP.png" if os.path.exists("static/LOGO CEI APP.png") else "LOGO CEI APP.png"

    with st.container(border=True):
        c_l1, c_l2 = st.columns([1.0, 2.8])
        with c_l1:
            if os.path.exists(logo_path):
                st.image(logo_path, width=95)
        with c_l2:
            st.markdown("### 📲 Instalar App Oficial — Career English Institute (CEI)")
            st.caption("Versión Oficial Móvil y Escritorio • Escudo Institucional Preconfigurado")

        st.divider()

        st.iframe(
            """
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    width: 100%;
                    overflow-x: hidden;
                    padding: 4px;
                }
                @keyframes pulseCEI {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.02); }
                    100% { transform: scale(1); }
                }
            </style>
            <div style="width:100%; text-align:center;">
                <button id="btnNativeInstallCEI" type="button" style="
                    background: linear-gradient(135deg, #0b2545 0%, #1e40af 100%);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 16px 18px;
                    font-size: 16px;
                    font-weight: 700;
                    cursor: pointer;
                    box-shadow: 0 4px 14px rgba(11, 37, 69, 0.28);
                    width: 100%;
                    display: block;
                ">
                    📲 INSTALAR APP OFICIAL CEI
                </button>
                <div id="installHintCEI" style="
                    color: #78350f;
                    background: #fef9c3;
                    border: 1.5px solid #facc15;
                    border-radius: 10px;
                    padding: 12px 14px;
                    font-size: 13.5px;
                    margin-top: 12px;
                    line-height: 1.5;
                    text-align: left;
                    width: 100%;
                    word-wrap: break-word;
                "></div>
            </div>
            <script>
                (function() {
                    const pWin = window.parent;
                    const hideCloudBadges = () => {
                        const docs = [document, pWin.document];
                        try { if (pWin.parent && pWin.parent.document) docs.push(pWin.parent.document); } catch(e) {}
                        docs.forEach(d => {
                            d.querySelectorAll(
                                '[data-testid="manage-app-button"], [class*="viewerBadge"], [class*="StatusWidget"], [class*="_profileContainer"], [class*="_profilePreview"], a[href*="streamlit.io"], a[href*="github.com"]'
                            ).forEach(el => el.style.setProperty('display', 'none', 'important'));
                        });
                    };
                    hideCloudBadges();
                    setInterval(hideCloudBadges, 600);

                    const btn = document.getElementById('btnNativeInstallCEI');
                    const hint = document.getElementById('installHintCEI');
                    const ua = navigator.userAgent || '';
                    const isInApp = /WhatsApp|Instagram|FBAN|FBAV|Line/i.test(ua);
                    const isIOS = /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
                    const isAndroid = /Android/i.test(ua);
                    const isMacSafari = /Macintosh/.test(ua) && /Safari/.test(ua) && !/Chrome/.test(ua);

                    const showStepGuide = (highlight) => {
                        if (highlight) {
                            hint.style.background = '#fef08a';
                            hint.style.borderColor = '#eab308';
                            hint.style.animation = 'pulseCEI 0.4s ease';
                            setTimeout(() => { hint.style.animation = 'none'; }, 450);
                        }
                        if (isInApp) {
                            hint.innerHTML = '⚠️ <b>Abriste este QR dentro de WhatsApp/Redes:</b><br>1. Toca los <b>3 puntos (⋮)</b> o el ícono de <b>brújula</b>.<br>2. Elige <b>"Abrir en Safari"</b> (iPhone) o <b>"Abrir en Chrome"</b> (Android).';
                        } else if (isIOS) {
                            hint.innerHTML = '🍎 <b>Instalación en iPhone / iPad (2 pasos):</b><br>1. Toca el ícono <b>Compartir (⬆️)</b> en la barra inferior de Safari.<br>2. Desliza y toca <b>"Agregar a inicio"</b> → <b>Agregar</b>.';
                        } else if (isMacSafari) {
                            hint.innerHTML = '💻 <b>Instalación en Mac Safari:</b><br>En la barra superior haz clic en <b>Archivo → Agregar al Dock</b> y pulsa <b>Agregar</b>.';
                        } else if (isAndroid) {
                            hint.innerHTML = '🤖 <b>Instalación en Android (Chrome):</b><br>1. Toca el menú de <b>3 puntos (⋮)</b> arriba a la derecha.<br>2. Selecciona <b>"Instalar aplicación"</b> o <b>"Agregar a pantalla principal"</b>.';
                        } else {
                            hint.innerHTML = '💻 <b>Instalación en Computadora:</b><br>Haz clic en el ícono de <b>Instalar (⊕)</b> en el extremo derecho de la barra de direcciones.';
                        }
                    };
                    showStepGuide(false);

                    const onPromptReady = (e) => {
                        e.preventDefault();
                        pWin.__ceiDeferredPrompt = e;
                        btn.innerText = '⬇️ INSTALAR APP OFICIAL CEI (1 CLIC)';
                        hint.style.background = '#dbeafe';
                        hint.style.borderColor = '#3b82f6';
                        hint.style.color = '#1e3a8a';
                        hint.innerHTML = '✅ <b>Instalación directa lista:</b> Pulsa el botón azul superior y confirma <b>"Instalar"</b>.';
                    };

                    window.addEventListener('beforeinstallprompt', onPromptReady);
                    pWin.addEventListener('beforeinstallprompt', onPromptReady);

                    btn.addEventListener('click', async () => {
                        const promptEvt = pWin.__ceiDeferredPrompt;
                        if (promptEvt) {
                            promptEvt.prompt();
                            const choice = await promptEvt.userChoice;
                            if (choice.outcome === 'accepted') {
                                hint.style.background = '#dcfce7';
                                hint.style.borderColor = '#22c55e';
                                hint.style.color = '#14532d';
                                hint.innerHTML = '🎉 <b>¡App Oficial CEI instalada!</b> Busca el escudo de CEI en tu pantalla de inicio.';
                            }
                            pWin.__ceiDeferredPrompt = null;
                        } else {
                            btn.innerText = '👇 SIGUE ESTOS 2 PASOS ABAJO';
                            showStepGuide(true);
                        }
                    });
                })();
            </script>
            """,
            height=265
        )



if str(st.query_params.get("install", "")).strip() in ["1", "true", "app"]:
    render_install_app_landing()
    st.stop()



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
    "Ver_Panel_Educativo",
    "Ver_Portal_Docente",
    "Ver_Mis_Estudiantes_Docente",
    "Motivar_Estudiantes_WhatsApp",
    "Asignar_Retroalimentacion_Docente",
    "Ver_Comisiones_Pagos_Docente",
    "Gestionar_Compliance_Legal",
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
    "Gestionar_IVA_Mensualidad",
    "Gestionar_Pagos_Cobranza",
    "Editar_Terminos_Afiliacion"
]

DEFAULT_PERMISSIONS_MATRIX = {
    "Total": {c: True for c in CAPABILITY_COLS},
    "Academico": {
        **{c: False for c in CAPABILITY_COLS},
        "Ver_Panel_Educativo": True,
        "Ver_Portal_Docente": True,
        "Ver_Mis_Estudiantes_Docente": True,
        "Motivar_Estudiantes_WhatsApp": True,
        "Asignar_Retroalimentacion_Docente": True,
        "Ver_Comisiones_Pagos_Docente": True,
        "Ver_Panel_Admin": True,
        "Registrar_Usuarios": True,
        "Gestionar_Usuarios": True,
        "Emitir_Certificados": True,
        "Previsualizar_A1_C2": True,
        "Reuso_Ilimitado_Folios": True
    },
    "Docente": {
        **{c: False for c in CAPABILITY_COLS},
        "Ver_Panel_Educativo": True,
        "Ver_Portal_Docente": True,
        "Ver_Mis_Estudiantes_Docente": True,
        "Motivar_Estudiantes_WhatsApp": True,
        "Asignar_Retroalimentacion_Docente": True,
        "Ver_Comisiones_Pagos_Docente": True,
        "Previsualizar_A1_C2": True,
        "Reuso_Ilimitado_Folios": True
    },
    "Certificador": {
        **{c: False for c in CAPABILITY_COLS},
        "Ver_Panel_Educativo": True,
        "Ver_Panel_Admin": True,
        "Emitir_Certificados": True,
        "Revocar_Certificados": True,
        "Reuso_Ilimitado_Folios": True
    },
    "Auditoria": {
        **{c: False for c in CAPABILITY_COLS},
        "Ver_Panel_Educativo": True,
        "Ver_Portal_Docente": True,
        "Ver_Mis_Estudiantes_Docente": True,
        "Ver_Comisiones_Pagos_Docente": True,
        "Gestionar_Compliance_Legal": True,
        "Ver_Panel_Admin": True,
        "Previsualizar_A1_C2": True,
        "Reuso_Ilimitado_Folios": True
    },
    "Basico": {
        **{c: False for c in CAPABILITY_COLS},
        "Ver_Panel_Educativo": True
    }
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
    u_clean = str(usuario_name or st.session_state.get("current_user") or "").strip()
    f_clean = str(folio or "").strip().upper()
    if not f_clean:
        return
    with pg_session(dict_rows=True) as cur:
        cur.execute("""
            ALTER TABLE lessons_folios
            ADD COLUMN IF NOT EXISTS usuario TEXT DEFAULT '',
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        """)
        cur.execute(
            """
            SELECT id FROM users_padron
            WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s))
            LIMIT 1;
            """,
            (u_clean,)
        )
        u_row = cur.fetchone()
        uid = int(u_row["id"]) if (isinstance(u_row, dict) and u_row.get("id") is not None) else None

        cur.execute("""
            INSERT INTO lessons_folios (folio, user_id, usuario, tema, cefr_level, academic_grade, lesson_text, pdf_link, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (folio) DO UPDATE SET
                user_id = COALESCE(EXCLUDED.user_id, lessons_folios.user_id),
                usuario = EXCLUDED.usuario,
                tema = EXCLUDED.tema,
                cefr_level = EXCLUDED.cefr_level,
                academic_grade = EXCLUDED.academic_grade,
                lesson_text = EXCLUDED.lesson_text,
                pdf_link = EXCLUDED.pdf_link,
                updated_at = CURRENT_TIMESTAMP;
        """, (f_clean, uid, u_clean, tema, cefr, grado, texto, pdf_link))
    try:
        load_lessons_history_pg.clear()
    except Exception:
        pass


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
            try:
                load_lessons_history_pg.clear()
            except Exception:
                pass
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
            try:
                load_lessons_history_pg.clear()
            except Exception:
                pass
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
        load_lessons_history_pg.clear()
    except Exception:
        pass

# ==============================================================================
# PARTE 4B: CONSULTA DE FOLIOS, VIDEO/APA 7 Y LIBRETA POR GRAMMAR TOPIC (PG)
# ==============================================================================
@st.cache_resource(show_spinner=False)
def ensure_video_summary_schema_pg() -> bool:
    """Agrega columnas de Video (25%) y Resumen APA 7 (15%) en lessons_folios sin afectar datos."""
    try:
        with pg_session() as cur:
            cur.execute("""
                ALTER TABLE lessons_folios
                ADD COLUMN IF NOT EXISTS video_url TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS video_title TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS video_channel TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS video_duration_sec INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS video_watched_sec INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS video_score_100 NUMERIC(5,2) DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS summary_text TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS apa7_reference TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS summary_score_100 NUMERIC(5,2) DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS summary_eval_json JSONB;
            """)
        return True
    except Exception:
        return False


ensure_video_summary_schema_pg()


def save_video_and_summary_pg(
    folio_code: str,
    video_info: dict = None,
    watched_sec: int = None,
    video_score_100: float = None,
    summary_text: str = None,
    apa7_reference: str = None,
    summary_score_100: float = None,
    summary_eval_dict: dict = None
) -> bool:
    """Guarda metadatos del video, tiempo visto (25%) y resumen APA 7 (15%) en lessons_folios."""
    fol = str(folio_code or "").strip().upper()
    if not fol:
        return False
    ensure_video_summary_schema_pg()
    try:
        with pg_session() as cur:
            if video_info:
                cur.execute("""
                    UPDATE lessons_folios
                    SET video_url = COALESCE(NULLIF(%s, ''), video_url),
                        video_title = COALESCE(NULLIF(%s, ''), video_title),
                        video_channel = COALESCE(NULLIF(%s, ''), video_channel),
                        video_duration_sec = CASE WHEN %s > 0 THEN %s ELSE video_duration_sec END
                    WHERE UPPER(TRIM(folio)) = %s;
                """, (
                    str(video_info.get("url") or ""),
                    str(video_info.get("title") or ""),
                    str(video_info.get("channel") or ""),
                    int(video_info.get("duration_sec") or 0),
                    int(video_info.get("duration_sec") or 0),
                    fol
                ))
            if watched_sec is not None and video_score_100 is not None:
                cur.execute("""
                    UPDATE lessons_folios
                    SET video_watched_sec = GREATEST(COALESCE(video_watched_sec, 0), %s),
                        video_score_100 = GREATEST(COALESCE(video_score_100, 0), %s)
                    WHERE UPPER(TRIM(folio)) = %s;
                """, (int(watched_sec), float(video_score_100), fol))
            if summary_text is not None and apa7_reference is not None and summary_score_100 is not None:
                cur.execute("""
                    UPDATE lessons_folios
                    SET summary_text = %s,
                        apa7_reference = %s,
                        summary_score_100 = GREATEST(COALESCE(summary_score_100, 0), %s),
                        summary_eval_json = %s::jsonb
                    WHERE UPPER(TRIM(folio)) = %s;
                """, (
                    str(summary_text),
                    str(apa7_reference),
                    float(summary_score_100),
                    json.dumps(summary_eval_dict or {}, ensure_ascii=False),
                    fol
                ))
        load_lessons_history_pg.clear()
        return True
    except Exception:
        return False


def fetch_lesson_by_folio(folio_code: str) -> dict | None:
    folio_clean = str(folio_code or "").strip().upper()
    if not folio_clean:
        return None
    ensure_video_summary_schema_pg()
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
                sum_raw = r.get("summary_eval_json")
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
                    "Video_URL": r.get("video_url") or "",
                    "Video_Title": r.get("video_title") or "",
                    "Video_Channel": r.get("video_channel") or "",
                    "Video_Duration_Sec": int(r.get("video_duration_sec") or 0),
                    "Video_Watched_Sec": int(r.get("video_watched_sec") or 0),
                    "Video_Score": float(r.get("video_score_100") or 0.0),
                    "Summary_Text": r.get("summary_text") or "",
                    "APA7_Reference": r.get("apa7_reference") or "",
                    "Summary_Score": float(r.get("summary_score_100") or 0.0),
                    "Summary_Eval": sum_raw if isinstance(sum_raw, dict) else (json.loads(sum_raw) if sum_raw else None),
                    "PDF_Link": r.get("pdf_link") or "",
                    "Created_At": r.get("fecha_fmt") or ""
                }
    except Exception:
        pass
    return None


@st.cache_data(ttl=30, show_spinner=False)
def load_lessons_history_pg() -> list[dict]:
    ensure_video_summary_schema_pg()
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                ALTER TABLE lessons_folios
                ADD COLUMN IF NOT EXISTS usuario TEXT DEFAULT '';
            """)
            cur.execute("""
                UPDATE lessons_folios f
                SET user_id = u.id
                FROM users_padron u
                WHERE f.user_id IS NULL
                  AND TRIM(COALESCE(f.usuario, '')) <> ''
                  AND LOWER(TRIM(f.usuario)) = LOWER(TRIM(u.usuario));
            """)
            cur.execute("""
                SELECT
                    f.folio AS "Folio",
                    COALESCE(NULLIF(TRIM(u.usuario), ''), NULLIF(TRIM(f.usuario), ''), 'Usuario') AS "Usuario",
                    f.tema AS "Tema",
                    f.cefr_level AS "Nivel_CEFR",
                    f.academic_grade AS "Grado_Academico",
                    f.lesson_text AS "Texto",
                    f.quiz_data AS "Quiz_JSON",
                    f.best_quiz_score AS "Mejor_Calificacion_PDF",
                    f.best_speaking_score AS "Speaking_Score",
                    f.speaking_eval_json AS "Speaking_Eval",
                    COALESCE(f.video_score_100, 0) AS "Video_Score",
                    COALESCE(f.summary_score_100, 0) AS "Summary_Score",
                    f.pdf_link AS "PDF_Link",
                    TO_CHAR(f.created_at AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS "Fecha_de_subida"
                FROM lessons_folios f
                LEFT JOIN users_padron u ON f.user_id = u.id
                ORDER BY f.created_at DESC
                LIMIT 200;
            """)
            return cur.fetchall()
    except Exception:
        return []

def fetch_student_gradebook_pg(target_usuario: str) -> dict:
    """Calcula promedios y rúbrica oficial (Quiz 35%, Audio 25%, Video 25%, Resumen APA 7 15%)."""
    default_res = {
        "matricula": "CEI-2026-0000",
        "nivel_cefr": "B1 (Intermediate)",
        "grado": "",
        "records": [],
        "topic_summary": [],
        "overall_avg": 0.0,
        "quiz_avg": 0.0,
        "oral_avg": 0.0,
        "video_avg": 0.0,
        "summary_avg": 0.0,
        "rubric_weights": {
            "Quiz": 35,
            "Audio": 25,
            "Ver Video": 25,
            "Resumen APA 7": 15
        }
    }
    ensure_video_summary_schema_pg()
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT id,
                       COALESCE(NULLIF(TRIM(matricula), ''), 'CEI-2026-' || LPAD(id::text, 4, '0')) AS matricula,
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
                    COALESCE(f.video_score_100, -1) AS video_score,
                    COALESCE(f.summary_score_100, -1) AS summary_score,
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
    todas_quiz, todas_oral, todas_video, todas_summary, todas_combinadas = [], [], [], [], []

    for r in rows:
        q_pct = _parse_quiz_pct(r.get("best_quiz_score"))
        o_raw = float(r.get("speaking_score") if r.get("speaking_score") is not None else -1)
        o_pct = o_raw if o_raw > 0 else None

        v_raw = float(r.get("video_score") if r.get("video_score") is not None else -1)
        v_pct = v_raw if v_raw > 0 else None

        s_raw = float(r.get("summary_score") if r.get("summary_score") is not None else -1)
        s_pct = s_raw if s_raw > 0 else None

        # Cálculo ponderado oficial: Quiz 35% + Audio 25% + Ver Video 25% + Resumen APA 7 15%
        hay_evaluacion = any(x is not None for x in [q_pct, o_pct, v_pct, s_pct])
        if hay_evaluacion:
            pts_q = ((q_pct or 0.0) * 0.35)
            pts_o = ((o_pct or 0.0) * 0.25)
            pts_v = ((v_pct or 0.0) * 0.25)
            pts_s = ((s_pct or 0.0) * 0.15)
            prom_leccion = round(pts_q + pts_o + pts_v + pts_s, 1)
        else:
            prom_leccion = None

        if q_pct is not None:
            todas_quiz.append(q_pct)
        if o_pct is not None:
            todas_oral.append(o_pct)
        if v_pct is not None:
            todas_video.append(v_pct)
        if s_pct is not None:
            todas_summary.append(s_pct)
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
            "Quiz (35%)": f"{q_pct}% ({round(q_pct*0.35,1)} pts)" if q_pct is not None else "Pendiente",
            "Audio (25%)": f"{o_pct}% ({round(o_pct*0.25,1)} pts)" if o_pct is not None else "Pendiente",
            "Video (25%)": f"{v_pct}% ({round(v_pct*0.25,1)} pts)" if v_pct is not None else "Pendiente",
            "Resumen APA7 (15%)": f"{s_pct}% ({round(s_pct*0.15,1)} pts)" if s_pct is not None else "Pendiente",
            "Calificación_Final": f"{prom_leccion}%" if prom_leccion is not None else "Sin evaluar"
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
        "oral_avg": round(sum(todas_oral) / len(todas_oral), 1) if todas_oral else 0.0,
        "video_avg": round(sum(todas_video) / len(todas_video), 1) if todas_video else 0.0,
        "summary_avg": round(sum(todas_summary) / len(todas_summary), 1) if todas_summary else 0.0,
        "rubric_weights": {
            "Quiz": 35,
            "Audio": 25,
            "Ver Video": 25,
            "Resumen APA 7": 15
        }
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

    app_base_url = str(
        st.secrets.get("PUBLIC_APP_URL")
        or st.secrets.get("APP_PUBLIC_URL")
        or st.secrets.get("APP_BASE_URL")
        or "https://streamlit.app"
    ).strip().rstrip("/")
    verify_url = f"{app_base_url}/?verify_transcript={urllib.parse.quote(folio_bol)}"

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
        for rel_p in ["LOGO CEI APP.png", os.path.join("static", "LOGO CEI APP.png")]:
            cand_logo = os.path.join(base_dir, rel_p)
            if os.path.exists(cand_logo):
                logo_src = cand_logo
                break


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
            self.cell(186, 4, clean_pdf_text(f"© 2026 CAREER ENGLISH INSTITUTE |Fundador CEI y Creador de 🎓 CEI ENGLISH LEARNING PLATFORM: Jacob Zumaya Prianti | APA 7th Ed. Standard | Page {self.page_no()}"), new_x="LMARGIN", new_y="NEXT", align="C")
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

    # Resumen Ejecutivo de Promedios (5 columnas equilibradas = 186 mm)
    pdf.set_fill_color(242, 245, 250)
    pdf.set_draw_color(26, 42, 68)
    pdf.rect(12, pdf.get_y(), 186, 15, style="DF")
    y_box = pdf.get_y() + 3.5
    pdf.set_xy(13, y_box)
    pdf.set_font("Times", "B", 9.5)
    pdf.set_text_color(26, 42, 68)
    pdf.cell(38, 8, f"Overall: {gb_data.get('overall_avg', 0.0)}%", align="C")
    pdf.cell(37, 8, f"Quiz: {gb_data.get('quiz_avg', 0.0)}%", align="C")
    pdf.cell(37, 8, f"Audio: {gb_data.get('oral_avg', 0.0)}%", align="C")
    pdf.cell(37, 8, f"Video: {gb_data.get('video_avg', 0.0)}%", align="C")
    pdf.cell(35, 8, f"Summary: {gb_data.get('summary_avg', 0.0)}%", align="C")
    pdf.ln(15)

    # TABLA 1: RÚBRICA INSTITUCIONAL DE EVALUACIÓN (APA 7)
    pdf.set_font("Times", "B", 10.5)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 5.5, "Table 1", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "I", 10)
    pdf.cell(0, 5.5, "Institutional Assessment Rubric & Weighting Criteria (APA 7th Edition Standard)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Times", "B", 9)
    pdf.set_draw_color(20, 20, 20)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.cell(62, 6.5, "Assessment Component", align="L")
    pdf.cell(96, 6.5, "Academic Requirement & Evaluation Metric", align="L")
    pdf.cell(28, 6.5, "Weight (%)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())

    rubrica_filas = [
        ("1. Lesson Comprehension Quiz", "Multiple-choice grammar & reading comprehension assessment", "35%"),
        ("2. Oral Pronunciation & Audio", "AI phonetic articulation, fluency, prosody & accuracy evaluation", "25%"),
        ("3. Educational Video Viewing", "Verified watch duration in minutes proportional to video length", "25%"),
        ("4. Written Summary & APA 7 Ref.", "120-125 word academic English summary + APA 7th Ed. citation", "15%"),
    ]
    pdf.set_font("Times", "", 8.8)
    for comp_name, comp_desc, comp_w in rubrica_filas:
        pdf.cell(62, 5.8, clean_pdf_text(comp_name), align="L")
        pdf.cell(96, 5.8, clean_pdf_text(comp_desc), align="L")
        pdf.cell(28, 5.8, comp_w, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.set_font("Times", "B", 9)
    pdf.cell(158, 6, "Total Weighted Coursework Score", align="R")
    pdf.cell(28, 6, "100%", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(4.5)

    # TABLA 2: DOMINIO POR GRAMMAR TOPIC
    pdf.set_font("Times", "B", 10.5)
    pdf.cell(0, 5.5, "Table 2", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "I", 10)
    pdf.cell(0, 5.5, clean_pdf_text(f"Applied Grammar Competency Breakdown by CEFR {gb_data.get('nivel_cefr')} Topic"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Times", "B", 9)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.cell(124, 6.5, "Grammar Topic", align="L")
    pdf.cell(18, 6.5, "Lessons", align="C")
    pdf.cell(22, 6.5, "Mastery", align="C")
    pdf.cell(22, 6.5, "Status", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())

    pdf.set_font("Times", "", 8.8)
    temas_pdf = gb_data.get("topic_summary", [])
    if topic_filter != "Vista General":
        temas_pdf = [t for t in temas_pdf if t["Grammar Topic"] == topic_filter]

    for t_row in temas_pdf:
        pdf.cell(124, 5.8, clean_pdf_text(t_row["Grammar Topic"])[:68], align="L")
        pdf.cell(18, 5.8, str(t_row["Lecciones"]), align="C")
        pdf.cell(22, 5.8, f"{t_row['Dominio (%)']}%", align="C")
        pdf.cell(22, 5.8, clean_pdf_text(t_row["Estatus"]), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(4.5)

    # TABLA 3: ARCHIVO CRONOLÓGICO CON QUIZ (35%), AUDIO (25%), VIDEO (25%) Y RESUMEN (15%)
    pdf.set_font("Times", "B", 10.5)
    pdf.cell(0, 5.5, "Table 3", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Times", "I", 10)
    pdf.cell(0, 5.5, "Chronological Archive of Assessed Lessons, Video Duration & APA 7 Summary Scores", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Times", "B", 8.2)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.cell(34, 6.5, "Folio", align="L")
    pdf.cell(52, 6.5, "Grammar Topic", align="L")
    pdf.cell(20, 6.5, "Quiz 35%", align="C")
    pdf.cell(20, 6.5, "Audio 25%", align="C")
    pdf.cell(20, 6.5, "Video 25%", align="C")
    pdf.cell(20, 6.5, "Sum. 15%", align="C")
    pdf.cell(20, 6.5, "Final", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())

    pdf.set_font("Times", "", 8.0)
    recs_pdf = gb_data.get("records", [])
    if topic_filter != "Vista General":
        recs_pdf = [r for r in recs_pdf if r["Grammar_Topic"] == topic_filter]

    def _short_cell(val_str: str) -> str:
        s = str(val_str or "").strip()
        if "%" in s:
            return s.split("%") + "%"
        return "Pend."

    for r_item in recs_pdf:
        q_txt = _short_cell(r_item.get("Quiz (35%)") or r_item.get("Quiz_Pct"))
        o_txt = _short_cell(r_item.get("Audio (25%)") or r_item.get("Oral_Pct"))
        v_txt = _short_cell(r_item.get("Video (25%)"))
        s_txt = _short_cell(r_item.get("Resumen APA7 (15%)"))
        f_txt = str(r_item.get("Calificación_Final") or r_item.get("Promedio_Leccion") or "Pend.")
        if f_txt == "Sin evaluar":
            f_txt = "Pend."

        pdf.cell(34, 5.8, clean_pdf_text(r_item["Folio"]), align="L")
        pdf.cell(52, 5.8, clean_pdf_text(r_item["Grammar_Topic"])[:34], align="L")
        pdf.cell(20, 5.8, clean_pdf_text(q_txt), align="C")
        pdf.cell(20, 5.8, clean_pdf_text(o_txt), align="C")
        pdf.cell(20, 5.8, clean_pdf_text(v_txt), align="C")
        pdf.cell(20, 5.8, clean_pdf_text(s_txt), align="C")
        pdf.cell(20, 5.8, clean_pdf_text(f_txt), align="C", new_x="LMARGIN", new_y="NEXT")
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
# PARTE 7B2: MOTORES DE IA CON GEMINI (TEXTO, QUIZ, PRONUNCIACIÓN Y VIDEO)
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

# ==============================================================================
# MOTOR DE VIDEO EDUCATIVO MULTI-NAVEGADOR (BRAVE, FIREFOX, OPERA, GOOGLE) + DICCIONARIO CEFR
# ==============================================================================
CURATED_CEFR_VIDEO_DICT = {
    "present simple": {"video_id": "L9AWrJnhsRI", "title": "Present Simple Tense - English Grammar Lesson", "channel": "Woodward English", "published_date": "2023", "duration_sec": 342},
    "present continuous": {"video_id": "oBbJNjjSYBo", "title": "Present Continuous Tense - When to Use & Examples", "channel": "English with Lucy", "published_date": "2023", "duration_sec": 485},
    "past simple": {"video_id": "g-uW_KheiEc", "title": "Past Simple Tense - Regular and Irregular Verbs", "channel": "BBC Learning English", "published_date": "2023", "duration_sec": 360},
    "present perfect": {"video_id": "L9AWrJnhsRI", "title": "Present Perfect & Tenses in Context", "channel": "Woodward English", "published_date": "2023", "duration_sec": 342},
    "future": {"video_id": "HTiTGTJ6Nok", "title": "Future Forms in English - Will, Going to, Present Continuous", "channel": "BBC Learning English", "published_date": "2023", "duration_sec": 390},
    "conditionals": {"video_id": "h-Np7dm-IVA", "title": "All Conditionals in English (Zero, First, Second, Third)", "channel": "English with Lucy", "published_date": "2024", "duration_sec": 720},
    "passive voice": {"video_id": "nRGLDD0BBdc", "title": "The Passive Voice in English Grammar", "channel": "Oxford Online English", "published_date": "2023", "duration_sec": 540},
    "reported speech": {"video_id": "tBtc6hnkb-M", "title": "Reported Speech (Indirect Speech) in English", "channel": "BBC Learning English", "published_date": "2023", "duration_sec": 410},
    "modal verbs": {"video_id": "Nk9nQwoCFig", "title": "Modal Verbs in English - Can, Could, May, Might, Must, Should", "channel": "Woodward English", "published_date": "2023", "duration_sec": 510},
    "relative clauses": {"video_id": "Pr0qUtBaNU0", "title": "Relative Clauses - Who, Which, That, Whose, Whom", "channel": "English with Lucy", "published_date": "2024", "duration_sec": 580},
    "phrasal verbs": {"video_id": "e7tZSwasnR0", "title": "Essential English Phrasal Verbs in Context", "channel": "Oxford Online English", "published_date": "2023", "duration_sec": 640},
    "subjunctive": {"video_id": "V1124f275mE", "title": "The Subjunctive Mood in Advanced English", "channel": "BBC Learning English", "published_date": "2023", "duration_sec": 380},
    "inversion": {"video_id": "h-Np7dm-IVA", "title": "Advanced English Structures for C1/C2", "channel": "English with Lucy", "published_date": "2024", "duration_sec": 720}
}

CEFR_LEVEL_DEFAULT_VIDEOS = {
    "A1": {"video_id": "L9AWrJnhsRI", "title": "A1 Beginner English Grammar & Sentence Structure", "channel": "Woodward English", "published_date": "2023", "duration_sec": 342},
    "A2": {"video_id": "g-uW_KheiEc", "title": "A2 Elementary English Past & Future Structures", "channel": "BBC Learning English", "published_date": "2023", "duration_sec": 360},
    "B1": {"video_id": "oBbJNjjSYBo", "title": "B1 Intermediate English Grammar in Context", "channel": "English with Lucy", "published_date": "2023", "duration_sec": 485},
    "B2": {"video_id": "h-Np7dm-IVA", "title": "B2 Upper-Intermediate Conditionals & Complex Clauses", "channel": "English with Lucy", "published_date": "2024", "duration_sec": 720},
    "C1": {"video_id": "nRGLDD0BBdc", "title": "C1 Advanced Academic English Discourse & Passive Structures", "channel": "Oxford Online English", "published_date": "2023", "duration_sec": 540},
    "C2": {"video_id": "V1124f275mE", "title": "C2 Proficiency Stylistic Nuance & Subjunctive Mood", "channel": "BBC Learning English", "published_date": "2023", "duration_sec": 380}
}


def _validar_video_oembed(video_id: str) -> dict | None:
    """Verifica con el endpoint oficial oEmbed de YouTube que el video sea público e incrustable."""
    vid = str(video_id or "").strip()
    if not re.match(r"^[a-zA-Z0-9_-]{11}$", vid):
        return None
    try:
        oembed_url = f"https://youtube.com{vid}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "video_id": vid,
                    "url": f"https://youtube.com{vid}",
                    "title": str(data.get("title") or "Educational English Video"),
                    "channel": str(data.get("author_name") or "ESL Academic Channel"),
                    "published_date": "2024"
                }
    except Exception:
        pass
    return None


def _buscar_en_motores_navegador(query_busqueda: str) -> list[str]:
    """Busca IDs de videos en motores web simulando Brave, Firefox, Opera y Google/YouTube."""
    q_enc = urllib.parse.quote(f"{query_busqueda} site:youtube.com")
    q_yt = urllib.parse.quote(query_busqueda)

    motores_config = [
        {
            "url": f"https://brave.com{q_enc}",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Brave/128"
        },
        {
            "url": f"https://duckduckgo.com{q_enc}",
            "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"
        },
        {
            "url": f"https://youtube.com{q_yt}",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 OPR/113.0.0.0",
            "cookie": "CONSENT=YES+cb.20230531-07-p0.en+FX+999"
        },
        {
            "url": f"https://google.com{q_enc}&hl=en",
            "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
    ]

    ids_encontrados = []
    for m_cfg in motores_config:
        try:
            headers = {
                "User-Agent": m_cfg["ua"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }
            if m_cfg.get("cookie"):
                headers["Cookie"] = m_cfg["cookie"]
            req = urllib.request.Request(m_cfg["url"], headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                html_body = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r"(?:watch\?v=|youtu\.be/|\"videoId\":\")([a-zA-Z0-9_-]{11})", html_body)
                for vid in matches:
                    if vid not in ids_encontrados:
                        ids_encontrados.append(vid)
                if len(ids_encontrados) >= 4:
                    break
        except Exception:
            continue

    return ids_encontrados
def buscar_video_relacionado_leccion(
    tema_gramatical: str,
    nivel_cefr: str,
    texto_leccion: str = "",
    client_obj=None,
    topic_context: str = "",
    max_videos: int = 12
) -> dict:
    """Catálogo tipo YouTube (12 a 20 videos) por Gramática y Tópico con Multi-Motor + Banco Curado."""
    cefr_code = next(iter(str(nivel_cefr).split()), "B1").upper() if nivel_cefr else "B1"
    if cefr_code not in CEFR_LEVEL_DEFAULT_VIDEOS:
        cefr_code = "B1"

    topico_clean = str(topic_context or "").strip()
    queries_busqueda = [
        f"English grammar {tema_gramatical} {cefr_code} lesson",
    ]
    if topico_clean:
        queries_busqueda.append(f"English listening comprehension {topico_clean} {cefr_code}")

    candidatos_ids = []
    for q_b in queries_busqueda:
        for vid_found in _buscar_en_motores_navegador(q_b):
            if vid_found not in candidatos_ids:
                candidatos_ids.append(vid_found)

    tema_low = str(tema_gramatical or "").lower()
    for key_c, info_c in CURATED_CEFR_VIDEO_DICT.items():
        if key_c in tema_low and info_c["video_id"] not in candidatos_ids:
            candidatos_ids.insert(0, info_c["video_id"])

    def_vid = CEFR_LEVEL_DEFAULT_VIDEOS.get(cefr_code, CEFR_LEVEL_DEFAULT_VIDEOS["B1"])
    if def_vid["video_id"] not in candidatos_ids:
        candidatos_ids.append(def_vid["video_id"])
    for info_c in CURATED_CEFR_VIDEO_DICT.values():
        if info_c["video_id"] not in candidatos_ids:
            candidatos_ids.append(info_c["video_id"])

    curated_lookup = {v["video_id"]: v for v in CURATED_CEFR_VIDEO_DICT.values()}
    curated_lookup[def_vid["video_id"]] = def_vid

    resultados = []
    for idx_v, vid in enumerate(candidatos_ids[:max_videos]):
        meta = curated_lookup.get(vid)
        if not meta and idx_v < 4:
            meta = _validar_video_oembed(vid)
        if meta:
            dur_s = int(meta.get("duration_sec") or 360)
            resultados.append({
                "video_id": vid,
                "url": f"https://youtube.com{vid}",
                "title": str(meta.get("title") or f"{tema_gramatical} ({cefr_code})"),
                "channel": str(meta.get("channel") or "YouTube ESL"),
                "published_date": str(meta.get("published_date") or "2024"),
                "duration_sec": dur_s,
                "duration_min": round(dur_s / 60.0, 2)
            })
        else:
            resultados.append({
                "video_id": vid,
                "url": f"https://youtube.com{vid}",
                "title": f"{tema_gramatical} — {topico_clean or cefr_code} (Video {idx_v + 1})",
                "channel": "YouTube ESL",
                "published_date": "2024",
                "duration_sec": 360,
                "duration_min": 6.0
            })

    principal = dict(resultados[0])
    principal["alternatives"] = resultados[1:]
    return principal

    # 3. Completar catálogo hasta max_videos (12 a 20 opciones) con Banco Curado CEFR + Tópico
    tema_low = str(tema_gramatical or "").lower()
    prioritarios = []
    secundarios = []
    for clave_gram, info_v in CURATED_CEFR_VIDEO_DICT.items():
        if clave_gram in tema_low:
            prioritarios.append(info_v)
        else:
            secundarios.append(info_v)

    def_v = CEFR_LEVEL_DEFAULT_VIDEOS.get(cefr_code, CEFR_LEVEL_DEFAULT_VIDEOS["B1"])
    banco_ordenado = prioritarios + [def_v] + list(CEFR_LEVEL_DEFAULT_VIDEOS.values()) + secundarios

    for item_b in banco_ordenado:
        if len(pool_videos) >= max_videos:
            break
        vid_b = item_b["video_id"]
        if vid_b not in seen_ids:
            seen_ids.add(vid_b)
            dur_b = int(item_b.get("duration_sec") or 360)
            titulo_claro = f"[{etiqueta_tema}] {item_b['title']}" if topico_clean else item_b["title"]
            pool_videos.append({
                "video_id": vid_b,
                "url": f"https://youtube.com{vid_b}",
                "title": titulo_claro,
                "channel": item_b["channel"],
                "published_date": item_b.get("published_date", "2024"),
                "duration_sec": dur_b,
                "duration_min": round(dur_b / 60.0, 2),
                "topic_label": etiqueta_tema,
                "query_used": queries_busqueda[0]
            })

    principal = dict(pool_videos[0])
    principal["alternatives"] = [dict(v) for v in pool_videos[1:max_videos]]
    return principal

def evaluar_resumen_video_apa7(
    resumen_texto: str,
    referencia_apa7: str,
    video_info: dict,
    tema_gramatical: str,
    nivel_cefr: str,
    client_obj=None
) -> dict:
    """WRITING SKILL (20%): Evalúa el resumen escrito (120 a 125 palabras) y su referencia APA 7."""
    palabras = [w for w in re.findall(r"\b[\w'-]+\b", str(resumen_texto or "").strip()) if w]
    conteo_palabras = len(palabras)
    en_rango_palabras = (120 <= conteo_palabras <= 125)

    if not en_rango_palabras:
        return {
            "ok": False,
            "word_count": conteo_palabras,
            "raw_score_100": 0.0,
            "weighted_points_20": 0.0,
            "apa7_valid": False,
            "feedback": (
                f"⚠️ El resumen tiene **{conteo_palabras} palabras**. "
                f"En **WRITING SKILL**, el texto debe contener estrictamente entre **120 y 125 palabras** para ser calificado."
            )
        }

    if len(str(referencia_apa7 or "").strip()) < 15:
        return {
            "ok": False,
            "word_count": conteo_palabras,
            "raw_score_100": 0.0,
            "weighted_points_20": 0.0,
            "apa7_valid": False,
            "feedback": "⚠️ Debes completar el apartado de **Referencia en formato APA 7** del video antes de calificar **WRITING SKILL**."
        }

    gm = client_obj or init_gemini_client()
    prompt_eval_sum = f"""
    Evaluate this student's English video summary and APA 7th edition video reference under CEFR {nivel_cefr} international academic standards.
    Target Grammar: {tema_gramatical}
    Video Title: {video_info.get('title', '')} | Channel: {video_info.get('channel', '')} | URL: {video_info.get('url', '')}
    Word Count Verified: {conteo_palabras} words (strictly within 120-125 words).

    STUDENT SUMMARY (English):
    {resumen_texto.strip()}

    STUDENT APA 7 REFERENCE:
    {referencia_apa7.strip()}

    Evaluate on a 100-point scale (worth 20% of total course grade):
    1. Academic summary coherence, synthesis of video content, vocabulary range, and grammatical accuracy in English (0-70 points).
    2. APA 7th edition video citation accuracy: Author/Channel. (Year, Month Day). Title of video [Video]. YouTube. URL (0-30 points).
    Return ONLY a valid JSON object with exact keys:
    {{"score_100": 92, "apa7_valid": true, "feedback_es": "Retroalimentación pedagógica detallada en español sobre síntesis, gramática inglesa y formato APA 7.", "apa7_corrected": "Ejemplo correcto en formato APA 7 de este video"}}
    """
    try:
        raw_res, _ = generar_con_maxima_potencia(
            gm,
            prompt_eval_sum,
            instruccion_sistema="Output strictly valid JSON only.",
            as_json=True
        )
        cleaned = raw_res.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        j_res = json.loads(cleaned)
        sc_100 = min(100.0, max(0.0, float(j_res.get("score_100") or 0.0)))
        pts_20 = round((sc_100 / 100.0) * 20.0, 2)
        return {
            "ok": True,
            "word_count": conteo_palabras,
            "raw_score_100": sc_100,
            "weighted_points_20": pts_20,
            "apa7_valid": bool(j_res.get("apa7_valid", True)),
            "feedback": str(j_res.get("feedback_es") or "Writing Skill y referencia APA 7 evaluados."),
            "apa7_corrected": str(j_res.get("apa7_corrected") or "")
        }
    except Exception as e:
        return {
            "ok": False,
            "word_count": conteo_palabras,
            "raw_score_100": 0.0,
            "weighted_points_20": 0.0,
            "apa7_valid": False,
            "feedback": f"Error al evaluar Writing Skill con IA: {e}"
        }


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
# PARTE 8B — SECCIÓN 1 DE 4: CACHÉ DE AUDIO MP3 Y TRADUCCIÓN REAL EN ESPAÑOL
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


def _translate_batch_to_spanish(words_list: list[str], api_key_override: str = "") -> dict:
    """Traduce al español real todas las palabras únicas usando Gemini Flash + GoogleTranslator."""
    result_map = {}
    if not words_list:
        return result_map

    gemini_key = str(api_key_override or "").strip()
    if not gemini_key:
        for k_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "API_KEY"):
            if k_name in st.secrets and str(st.secrets[k_name]).strip():
                gemini_key = str(st.secrets[k_name]).strip()
                break

    if gemini_key:
        try:
            client_g = genai.Client(api_key=gemini_key)
            for i in range(0, len(words_list), 45):
                chunk_w = words_list[i:i + 45]
                prompt_tr = (
                    "Translate EVERY English word in this list into natural Spanish for a Mexican/Latin American student. "
                    "Return ONLY a valid JSON object mapping each lowercase English word to an object with: "
                    '{"es": "traducción al español", "pos": "categoría gramatical en español", '
                    '"ipa": "/transcripción IPA/", "alt": "2 sinónimos en español", "def": "definición breve en español"}.\n'
                    f"Words: {json.dumps(chunk_w)}"
                )
                resp = client_g.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_tr,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
                )
                txt = str(resp.text or "").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                data_j = json.loads(txt)
                if isinstance(data_j, dict):
                    for k_en, val_obj in data_j.items():
                        kl = str(k_en).strip().lower()
                        if isinstance(val_obj, dict):
                            entry = result_map.setdefault(kl, {})
                            for fk in ("es", "pos", "ipa", "alt", "def"):
                                if val_obj.get(fk):
                                    entry[fk] = str(val_obj[fk]).strip()
                        elif isinstance(val_obj, str) and val_obj.strip():
                            result_map.setdefault(kl, {})["es"] = val_obj.strip()
        except Exception:
            pass

    missing = [w for w in words_list if not result_map.get(w.lower(), {}).get("es")]
    if missing:
        try:
            for i in range(0, len(missing), 20):
                sub = missing[i:i + 20]
                block_en = " ||| ".join(sub)
                block_es = GoogleTranslator(source="en", target="es").translate(block_en)
                if block_es:
                    parts_es = [p.strip() for p in str(block_es).split("|||")]
                    if len(parts_es) == len(sub):
                        for w_en, w_es in zip(sub, parts_es):
                            if w_es:
                                result_map.setdefault(w_en.lower(), {})["es"] = w_es
        except Exception:
            pass

    return result_map
# ==============================================================================
# PARTE 8B — SECCIÓN 2 DE 4: PAQUETE EN CACHÉ Y PREPARACIÓN DE TOKENS HTML
# ==============================================================================
@st.cache_data(ttl=86400, show_spinner=False, max_entries=60)
def _build_full_study_bundle(
    unique_words_tuple: tuple,
    base_dict_json: str,
    api_key_override: str = "",
    cache_v: str = "v60_final_es_audio"
) -> tuple[dict, dict]:
    """Pre-calcula audios Base64 y traducciones reales al español."""
    words_list = [str(w).strip() for w in unique_words_tuple if str(w).strip()]
    base_dict = json.loads(base_dict_json) if base_dict_json else {}
    merged_dict = {str(k).lower(): (dict(v) if isinstance(v, dict) else {}) for k, v in base_dict.items()}
    audio_map = {}

    if not words_list:
        return audio_map, merged_dict

    # 1. Traducir todas las palabras al español real
    tr_dict = _translate_batch_to_spanish(words_list, api_key_override=api_key_override)
    for kl, info_d in tr_dict.items():
        cur = merged_dict.setdefault(kl, {})
        for fk, fv in info_d.items():
            if fv:
                cur[fk] = fv

    # 2. Sintetizar audio MP3 Base64 (Normal y Lento) con concurrencia controlada
    def _gen_audio_pair(w_item: str):
        mp3_n = _synthesize_word_mp3(w_item, slow_mode=False)
        mp3_s = _synthesize_word_mp3(w_item, slow_mode=True)
        b_n = base64.b64encode(mp3_n).decode("ascii") if mp3_n else ""
        b_s = base64.b64encode(mp3_s).decode("ascii") if mp3_s else b_n
        return w_item.lower(), {"n": b_n, "s": b_s}

    with ThreadPoolExecutor(max_workers=4) as pool:
        for k_w, pair in pool.map(_gen_audio_pair, words_list):
            if pair["n"]:
                audio_map[k_w] = pair

    return audio_map, merged_dict


def render_interactive_study_viewer(study_payload: dict):
    """
    - Móvil / Touch: 1 toque = Voz US | 2 toques = Selecciona la palabra para diccionario nativo del teléfono (sin abrir tarjeta azul).
    - Mac / PC: Hover = Voz US | Doble clic = Tarjeta Bilingüe en la parte inferior con traducción real en español.
    """
    if not study_payload or not study_payload.get("sentences"):
        st.warning("No se pudo estructurar el modo estudio para este texto.")
        return

    sentences = study_payload.get("sentences", [])
    dictionary = study_payload.get("dictionary", {})

    unique_words = []
    seen_w = set()
    for sent in sentences:
        for tok in sent.get("tokens", []):
            wc = re.sub(r"^[^a-zA-Z0-9'-]+|[^a-zA-Z0-9'-]+$", "", str(tok.get("w", "")).strip())
            if wc and wc.lower() not in seen_w:
                seen_w.add(wc.lower())
                unique_words.append(wc)

    active_k_override = str(st.session_state.get("custom_api_key", "")).strip()
    audio_map, merged_dict = _build_full_study_bundle(
        tuple(unique_words),
        json.dumps(dictionary, ensure_ascii=False),
        api_key_override=active_k_override,
        cache_v="v60_final_es_audio"
    )

    pos_class = {"verb": "verb", "noun": "noun", "adjective": "adjective", "conjunction": "conjunction"}
    blocks_html = []
    for sent in sentences:
        tokens = sent.get("tokens", [])
        full_s_attr = html_lib.escape(str(sent.get("full_sentence", "")).strip(), quote=True)
        spans = []
        for tok in tokens:
            w_raw = str(tok.get("w", ""))
            w_esc = html_lib.escape(w_raw)
            p_raw = str(tok.get("pos", "other")).lower()
            p_cls = pos_class.get(p_raw, "other")
            w_clean = re.sub(r"^[^a-zA-Z0-9'-]+|[^a-zA-Z0-9'-]+$", "", w_raw).lower()
            if w_clean:
                w_attr = html_lib.escape(w_clean, quote=True)
                spans.append(
                    f'<span class="wt {p_cls}" data-k="{w_attr}" data-p="{p_cls}" data-s="{full_s_attr}">{w_esc}</span>'
                )
            else:
                spans.append(f"<span>{w_esc}</span>")
        box_cls = "tbox" if sent.get("is_title") else "sbox"
        blocks_html.append(f'<div class="{box_cls}">{" ".join(spans)}</div>')

    lesson_html = "".join(blocks_html)
    audio_json = json.dumps(audio_map).replace("</", "<\\/")
    dict_json = json.dumps(merged_dict, ensure_ascii=False).replace("</", "<\\/")
    viewer_html = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:10px;background:#f8fafc;color:#1e293b}
    .tb{display:flex;flex-wrap:wrap;gap:6px;justify-content:space-between;align-items:center;
        background:#fff;padding:8px 12px;border-radius:10px;border:1px solid #cbd5e1;
        margin-bottom:8px;font-size:12px;font-weight:700;position:sticky;top:0;z-index:100}
    .bg{padding:2px 7px;border-radius:5px}
    .verb{background:#fee2e2;color:#991b1b;border-bottom:2px solid #ef4444}
    .noun{background:#dbeafe;color:#1e40af;border-bottom:2px solid #3b82f6}
    .adjective{background:#dcfce7;color:#166534;border-bottom:2px solid #22c55e}
    .conjunction{background:#fef3c7;color:#92400e;border-bottom:2px solid #f59e0b}
    .other{background:#f1f5f9;color:#334155}
    .tbox{background:#1a2a44;color:#fff;padding:12px 16px;border-radius:10px;margin-bottom:10px;font-size:17px;font-weight:700}
    .tbox .wt{color:#1e293b;font-size:15px}
    .sbox{background:#fff;border-left:4px solid #1a2a44;padding:10px 14px;margin-bottom:10px;
          border-radius:8px;line-height:2.05;font-size:16px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
    .wt{display:inline-block;padding:1px 6px;margin:2px;border-radius:5px;cursor:pointer;transition:transform .1s}
    @media (pointer: fine) { .wt { user-select: none; -webkit-user-select: none; } }
    @media (pointer: coarse) { .wt { user-select: text; -webkit-user-select: text; } }
    .wt:hover,.act{outline:2px solid #1a73e8;background:#e8f0fe !important;color:#174ea6 !important;transform:translateY(-1px)}
    #drawer{position:sticky;bottom:0;z-index:999;background:#fff;border:2px solid #1a73e8;
            border-radius:14px;box-shadow:0 -8px 26px rgba(26,115,232,.30);padding:10px 14px 14px 14px;
            margin-top:10px;display:none}
    .dhead{display:flex;justify-content:space-between;align-items:center;background:#1a73e8;color:#fff;
           margin:-10px -14px 10px -14px;padding:8px 14px;border-radius:11px 11px 0 0;font-size:12px;font-weight:800}
    .dbtn{border:none;border-radius:6px;padding:4px 9px;font-size:12px;font-weight:700;cursor:pointer;margin-left:4px;background:rgba(255,255,255,.22);color:#fff}
    .dgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    </style></head><body>
    <div class="tb">
      <div><span class="bg verb">Verbos</span> <span class="bg noun">Sustantivos</span>
           <span class="bg adjective">Adjetivos</span> <span class="bg conjunction">Conjunciones</span>
           <span class="bg other">Otros</span></div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="color:#475569;font-size:11px;">📱 1 toque: 🔊 | 2 toques: 📖  •  💻 Hover: 🔊 | 2 clics: 📖</span>
        <button type="button" id="spdBtn" style="border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:4px 8px;font-weight:700;cursor:pointer;">1.0x</button>
      </div>
    </div>

    <div id="lc">__LESSON_HTML__</div>

    <div id="drawer">
      <div class="dhead">
        <span>🌐 DICCIONARIO BILINGÜE — 🇺🇸 INGLÉS (US) ➔ 🇪🇸 ESPAÑOL</span>
        <div>
          <button type="button" class="dbtn" id="btnN">🔊 Normal</button>
          <button type="button" class="dbtn" id="btnS">🐢 Lento</button>
          <button type="button" class="dbtn" id="btnC">✖ Cerrar</button>
        </div>
      </div>
      <div class="dgrid">
        <div style="background:#f8fafc;padding:9px;border-radius:9px;border:1px solid #e2e8f0;">
          <div style="font-size:10px;color:#64748b;font-weight:700;">ENGLISH (US)</div>
          <div id="dEn" style="font-size:20px;font-weight:800;color:#0f172a;"></div>
          <div id="dIpa" style="font-size:12px;color:#475569;margin-top:2px;"></div>
          <div id="dPos" style="font-size:12px;color:#1a73e8;font-weight:700;margin-top:3px;"></div>
        </div>
        <div style="background:#eff6ff;padding:9px;border-radius:9px;border:1px solid #bfdbfe;">
          <div style="font-size:10px;color:#1e40af;font-weight:700;">ESPAÑOL (TRADUCCIÓN)</div>
          <div id="dEs" style="font-size:20px;font-weight:800;color:#1a73e8;"></div>
          <div id="dAlt" style="font-size:12px;color:#334155;margin-top:3px;"></div>
        </div>
      </div>
      <div id="dDef" style="margin-top:8px;font-size:12px;color:#334155;background:#f8fafc;padding:7px 10px;border-radius:8px;"></div>
      <div id="dLnk" style="margin-top:8px;font-size:12px;font-weight:700;display:flex;gap:14px;flex-wrap:wrap;"></div>
    </div>
    <script>
    const AMAP = __AUDIO_JSON__;
    const DMAP = __DICT_JSON__;
    const POS_L = {verb:"Verbo",noun:"Sustantivo",adjective:"Adjetivo",conjunction:"Conjunción",other:"Vocabulario"};
    const player = new Audio();
    let slowMode = false, curKey = "", lastHover = "", lastTapK = "", lastTapT = 0;

    function speakFallbackUS(wordText, isSlow) {
      try {
        if (!('speechSynthesis' in window) || !wordText) return;
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(String(wordText));
        u.lang = 'en-US';
        u.rate = isSlow ? 0.68 : 0.98;
        window.speechSynthesis.speak(u);
      } catch (e) {}
    }

    function playKey(k, forceSlow, rawWord) {
      const isSlow = Boolean(forceSlow || slowMode);
      const item = AMAP[k];
      const b64 = item ? (isSlow ? item.s : item.n) : "";
      if (b64) {
        player.pause();
        player.src = "data:audio/mp3;base64," + b64;
        player.play().catch(() => speakFallbackUS(rawWord || k, isSlow));
      } else {
        speakFallbackUS(rawWord || k, isSlow);
      }
    }

    function selectWordNode(el) {
      try {
        const sel = window.getSelection();
        if (!sel) return;
        sel.removeAllRanges();
        const range = document.createRange();
        range.selectNodeContents(el);
        sel.addRange(range);
      } catch (e) {}
    }

    function openDrawer(el, isTouchDevice) {
      document.querySelectorAll('.act').forEach(x=>x.classList.remove('act'));
      el.classList.add('act');
      const k = el.getAttribute('data-k') || '';
      const p = el.getAttribute('data-p') || 'other';
      const origTxt = el.innerText.trim();
      curKey = k;

      if (isTouchDevice) {
        document.getElementById('drawer').style.display = 'none';
        selectWordNode(el);
        playKey(k, false, origTxt);
        return;
      }

      const info = DMAP[k] || {};
      const q = encodeURIComponent(k || origTxt);
      const gtUrl = 'https://google.com' + q + '&op=translate';
      const wrUrl = 'https://wordreference.com' + q;

      document.getElementById('dEn').innerText = origTxt;
      document.getElementById('dEs').innerText = info.es || origTxt;
      document.getElementById('dIpa').innerText = info.ipa ? ('IPA: ' + info.ipa) : '🇺🇸 US Pronunciation';
      document.getElementById('dPos').innerText = info.pos || POS_L[p] || 'Vocabulario';
      document.getElementById('dAlt').innerText = info.alt ? ('Sinónimos: ' + info.alt) : '';
      document.getElementById('dDef').innerText = info.def ? ('📖 ' + info.def) : '';
      document.getElementById('dLnk').innerHTML =
        '<a href="' + gtUrl + '" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();" style="color:#0f766e;text-decoration:underline;cursor:pointer;">🌐 Abrir en Google Translate ↗</a>' +
        '<a href="' + wrUrl + '" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();" style="color:#1a73e8;text-decoration:underline;cursor:pointer;">📖 Abrir en WordReference ↗</a>';

      document.getElementById('drawer').style.display = 'block';
      playKey(k, false, origTxt);
    }

    function closeDrawer() {
      document.getElementById('drawer').style.display = 'none';
      document.querySelectorAll('.act').forEach(x=>x.classList.remove('act'));
      try { const sel = window.getSelection(); if (sel) sel.removeAllRanges(); } catch (e) {}
    }

    document.getElementById('spdBtn').onclick = () => {
      slowMode = !slowMode;
      document.getElementById('spdBtn').innerText = slowMode ? '0.75x' : '1.0x';
    };
    document.getElementById('btnN').onclick = () => playKey(curKey, false, curKey);
    document.getElementById('btnS').onclick = () => playKey(curKey, true, curKey);
    document.getElementById('btnC').onclick = closeDrawer;

    document.getElementById('lc').addEventListener('pointerover', (e) => {
      if (e.pointerType !== 'mouse') return;
      const w = e.target.closest('.wt');
      if (!w) return;
      const k = w.getAttribute('data-k') || '';
      const txt = w.innerText.trim();
      if (k && lastHover !== k) { lastHover = k; playKey(k, false, txt); }
    });
    document.getElementById('lc').addEventListener('pointerout', (e) => {
      if (e.pointerType === 'mouse' && e.target.closest('.wt')) lastHover = '';
    });
    document.getElementById('lc').addEventListener('click', (e) => {
      const w = e.target.closest('.wt');
      if (!w) { closeDrawer(); return; }
      const k = w.getAttribute('data-k') || '';
      const txt = w.innerText.trim();
      const isTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
      const now = Date.now();
      const isDbl = (lastTapK === k && (now - lastTapT) < 440);
      lastTapK = k; lastTapT = now;
      playKey(k, false, txt);
      if (isDbl) openDrawer(w, isTouch);
    });
    document.getElementById('lc').addEventListener('dblclick', (e) => {
      const w = e.target.closest('.wt');
      const isTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
      if (w && !isTouch) openDrawer(w, false);
    });
    </script></body></html>"""

    final_html = (
        viewer_html
        .replace("__LESSON_HTML__", lesson_html)
        .replace("__AUDIO_JSON__", audio_json)
        .replace("__DICT_JSON__", dict_json)
    )
    components.html(final_html, height=620, scrolling=True)


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
# PARTE 10A — MITAD 1: ESQUEMA V2, VACACIONES Y MENSAJES WHATSAPP
# ==============================================================================
@st.cache_resource(show_spinner=False)
def ensure_financial_v2_schema() -> bool:
    """Amplía users_padron y tuition_payments, y crea institute_holidays sin afectar datos."""
    try:
        with pg_session() as cur:
            cur.execute("""
                ALTER TABLE users_padron
                ADD COLUMN IF NOT EXISTS fecha_inscripcion DATE,
                ADD COLUMN IF NOT EXISTS telefono_whatsapp TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS recargo_tardio NUMERIC(10,2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS boletin_habilitado BOOLEAN DEFAULT TRUE;
            """)
            cur.execute("""
                UPDATE users_padron
                SET fecha_inscripcion = COALESCE(fecha_inscripcion, fecha_inicio_curso, CURRENT_DATE)
                WHERE fecha_inscripcion IS NULL;
            """)
            cur.execute("""
                ALTER TABLE tuition_payments
                ADD COLUMN IF NOT EXISTS folio_pago TEXT,
                ADD COLUMN IF NOT EXISTS nivel_cefr TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS metodo_pago TEXT DEFAULT 'Transferencia Bancaria',
                ADD COLUMN IF NOT EXISTS referencia_comprobante TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS comprobante_b64 TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS comprobante_mime TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS validado_por TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS fecha_validacion TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS notas_admin TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS matricula_alumno TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS clave_rastreo_unica TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS ai_score INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS ai_audit_json TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS gracia_expira_en TIMESTAMPTZ;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS institute_holidays (
                    id SERIAL PRIMARY KEY,
                    nombre_periodo TEXT NOT NULL,
                    fecha_inicio DATE NOT NULL,
                    fecha_fin DATE NOT NULL,
                    activo BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        return True
    except Exception:
        return False


ensure_financial_v2_schema()


@st.cache_data(ttl=120, show_spinner=False)
def load_institute_holidays_pg() -> list[dict]:
    """Obtiene los períodos vacacionales activos ordenados cronológicamente por fecha."""
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT id, nombre_periodo, fecha_inicio, fecha_fin, activo
                FROM institute_holidays
                WHERE activo = TRUE
                ORDER BY fecha_inicio ASC, fecha_fin ASC, id ASC;
            """)
            rows = [dict(r) for r in cur.fetchall()]
            return sorted(rows, key=lambda x: (x["fecha_inicio"], x["fecha_fin"], x["id"]))
    except Exception:
        return []


def _format_wa_phone(raw_phone: str, default_cc: str = "52") -> str:
    digits = re.sub(r"\D+", "", str(raw_phone or ""))
    if not digits:
        return ""
    if len(digits) == 10:
        return default_cc + digits
    return digits


def build_whatsapp_recordatorio_estudiante(est_info: dict, nombre_alumno: str, telefono_alumno: str) -> tuple[str, str]:
    """Genera el texto y la URL de WhatsApp para recordar al estudiante su 4ta semana de pago o recargo."""
    ciclo_n = est_info.get("ciclo_a_cobrar", 1)
    sem4_ini = est_info.get("sem4_pago_inicio") or est_info.get("ventana_pago_inicio")
    sem4_fin = est_info.get("sem4_pago_fin") or est_info.get("ventana_pago_fin")
    f_recargo = est_info.get("fecha_recargo")
    monto = float(est_info.get("monto_a_pagar") or 0.0)
    es_moratorio = int(est_info.get("dias_retraso") or 0) > 0
    en_vacaciones = bool(est_info.get("en_vacaciones"))

    nota_vac = (
        " Te recordamos que, aun durante el receso vacacional de clases, tu plataforma inteligente con IA "
        "permanece 100% activa las 24 horas para que sigas generando lecciones y avanzando en tu aprendizaje."
        if en_vacaciones
        else " Tu membresía mantiene activa 24/7 nuestra plataforma inteligente con IA para seguir generando lecciones y avanzando en tu aprendizaje."
    )

    if es_moratorio:
        msg = (
            f"Hola {nombre_alumno}, te saludamos de Career English Institute 🎓. "
            f"Te informamos que el Bloque {ciclo_n} de 9 ha entrado en Semana 5 con recargo activo "
            f"(monto actualizado: ${monto:,.2f} MXN).{nota_vac} "
            f"Recuerda que mantener tu pago al día te permite descargar tu Boletín Oficial de Calificaciones "
            f"para mantenerte informado de tu avance académico. Puedes subir tu comprobante directamente en la plataforma."
        )
    else:
        msg = (
            f"Hola {nombre_alumno}, te saludamos de Career English Institute 🎓. "
            f"Has llegado a tu 4ta semana calendario (del {sem4_ini} al {sem4_fin}), período habilitado "
            f"para registrar sin recargo el pago de tu Bloque {ciclo_n} de 9 por ${monto:,.2f} MXN "
            f"(el recargo se activa a partir del {f_recargo}).{nota_vac} "
            f"Además, tu pago puntual te permite descargar tu Boletín Oficial de Calificaciones para mantenerte informado de tu avance."
        )

    phone_clean = _format_wa_phone(telefono_alumno)
    wa_url = (
        f"https://wa.me{phone_clean}?text={urllib.parse.quote(msg)}"
        if phone_clean
        else f"https://wa.me?text={urllib.parse.quote(msg)}"
    )
    return msg, wa_url


def build_whatsapp_aviso_pago_owner(
    nombre_alumno: str,
    usuario_alumno: str,
    nivel_cefr: str,
    folio_pago: str,
    ciclo_num: int,
    monto_pagado: float,
    referencia: str,
    telefono_owner: str = ""
) -> tuple[str, str]:
    """Genera la nota informativa vía WhatsApp para el Owner o Administrador autorizado."""
    msg = (
        f"Hola, soy {nombre_alumno} (Usuario: {usuario_alumno} | Nivel {nivel_cefr}). "
        f"Acabo de informar en la plataforma mi comprobante de pago con Folio {folio_pago} "
        f"correspondiente al Bloque {ciclo_num} de 9 por ${monto_pagado:,.2f} MXN "
        f"(Referencia: {referencia or 'Adjunta en comprobante'}). "
        f"Te invito amablemente a verificar el comprobante contra el registro en la cuenta bancaria "
        f"para confirmar mi pago y mantener activo mi Boletín de Calificaciones. ¡Muchas gracias!"
    )
    phone_clean = _format_wa_phone(telefono_owner)
    wa_url = (
        f"https://wa.me{phone_clean}?text={urllib.parse.quote(msg)}"
        if phone_clean
        else f"https://wa.me?text={urllib.parse.quote(msg)}"
    )
    return msg, wa_url
# ==============================================================================
# PARTE 10A — MITAD 2A: EVALUACIÓN FINANCIERA DE 9 BLOQUES Y MATRÍCULA (PARTE 1)
# ==============================================================================
def evaluar_estado_financiero_alumno(student_user: str) -> dict:
    hoy = datetime.now(ZoneInfo("America/Hermosillo")).date()
    reglas_activas = get_billing_global_settings_pg()
    holidays = load_institute_holidays_pg()

    info = {
        "matricula": "",
        "student_id_num": 0,
        "fecha_inscripcion": hoy,
        "fecha_inicio": hoy,
        "telefono_whatsapp": "",
        "nivel_cefr": "A1",
        "mensualidad_base": 1500.00,
        "aplicar_iva": False,
        "subtotal_ajustado": 1500.00,
        "iva_monto": 0.00,
        "reglas_incentivo_activas": reglas_activas,
        "afiliado_usuario": "",
        "porcentaje_comision": 0.0,
        "ciclo_actual": 1,
        "ciclo_a_cobrar": 1,
        "bloque_en_nivel": 1,
        "semana_ciclo": 1,
        "ventana_pago_inicio": hoy,
        "ventana_pago_fin": hoy + timedelta(days=27),
        "sem4_pago_inicio": hoy + timedelta(days=21),
        "sem4_pago_fin": hoy + timedelta(days=27),
        "fecha_recargo": hoy + timedelta(days=28),
        "en_vacaciones": False,
        "nombre_vacaciones": "",
        "bloques_9": [],
        "pagos_historial": [],
        "tiene_pago_en_revision": False,
        "ajuste_label": "Tarifa Base",
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
                SELECT id, COALESCE(NULLIF(TRIM(matricula), ''), 'CEI-2026-' || LPAD(id::text, 4, '0')) AS matricula,
                       rol, nivel_cefr, fecha_inscripcion, fecha_inicio_curso, telefono_whatsapp,
                       mensualidad_base, recargo_tardio, aplicar_iva, afiliado_usuario, porcentaje_comision
                FROM users_padron WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) LIMIT 1;
            """, (student_user,))
            u = cur.fetchone()
            if not u:
                return info

            mat_alumno = str(u.get("matricula") or "").strip()
            id_num_alumno = int(u.get("id") or 0)
            info["matricula"] = mat_alumno
            info["student_id_num"] = id_num_alumno

            if str(u.get("rol", "")).lower() not in ["estudiante", "student", "alumno"]:
                return info

            f_ins = u.get("fecha_inscripcion") or u.get("fecha_inicio_curso") or hoy
            f_ini = u.get("fecha_inicio_curso") or f_ins
            base = float(u.get("mensualidad_base") or 1500.0)
            recargo_fijo = float(u.get("recargo_tardio") or 0.0)
            con_iva = bool(u.get("aplicar_iva") or False)
            nivel_al = str(u.get("nivel_cefr") or "A1").strip()
            tel_wa = str(u.get("telefono_whatsapp") or "").strip()

            dias_transcurridos = max(0, (hoy - f_ini).days)
            ciclo_vigente = (dias_transcurridos // 28) + 1
            dia_en_ciclo = (dias_transcurridos % 28) + 1
            semana_en_ciclo = ((dia_en_ciclo - 1) // 7) + 1
            bloque_nivel_actual = ((ciclo_vigente - 1) % 9) + 1

            ahora_utc = datetime.now(ZoneInfo("UTC"))
            cur.execute("""
                SELECT ciclo_numero, estatus, folio_pago, monto_final, metodo_pago,
                       referencia_comprobante, fecha_pago, validado_por, ai_score, gracia_expira_en
                FROM tuition_payments
                WHERE LOWER(TRIM(student_user)) = LOWER(TRIM(%s))
                ORDER BY ciclo_numero ASC;
            """, (student_user,))
            rows_pay = [dict(r) for r in cur.fetchall()]
            pagos_by_ciclo = {int(r["ciclo_numero"]): r for r in rows_pay if r.get("ciclo_numero") is not None}

            ciclos_pagados = set()
            ciclos_revision = set()
            for c_num, r_pay in pagos_by_ciclo.items():
                st_p = str(r_pay.get("estatus", ""))
                g_exp = r_pay.get("gracia_expira_en")
                gracia_vigente = bool(st_p == "Gracia_72h" and g_exp and g_exp > ahora_utc)
                if st_p in ("Pagado", "Aprobado_IA") or gracia_vigente:
                    ciclos_pagados.add(c_num)
                elif st_p in ("Pendiente_Revision", "Gracia_72h"):
                    ciclos_revision.add(c_num)

            ciclos_vencidos = [c for c in range(1, ciclo_vigente) if c not in ciclos_pagados]

            if ciclos_vencidos:
                ciclo_objetivo = next(iter(ciclos_vencidos))
                es_moratorio = True
                esta_pagado = False
            elif ciclo_vigente in ciclos_pagados and semana_en_ciclo == 4 and (ciclo_vigente + 1) not in ciclos_pagados:
                ciclo_objetivo = ciclo_vigente + 1
                es_moratorio = False
                esta_pagado = False
            else:
                ciclo_objetivo = ciclo_vigente
                es_moratorio = False
                esta_pagado = ciclo_vigente in ciclos_pagados

            inicio_ciclo_obj = f_ini + timedelta(days=(ciclo_objetivo - 1) * 28)
            if ciclo_objetivo > 1 and ciclo_objetivo == ciclo_vigente + 1:
                sem4_ini_obj = f_ini + timedelta(days=(ciclo_vigente - 1) * 28 + 21)
                sem4_fin_obj = f_ini + timedelta(days=(ciclo_vigente - 1) * 28 + 27)
                fecha_recargo_obj = f_ini + timedelta(days=ciclo_vigente * 28)
            else:
                sem4_ini_obj = inicio_ciclo_obj + timedelta(days=21)
                sem4_fin_obj = inicio_ciclo_obj + timedelta(days=27)
                fecha_recargo_obj = inicio_ciclo_obj + timedelta(days=28)

            dias_retraso_calc = max(0, (hoy - (inicio_ciclo_obj + timedelta(days=27))).days) if es_moratorio else 0

            en_vac = False
            nom_vac = ""
            for h in holidays:
                if h["fecha_inicio"] <= hoy <= h["fecha_fin"]:
                    en_vac = True
                    nom_vac = str(h["nombre_periodo"])
                    break
# ==============================================================================
# PARTE 10A — MITAD 2B: PROYECCIÓN DE 9 BLOQUES Y MATRÍCULA EN INFO.UPDATE
# ==============================================================================
            base_bloque_nivel = ((ciclo_vigente - 1) // 9) * 9
            bloques_9_list = []
            for b_idx in range(1, 10):
                c_abs = base_bloque_nivel + b_idx
                b_ini = f_ini + timedelta(days=(c_abs - 1) * 28)
                b_fin = b_ini + timedelta(days=27)
                b_sem4_ini = b_ini + timedelta(days=21)
                b_sem4_fin = b_fin
                b_recargo = b_ini + timedelta(days=28)

                vac_names = [
                    str(h["nombre_periodo"]) for h in holidays
                    if not (b_fin < h["fecha_inicio"] or b_ini > h["fecha_fin"])
                ]

                if c_abs in ciclos_pagados:
                    b_status = "✅ Pagado / Verificado (Boletín Activo)"
                elif c_abs in ciclos_revision:
                    b_status = "⏳ En Revisión Bancaria"
                elif c_abs < ciclo_vigente:
                    b_status = "🔴 Vencido — Recargo Activo (Sem. 5+)"
                elif c_abs == ciclo_vigente and semana_en_ciclo == 4:
                    b_status = "🟡 4ta Semana — Ventana de Pago Abierta"
                elif c_abs == ciclo_vigente:
                    b_status = f"🟢 Cursando (Semana {semana_en_ciclo}/4)"
                else:
                    b_status = "⚪ Programado"

                bloques_9_list.append({
                    "bloque_num": b_idx,
                    "ciclo_global": c_abs,
                    "inicio_bloque": b_ini,
                    "fin_bloque": b_fin,
                    "sem4_inicio": b_sem4_ini,
                    "sem4_fin": b_sem4_fin,
                    "fecha_recargo": b_recargo,
                    "vacaciones": ", ".join(vac_names) if vac_names else "Clases Regulares",
                    "estatus": b_status
                })

            if not reglas_activas and not es_moratorio:
                ajuste_lbl = "Mensualidad Estándar"
                ajuste_mto = 0.0
            elif es_moratorio:
                rec_calc = recargo_fijo if recargo_fijo > 0 else round(base * 0.05, 2)
                ajuste_lbl = f"Recargo Moratorio Bloque {ciclo_objetivo} (Semana 5+)"
                ajuste_mto = round(rec_calc, 2)
            elif reglas_activas:
                ajuste_lbl = f"Incentivo Pago Puntual Sem. {semana_en_ciclo}/4 (-7%)"
                ajuste_mto = round(-base * 0.07, 2)
            else:
                ajuste_lbl = "Mensualidad Sin Recargo (4ta Semana)"
                ajuste_mto = 0.0

            subtotal_mes = round(base + ajuste_mto, 2)
            iva_mto = round(subtotal_mes * 0.16, 2) if con_iva else 0.0
            monto_calc = round(subtotal_mes + iva_mto, 2)
            boletin_activo = not es_moratorio

            info.update({
                "matricula": mat_alumno,
                "student_id_num": id_num_alumno,
                "fecha_inscripcion": f_ins,
                "fecha_inicio": f_ini,
                "telefono_whatsapp": tel_wa,
                "nivel_cefr": nivel_al,
                "mensualidad_base": base,
                "aplicar_iva": con_iva,
                "subtotal_ajustado": subtotal_mes,
                "iva_monto": iva_mto,
                "reglas_incentivo_activas": reglas_activas,
                "afiliado_usuario": str(u.get("afiliado_usuario") or ""),
                "porcentaje_comision": float(u.get("porcentaje_comision") or 0.0),
                "ciclo_actual": ciclo_objetivo,
                "ciclo_a_cobrar": ciclo_objetivo,
                "bloque_en_nivel": bloque_nivel_actual,
                "semana_ciclo": semana_en_ciclo,
                "ventana_pago_inicio": inicio_ciclo_obj,
                "ventana_pago_fin": sem4_fin_obj,
                "sem4_pago_inicio": sem4_ini_obj,
                "sem4_pago_fin": sem4_fin_obj,
                "fecha_recargo": fecha_recargo_obj,
                "en_vacaciones": en_vac,
                "nombre_vacaciones": nom_vac,
                "bloques_9": bloques_9_list,
                "pagos_historial": rows_pay,
                "tiene_pago_en_revision": bool(ciclos_revision),
                "ajuste_label": ajuste_lbl,
                "ajuste_monto": ajuste_mto,
                "monto_a_pagar": monto_calc,
                "ciclo_pagado": esta_pagado,
                "descarga_permitida": boletin_activo,
                "dias_retraso": dias_retraso_calc,
                "mensaje_estado": (
                    f"✅ Bloque {bloque_nivel_actual}/9 Pagado (Boletín de Calificaciones Activo)"
                    if esta_pagado
                    else (
                        f"⛔ Semana 5+ sin pago: Bloque {ciclo_objetivo} vencido ({dias_retraso_calc} días — Recargo activo: ${monto_calc:,.2f}). Boletín pausado hasta confirmar pago."
                        if es_moratorio
                        else f"⏳ Bloque {bloque_nivel_actual}/9 — Semana {semana_en_ciclo}/4 ({ajuste_lbl}: ${monto_calc:,.2f})"
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


def actualizar_config_financiera_alumno_pg(
    student_user: str,
    fecha_inicio_val,
    mensualidad_val: float,
    aplicar_iva_val: bool,
    afiliado_user: str,
    pct_comision: float,
    fecha_inscripcion_val=None,
    telefono_whatsapp_val: str = "",
    recargo_tardio_val: float = 0.0
) -> bool:
    try:
        with pg_session() as cur:
            cur.execute("""
                ALTER TABLE users_padron
                ADD COLUMN IF NOT EXISTS fecha_inscripcion DATE,
                ADD COLUMN IF NOT EXISTS fecha_inicio_curso DATE,
                ADD COLUMN IF NOT EXISTS telefono_whatsapp TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS mensualidad_base NUMERIC(10,2) DEFAULT 1500.00,
                ADD COLUMN IF NOT EXISTS recargo_tardio NUMERIC(10,2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS aplicar_iva BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS afiliado_usuario TEXT DEFAULT '',
                ADD COLUMN IF NOT EXISTS afiliador_id INTEGER,
                ADD COLUMN IF NOT EXISTS porcentaje_comision NUMERIC(5,2) DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS boletin_habilitado BOOLEAN DEFAULT TRUE;
            """)

            aff_clean = str(afiliado_user or "").strip()
            aff_id_val = None
            if aff_clean:
                cur.execute("SELECT id FROM users_padron WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) LIMIT 1;", (aff_clean,))
                r_id = cur.fetchone()
                if r_id:
                    aff_id_val = int(r_id["id"]) if isinstance(r_id, dict) else int(r_id[0])

            f_ins_final = fecha_inscripcion_val or fecha_inicio_val
            cur.execute("""
                UPDATE users_padron
                SET fecha_inscripcion = %s,
                    fecha_inicio_curso = %s,
                    telefono_whatsapp = %s,
                    mensualidad_base = %s,
                    recargo_tardio = %s,
                    aplicar_iva = %s,
                    afiliado_usuario = %s,
                    afiliador_id = %s,
                    porcentaje_comision = %s
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s));
            """, (
                f_ins_final,
                fecha_inicio_val,
                str(telefono_whatsapp_val or "").strip(),
                float(mensualidad_val),
                float(recargo_tardio_val or 0.0),
                bool(aplicar_iva_val),
                aff_clean,
                aff_id_val,
                float(pct_comision),
                student_user.strip()
            ))
        load_padron_records.clear()
        return True
    except Exception as e:
        st.error(f"❌ Error al actualizar Supabase (`users_padron`): {e}")
        return False


def fetch_affiliate_dashboard_pg(affiliate_user: str) -> dict:
    res = {"students": [], "commissions": [], "total_ganado": 0.0, "total_pendiente": 0.0, "total_pagado": 0.0}
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT usuario, nivel_cefr AS nivel, fecha_inscripcion, fecha_inicio_curso,
                       mensualidad_base, porcentaje_comision, estatus
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
# PARTE 10B3 — MITAD 1 DE 2: AUDITORÍA FORENSE CON VISIÓN IA Y MATRÍCULA OFICIAL
# ==============================================================================
def _analizar_comprobante_con_vision_ia(
    comprobante_b64: str,
    comprobante_mime: str,
    matricula_esperada: str,
    monto_esperado: float
) -> dict:
    """Audita el comprobante bancario con Gemini Vision cotejando Matrícula, monto y clave de rastreo."""
    resultado = {
        "score": 40,
        "estatus_sugerido": "Gracia_72h",
        "monto_detectado": 0.0,
        "clave_rastreo": "",
        "matricula_detectada": "",
        "fecha_detectada": "",
        "banco_emisor": "",
        "diagnostico": "Pase provisional de 72h activado. Pendiente de cotejo visual por el administrador."
    }
    if not comprobante_b64:
        return resultado

    gemini_key = ""
    for k_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "API_KEY"):
        if k_name in st.secrets and str(st.secrets[k_name]).strip():
            gemini_key = str(st.secrets[k_name]).strip()
            break
    if not gemini_key:
        return resultado

    try:
        client_v = genai.Client(api_key=gemini_key)
        raw_doc = base64.b64decode(comprobante_b64)
        mime_clean = comprobante_mime if comprobante_mime else "image/jpeg"
        prompt_audit = (
            f"Audit this bank transfer/deposit receipt for Career English Institute. "
            f"Expected student Matrícula: '{matricula_esperada}'. Expected amount: {monto_esperado:.2f} MXN. "
            "Extract the fields and return ONLY a valid JSON object with exact keys: "
            '{"monto_detectado": 0.0, "clave_rastreo": "tracking key or reference", '
            '"matricula_detectada": "student matricula or concept text", '
            '"fecha_detectada": "YYYY-MM-DD", "banco_emisor": "bank name", "es_comprobante_valido": true}.'
        )
        resp_v = client_v.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=raw_doc, mime_type=mime_clean),
                prompt_audit
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0)
        )
        txt_v = str(resp_v.text or "").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        j_v = json.loads(txt_v)

        monto_det = float(j_v.get("monto_detectado") or 0.0)
        clave_det = str(j_v.get("clave_rastreo") or "").strip().upper()
        mat_det = str(j_v.get("matricula_detectada") or "").strip().upper()
        fecha_det = str(j_v.get("fecha_detectada") or "").strip()
        banco_det = str(j_v.get("banco_emisor") or "").strip()
        es_valido = bool(j_v.get("es_comprobante_valido", False))

        score = 20 if es_valido else 0
        notas = []

        if abs(monto_det - monto_esperado) <= 2.0 and monto_det > 0:
            score += 40
            notas.append(f"Monto exacto (${monto_det:,.2f})")
        elif monto_det > 0:
            notas.append(f"Monto detectado (${monto_det:,.2f} vs esperado ${monto_esperado:,.2f})")

        mat_norm = re.sub(r"[^A-Z0-9]", "", matricula_esperada.upper())
        mat_det_norm = re.sub(r"[^A-Z0-9]", "", mat_det)
        if mat_norm and mat_norm in mat_det_norm:
            score += 30
            notas.append(f"Matrícula verificada ({matricula_esperada})")
        else:
            notas.append(f"Concepto leído: '{mat_det or 'No visible'}'")

        if len(clave_det) >= 5:
            score += 10
            notas.append(f"Rastreo: {clave_det}")

        duplicado = False
        if len(clave_det) >= 6:
            with pg_session() as cur:
                cur.execute("""
                    SELECT 1 FROM tuition_payments
                    WHERE clave_rastreo_unica = %s AND estatus IN ('Pagado', 'Aprobado_IA')
                    LIMIT 1;
                """, (clave_det,))
                if cur.fetchone():
                    duplicado = True
                    score = 0
                    notas.append("⚠️ ALERTA: Clave de rastreo ya utilizada previamente")

        estatus_fin = "Aprobado_IA" if (score >= 85 and not duplicado) else "Gracia_72h"
        resultado.update({
            "score": score,
            "estatus_sugerido": estatus_fin,
            "monto_detectado": monto_det,
            "clave_rastreo": clave_det,
            "matricula_detectada": mat_det,
            "fecha_detectada": fecha_det,
            "banco_emisor": banco_det,
            "diagnostico": " | ".join(notas) if notas else resultado["diagnostico"]
        })
    except Exception:
        pass
    return resultado
# ==============================================================================
# PARTE 10B3 — MITAD 2 DE 2: REGISTRO CON MATRÍCULA Y BANDEJA PRIORITARIA
# ==============================================================================
def reportar_comprobante_pago_estudiante_pg(
    student_user: str,
    metodo_pago: str,
    referencia: str,
    comprobante_b64: str = "",
    comprobante_mime: str = "",
    ciclo_seleccionado: int | None = None
) -> dict:
    """Audita el comprobante con Visión IA, vincula la Matrícula y desbloquea el Boletín al instante."""
    est = evaluar_estado_financiero_alumno(student_user)
    ciclo_obj = int(ciclo_seleccionado) if ciclo_seleccionado else int(est["ciclo_a_cobrar"])

    # Buscar fechas y monto exacto del bloque seleccionado
    b_match = next((b for b in est.get("bloques_9", []) if int(b["ciclo_global"]) == ciclo_obj), None)
    if b_match and "Pagado" in str(b_match.get("estatus", "")):
        return {"ok": False, "msg": f"El Bloque {ciclo_obj} ya se encuentra pagado."}

    f_venc_obj = b_match["sem4_fin"] if b_match else est["sem4_pago_fin"]
    base_mto = float(est["mensualidad_base"])
    con_iva = bool(est.get("aplicar_iva"))
    hoy_loc = datetime.now(ZoneInfo("America/Hermosillo")).date()
    es_vencido_sel = bool(b_match and hoy_loc >= b_match["fecha_recargo"])

    if es_vencido_sel:
        ajuste_lbl_sel = f"Recargo Moratorio Bloque {ciclo_obj} (Semana 5+)"
        sub_sel = round(base_mto * 1.05, 2)
    elif est.get("reglas_incentivo_activas"):
        ajuste_lbl_sel = f"Incentivo Pago Puntual Bloque {ciclo_obj} (-7%)"
        sub_sel = round(base_mto * 0.93, 2)
    else:
        ajuste_lbl_sel = f"Mensualidad Bloque {ciclo_obj}"
        sub_sel = base_mto

    monto_esperado_sel = round(sub_sel * 1.16, 2) if con_iva else sub_sel
    mat_alumno = str(est.get("matricula") or "").strip()
    folio_gen = f"PAY-{datetime.now(ZoneInfo('America/Hermosillo')).strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

    audit = _analizar_comprobante_con_vision_ia(
        comprobante_b64=comprobante_b64,
        comprobante_mime=comprobante_mime,
        matricula_esperada=mat_alumno,
        monto_esperado=monto_esperado_sel
    )
    estatus_nuevo = audit["estatus_sugerido"]
    expira_gracia = datetime.now(ZoneInfo("UTC")) + timedelta(hours=72)
    clave_unica = audit["clave_rastreo"] or referencia.strip().upper()

    try:
        with pg_session() as cur:
            cur.execute("""
                INSERT INTO tuition_payments (
                    student_user, matricula_alumno, ciclo_numero, fecha_vencimiento,
                    monto_base, ajuste_tipo, monto_final, estatus,
                    folio_pago, nivel_cefr, metodo_pago, referencia_comprobante,
                    clave_rastreo_unica, ai_score, ai_audit_json, gracia_expira_en,
                    comprobante_b64, comprobante_mime, registrado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_user, ciclo_numero) DO UPDATE SET
                    matricula_alumno = EXCLUDED.matricula_alumno,
                    estatus = EXCLUDED.estatus,
                    monto_final = EXCLUDED.monto_final,
                    ajuste_tipo = EXCLUDED.ajuste_tipo,
                    folio_pago = COALESCE(tuition_payments.folio_pago, EXCLUDED.folio_pago),
                    metodo_pago = EXCLUDED.metodo_pago,
                    referencia_comprobante = EXCLUDED.referencia_comprobante,
                    clave_rastreo_unica = EXCLUDED.clave_rastreo_unica,
                    ai_score = EXCLUDED.ai_score,
                    ai_audit_json = EXCLUDED.ai_audit_json,
                    gracia_expira_en = EXCLUDED.gracia_expira_en,
                    comprobante_b64 = CASE WHEN EXCLUDED.comprobante_b64 <> '' THEN EXCLUDED.comprobante_b64 ELSE tuition_payments.comprobante_b64 END,
                    comprobante_mime = CASE WHEN EXCLUDED.comprobante_mime <> '' THEN EXCLUDED.comprobante_mime ELSE tuition_payments.comprobante_mime END,
                    fecha_pago = NOW(),
                    registrado_por = EXCLUDED.registrado_por;
            """, (
                student_user.strip(),
                mat_alumno,
                ciclo_obj,
                f_venc_obj,
                base_mto,
                ajuste_lbl_sel,
                monto_esperado_sel,
                estatus_nuevo,
                folio_gen,
                est.get("nivel_cefr", ""),
                metodo_pago.strip(),
                referencia.strip(),
                clave_unica,
                int(audit["score"]),
                json.dumps(audit, ensure_ascii=False),
                expira_gracia,
                comprobante_b64,
                comprobante_mime,
                student_user.strip()
            ))

            cur.execute("""
                UPDATE users_padron
                SET boletin_habilitado = TRUE
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s));
            """, (student_user.strip(),))

        badge_msg = (
            f"🟢 **Aprobación Express IA ({audit['score']}%)** — Matrícula `{mat_alumno}` verificada para **Bloque {ciclo_obj}**. ¡Tu Boletín ya está desbloqueado!"
            if estatus_nuevo == "Aprobado_IA"
            else f"🟡 **Pase Provisional de 72 horas activado** para Matrícula `{mat_alumno}` (**Bloque {ciclo_obj}**). ¡Ya puedes descargar tu Boletín mientras el administrador concilia el movimiento!"
        )
        return {
            "ok": True,
            "folio_pago": folio_gen,
            "matricula": mat_alumno,
            "ciclo_num": ciclo_obj,
            "monto": monto_esperado_sel,
            "nivel_cefr": est.get("nivel_cefr", ""),
            "estatus_ia": estatus_nuevo,
            "msg": f"✅ Comprobante `{folio_gen}` registrado.\n\n{badge_msg}\n\n🔍 *Auditoría:* {audit['diagnostico']}"
        }
    except Exception as e:
        return {"ok": False, "msg": f"Error al registrar comprobante: {e}"}


def listar_comprobantes_pendientes_pg() -> list[dict]:
    """Lista comprobantes en Gracia_72h, Pendiente_Revision o Aprobado_IA con Matrícula Oficial."""
    try:
        with pg_session(dict_rows=True) as cur:
            cur.execute("""
                SELECT tp.id, tp.folio_pago, tp.student_user,
                       COALESCE(NULLIF(tp.matricula_alumno, ''), up.matricula, 'SIN-MAT') AS matricula_alumno,
                       tp.nivel_cefr, tp.ciclo_numero, tp.monto_final, tp.metodo_pago,
                       tp.referencia_comprobante, tp.ai_score, tp.ai_audit_json,
                       tp.comprobante_b64, tp.comprobante_mime, tp.estatus,
                       TO_CHAR(tp.fecha_pago AT TIME ZONE 'America/Hermosillo', 'YYYY-MM-DD HH24:MI') AS fecha_reporte,
                       COALESCE(up.nombre_completo, tp.student_user) AS nombre_completo,
                       COALESCE(up.telefono_whatsapp, '') AS telefono_whatsapp
                FROM tuition_payments tp
                LEFT JOIN users_padron up ON LOWER(TRIM(up.usuario)) = LOWER(TRIM(tp.student_user))
                WHERE tp.estatus IN ('Pendiente_Revision', 'Gracia_72h', 'Aprobado_IA')
                ORDER BY
                    CASE tp.estatus WHEN 'Gracia_72h' THEN 1 WHEN 'Pendiente_Revision' THEN 2 ELSE 3 END,
                    tp.fecha_pago ASC;
            """)
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []

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
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🎓 CEI ENGLISH LEARNING PLATFORM</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #475569; font-size: 14px;'>Career English Institute • Global Pedagogical &amp; CEFR Assessment Suite</p>", unsafe_allow_html=True)
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


# --- AUTO-RESTAURACIÓN DE SESIÓN RECORDADA (HMAC TOKEN EN URL / PWA) ---
if not st.session_state.get("authenticated", False) and not st.session_state.get("just_logged_out", False):
    tok_url_saved = str(st.query_params.get("cei_auth", "")).strip()
    if tok_url_saved and "." in tok_url_saved:
        try:
            b64_payload, sig_hex = tok_url_saved.rsplit(".", 1)
            raw_bytes = base64.urlsafe_b64decode(b64_payload.encode("ascii"))
            secret_salt = str(st.secrets.get("OWNER_MASTER_KEY", "CEI_HMAC_2026")).encode("utf-8")
            expected_sig = hmac.new(secret_salt, raw_bytes, hashlib.sha256).hexdigest()[:24]
            if hmac.compare_digest(sig_hex, expected_sig):
                u_saved, c_saved = raw_bytes.decode("utf-8").split("::", 1)
                registros_auto = load_padron_records() or []
                u_match_auto = next(
                    (r for r in registros_auto
                     if str(r.get("Usuario", "")).strip().lower() == u_saved.strip().lower()
                     and hmac.compare_digest(str(r.get("Clave", "")).strip(), c_saved.strip())),
                    None
                )
                if u_match_auto is None:
                    m_u = str(st.secrets.get("OWNER_MASTER_USER", "")).strip()
                    m_k = str(st.secrets.get("OWNER_MASTER_KEY", "")).strip()
                    if m_u and m_k and u_saved.strip().lower() == m_u.lower() and hmac.compare_digest(m_k, c_saved.strip()):
                        u_match_auto = {
                            "Usuario": m_u, "Clave": m_k, "Rol": "Propietario",
                            "Permisos": "Total", "Nivel": "C2",
                            "Grado_Academico": "Doctorado / Posgrado", "Estatus": "Activo"
                        }
                if u_match_auto and str(u_match_auto.get("Estatus", "Activo")).strip().lower() == "activo":
                    r_auto = str(u_match_auto.get("Rol", "Estudiante")).strip()
                    n_auto = normalize_cefr(u_match_auto.get("Nivel", "B1"))
                    g_auto = str(u_match_auto.get("Grado_Academico", "Licenciatura / Universidad")).strip() or "Licenciatura / Universidad"
                    st.session_state.authenticated = True
                    st.session_state.current_user = str(u_match_auto.get("Usuario", "")).strip()
                    st.session_state.user_role = r_auto
                    st.session_state.user_permissions = resolve_permission_profile(u_match_auto.get("Permisos", ""), r_auto, PERMISSIONS_MATRIX)
                    st.session_state.user_assigned_level = n_auto
                    st.session_state.selected_cefr = n_auto
                    st.session_state.user_academic_grade = g_auto
                    st.session_state.selected_academic_grade = g_auto
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
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🎓 CEI ENGLISH LEARNING PLATFORM</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #475569; font-size: 14px;'>Career English Institute • Global Pedagogical &amp; CEFR Assessment Suite</p>", unsafe_allow_html=True)
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
                                        tok_signed = _sign_session_token(u_db, c_db)
                                        st.session_state.pending_ls_token = tok_signed
                                        st.query_params["cei_auth"] = tok_signed
                                    else:
                                        st.session_state.pending_ls_token = "REMOVE"
                                        if "cei_auth" in st.query_params:
                                            del st.query_params["cei_auth"]
                                    st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error de conexión al verificar credenciales: {e}") 

        st.markdown(
            f"<div style='text-align: center; color: #777; font-size: 12px; margin-top: 15px;'>📍 {institute_address}<br>© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti</div>",
            unsafe_allow_html=True
        )
    st.stop()

DEFAULT_AFFILIATE_TERMS_TEXT = """TÉRMINOS Y CONDICIONES DEL PROGRAMA DE SOCIOS AFILIADOS
CAREER ENGLISH INSTITUTE (CEI) — AGUA PRIETA, SONORA, MÉXICO

PRIMERA. OBJETO Y NATURALEZA JURÍDICA DE LA AFILIACIÓN.
Los presentes Términos y Condiciones regulan la incorporación y participación en el Programa de Socios Afiliados de Career English Institute (CEI), con sede en Agua Prieta, Sonora. La relación entre CEI y el Socio Afiliado es de carácter estrictamente mercantil e independiente (comisión mercantil y prestación de servicios independientes), regida por el Código de Comercio y el Código Civil Federal y del Estado de Sonora. En ningún caso constituirá relación laboral, subordinación, dependencia económica ni representación legal.

SEGUNDA. REQUISITOS OBLIGATORIOS DE INSCRIPCIÓN Y EXPEDIENTE.
1. Identificación Oficial Vigente: Copia digital legible por ambos lados (anverso y reverso) de INE o Pasaporte vigente.
2. Registro Federal de Contribuyentes (RFC): Constancia de Situación Fiscal actualizada emitida por el SAT, habilitada para emitir CFDI por concepto de comisiones u honorarios mercantiles.
3. Datos de Contacto y Cuenta Bancaria: Correo electrónico, teléfono/WhatsApp activo, domicilio completo y cuenta CLABE a nombre del titular.

TERCERA. ACTIVIDADES Y COMPROMISOS DEL SOCIO AFILIADO.
1. Invitar y canalizar prospectos interesados en los programas académicos de CEI.
2. Motivar y acompañar a sus estudiantes referidos para mantener la constancia en su aprendizaje.
3. Motivar oportunamente a sus estudiantes referidos para mantenerse al corriente con sus pagos mensuales.

CUARTA. ESQUEMA DE COMISIONES Y FACTURACIÓN FISCAL (CFDI).
Para recibir el pago de las comisiones liquidadas del mes inmediato anterior, el Socio Afiliado deberá expedir y entregar a CEI su Factura Electrónica (CFDI) de honorarios / comisiones mercantiles dentro de los primeros cinco (5) días hábiles del mes siguiente, cumpliendo con los requisitos del Código Fiscal de la Federación (CFF).

QUINTA. LEGISLACIÓN APLICABLE Y JURISDICCIÓN.
Para la interpretación y cumplimiento de los presentes Términos y Condiciones, las partes se someten a las leyes vigentes en los Estados Unidos Mexicanos y a la jurisdicción competente de los tribunales de Agua Prieta, Sonora, México."""


def _open_legal_pg_conn():
    """Abre conexión directa a PostgreSQL usando los secretos configurados."""
    def _sec(k: str) -> str:
        if k in st.secrets:
            return str(st.secrets[k]).strip()
        for v in st.secrets.values():
            if isinstance(v, dict) and k in v:
                return str(v[k]).strip()
        return ""

    pg_host = _sec("PG_HOST")
    pg_user = _sec("PG_USER")
    pg_pass = _sec("PG_PASSWORD")
    pg_port = int(_sec("PG_PORT") or 6543)
    pg_db = _sec("PG_DBNAME") or "postgres"
    if pg_host and pg_user and pg_pass:
        return psycopg.connect(
            host=pg_host, port=pg_port, dbname=pg_db,
            user=pg_user, password=pg_pass, sslmode="require", prepare_threshold=None
        )
    db_url = _sec("SUPABASE_DB_URL") or _sec("DATABASE_URL")
    if not db_url and "postgres" in st.secrets and isinstance(st.secrets["postgres"], dict):
        db_url = str(st.secrets["postgres"].get("url", "")).strip()
    if not db_url:
        return None
    if "sslmode=" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require"
    return psycopg.connect(db_url, prepare_threshold=None)


def get_affiliate_terms_pg() -> dict:
    """Obtiene los Términos y Condiciones de Afiliación vigentes desde PostgreSQL."""
    conn = _open_legal_pg_conn()
    if not conn:
        return {"texto": DEFAULT_AFFILIATE_TERMS_TEXT, "updated_by": "Sistema", "updated_at": ""}
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
                cur.execute("SELECT contenido, updated_by, updated_at FROM cei_configuracion_legal WHERE clave = 'terminos_afiliacion';")
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        "INSERT INTO cei_configuracion_legal (clave, contenido, updated_by) VALUES ('terminos_afiliacion', %s, 'Owner');",
                        (DEFAULT_AFFILIATE_TERMS_TEXT,)
                    )
                    return {"texto": DEFAULT_AFFILIATE_TERMS_TEXT, "updated_by": "Owner", "updated_at": ""}
                return {
                    "texto": str(row[0] or DEFAULT_AFFILIATE_TERMS_TEXT),
                    "updated_by": str(row[1] or ""),
                    "updated_at": str(row[2] or "")[:19]
                }
    except Exception:
        return {"texto": DEFAULT_AFFILIATE_TERMS_TEXT, "updated_by": "Sistema", "updated_at": ""}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def save_affiliate_terms_pg(nuevo_texto: str, autor: str) -> tuple[bool, str]:
    """Guarda los Términos y Condiciones de Afiliación editados por el Owner/Admin autorizado."""
    conn = _open_legal_pg_conn()
    if not conn:
        return False, "No hay conexión activa con Supabase PostgreSQL."
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
                cur.execute("""
                    INSERT INTO cei_configuracion_legal (clave, contenido, updated_by, updated_at)
                    VALUES ('terminos_afiliacion', %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (clave) DO UPDATE SET
                        contenido = EXCLUDED.contenido,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = CURRENT_TIMESTAMP;
                """, (nuevo_texto.strip(), autor))
        return True, "✅ Términos y Condiciones de Afiliación actualizados y publicados en vivo."
    except Exception as e:
        return False, f"Error al guardar términos: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass

DEFAULT_STUDENT_TERMS_TEXT = """TÉRMINOS, CONDICIONES Y REGLAMENTO ACADÉMICO DE INSCRIPCIÓN
CAREER ENGLISH INSTITUTE (CEI) — AGUA PRIETA, SONORA, MÉXICO

PRIMERA. NATURALEZA DEL SERVICIO (100% EN LÍNEA) Y MARCO LEGAL APLICABLE.
Los presentes Términos y Condiciones regulan la prestación de servicios educativos privados de enseñanza del idioma inglés en modalidad 100% en línea (clases en vivo por videoconferencia y plataforma educativa interactiva), impartidos por Career English Institute (CEI), con sede administrativa en Agua Prieta, Sonora, México, de conformidad con la legislación civil, educativa y de protección al consumidor vigente en los Estados Unidos Mexicanos y en el Estado de Sonora.

SEGUNDA. CALIBRACIÓN AL MARCO COMÚN EUROPEO (CEFR).
Los programas académicos de CEI son flexibles y ajustables al nivel real del estudiante conforme al Marco Común Europeo de Referencia para las Lenguas (CEFR: A1, A2, B1, B2, C1 y C2). Al formalizar su inscripción, la plataforma educativa y todas las lecciones, audios, evaluaciones y ejercicios generados en ella quedarán calibrados automáticamente al nivel CEFR indicado en este formulario, pudiendo ajustarse previa valoración académica.

TERCERA. DURACIÓN DEL PROGRAMA (9 PERIODOS) Y PERIODOS VACACIONALES ACTIVOS.
1. Estructura del Nivel: Cada nivel académico está estructurado en nueve (9) periodos mensuales de cuatro (4) semanas cada uno.
2. Periodos Vacacionales Activos (Verano e Invierno): Durante los recesos vacacionales largos de verano e invierno no se imparten clases en vivo en línea; sin embargo, la plataforma educativa permanecerá plenamente activa y disponible las 24 horas para que el estudiante continúe practicando y manteniendo su avance académico.
3. Conclusión del Nivel: Al finalizar satisfactoriamente los 9 periodos y acreditar la rúbrica correspondiente, el estudiante obtiene su constancia o certificado institucional del nivel cursado.

CUARTA. ASISTENCIA EN LÍNEA, INASISTENCIAS JUSTIFICADAS Y RECUPERACIÓN DE CLASES.
1. Asistencia del Estudiante y Asignación de Trabajo (Homework): El estudiante se compromete a conectarse puntualmente a sus clases en línea. En caso de requerir ausentarse por causa justificada, deberá avisar con anticipación a la institución o docente para recibir su asignación de trabajo (homework). La entrega y cumplimiento oportuno de dicha asignación será suficiente para dar la clase por dada o satisfecha.
2. Ausencia del Docente: En caso de que el docente deba ausentarse por causa justificada, se notificará con anticipación al estudiante y, por mutuo acuerdo entre ambas partes, se reprogramará y recuperará íntegramente la clase perdida sin costo adicional.

QUINTA. RÚBRICA DE EVALUACIÓN POR CRITERIOS Y ACCESO AL BOLETÍN.
1. Evaluación Integral: El estudiante deberá asegurarse de completar en tiempo y forma los criterios de la rúbrica de calificaciones acordes a su nivel (Reading & Quiz 30%, Viewing & Listening 25%, Alphabetical & Speaking 25% y Writing Skill APA 7 20%).
2. Puntualidad en Mensualidades y Boletín: El estudiante (o su padre/tutor) se compromete a mantenerse al corriente en el pago de sus mensualidades (dentro de la 4ta semana de cada bloque) e informarlo oportunamente en la plataforma para conservar activo su acceso al Boletín Informativo de Calificaciones y avances.

SEXTA. PROTECCIÓN DE DATOS PERSONALES Y JURISDICCIÓN.
De conformidad con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP), los datos recabados se utilizarán exclusivamente para fines académicos, administrativos y de certificación interna. Para cualquier controversia derivada de la interpretación o cumplimiento de este acuerdo, las partes se someten a las leyes vigentes y a los tribunales competentes de Agua Prieta, Sonora, México."""


def get_student_terms_pg() -> dict:
    """Obtiene los Términos y Condiciones de Inscripción de Estudiantes desde PostgreSQL."""
    conn = _open_legal_pg_conn()
    if not conn:
        return {"texto": DEFAULT_STUDENT_TERMS_TEXT, "updated_by": "Sistema", "updated_at": ""}
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
                cur.execute("SELECT contenido, updated_by, updated_at FROM cei_configuracion_legal WHERE clave = 'terminos_estudiantes';")
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        "INSERT INTO cei_configuracion_legal (clave, contenido, updated_by) VALUES ('terminos_estudiantes', %s, 'Owner');",
                        (DEFAULT_STUDENT_TERMS_TEXT,)
                    )
                    return {"texto": DEFAULT_STUDENT_TERMS_TEXT, "updated_by": "Owner", "updated_at": ""}
                return {
                    "texto": str(row[0] or DEFAULT_STUDENT_TERMS_TEXT),
                    "updated_by": str(row[1] or ""),
                    "updated_at": str(row[2] or "")[:19]
                }
    except Exception:
        return {"texto": DEFAULT_STUDENT_TERMS_TEXT, "updated_by": "Sistema", "updated_at": ""}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def save_student_terms_pg(nuevo_texto: str, autor: str) -> tuple[bool, str]:
    """Guarda los Términos y Condiciones de Estudiantes editados por el Owner/Admin autorizado."""
    conn = _open_legal_pg_conn()
    if not conn:
        return False, "No hay conexión activa con Supabase PostgreSQL."
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
                cur.execute("""
                    INSERT INTO cei_configuracion_legal (clave, contenido, updated_by, updated_at)
                    VALUES ('terminos_estudiantes', %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (clave) DO UPDATE SET
                        contenido = EXCLUDED.contenido,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = CURRENT_TIMESTAMP;
                """, (nuevo_texto.strip(), autor))
        return True, "✅ Términos y Condiciones de Estudiantes actualizados y publicados en vivo."
    except Exception as e:
        return False, f"Error al guardar términos de estudiantes: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def evaluar_pronunciacion_oral_ia(
    media_bytes: bytes,
    mime_type: str,
    reference_text: str,
    cefr_level: str,
    grammar_topic: str
) -> dict:
    """Evalúa pronunciación, fluidez y gramática oral en audio o video usando Gemini Multimodal."""
    gm = init_gemini_client()
    clean_ref = re.sub(r"[*#`]", "", str(reference_text or "")).strip()[:2500]
    prompt_eval = f"""
    You are an expert CEFR English pronunciation, phonetics, and oral fluency examiner for Career English Institute (CEI).
    Evaluate the student's spoken recording (audio or video) reading or discussing the following reference text.
    - Target CEFR Level: {cefr_level}
    - Target Grammar Topic: {grammar_topic}
    - Reference Text:
    \"\"\"{clean_ref}\"\"\"

    Return strictly a valid JSON object (no markdown fences) with these exact keys:
    {{
      "score_percent": <number from 0 to 100>,
      "cefr_performance": "<short label e.g. B1 Solid>",
      "transcription": "<accurate transcription of what the student actually said>",
      "phonetic_feedback": "<specific feedback in Spanish on English vowels, consonants, word stress, and mispronounced words>",
      "fluency_prosody": "<specific feedback in Spanish on rhythm, intonation, pacing, and pauses>",
      "grammar_accuracy": "<specific feedback in Spanish on oral grammar accuracy>",
      "actionable_tips": ["<tip 1 in Spanish>", "<tip 2 in Spanish>", "<tip 3 in Spanish>"]
    }}
    """
    try:
        from google.genai import types
        part_media = types.Part.from_bytes(data=media_bytes, mime_type=mime_type)
        resp = gm.models.generate_content(
            model="gemini-2.5-flash",
            contents=[part_media, prompt_eval]
        )
        raw_txt = str(getattr(resp, "text", "") or "").strip()
        raw_txt = re.sub(r"^```(?:json)?|```$", "", raw_txt, flags=re.MULTILINE).strip()
        data = json.loads(raw_txt)
        return {
            "score_percent": round(float(data.get("score_percent", 75.0)), 1),
            "cefr_performance": str(data.get("cefr_performance") or cefr_level),
            "transcription": str(data.get("transcription") or ""),
            "phonetic_feedback": str(data.get("phonetic_feedback") or "Articulación clara en general."),
            "fluency_prosody": str(data.get("fluency_prosody") or "Ritmo adecuado al nivel."),
            "grammar_accuracy": str(data.get("grammar_accuracy") or "Estructuras gramaticales consistentes."),
            "actionable_tips": list(data.get("actionable_tips") or [])
        }
    except Exception as e:
        return {
            "score_percent": 0.0,
            "cefr_performance": cefr_level,
            "transcription": "",
            "phonetic_feedback": f"No se pudo completar el análisis automático: {e}",
            "fluency_prosody": "Intenta grabar nuevamente en un entorno silencioso.",
            "grammar_accuracy": "Pendiente de evaluación.",
            "actionable_tips": ["Verifica que el micrófono tenga permiso activo y habla con claridad."]
        }


# ==============================================================================
# PARTE 12A: EVALUACIÓN DE CAPACIDADES RBAC Y TARJETA CREADORA CENTRAL
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

# --- VALORES SEGUROS POR DEFECTO (SIN BARRA LATERAL IZQUIERDA) ---
generar_btn = False
usuario = str(st.session_state.get("current_user") or "Usuario").strip()
cefr_level = st.session_state.get("selected_cefr") or st.session_state.get("user_assigned_level") or "B1 (Intermediate)"
academic_grade = st.session_state.get("selected_academic_grade") or st.session_state.get("user_academic_grade") or "Licenciatura / Universidad"
gramatica_b1 = st.session_state.get("selected_grammar") or "General English Grammar"
contexto = str(st.session_state.get("sb_context_input") or "")
personas = str(st.session_state.get("sb_personas_input") or "")
asunto = str(st.session_state.get("sb_subject_input") or "")
tipo_texto = str(st.session_state.get("sb_tipo_texto_input") or "Narración (Narration)")
has_lesson_now = bool(str(st.session_state.get("generated_text") or "").strip())
stage_5_now = st.session_state.get("active_stage_5", "READING")
stage_now = stage_5_now

if st.session_state.pop("trigger_generate_from_top", False):
    generar_btn = True



# ==============================================================================
# PARTE 12B — MITAD 1 DE 2: CABECERA INSTITUCIONAL, VISOR DE USUARIO Y QR APP
# ==============================================================================
if "active_stage_5" not in st.session_state:
    st.session_state["active_stage_5"] = "READING"
if "show_lesson_creator" not in st.session_state:
    st.session_state["show_lesson_creator"] = False

puede_ver_qr_hdr = is_owner or can("Mostrar_QR_App_Header")
u_login_hdr = str(st.session_state.get("current_user") or usuario or "").strip()
reg_padron_hdr = next(
    (r for r in (load_padron_records() or [])
     if str(r.get("Usuario") or "").strip().lower() == u_login_hdr.lower()),
    {}
)
mat_hdr_mostrar = str(reg_padron_hdr.get("Matricula") or reg_padron_hdr.get("ID") or "").strip()
nom_hdr_mostrar = str(
    reg_padron_hdr.get("Nombre_Completo")
    or reg_padron_hdr.get("Nombre")
    or st.session_state.get("current_user_fullname")
    or u_login_hdr
    or "Usuario"
).strip()
rol_hdr_mostrar = "Propietario / Owner" if is_owner else str(st.session_state.get("user_role") or "Usuario").strip()

col_logo, col_title, col_logout = st.columns([0.9, 4.1, 1.3])
with col_logo:
    if os.path.exists("static/LOGO CEI APP.png"):
        st.image("static/LOGO CEI APP.png", width=105)
    elif os.path.exists("LOGO CEI APP.png"):
        st.image("LOGO CEI APP.png", width=105)
    else:
        st.markdown("## 🎓")

with col_title:
    cefr_raw = st.session_state.get("selected_cefr") or "B1"
    cefr_badge = next(iter(str(cefr_raw).split()), "B1")
    st.markdown("#### 🏛️ CAREER ENGLISH INSTITUTE — GLOBAL PEDAGOGICAL SUITE")
    st.title("🎓 CEI ENGLISH LEARNING PLATFORM")
    st.caption(
        f"**CEFR Level {cefr_badge} Integrated Competency Framework**  |  "
        "Author: Jacob Zumaya Prianti  |  APA 7th Ed. Academic Standard"
    )
    st.markdown(
        f"👤 **Sesión Activa:** **{nom_hdr_mostrar}** (`{u_login_hdr}`)"
        + (f"  •  🆔 **Matrícula:** `{mat_hdr_mostrar}`" if mat_hdr_mostrar else "")
        + f"  •  🏷️ **Tipo:** **{rol_hdr_mostrar}**"
    )

with col_logout:
    if st.button("🚪 Salir", type="secondary", width="stretch", key="btn_top_logout_clean"):
        for k_out in list(st.session_state.keys()):
            del st.session_state[k_out]
        st.query_params.clear()
        st.rerun()

    if puede_ver_qr_hdr:
        mostrar_qr_hdr_now = st.toggle(
            "📲 QR App",
            value=False,
            key="tgl_header_qr_app_visible",
            help="Muestra u oculta el QR oficial para instalar la App CEI"
        )
        if mostrar_qr_hdr_now:
            url_install_hdr = "https://" + "drzumaya.github.io/My-CEI-English-Reading-Improvement-Tool/"


            buf_qh = io.BytesIO()
            qrcode.make(url_install_hdr).save(buf_qh, format="PNG")
            qa_bytes_hdr = buf_qh.getvalue()
            qh_b64 = base64.b64encode(qa_bytes_hdr).decode("utf-8")

            st.iframe(
                f"""
                <div style="text-align:center; background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:6px; font-family:-apple-system, BlinkMacSystemFont, sans-serif;">
                    <img src="data:image/png;base64,{qh_b64}"
                         title="Doble clic para proyectar QR de App CEI"
                         ondblclick="expandirQRAppCEI()"
                         style="width:86px;height:86px;border-radius:8px;border:2px solid #0b2545;padding:3px;background:white;cursor:zoom-in;" />
                    <div style="margin-top:4px;">
                        <button onclick="expandirQRAppCEI()" style="
                            background:#0b2545;color:white;border:none;border-radius:6px;
                            padding:4px 8px;font-size:10px;font-weight:700;cursor:pointer;width:100%;
                        ">🔍 Expandir QR</button>
                    </div>
                </div>
                <script>
                function expandirQRAppCEI() {{
                    const pDoc = window.parent.document;
                    const prev = pDoc.getElementById('modal_qr_app_cei_fs');
                    if (prev) prev.remove();
                    const m = pDoc.createElement('div');
                    m.id = 'modal_qr_app_cei_fs';
                    m.style.cssText = 'position:fixed;inset:0;background:rgba(11,37,69,0.96);z-index:999999;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;font-family:-apple-system,BlinkMacSystemFont,sans-serif;';
                    m.innerHTML = `
                        <img src="data:image/png;base64,{qh_b64}" style="width:340px;height:340px;border-radius:18px;background:white;padding:16px;box-shadow:0 12px 36px rgba(0,0,0,0.45);" />
                        <p style="color:white;font-size:20px;margin-top:16px;font-weight:700;">📲 QR Oficial de Descarga e Instalación de la App CEI</p>
                        <p style="color:#cbd5e1;font-size:13px;max-width:440px;text-align:center;">Comparte o proyecta este código QR para instalar la App CEI en celular o Mac con su escudo oficial.</p>
                        <button style="margin-top:12px;background:#ef4444;color:white;border:none;border-radius:8px;padding:8px 18px;font-size:13px;font-weight:700;cursor:pointer;">✖️ Cerrar Proyección</button>
                    `;
                    m.onclick = () => m.remove();
                    pDoc.body.appendChild(m);
                }}
                </script>
                """,
                height=138
            )
            st.download_button(
                "⬇️ PNG",
                data=qa_bytes_hdr,
                file_name="QR_Instalar_App_CEI.png",
                mime="image/png",
                width="stretch",
                key="btn_dl_hdr_qr_app"
            )
es_docente_rol = (curr_r_clean in ["teacher", "docente"]) or can("Ver_Portal_Docente")
es_admin_o_staff = is_owner or can("Ver_Panel_Admin") or (curr_r_clean in ["admin", "administrador", "propietario", "owner"])
solo_docente = es_docente_rol and not es_admin_o_staff
es_socio_afiliado = (curr_r_clean in ["socio", "partner", "afiliado", "socio afiliado"])
solo_socio_afiliado = es_socio_afiliado and not es_admin_o_staff and not es_docente_rol

if solo_socio_afiliado:
    url_portal_aff_redir = str(
        st.secrets.get("AFFILIATE_PORTAL_URL")
        or ("https://" + "ceiafiliados.streamlit.app")
    ).strip()
    url_app_aff_redir = str(
        st.secrets.get("AFFILIATE_APP_INSTALL_URL")
        or ("https://" + "drzumaya.github.io/My-CEI-English-Reading-Improvement-Tool/socio_app.html")
    ).strip()

    buf_qr_redir = io.BytesIO()
    qrcode.make(url_portal_aff_redir).save(buf_qr_redir, format="PNG")

    with st.container(border=True):
        st.warning("🤝 **Acceso Exclusivo de Socios Afiliados — Career English Institute (CEI)**")
        st.markdown(
            "Esta aplicación está reservada para **Estudiantes, Docentes y Administración Académica**.\n\n"
            "Como **Socio Afiliado**, accede a tu **Portal Oficial de Asociados** para gestionar tus códigos QR de inscripción, "
            "monitorear las rachas de tus alumnos y revisar tus comisiones:"
        )
        c_ra1, c_ra2 = st.columns([2.2, 1.1])
        with c_ra1:
            st.link_button(
                "🚀 Entrar a mi Portal Oficial de Socios Afiliados",
                url=url_portal_aff_redir,
                type="primary",
                width="stretch"
            )
            st.link_button(
                "📲 Instalar App Portal Socios en mi Celular / PC",
                url=url_app_aff_redir,
                width="stretch"
            )
        with c_ra2:
            st.image(buf_qr_redir.getvalue(), width=145, caption="QR Portal Socios CEI")
            st.caption(f"🔗 `{url_portal_aff_redir}`")
    st.stop()

# Medidor Estadístico de Compliance y Confianza Institucional visible para el usuario activo
try:
    from compliance_engine import render_medidor_compliance_confianza
    if not solo_docente:
        render_medidor_compliance_confianza(
            usuario=u_login_hdr,
            rol="Propietario" if is_owner else curr_r_clean
        )
except Exception:
    pass

puede_ver_panel_educativo = is_owner or can("Ver_Panel_Educativo")
if not puede_ver_panel_educativo:
    st.session_state["active_stage_5"] = "PORTAL"
    st.session_state["show_lesson_creator"] = False
    st.session_state["generated_text"] = ""

if solo_docente:
    lbl_btn_portal = "🧑‍🏫 MI PORTAL DOCENTE CEI"
elif es_admin_o_staff:
    lbl_btn_portal = "🛡️ PANEL ADMINISTRATIVO"
else:
    lbl_btn_portal = "🎓 MI PANEL ESTUDIANTIL"

tiene_leccion_activa = bool(str(st.session_state.get("generated_text") or "").strip())

if not tiene_leccion_activa:
    if puede_ver_panel_educativo:
        c_init1, c_init2 = st.columns(2)
        with c_init1:
            en_panel_edu = (st.session_state.get("active_stage_5", "READING") != "PORTAL")
            if st.button(
                "🎓 PANEL EDUCATIVO",
                type="primary" if en_panel_edu else "secondary",
                width="stretch",
                key="btn_init_2_panel_educativo"
            ):
                st.session_state["active_stage_5"] = "READING"
                st.session_state["active_admin_workspace"] = None
                st.session_state["active_student_workspace"] = None
                st.rerun()

        with c_init2:
            if st.button(
                lbl_btn_portal,
                type="primary" if st.session_state["active_stage_5"] == "PORTAL" else "secondary",
                width="stretch",
                key="btn_init_2_portal"
            ):
                st.session_state["active_stage_5"] = "PORTAL"
                st.session_state["show_lesson_creator"] = False
                st.session_state["creator_missing_fields"] = []
                if es_admin_o_staff:
                    st.session_state["active_admin_workspace"] = st.session_state.get("active_admin_workspace") or "💳 Cobranza Mensual e IVA"
                elif not solo_docente:
                    st.session_state["active_student_workspace"] = st.session_state.get("active_student_workspace") or "💳 Mis Pagos (9 Bloques)"
                st.rerun()
    else:
        if st.button(
            lbl_btn_portal,
            type="primary",
            width="stretch",
            key="btn_init_2_portal_unico"
        ):
            st.session_state["active_stage_5"] = "PORTAL"
            st.session_state["show_lesson_creator"] = False
            st.session_state["creator_missing_fields"] = []
            if es_admin_o_staff:
                st.session_state["active_admin_workspace"] = st.session_state.get("active_admin_workspace") or "💳 Cobranza Mensual e IVA"
            elif not solo_docente:
                st.session_state["active_student_workspace"] = st.session_state.get("active_student_workspace") or "💳 Mis Pagos (9 Bloques)"
            st.rerun()

    if puede_ver_panel_educativo and st.session_state.get("active_stage_5", "READING") != "PORTAL":
        abierto_creador = bool(st.session_state.get("show_lesson_creator"))
        with st.container(border=True):
            c_edu_gen, c_edu_sep = st.columns([1.2, 2.4])
            with c_edu_gen:
                lbl_gen_inner = "✖️ Cerrar Creador de Lección" if abierto_creador else "✨ GENERAR LECCIÓN"
                if st.button(
                    lbl_gen_inner,
                    type="primary",
                    width="stretch",
                    key="btn_inside_edu_toggle_creator"
                ):
                    st.session_state["show_lesson_creator"] = not abierto_creador
                    st.session_state["creator_missing_fields"] = []
                    st.rerun()
            with c_edu_sep:
                st.caption("Crea una lección nueva con IA o selecciona abajo una lección guardada por Folio para abrirla.")

# Si un Docente abrió MI PORTAL DOCENTE CEI, renderizarlo directamente
if solo_docente and st.session_state.get("active_stage_5") == "PORTAL":
    from portal_docente import render_portal_docente_cei
    render_portal_docente_cei(
        usuario_actual=u_login_hdr,
        rol_actual=curr_r_clean,
        puede_ver_estudiantes=can("Ver_Mis_Estudiantes_Docente"),
        puede_motivar_wa=can("Motivar_Estudiantes_WhatsApp"),
        puede_retroalimentar=can("Asignar_Retroalimentacion_Docente"),
        puede_ver_comisiones=can("Ver_Comisiones_Pagos_Docente"),
        es_admin_o_owner=False,
        dia_corte_cfdi=25,
        institute_address=str(institute_address or "Agua Prieta, Sonora, México")
    )
    st.stop()




# ==============================================================================
# PARTE 12B — MITAD 2 DE 2 (FINAL): TARJETA CREADORA CENTRAL Y BOTONES MAESTROS
# ==============================================================================
    if st.session_state.get("show_lesson_creator") and st.session_state["active_stage_5"] != "PORTAL":
        with st.container(border=True):
            st.markdown("### ✨ Configurador Académico de Nueva Lección CEFR")
            st.caption("Completa los parámetros pedagógicos en el centro para generar tu lección con Audio, Quiz y Video educativo.")

            col_c_izq, col_c_der = st.columns(2)
            with col_c_izq:
                if is_owner or can("Previsualizar_A1_C2"):
                    default_idx = (
                        cefr_options.index(st.session_state.user_assigned_level)
                        if st.session_state.user_assigned_level in cefr_options else 2
                    )
                    cefr_level = st.selectbox("🎯 Nivel Objetivo (CEFR A1 - C2):", cefr_options, index=default_idx, key="sb_cefr_sel")

                    g_idx = (
                        GRADOS_ACADEMICOS.index(st.session_state.user_academic_grade)
                        if st.session_state.user_academic_grade in GRADOS_ACADEMICOS else 4
                    )
                    academic_grade = st.selectbox("🎓 Grado Académico:", GRADOS_ACADEMICOS, index=g_idx, key="sb_grade_sel")
                else:
                    cefr_level = st.session_state.user_assigned_level
                    academic_grade = st.session_state.user_academic_grade
                    st.info(f"🎯 **Nivel CEFR:** {cefr_level}  |  🎓 **Grado:** {academic_grade}")

                st.session_state["selected_cefr"] = cefr_level
                st.session_state["selected_academic_grade"] = academic_grade

                cefr_short_sb = next(iter(cefr_level.split()), "B1")
                temas_nivel_actual = CEFR_GRAMMAR_TOPICS.get(cefr_short_sb, CEFR_GRAMMAR_TOPICS["B1"])
                gramatica_b1 = st.selectbox(
                    f"📐 Tema Gramatical ({cefr_short_sb}):",
                    temas_nivel_actual,
                    index=0,
                    key="selected_grammar_topic"
                )
                st.session_state["selected_grammar"] = gramatica_b1

                tipo_texto = st.selectbox(
                    "📝 Formato Discursivo:",
                    [
                        "Preguntas (Comprehension & Grammar Questions)",
                        "Descripción (Detailed Description)",
                        "Narración (Narration)",
                        "Juicio (Critical Judgment / Opinion)",
                        "Explicación (Clear Explanation)",
                        "Historia (Short Story)",
                        "Storytelling (Engaging Narrative)"
                    ],
                    key="sb_tipo_texto_input"
                )

            with col_c_der:
                contexto = st.text_input(
                    "1️⃣ Contexto / Lugar / Tema (Español / English):",
                    placeholder="Ej: En un aeropuerto en Londres / At an airport",
                    key="sb_context_input"
                )
                personas = st.text_input(
                    "2️⃣ Personas / Personajes (Español / English):",
                    placeholder="Ej: Un turista y una azafata / A tourist and a pilot",
                    key="sb_personas_input"
                )
                asunto = st.text_input(
                    "3️⃣ Asunto / Materia (Español / English):",
                    placeholder="Ej: Equipaje perdido / Lost luggage",
                    key="sb_subject_input"
                )

            if st.session_state.get("creator_missing_fields"):
                faltantes_txt = "  •  ".join(st.session_state["creator_missing_fields"])
                st.warning(f"⚠️ **Por favor completa las siguientes casillas obligatorias:** {faltantes_txt}")

            if st.button(f"🚀 CREAR Y DESPLEGAR LECCIÓN ({cefr_short_sb})", type="primary", width="stretch", key="btn_center_create_lesson"):
                faltantes_now = []
                if not str(contexto).strip():
                    faltantes_now.append("1️⃣ **Contexto / Lugar / Tema**")
                if not str(asunto).strip():
                    faltantes_now.append("3️⃣ **Asunto / Materia**")
                if not str(gramatica_b1).strip():
                    faltantes_now.append("📐 **Tema Gramatical**")

                if faltantes_now:
                    st.session_state["creator_missing_fields"] = faltantes_now
                    st.rerun()
                else:
                    st.session_state["creator_missing_fields"] = []
                    st.session_state["show_lesson_creator"] = False
                    generar_btn = True
else:
    st.session_state["show_lesson_creator"] = False
    if st.session_state.get("active_stage_5") in ["SPEAKING", "WRITING"]:
        st.session_state["active_stage_5"] = "READING" if st.session_state["active_stage_5"] == "SPEAKING" else "VIEWING"
    stage_actual = st.session_state.get("active_stage_5", "READING")

    b1, b2, b3 = st.columns([1.35, 1.35, 1.0])
    botones_maestros = [
        (b1, "READING", "📖 1. READING (30%) & 🎙️ SPEAKING (25%)"),
        (b2, "VIEWING", "🎬 2. VIEWING (25%) & ✍️ WRITING (20%)"),
        (b3, "PORTAL", lbl_btn_portal),
    ]

    for col_b, stage_key, stage_label in botones_maestros:
        es_activo = (stage_actual == stage_key)
        texto_btn = f"🟢 {stage_label}" if es_activo else f"⏳ {stage_label}"
        with col_b:
            if st.button(
                texto_btn,
                type="primary" if es_activo else "secondary",
                width="stretch",
                key=f"btn_master_stage_{stage_key}"
            ):
                st.session_state["active_stage_5"] = stage_key
                st.session_state["viewing_center_stage"] = (stage_key == "VIEWING")
                if stage_key == "PORTAL":
                    if es_admin_o_staff or es_socio_afiliado:
                        st.session_state["active_admin_workspace"] = st.session_state.get("active_admin_workspace") or "💳 Cobranza Mensual e IVA"
                    else:
                        st.session_state["active_student_workspace"] = st.session_state.get("active_student_workspace") or "💳 Mis Pagos (9 Bloques)"
                else:
                    st.session_state["active_admin_workspace"] = None
                    st.session_state["active_student_workspace"] = None
                if stage_key == "VIEWING" and not st.session_state.get("video_watch_started_ts"):
                    st.session_state["video_watch_started_ts"] = time.time()
                st.rerun()




# ==============================================================================
# PARTE 13A1-A: HELPERS DE CIERRE DE PANEL Y QR OFICIAL CON ID DE AFILIADO
# ==============================================================================
DEFAULT_STUDENT_INSCRIPTION_URL = "https://inscripcioncei.streamlit.app"


def _cerrar_panel_y_volver_leccion():
    st.session_state["active_admin_workspace"] = None
    st.session_state["active_student_workspace"] = None
    st.session_state["qr_zoom_fullscreen"] = False
    st.session_state["show_gradebook_panel"] = False
    st.session_state["show_student_payments_panel"] = False
    st.session_state["active_stage_5"] = "READING"

# ==============================================================================
# MOTOR DE CATEGORÍAS ESTUDIANTILES (BRONCE / PLATA / ORO) — BLOQUE A DE 2
# ==============================================================================
CRITERIOS_POR_NIVEL_CEFR = {
    "A1": [
        "Verb To Be & Personal Pronouns",
        "Simple Present & Daily Routines",
        "Articles, Plurals & Demonstratives",
        "There is / There are & Prepositions of Place",
        "Present Continuous (Actions in Progress)",
        "Can / Can't (Abilities & Permissions)",
        "Simple Past (Regular & Irregular Verbs)",
        "Countable / Uncountable Nouns & Quantifiers",
        "Future with Going to (Plans & Intentions)"
    ],
    "A2": [
        "Past Continuous vs. Simple Past",
        "Comparatives & Superlatives",
        "Present Perfect (Experiences: Ever / Never)",
        "Modal Verbs (Should, Must, Have to)",
        "Future Simple (Will vs. Going to)",
        "First Conditional (Real Possibilities)",
        "Object Pronouns & Possessive Pronouns",
        "Adverbs of Manner & Frequency",
        "Used to (Past Habits & States)"
    ],
    "B1": [
        "Present Perfect Continuous (For / Since)",
        "Past Perfect Simple (Narrative Sequence)",
        "Second Conditional (Hypothetical Situations)",
        "Passive Voice (Present & Past Simple)",
        "Reported Speech (Statements & Questions)",
        "Defining & Non-Defining Relative Clauses",
        "Gerunds vs. Infinitives (Verb Patterns)",
        "Modals of Deduction (Must, Might, Can't)",
        "Tag Questions & Indirect Questions"
    ],
    "B2": [
        "Third Conditional & Mixed Conditionals",
        "Passive Voice (All Tenses & Causative Have/Get)",
        "Future Perfect & Future Continuous",
        "Wish / If Only (Regrets & Desires)",
        "Advanced Reported Speech & Reporting Verbs",
        "Participle Clauses & Cleft Sentences",
        "Modal Perfects (Should have, Could have)",
        "Inversion for Emphasis & Negative Adverbials",
        "Academic Connectors & Discourse Markers"
    ],
    "C1": [
        "Subjunctive Mood & Mandative Structures",
        "Advanced Inversion & Fronting",
        "Ellipsis & Substitution in Academic Prose",
        "Complex Noun Phrases & Nominalization",
        "Nuanced Modality & Epistemic Stance",
        "Advanced Conditional Alternatives (Provided, Were it not)",
        "Rhetorical Devices & Hedging in Research",
        "Idiomatic Phrasal Verbs & Collocations",
        "APA 7th Academic Synthesis & Critical Tone"
    ],
    "C2": [
        "Mastery of Register, Nuance & Stylistic Shift",
        "Complex Syntactic Embedding & Subordination",
        "Archaisms, Legal & Diplomatic English Structures",
        "Precision Lexical Collocations & Figurative Idioms",
        "Advanced Discourse Cohesion & Pragmatics",
        "Prosodic Stress & Phonological Subtlety",
        "Critical Argumentation & Counter-Refutation",
        "Cross-Cultural Rhetoric & Editorial Style",
        "Publication-Grade Academic Writing (APA 7)"
    ]
}


def calcular_categoria_automatica_estudiante(student_user: str, nivel_cefr: str = "B1") -> dict:
    """Calcula automáticamente la categoría (Bronce, Plata, Oro) según clases/lecciones completadas."""
    niv_code = next(iter(str(nivel_cefr or "B1").upper().split()), "B1")
    if niv_code not in CRITERIOS_POR_NIVEL_CEFR:
        niv_code = "B1"
    criterios_lista = CRITERIOS_POR_NIVEL_CEFR[niv_code]
    total_criterios = len(criterios_lista)

    lecciones_user = []
    try:
        todos_folios = load_lessons_history_pg() or []
        lecciones_user = [
            r for r in todos_folios
            if str(r.get("Usuario", "")).strip().lower() == str(student_user or "").strip().lower()
            and str(r.get("Folio") or "").strip()
        ]
    except Exception:
        lecciones_user = []

    conteo_por_tema = {}
    for lec in lecciones_user:
        tema_raw = str(lec.get("Gramatica") or lec.get("Tema") or "General").strip()
        conteo_por_tema[tema_raw] = conteo_por_tema.get(tema_raw, 0) + 1

    total_lecciones = len(lecciones_user)
    criterios_cubiertos = len(conteo_por_tema)
    promedio_por_criterio = (total_lecciones / total_criterios) if total_criterios > 0 else 0.0

    if total_lecciones >= (total_criterios * 3):
        cat_nombre = "🥇 Categoría Oro"
        cat_corto = "ORO"
        meta_mult = 3
    elif total_lecciones >= (total_criterios * 2):
        cat_nombre = "🥈 Categoría Plata"
        cat_corto = "PLATA"
        meta_mult = 2
    else:
        cat_nombre = "🥉 Categoría Bronce"
        cat_corto = "BRONCE"
        meta_mult = 1

    return {
        "nivel": niv_code,
        "criterios": criterios_lista,
        "total_criterios": total_criterios,
        "total_lecciones": total_lecciones,
        "criterios_cubiertos": criterios_cubiertos,
        "promedio_por_criterio": round(promedio_por_criterio, 2),
        "categoria_label": cat_nombre,
        "categoria_corto": cat_corto,
        "meta_mult": meta_mult,
        "conteo_por_tema": conteo_por_tema
    }
# ==============================================================================
# MOTOR DE CATEGORÍAS ESTUDIANTILES (BRONCE / PLATA / ORO) — BLOQUE B DE 2
# ==============================================================================
def _cerrar_guia_y_volver():
    st.session_state["guia_plan_seccion_activa"] = None
    st.session_state["sb_edu_guia_plan_cat"] = "— Guía del Curso: Instrucciones, Plan y Categoría —"
    if st.session_state.get("active_admin_workspace") == "📘 Guía, Plan y Categoría":
        st.session_state["active_admin_workspace"] = None
        st.session_state["active_stage_5"] = "READING"
    if st.session_state.get("active_student_workspace") == "📘 Guía, Plan y Categoría":
        st.session_state["active_student_workspace"] = None
        st.session_state["active_stage_5"] = "READING"


def render_guia_plan_categoria_view(usuario_actual: str, nivel_cefr_actual: str = "B1"):
    """Renderiza en pantalla principal Instrucciones, Plan del Curso (9 meses) y Categoría Estudiantil."""
    datos_cat = calcular_categoria_automatica_estudiante(usuario_actual, nivel_cefr_actual)
    niv_code = datos_cat["nivel"]
    n_crit = datos_cat["total_criterios"]

    with st.container(border=True):
        c_gh1, c_gh2 = st.columns([3.2, 1.2])
        with c_gh1:
            st.markdown("### 📘 Guía Académica, Plan del Curso y Categoría Estudiantil")
            st.caption(
                f"Estudiante / Usuario: **{usuario_actual}**  |  "
                f"Nivel Calibrado: **CEFR {niv_code}**  |  "
                f"Insignia Actual: **{datos_cat['categoria_label']}**"
            )
        with c_gh2:
            st.button(
                "✖️ Cerrar Guía y Volver",
                type="primary",
                width="stretch",
                key="btn_close_guia_plan_cat",
                on_click=_cerrar_guia_y_volver
            )

        opciones_radio = [
            "📖 Instrucciones",
            "📅 Plan del Curso (9 Meses)",
            "🏅 Categoría Estudiantil (Bronce, Plata y Oro)"
        ]
        sel_act = st.session_state.get("guia_plan_seccion_activa") or "📖 Instrucciones"
        idx_radio = opciones_radio.index(sel_act) if sel_act in opciones_radio else 0

        opcion_guia = st.radio(
            "Selecciona el apartado a consultar:",
            opciones_radio,
            index=idx_radio,
            horizontal=True,
            key="radio_guia_plan_categoria_main"
        )
        st.session_state["guia_plan_seccion_activa"] = opcion_guia
        st.divider()

        if opcion_guia == "📖 Instrucciones":
            st.markdown("#### 👋 ¡Bienvenido(a) a tu Plataforma Educativa Career English Institute (CEI)!")
            st.markdown(
                "Esta plataforma está diseñada para acompañarte paso a paso en tu aprendizaje del idioma inglés **100 % en línea**, "
                "combinando tus clases en vivo con práctica inteligente calibrada exactamente a tu nivel **CEFR**.\n\n"
                "##### 🚀 ¿Cómo aprovechar cada lección al máximo?\n"
                "1. **📖 1. Reading & Comprehension (30 %):** Lee el texto generado para tu nivel. Puedes cambiar el **tamaño de letra** "
                "(16 px a 26 px) según tu comodidad visual y activar el **🧠 Modo Estudio IA** para escuchar la pronunciación y ver el significado de cada palabra.\n"
                "2. **📝 Quiz de Comprensión:** Al terminar de leer, responde las preguntas de opción múltiple y pulsa **Calificar Quiz** para registrar tu puntaje.\n"
                "3. **🎬 2. Viewing & Listening (25 %):** Observa el video contextual relacionado con el tema de tu lección para entrenar tu oído con inglés real.\n"
                "4. **🎙️ 3. Alphabetical & Speaking (25 %):** Graba tu voz o video leyendo el texto en voz alta. Nuestra IA evaluará tu pronunciación, entonación y fluidez.\n"
                "5. **✍️ 4. Writing Skill APA 7 (20 %):** Redacta un resumen en inglés de **120 a 125 palabras** sobre el video y agrega su referencia bibliográfica en formato **APA 7.ª Edición**.\n"
                "6. **📊 Tu Boletín y Certificado:** Todas tus calificaciones y tu **Categoría Estudiantil (Bronce, Plata u Oro)** se actualizan automáticamente en tu Boletín Informativo."
            )

            st.divider()
            st.markdown("##### 📲 Instala la App Oficial CEI en tu Celular (iOS y Android)")
            col_pwa1, col_pwa2 = st.columns(2)
            with col_pwa1:
                with st.container(border=True):
                    st.markdown("**🍎 En iPhone / iPad (Safari):**")
                    st.markdown(
                        "1. Abre el enlace de la plataforma en **Safari**.\n"
                        "2. Toca el botón **Compartir** (cuadro con flecha hacia arriba ⬆️).\n"
                        "3. Selecciona **Agregar a inicio** (*Add to Home Screen*).\n"
                        "4. Pulsa **Agregar** arriba a la derecha. ¡Listo!"
                    )
            with col_pwa2:
                with st.container(border=True):
                    st.markdown("**🤖 En Android (Google Chrome):**")
                    st.markdown(
                        "1. Abre el enlace de la plataforma en **Chrome**.\n"
                        "2. Toca el menú de **tres puntos (⋮)** arriba a la derecha.\n"
                        "3. Selecciona **Instalar aplicación** o **Agregar a la pantalla principal**.\n"
                        "4. Confirma pulsando **Instalar**. ¡Listo!"
                    )

        elif opcion_guia == "📅 Plan del Curso (9 Meses)":
            st.markdown(f"#### 📅 Plan Curricular de 9 Periodos (36 Semanas) — Nivel CEFR {niv_code}")
            st.info(
                f"El programa completo del nivel **{niv_code}** consta de **9 periodos mensuales de 4 semanas (36 semanas en total)** "
                f"y abarca **{n_crit} criterios gramaticales fundamentales** (1 criterio eje por mes).\n\n"
                "El número total de clases requeridas a lo largo de los 9 meses depende de la **Categoría Estudiantil** que desees alcanzar:"
            )

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("🥉 Meta Categoría Bronce", f"{n_crit * 1} clases en 9 meses", "1 clase por mes")
            with col_p2:
                st.metric("🥈 Meta Categoría Plata", f"{n_crit * 2} clases en 9 meses", "2 clases por mes")
            with col_p3:
                st.metric("🥇 Meta Categoría Oro", f"{n_crit * 3} clases en 9 meses", "3 clases por mes")

            filas_plan = []
            for idx_m, crit_nom in enumerate(datos_cat["criterios"], start=1):
                filas_plan.append({
                    "Periodo (Mes)": f"Mes {idx_m} (Semanas {(idx_m - 1) * 4 + 1}–{idx_m * 4})",
                    f"Criterio Gramatical ({niv_code})": crit_nom,
                    "🥉 Bronce (1x)": "1 clase / mes",
                    "🥈 Plata (2x)": "2 clases / mes",
                    "🥇 Oro (3x)": "3 clases / mes"
                })
            st.dataframe(pd.DataFrame(filas_plan), width="stretch", hide_index=True)

        elif opcion_guia == "🏅 Categoría Estudiantil (Bronce, Plata y Oro)":
            st.markdown("#### 🏅 Sistema de Categorías Estudiantiles CEI")
            st.success(
                f"Tu insignia actual calculada automáticamente es: **{datos_cat['categoria_label']}** "
                f"(`{datos_cat['total_lecciones']}` clases/lecciones completadas en el nivel **{niv_code}**)."
            )
            c_cat1, c_cat2, c_cat3 = st.columns(3)
            with c_cat1:
                with st.container(border=True):
                    st.markdown("### 🥉 Categoría Bronce")
                    st.markdown("**Requisito:** **1 clase por mes** acreditada en cada periodo del curso.")
                    st.caption(f"Total en nivel {niv_code}: **{n_crit} clases** en los 9 periodos.")
            with c_cat2:
                with st.container(border=True):
                    st.markdown("### 🥈 Categoría Plata")
                    st.markdown("**Requisito:** **2 clases por mes** acreditadas en cada periodo del curso.")
                    st.caption(f"Total en nivel {niv_code}: **{n_crit * 2} clases** en los 9 periodos.")
            with c_cat3:
                with st.container(border=True):
                    st.markdown("### 🥇 Categoría Oro")
                    st.markdown("**Requisito:** **3 clases por mes** acreditadas en cada periodo del curso.")
                    st.caption(f"Total en nivel {niv_code}: **{n_crit * 3} clases** en los 9 periodos.")

            st.info(
                "✨ **Asignación Automática:** No necesitas solicitar tu categoría. Conforme avanzas y completas tus clases mensuales en cada periodo, "
                "la plataforma actualiza tu insignia automáticamente y la imprime tanto en tu **Boletín Informativo** como en tu **Certificado Oficial**."
            )


# ==============================================================================
# MOTOR DE GAMIFICACIÓN SOCIAL: RACHAS SEMANALES, INSIGNIAS Y WHATSAPP
# ==============================================================================
def calcular_gamificacion_estudiante(student_user: str, nivel_cefr: str = "B1") -> dict:
    """Calcula racha semanal consecutiva, insignias obtenidas por Folio y estado de actividad."""
    u_clean = str(student_user or "").strip().lower()
    hoy_local = datetime.now(ZoneInfo("America/Hermosillo")).date()
    iso_hoy = hoy_local.isocalendar()
    semana_actual_key = (iso_hoy[0], iso_hoy[1])

    folios_u = []
    try:
        todos_f = load_lessons_history_pg() or []
        folios_u = [
            r for r in todos_f
            if str(r.get("Usuario", "")).strip().lower() == u_clean
            and str(r.get("Folio") or "").strip()
        ]
    except Exception:
        folios_u = []

    semanas_activas = set()
    folios_completos = 0
    speaking_elite = 0
    apa_scholar = 0
    quiz_perfecto = 0

    for f in folios_u:
        # 1. Extraer fecha para racha semanal
        f_str = str(f.get("Fecha") or f.get("Created_At") or "").strip()[:10]
        try:
            d_obj = datetime.strptime(f_str, "%Y-%m-%d").date()
            iso_d = d_obj.isocalendar()
            semanas_activas.add((iso_d[0], iso_d[1]))
        except Exception:
            pass

        # 2. Evaluar logros por Folio
        try:
            q_score = float(f.get("Quiz_Score") or f.get("Calificacion_Quiz") or 0)
        except Exception:
            q_score = 0.0
        try:
            s_score = float(f.get("Speaking_Score") or f.get("Calificacion_Speaking") or 0)
        except Exception:
            s_score = 0.0
        try:
            w_score = float(f.get("Writing_Score") or f.get("Calificacion_Writing") or 0)
        except Exception:
            w_score = 0.0

        if q_score >= 95:
            quiz_perfecto += 1
        if s_score >= 90:
            speaking_elite += 1
        if w_score >= 90:
            apa_scholar += 1
        if q_score > 0 and s_score > 0 and w_score > 0:
            folios_completos += 1

    # 3. Calcular racha semanal consecutiva hacia atrás desde esta semana o la pasada
    racha_semanas = 0
    cursor_fecha = hoy_local
    iso_cursor = cursor_fecha.isocalendar()
    if (iso_cursor[0], iso_cursor[1]) not in semanas_activas:
        cursor_fecha = hoy_local - timedelta(days=7)

    while True:
        iso_c = cursor_fecha.isocalendar()
        if (iso_c[0], iso_c[1]) in semanas_activas:
            racha_semanas += 1
            cursor_fecha = cursor_fecha - timedelta(days=7)
        else:
            break

    activo_esta_semana = semana_actual_key in semanas_activas

    insignias = []
    if len(folios_u) >= 1:
        insignias.append("🚀 Primer Folio Creado")
    if folios_completos >= 1:
        insignias.append(f"🎯 Folio 360° Completo ({folios_completos})")
    if quiz_perfecto >= 1:
        insignias.append(f"🧠 Maestro Reading ({quiz_perfecto})")
    if speaking_elite >= 1:
        insignias.append(f"🎙️ Speaking Elite ({speaking_elite})")
    if apa_scholar >= 1:
        insignias.append(f"✍️ APA 7 Scholar ({apa_scholar})")
    if racha_semanas >= 4:
        insignias.append(f"🔥 Imparable {racha_semanas} Semanas")

    cat_info = calcular_categoria_automatica_estudiante(student_user, nivel_cefr)

    return {
        "racha_semanas": racha_semanas,
        "activo_esta_semana": activo_esta_semana,
        "total_folios": len(folios_u),
        "folios_completos": folios_completos,
        "insignias": insignias,
        "categoria_label": cat_info["categoria_label"],
        "categoria_corto": cat_info["categoria_corto"]
    }


def build_whatsapp_motivacion_racha(student_user: str, gam_data: dict, telefono_alumno: str = "") -> str:
    """Construye el enlace de WhatsApp con mensaje motivacional personalizado de racha e insignias."""
    racha = int(gam_data.get("racha_semanas") or 0)
    cat_lbl = gam_data.get("categoria_label") or "🥉 Categoría Bronce"
    if gam_data.get("activo_esta_semana"):
        msg = (
            f"¡Hola {student_user}! 🔥 Te saludamos de Career English Institute (CEI) 🎓.\n\n"
            f"¡Felicidades por mantener tu racha activa de *{racha} semana(s)* consecutiva(s) y tu *{cat_lbl}*! "
            f"Sigue practicando tus 4 habilidades en la plataforma para alcanzar tu siguiente insignia. ¡Excelente trabajo!"
        )
    else:
        msg = (
            f"¡Hola {student_user}! 👋 Te saludamos de Career English Institute (CEI) 🎓.\n\n"
            f"Esta semana aún no registras tu lección en la plataforma. ¡No pierdas el ritmo hacia tu *{cat_lbl}*! "
            f"Ingresa hoy mismo, genera un nuevo Folio y mantén encendido tu progreso en inglés. 🚀"
        )
    tel_clean = _format_wa_phone(telefono_alumno) if "_format_wa_phone" in globals() else "".join(ch for ch in str(telefono_alumno or "") if ch.isdigit())
    if tel_clean:
        return f"https://wa.me{tel_clean}?text={urllib.parse.quote(msg)}"
    return f"https://wa.me?text={urllib.parse.quote(msg)}"


def get_student_inscription_url_pg() -> str:
    """Obtiene desde PostgreSQL el enlace oficial del formulario de inscripción de estudiantes."""
    fallback_url = str(st.secrets.get("STUDENT_INSCRIPTION_URL", DEFAULT_STUDENT_INSCRIPTION_URL)).strip().rstrip("/")
    conn = _open_legal_pg_conn()
    if not conn:
        return fallback_url
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
    return fallback_url


def save_student_inscription_url_pg(nueva_url: str, autor: str) -> tuple[bool, str]:
    """Guarda en PostgreSQL la URL del formulario de inscripción de alumnos editada por Owner/Admin."""
    url_clean = str(nueva_url or "").strip().rstrip("/")
    if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
        return False, "⚠️ La URL debe comenzar con https:// o http://"
    conn = _open_legal_pg_conn()
    if not conn:
        return False, "No hay conexión activa con Supabase PostgreSQL."
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
                cur.execute("""
                    INSERT INTO cei_configuracion_legal (clave, contenido, updated_by, updated_at)
                    VALUES ('url_inscripcion_estudiantes', %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (clave) DO UPDATE SET
                        contenido = EXCLUDED.contenido,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = CURRENT_TIMESTAMP;
                """, (url_clean, autor))
        return True, f"✅ Enlace oficial de inscripción actualizado a: `{url_clean}`"
    except Exception as e:
        return False, f"Error al guardar enlace: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _obtener_id_oficial_afiliado(usuario_o_id: str) -> tuple[str, str]:
    """Busca el affiliate_id oficial (ej. AFIL-CEI-2026-1234) y nombre completo en affiliate_partners."""
    val = str(usuario_o_id or "").strip()
    if not val:
        return "", ""
    conn = _open_legal_pg_conn()
    if not conn:
        return val, val
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(NULLIF(TRIM(affiliate_id), ''), usuario_login),
                       COALESCE(NULLIF(TRIM(nombre || ' ' || apellido_paterno), ''), usuario_login)
                FROM affiliate_partners
                WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                   OR LOWER(TRIM(affiliate_id)) = LOWER(TRIM(%s))
                LIMIT 1;
            """, (val, val))
            row = cur.fetchone()
            if row:
                return str(row[0]).strip(), str(row[1]).strip()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return val, val


def _render_qr_inscripcion_alumnos_box(afiliado_ref: str = "", key_prefix: str = "qr_ins"):
    """Muestra el QR de Inscripción de Alumnos ligado por defecto al ID oficial del Socio Afiliado."""
    url_ins_secret = str(st.secrets.get("STUDENT_REG_URL", "")).strip().rstrip("/")
    url_ins_db = str(get_student_inscription_url_pg() or "").strip().rstrip("/")
    if url_ins_secret:
        url_ins_base = url_ins_secret
    elif url_ins_db and "streamlit.app" in url_ins_db and url_ins_db != "https://streamlit.app":
        url_ins_base = url_ins_db
    else:
        url_ins_base = "https://streamlit.app"

    ref_raw = str(afiliado_ref or "").strip()
    aff_id_oficial, aff_nombre_completo = _obtener_id_oficial_afiliado(ref_raw) if ref_raw else ("", "")

    sep_q = "&" if "?" in url_ins_base else "?"
    url_qr_final = f"{url_ins_base}{sep_q}ref_aff={urllib.parse.quote(aff_id_oficial)}" if aff_id_oficial else url_ins_base


    buf_qr = io.BytesIO()
    qrcode.make(url_qr_final).save(buf_qr, format="PNG")
    qr_bytes = buf_qr.getvalue()
    zoom_state_key = f"{key_prefix}_zoom_fullscreen"

    if st.session_state.get(zoom_state_key, False):
        st.markdown(
            "<div style='text-align:center; padding-top:10px;'>"
            "<h2>📲 Escanea para Inscribirte en Career English Institute (CEI)</h2>"
            "</div>",
            unsafe_allow_html=True
        )
        _, col_ctr, _ = st.columns([1.0, 1.4, 1.0])
        with col_ctr:
            st.image(qr_bytes, width=420)
            if aff_id_oficial:
                st.info(
                    f"🤝 **Socio Afiliado Anfitrión:** {aff_nombre_completo}\n\n"
                    f"🆔 **ID Oficial Ligado al QR:** `{aff_id_oficial}`\n\n"
                    f"🔗 `{url_qr_final}`"
                )
            else:
                st.info(f"🏛️ **Inscripción Directa CEI (Agua Prieta, Sonora)**\n\n🔗 `{url_qr_final}`")
            if st.button("✖️ CERRAR QR", type="primary", width="stretch", key=f"{key_prefix}_btn_close_fs"):
                st.session_state[zoom_state_key] = False
                st.rerun()
        st.stop()

    with st.container(border=True):
        c_q1, c_q2 = st.columns([1.1, 2.4])
        with c_q1:
            qr_b64 = base64.b64encode(qr_bytes).decode("ascii")
            if st.button("🖥️ Ampliar QR", key=f"{key_prefix}_btn_trigger_dbl", width="stretch"):
                st.session_state[zoom_state_key] = True
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
            st.markdown("#### 📲 Código QR Oficial de Inscripción de Alumnos")
            if aff_id_oficial:
                st.success(f"🆔 **ID Oficial del Socio Afiliado Ligado:** `{aff_id_oficial}` ({aff_nombre_completo})")
            st.caption(
                "Al escanear este QR, el formulario de inscripción mostrará automáticamente el **ID del Socio Afiliado** "
                "sin que el estudiante tenga que escribir nada."
            )
            st.code(url_qr_final, language=None)
            b1, b2 = st.columns(2)
            with b1:
                sufijo_archivo = aff_id_oficial.replace(" ", "_") if aff_id_oficial else "Directo_CEI"
                st.download_button(
                    "⬇️ Descargar QR Inscripción (PNG)",
                    data=qr_bytes,
                    file_name=f"QR_Inscripcion_CEI_{sufijo_archivo}.png",
                    mime="image/png",
                    type="primary",
                    width="stretch",
                    key=f"{key_prefix}_btn_dl"
                )
            with b2:
                if st.button("🖥️ Proyectar QR en Centro", type="secondary", width="stretch", key=f"{key_prefix}_btn_open_fs"):
                    st.session_state[zoom_state_key] = True
                    st.rerun()

def get_cei_qr_link(tipo_qr: str, ref_code: str = "", campus_id: str = "") -> str:
    """
    Devuelve el enlace oficial exacto para cada uno de los Códigos QR de CEI:
      1. 'app'        -> https://github.io
      2. 'app_socio'  -> https://github.iosocio_app.html
      3. 'estudiante' -> https://inscripcioncei.streamlit.app
      4. 'socio'      -> https://ceisociosafiliados.streamlit.app
    """
    t = str(tipo_qr or "").strip().lower()

    if t in ["app_socio", "socio_app", "install_socio"]:
        raw = str(st.secrets.get("AFFILIATE_APP_INSTALL_URL", "")).strip()
        base = raw if "drzumaya.github.io" in raw else "https://github.iosocio_app.html"
    elif t in ["app", "descarga", "install"]:
        raw = str(st.secrets.get("APP_INSTALL_QR_URL", "")).strip()
        base = raw if "drzumaya.github.io" in raw else "https://github.io"
    elif t in ["socio", "afiliado", "partner"]:
        raw = str(st.secrets.get("AFFILIATE_REG_URL", "")).strip()
        base = raw if "ceisociosafiliados.streamlit.app" in raw else "https://ceisociosafiliados.streamlit.app"
    else:
        raw = str(st.secrets.get("STUDENT_REG_URL", "")).strip()
        base = raw if "inscripcioncei.streamlit.app" in raw else "https://inscripcioncei.streamlit.app"

    extra_params = []
    if ref_code:
        extra_params.append(f"ref={urllib.parse.quote(str(ref_code).strip())}")
    if campus_id:
        extra_params.append(f"campus={urllib.parse.quote(str(campus_id).strip())}")

    if not extra_params:
        return base

    sep = "&" if "?" in base else "?"
    return f"{base}{sep}{'&'.join(extra_params)}"



def _render_qr_descarga_app_box(key_prefix: str = "qr_app_dl"):
    """Muestra y permite proyectar/descargar el Código QR exclusivo para instalar la App Oficial CEI."""
    base_url = str(
        st.secrets.get("PUBLIC_APP_URL", "https://myceigrammarly.streamlit.app")
    ).strip().rstrip("/")
    url_install_app = str(
        st.secrets.get("APP_INSTALL_QR_URL") or f"{base_url}/?install=1"
    ).strip()

    buf_qa = io.BytesIO()
    qrcode.make(url_install_app).save(buf_qa, format="PNG")
    qa_bytes = buf_qa.getvalue()
    qa_b64 = base64.b64encode(qa_bytes).decode("utf-8")

    with st.container(border=True):
        c_a1, c_a2 = st.columns([2.4, 1.1])
        with c_a1:
            st.markdown("##### 📲 QR Oficial de Descarga e Instalación de la App CEI")
            st.caption(
                "Comparte o proyecta este código QR para que estudiantes, docentes y socios afiliados instalen la App CEI "
                "en su celular o Mac con su escudo oficial preconfigurado."
            )
            st.code(url_install_app, language="text")
            st.download_button(
                "⬇️ Descargar QR de la App (PNG)",
                data=qa_bytes,
                file_name="QR_Instalar_App_CEI.png",
                mime="image/png",
                key=f"dl_{key_prefix}"
            )
        with c_a2:
            st.iframe(
                f"""
                <div style="text-align:center; font-family:-apple-system, BlinkMacSystemFont, sans-serif;">
                    <img id="img_{key_prefix}" src="data:image/png;base64,{qa_b64}"
                         title="Doble clic para proyectar en pantalla grande"
                         ondblclick="expandirQRBoxCEI_{key_prefix}()"
                         style="width:130px;height:130px;border-radius:10px;border:2px solid #0b2545;padding:4px;background:white;cursor:zoom-in;" />
                    <div style="margin-top:6px;">
                        <button onclick="expandirQRBoxCEI_{key_prefix}()" style="
                            background:#0b2545;color:white;border:none;border-radius:6px;
                            padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer;
                        ">🔍 Expandir QR</button>
                    </div>
                </div>
                <script>
                function expandirQRBoxCEI_{key_prefix}() {{
                    const pDoc = window.parent.document;
                    const prev = pDoc.getElementById('modal_qr_box_{key_prefix}');
                    if (prev) prev.remove();
                    const m = pDoc.createElement('div');
                    m.id = 'modal_qr_box_{key_prefix}';
                    m.style.cssText = 'position:fixed;inset:0;background:rgba(11,37,69,0.95);z-index:999999;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;font-family:-apple-system,BlinkMacSystemFont,sans-serif;';
                    m.innerHTML = `
                        <img src="data:image/png;base64,{qa_b64}" style="width:340px;height:340px;border-radius:16px;background:white;padding:14px;box-shadow:0 12px 36px rgba(0,0,0,0.45);" />
                        <p style="color:white;font-size:19px;margin-top:14px;font-weight:700;">📲 Escanea para Instalar la App Oficial CEI</p>
                        <button style="margin-top:10px;background:#ef4444;color:white;border:none;border-radius:8px;padding:8px 18px;font-size:13px;font-weight:700;cursor:pointer;">✖️ Cerrar Proyección</button>
                    `;
                    m.onclick = () => m.remove();
                    pDoc.body.appendChild(m);
                }}
                </script>
                """,
                height=175
            )

def render_header_identidad_y_qr_app(usuario_login: str, nombre_completo: str, rol_usuario: str, is_owner: bool = False):
    """Renderiza el visor del usuario activo y un QR de descarga ocultable y expansible (doble clic o botón)."""
    puede_ver_qr_hdr = is_owner or can("Mostrar_QR_App_Header")
    nom_mostrar = str(nombre_completo or usuario_login or "Usuario").strip()
    rol_mostrar = "Propietario / Owner" if is_owner else str(rol_usuario or "Usuario").strip()

    with st.container(border=True):
        if puede_ver_qr_hdr:
            c_id, c_tog = st.columns([3.0, 1.2])
        else:
            c_id = st.container()
            c_tog = None

        with c_id:
            st.markdown(
                f"### 🎓 CAREER ENGLISH INSTITUTE — Plataforma Oficial\n"
                f"👤 **Sesión Activa:** **{nom_mostrar}** (`{usuario_login}`)  •  "
                f"🏷️ **Tipo de Usuario:** **{rol_mostrar}**"
            )

        mostrar_qr_ahora = False
        if puede_ver_qr_hdr and c_tog is not None:
            with c_tog:
                st.write("")
                mostrar_qr_ahora = st.toggle(
                    "📲 QR App",
                    value=False,
                    key="tgl_header_qr_app_visible",
                    help="Muestra u oculta el código QR para instalar la App Oficial CEI"
                )

        if puede_ver_qr_hdr and mostrar_qr_ahora:
            st.divider()
            base_url = str(
                st.secrets.get("PUBLIC_APP_URL", "https://myceigrammarly.streamlit.app")
            ).strip().rstrip("/")
            url_install_app = str(
                st.secrets.get("APP_INSTALL_QR_URL") or f"{base_url}/?install=1"
            ).strip()
            buf_qh = io.BytesIO()
            qrcode.make(url_install_app).save(buf_qh, format="PNG")
            qa_bytes = buf_qh.getvalue()
            qh_b64 = base64.b64encode(qa_bytes).decode("utf-8")

            c_q1, c_q2 = st.columns([2.4, 1.2])
            with c_q1:
                st.markdown("##### 📲 QR Oficial de Descarga e Instalación de la App CEI")
                st.caption("Escanea para instalar en iPhone, Android o Mac. Haz doble clic en el QR o pulsa Expandir para proyectar.")
                st.code(url_install_app, language="text")
                st.download_button(
                    "⬇️ Descargar QR App (PNG)",
                    data=qa_bytes,
                    file_name="QR_Instalar_App_CEI.png",
                    mime="image/png",
                    key="btn_dl_hdr_qr_app"
                )
            with c_q2:
                st.iframe(
                    f"""
                    <div style="text-align:center; font-family:-apple-system, BlinkMacSystemFont, sans-serif;">
                        <img src="data:image/png;base64,{qh_b64}"
                             title="Doble clic para proyectar QR de App CEI"
                             ondblclick="expandirQRAppCEI()"
                             style="width:115px;height:115px;border-radius:10px;border:2px solid #0b2545;padding:4px;background:white;cursor:zoom-in;" />
                        <div style="margin-top:6px;">
                            <button onclick="expandirQRAppCEI()" style="
                                background:#0b2545;color:white;border:none;border-radius:7px;
                                padding:5px 12px;font-size:11px;font-weight:600;cursor:pointer;
                            ">🔍 Expandir QR</button>
                        </div>
                    </div>
                    <script>
                    function expandirQRAppCEI() {{
                        const pDoc = window.parent.document;
                        const prev = pDoc.getElementById('modal_qr_app_cei_fs');
                        if (prev) prev.remove();
                        const m = pDoc.createElement('div');
                        m.id = 'modal_qr_app_cei_fs';
                        m.style.cssText = 'position:fixed;inset:0;background:rgba(11,37,69,0.96);z-index:999999;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;font-family:-apple-system,BlinkMacSystemFont,sans-serif;';
                        m.innerHTML = `
                            <img src="data:image/png;base64,{qh_b64}" style="width:350px;height:350px;border-radius:18px;background:white;padding:16px;box-shadow:0 12px 36px rgba(0,0,0,0.45);" />
                            <p style="color:white;font-size:20px;margin-top:16px;font-weight:700;">📲 Escanea para Instalar la App Oficial CEI</p>
                            <button style="margin-top:10px;background:#ef4444;color:white;border:none;border-radius:8px;padding:8px 18px;font-size:13px;font-weight:700;cursor:pointer;">✖️ Cerrar Proyección</button>
                        `;
                        m.onclick = () => m.remove();
                        pDoc.body.appendChild(m);
                    }}
                    </script>
                    """,
                    height=168
                )



# ==============================================================================
# PARTE 13A1-B: SELECTOR DE MÓDULOS DEL PORTAL Y DESPLEGABLE DE FOLIOS
# ==============================================================================
if st.session_state.get("active_stage_5") == "PORTAL":
    tiene_acceso_admin_portal = (
        es_admin_o_staff
        or can("Editar_Permisos")
        or can("Editar_Terminos_Afiliacion")
        or can("Gestionar_Comisiones_Afiliados")
        or can("Gestionar_Compliance_Legal")
    )
    lbl_volver_edu = (
        "🔙 CERRAR Y VOLVER A LA LECCIÓN"
        if bool(str(st.session_state.get("generated_text") or "").strip())
        else "🔙 CERRAR Y VOLVER AL PANEL EDUCATIVO"
    )

    if tiene_acceso_admin_portal or es_socio_afiliado:
        if es_socio_afiliado:
            opciones_p_adm = [
                "🤝 Portal Socio Afiliado",
                "📘 Guía, Plan y Categoría"
            ]
        else:
            opciones_p_adm = [
                "💳 Cobranza Mensual e IVA",
                "📊 Estados Financieros",
                "🧑‍🏫 Plantilla y Portal Docente",
                "🤝 Alta de Socios Afiliados",
                "🤝 Portal Socio Afiliado",
                "👥 Inscripción y Padrón",
                "📚 Ver Lecciones Creadas",
            ]

            if is_owner or can("Gestionar_Compliance_Legal"):
                opciones_p_adm.append("⚖️ Compliance y Vigilancia Legal")
            if is_owner:
                opciones_p_adm.append("🌎 Red de Franquicias")
            if is_owner or can("Editar_Permisos") or can("Gestionar_Usuarios"):
                opciones_p_adm.append("🔐 Gestionar Permisos")
            opciones_p_adm.extend([
                "🏅 Certificados (Timbre y QR)",
                "🏛️ Datos del Instituto",
                "📘 Guía, Plan y Categoría",
                "🔄 Autoactualización de Librerías"
            ])

        idx_def_adm = 3 if (not is_owner and not es_socio_afiliado and can("Editar_Terminos_Afiliacion")) else 0
        col_mod_sel, col_mod_back = st.columns([2.5, 1.3])
        with col_mod_sel:
            sel_adm = st.selectbox(
                "Seleccionar módulo institucional:",
                opciones_p_adm,
                index=idx_def_adm,
                key="sb_stage5_admin_mod"
            )
            if st.session_state.get("active_stage_5") == "PORTAL":
                st.session_state["active_admin_workspace"] = sel_adm
        with col_mod_back:
            st.write("")
            if is_owner or can("Ver_Panel_Educativo"):
                st.button(
                    lbl_volver_edu,
                    type="primary",
                    width="stretch",
                    key="btn_global_close_admin_back_lesson",
                    on_click=_cerrar_panel_y_volver_leccion
                )

        if st.session_state.get("active_admin_workspace") == "📘 Guía, Plan y Categoría":
            render_guia_plan_categoria_view(
                usuario_actual=str(st.session_state.get("current_user") or usuario),
                nivel_cefr_actual=str(st.session_state.get("selected_cefr") or "B1")
            )
            st.stop()
    else:
        opciones_p_est = [
            "💳 Mis Pagos (9 Bloques)",
            "📊 Mis Calificaciones y Boletín",
            "📚 Mis Lecciones y Folios",
            "🎧 Mis Audios y Pronunciación",
            "📘 Guía, Plan y Categoría"
        ]
        col_est_sel, col_est_back = st.columns([2.5, 1.3])
        with col_est_sel:
            sel_est = st.selectbox("Seleccionar herramienta estudiantil:", opciones_p_est, key="sb_stage5_est_mod")
            if st.session_state.get("active_stage_5") == "PORTAL":
                st.session_state["active_student_workspace"] = sel_est
        with col_est_back:
            st.write("")
            if is_owner or can("Ver_Panel_Educativo"):
                st.button(
                    lbl_volver_edu,
                    type="primary",
                    width="stretch",
                    key="btn_global_close_est_back_lesson",
                    on_click=_cerrar_panel_y_volver_leccion
                )

        if st.session_state.get("active_student_workspace") == "📘 Guía, Plan y Categoría":
            render_guia_plan_categoria_view(
                usuario_actual=str(st.session_state.get("current_user") or usuario),
                nivel_cefr_actual=str(st.session_state.get("selected_cefr") or "B1")
            )
            st.stop()


# TARJETA DE GAMIFICACIÓN: RACHA SEMANAL E INSIGNIAS DEL ESTUDIANTE
if st.session_state.get("active_stage_5", "READING") == "READING" and not st.session_state.get("active_admin_workspace"):
    gam_curr = calcular_gamificacion_estudiante(
        student_user=str(st.session_state.get("current_user") or usuario),
        nivel_cefr=str(st.session_state.get("selected_cefr") or "B1")
    )
    with st.container(border=True):
        g1, g2, g3, g4 = st.columns([1.2, 1.3, 2.2, 1.3])
        with g1:
            estado_fuego = "🔥 Activa esta semana" if gam_curr["activo_esta_semana"] else "⏳ Pendiente esta semana"
            st.metric("🔥 Racha Semanal", f"{gam_curr['racha_semanas']} sem.", estado_fuego)
        with g2:
            st.metric("🏅 Categoría Actual", gam_curr["categoria_corto"], f"{gam_curr['total_folios']} Folios")
        with g3:
            st.markdown("**🎖️ Insignias Desbloqueadas:**")
            if gam_curr["insignias"]:
                st.caption("  •  ".join(gam_curr["insignias"]))
            else:
                st.caption("Completa tu primer Folio (Reading, Video, Speaking y Writing) para desbloquear tu primera medalla.")
        with g4:
            st.write("")
            if has_faculty_access or is_owner:
                wa_mot_url = build_whatsapp_motivacion_racha(
                    student_user=str(st.session_state.get("current_user") or usuario),
                    gam_data=gam_curr
                )
                st.link_button("📲 Motivar por WhatsApp", url=wa_mot_url, width="stretch")
            else:
                st.caption("🎯 ¡Completa 1 Folio esta semana para sumar +1 a tu racha!")

folio_input = ""
buscar_folio_btn = False

mostrar_barra_folios = (
    not st.session_state.get("active_admin_workspace")
    and st.session_state.get("active_stage_5", "READING") == "READING"
    and not st.session_state.get("show_lesson_creator", False)
)

if mostrar_barra_folios:
    st.session_state.show_gradebook_panel = False
    st.session_state.show_student_payments_panel = False

    try:
        regs_folios_dd = load_lessons_history_pg() or []
    except Exception:
        regs_folios_dd = []

    # Buscar datos exactos del usuario activo en el padrón (usuario, nombre completo y matrícula)
    u_sesion_act = str(st.session_state.get("current_user") or usuario or "").strip()
    reg_padron_act = next(
        (r for r in (load_padron_records() or [])
         if str(r.get("Usuario") or "").strip().lower() == u_sesion_act.lower()),
        {}
    )
    mat_usuario_act = str(reg_padron_act.get("Matricula") or reg_padron_act.get("ID") or "").strip()
    nom_usuario_act = str(
        reg_padron_act.get("Nombre_Completo")
        or reg_padron_act.get("Nombre")
        or st.session_state.get("current_user_fullname")
        or u_sesion_act
    ).strip()

    ids_personales_estrictos = {
        str(x).strip().lower()
        for x in [u_sesion_act, nom_usuario_act, mat_usuario_act, usuario]
        if str(x or "").strip()
    }

    # Filtrar estrictamente para mostrar solo las lecciones de este usuario (nombre / matrícula)
    regs_folios_dd = [
        r for r in regs_folios_dd
        if str(r.get("Usuario") or "").strip().lower() in ids_personales_estrictos
        or str(r.get("Nombre_Estudiante") or "").strip().lower() in ids_personales_estrictos
        or (mat_usuario_act and str(r.get("Matricula") or "").strip().lower() == mat_usuario_act.lower())
    ]

    # Garantizar que el folio recién generado en sesión aparezca primero
    curr_f_now = str(st.session_state.get("current_folio") or "").strip()
    if curr_f_now and not any(str(r.get("Folio") or "").strip() == curr_f_now for r in regs_folios_dd):
        regs_folios_dd.insert(0, {
            "Folio": curr_f_now,
            "Tema": str(st.session_state.get("current_topic") or "Lección Activa").strip(),
            "Nivel_CEFR": str(st.session_state.get("selected_cefr") or "B1").strip(),
            "Usuario": u_sesion_act,
        })

    opciones_folios_map = {}
    for r_dd in regs_folios_dd:
        f_cod = str(r_dd.get("Folio") or "").strip()
        if not f_cod:
            continue
        tema_dd = str(r_dd.get("Tema") or "Lección CEI").strip()
        if len(tema_dd) > 65:
            tema_dd = tema_dd[:62] + "..."
        cefr_dd = str(r_dd.get("Nivel_CEFR") or "").strip()
        etiqueta_dd = f"{f_cod} — {tema_dd} ({cefr_dd})"
        if etiqueta_dd not in opciones_folios_map:
            opciones_folios_map[etiqueta_dd] = f_cod

    with st.container(border=True):
        if opciones_folios_map:
            lista_lbl_folios = list(opciones_folios_map.keys())
            idx_default_f = 0
            for i_f, lbl_f in enumerate(lista_lbl_folios):
                if opciones_folios_map[lbl_f] == curr_f_now:
                    idx_default_f = i_f
                    break

            col_f1, col_f2, col_f4 = st.columns([2.6, 0.9, 1.9])
            with col_f1:
                sel_folio_lbl = st.selectbox(
                    "📚 Seleccionar Folio de Lección:",
                    lista_lbl_folios,
                    index=idx_default_f,
                    label_visibility="collapsed",
                    key="sb_dropdown_folios_inicio"
                )
                folio_input = opciones_folios_map.get(sel_folio_lbl, "")
            with col_f2:
                buscar_folio_btn = st.button("📂 Abrir", type="primary", width="stretch", key="btn_abrir_folio_dd")
            with col_f4:
                if st.session_state.current_folio and st.session_state.generated_text:
                    st.info(f"📄 `{st.session_state.current_folio}` | `{st.session_state.current_creation_date}`")
                else:
                    st.caption(
                        f"Lecciones de **{nom_usuario_act}**"
                        + (f" (`Mat: {mat_usuario_act}`)" if mat_usuario_act else "")
                        + ". Elige una y pulsa **📂 Abrir**."
                    )
        else:
            st.caption("📭 Aún no tienes lecciones guardadas. Presiona **✨ GENERAR LECCIÓN** arriba para crear la primera.")



# ==============================================================================
# PARTE 13A2: RECUPERACIÓN DE FOLIOS DESDE SUPABASE (POR URL O BÚSQUEDA)
# ==============================================================================
auto_fetch_url_folio = bool(
    st.session_state.current_folio
    and not st.session_state.generated_text
    and not st.session_state.get("url_folio_checked", False)
)

folio_target_load = folio_input.strip() or (
    str(st.session_state.get("current_folio") or "").strip() if auto_fetch_url_folio else ""
)

if (buscar_folio_btn or auto_fetch_url_folio) and folio_target_load:
    if auto_fetch_url_folio:
        st.session_state.url_folio_checked = True

    folio_buscado = folio_target_load.upper()
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
                st.session_state["active_stage_5"] = "READING"
                st.session_state["split_speaking_open"] = False
                st.session_state["split_writing_open"] = False
                st.session_state["show_lesson_creator"] = False

                v_url_f = str(row_f.get("Video_URL") or "").strip()
                if v_url_f:
                    st.session_state["current_lesson_video"] = {
                        "url": v_url_f,
                        "title": str(row_f.get("Video_Title") or "Educational Video"),
                        "channel": str(row_f.get("Video_Channel") or "YouTube"),
                        "duration_sec": int(row_f.get("Video_Duration_Sec") or 240),
                        "duration_min": round(int(row_f.get("Video_Duration_Sec") or 240) / 60.0, 2)
                    }
                else:
                    st.session_state["current_lesson_video"] = None

                st.session_state["video_watched_sec"] = int(row_f.get("Video_Watched_Sec") or 0)
                st.session_state["video_score_100"] = float(row_f.get("Video_Score") or 0.0)
                st.session_state["video_summary_draft"] = str(row_f.get("Summary_Text") or "")
                st.session_state["video_apa7_draft"] = str(row_f.get("APA7_Reference") or "")
                st.session_state["summary_score_100"] = float(row_f.get("Summary_Score") or 0.0)
                st.session_state["summary_eval_result"] = row_f.get("Summary_Eval")

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
                        )[0]
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


# ==============================================================================
# PARTE 14E — SECCIÓN 1A: PORTAL EXCLUSIVO DEL ESTUDIANTE (CABECERA Y MÉTRICAS)
# ==============================================================================
if st.session_state.get("active_student_workspace"):
    vista_est_sel = st.session_state["active_student_workspace"]
    alumno_actual_ws = str(st.session_state.get("current_user") or "").strip()

    if "hide_payment_report_form" not in st.session_state:
        st.session_state["hide_payment_report_form"] = True
    if "pay_report_step" not in st.session_state:
        st.session_state["pay_report_step"] = "form"
    if "payment_report_sent_msg" not in st.session_state:
        st.session_state["payment_report_sent_msg"] = ""

    with st.container(border=True):
        if vista_est_sel == "💳 Mis Pagos (9 Bloques)":
            st.subheader("💳 Mis Pagos Mensuales (9 Bloques de 4 Semanas) y Comprobantes")
            est_sp = evaluar_estado_financiero_alumno(alumno_actual_ws)
            mat_oficial_sp = str(est_sp.get("matricula") or "").strip()
            if not mat_oficial_sp:
                for _rp in load_padron_records():
                    if str(_rp.get("Usuario") or "").strip().lower() == alumno_actual_ws.lower():
                        mat_oficial_sp = str(_rp.get("Matricula") or "").strip()
                        break

            st.info(
                f"🆔 **Matrícula Oficial:** `{mat_oficial_sp or 'SIN-MATRÍCULA'}` *(inclúyela en el concepto de tu transferencia para desbloqueo automático)*\n\n"
                "🎓 **Beneficios de tu Membresía Activa:** Tu pago puntual mantiene habilitada las **24 horas del día** "
                "(incluso durante los recesos vacacionales de clases) la plataforma inteligente para generar lecciones y avanzar en tu aprendizaje, "
                "además de permitirte **descargar tu Boletín Oficial de Calificaciones** en cualquier momento para mantenerte informado de tu avance."
            )

            sp1, sp2, sp3, sp4 = st.columns(4)
            sp1.metric("📝 Inscripción / Inicio", f"{est_sp['fecha_inicio']}", delta=f"Inscrito: {est_sp['fecha_inscripcion']}")
            sp2.metric("📅 Bloque Nivel", f"Bloque {est_sp['bloque_en_nivel']}/9", delta=f"Semana {est_sp['semana_ciclo']}/4")
            sp3.metric("🟡 4ta Sem. Pago", f"{est_sp['sem4_pago_inicio']}", delta=f"Hasta {est_sp['sem4_pago_fin']}")
            sp4.metric(
                "📄 Boletín Calificaciones",
                "✅ Activo" if est_sp["descarga_permitida"] else "🔒 Pausado (Sem. 5+)",
                delta=f"Recargo desde {est_sp['fecha_recargo']}"
            )

            if est_sp.get("en_vacaciones"):
                st.warning(f"🏖️ **Período Vacacional Activo ({est_sp['nombre_vacaciones']}):** Las clases presenciales están en receso, pero tu plataforma IA sigue activa 24/7 y tu calendario de pago continúa normal.")

            form_cerrado = bool(st.session_state.get("hide_payment_report_form", True))
            lbl_btn_reversible = "📤 Informar pago" if form_cerrado else "✖️ Cerrar informe de pago"
            tipo_btn_reversible = "primary" if form_cerrado else "secondary"
            if st.button(lbl_btn_reversible, type=tipo_btn_reversible, width="stretch", key="ws_btn_toggle_pay_form"):
                nuevo_estado_cerrado = not form_cerrado
                st.session_state["hide_payment_report_form"] = nuevo_estado_cerrado
                if not nuevo_estado_cerrado:
                    # Al abrir el formulario, limpiar estados previos para ocultar WhatsApp y confirmación
                    st.session_state["pay_report_step"] = "form"
                    st.session_state["last_wa_owner_url"] = ""
                    st.session_state["last_folio_reportado"] = ""
                st.rerun()

            if st.session_state.get("payment_report_sent_msg"):
                st.success(st.session_state["payment_report_sent_msg"])
# ==============================================================================
# PARTE 14E — SECCIÓN 1B: MÁQUINA DE ESTADOS DE INFORME DE PAGO Y WHATSAPP
# ==============================================================================
            if not st.session_state.get("hide_payment_report_form", True):
                with st.container(border=True):
                    st.markdown("#### 📤 Informar Pago y Subir Comprobante Bancario")
                    bloques_pendientes = [
                        b for b in est_sp.get("bloques_9", [])
                        if "Pagado" not in str(b.get("estatus", ""))
                    ]
                    if not bloques_pendientes:
                        st.success("✅ ¡Felicidades! Todos los bloques de tu nivel están pagados. Tu Boletín de Calificaciones está **ACTIVO**.")
                    else:
                        opciones_bloques_pay = {
                            f"Bloque {b['bloque_num']}/9 (Ciclo #{b['ciclo_global']}) — {b['estatus']} | Ventana 4ta Sem: {b['sem4_inicio']} al {b['sem4_fin']}": b
                            for b in bloques_pendientes
                        }
                        sel_bloque_lbl = st.selectbox(
                            "🎯 Selecciona el Bloque que deseas informar como pagado:",
                            list(opciones_bloques_pay.keys()),
                            key="ws_est_sel_bloque_pago"
                        )
                        b_elegido = opciones_bloques_pay[sel_bloque_lbl]
                        ciclo_elegido_num = int(b_elegido["ciclo_global"])

                        hoy_loc_ui = datetime.now(ZoneInfo("America/Hermosillo")).date()
                        base_ui = float(est_sp["mensualidad_base"])
                        es_venc_ui = hoy_loc_ui >= b_elegido["fecha_recargo"]
                        if es_venc_ui:
                            sub_ui = round(base_ui * 1.05, 2)
                        elif est_sp.get("reglas_incentivo_activas"):
                            sub_ui = round(base_ui * 0.93, 2)
                        else:
                            sub_ui = base_ui
                        monto_ui = round(sub_ui * 1.16, 2) if est_sp.get("aplicar_iva") else sub_ui

                        col_up1, col_up2 = st.columns([1.4, 1.6])
                        with col_up1:
                            st.markdown(
                                f"- **Matrícula Oficial:** `{mat_oficial_sp}`\n"
                                f"- **Bloque seleccionado:** **Bloque {b_elegido['bloque_num']}/9** (Ciclo `#{ciclo_elegido_num}`)\n"
                                f"- **Ventana 4ta semana (sin recargo):** `{b_elegido['sem4_inicio']}` al `{b_elegido['sem4_fin']}`\n"
                                f"- **Activación de recargo (Semana 5):** `{b_elegido['fecha_recargo']}`\n"
                                f"- **Monto total transferido:** **`${monto_ui:,.2f} MXN`**"
                            )
                            metodo_p_est = st.selectbox(
                                "Método de pago utilizado:",
                                ["Transferencia Bancaria (SPEI)", "Depósito en Ventanilla / Practicaja", "Pago en Efectivo en Instituto"],
                                key="ws_est_metodo_pago"
                            )
                            ref_p_est = st.text_input("Número de referencia / rastreo bancario:", placeholder="Ej: SPEI-8492014", key="ws_est_ref_pago")

                        with col_up2:
                            archivo_comp = st.file_uploader(
                                "📎 Adjuntar Comprobante de Pago (Obligatorio — Imagen JPG/PNG o PDF):",
                                type=["jpg", "jpeg", "png", "pdf"],
                                key="ws_est_up_comp"
                            )

                            paso_actual = st.session_state.get("pay_report_step", "form")

                            if paso_actual == "form":
                                if st.button(
                                    f"📤 Informar pago y subir comprobante (Bloque {b_elegido['bloque_num']}/9)",
                                    type="primary",
                                    width="stretch",
                                    key="ws_est_btn_comp"
                                ):
                                    if archivo_comp is None:
                                        st.warning("⚠️ **Comprobante faltante:** Debes adjuntar el archivo de tu comprobante (JPG, PNG o PDF) antes de continuar.")
                                    else:
                                        raw_bytes = archivo_comp.getvalue()
                                        mime_comp = str(archivo_comp.type or "image/jpeg")
                                        if "image" in mime_comp.lower():
                                            try:
                                                raw_bytes = compress_bytes_image(raw_bytes, max_side=1100, quality=78)
                                                mime_comp = "image/jpeg"
                                            except Exception:
                                                pass
                                        b64_comp = base64.b64encode(raw_bytes).decode("ascii")

                                        res_rep = reportar_comprobante_pago_estudiante_pg(
                                            student_user=alumno_actual_ws,
                                            metodo_pago=metodo_p_est,
                                            referencia=ref_p_est,
                                            comprobante_b64=b64_comp,
                                            comprobante_mime=mime_comp,
                                            ciclo_seleccionado=ciclo_elegido_num
                                        )
                                        if res_rep["ok"]:
                                            _, wa_owner_url = build_whatsapp_aviso_pago_owner(
                                                nombre_alumno=f"{alumno_actual_ws} (Matrícula: {mat_oficial_sp})",
                                                usuario_alumno=alumno_actual_ws,
                                                nivel_cefr=res_rep.get("nivel_cefr", est_sp.get("nivel_cefr", "")),
                                                folio_pago=res_rep["folio_pago"],
                                                ciclo_num=res_rep["ciclo_num"],
                                                monto_pagado=res_rep["monto"],
                                                referencia=ref_p_est
                                            )
                                            st.session_state["last_wa_owner_url"] = wa_owner_url
                                            st.session_state["last_folio_reportado"] = res_rep["folio_pago"]
                                            st.session_state["last_bloque_reportado"] = b_elegido["bloque_num"]
                                            st.session_state["last_audit_msg"] = res_rep["msg"]
                                            st.session_state["pay_report_step"] = "wa_pending"
                                            st.rerun()
                                        else:
                                            st.error(res_rep["msg"])

                            elif paso_actual == "wa_pending":
                                st.success(st.session_state.get("last_audit_msg", "✅ Comprobante guardado en base de datos."))
                                st.link_button(
                                    f"📲 Enviar aviso por WhatsApp al Owner / Admin (Folio {st.session_state.get('last_folio_reportado', '')})",
                                    url=st.session_state.get("last_wa_owner_url", "https://wa.me"),
                                    type="primary",
                                    width="stretch"
                                )
                                if st.button(
                                    "✅ Confirmar envío de WhatsApp",
                                    type="secondary",
                                    width="stretch",
                                    key="ws_btn_confirm_wa_step"
                                ):
                                    st.session_state["pay_report_step"] = "confirmed"
                                    st.rerun()

                            elif paso_actual == "confirmed":
                                st.button(
                                    "✅ Confirmación recibida",
                                    disabled=True,
                                    width="stretch",
                                    key="ws_btn_confirmed_badge"
                                )
                                if st.button(
                                    "✖️ Cerrar formulario",
                                    type="primary",
                                    width="stretch",
                                    key="ws_btn_close_after_confirm"
                                ):
                                    fol_env = st.session_state.get("last_folio_reportado", "")
                                    blq_env = st.session_state.get("last_bloque_reportado", "")
                                    st.session_state["payment_report_sent_msg"] = (
                                        f"✅ **Confirmación recibida:** Informe de pago guardado y notificado "
                                        f"(Folio `{fol_env}` — Bloque {blq_env}/9, Matrícula `{mat_oficial_sp}`). "
                                        f"Tu Boletín de Calificaciones está activo."
                                    )
                                    st.session_state["hide_payment_report_form"] = True
                                    st.session_state["pay_report_step"] = "form"
                                    st.session_state["last_wa_owner_url"] = ""
                                    st.rerun()

# ==============================================================================
# PARTE 14E — SECCIÓN 2 DE 3: TABLA 9 BLOQUES Y MIS CALIFICACIONES Y BOLETÍN
# ==============================================================================
            if est_sp.get("bloques_9"):
                st.markdown("#### 🗓️ Calendario Completo del Nivel (9 Bloques de 4 Semanas = 36 Semanas)")
                df_sp9 = pd.DataFrame([
                    {
                        "Bloque": f"Bloque {b['bloque_num']}/9",
                        "Inicio Bloque": str(b["inicio_bloque"]),
                        "Fin Bloque": str(b["fin_bloque"]),
                        "4ta Semana (Pago Sin Recargo)": f"{b['sem4_inicio']} al {b['sem4_fin']}",
                        "Recargo / Sig. Bloque": str(b["fecha_recargo"]),
                        "Actividad / Vacaciones (IA 24/7)": b["vacaciones"],
                        "Estatus": b["estatus"]
                    }
                    for b in est_sp["bloques_9"]
                ])
                st.dataframe(df_sp9, width="stretch", hide_index=True)

        elif vista_est_sel == "📊 Mis Calificaciones y Boletín":
            st.subheader(f"📊 Mis Calificaciones y Boletín Oficial — {alumno_actual_ws}")
            gb_data = fetch_student_gradebook_pg(alumno_actual_ws)
            info_cat_bol = calcular_categoria_automatica_estudiante(alumno_actual_ws, gb_data.get("nivel_cefr", "B1"))
            gb_data["categoria_estudiantil"] = info_cat_bol["categoria_label"]
            gb_data["categoria_corto"] = info_cat_bol["categoria_corto"]

            st.success(
                f"🏅 **Categoría Estudiantil Oficial:** **{info_cat_bol['categoria_label']}**  |  "
                f"📚 **Lecciones Completadas:** `{info_cat_bol['total_lecciones']}` "
                f"(Promedio `{info_cat_bol['promedio_por_criterio']}` lecciones por criterio gramatical en nivel **{info_cat_bol['nivel']}**)"
            )

            lista_topicos_disp = ["Vista General"] + [t["Grammar Topic"] for t in gb_data["topic_summary"]]
            col_f_top, col_f_pdf = st.columns([2.1, 1.4])
            with col_f_top:
                topico_sel_ws = st.selectbox(
                    f"🎯 Filtrar por Grammar Topic (Nivel CEFR {gb_data['nivel_cefr']}):",
                    lista_topicos_disp,
                    key="ws_est_filtro_topico"
                )
            with col_f_pdf:
                st.write("")
                fin_al = evaluar_estado_financiero_alumno(alumno_actual_ws)
                d_ret = int(fin_al.get("dias_retraso", 0))
                if fin_al["descarga_permitida"]:
                    pdf_bol_bytes, timbre_bol = create_official_gradebook_pdf(alumno_actual_ws, gb_data, topico_sel_ws)
                    st.download_button(
                        label=f"📥 Descargar Boletín Timbrado ({timbre_bol['folio_boletin']})",
                        data=pdf_bol_bytes,
                        file_name=f"{timbre_bol['folio_boletin']}_{gb_data['matricula']}_{alumno_actual_ws.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        type="primary",
                        width="stretch",
                        key="ws_est_dl_bol"
                    )
                    st.caption(f"🛡️ Timbrado: `{timbre_bol['folio_boletin']}` | {fin_al['mensaje_estado']}")
                else:
                    st.error(f"🔒 Descarga pausada por atraso de {d_ret} días en Bloque {fin_al['ciclo_a_cobrar']}.")
                    if st.button("💳 Ir a Subir Comprobante", type="primary", width="stretch", key="ws_est_go_pay"):
                        st.session_state["active_student_workspace"] = "💳 Mis Pagos (9 Bloques)"
                        st.rerun()

            if topico_sel_ws == "Vista General":
                prom_v, recs_f, temas_f = gb_data["overall_avg"], gb_data["records"], gb_data["topic_summary"]
            else:
                t_inf = next((t for t in gb_data["topic_summary"] if t["Grammar Topic"] == topico_sel_ws), {})
                prom_v = t_inf.get("Dominio (%)", 0.0)
                recs_f = [r for r in gb_data["records"] if r["Grammar_Topic"] == topico_sel_ws]
                temas_f = [t_inf] if t_inf else []

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🏆 Promedio General", f"{gb_data['overall_avg']}%")
            m2.metric("🎯 Promedio Vista", f"{prom_v}%")
            m3.metric("📝 Escrito / 🎙️ Oral", f"{gb_data['quiz_avg']}% / {gb_data['oral_avg']}%")
            m4.metric("🏅 Categoría / Lecciones", f"{info_cat_bol['categoria_corto']} ({len(recs_f)})")
            if temas_f:
                st.bar_chart(pd.DataFrame(temas_f).set_index("Grammar Topic")[["Dominio (%)"]], height=240)
            if recs_f:
                st.dataframe(pd.DataFrame(recs_f), width="stretch", hide_index=True)

# ==============================================================================
# PARTE 14E — SECCIÓN 3 DE 3 (FINAL): MIS LECCIONES, AUDIOS Y CIERRE FOCUS MODE
# ==============================================================================
        elif vista_est_sel == "📚 Mis Lecciones y Folios":
            c_ml1, c_ml2 = st.columns([2.8, 1.2])
            with c_ml1:
                st.subheader(f"📚 Mis Lecciones y Folios Guardados — {alumno_actual_ws}")
            with c_ml2:
                if st.button("🔄 Actualizar Lista", width="stretch", key="btn_refresh_mis_lecciones_ws"):
                    try:
                        load_lessons_history_pg.clear()
                    except Exception:
                        pass
                    st.rerun()

            ids_est_ws = {
                str(x).strip().lower()
                for x in [
                    alumno_actual_ws,
                    st.session_state.get("current_user"),
                    st.session_state.get("current_user_fullname"),
                    st.session_state.get("nombre_completo"),
                ]
                if str(x or "").strip()
            }

            # Si hay una lección recién generada en memoria, asegurar su persistencia en PostgreSQL
            fol_mem = str(st.session_state.get("current_folio") or "").strip().upper()
            txt_mem = str(st.session_state.get("generated_text") or "").strip()
            if fol_mem and txt_mem:
                try:
                    regs_pre = load_lessons_history_pg() or []
                    ya_en_bd = any(str(r.get("Folio") or "").strip().upper() == fol_mem for r in regs_pre)
                    if not ya_en_bd:
                        save_lesson_to_postgres(
                            folio=fol_mem,
                            usuario_name=str(st.session_state.get("current_user") or alumno_actual_ws).strip(),
                            tema=str(st.session_state.get("current_topic") or st.session_state.get("lesson_topic") or "Lección CEI").strip(),
                            cefr=str(st.session_state.get("selected_cefr") or "B1").strip(),
                            grado=str(st.session_state.get("selected_academic_grade") or "Licenciatura / Universidad").strip(),
                            texto=txt_mem,
                            pdf_link=str(st.session_state.get("current_pdf_link") or "").strip()
                        )
                except Exception as e_sync_l:
                    st.warning(f"⚠️ No se pudo sincronizar el folio activo con Supabase: {e_sync_l}")

            regs_all = load_lessons_history_pg() or []
            mis_lecciones = [
                r for r in regs_all
                if str(r.get("Usuario") or "").strip().lower() in ids_est_ws
            ]

            if not mis_lecciones:
                st.info("Aún no tienes lecciones guardadas. Presiona **✖️ CERRAR** arriba para generar tu primera lección con IA.")
            else:
                for idx_l, row_l in enumerate(mis_lecciones):
                    fol_l = str(row_l.get("Folio") or "S/F").strip()
                    with st.container(border=True):
                        cl1, cl2 = st.columns([2.8, 1.2])
                        with cl1:
                            st.markdown(f"**📘 {row_l.get('Tema', 'Lección CEFR')}** — Folio `{fol_l}`")
                            st.caption(
                                f"Nivel: **{row_l.get('Nivel_CEFR', '')}** | Fecha: {row_l.get('Fecha_de_subida', '')} | "
                                f"Mejor Quiz: `{row_l.get('Mejor_Calificacion_PDF') or 'Pendiente'}`"
                            )
                        with cl2:
                            if st.button("📖 Abrir Lección", type="primary", width="stretch", key=f"ws_open_lec_{fol_l}_{idx_l}"):
                                st.session_state.generated_text = str(row_l.get("Texto", ""))
                                st.session_state.current_folio = fol_l
                                st.session_state.selected_cefr = normalize_cefr(row_l.get("Nivel_CEFR", "B1"))
                                st.session_state.selected_academic_grade = str(row_l.get("Grado_Academico", "Licenciatura / Universidad"))
                                st.session_state.study_mode_active = False
                                st.session_state["active_student_workspace"] = None
                                st.rerun()


        elif vista_est_sel == "🎧 Mis Audios y Pronunciación":
            st.subheader(f"🎧 Mis Audios y Práctica de Pronunciación — {alumno_actual_ws}")
            regs_all_a = load_lessons_history_pg()
            mis_audios = [
                r for r in regs_all_a
                if str(r.get("Usuario") or "").strip().lower() == alumno_actual_ws.lower() and str(r.get("Texto") or "").strip()
            ]
            if not mis_audios:
                st.info("Aún no tienes lecciones con audio generado. Presiona **✖️ CERRAR** arriba para crear una lección.")
            else:
                mapa_aud = {
                    f"{r.get('Folio', 'S/F')} — {r.get('Tema', 'Lección')} ({r.get('Nivel_CEFR', '')})": r
                    for r in mis_audios
                }
                sel_aud_lbl = st.selectbox("Selecciona una lección para escuchar su audio estadounidense (US):", list(mapa_aud.keys()), key="ws_est_sel_audio")
                row_aud = mapa_aud[sel_aud_lbl]
                texto_aud_raw = str(row_aud.get("Texto") or "")
                clean_tts_aud = re.split(r"\bBibliography\b", texto_aud_raw.replace("*", "").replace("#", ""), maxsplit=1)
                mp3_lesson_bytes = _synthesize_word_mp3(clean_tts_aud[:2800], slow_mode=False)
                if mp3_lesson_bytes:
                    st.audio(mp3_lesson_bytes, format="audio/mp3")
                if st.button("🧠 Abrir en Modo Estudio Interactivo (Pronunciación Palabra por Palabra)", type="primary", width="stretch", key="ws_est_go_study"):
                    st.session_state.generated_text = texto_aud_raw
                    st.session_state.current_folio = str(row_aud.get("Folio") or "")
                    st.session_state.selected_cefr = normalize_cefr(row_aud.get("Nivel_CEFR", "B1"))
                    st.session_state.study_mode_active = True
                    st.session_state["active_student_workspace"] = None
                    st.rerun()

    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #777; font-size: 13px; margin-top: 20px;'>"
        "📍 <b>" + str(institute_address) + "</b><br>"
        "© 2026 CAREER ENGLISH INSTITUTE | Author: Jacob Zumaya Prianti"
        "</div>",
        unsafe_allow_html=True
    )
    st.stop()

# ==============================================================================
# PARTE 14-A: HELPERS DE DELEGACIÓN Y CENTRO DE MANDO SPA (CERTIFICADOS 1/2)
# ==============================================================================
CAPACIDADES_DELEGABLES_OWNER = [
    "Ver_Panel_Educativo",
    "Ver_Portal_Docente",
    "Ver_Mis_Estudiantes_Docente",
    "Motivar_Estudiantes_WhatsApp",
    "Asignar_Retroalimentacion_Docente",
    "Ver_Comisiones_Pagos_Docente",
    "Gestionar_Compliance_Legal",
    "Ver_Panel_Admin",
    "Registrar_Usuarios",
    "Gestionar_Usuarios",
    "Editar_Permisos",
    "Editar_Terminos_Afiliacion",
    "Gestionar_Comisiones_Afiliados",
    "Ver_Racha_Referidos_WhatsApp",
    "Mostrar_QR_App_Header",
    "Emitir_Certificados",
    "Gestionar_IVA_Mensualidad",
    "Editar_Fecha_Inicio_Curso"
]


def generar_tablero_franquicias_pg() -> dict:
    """Consolida KPIs académicos, financieros y de retención por cada plantel/franquicia."""
    sedes = list_campuses_pg() or []
    padron_all = load_padron_records() or []
    folios_all = []
    certs_all = []
    try:
        folios_all = load_lessons_history_pg() or []
    except Exception:
        folios_all = []
    try:
        certs_all = load_certificates_pg() or []
    except Exception:
        certs_all = []

    ranking_rows = []
    total_alumnos_red = 0
    total_folios_red = 0
    total_certs_red = 0
    total_ingresos_est_red = 0.0

    for s in sedes:
        cid = str(s.get("campus_id") or "CEI-AP-01").strip().upper()
        alumnos_sede = [
            r for r in padron_all
            if str(r.get("Rol", "")).lower() in ["estudiante", "student", "alumno"]
            and str(r.get("campus_id") or "CEI-AP-01").strip().upper() == cid
        ]
        afiliados_sede = [
            r for r in padron_all
            if str(r.get("Rol", "")).lower() in ["socio afiliado", "afiliado", "affiliate"]
            and str(r.get("campus_id") or "CEI-AP-01").strip().upper() == cid
        ]
        usuarios_sede_set = {str(r.get("Usuario") or "").strip().lower() for r in alumnos_sede}

        folios_sede = [
            f for f in folios_all
            if str(f.get("campus_id") or "").strip().upper() == cid
            or str(f.get("Usuario") or "").strip().lower() in usuarios_sede_set
        ]
        certs_sede = [
            c for c in certs_all
            if str(c.get("campus_id") or "").strip().upper() == cid
            or str(c.get("Nombre_Estudiante") or "").strip().lower() in usuarios_sede_set
        ]

        ingresos_sede = 0.0
        for al in alumnos_sede:
            try:
                est_fin_al = evaluar_estado_financiero_alumno(str(al.get("Usuario") or "").strip())
                if est_fin_al.get("ciclo_pagado"):
                    ingresos_sede += float(est_fin_al.get("monto_a_pagar") or 0.0)
            except Exception:
                pass

        n_al = len(alumnos_sede)
        n_fol = len(folios_sede)
        n_cert = len(certs_sede)
        total_alumnos_red += n_al
        total_folios_red += n_fol
        total_certs_red += n_cert
        total_ingresos_est_red += ingresos_sede

        ranking_rows.append({
            "ID Plantel": cid,
            "Plantel / Franquicia": s.get("nombre_plantel", cid),
            "Ciudad / Sede": s.get("ciudad_estado", ""),
            "Director": s.get("director_usuario") or "Matriz CEI",
            "Alumnos": n_al,
            "Socios Afiliados": len(afiliados_sede),
            "Folios Generados": n_fol,
            "Certificados": n_cert,
            "Ingreso Ciclo Cobrado": f"${ingresos_sede:,.2f} {s.get('moneda', 'MXN')}",
            "Estatus": s.get("estatus", "Activo")
        })

    return {
        "sedes": sedes,
        "total_sedes": len(sedes),
        "total_alumnos_red": total_alumnos_red,
        "total_folios_red": total_folios_red,
        "total_certs_red": total_certs_red,
        "total_ingresos_est_red": total_ingresos_est_red,
        "ranking_rows": ranking_rows
    }


if (is_owner or is_faculty_desktop or es_socio_afiliado) and st.session_state.get("active_admin_workspace"):
    seccion_inst_sel = str(st.session_state["active_admin_workspace"]).strip()

    with st.container(border=True):
        st.markdown(f"### {seccion_inst_sel}")
        st.divider()

        puede_editar_inicio = is_owner or can("Editar_Fecha_Inicio_Curso")
        puede_gestionar_afiliados = is_owner or can("Gestionar_Comisiones_Afiliados")
        puede_gestionar_iva = is_owner or can("Gestionar_IVA_Mensualidad")

 # 14.0A PLANTILLA DOCENTE (TÉRMINOS LEGALES, ALTA Y AUDITORÍA DEL PORTAL DOCENTE CEI)
        if seccion_inst_sel == "🧑‍🏫 Plantilla y Portal Docente":
            puede_editar_terminos_leg = is_owner or can("Editar_Terminos_Afiliacion") or can("Gestionar_Compliance_Legal")
            if not (is_owner or can("Ver_Panel_Admin") or can("Registrar_Usuarios") or puede_editar_terminos_leg):
                st.warning("⛔ Tu perfil actual no tiene acceso a la gestión de Plantilla Docente.")
            else:
                if puede_editar_terminos_leg:
                    with st.expander("📜 Editar Términos, Condiciones y Código de Compliance Docente", expanded=False):
                        from legal_terms_manager import get_institutional_terms_pg, save_institutional_terms_pg
                        t_doc_info = get_institutional_terms_pg("docente")
                        if t_doc_info.get("updated_at"):
                            st.caption(f"Última actualización: `{t_doc_info['updated_at']}` por **{t_doc_info['updated_by']}**")
                        txt_terms_doc_ed = st.text_area(
                            "Marco Legal, Fiscal y Compliance mostrado en registro_docentes.py:",
                            value=t_doc_info["texto"],
                            height=220,
                            key="ta_edit_teacher_terms_admin"
                        )
                        if st.button("💾 Guardar y Publicar Términos Docentes", type="primary", key="btn_save_teacher_terms_admin"):
                            if not txt_terms_doc_ed.strip():
                                st.warning("⚠️ El texto legal docente no puede quedar vacío.")
                            else:
                                ok_td, msg_td = save_institutional_terms_pg("docente", txt_terms_doc_ed, str(st.session_state.current_user or "Owner"))
                                st.success(msg_td) if ok_td else st.error(msg_td)

                tab_doc_reg, tab_doc_audit = st.tabs([
                    "➕ Registrar / Actualizar Docente",
                    "🔍 Auditar Portal y Bóveda Fiscal Docente"
                ])
                with tab_doc_reg:
                    from registro_docentes import render_formulario_registro_docente
                    render_formulario_registro_docente(
                        registrado_por=u_login_hdr,
                        key_prefix="admin_doc_reg",
                        es_registro_externo=False
                    )
                with tab_doc_audit:
                    from portal_docente import render_portal_docente_cei
                    render_portal_docente_cei(
                        usuario_actual=u_login_hdr,
                        rol_actual="Propietario" if is_owner else curr_r_clean,
                        puede_ver_estudiantes=True,
                        puede_motivar_wa=True,
                        puede_retroalimentar=True,
                        puede_ver_comisiones=True,
                        es_admin_o_owner=True,
                        dia_corte_cfdi=25,
                        institute_address=str(institute_address or "Agua Prieta, Sonora, México")
                    )

        # 14.0B CENTRO DE COMPLIANCE, VIGILANCIA LEGAL SEMANAL Y RELOJ SLA
        if seccion_inst_sel == "⚖️ Compliance y Vigilancia Legal":
            from compliance_engine import render_panel_compliance_gerencial
            render_panel_compliance_gerencial(
                usuario_actual=u_login_hdr,
                puede_gestionar=bool(is_owner or can("Gestionar_Compliance_Legal"))
            )


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
                            cat_cert_info = calcular_categoria_automatica_estudiante(nombre_sel, nivel_sel)
                            cat_cert_lbl = cat_cert_info["categoria_label"]
                            cat_cert_corto = cat_cert_info["categoria_corto"]

                            st.info(
                                f"**Titular:** {nombre_sel}\n\n"
                                f"**Matrícula:** `{clave_sel}` | **Nivel CEFR:** {nivel_sel}\n\n"
                                f"**Grado:** {grado_sel}\n\n"
                                f"**Insignia Académica:** **{cat_cert_lbl}** (`{cat_cert_info['total_lecciones']}` lecciones)"
                            )

                        with col_c2:
                            programa_cert = st.text_input(
                                "📚 Programa / Curso Acreditado:",
                                value=f"CEFR {nivel_sel} Academic English Grammar & Applied Discourse — CATEGORÍA {cat_cert_corto}",
                                key=f"cert_prog_input_{clave_sel}_{cat_cert_corto}"
                            )
                            calif_cert = st.text_input(
                                "🏆 Calificación / Resultado Final:",
                                value=f"98.0% — Passed with Academic Distinction ({cat_cert_lbl})",
                                key=f"cert_grade_input_{clave_sel}_{cat_cert_corto}"
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
                                    st.success(f"✅ ¡Certificado timbrado ({cat_cert_lbl}) y guardado en Supabase! Folio: **{folio_c}**")

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

                    # ==========================================================
                    # PARTE 14A: HISTORIAL Y REVOCACIÓN DE CERTIFICADOS
                    # ==========================================================
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
            puede_editar_terminos_est = is_owner or can("Editar_Terminos_Afiliacion") or can("Registrar_Usuarios")
            if not (is_owner or can("Registrar_Usuarios") or can("Gestionar_Usuarios") or puede_editar_terminos_est):
                st.warning("⛔ Tu perfil actual no tiene capacidad habilitada para registrar o modificar usuarios.")
            else:
                if puede_editar_terminos_est:
                    with st.expander("📜 Editar Términos y Condiciones de Inscripción de Estudiantes (Inscripcion_alumnosCEI.py)", expanded=False):
                        st_terms_data = get_student_terms_pg()
                        if st_terms_data.get("updated_at"):
                            st.caption(f"Última actualización: `{st_terms_data['updated_at']}` por **{st_terms_data['updated_by']}**")
                        txt_st_terms_edit = st.text_area(
                            "Texto legal y reglamento académico vigente mostrado en Inscripcion_alumnosCEI.py:",
                            value=st_terms_data["texto"],
                            height=250,
                            key="ta_edit_student_terms_admin"
                        )
                        if st.button("💾 Guardar y Publicar Términos de Estudiantes", type="primary", key="btn_save_student_terms_admin"):
                            if not txt_st_terms_edit.strip():
                                st.warning("⚠️ El texto de Términos y Condiciones no puede quedar vacío.")
                            else:
                                ok_st, msg_st = save_student_terms_pg(txt_st_terms_edit, str(st.session_state.current_user or "Owner"))
                                if ok_st:
                                    st.success(msg_st)
                                else:
                                    st.error(msg_st) 

                with st.expander("📲 Código QR Oficial de Auto-Inscripción de Alumnos (Zoom / WhatsApp)", expanded=False):
                    padron_qr_st = load_padron_records()
                    afiliados_qr_list = ["Inscripción Directa CEI (Sin Afiliado)"] + [
                        str(r.get("Usuario", "")).strip()
                        for r in padron_qr_st
                        if str(r.get("Rol", "")).lower() in ["socio afiliado", "afiliado", "affiliate"]
                    ]
                    sel_ref_qr_admin = st.selectbox(
                        "Vincular QR a Socio Afiliado (para incrustar su ID oficial automáticamente):",
                        afiliados_qr_list,
                        index=0,
                        key="sb_admin_inscripcion_qr_ref"
                    )
                    ref_qr_param = "" if sel_ref_qr_admin.startswith("Inscripción Directa") else sel_ref_qr_admin
                    _render_qr_inscripcion_alumnos_box(
                        afiliado_ref=ref_qr_param,
                        key_prefix="admin_inscripcion_padron"
                    )

                permisos_disponibles = PERMISOS_LISTA if (is_owner or can("Editar_Permisos")) else ["Basico"]
                default_perm_idx = permisos_disponibles.index("Basico") if "Basico" in permisos_disponibles else 0
                hoy_hermosillo = datetime.now(ZoneInfo("America/Hermosillo")).date()

                col_form_reg, col_tabla_reg = st.columns([1.25, 2.0])
                with col_form_reg:
                    st.markdown("#### ➕ Formulario de Inscripción")
                    records_afiliadores = load_padron_records()
                    opciones_afiliadores = {"Sin afiliador (Inscripción directa)": (None, "")}
                    for r_aff in records_afiliadores:
                        if r_aff.get("ID"):
                            etiqueta_aff = f"ID #{r_aff['ID']} — {r_aff['Matricula']} ({r_aff['Usuario']})"
                            opciones_afiliadores[etiqueta_aff] = (int(r_aff["ID"]), str(r_aff["Usuario"]).strip())

                    with st.form("form_registro_estudiante", clear_on_submit=True):
                        reg_usuario = st.text_input("👤 Nombre Completo / Usuario:", placeholder="Ej: Carlos Mendoza")
                        reg_clave = st.text_input("🔑 Clave de Acceso asignada:", placeholder="Ej: CEI-2026-05")
                        reg_whatsapp = st.text_input("📱 Teléfono WhatsApp (10 dígitos o +52):", placeholder="Ej: 6331234567")

                        c_r1, c_r2 = st.columns(2)
                        with c_r1:
                            reg_rol = st.selectbox("Rol:", ROLES_LISTA, index=0)
                        with c_r2:
                            reg_nivel = st.selectbox("Nivel CEFR:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2)

                        c_f1, c_f2 = st.columns(2)
                        with c_f1:
                            reg_fecha_inscripcion = st.date_input("📝 Fecha de Inscripción:", value=hoy_hermosillo)
                        with c_f2:
                            reg_fecha_inicio = st.date_input("🎓 Fecha de Inicio de Clases:", value=hoy_hermosillo)

                        c_m1, c_m2 = st.columns(2)
                        with c_m1:
                            reg_mensualidad = st.number_input("💵 Mensualidad ($ MXN):", min_value=0.0, value=1500.0, step=100.0)
                        with c_m2:
                            reg_recargo = st.number_input("⚠️ Recargo Sem. 5 ($ MXN):", min_value=0.0, value=150.0, step=50.0)

                        reg_grado = st.selectbox("🎓 Nivel Académico:", GRADOS_ACADEMICOS, index=1)
                        reg_permiso = st.selectbox("🛡️ Perfil de Permiso:", permisos_disponibles, index=default_perm_idx)
                        reg_afiliador_label = st.selectbox(
                            "🤝 Socio Afiliado / Recomendado por:",
                            list(opciones_afiliadores.keys()),
                            index=0
                        )
                        reg_afiliador_id, reg_afiliador_user = opciones_afiliadores[reg_afiliador_label]
                        reg_pago_inicial_ok = st.checkbox("✅ Suscripción / Bloque 1 Pagado al inscribir", value=True)

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
                                        actualizar_config_financiera_alumno_pg(
                                            student_user=reg_usuario.strip(),
                                            fecha_inicio_val=reg_fecha_inicio,
                                            mensualidad_val=float(reg_mensualidad),
                                            aplicar_iva_val=False,
                                            afiliado_user=reg_afiliador_user,
                                            pct_comision=10.0 if reg_afiliador_user else 0.0,
                                            fecha_inscripcion_val=reg_fecha_inscripcion,
                                            telefono_whatsapp_val=reg_whatsapp.strip(),
                                            recargo_tardio_val=float(reg_recargo)
                                        )
                                        if reg_pago_inicial_ok and reg_rol.lower() in ["estudiante", "student", "alumno"]:
                                            registrar_pago_mensual_y_comision_pg(
                                                student_user=reg_usuario.strip(),
                                                registrado_por=str(st.session_state.get("current_user", "Admin"))
                                            )
                                        st.success(
                                            f"✅ {reg_usuario.strip()} inscrito con Matrícula **{matricula_nueva}** "
                                            f"(Inscripción: {reg_fecha_inscripcion} | Inicio Clases: {reg_fecha_inicio})."
                                        )
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
# PARTE 14C — PARTE 1 DE 2: GESTIÓN DE PERMISOS POR TIPO DE USUARIO
# ==============================================================================
        # 14.3 PESTAÑA GESTIÓN DE PERMISOS Y MATRIZ GLOBAL RBAC
        if seccion_inst_sel in ["🔐 Gestionar Permisos", "🔐 Gestión de Permisos", "🔐 Matriz Global de Permisos"]:
            if not (is_owner or can("Editar_Permisos") or can("Gestionar_Usuarios")):
                st.warning("⛔ Solo el Owner o un Administrador autorizado puede gestionar los permisos de usuario.")
            else:
                st.markdown("#### 🔐 Gestión Integral de Permisos por Tipo de Usuario y Usuario Individual")

                with st.container(border=True):
                    st.markdown("##### 1️⃣ Configurar Permisos por Tipo de Usuario / Perfil")
                    tipos_usuario_rb = [
                        "Owner (Total)",
                        "Administrador",
                        "Docente",
                        "Socio Afiliado",
                        "Estudiante"
                    ]
                    for k_mat in PERMISSIONS_MATRIX.keys():
                        if k_mat not in tipos_usuario_rb and k_mat.lower() != "total":
                            tipos_usuario_rb.append(k_mat)

                    tipo_sel_perm = st.selectbox(
                        "🎭 Seleccionar Tipo de Usuario:",
                        tipos_usuario_rb,
                        index=1,
                        key="sb_tipo_usuario_permisos_editor"
                    )
                    clave_perfil_bd = "Total" if tipo_sel_perm.startswith("Owner") else tipo_sel_perm
                    caps_base_tipo = dict(PERMISSIONS_MATRIX.get(clave_perfil_bd) or {})

                    todas_capacidades = list(dict.fromkeys(list(CAPABILITY_COLS) + list(CAPACIDADES_DELEGABLES_OWNER)))
                    st.caption(f"Marca o desmarca las casillas para añadir o quitar permisos al tipo **{tipo_sel_perm}**:")

                    cols_tipo = st.columns(3)
                    nuevos_permisos_tipo = {}
                    for i_c, cap_item in enumerate(todas_capacidades):
                        with cols_tipo[i_c % 3]:
                            val_def = True if clave_perfil_bd == "Total" else bool(caps_base_tipo.get(cap_item, False))
                            nuevos_permisos_tipo[cap_item] = st.checkbox(
                                cap_item.replace("_", " "),
                                value=val_def,
                                key=f"chk_tipo_{clave_perfil_bd}_{cap_item}",
                                disabled=(clave_perfil_bd == "Total" and cap_item in ["Ver_Panel_Admin", "Editar_Permisos"])
                            )

                    if st.button("💾 Guardar Permisos del Tipo de Usuario", type="primary", key="btn_save_tipo_usuario_perms"):
                        try:
                            upsert_permission_profile_pg(clave_perfil_bd, nuevos_permisos_tipo)
                            st.success(f"✅ Permisos del tipo **{tipo_sel_perm}** actualizados en Supabase.")
                            st.rerun()
                        except Exception as e_tp:
                            st.error(f"Error al guardar permisos por tipo de usuario: {e_tp}")


# ==============================================================================
# PARTE 14C — PARTE 2 DE 2: DELEGACIÓN POR USUARIO Y MATRIZ RBAC
# ==============================================================================
                padron_perm_users = load_padron_records()
                if is_owner and padron_perm_users:
                    with st.container(border=True):
                        st.markdown("##### 2️⃣ Delegación Individual de Capacidades por Usuario (Exclusivo Owner)")
                        st.caption(
                            "Delega o retira permisos puntuales (como **Editar Términos y Condiciones** o **Editar Permisos**) "
                            "a un usuario específico sin modificar el perfil global de los demás usuarios."
                        )
                        curr_owner_clean = str(st.session_state.get("current_user") or "").strip().lower()
                        lista_u_delegar = [
                            str(r.get("Usuario", "")).strip()
                            for r in padron_perm_users
                            if str(r.get("Usuario", "")).strip()
                            and str(r.get("Usuario", "")).strip().lower() != curr_owner_clean
                            and str(r.get("Permisos", "")).strip().lower() != "total"
                        ]
                        if lista_u_delegar:
                            u_del_sel = st.selectbox(
                                "👤 Seleccionar usuario a delegar capacidades:",
                                lista_u_delegar,
                                key="sb_owner_delegate_user"
                            )
                            caps_actuales_u = get_user_delegated_caps_pg(u_del_sel)
                            cols_del = st.columns(3)
                            nuevas_caps_u = {}
                            for idx_d, cap_nom in enumerate(CAPACIDADES_DELEGABLES_OWNER):
                                with cols_del[idx_d % 3]:
                                    nuevas_caps_u[cap_nom] = st.checkbox(
                                        cap_nom.replace("_", " "),
                                        value=bool(caps_actuales_u.get(cap_nom, False)),
                                        key=f"chk_del_{u_del_sel}_{cap_nom}"
                                    )
                            if st.button("💾 Guardar Delegación Individual", type="primary", key="btn_save_owner_delegation"):
                                ok_d, msg_d = save_user_delegated_caps_pg(
                                    u_del_sel,
                                    nuevas_caps_u,
                                    str(st.session_state.current_user or "Owner")
                                )
                                if ok_d:
                                    st.success(msg_d)
                                    st.rerun()
                                else:
                                    st.error(msg_d)

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

                with st.expander("📊 Ver Tabla Completa de Matriz RBAC Activa", expanded=False):
                    df_mat = pd.DataFrame([
                        {"Perfil_Permiso": k, **{cap: ("SI" if v.get(cap) else "NO") for cap in CAPABILITY_COLS}}
                        for k, v in PERMISSIONS_MATRIX.items()
                    ])
                    st.dataframe(df_mat, width="stretch", hide_index=True)



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

            st.divider()
            _render_qr_descarga_app_box(key_prefix="admin_datos_inst_app_qr")

                           

                                
        # 14.4C PESTAÑA TORRE DE CONTROL UNIFICADA: RED DE FRANQUICIAS Y EXPANSIÓN MULTI-SEDE
        if seccion_inst_sel == "🌎 Red de Franquicias":
            if not is_owner:
                st.warning("⛔ Solo el Propietario Principal (Owner) puede auditar y administrar la Red Global de Franquicias.")
            else:
                st.markdown("#### 🌎 CEI Global Franchise Hub — Torre de Control Multi-Sede")
                st.caption(
                    "Supervisa el crecimiento de la Sede Matriz (Agua Prieta, Sonora) y cada franquicia nacional o internacional, "
                    "da de alta nuevos planteles y genera su QR exclusivo de inscripción."
                )

                hub_data = generar_tablero_franquicias_pg()

                k_f1, k_f2, k_f3, k_f4 = st.columns(4)
                k_f1.metric("🏛️ Planteles Activos", f"{hub_data['total_sedes']} sedes", "Red CEI")
                k_f2.metric("🎓 Matrícula Global", f"{hub_data['total_alumnos_red']} alumnos", "Todas las sedes")
                k_f3.metric("📚 Producción Académica", f"{hub_data['total_folios_red']} Folios", f"{hub_data['total_certs_red']} Certificados")
                k_f4.metric("💰 Recaudación Ciclo Red", f"${hub_data['total_ingresos_est_red']:,.2f}", "Consolidado")

                st.divider()
                st.markdown("##### 🏆 Ranking Comparativo de Planteles y Franquicias")
                if hub_data["ranking_rows"]:
                    st.dataframe(pd.DataFrame(hub_data["ranking_rows"]), width="stretch", hide_index=True)

                with st.expander("➕ Registrar o Editar Plantel / Franquicia (campus_id)", expanded=False):
                    with st.form("form_upsert_campus_cei_hub"):
                        fc1, fc2 = st.columns(2)
                        with fc1:
                            in_cid = st.text_input("🆔 Código de Plantel (`campus_id`):", placeholder="Ej: CEI-HMO-02")
                            in_cnom = st.text_input("🏛️ Nombre Oficial del Plantel:", placeholder="Ej: Career English Institute — Hermosillo")
                            in_cciud = st.text_input("📍 Ciudad y Estado / País:", placeholder="Ej: Hermosillo, Sonora, México")
                            in_cdir = st.text_area("🏢 Dirección Oficial (aparece en Certificados PDF):", height=70)
                        with fc2:
                            in_ctel = st.text_input("📱 Teléfono / WhatsApp del Plantel:", placeholder="+52 ...")
                            in_cmon = st.selectbox("💱 Moneda Local:", ["MXN", "USD", "CAD", "EUR"], index=0)
                            in_civa = st.number_input("🧾 IVA / Impuesto Local (%):", min_value=0.0, max_value=30.0, value=16.0, step=0.5)
                            in_cdir_u = st.text_input("👤 Usuario Director de Sede (opcional):", placeholder="Usuario en padrón")
                            in_cest = st.selectbox("🏷️ Estatus Operativo:", ["Activo", "En Apertura", "Suspendido"])

                        if st.form_submit_button("💾 Guardar Plantel / Franquicia en Red CEI", type="primary", width="stretch"):
                            ok_c, msg_c = upsert_campus_pg(
                                campus_id=in_cid,
                                nombre_plantel=in_cnom,
                                ciudad_estado=in_cciud,
                                direccion_oficial=in_cdir,
                                telefono_contacto=in_ctel,
                                moneda=in_cmon,
                                iva_pct=in_civa,
                                director_usuario=in_cdir_u,
                                estatus=in_cest
                            )
                            if ok_c:
                                st.success(msg_c)
                                st.rerun()
                            else:
                                st.error(msg_c)

                st.divider()
                st.markdown("##### 📲 Kit de Expansión Instantánea: QR Oficial y Sello por Franquicia")
                if hub_data["sedes"]:
                    mapa_hub_sedes = {
                        f"{s['campus_id']} — {s['nombre_plantel']} ({s['ciudad_estado']})": s
                        for s in hub_data["sedes"]
                    }
                    sel_hub_lbl = st.selectbox(
                        "Selecciona una franquicia para generar su QR oficial de inscripción y activar su sede:",
                        list(mapa_hub_sedes.keys()),
                        key="sb_franchise_hub_qr_selector"
                    )
                    sede_hub_obj = mapa_hub_sedes[sel_hub_lbl]
                    cid_hub = sede_hub_obj["campus_id"]

                    c_hq1, c_hq2 = st.columns([2.2, 1.2])
                    with c_hq1:
                        st.info(
                            f"**Plantel:** {sede_hub_obj['nombre_plantel']}\n\n"
                            f"**Código Oficial:** `{cid_hub}`  |  **Ciudad:** {sede_hub_obj['ciudad_estado']}\n\n"
                            f"**Dirección en Certificados:** {sede_hub_obj['direccion_oficial']}\n\n"
                            f"**Moneda / IVA:** `{sede_hub_obj['moneda']}` ({sede_hub_obj['iva_pct']}%)"
                        )
                        if st.button(f"🎯 Operar Sesión bajo Sede {cid_hub}", type="primary", key="btn_activate_hub_campus"):
                            st.session_state["active_campus_id"] = cid_hub
                            st.session_state["active_campus_address"] = sede_hub_obj["direccion_oficial"]
                            st.success(f"✅ Sesión vinculada al plantel **{cid_hub}**.")

                    with c_hq2:
                        base_ins_campus = str(
                            st.secrets.get("STUDENT_REG_URL")
                            or st.secrets.get("PUBLIC_APP_URL")
                            or "https://inscripcioncei.streamlit.app"
                        ).strip().rstrip("/")
                        sep_c = "&" if "?" in base_ins_campus else "?"
                        url_qr_campus = f"{base_ins_campus}{sep_c}campus={urllib.parse.quote(cid_hub)}"
                        buf_qc = io.BytesIO()
                        qrcode.make(url_qr_campus).save(buf_qc, format="PNG")
                        st.image(buf_qc.getvalue(), caption=f"QR Inscripción {cid_hub}", width=150)
                        st.download_button(
                            f"⬇️ Descargar QR {cid_hub}",
                            data=buf_qc.getvalue(),
                            file_name=f"QR_Franquicia_{cid_hub}.png",
                            mime="image/png",
                            width="stretch",
                            key=f"btn_dl_qr_campus_{cid_hub}"
                        )


        # 14.4D PESTAÑA AUDITORÍA ACADÉMICA: VER LECCIONES CREADAS POR USUARIO, MATRÍCULA O NIVEL
        if seccion_inst_sel == "📚 Ver Lecciones Creadas":
            if not (is_owner or has_faculty_access or can("Ver_Panel_Admin")):
                st.warning("⛔ Tu perfil actual no tiene permiso para auditar el historial de lecciones.")
            else:
                st.markdown("#### 📚 Auditoría de Lecciones Creadas y Folios por Usuario")
                st.caption(
                    "Busca cualquier estudiante, docente o usuario registrado por **Nombre, Usuario, Matrícula o Nivel CEFR**, "
                    "consulta todas sus lecciones generadas y ábrelas directamente en el visor de lectura."
                )

                if st.button("🔄 Actualizar Historial y Padrón desde Supabase", key="btn_refresh_folios_admin_tab"):
                    try:
                        load_lessons_history_pg.clear()
                        load_padron_records.clear()
                    except Exception:
                        pass
                    st.rerun()

                padron_aud = load_padron_records() or []
                folios_aud = load_lessons_history_pg() or []

                def _get_ci(d_obj: dict, *keys) -> str:
                    if not isinstance(d_obj, dict):
                        return ""
                    low_map = {str(k).lower(): v for k, v in d_obj.items()}
                    for k in keys:
                        val = low_map.get(str(k).lower())
                        if val is not None and str(val).strip():
                            return str(val).strip()
                    return ""

                c_bus1, c_bus2 = st.columns([2.2, 1.2])
                with c_bus1:
                    q_busq_u = st.text_input(
                        "🔍 Buscar por Nombre, Usuario o Matrícula:",
                        placeholder="Ej: Vicente, CEI-2026-001, Maria...",
                        key="txt_admin_search_lessons_user"
                    ).strip().lower()
                with c_bus2:
                    niveles_filtro = ["Todos los Niveles", "A1", "A2", "B1", "B2", "C1", "C2"]
                    sel_niv_aud = st.selectbox(
                        "🎯 Filtrar por Nivel CEFR:",
                        niveles_filtro,
                        key="sb_admin_search_lessons_cefr"
                    )

                usuarios_filtrados_aud = []
                seen_users_aud = set()

                for r_u in padron_aud:
                    u_log = _get_ci(r_u, "Usuario", "usuario_login", "user")
                    if not u_log or u_log.lower() in seen_users_aud:
                        continue
                    seen_users_aud.add(u_log.lower())

                    nom_c = _get_ci(r_u, "Nombre_Completo", "Nombre", "full_name") or u_log
                    mat_c = _get_ci(r_u, "Matricula", "ID", "id")
                    rol_c = _get_ci(r_u, "Rol", "role") or "Estudiante"
                    niv_raw = _get_ci(r_u, "Nivel", "cefr_level") or "B1"
                    niv_sigla = next((n for n in ["A1", "A2", "B1", "B2", "C1", "C2"] if n in niv_raw.upper()), "B1")

                    if sel_niv_aud != "Todos los Niveles" and niv_sigla != sel_niv_aud:
                        continue
                    if q_busq_u:
                        blob_u = f"{u_log} {nom_c} {mat_c} {rol_c} {niv_sigla}".lower()
                        if q_busq_u not in blob_u:
                            continue

                    usuarios_filtrados_aud.append({
                        "usuario": u_log,
                        "nombre": nom_c,
                        "matricula": mat_c,
                        "rol": rol_c,
                        "nivel": niv_sigla,
                        "label": f"{nom_c} (@{u_log}) • {rol_c} • Nivel {niv_sigla}" + (f" • Mat: {mat_c}" if mat_c else "")
                    })

                opciones_selector_aud = ["🌐 Todos los Usuarios y Lecciones"] + [u["label"] for u in usuarios_filtrados_aud]
                sel_usuario_aud_lbl = st.selectbox(
                    f"👤 Seleccionar Usuario ({len(usuarios_filtrados_aud)} encontrados en padrón):",
                    opciones_selector_aud,
                    key="sb_admin_pick_user_lessons"
                )

                folios_mostrados = []
                if sel_usuario_aud_lbl == "🌐 Todos los Usuarios y Lecciones":
                    for f_item in folios_aud:
                        fu = _get_ci(f_item, "Usuario")
                        ftema = _get_ci(f_item, "Tema")
                        ffolio = _get_ci(f_item, "Folio")
                        fniv_raw = _get_ci(f_item, "Nivel_CEFR") or "B1"
                        fniv_sigla = next((n for n in ["A1", "A2", "B1", "B2", "C1", "C2"] if n in fniv_raw.upper()), "B1")

                        if sel_niv_aud != "Todos los Niveles" and fniv_sigla != sel_niv_aud:
                            continue
                        if q_busq_u:
                            blob_f = f"{fu} {ftema} {ffolio} {fniv_sigla}".lower()
                            if q_busq_u not in blob_f:
                                continue
                        folios_mostrados.append(f_item)
                else:
                    u_obj_sel = next((u for u in usuarios_filtrados_aud if u["label"] == sel_usuario_aud_lbl), None)
                    if u_obj_sel:
                        ids_match = {u_obj_sel["usuario"].lower(), u_obj_sel["nombre"].lower()}
                        folios_mostrados = [
                            f_item for f_item in folios_aud
                            if _get_ci(f_item, "Usuario").lower() in ids_match
                        ]

                st.divider()
                st.markdown(f"##### 📄 Lecciones y Folios Encontrados: `{len(folios_mostrados)}`")

                if not folios_mostrados:
                    st.info("📭 No se encontraron lecciones guardadas para los criterios seleccionados.")
                else:
                    df_aud_folios = pd.DataFrame([
                        {
                            "Folio": _get_ci(f, "Folio"),
                            "Usuario": _get_ci(f, "Usuario"),
                            "Tema": _get_ci(f, "Tema"),
                            "Nivel CEFR": _get_ci(f, "Nivel_CEFR"),
                            "Grado": _get_ci(f, "Grado_Academico"),
                            "Quiz": _get_ci(f, "Mejor_Calificacion_PDF") or "—",
                            "Speaking": f"{float(f.get('Speaking_Score') or 0):.1f}" if float(f.get("Speaking_Score") or -1) >= 0 else "—",
                            "Fecha": _get_ci(f, "Fecha_de_subida")
                        }
                        for f in folios_mostrados
                    ])
                    st.dataframe(df_aud_folios, width="stretch", hide_index=True)

                    mapa_abrir_aud = {
                        f"{_get_ci(f, 'Folio')} — {_get_ci(f, 'Tema')[:55]} ({_get_ci(f, 'Usuario')})": _get_ci(f, "Folio")
                        for f in folios_mostrados if _get_ci(f, "Folio")
                    }
                    c_op1, c_op2 = st.columns([2.8, 1.2])
                    with c_op1:
                        sel_f_open_lbl = st.selectbox(
                            "Seleccionar Folio para abrir en el Panel Educativo:",
                            list(mapa_abrir_aud.keys()),
                            key="sb_admin_open_specific_folio"
                        )
                    with c_op2:
                        st.write("")
                        if st.button("📂 Abrir Lección en Visor", type="primary", width="stretch", key="btn_admin_open_folio_go"):
                            f_go = mapa_abrir_aud[sel_f_open_lbl]
                            st.session_state["current_folio"] = f_go
                            st.session_state["generated_text"] = ""
                            st.session_state["url_folio_checked"] = False
                            st.session_state["active_admin_workspace"] = None
                            st.session_state["active_stage_5"] = "READING"
                            st.rerun()


        # 14.4B PESTAÑA AUTOACTUALIZACIÓN DE LIBRERÍAS (SIN REVISAR CÓDIGO)
        if seccion_inst_sel == "🔄 Autoactualización de Librerías":
            if not is_owner:
                st.warning("⛔ Solo el Propietario / Administrador Principal puede actualizar las librerías del servidor.")
            else:
                import importlib.metadata
                import subprocess
                import sys
                import urllib.request

                st.markdown("#### 🔄 Gestor Automático de Librerías y Dependencias (PyPI / Cloud)")
                st.caption(
                    "Verifica las versiones instaladas en el servidor, comprueba disponibilidad en PyPI y descarga el "
                    "`requirements.txt` sincronizado para actualizar permanentemente en Streamlit Cloud."
                )

                paquetes_cei = [
                    "streamlit", "google-genai", "gtts", "qrcode", "pillow",
                    "fpdf2", "gspread", "google-auth", "pandas", "streamlit-js-eval",
                    "psycopg", "deep-translator", "requests", "pypdfium2", "pydub", "static-ffmpeg"
                ]

                c_upd1, c_upd2 = st.columns([1.2, 2.0])
                with c_upd1:
                    btn_check_pypi = st.button("🔍 Comprobar Actualizaciones", width="stretch", key="btn_check_pypi_updates")
                with c_upd2:
                    btn_run_upd = st.button(
                        "⚡ Autoactualizar Librerías en Entorno",
                        type="primary",
                        width="stretch",
                        key="btn_run_auto_upgrade"
                    )

                if btn_run_upd:
                    with st.spinner("Actualizando librerías en el entorno activo (30-60 segundos)..."):
                        try:
                            res_pip = subprocess.run(
                                [sys.executable, "-m", "pip", "install", "--upgrade", "--user"] + paquetes_cei,
                                capture_output=True, text=True, timeout=90
                            )
                            if res_pip.returncode == 0:
                                st.success("✅ Librerías actualizadas en el entorno. Reinicia la app para aplicar los cambios.")
                            else:
                                st.info(
                                    "ℹ️ El entorno de Streamlit Cloud tiene bloqueada la escritura directa de paquetes (`pip`). "
                                    "Usa el botón inferior para descargar el **`requirements.txt`** actualizado y súbelo a tu repositorio en GitHub."
                                )
                        except Exception as e_pip:
                            st.info(f"ℹ️ Entorno Cloud de solo lectura ({e_pip}). Descarga el `requirements.txt` abajo para actualizar vía GitHub.")

                filas_pkgs = []
                lineas_req = []
                for pkg in paquetes_cei:
                    try:
                        v_inst = importlib.metadata.version(pkg)
                    except Exception:
                        v_inst = "No instalado"

                    v_latest = "— (Pulsa Comprobar)"
                    estado_pkg = "✅ Operativa en servidor"
                    if btn_check_pypi:
                        try:
                            req_p = urllib.request.Request(
                                f"https://pypi.org{pkg}/json",
                                headers={"User-Agent": "CEI-Platform-Updater/1.0"}
                            )
                            with urllib.request.urlopen(req_p, timeout=4) as resp_p:
                                data_p = json.loads(resp_p.read().decode("utf-8"))
                                v_latest = str(data_p.get("info", {}).get("version") or v_inst)
                                if v_inst != "No instalado":
                                    estado_pkg = "✅ Al día" if v_inst == v_latest else f"⬆️ Nueva versión: {v_latest}"
                        except Exception:
                            v_latest = v_inst
                            estado_pkg = "✅ Activa (PyPI restringido en Cloud)"

                    filas_pkgs.append({
                        "Paquete": pkg,
                        "Instalada": v_inst,
                        "Última PyPI": v_latest,
                        "Estado": estado_pkg
                    })
                    lineas_req.append(f"{pkg}>={v_inst}" if v_inst != "No instalado" else pkg)

                st.dataframe(pd.DataFrame(filas_pkgs), width="stretch", hide_index=True)

                req_txt_out = "\n".join(lineas_req) + "\n"
                st.download_button(
                    "📥 Descargar requirements.txt Actualizado para GitHub",
                    data=req_txt_out,
                    file_name="requirements.txt",
                    mime="text/plain",
                    type="primary",
                    width="stretch",
                    key="btn_dl_requirements_updated_cei"
                )


# ==============================================================================
# PARTE 14D1: MÓDULOS FINANCIEROS SPA — COBRANZA MENSUAL, COMPROBANTES Y WHATSAPP
# ==============================================================================
        # 14.5 PESTAÑA COBRANZA MENSUAL E IVA
        if seccion_inst_sel == "💳 Cobranza Mensual e IVA":
            puede_cobranza_v2 = is_owner or can("Gestionar_Pagos_Cobranza")
            if not (is_owner or puede_cobranza_v2 or puede_editar_inicio or puede_gestionar_afiliados or puede_gestionar_iva):
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

                tab_val, tab_vac, tab_ind = st.tabs([
                    "🏦 Comprobantes y Avisos WhatsApp",
                    "🏖️ Vacaciones del Instituto",
                    "👤 Expediente y Tarifa por Alumno"
                ])

                with tab_val:
                    if puede_cobranza_v2:
                        pendientes_comp = listar_comprobantes_pendientes_pg()
                        st.markdown(f"##### 🏦 Comprobantes Bancarios Pendientes de Confirmación ({len(pendientes_comp)})")
                        if not pendientes_comp:
                            st.caption("No hay comprobantes bancarios pendientes de revisión en este momento.")
                        else:
                            for idx_c, comp in enumerate(pendientes_comp):
                                with st.container(border=True):
                                    cc1, cc2, cc3 = st.columns([2.2, 1.4, 1.4])
                                    with cc1:
                                        etq_ia = "🟢 Aprobado Express IA" if comp.get("estatus") == "Aprobado_IA" else "🟡 Pase Provisional 72h"
                                        st.markdown(
                                            f"**{comp['nombre_completo']}** (`{comp['student_user']}`) — **Matrícula: `{comp.get('matricula_alumno', 'SIN-MAT')}`** | Nivel **{comp['nivel_cefr']}**\n\n"
                                            f"Folio: `{comp['folio_pago']}` | **Bloque {comp['ciclo_numero']}** | Monto: **`${float(comp['monto_final']):,.2f} MXN`** | {etq_ia} ({int(comp.get('ai_score') or 0)}%)\n\n"
                                            f"Método: {comp['metodo_pago']} | Ref: `{comp['referencia_comprobante']}` | Reportado: {comp['fecha_reporte']}"
                                        )
                                    with cc2:
                                        b64_doc = str(comp.get("comprobante_b64") or "").strip()
                                        mime_doc = str(comp.get("comprobante_mime") or "image/jpeg").strip()
                                        if b64_doc:
                                            raw_doc = base64.b64decode(b64_doc)
                                            if "pdf" in mime_doc.lower():
                                                st.download_button(
                                                    "📄 Ver Comprobante PDF",
                                                    data=raw_doc,
                                                    file_name=f"{comp['folio_pago']}.pdf",
                                                    mime="application/pdf",
                                                    key=f"dl_comp_pdf_{comp['id']}_{idx_c}"
                                                )
                                            else:
                                                st.image(raw_doc, caption="Comprobante adjunto", width=180)
                                        else:
                                            st.caption("Sin archivo adjunto (solo referencia).")
                                    with cc3:
                                        nota_val = st.text_input(
                                            "Nota de cotejo bancario:",
                                            key=f"nota_bco_{comp['id']}_{idx_c}",
                                            placeholder="Ej: Transferencia verificada en estado de cuenta"
                                        )
                                        if st.button("✅ Confirmar Pago y Activar Boletín", type="primary", width="stretch", key=f"btn_ok_bco_{comp['id']}_{idx_c}"):
                                            res_conf = confirmar_pago_bancario_pg(
                                                student_user=comp["student_user"],
                                                ciclo_numero=int(comp["ciclo_numero"]),
                                                validado_por=str(st.session_state.current_user),
                                                notas_admin=nota_val
                                            )
                                            if res_conf["ok"]:
                                                st.success(res_conf["msg"])
                                                st.rerun()
                                            else:
                                                st.error(res_conf["msg"])

                                        if st.button("❌ Rechazar Comprobante", width="stretch", key=f"btn_rej_bco_{comp['id']}_{idx_c}"):
                                            motivo_final = nota_val.strip() or "Comprobante no legible o movimiento no reflejado en banco."
                                            res_rej = rechazar_comprobante_bancario_pg(
                                                student_user=comp["student_user"],
                                                ciclo_numero=int(comp["ciclo_numero"]),
                                                validado_por=str(st.session_state.current_user),
                                                motivo=motivo_final
                                            )
                                            if res_rej["ok"]:
                                                msg_rej_wa = (
                                                    f"Hola {comp['nombre_completo']}, te saludamos de Career English Institute 🎓. "
                                                    f"Revisamos tu comprobante (Folio {comp['folio_pago']}) del Bloque {comp['ciclo_numero']}, "
                                                    f"pero no pudimos validarlo por el siguiente motivo: {motivo_final}. "
                                                    f"Por favor ingresa a 'Mis Pagos' en la plataforma para subir nuevamente tu comprobante legible y mantener activo tu Boletín de Calificaciones."
                                                )
                                                tel_clean_r = _format_wa_phone(comp.get("telefono_whatsapp", ""))
                                                wa_rej_url = (
                                                    f"https://wa.me{tel_clean_r}?text={urllib.parse.quote(msg_rej_wa)}"
                                                    if tel_clean_r
                                                    else f"https://wa.me?text={urllib.parse.quote(msg_rej_wa)}"
                                                )
                                                st.session_state[f"wa_rej_url_{comp['id']}"] = wa_rej_url
                                                st.warning(res_rej["msg"])
                                                st.rerun()
                                            else:
                                                st.error(res_rej["msg"])

                        st.divider()
                        st.markdown("##### 📲 Radar de Avisos WhatsApp (4ta Semana de Pago y 5ta Semana con Recargo)")
                        padron_radar = load_padron_records()
                        alumnos_radar = [r for r in padron_radar if str(r.get("Rol", "")).lower() in ["estudiante", "student", "alumno"]]
                        avisos_encontrados = 0
                        for r_al in alumnos_radar:
                            u_al = str(r_al.get("Usuario") or "").strip()
                            nom_al = str(r_al.get("Nombre_Completo") or u_al).strip()
                            est_r = evaluar_estado_financiero_alumno(u_al)
                            es_sem4 = (int(est_r.get("semana_ciclo") or 1) == 4 and not est_r.get("ciclo_pagado"))
                            es_mora = (int(est_r.get("dias_retraso") or 0) > 0)
                            if es_sem4 or es_mora:
                                avisos_encontrados += 1
                                _, wa_link_est = build_whatsapp_recordatorio_estudiante(
                                    est_r,
                                    nombre_alumno=nom_al,
                                    telefono_alumno=est_r.get("telefono_whatsapp", "")
                                )
                                etq_badge = "🔴 Semana 5+ (Recargo Activo)" if es_mora else "🟡 4ta Semana (Ventana de Pago)"
                                with st.container(border=True):
                                    rw1, rw2 = st.columns([2.6, 1.2])
                                    with rw1:
                                        st.markdown(
                                            f"**{etq_badge}** — **{nom_al}** (`{u_al}`)  |  "
                                            f"Bloque **{est_r['ciclo_a_cobrar']}**  |  Monto: **${est_r['monto_a_pagar']:,.2f} MXN**"
                                        )
                                        st.caption(
                                            f"Ventana 4ta Sem: {est_r['sem4_pago_inicio']} al {est_r['sem4_pago_fin']}  •  "
                                            f"Recargo desde: {est_r['fecha_recargo']}  •  "
                                            f"Boletín: {'✅ Activo' if est_r['descarga_permitida'] else '🔒 Pausado'}"
                                        )
                                    with rw2:
                                        st.link_button("📲 Enviar Aviso WhatsApp", url=wa_link_est, width="stretch")
                        if avisos_encontrados == 0:
                            st.info("🟢 Todos los estudiantes se encuentran al corriente en semanas 1 a 3.")
                    else:
                        st.info("Tu perfil no tiene habilitado el permiso `Gestionar_Pagos_Cobranza`.")
                with tab_vac:
                    st.markdown("##### 🏖️ Calendario de Vacaciones del Instituto")
                    st.info(
                        "📚 **Política Académica y Tecnológica:** Durante los períodos vacacionales se suspenden las clases presenciales, "
                        "**pero el sistema permanece 100 % activo las 24 horas** para que el estudiante siga generando lecciones y avanzando en su aprendizaje. "
                        "Por ello, los ciclos de pago de 4 semanas continúan de forma ininterrumpida."
                    )
                    cv1, cv2, cv3, cv4 = st.columns([1.8, 1.1, 1.1, 1.0])
                    v_nom = cv1.text_input("Nombre del período:", placeholder="Ej: Receso de Invierno 2026", key="vac_nom_in")
                    v_ini = cv2.date_input("Desde:", key="vac_ini_in")
                    v_fin = cv3.date_input("Hasta:", key="vac_fin_in")
                    if cv4.button("➕ Agregar", type="primary", width="stretch", key="btn_add_vac"):
                        if v_nom.strip() and v_fin >= v_ini:
                            if guardar_vacaciones_instituto_pg(v_nom, v_ini, v_fin):
                                st.success("✅ Período vacacional guardado.")
                                st.rerun()
                    lista_v = load_institute_holidays_pg()
                    for hv in lista_v:
                        vc1, vc2 = st.columns([3.5, 0.8])
                        vc1.markdown(f"🏖️ **{hv['nombre_periodo']}** — Del `{hv['fecha_inicio']}` al `{hv['fecha_fin']}`")
                        if vc2.button("🗑️ Quitar", key=f"del_vac_{hv['id']}"):
                            eliminar_vacaciones_instituto_pg(hv["id"])
                            st.rerun()

                with tab_ind:
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
                            st.markdown("##### ⚙️ Configuración de Inscripción, Inicio y Tarifa")
                            nueva_fecha_ins = st.date_input("📝 Fecha de Inscripción:", value=estado_f["fecha_inscripcion"], disabled=not puede_editar_inicio, key="inp_f_ins")
                            nueva_fecha_ini = st.date_input("🎓 Fecha de Inicio de Clases:", value=estado_f["fecha_inicio"], disabled=not puede_editar_inicio, key="inp_f_ini")
                            nuevo_tel_wa = st.text_input("📱 WhatsApp del Estudiante:", value=estado_f["telefono_whatsapp"], key="inp_tel_wa")
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
                                if actualizar_config_financiera_alumno_pg(
                                    est_objetivo, nueva_fecha_ini, nueva_mensualidad, nuevo_aplicar_iva,
                                    aff_s, nuevo_pct_com, fecha_inscripcion_val=nueva_fecha_ins, telefono_whatsapp_val=nuevo_tel_wa
                                ):
                                    st.success(f"✅ Guardado. Total: ${total_vivo:,.2f} MXN")
                                    st.rerun()

                        with metrics_placeholder:
                            f1, f2, f3, f4 = st.columns(4)
                            f1.metric("📅 Bloque Nivel", f"Bloque {estado_f['bloque_en_nivel']}/9", delta=f"Sem. {estado_f['semana_ciclo']}/4")
                            f2.metric("🟡 4ta Sem. Pago", f"{estado_f['sem4_pago_inicio']}", delta=f"Hasta {estado_f['sem4_pago_fin']}")
                            f3.metric("🧾 Total Ciclo", f"${total_vivo:,.2f}", delta=f"Recargo: {estado_f['fecha_recargo']}")
                            d_ret_m = int(estado_f.get("dias_retraso", 0))
                            f4.metric(
                                "📄 Boletín",
                                "✅ Activo" if estado_f["descarga_permitida"] else "🔒 Bloqueado",
                                delta="Al corriente" if estado_f["descarga_permitida"] else f"{d_ret_m} días retraso"
                            )

                        with col_cfg2:
                            st.markdown("##### 🧾 Registro Oficial de Pago (Owner / Admin) y Aviso WhatsApp")
                            st.info(
                                f"- **Inscripción:** `{nueva_fecha_ins}`  |  **Inicio Clases:** `{nueva_fecha_ini}`\n"
                                f"- **Ventana 4ta Semana (Sin recargo):** `{estado_f['sem4_pago_inicio']}` al `{estado_f['sem4_pago_fin']}`\n"
                                f"- **Inicio Siguiente Bloque / Recargo:** `{estado_f['fecha_recargo']}`\n"
                                f"- **TOTAL A REGISTRAR:** **`${total_vivo:,.2f} MXN`**"
                            )
                            _, wa_est_url = build_whatsapp_recordatorio_estudiante(estado_f, est_objetivo, nuevo_tel_wa)
                            st.link_button("📲 Enviar Recordatorio WhatsApp al Estudiante", url=wa_est_url, width="stretch")

                            if estado_f["ciclo_pagado"]:
                                st.success(f"✅ Bloque {estado_f['ciclo_a_cobrar']} registrado como Pagado.")
                            elif puede_cobranza_v2:
                                if st.button(
                                    f"✅ Registrar Pago Oficial (${total_vivo:,.2f} MXN)",
                                    type="primary",
                                    width="stretch",
                                    key="btn_reg_pay"
                                ):
                                    aff_s = "" if sel_aff_user == "Sin Afiliado" else sel_aff_user
                                    actualizar_config_financiera_alumno_pg(
                                        est_objetivo, nueva_fecha_ini, nueva_mensualidad, nuevo_aplicar_iva,
                                        aff_s, nuevo_pct_com, fecha_inscripcion_val=nueva_fecha_ins, telefono_whatsapp_val=nuevo_tel_wa
                                    )
                                    res_p = registrar_pago_mensual_y_comision_pg(est_objetivo, st.session_state.current_user)
                                    if res_p["ok"]:
                                        st.success(res_p["msg"])
                                        st.rerun()
                                    else:
                                        st.error(res_p["msg"])
                            else:
                                st.warning("🔒 Solo el Owner o un Administrador con permiso **Gestionar_Pagos_Cobranza** puede registrar pagos oficiales.")

                        if estado_f.get("bloques_9"):
                            st.markdown("##### 🗓️ Plan de 9 Bloques de 4 Semanas del Nivel (36 Semanas)")
                            df_b9 = pd.DataFrame([
                                {
                                    "Bloque (4 Sem)": f"Bloque {b['bloque_num']}/9",
                                    "Inicio Bloque": str(b["inicio_bloque"]),
                                    "Fin Bloque": str(b["fin_bloque"]),
                                    "4ta Semana Pago (Sin Recargo)": f"{b['sem4_inicio']} al {b['sem4_fin']}",
                                    "Recargo / Sig. Bloque": str(b["fecha_recargo"]),
                                    "Clases / Vacaciones (IA 24/7)": b["vacaciones"],
                                    "Estatus": b["estatus"]
                                }
                                for b in estado_f["bloques_9"]
                            ])
                            st.dataframe(df_b9, width="stretch", hide_index=True)

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

                    # Preparar datos ejecutivos para el PDF de Alta Gerencia (Board Pack NIF/IFRS)
                    ing_bruto = float(ef_data.get("ingresos_cobrados_hist", 0.0))
                    com_aff = float(ef_data.get("comisiones_generadas_hist", 0.0))
                    util_neta = float(ef_data.get("ingreso_neto_post_comision", ing_bruto - com_aff))
                    iva_pct_sede = float(st.session_state.get("active_campus_iva", 8.0))
                    subtotal_sin_iva = round(ing_bruto / (1.0 + (iva_pct_sede / 100.0)), 2) if ing_bruto > 0 else 0.0
                    iva_trasladado = round(ing_bruto - subtotal_sin_iva, 2)

                    campus_pdf_info = {
                        "campus_id": str(st.session_state.get("active_campus_id", "CEI-AP-01")),
                        "nombre_plantel": str(st.session_state.get("active_campus_name", "Career English Institute — Sede Central")),
                        "direccion_oficial": str(institute_address or "Agua Prieta, Sonora, Mexico"),
                        "moneda": str(st.session_state.get("active_campus_currency", "MXN")),
                    }
                    resumen_kpis_pdf = {
                        "ingresos_brutos": ing_bruto,
                        "iva_total": iva_trasladado,
                        "egresos_totales": com_aff,
                        "utilidad_neta": util_neta,
                    }
                    lineas_pnl_pdf = [
                        {"concepto": "Ingresos Brutos Cobrados (Colegiaturas e Inscripciones)", "monto": ing_bruto, "pct": 100.0, "es_total": False},
                        {"concepto": f"(-) IVA Trasladado Desglosado ({iva_pct_sede:.0f}%)", "monto": iva_trasladado, "pct": round((iva_trasladado / ing_bruto * 100.0), 1) if ing_bruto else 0.0, "es_total": False},
                        {"concepto": "Ingresos Netos Antes de Comisiones", "monto": subtotal_sin_iva, "pct": round((subtotal_sin_iva / ing_bruto * 100.0), 1) if ing_bruto else 0.0, "es_total": True},
                        {"concepto": "(-) Provision y Liquidacion Comisiones Socios Afiliados", "monto": com_aff, "pct": round((com_aff / ing_bruto * 100.0), 1) if ing_bruto else 0.0, "es_total": False},
                        {"concepto": "UTILIDAD NETA OPERATIVA DEL PERIODO", "monto": util_neta, "pct": round((util_neta / ing_bruto * 100.0), 1) if ing_bruto else 0.0, "es_total": True},
                    ]
                    detalle_rubros_pdf = [
                        {
                            "rubro": "Colegiaturas Cobradas (Alumnos Al Corriente)",
                            "movimientos": int(ef_data.get("conteo_al_corriente", 0)),
                            "subtotal": subtotal_sin_iva,
                            "total": ing_bruto,
                        },
                        {
                            "rubro": "Cartera Vigente por Cobrar (Semanas 1-4)",
                            "movimientos": max(0, int(ef_data.get("total_alumnos", 0)) - int(ef_data.get("conteo_al_corriente", 0)) - int(ef_data.get("conteo_moratorios", 0))),
                            "subtotal": round(float(ef_data.get("cartera_por_cobrar_vigente", 0.0)) / (1.0 + (iva_pct_sede / 100.0)), 2),
                            "total": float(ef_data.get("cartera_por_cobrar_vigente", 0.0)),
                        },
                        {
                            "rubro": "Cartera Vencida en Mora (Requiere Seguimiento)",
                            "movimientos": int(ef_data.get("conteo_moratorios", 0)),
                            "subtotal": round(float(ef_data.get("cartera_vencida_moratoria", 0.0)) / (1.0 + (iva_pct_sede / 100.0)), 2),
                            "total": float(ef_data.get("cartera_vencida_moratoria", 0.0)),
                        },
                    ]

                    col_exp1, col_exp2 = st.columns(2)
                    with col_exp1:
                        try:
                            from financial_report_pdf import generar_pdf_estado_financiero_gerencial
                            periodo_hoy = datetime.now(ZoneInfo("America/Hermosillo")).strftime("%B %Y").upper()
                            pdf_ef_bytes, folio_ef_pdf = generar_pdf_estado_financiero_gerencial(
                                campus_info=campus_pdf_info,
                                periodo_label=periodo_hoy,
                                resumen_kpis=resumen_kpis_pdf,
                                lineas_pnl=lineas_pnl_pdf,
                                detalle_conceptos=detalle_rubros_pdf,
                                emisor_nombre="Jacob Zumaya Prianti"
                            )
                            st.download_button(
                                label="🏛️ Descargar Estado Financiero Gerencial (PDF)",
                                data=pdf_ef_bytes,
                                file_name=f"Estado_Financiero_Gerencial_CEI_{folio_ef_pdf}.pdf",
                                mime="application/pdf",
                                type="primary",
                                width="stretch",
                                key="btn_dl_ef_pdf_gerencial"
                            )
                        except Exception as e_pdf:
                            st.warning(f"⚠️ No se pudo generar el PDF gerencial: {e_pdf}")

                    with col_exp2:
                        csv_ef = df_ef.to_csv(index=False).encode("utf-8-sig")
                        st.download_button(
                            label="📥 Exportar Auxiliar de Cartera (CSV / Excel)",
                            data=csv_ef,
                            file_name=f"Estado_Financiero_CEI_{datetime.now(ZoneInfo('America/Hermosillo')).strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            width="stretch",
                            key="btn_dl_ef_csv"
                        )
                else:
                    st.info("No hay registros financieros de estudiantes para mostrar.")


 # 14.5C PESTAÑA DEDICADA: ALTA DE SOCIOS AFILIADOS, TÉRMINOS Y QR DE REGISTRO
        if seccion_inst_sel == "🤝 Alta de Socios Afiliados":
            puede_editar_terminos_aff = is_owner or can("Editar_Terminos_Afiliacion") or can("Gestionar_Compliance_Legal")
            if not (is_owner or puede_gestionar_afiliados or puede_editar_terminos_aff):
                st.warning("⛔ Tu perfil actual no tiene permisos habilitados para gestionar Socios Afiliados ni Términos.")
            else:
                if puede_editar_terminos_aff:
                    with st.expander("📜 Editar Términos, Condiciones y Compliance de Socios Afiliados", expanded=False):
                        from legal_terms_manager import get_institutional_terms_pg, save_institutional_terms_pg
                        terms_data = get_institutional_terms_pg("afiliado")
                        if terms_data.get("updated_at"):
                            st.caption(f"Última actualización: `{terms_data['updated_at']}` por **{terms_data['updated_by']}**")
                        txt_terms_edit = st.text_area(
                            "Texto legal vigente mostrado en registro_afiliados.py:",
                            value=terms_data["texto"],
                            height=240,
                            key="ta_edit_affiliate_terms_admin"
                        )
                        if st.button("💾 Guardar y Publicar Términos de Afiliados", type="primary", key="btn_save_aff_terms_admin"):
                            if not txt_terms_edit.strip():
                                st.warning("⚠️ El texto de Términos y Condiciones no puede quedar vacío.")
                            else:
                                ok_t, msg_t = save_institutional_terms_pg("afiliado", txt_terms_edit, str(st.session_state.current_user or "Owner"))
                                st.success(msg_t) if ok_t else st.error(msg_t)

                if is_owner or puede_gestionar_afiliados:
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
            url_portal_aff = str(
                st.secrets.get("AFFILIATE_PORTAL_URL")
                or ("https://" + "ceiafiliados.streamlit.app")
            ).strip().rstrip("/")
            aff_objetivo_portal = st.session_state.current_user

            if is_owner or puede_gestionar_afiliados:
                padron_aff_view = load_padron_records()
                lista_aff_view = [
                    str(r.get("Usuario", "")).strip()
                    for r in padron_aff_view
                    if str(r.get("Rol", "")).lower() in ["socio afiliado", "afiliado", "affiliate"]
                ]
                col_p_sel, col_p_qr = st.columns([2.6, 1.0])
                with col_p_sel:
                    if lista_aff_view:
                        aff_objetivo_portal = st.selectbox("Portal del Socio Afiliado:", lista_aff_view, key="sel_prev_aff")
                    else:
                        aff_objetivo_portal = None
                        st.info("Aún no hay Socios Afiliados registrados.")
                with col_p_qr:
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
                _render_qr_inscripcion_alumnos_box(
                    afiliado_ref=str(aff_objetivo_portal).strip(),
                    key_prefix=f"portal_aff_{str(aff_objetivo_portal).strip().replace(' ', '_')}"
                )
                _render_qr_descarga_app_box(
                    key_prefix=f"portal_aff_app_{str(aff_objetivo_portal).strip().replace(' ', '_')}"
                )

                conn_pf = _open_legal_pg_conn()
                s_dat = None
                if conn_pf:
                    try:
                        with conn_pf.cursor() as cur:
                            cur.execute("""
                                ALTER TABLE affiliate_partners
                                ADD COLUMN IF NOT EXISTS rfc TEXT DEFAULT '',
                                ADD COLUMN IF NOT EXISTS terminos_aceptados BOOLEAN DEFAULT TRUE,
                                ADD COLUMN IF NOT EXISTS terminos_aceptados_at TIMESTAMP WITH TIME ZONE;
                            """)
                            cur.execute("""
                                SELECT affiliate_id, usuario_login, nombre, apellido_paterno, apellido_materno,
                                       COALESCE(rfc, ''), COALESCE(telefono, ''), COALESCE(email, ''),
                                       COALESCE(domicilio, ''), COALESCE(estatus, 'Activo'),
                                       COALESCE(porcentaje_default, 0.0), terminos_aceptados_at
                                FROM affiliate_partners
                                WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s))
                                LIMIT 1;
                            """, (aff_objetivo_portal,))
                            s_dat = cur.fetchone()
                    except Exception:
                        pass
                    finally:
                        try:
                            conn_pf.close()
                        except Exception:
                            pass


                # 14.6B EDITOR DE EXPEDIENTE Y RADAR DE RACHAS SEMANALES + WHATSAPP (PARTE 2 DE 2 — MITAD 1)
                if s_dat:
                    (
                        aff_id_v, _aff_usr_v, aff_nom_v, aff_pat_v, aff_mat_v,
                        aff_rfc_v, aff_tel_v, aff_mail_v, aff_dom_v,
                        aff_est_v, aff_pct_v, aff_terms_v
                    ) = (list(s_dat) + ["", "", "", "", "", "", "", "", "", "Activo", 0.0, None])[:12]

                    st.info(
                        f"🆔 **ID Afiliado:** `{aff_id_v}`  |  👤 **Titular:** **{aff_nom_v} {aff_pat_v} {aff_mat_v or ''}**\n\n"
                        f"🧾 **RFC:** `{aff_rfc_v or 'No registrado'}`  |  📞 **Tel:** `{aff_tel_v or '—'}`  |  ✉️ **Email:** `{aff_mail_v or '—'}`\n\n"
                        f"📍 **Domicilio:** {aff_dom_v or 'No registrado'}\n\n"
                        f"💼 **Comisión Asignada:** **`{float(aff_pct_v or 0.0):.1f}%`**  |  🏷️ **Estatus:** `{aff_est_v}`\n\n"
                        "📄 *Recordatorio Fiscal: Expedir factura electrónica (CFDI) vigente para cobro de comisiones.*"
                    )

                    if is_owner or puede_gestionar_afiliados:
                        with st.expander(f"✏️ Editar Datos, RFC y Comisión de {aff_nom_v} {aff_pat_v} (Owner / Admin)", expanded=False):
                            if aff_terms_v:
                                st.caption(f"🛡️ Términos y Condiciones aceptados el: `{str(aff_terms_v)[:19]}`")
                            with st.form(f"form_edit_aff_portal_{aff_objetivo_portal}"):
                                c_e1, c_e2 = st.columns(2)
                                with c_e1:
                                    ed_id = st.text_input("🆔 ID de Afiliado:", value=str(aff_id_v or ""))
                                    ed_nom = st.text_input("Nombre(s):", value=str(aff_nom_v or ""))
                                    ed_pat = st.text_input("Apellido Paterno:", value=str(aff_pat_v or ""))
                                    ed_mat = st.text_input("Apellido Materno:", value=str(aff_mat_v or ""))
                                    ed_rfc = st.text_input("🧾 RFC (12 o 13 caracteres):", value=str(aff_rfc_v or ""), max_chars=13)
                                with c_e2:
                                    ed_tel = st.text_input("Teléfono / WhatsApp:", value=str(aff_tel_v or ""))
                                    ed_mail = st.text_input("Correo Electrónico:", value=str(aff_mail_v or ""))
                                    ed_dom = st.text_input("Domicilio Completo:", value=str(aff_dom_v or ""))
                                    ed_pct = st.number_input(
                                        "💼 Porcentaje Comisión Base (%):",
                                        min_value=0.0, max_value=100.0,
                                        value=float(aff_pct_v or 0.0), step=1.0
                                    )
                                    estados_aff = ["Activo", "Inactivo", "Baja"]
                                    idx_est = estados_aff.index(aff_est_v) if aff_est_v in estados_aff else 0
                                    ed_est = st.selectbox("Estado del Afiliado:", estados_aff, index=idx_est)


                                if st.form_submit_button("💾 Guardar Cambios y Comisión", type="primary", width="stretch"):
                                    conn_sv = _open_legal_pg_conn()
                                    if conn_sv:
                                        try:
                                            with conn_sv:
                                                with conn_sv.cursor() as cur:
                                                    cur.execute("""
                                                        UPDATE affiliate_partners SET
                                                            affiliate_id = %s,
                                                            nombre = %s,
                                                            apellido_paterno = %s,
                                                            apellido_materno = %s,
                                                            rfc = %s,
                                                            telefono = %s,
                                                            email = %s,
                                                            domicilio = %s,
                                                            porcentaje_default = %s,
                                                            estatus = %s
                                                        WHERE LOWER(TRIM(usuario_login)) = LOWER(TRIM(%s));
                                                    """, (
                                                        ed_id.strip().upper(), ed_nom.strip(), ed_pat.strip(), ed_mat.strip(),
                                                        ed_rfc.strip().upper(), ed_tel.strip(), ed_mail.strip(), ed_dom.strip(),
                                                        float(ed_pct), ed_est, aff_objetivo_portal
                                                    ))
                                                    est_pad = "Activo" if ed_est == "Activo" else "Inactivo"
                                                    cur.execute("""
                                                        UPDATE users_padron SET
                                                            estatus = %s,
                                                            porcentaje_comision = %s
                                                        WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s));
                                                    """, (est_pad, float(ed_pct), aff_objetivo_portal))
                                            st.cache_data.clear()
                                            st.success(f"✅ Datos y comisión ({ed_pct:.1f}%) actualizados correctamente.")
                                            st.rerun()
                                        except Exception as e_sv:
                                            st.error(f"Error al guardar cambios: {e_sv}")
                                        finally:
                                            try:
                                                conn_sv.close()
                                            except Exception:
                                                pass


                # RADAR DE RACHAS SEMANALES, HISTORIAL DE PAGOS (9 BLOQUES) Y WHATSAPP 200%
                puede_ver_racha_ref = (
                    is_owner
                    or can("Ver_Racha_Referidos_WhatsApp")
                    or bool(PERMISSIONS_MATRIX.get("Socio Afiliado", {}).get("Ver_Racha_Referidos_WhatsApp"))
                )
                if puede_ver_racha_ref:
                    padron_aff_ref = load_padron_records() or []
                    aff_id_cmp = str(s_dat[0]).strip().lower() if s_dat else ""
                    aff_usr_cmp = str(aff_objetivo_portal or "").strip().lower()
                    pct_com_socio = float(s_dat[10] or 0.0) if s_dat else 0.0

                    referidos_lista = [
                        r for r in padron_aff_ref
                        if str(r.get("Rol", "")).lower() in ["estudiante", "student", "alumno"]
                        and str(r.get("Socio_Afiliado") or r.get("Afiliado") or "").strip().lower() in [aff_usr_cmp, aff_id_cmp]
                    ]

                    pagos_por_alumno = {}
                    conn_pay_aff = _open_legal_pg_conn()
                    if conn_pay_aff:
                        try:
                            with conn_pay_aff.cursor() as cur:
                                cur.execute("""
                                    SELECT LOWER(TRIM(usuario_estudiante)),
                                           COUNT(*) FILTER (WHERE LOWER(COALESCE(estatus, 'pagado')) IN ('pagado', 'completado', 'activo')),
                                           COALESCE(SUM(monto_total) FILTER (WHERE LOWER(COALESCE(estatus, 'pagado')) IN ('pagado', 'completado', 'activo')), 0.0),
                                           MAX(fecha_pago)
                                    FROM student_payments
                                    GROUP BY LOWER(TRIM(usuario_estudiante));
                                """)
                                for row_p in cur.fetchall():
                                    pagos_por_alumno[str(row_p[0])] = {
                                        "bloques_pagados": int(row_p[1] or 0),
                                        "monto_pagado": float(row_p[2] or 0.0),
                                        "ultimo_pago": str(row_p[3] or "")[:10]
                                    }
                        except Exception:
                            pass
                        finally:
                            try:
                                conn_pay_aff.close()
                            except Exception:
                                pass

                    total_recaudado_ref = sum(
                        pagos_por_alumno.get(str(r.get("Usuario") or "").strip().lower(), {}).get("monto_pagado", 0.0)
                        for r in referidos_lista
                    )
                    comision_ganada_mxn = round(total_recaudado_ref * (pct_com_socio / 100.0), 2)
                    alumnos_oro_cnt = 0
                    resumen_gam_cache = {}
                    for r_tmp in referidos_lista:
                        u_tmp = str(r_tmp.get("Usuario") or "").strip()
                        n_tmp = str(r_tmp.get("Nivel") or "B1").strip()
                        g_tmp = calcular_gamificacion_estudiante(u_tmp, n_tmp)
                        resumen_gam_cache[u_tmp] = g_tmp
                        if "oro" in str(g_tmp.get("categoria_label", "")).lower():
                            alumnos_oro_cnt += 1

                    # KPIs superiores en 2 pares responsivos
                    k_s1, k_s2 = st.columns(2)
                    k_s1.metric("🎓 Alumnos Inscritos", f"{len(referidos_lista)}")
                    k_s2.metric("🥇 En Categoría Oro", f"{alumnos_oro_cnt} / {len(referidos_lista)}")

                    k_s3, k_s4 = st.columns(2)
                    k_s3.metric("💼 Tasa Comisión", f"{pct_com_socio:.1f}%")
                    k_s4.metric("💰 Comisión Generada", f"${comision_ganada_mxn:,.2f}")

                    with st.container(border=True):
                        st.markdown("##### 🔥 Acompañamiento 200%: Rachas Oro, Pagos (9 Bloques) y WhatsApp")
                        st.caption(
                            "Impulsa a cada estudiante hacia la Categoría Oro y mantén al corriente sus 9 bloques "
                            "con mensajes personalizados en un clic."
                        )

                        if not referidos_lista:
                            st.info("ℹ️ Aún no tienes estudiantes referidos registrados con tu código o QR.")
                        else:
                            app_link_pub = str(st.secrets.get("PUBLIC_APP_URL", "https://streamlit.app")).strip()
                            for idx_ref, r_est in enumerate(referidos_lista):
                                est_u = str(r_est.get("Usuario") or "").strip()
                                est_nom = str(r_est.get("Nombre_Completo") or est_u).strip()
                                est_mat = str(r_est.get("Matricula") or r_est.get("ID") or "").strip()
                                est_niv = str(r_est.get("Nivel") or "B1").strip()
                                est_tel = str(r_est.get("Telefono") or r_est.get("Whatsapp") or "").strip()

                                gam_est = resumen_gam_cache.get(est_u) or calcular_gamificacion_estudiante(est_u, est_niv)
                                wa_mot_link = build_whatsapp_motivacion_racha(
                                    student_user=est_nom,
                                    gam_data=gam_est,
                                    telefono_alumno=est_tel
                                )

                                info_pago = pagos_por_alumno.get(est_u.lower(), {"bloques_pagados": 0, "monto_pagado": 0.0, "ultimo_pago": ""})
                                bloq_pag = min(9, int(info_pago["bloques_pagados"]))
                                monto_est = float(info_pago["monto_pagado"])
                                com_est = round(monto_est * (pct_com_socio / 100.0), 2)

                                if bloq_pag >= 9:
                                    semaforo_pago = "🏆 Liquidado (9/9)"
                                elif bloq_pag >= 1:
                                    semaforo_pago = f"🟢 Al Corriente ({bloq_pag}/9)"
                                else:
                                    semaforo_pago = "🟡 Pendiente 1er Bloque (0/9)"

                                digits_tel = "".join(ch for ch in est_tel if ch.isdigit())
                                if len(digits_tel) == 10:
                                    digits_tel = f"52{digits_tel}"
                                msg_pago_wa = (
                                    f"¡Hola {est_nom}! 👋 Te saluda tu asesor de *Career English Institute (CEI)*. "
                                    f"Revisando tu avance vas en *{bloq_pag}/9 bloques* y categoría *{gam_est['categoria_label']}* 🏅. "
                                    f"Recuerda mantener al corriente tu siguiente bloque para conservar tus beneficios y seguir sumando hacia *Categoría Oro*. "
                                    f"Ingresa aquí a tu plataforma: {app_link_pub}"
                                )
                                wa_pago_link = (
                                    f"https://wa.me{digits_tel}?text={urllib.parse.quote(msg_pago_wa)}"
                                    if digits_tel else f"https://wa.me?text={urllib.parse.quote(msg_pago_wa)}"
                                )

                                with st.container(border=True):
                                    st.markdown(
                                        f"**🎓 {est_nom}** (`{est_u}`)"
                                        + (f" • 🆔 `{est_mat}`" if est_mat else "")
                                        + f" • Nivel **{est_niv}**"
                                    )
                                    est_fuego = "🔥 Activa" if gam_est["activo_esta_semana"] else "⏳ Pendiente"
                                    st.markdown(
                                        f"🏅 **{gam_est['categoria_label']}** | "
                                        f"🔥 Racha: **{gam_est['racha_semanas']} sem.** ({est_fuego}) | "
                                        f"📚 Folios: **{gam_est['total_folios']}**\n\n"
                                        f"💳 **Pagos:** {semaforo_pago} | "
                                        f"💰 **Comisión generada:** **`${com_est:,.2f}`**"
                                        + (f" *(Último pago: `{info_pago['ultimo_pago']}`)*" if info_pago["ultimo_pago"] else "")
                                    )
                                    c_b1, c_b2 = st.columns(2)
                                    with c_b1:
                                        st.link_button(
                                            "🔥 Motivar Meta Oro (WhatsApp)",
                                            url=wa_mot_link,
                                            width="stretch"
                                        )
                                    with c_b2:
                                        st.link_button(
                                            "💳 Seguimiento Pago (WhatsApp)",
                                            url=wa_pago_link,
                                            width="stretch"
                                        )

  

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
# PARTE 15A: EJECUCIÓN PARALELA (QUIZ + VIDEO EDUCATIVO), AUDIO Y PERSISTENCIA
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

                # Inicializar estados del Video Educativo (25%) y Resumen APA 7 (15%)
                st.session_state["current_lesson_video"] = None
                st.session_state["video_watched_sec"] = 0
                st.session_state["video_score_100"] = 0.0
                st.session_state["video_watch_started_ts"] = None
                st.session_state["video_summary_draft"] = ""
                st.session_state["video_apa7_draft"] = ""
                st.session_state["summary_score_100"] = 0.0
                st.session_state["summary_eval_result"] = None

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
                    fut_vid = pool.submit(
                        _run_with_ctx,
                        buscar_video_relacionado_leccion,
                        gramatica_b1,
                        cefr_level,
                        texto_gen,
                        gm_active
                    )
                    try:
                        st.session_state.quiz_data = fut_quiz.result(timeout=20)
                    except Exception:
                        st.session_state.quiz_data = None
                    try:
                        st.session_state["current_lesson_video"] = fut_vid.result(timeout=20)
                    except Exception:
                        st.session_state["current_lesson_video"] = None

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
                    if st.session_state.get("current_lesson_video"):
                        save_video_and_summary_pg(
                            folio_code=nuevo_folio,
                            video_info=st.session_state["current_lesson_video"]
                        )
                except Exception as e_db:
                    st.warning(f"⚠️ Lección generada, pero hubo un aviso al guardar en Supabase: {e_db}")

                st.session_state.sidebar_state = "collapsed"
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error al generar lección: {e}")

# ==============================================================================
# PARTE 16 — BLOQUE 1-A: VENTANA MAESTRA 1 (READING 30% + TAMAÑO DE LETRA + QUIZ)
# ==============================================================================
if st.query_params.get("study_w"):
    st.session_state["study_mode_active"] = True
if "split_speaking_open" not in st.session_state:
    st.session_state["split_speaking_open"] = False
if "split_writing_open" not in st.session_state:
    st.session_state["split_writing_open"] = False

texto_leccion_activo = str(st.session_state.get("generated_text") or "").strip()
has_lesson_now = bool(texto_leccion_activo)
stage_5_now = st.session_state.get("active_stage_5") or "READING"
if stage_5_now not in ["READING", "VIEWING", "PORTAL"]:
    stage_5_now = "READING"
    st.session_state["active_stage_5"] = "READING"

if has_lesson_now and stage_5_now != "PORTAL":
    if stage_5_now == "READING":
        hdr_r1, hdr_r2, hdr_r3 = st.columns([2.1, 1.0, 1.35])
        with hdr_r1:
            st.subheader(f"📖 1. READING & COMPREHENSION ({st.session_state.selected_cefr})")
        with hdr_r2:
            lbl_modo = "📄 Lectura Clásica" if st.session_state.get("study_mode_active") else "🧠 Modo Estudio IA"
            if st.button(lbl_modo, type="secondary", width="stretch", key="btn_toggle_study_mode"):
                st.session_state.study_mode_active = not st.session_state.get("study_mode_active", False)
                if not st.session_state.study_mode_active:
                    st.session_state["active_study_word"] = ""
                    if "study_w" in st.query_params:
                        del st.query_params["study_w"]
                    if "study_p" in st.query_params:
                        del st.query_params["study_p"]
                st.rerun()
        with hdr_r3:
            spk_open = bool(st.session_state.get("split_speaking_open"))
            lbl_btn_3 = "✖️ Cerrar Grabadora (3)" if spk_open else "🎙️ 3. ALPHABETICAL & SPEAKING (25%)"
            if st.button(lbl_btn_3, type="primary", width="stretch", key="btn_toggle_split_speaking"):
                st.session_state["split_speaking_open"] = not spk_open
                st.rerun()

        if st.session_state.get("split_speaking_open"):
            col_read_box, col_spk_box = st.columns([1.35, 1.05])
        else:
            col_read_box = st.container()
            col_spk_box = None

        with col_read_box:
            font_options_map = {
                "Normal (16 px)": 16,
                "Mediana (19 px)": 19,
                "Grande (22 px)": 22,
                "Extra Grande (26 px)": 26
            }
            cf_1, cf_2 = st.columns([1.5, 2.3])
            with cf_1:
                sel_font_lbl = st.selectbox(
                    "🔠 Tamaño de letra:",
                    list(font_options_map.keys()),
                    index=0,
                    key="sb_lesson_font_size"
                )
            font_px = font_options_map[sel_font_lbl]

            st.markdown(
                f"""
                <style>
                .cei-lesson-reader, .cei-lesson-reader p, .cei-lesson-reader li,
                .cei-lesson-reader span, .cei-lesson-reader a,
                .cei-quiz-box p, .cei-quiz-box label,
                .cei-quiz-box div[data-testid="stRadio"] p {{
                    font-size: {font_px}px !important;
                    line-height: 1.65 !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

            if st.session_state.get("study_mode_active"):
                with st.spinner("Analizando estructuras gramaticales, fonética y definiciones..."):
                    payload_estudio = analyze_lesson_for_study_mode(
                        st.session_state.generated_text,
                        st.session_state.selected_cefr
                    )
                st.markdown("<div class='cei-lesson-reader'>", unsafe_allow_html=True)
                render_interactive_study_viewer(payload_estudio)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                with st.container(height=540, border=True):
                    st.markdown(
                        f"<div class='cei-lesson-reader'>{st.session_state.generated_text}</div>",
                        unsafe_allow_html=True
                    )

            # QUIZ DE COMPRENSIÓN (30% DE LA RÚBRICA — SINCRONIZADO CON TAMAÑO DE LETRA)
            if st.session_state.quiz_data is None:
                cefr_tag = next(iter(st.session_state.selected_cefr.split()), "CEFR") if st.session_state.selected_cefr else "CEFR"
                if st.button(
                    f"📝 Generar Quiz de Comprensión — 30% ({cefr_tag} - {st.session_state.selected_academic_grade})",
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
                                save_quiz_and_best_score_pg(st.session_state.current_folio, "", q_gen, {})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al generar quiz: {e}")
            else:
                with st.container(border=True):
                    st.markdown("<div class='cei-quiz-box'>", unsafe_allow_html=True)
                    st.subheader(f"📝 Reading & Grammar Comprehension Quiz — 30% (Folio: {st.session_state.current_folio})")
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
                    st.markdown("</div>", unsafe_allow_html=True)

                    c_qz1, c_qz2 = st.columns(2)
                    with c_qz1:
                        if st.button("✅ Calificar Quiz (30%)", type="primary", width="stretch", key="btn_grade_quiz_in_box"):
                            correctas = 0
                            total_q = len(st.session_state.quiz_data)
                            for idx_g, item_g in enumerate(st.session_state.quiz_data):
                                if st.session_state.quiz_user_answers.get(idx_g) == item_g.get("answer"):
                                    correctas += 1
                            st.session_state.quiz_graded = True
                            st.session_state.quiz_score = f"{correctas}/{total_q}"
                            if st.session_state.current_folio:
                                save_quiz_and_best_score_pg(
                                    st.session_state.current_folio,
                                    st.session_state.quiz_score,
                                    st.session_state.quiz_data,
                                    st.session_state.quiz_user_answers
                                )
                            st.rerun()

                    with c_qz2:
                        if st.button("🔄 Nuevo Quiz / Cambiar Preguntas", type="secondary", width="stretch", key="btn_regen_quiz_in_box"):
                            with st.spinner("Generando nuevas preguntas de evaluación..."):
                                try:
                                    q_new = generar_quiz_leccion(
                                        st.session_state.generated_text,
                                        gramatica_b1,
                                        st.session_state.selected_cefr,
                                        st.session_state.selected_academic_grade
                                    )
                                    st.session_state.quiz_data = q_new
                                    st.session_state.quiz_graded = False
                                    st.session_state.quiz_score = None
                                    st.session_state.quiz_user_answers = {}
                                    st.session_state.quiz_audio_bytes = None
                                    if st.session_state.current_folio:
                                        save_quiz_and_best_score_pg(st.session_state.current_folio, "", q_new, {})
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al regenerar quiz: {e}")

                    if st.session_state.quiz_graded and st.session_state.quiz_score:
                        st.success(f"🏆 **Resultado del Quiz (30%):** `{st.session_state.quiz_score}` respuestas correctas.")


# ==============================================================================
# PARTE 16 — BLOQUE 1-B: PANEL DERECHO DE SPEAKING (25%) EN VISTA DIVIDIDA
# ==============================================================================
        if col_spk_box is not None:
            with col_spk_box:
                with st.container(border=True):
                    st.subheader("🎙️ 3. ALPHABETICAL & SPEAKING (25%)")
                    if st.session_state.audio_bytes:
                        st.caption("🎧 **1. Escucha el Audio Modelo:**")
                        st.audio(st.session_state.audio_bytes, format="audio/mp3")
                        safe_audio_name = f"CEI_Audio_{st.session_state.current_folio or usuario.replace(' ', '_')}.mp3"
                        st.download_button(
                            label="📥 Descargar Audio Modelo (MP3)",
                            data=st.session_state.audio_bytes,
                            file_name=safe_audio_name,
                            mime="audio/mp3",
                            width="stretch"
                        )
                    else:
                        st.caption("Audio modelo disponible al generar o cargar una lección.")

                    st.divider()
                    st.caption("🎤 **2. Graba tu lectura observando el texto a la izquierda:**")
                    tab_rec_audio, tab_rec_video = st.tabs(["🎤 Grabar Audio", "📹 Grabar Video"])

                    with tab_rec_audio:
                        student_audio = st.audio_input("Graba tu voz leyendo el texto:", key="audio_in_split_s3")
                        if student_audio is not None:
                            raw_aud = student_audio.getvalue()
                            st.audio(raw_aud)
                            if st.button("🤖 Evaluar Pronunciación con IA (25%)", type="primary", key="btn_eval_aud_split_s3", width="stretch"):
                                with st.spinner("Analizando pronunciación, entonación y gramática oral con IA..."):
                                    try:
                                        ev_oral = evaluar_pronunciacion_oral_ia(
                                            raw_aud, "audio/wav", st.session_state.generated_text,
                                            st.session_state.selected_cefr, gramatica_b1
                                        )
                                        st.session_state["speaking_eval_result"] = ev_oral
                                        sc_pct = float(ev_oral.get("score_percent") or 0.0)
                                        pts_25 = round((sc_pct / 100.0) * 25.0, 2)
                                        f_code = st.session_state.current_folio or ""
                                        usr_now = st.session_state.get("current_user") or "Estudiante"
                                        if f_code:
                                            public_u, _ = upload_student_media_to_storage(raw_aud, "audio/wav", "wav", f_code, usr_now)
                                            save_student_media_record_pg(
                                                f_code, usr_now, "audio", public_u or "", gramatica_b1,
                                                st.session_state.selected_cefr, eval_dict=ev_oral
                                            )
                                        st.success(f"🏆 **Calificación Oral:** {sc_pct}% (`{pts_25} / 25.0 pts`)")
                                        st.write(f"**🔤 Fonética:** {ev_oral.get('phonetic_feedback', '')}")
                                        st.write(f"**🎵 Fluidez:** {ev_oral.get('fluency_prosody', '')}")
                                        st.write(f"**📐 Gramática:** {ev_oral.get('grammar_accuracy', '')}")
                                    except Exception as e:
                                        st.error(f"Error al evaluar pronunciación: {e}")

                    with tab_rec_video:
                        st.caption("📹 **Cámara Web en Vivo:** Pulsa **🔴 Grabar**, lee el texto de la izquierda, pulsa **⏹️ Detener**, descárgalo y evalúalo con IA:")

                        webcam_recorder_html = """
                        <div style="background:#0f172a;padding:12px;border-radius:12px;color:#f8fafc;font-family:sans-serif;">
                          <video id="ceiPreview" autoplay muted playsinline style="width:100%;max-height:240px;border-radius:8px;background:#000;object-fit:cover;"></video>
                          <video id="ceiPlayback" controls playsinline style="width:100%;max-height:240px;border-radius:8px;background:#000;display:none;margin-top:8px;"></video>
                          <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
                            <button id="btnStartVid" style="flex:1;padding:8px 12px;border:none;border-radius:8px;background:#dc2626;color:#fff;font-weight:bold;cursor:pointer;">🔴 Grabar</button>
                            <button id="btnStopVid" disabled style="flex:1;padding:8px 12px;border:none;border-radius:8px;background:#475569;color:#fff;font-weight:bold;cursor:pointer;">⏹️ Detener</button>
                            <a id="btnDlVid" style="display:none;flex:1;padding:8px 12px;border-radius:8px;background:#16a34a;color:#fff;font-weight:bold;text-align:center;text-decoration:none;">📥 Descargar Video</a>
                          </div>
                          <div id="vidStatus" style="font-size:12px;color:#94a3b8;margin-top:6px;">Listo para activar cámara y micrófono.</div>
                        </div>
                        <script>
                        (function() {
                          let mediaRecorder;
                          let recordedChunks = [];
                          let activeStream = null;
                          const preview = document.getElementById('ceiPreview');
                          const playback = document.getElementById('ceiPlayback');
                          const btnStart = document.getElementById('btnStartVid');
                          const btnStop = document.getElementById('btnStopVid');
                          const btnDl = document.getElementById('btnDlVid');
                          const statusEl = document.getElementById('vidStatus');

                          btnStart.onclick = async () => {
                            try {
                              recordedChunks = [];
                              playback.style.display = 'none';
                              btnDl.style.display = 'none';
                              preview.style.display = 'block';
                              activeStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                              preview.srcObject = activeStream;
                              const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
                                ? 'video/webm;codecs=vp8,opus'
                                : 'video/webm';
                              mediaRecorder = new MediaRecorder(activeStream, { mimeType });
                              mediaRecorder.ondataavailable = (e) => {
                                if (e.data && e.data.size > 0) recordedChunks.push(e.data);
                              };
                              mediaRecorder.onstop = () => {
                                const blob = new Blob(recordedChunks, { type: 'video/webm' });
                                const url = URL.createObjectURL(blob);
                                preview.style.display = 'none';
                                playback.src = url;
                                playback.style.display = 'block';
                                btnDl.href = url;
                                btnDl.download = 'CEI_Speaking_Video.webm';
                                btnDl.style.display = 'inline-block';
                                statusEl.textContent = '✅ Grabación finalizada. Puedes reproducirla, descargarla o cargarla abajo para calificación con IA.';
                                if (activeStream) activeStream.getTracks().forEach(t => t.stop());
                              };
                              mediaRecorder.start();
                              btnStart.disabled = true;
                              btnStop.disabled = false;
                              btnStop.style.background = '#ea580c';
                              statusEl.textContent = '🔴 Grabando video y audio en vivo...';
                            } catch (err) {
                              statusEl.textContent = '⚠️ Permiso de cámara/micrófono denegado o no disponible: ' + err.message;
                            }
                          };

                          btnStop.onclick = () => {
                            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                              mediaRecorder.stop();
                              btnStart.disabled = false;
                              btnStop.disabled = true;
                              btnStop.style.background = '#475569';
                            }
                          };
                        })();
                        </script>
                        """
                        components.html(webcam_recorder_html, height=345)

                        student_video_file = st.file_uploader(
                            "📤 Cargar el video recién grabado (CEI_Speaking_Video.webm / MP4) para evaluar con IA:",
                            type=["webm", "mp4", "mov"],
                            key="vid_in_split_s3"
                        )
                        if student_video_file is not None:
                            raw_vid = student_video_file.getvalue()
                            st.video(raw_vid)
                            v_mime = student_video_file.type or "video/webm"
                            v_ext = "webm" if "webm" in v_mime else "mp4"

                            cv_act1, cv_act2 = st.columns(2)
                            with cv_act1:
                                st.download_button(
                                    label="📥 Descargar Video",
                                    data=raw_vid,
                                    file_name=f"CEI_Video_{st.session_state.current_folio or usuario.replace(' ', '_')}.{v_ext}",
                                    mime=v_mime,
                                    type="secondary",
                                    width="stretch",
                                    key="btn_dl_vid_split_s3"
                                )
                            with cv_act2:
                                if st.button("🤖 Evaluar Pronunciación con IA (25%)", type="primary", key="btn_eval_vid_split_s3", width="stretch"):
                                    with st.spinner("Analizando pronunciación, entonación y gramática oral en video con IA..."):
                                        try:
                                            ev_vid = evaluar_pronunciacion_oral_ia(
                                                raw_vid, v_mime, st.session_state.generated_text,
                                                st.session_state.selected_cefr, gramatica_b1
                                            )
                                            st.session_state["speaking_eval_result"] = ev_vid
                                            sc_vpct = float(ev_vid.get("score_percent") or 0.0)
                                            pts_v25 = round((sc_vpct / 100.0) * 25.0, 2)
                                            f_code = st.session_state.current_folio or ""
                                            usr_now = st.session_state.get("current_user") or "Estudiante"
                                            if f_code:
                                                public_v, _ = upload_student_media_to_storage(raw_vid, v_mime, v_ext, f_code, usr_now)
                                                save_student_media_record_pg(
                                                    f_code, usr_now, "video", public_v or "", gramatica_b1,
                                                    st.session_state.selected_cefr, eval_dict=ev_vid
                                                )
                                            st.success(f"🏆 **Calificación Oral (Video):** {sc_vpct}% (`{pts_v25} / 25.0 pts`)")
                                            st.write(f"**🔤 Fonética:** {ev_vid.get('phonetic_feedback', '')}")
                                            st.write(f"**🎵 Fluidez:** {ev_vid.get('fluency_prosody', '')}")
                                            st.write(f"**📐 Gramática:** {ev_vid.get('grammar_accuracy', '')}")
                                        except Exception as e:
                                            st.error(f"Error al evaluar video: {e}")

# ==============================================================================
# PARTE 16 — BLOQUE 2-A: VENTANA MAESTRA 2 (VIDEO ACTIVO + CRONÓMETRO 25%)
# ==============================================================================
    elif stage_5_now == "VIEWING":
        vid_stage = st.session_state.get("current_lesson_video") or {}
        if not vid_stage.get("url"):
            with st.spinner("Cargando video educativo relacionado con la lección..."):
                vid_stage = buscar_video_relacionado_leccion(
                    gramatica_b1,
                    st.session_state.selected_cefr,
                    st.session_state.generated_text,
                    topic_context=str(st.session_state.get("current_topic") or "").strip(),
                    max_videos=12
                )
                st.session_state["current_lesson_video"] = vid_stage
                if st.session_state.current_folio and vid_stage.get("url"):
                    save_video_and_summary_pg(folio_code=st.session_state.current_folio, video_info=vid_stage)
        v_url_st = str(vid_stage.get("url") or "").strip()
        m_id_st = re.search(r"(?:v=|youtu\.be/|embed/|youtube\.com/?)([a-zA-Z0-9_-]{11})", v_url_st)
        vid_id_st = m_id_st.group(1) if m_id_st else "L9AWrJnhsRI"
        if vid_id_st.lower() == "o1_0gz4urko":
            vid_id_st = "L9AWrJnhsRI"
        v_watch_url = "https://youtube.com" + "/watch?v=" + vid_id_st


        hdr_v1, hdr_v2 = st.columns([2.4, 1.35])
        with hdr_v1:
            st.subheader("🎬 2. VIEWING & LISTENING SKILLS (25%)")
        with hdr_v2:
            wrt_open = bool(st.session_state.get("split_writing_open"))
            lbl_btn_4 = "✖️ Cerrar Writing (4)" if wrt_open else "✍️ 4. WRITING SKILL (20%)"
            if st.button(lbl_btn_4, type="primary", width="stretch", key="btn_toggle_split_writing"):
                st.session_state["split_writing_open"] = not wrt_open
                st.rerun()

        if st.session_state.get("split_writing_open"):
            col_vid_box, col_wrt_box = st.columns([1.25, 1.15])
        else:
            col_vid_box = st.container()
            col_wrt_box = None

        with col_vid_box:
            with st.container(border=True):
                titulo_st_safe = str(vid_stage.get("title") or "Educational Video").replace("[", "(").replace("]", ")")
                dur_sec_st = max(60, int(vid_stage.get("duration_sec") or 300))
                dur_min_st = round(dur_sec_st / 60.0, 2)
                watched_st = int(st.session_state.get("video_watched_sec") or 0)
                v_sc_st = float(st.session_state.get("video_score_100") or 0.0)
                pts_v_st = round((v_sc_st / 100.0) * 25.0, 2)
                folio_vid_key = str(st.session_state.current_folio or "DEFAULT")

                st.write(f"**📺 Video Activo:** {titulo_st_safe}")
                st.caption(
                    f"Canal: *{vid_stage.get('channel', 'YouTube')}*  |  Duración oficial: **`{dur_min_st} min`**  |  "
                    f"Acreditado en Boletín (25%): **`{pts_v_st} / 25.0 pts`** (`{round(v_sc_st, 1)}%`)"
                )

                v_watch_url = "https://youtube.com" + "/watch?v=" + vid_id_st

                # REPRODUCTOR OFICIAL YOUTUBE API + REGLA VISUAL AUTOMÁTICA SINCRONIZADA
                yt_ruler_html = f"""
                <div style="font-family:sans-serif;background:#0f172a;padding:12px;border-radius:12px;color:#f8fafc;">
                  <div id="ceiYtPlayer" style="width:100%;height:360px;border-radius:8px;overflow:hidden;background:#000;"></div>

                  <!-- REGLA VISUAL GRADUADA EN TIEMPO REAL -->
                  <div style="margin-top:12px;background:#1e293b;padding:10px 12px;border-radius:10px;border:1px solid #334155;">
                    <div style="display:flex;justify-content:space-between;align-items:center;font-size:13px;margin-bottom:6px;">
                      <span id="rulerStateBadge" style="font-weight:bold;color:#38bdf8;">⏸️ En espera (Pulsa Play en el video)</span>
                      <span id="rulerTimeText" style="font-family:monospace;font-size:14px;font-weight:bold;color:#f8fafc;">00:00 / 00:00 (0%)</span>
                    </div>

                    <!-- Barra de progreso sobre regla -->
                    <div style="position:relative;width:100%;height:18px;background:#0f172a;border-radius:9px;overflow:hidden;border:1px solid #475569;">
                      <div id="rulerFillBar" style="width:0%;height:100%;background:linear-gradient(90deg,#0284c7,#22c55e);transition:width 0.3s ease;"></div>
                    </div>

                    <!-- Marcas de graduación de la regla -->
                    <div style="display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;margin-top:4px;font-family:monospace;">
                      <span>0% (0 pts)</span>
                      <span>25% (6.25 pts)</span>
                      <span>50% (12.5 pts)</span>
                      <span>75% (18.75 pts)</span>
                      <span>100% (25.0 pts)</span>
                    </div>

                    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;font-size:12px;">
                      <span style="color:#cbd5e1;">⏱️ Tiempo efectivo acumulado al ritmo del video:</span>
                      <span id="rulerPointsBadge" style="font-weight:bold;color:#4ade80;font-size:14px;">0.00 / 25.00 pts</span>
                    </div>
                  </div>
                </div>

                <script src="https://youtube.com/iframe_api"></script>
                <script>
                  (function() {{
                    const storageKey = "cei_vid_sec_{folio_vid_key}_{vid_id_st}";
                    let watchedSeconds = Math.max({watched_st}, parseInt(localStorage.getItem(storageKey) || "0", 10));
                    let totalDuration = {dur_sec_st};
                    let player = null;
                    let tickInterval = null;

                    function fmtTime(sec) {{
                      sec = Math.max(0, Math.floor(sec));
                      const m = String(Math.floor(sec / 60)).padStart(2, '0');
                      const s = String(sec % 60).padStart(2, '0');
                      return m + ":" + s;
                    }}

                    function renderRuler() {{
                      const effectiveSec = Math.min(totalDuration, watchedSeconds);
                      const pct = totalDuration > 0 ? Math.min(100, (effectiveSec / totalDuration) * 100) : 0;
                      const pts = ((pct / 100) * 25.0).toFixed(2);
                      document.getElementById("rulerFillBar").style.width = pct.toFixed(1) + "%";
                      document.getElementById("rulerTimeText").textContent =
                        fmtTime(effectiveSec) + " / " + fmtTime(totalDuration) + " (" + pct.toFixed(1) + "%)";
                      document.getElementById("rulerPointsBadge").textContent = pts + " / 25.00 pts";
                      localStorage.setItem(storageKey, String(Math.floor(effectiveSec)));
                    }}

                    function startTick() {{
                      if (tickInterval) return;
                      tickInterval = setInterval(() => {{
                        if (player && typeof player.getPlayerState === "function" && player.getPlayerState() === 1) {{
                          const realDur = player.getDuration();
                          if (realDur && realDur > 10) totalDuration = Math.floor(realDur);
                          const currPos = Math.floor(player.getCurrentTime() || 0);
                          watchedSeconds = Math.max(watchedSeconds + 1, currPos);
                          if (watchedSeconds >= totalDuration - 2) {{
                            watchedSeconds = totalDuration;
                          }}
                          renderRuler();
                        }}
                      }}, 1000);
                    }}

                    function stopTick() {{
                      if (tickInterval) {{
                        clearInterval(tickInterval);
                        tickInterval = null;
                      }}
                    }}

                    window.onYouTubeIframeAPIReady = function() {{
                      player = new YT.Player('ceiYtPlayer', {{
                        videoId: '{vid_id_st}',
                        playerVars: {{ rel: 0, modestbranding: 1 }},
                        events: {{
                          onReady: function(e) {{
                            const d = e.target.getDuration();
                            if (d && d > 10) totalDuration = Math.floor(d);
                            renderRuler();
                          }},
                          onStateChange: function(e) {{
                            const badge = document.getElementById("rulerStateBadge");
                            if (e.data === 1) {{
                              badge.textContent = "▶️ Reproduciendo — Regla sincronizada activa";
                              badge.style.color = "#4ade80";
                              startTick();
                            }} else if (e.data === 2) {{
                              badge.textContent = "⏸️ Video pausado — Conteo detenido";
                              badge.style.color = "#facc15";
                              stopTick();
                              renderRuler();
                            }} else if (e.data === 0) {{
                              watchedSeconds = totalDuration;
                              badge.textContent = "✅ Video completado al 100% (25.0 / 25.0 pts)";
                              badge.style.color = "#4ade80";
                              stopTick();
                              renderRuler();
                            }}
                          }}
                        }}
                      }});
                    }};

                    if (window.YT && window.YT.Player) {{
                      window.onYouTubeIframeAPIReady();
                    }}
                    renderRuler();
                  }})();
                </script>
                """
                components.html(yt_ruler_html, height=495)

                # CANDADO DE ACREDITACIÓN: SI YA ESTÁ CALIFICADO AL 100%, MODO EXPLORACIÓN LIBRE
                video_ya_acreditado = float(st.session_state.get("video_score_100") or 0.0) >= 100.0

                if video_ya_acreditado:
                    st.success(
                        f"🏆 **Componente de Video ya acreditado al 100% ({pts_v_st} / 25.0 pts) en el Folio `{folio_vid_key}`.**\n\n"
                        "Puedes reproducir libremente todos los demás videos del catálogo para seguir practicando; "
                        "tu calificación ya quedó asegurada y no requiere volver a computarse ni registrarse."
                    )
                else:
                    c_sync1, c_sync2 = st.columns([1.4, 1.0])
                    with c_sync1:
                        min_leidos_manual = st.number_input(
                            "⏱️ Minutos marcados en la regla superior (para guardar en Boletín):",
                            min_value=0.0,
                            max_value=float(dur_min_st),
                            value=float(round(watched_st / 60.0, 2)),
                            step=0.25,
                            key="num_sync_video_minutes"
                        )
                    with c_sync2:
                        st.write("")
                        if st.button("✅ Guardar Progreso en Boletín", type="primary", key="btn_stage_save_timer", width="stretch"):
                            nuevo_w = min(dur_sec_st, int(round(min_leidos_manual * 60)))
                            if nuevo_w >= dur_sec_st - 5:
                                nuevo_w = dur_sec_st
                            nuevo_sc = min(100.0, round((nuevo_w / float(dur_sec_st)) * 100.0, 1))
                            st.session_state["video_watched_sec"] = nuevo_w
                            st.session_state["video_score_100"] = nuevo_sc
                            if st.session_state.current_folio:
                                save_video_and_summary_pg(folio_code=st.session_state.current_folio, watched_sec=nuevo_w, video_score_100=nuevo_sc)
                            st.success(f"✅ Acreditado en Boletín: {round(nuevo_w / 60.0, 2)} min ({nuevo_sc}%).")
                            st.rerun()


# ==============================================================================
# PARTE 16 — BLOQUE 2-B (FINAL): PANEL DERECHO DE WRITING SKILL (20%)
# ==============================================================================
        if col_wrt_box is not None:
            with col_wrt_box:
                with st.container(border=True):
                    st.subheader("✍️ 4. WRITING SKILL (20%)")
                    s_sc_c = float(st.session_state.get("summary_score_100") or 0.0)
                    pts_w_c = round((s_sc_c / 100.0) * 20.0, 2)
                    st.caption(f"**Resumen (120–125 palabras) + Cita APA 7 — Valor: 20% (`{pts_w_c} / 20.0 pts`)**")

                    font_opts_w = {
                        "Normal (16 px)": 16,
                        "Mediana (19 px)": 19,
                        "Grande (22 px)": 22,
                        "Extra Grande (26 px)": 26
                    }
                    lista_fw = list(font_opts_w.keys())
                    sel_prev_f = st.session_state.get("sb_lesson_font_size", "Normal (16 px)")
                    idx_fw = lista_fw.index(sel_prev_f) if sel_prev_f in lista_fw else 0

                    sel_fw = st.selectbox(
                        "🔠 Tamaño de letra del Resumen:",
                        lista_fw,
                        index=idx_fw,
                        key="sb_writing_font_size"
                    )
                    w_px = font_opts_w[sel_fw]
                    st.markdown(
                        f"""
                        <style>
                        div[data-testid="stTextArea"] textarea {{
                            font-size: {w_px}px !important;
                            line-height: 1.6 !important;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True
                    )

                    res_central = st.text_area(
                        "Write your English summary while watching the video (strictly 120 to 125 words):",
                        value=st.session_state.get("video_summary_draft", ""),
                        height=180,
                        placeholder="Write your academic summary in English while watching the video on the left (120–125 words)...",
                        key="txt_central_writing_summary"
                    )
                    cnt_c = len([w for w in re.findall(r"\b[\w'-]+\b", res_central.strip()) if w])
                    if 120 <= cnt_c <= 125:
                        st.success(f"✅ Conteo exacto: **{cnt_c} palabras** (rango válido: 120–125).")
                    else:
                        st.warning(f"📏 Conteo actual: **{cnt_c} palabras** *(debe contener 120–125 palabras)*.")

                    vid_ref_c = st.session_state.get("current_lesson_video") or {}
                    url_vid_apa = str(vid_ref_c.get("url") or "https://youtube.com")
                    ej_apa_c = (
                        f"{vid_ref_c.get('channel', 'Author/Channel')}. ({str(vid_ref_c.get('published_date', '2026'))[:4]}). "
                        f"{vid_ref_c.get('title', 'Title of the video')} [Video]. YouTube. {url_vid_apa}"
                    )
                    apa_central = st.text_area(
                        "📚 Referencia Bibliográfica en Formato APA 7:",
                        value=st.session_state.get("video_apa7_draft", ""),
                        height=80,
                        placeholder=f"Ejemplo APA 7:\n{ej_apa_c}",
                        key="txt_central_writing_apa7"
                    )

                    if st.button("📝 Calificar Writing Skill y APA 7 (20%)", type="primary", width="stretch", key="btn_central_eval_writing"):
                        with st.spinner("Evaluando Writing Skill (120-125 palabras) y formato APA 7 con IA..."):
                            ev_w = evaluar_resumen_video_apa7(
                                resumen_texto=res_central,
                                referencia_apa7=apa_central,
                                video_info=vid_ref_c,
                                tema_gramatical=gramatica_b1,
                                nivel_cefr=st.session_state.selected_cefr
                            )
                            st.session_state["video_summary_draft"] = res_central
                            st.session_state["video_apa7_draft"] = apa_central
                            if ev_w["ok"]:
                                st.session_state["summary_score_100"] = ev_w["raw_score_100"]
                                st.session_state["summary_eval_result"] = ev_w
                                if st.session_state.current_folio:
                                    save_video_and_summary_pg(
                                        folio_code=st.session_state.current_folio,
                                        summary_text=res_central,
                                        apa7_reference=apa_central,
                                        summary_score_100=ev_w["raw_score_100"],
                                        summary_eval_dict=ev_w
                                    )
                                st.success(f"🏆 Writing Skill: **{ev_w['raw_score_100']}%** (`{ev_w['weighted_points_20']} / 20.0 pts`).")
                                st.info(ev_w["feedback"])
                                if ev_w.get("apa7_corrected"):
                                    st.caption(f"📖 **Sugerencia APA 7:** {ev_w['apa7_corrected']}")
                            else:
                                st.error(ev_w["feedback"])


# ==============================================================================
# PARTE 17 — BLOQUE 2A: CATÁLOGO DE VIDEOS (SOLO ACTIVO EN BOTÓN 2 VIEWING)
# ==============================================================================
has_lesson_p17 = bool(str(st.session_state.get("generated_text") or "").strip())
stage_5_p17 = st.session_state.get("active_stage_5", "READING")

if has_lesson_p17 and stage_5_p17 == "VIEWING":
    st.markdown("### 📚 Catálogo Escrolable de Videos Relacionados")

    topico_actual_leccion = str(st.session_state.get("current_topic") or "").strip()
    titulo_catalogo = (
        f"{gramatica_b1} • {topico_actual_leccion}"
        if topico_actual_leccion
        else f"{gramatica_b1} ({st.session_state.selected_cefr})"
    )
    if "video_catalog_limit" not in st.session_state:
        st.session_state["video_catalog_limit"] = 12

    vid_data = st.session_state.get("current_lesson_video")
    if not vid_data or not vid_data.get("url"):
        vid_data = buscar_video_relacionado_leccion(
            gramatica_b1,
            st.session_state.selected_cefr,
            st.session_state.generated_text,
            topic_context=topico_actual_leccion,
            max_videos=st.session_state["video_catalog_limit"]
        )
        st.session_state["current_lesson_video"] = vid_data
        if st.session_state.current_folio and vid_data.get("url"):
            save_video_and_summary_pg(folio_code=st.session_state.current_folio, video_info=vid_data)

    alts_list = list(vid_data.get("alternatives") or []) if isinstance(vid_data, dict) else []
    if not alts_list and not st.session_state.get("_vid_alts_fetched_once"):
        st.session_state["_vid_alts_fetched_once"] = True
        _fresh_pack = buscar_video_relacionado_leccion(
            gramatica_b1,
            st.session_state.selected_cefr,
            st.session_state.generated_text,
            topic_context=topico_actual_leccion,
            max_videos=st.session_state["video_catalog_limit"]
        )
        curr_url_now = (vid_data or {}).get("url", "")
        existentes_urls = {curr_url_now}
        for cand_v in ([_fresh_pack] + list(_fresh_pack.get("alternatives") or [])):
            if cand_v.get("url") and cand_v.get("url") not in existentes_urls:
                alts_list.append(cand_v)
                existentes_urls.add(cand_v.get("url"))
        if isinstance(vid_data, dict):
            vid_data["alternatives"] = alts_list
            st.session_state["current_lesson_video"] = vid_data

    st.markdown(f"**Temática:** _{titulo_catalogo}_ (`{len(alts_list) + 1}` opciones)")
    with st.container(height=280, border=True):
        if not alts_list:
            st.caption("No hay videos alternativos cargados en este momento.")
        else:
            for idx_alt, alt_v in enumerate(alts_list, start=1):
                alt_title_safe = str(alt_v.get("title") or f"Video Relacionado {idx_alt}").replace("[", "(").replace("]", ")")
                alt_chan = str(alt_v.get("channel") or "YouTube ESL")
                alt_min = alt_v.get("duration_min", 5.0)
                alt_url = str(alt_v.get("url") or "")

                cv_txt, cv_btn = st.columns([3.4, 1.0])
                with cv_txt:
                    st.write(f"**{idx_alt}. {alt_title_safe}**")
                    st.caption(f"📺 {alt_chan} • ⏱️ `{alt_min} min`")
                with cv_btn:
                    if st.button("▶️ Reproducir Arriba", key=f"btn_pick_vid_{idx_alt}_{alt_url[-11:]}", width="stretch"):
                        nuevo_principal = dict(alt_v)
                        otras_alts = [v for v in alts_list if v.get("url") != alt_url]
                        if vid_data and vid_data.get("url"):
                            vieja_opcion = {k: v for k, v in vid_data.items() if k != "alternatives"}
                            otras_alts.insert(0, vieja_opcion)
                        nuevo_principal["alternatives"] = otras_alts

                        st.session_state["current_lesson_video"] = nuevo_principal
                        st.session_state["video_watched_sec"] = 0
                        st.session_state["video_score_100"] = 0.0
                        st.session_state["video_watch_started_ts"] = time.time()
                        st.session_state["viewing_center_stage"] = True
                        if st.session_state.current_folio:
                            save_video_and_summary_pg(folio_code=st.session_state.current_folio, video_info=nuevo_principal)
                        st.rerun()
                st.divider()

# ==============================================================================
# PARTE 17 — BLOQUE 2B (FINAL): MÁS OPCIONES DE VIDEO Y URL PROPIA (BOTÓN 2)
# ==============================================================================
    c_more1, c_more2 = st.columns([1.6, 1.8])
    with c_more1:
        if len(alts_list) < 19:
            if st.button("➕ Ver más opciones (hasta 20)", key="btn_load_more_videos", width="stretch"):
                with st.spinner("Cargando más videos sobre el tema y tópico..."):
                    st.session_state["video_catalog_limit"] = 20
                    mas_pack = buscar_video_relacionado_leccion(
                        gramatica_b1,
                        st.session_state.selected_cefr,
                        st.session_state.generated_text,
                        topic_context=topico_actual_leccion,
                        max_videos=20
                    )
                    curr_u = (vid_data or {}).get("url", "")
                    urls_ya = {curr_u} | {v.get("url") for v in alts_list}
                    for nv in ([mas_pack] + list(mas_pack.get("alternatives") or [])):
                        if nv.get("url") and nv.get("url") not in urls_ya and len(alts_list) < 19:
                            alts_list.append(nv)
                            urls_ya.add(nv.get("url"))
                    if isinstance(vid_data, dict):
                        vid_data["alternatives"] = alts_list
                        st.session_state["current_lesson_video"] = vid_data
                st.rerun()
        else:
            st.caption("✅ Catálogo completo (20 videos)")

    with c_more2:
        custom_yt_url = st.text_input(
            "🔗 Pegar enlace YouTube propio:",
            placeholder="https://youtube.com...",
            key="input_custom_yt_url",
            label_visibility="collapsed"
        )
        if custom_yt_url.strip() and ("youtube.com" in custom_yt_url or "youtu.be" in custom_yt_url):
            if st.button("🔄 Reproducir URL Pegada Arriba", key="btn_refresh_lesson_video", width="stretch"):
                m_id = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", custom_yt_url.strip())
                vid_id_c = m_id.group(1) if m_id else ""
                meta_c = _validar_video_oembed(vid_id_c) or {}
                vid_obj_new = {
                    "video_id": vid_id_c,
                    "url": custom_yt_url.strip(),
                    "title": meta_c.get("title") or f"({titulo_catalogo}) Custom Video",
                    "channel": meta_c.get("channel") or "YouTube Academic Resource",
                    "published_date": "2026",
                    "duration_sec": 300,
                    "duration_min": 5.0,
                    "alternatives": alts_list
                }
                st.session_state["current_lesson_video"] = vid_obj_new
                st.session_state["video_watched_sec"] = 0
                st.session_state["video_score_100"] = 0.0
                st.session_state["video_watch_started_ts"] = time.time()
                st.session_state["viewing_center_stage"] = True
                if st.session_state.current_folio:
                    save_video_and_summary_pg(folio_code=st.session_state.current_folio, video_info=vid_obj_new)
                st.rerun()

# ==============================================================================
# PARTE 17A: GRABADORA DE AUDIO Y VIDEO (SOLO ACTIVO EN BOTÓN 3 SPEAKING)
# ==============================================================================
if has_lesson_now and stage_5_now == "SPEAKING":
    st.subheader("🎤 Grabación de Lectura Oral y Evaluación Fonética con IA (25%)")
    tab_rec_audio, tab_rec_video = st.tabs(["🎤 Grabar Audio", "📹 Grabar Video"])

    with tab_rec_audio:
        student_audio = st.audio_input("Graba tu voz leyendo el texto:")
        if student_audio is not None:
            raw_aud = student_audio.getvalue()
            st.audio(raw_aud)
            c_aud1, c_aud2 = st.columns(2)
            with c_aud1:
                if st.button("💾 Guardar Audio en Folio", key="btn_save_student_audio_s3", width="stretch"):
                    with st.spinner("Guardando grabación en Supabase Storage..."):
                        try:
                            f_code = st.session_state.current_folio or "SIN-FOLIO"
                            usr_now = st.session_state.get("current_user") or "Estudiante"
                            public_u, err_u = upload_student_media_to_storage(
                                raw_aud, "audio/wav", "wav", f_code, usr_now
                            )
                            if err_u:
                                st.error(f"Error al subir audio: {err_u}")
                            else:
                                save_student_media_record_pg(
                                    f_code, usr_now, "audio", public_u, gramatica_b1, st.session_state.selected_cefr
                                )
                                st.success("✅ Audio guardado permanentemente en tu Folio.")
                        except Exception as e:
                            st.error(f"Error: {e}")

            with c_aud2:
                if st.button("🤖 Evaluar Pronunciación con IA (25%)", type="primary", key="btn_eval_student_audio_s3", width="stretch"):
                    with st.spinner("Analizando pronunciación, entonación y gramática oral con IA..."):
                        try:
                            ev_oral = evaluar_pronunciacion_oral_ia(
                                raw_aud,
                                "audio/wav",
                                st.session_state.generated_text,
                                st.session_state.selected_cefr,
                                gramatica_b1
                            )
                            st.session_state["speaking_eval_result"] = ev_oral
                            sc_pct = float(ev_oral.get("score_percent") or 0.0)
                            pts_25 = round((sc_pct / 100.0) * 25.0, 2)
                            f_code = st.session_state.current_folio or ""
                            usr_now = st.session_state.get("current_user") or "Estudiante"
                            if f_code:
                                public_u, _ = upload_student_media_to_storage(
                                    raw_aud, "audio/wav", "wav", f_code, usr_now
                                )
                                save_student_media_record_pg(
                                    f_code, usr_now, "audio", public_u or "", gramatica_b1,
                                    st.session_state.selected_cefr, eval_dict=ev_oral
                                )
                            st.success(f"🏆 **Calificación Oral:** {sc_pct}% (`{pts_25} / 25.0 pts`) — Nivel: **{ev_oral.get('cefr_performance', '')}**")
                            st.write(f"**🔤 Fonética y Articulación:** {ev_oral.get('phonetic_feedback', '')}")
                            st.write(f"**🎵 Fluidez y Prosodia:** {ev_oral.get('fluency_prosody', '')}")
                            st.write(f"**📐 Precisión Gramatical:** {ev_oral.get('grammar_accuracy', '')}")
                            if ev_oral.get("words_to_practice"):
                                st.info(f"🎯 **Palabras sugeridas para practicar:** {', '.join(ev_oral['words_to_practice'])}")
                        except Exception as e:
                            st.error(f"Error al evaluar pronunciación: {e}")

    with tab_rec_video:
        st.caption("📹 Graba o sube un video breve en formato MP4 / WebM leyendo o explicando la lección:")
        student_video_file = st.file_uploader(
            "Subir o grabar video desde cámara (MP4 / WebM / MOV):",
            type=["mp4", "webm", "mov"],
            key="uploader_student_video_s3"
        )
        if student_video_file is not None:
            raw_vid = student_video_file.getvalue()
            st.video(raw_vid)
            v_mime = student_video_file.type or "video/mp4"
            v_ext = "webm" if "webm" in v_mime else "mp4"
            c_vid1, c_vid2 = st.columns(2)
            with c_vid1:
                if st.button("💾 Guardar Video en Folio", key="btn_save_student_video_s3", width="stretch"):
                    with st.spinner("Guardando video en Supabase Storage..."):
                        try:
                            f_code = st.session_state.current_folio or "SIN-FOLIO"
                            usr_now = st.session_state.get("current_user") or "Estudiante"
                            public_v, err_v = upload_student_media_to_storage(
                                raw_vid, v_mime, v_ext, f_code, usr_now
                            )
                            if err_v:
                                st.error(f"Error al subir video: {err_v}")
                            else:
                                save_student_media_record_pg(
                                    f_code, usr_now, "video", public_v, gramatica_b1, st.session_state.selected_cefr
                                )
                                st.success("✅ Video guardado permanentemente en tu Folio.")
                        except Exception as e:
                            st.error(f"Error: {e}")

            with c_vid2:
                if st.button("🤖 Evaluar Video Oral con IA (25%)", type="primary", key="btn_eval_student_video_s3", width="stretch"):
                    with st.spinner("Evaluando desempeño oral en video con IA..."):
                        try:
                            ev_vid = evaluar_pronunciacion_oral_ia(
                                raw_vid,
                                v_mime,
                                st.session_state.generated_text,
                                st.session_state.selected_cefr,
                                gramatica_b1
                            )
                            st.session_state["speaking_eval_result"] = ev_vid
                            sc_vpct = float(ev_vid.get("score_percent") or 0.0)
                            pts_v25 = round((sc_vpct / 100.0) * 25.0, 2)
                            f_code = st.session_state.current_folio or ""
                            usr_now = st.session_state.get("current_user") or "Estudiante"
                            if f_code:
                                public_v, _ = upload_student_media_to_storage(
                                    raw_vid, v_mime, v_ext, f_code, usr_now
                                )
                                save_student_media_record_pg(
                                    f_code, usr_now, "video", public_v or "", gramatica_b1,
                                    st.session_state.selected_cefr, eval_dict=ev_vid
                                )
                            st.success(f"🏆 **Calificación Oral (Video):** {sc_vpct}% (`{pts_v25} / 25.0 pts`)")
                            st.write(f"**🔤 Fonética:** {ev_vid.get('phonetic_feedback', '')}")
                            st.write(f"**🎵 Fluidez:** {ev_vid.get('fluency_prosody', '')}")
                        except Exception as e:
                            st.error(f"Error al evaluar video: {e}")

    if st.session_state.get("speaking_eval_result"):
        ev_prev = st.session_state["speaking_eval_result"]
        with st.container(border=True):
            st.markdown(f"**📊 Última Calificación Registrada (25%):** `{ev_prev.get('score_percent', 0)}%` (`{round((float(ev_prev.get('score_percent', 0))/100.0)*25.0, 2)} / 25.0 pts`)")
            st.caption(ev_prev.get("phonetic_feedback", ""))

# ==============================================================================
# PARTE 18: AUDIO DEL QUIZ, DESCARGA MP3/PDF OFICIAL Y REINICIO (SOLO BOTÓN 1)
# ==============================================================================
has_lesson_p18 = bool(str(st.session_state.get("generated_text") or "").strip())
stage_5_p18 = st.session_state.get("active_stage_5", "READING")

if has_lesson_p18 and stage_5_p18 == "READING":
    if st.session_state.get("split_speaking_open"):
        aud_grabado = locals().get("student_audio")
        if aud_grabado is not None:
            safe_rec_name = f"CEI_Speaking_{st.session_state.current_folio or usuario.replace(' ', '_')}.mp3"
            try:
                import static_ffmpeg
                static_ffmpeg.add_paths()
                from pydub import AudioSegment

                wav_buf = io.BytesIO(aud_grabado.getvalue())
                audio_seg = AudioSegment.from_file(wav_buf, format="wav")
                mp3_buf = io.BytesIO()
                audio_seg.export(mp3_buf, format="mp3", bitrate="128k")
                mp3_data = mp3_buf.getvalue()
                dl_mime = "audio/mp3"
            except Exception:
                mp3_data = aud_grabado.getvalue()
                safe_rec_name = safe_rec_name.replace(".mp3", ".wav")
                dl_mime = "audio/wav"

            st.download_button(
                label="📥 Descargar Audio Grabado (MP3)",
                data=mp3_data,
                file_name=safe_rec_name,
                mime=dl_mime,
                type="secondary",
                width="stretch",
                key="btn_dl_recorded_mp3_p18"
            )

        if st.session_state.get("speaking_eval_result"):
            ev = st.session_state["speaking_eval_result"]
            with st.container(border=True):
                st.markdown(f"#### 🎯 Evaluación Oral Detallada: **{ev.get('score_percent', 0)}%** ({ev.get('cefr_performance', '')})")
                if ev.get("transcription"):
                    st.caption(f"🗣️ **Transcripción detectada:** *\"{ev.get('transcription', '')}\"*")
                st.markdown(f"**🔤 Fonética y Articulación:** {ev.get('phonetic_feedback', '')}")
                st.markdown(f"**🎵 Fluidez y Prosodia:** {ev.get('fluency_prosody', '')}")
                st.markdown(f"**📐 Precisión Gramatical Oral:** {ev.get('grammar_accuracy', '')}")
                tips = ev.get("actionable_tips", [])
                if tips:
                    st.markdown("**💡 Recomendaciones de Mejora:**")
                    for t in tips:
                        st.markdown(f"- {t}")

    # BOTONES DE AUDIO DEL QUIZ (DEBAJO DEL QUIZ Y ARRIBA DEL PDF OFICIAL)
    if st.session_state.quiz_data:
        st.divider()
        st.markdown("#### 🎧 Audio de Comprensión del Quiz (Inglés)")
        cq_aud1, cq_aud2 = st.columns(2)
        with cq_aud1:
            if st.button("🔊 Crear Audio del Quiz", type="secondary", width="stretch", key="btn_create_quiz_audio_p18"):
                with st.spinner("Sintetizando preguntas y opciones del Quiz en inglés..."):
                    try:
                        lineas_q_tts = []
                        for idx_q, item_q in enumerate(st.session_state.quiz_data, start=1):
                            q_txt = str(item_q.get("question") or "").strip()
                            opts_q = [str(o).strip() for o in (item_q.get("options") or [])]
                            lineas_q_tts.append(f"Question {idx_q}. {q_txt}. Options: {', '.join(opts_q)}.")
                        tts_q = gTTS(text=" ".join(lineas_q_tts), lang="en", slow=False)
                        q_buf = io.BytesIO()
                        tts_q.write_to_fp(q_buf)
                        st.session_state.quiz_audio_bytes = q_buf.getvalue()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al generar audio del quiz: {e}")

        with cq_aud2:
            if st.session_state.get("quiz_audio_bytes"):
                st.download_button(
                    label="📥 Descargar Audio del Quiz (MP3)",
                    data=st.session_state.quiz_audio_bytes,
                    file_name=f"CEI_Quiz_Audio_{st.session_state.current_folio or usuario.replace(' ', '_')}.mp3",
                    mime="audio/mp3",
                    type="primary",
                    width="stretch",
                    key="btn_dl_quiz_audio_p18"
                )
            else:
                st.button("📥 Descargar Audio del Quiz (MP3)", disabled=True, width="stretch", key="btn_dl_quiz_audio_disabled_p18")

        if st.session_state.get("quiz_audio_bytes"):
            st.audio(st.session_state.quiz_audio_bytes, format="audio/mp3")

    # DESCARGA DE PDF OFICIAL DE LA LECCIÓN
    st.divider()
    nota_actual_pdf = st.session_state.get("best_stored_score") or st.session_state.get("quiz_score")
    pdf_bytes = create_lesson_pdf(
        st.session_state.generated_text.replace("*", ""),
        quiz_items=st.session_state.quiz_data,
        user_ans=st.session_state.quiz_user_answers,
        score=nota_actual_pdf,
        speaking_eval=st.session_state.get("speaking_eval_result")
    )
    st.download_button(
        label=f"📥 Descargar PDF Oficial de la Lección ({st.session_state.current_folio or 'Lección'})",
        data=pdf_bytes,
        file_name=f"{st.session_state.current_folio or 'CEI_Lesson'}_{usuario.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary",
        width="stretch",
        key="btn_dl_pdf_official_stage"
    )

    # REINICIO DE AULA (EXCLUSIVO EN BOTÓN 1)
    st.divider()
    if st.button("🗑️ Borrar Todo", type="secondary", width="stretch", key="btn_clear_all_stage"):
        for k_reset in [
            "generated_text", "current_folio", "current_pdf_link", "current_creation_date",
            "best_stored_score", "video_summary_draft", "video_apa7_draft"
        ]:
            st.session_state[k_reset] = ""
        for k_none in [
            "image_bytes", "current_lesson_image", "current_motivational_quote", "last_img_error",
            "audio_bytes", "quiz_audio_bytes", "speaking_eval_result", "quiz_data", "quiz_score",
            "current_lesson_video", "video_watch_started_ts", "summary_eval_result"
        ]:
            st.session_state[k_none] = None
        for k_false in [
            "study_mode_active", "show_saved_audios", "quiz_graded", "url_folio_checked",
            "split_speaking_open", "split_writing_open", "show_lesson_creator"
        ]:
            st.session_state[k_false] = False
        st.session_state.quiz_user_answers = {}
        st.session_state["video_watched_sec"] = 0
        st.session_state["video_score_100"] = 0.0
        st.session_state["summary_score_100"] = 0.0
        st.session_state["active_stage_5"] = "READING"
        st.query_params.clear()
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

