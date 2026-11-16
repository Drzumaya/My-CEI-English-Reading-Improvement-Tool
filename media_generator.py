import base64
import io
import json
import re
import urllib.parse
import urllib.request
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
import streamlit as st


def generar_imagen_garantizada(client_gm, scene_prompt: str, folio_tag: str, cefr_lvl: str, academic_gr: str) -> bytes:
    # Genera ilustracion educativa (IA o fotografia tematica Wikimedia) y frase celebre motivacional
    st.session_state["last_img_error"] = None
    escena_limpia = re.sub(r'[^a-zA-Z0-9 ,.-]+', ' ', str(scene_prompt or "")).strip()
    escena_limpia = re.sub(r'\s+', ' ', escena_limpia)
    full_prompt = (
        "Create a clean, modern educational textbook illustration (no text or letters inside the image), "
        "bright natural lighting, expressive characters. Scene: " + escena_limpia
    )[:400]

    # 1. Genera Frase Celebre Motivacional + Palabras Clave Tematicas con Gemini Flash
    kw_busqueda = escena_limpia[:60] or "education library"
    if client_gm:
        try:
            prompt_q = (
                "Lesson scene/topic: '" + escena_limpia + "'. CEFR Level: " + str(cefr_lvl) + ".\n"
                "Respond ONLY in valid JSON with keys:\n"
                '{"keywords": "2-3 simple English nouns for photo search", '
                '"quote_en": "famous motivational quote in English related to topic", '
                '"author": "real author", '
                '"quote_es": "Spanish translation", '
                '"reflection": "one brief English sentence connecting quote to learning English"}'
            )
            r_q = client_gm.models.generate_content(model="gemini-2.5-flash", contents=prompt_q)
            raw_q = r_q.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            q_data = json.loads(raw_q)
            if isinstance(q_data, dict):
                if q_data.get("keywords"):
                    kw_busqueda = str(q_data["keywords"]).strip()
                st.session_state["current_motivational_quote"] = q_data
        except Exception:
            pass

    # 2. Intento con Gemini Image Generation
    if client_gm:
        for modelo_mm in ["gemini-2.5-flash-image", "gemini-2.0-flash-exp-image-generation"]:
            try:
                res = client_gm.models.generate_content(
                    model=modelo_mm,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
                )
                for cand in getattr(res, "candidates", []) or []:
                    for part in getattr(cand.content, "parts", []) or []:
                        inline = getattr(part, "inline_data", None)
                        if inline and getattr(inline, "data", None):
                            img_b = inline.data
                            if isinstance(img_b, str):
                                img_b = base64.b64decode(img_b)
                            if img_b and len(img_b) > 2000:
                                return img_b
            except Exception:
                pass

    # 3. Opcion B Gratuita e Ilimitada: Fotografia Educativa Real desde Wikimedia Commons
    try:
        kw_enc = urllib.parse.quote(kw_busqueda)
        wiki_api = (
            "https://wikimedia.org"
            "&gsrsearch=filetype:bitmap+" + kw_enc + "&gsrnamespace=6&gsrlimit=6"
            "&prop=imageinfo&iiprop=url&iiurlwidth=900&format=json"
        )
        req_w = urllib.request.Request(wiki_api, headers={"User-Agent": "CEI-Academic-App/1.0"})
        with urllib.request.urlopen(req_w, timeout=8) as rw:
            w_data = json.loads(rw.read().decode("utf-8"))
        q_obj = w_data.get("query") if isinstance(w_data, dict) else {}
        p_obj = q_obj.get("pages") if isinstance(q_obj, dict) else {}
        for p in list(p_obj.values()):
            ii_list = p.get("imageinfo") if isinstance(p, dict) else []
            ii = ii_list[0] if isinstance(ii_list, list) and len(ii_list) > 0 else {}
            t_url = ii.get("thumburl") or ii.get("url")
            if t_url and any(str(t_url).lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
                req_i = urllib.request.Request(t_url, headers={"User-Agent": "CEI-Academic-App/1.0"})
                with urllib.request.urlopen(req_i, timeout=8) as ri:
                    img_web = ri.read()
                if img_web and len(img_web) > 3000:
                    return img_web
    except Exception:
        pass

    # 4. Respaldo visual institucional en Pillow
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
