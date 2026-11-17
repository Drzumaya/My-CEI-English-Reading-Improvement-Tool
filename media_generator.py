import base64
import io
import json
import re
import urllib.parse
import urllib.request
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
import streamlit as st


def _fetch_real_topic_photo(keywords: str) -> bytes | None:
    """Obtiene una fotografía educativa real y gratuita desde Wikipedia / Wikimedia Commons."""
    clean_kw = re.sub(r"[^a-zA-Z0-9 ]+", " ", str(keywords or "")).strip()
    words = [w for w in clean_kw.split() if len(w) > 2][:3]
    queries = []
    if words:
        queries.append(" ".join(words[:2]))
        queries.append(words[0])
    queries.append("education study books")

    headers = {"User-Agent": "CEI-Academic-Portal/1.0 (https://careerenglish.edu; contact@careerenglish.edu)"}

    # 1. Wikipedia PageImages API (alta precisión en temas académicos y culturales)
    for q in queries:
        try:
            q_enc = urllib.parse.quote(q)
            wp_url = (
                "https://wikipedia.org"
                "&gsrsearch=" + q_enc + "&gsrlimit=5&prop=pageimages&pithumbsize=900&format=json"
            )
            req = urllib.request.Request(wp_url, headers=headers)
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            pages = list((data.get("query") or {}).get("pages", {}).values())
            for p in pages:
                thumb = (p.get("thumbnail") or {}).get("source")
                if thumb and any(thumb.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
                    req_i = urllib.request.Request(thumb, headers=headers)
                    with urllib.request.urlopen(req_i, timeout=7) as ri:
                        img_data = ri.read()
                    if img_data and len(img_data) > 4000:
                        return img_data
        except Exception:
            continue

    # 2. Respaldo en Wikimedia Commons
    for q in queries:
        try:
            q_enc = urllib.parse.quote(q)
            cm_url = (
                "https://wikimedia.org"
                "&gsrsearch=filetype:bitmap+" + q_enc + "&gsrnamespace=6&gsrlimit=5"
                "&prop=imageinfo&iiprop=url&iiurlwidth=900&format=json"
            )
            req = urllib.request.Request(cm_url, headers=headers)
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            pages = list((data.get("query") or {}).get("pages", {}).values())
            for p in pages:
                ii_list = p.get("imageinfo") or []
                ii = ii_list[0] if ii_list else {}
                t_url = ii.get("thumburl") or ii.get("url")
                if t_url and any(str(t_url).lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
                    req_i = urllib.request.Request(t_url, headers=headers)
                    with urllib.request.urlopen(req_i, timeout=7) as ri:
                        img_data = ri.read()
                    if img_data and len(img_data) > 4000:
                        return img_data
        except Exception:
            continue

    return None


def generar_imagen_garantizada(client_gm, scene_prompt: str, folio_tag: str, cefr_lvl: str, academic_gr: str) -> bytes:
    """Genera fotografía temática real acorde al tópico y frase célebre motivacional bilingüe."""
    st.session_state["last_img_error"] = None
    escena_limpia = re.sub(r"[^a-zA-Z0-9 ,.-]+", " ", str(scene_prompt or "")).strip()
    escena_limpia = re.sub(r"\s+", " ", escena_limpia)

    topico_activo = str(st.session_state.get("current_topic") or escena_limpia[:60] or "education").strip()
    kw_busqueda = topico_activo

    # 1. Genera Frase Célebre Motivacional + Palabras Clave Visuales con Gemini Flash
    if client_gm:
        try:
            prompt_q = (
                "Topic: '" + topico_activo + "'. Scene: '" + escena_limpia[:180] + "'. CEFR: " + str(cefr_lvl) + ".\n"
                "Respond ONLY in valid JSON with keys:\n"
                '{"keywords": "2 simple English nouns for Wikipedia photo search", '
                '"quote_en": "famous motivational quote in English related to topic", '
                '"author": "real author", '
                '"quote_es": "Spanish translation", '
                '"reflection": "one brief English sentence connecting quote to learning English"}'
            )
            r_q = client_gm.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_q,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.5)
            )
            raw_q = str(r_q.text or "").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            q_data = json.loads(raw_q)
            if isinstance(q_data, dict):
                if q_data.get("keywords"):
                    kw_busqueda = str(q_data["keywords"]).strip()
                st.session_state["current_motivational_quote"] = q_data
        except Exception:
            pass

    # 2. Fotografía Educativa Real desde Wikipedia / Wikimedia Commons (100% gratuita y sin límite de cuota)
    foto_real = _fetch_real_topic_photo(kw_busqueda)
    if foto_real:
        return foto_real

    # 3. Respaldo visual institucional en Pillow (solo si no hay conexión externa)
    w, h = 800, 420
    img = Image.new("RGB", (w, h), color=(18, 36, 66))
    draw = ImageDraw.Draw(img)
    draw.rectangle([14, 14, w - 14, h - 14], outline=(212, 175, 55), width=4)
    draw.rectangle([28, 28, w - 28, 92], fill=(30, 56, 98))
    font_std = ImageFont.load_default()
    banner_txt = "CAREER ENGLISH INSTITUTE  |  " + str(folio_tag) + "  |  CEFR " + str(cefr_lvl)
    draw.text((46, 50), banner_txt, fill=(255, 223, 128), font=font_std)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
