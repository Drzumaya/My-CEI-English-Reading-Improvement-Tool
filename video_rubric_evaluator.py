import json
import re
import streamlit as st

VIDEO_CRITERIA_BY_CEFR = {
    "A1-A2": {
        "etiqueta": "Nivel A1 – A2",
        "actividad": "Resumen de video en inglés",
        "min_words": 50,
        "max_words": 100,
        "instruccion": "Mira el video con atención y escribe un resumen en inglés de 50 a 100 palabras.",
        "que_incluir": "El tema principal, quién habla o aparece y 2 o 3 datos clave.",
        "consejos": "Usa oraciones cortas y claras en presente o pasado simple (present/past simple), e incluye conectores básicos (and, but, because, first, then).",
        "importante": "Escribe con tus propias palabras (sin usar traductores ni IA) y verifica el contador de palabras antes de enviar tu entrega."
    },
    "B1-B2": {
        "etiqueta": "Nivel B1 – B2",
        "actividad": "Síntesis de video en inglés",
        "min_words": 120,
        "max_words": 180,
        "instruccion": "Analiza el video asignado y redacta un resumen estructurado en inglés de 120 a 180 palabras.",
        "que_incluir": "La idea central, los argumentos secundarios más relevantes y las causas o consecuencias mencionadas.",
        "consejos": "Organiza tu texto en 2 párrafos usando conectores de secuencia y contraste (however, furthermore, therefore). Evita copiar frases literales del audio; usa sinónimos y paráfrasis.",
        "importante": "Respeta estrictamente el límite de palabras (mínimo 120, máximo 180) y redacta sin ayuda de traductores o IA."
    },
    "C1-C2": {
        "etiqueta": "Nivel C1 – C2",
        "actividad": "Síntesis crítica de video en inglés",
        "min_words": 200,
        "max_words": 300,
        "instruccion": "Elabora una síntesis objetiva y concisa del video en inglés dentro de un rango estricto de 200 a 300 palabras.",
        "que_incluir": "La tesis principal, los argumentos clave que la sustentan, el tono o postura del hablante y las conclusiones implicadas.",
        "consejos": "Demuestra capacidad de abstracción y reformulación léxica avanzada. No transcribas expresiones del video ni excedas el límite máximo, ya que la concisión forma parte de tu calificación.",
        "importante": "El texto debe ser de autoría 100% propia (sin traductores ni herramientas de IA)."
    }
}


def obtener_criterios_video_nivel(cefr_code: str) -> dict:
    c = str(cefr_code or "B1").strip().upper()
    if c.startswith("A"):
        return VIDEO_CRITERIA_BY_CEFR["A1-A2"]
    if c.startswith("C"):
        return VIDEO_CRITERIA_BY_CEFR["C1-C2"]
    return VIDEO_CRITERIA_BY_CEFR["B1-B2"]


def render_criterios_video_plegable(cefr_code: str):
    """Despliega únicamente los criterios del nivel MCER actual en modo plegable debajo del video (Botón 2)."""
    crit = obtener_criterios_video_nivel(cefr_code)
    with st.expander(
        f"📋 Instrucciones y Criterios del Resumen ({crit['etiqueta']} • {crit['min_words']}–{crit['max_words']} palabras)",
        expanded=False
    ):
        st.markdown(f"**Actividad:** {crit['actividad']}")
        st.markdown(crit["instruccion"])
        st.markdown(f"- **Qué incluir:** {crit['que_incluir']}")
        st.markdown(f"- **Consejos:** {crit['consejos']}")
        st.markdown(f"- **Importante:** {crit['importante']}")


def render_rubrica_video_plegable():
    """Despliega la rúbrica oficial de 20 puntos (20%) justo arriba del Botón 4."""
    with st.expander("📊 Rúbrica Oficial de Evaluación de Síntesis de Video (20 puntos / 20%)", expanded=False):
        st.markdown(
            "| Criterios | Excelente (5 pts / 5%) | Satisfactorio (3.5 pts / 3.5%) | En desarrollo (2 pts / 2%) | Insuficiente (1 pt / 1%) |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **Comprensión y síntesis** | Identifica con precisión la idea central y los puntos clave sin omitir información esencial ni añadir detalles irrelevantes. | Identifica la idea principal, aunque omite algún punto secundario o incluye detalles innecesarios. | Comprensión parcial del video; el resumen es confuso o se centra solo en detalles aislados. | No logra identificar el tema central o malinterpreta el contenido del video. |\n"
            "| **Paráfrasis y originalidad** | Reformula las ideas completamente con sus propias palabras utilizando vocabulario adecuado a su nivel. | Parafrasea la mayor parte del texto, aunque repite algunas expresiones literales del video. | Depende en exceso de frases copiadas o transcritas directamente del audio o los subtítulos. | El texto es una transcripción literal palabra por palabra del video sin elaboración propia. |\n"
            "| **Cohesión y gramática** | Texto bien estructurado, con conectores adecuados al nivel y sin errores que afecten la claridad. | Buena estructura general; contiene errores menores de gramática u ortografía que no impiden la lectura. | Uso limitado de conectores; errores frecuentes de gramática o puntuación que dificultan la comprensión. | Texto desorganizado y sin cohesión, con errores graves que impiden entender el mensaje. |\n"
            "| **Cumplimiento de extensión** | Cumple estrictamente con el rango de palabras solicitado para su nivel del MCER. | Se desvía ligeramente del rango permitido (hasta un 10% por encima o por debajo del límite). | Se desvía significativamente del rango (entre un 15% y 25% fuera del límite). | No alcanza la extensión mínima o excede ampliamente el máximo (más del 25% fuera de rango). |"
        )


def _init_gm_local():
    import os
    from google import genai
    api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("No se encontró GEMINI_API_KEY en Secrets.")
    return genai.Client(api_key=api_key)


def evaluar_resumen_video_rubrica_ia(
    student_summary: str,
    lesson_reference: str,
    cefr_code: str,
    grammar_topic: str = ""
) -> dict:
    """Evalúa el resumen del video sobre 20 puntos (20%) aplicando la rúbrica oficial por nivel MCER."""
    from google.genai import types

    crit = obtener_criterios_video_nivel(cefr_code)
    texto_limpio = str(student_summary or "").strip()
    palabras = [w for w in re.findall(r"\b[\w'-]+\b", texto_limpio) if w]
    word_count = len(palabras)
    min_w, max_w = crit["min_words"], crit["max_words"]

    if min_w <= word_count <= max_w:
        pts_ext = 5.0
        nivel_ext = "Excelente (5 pts)"
    elif int(min_w * 0.90) <= word_count <= int(max_w * 1.10):
        pts_ext = 3.5
        nivel_ext = "Satisfactorio (3.5 pts)"
    elif int(min_w * 0.75) <= word_count <= int(max_w * 1.25):
        pts_ext = 2.0
        nivel_ext = "En desarrollo (2 pts)"
    else:
        pts_ext = 1.0
        nivel_ext = "Insuficiente (1 pt)"

    gm = _init_gm_local()
    prompt_rubrica = f"""
    You are an expert CEFR English writing & video comprehension evaluator at Career English Institute (CEI).
    Evaluate the student's English summary using the official 20-point rubric for {crit['etiqueta']} ({min_w}-{max_w} words).

    Reference lesson / video topic context:
    {str(lesson_reference or '')[:2200]}

    Target Grammar: {grammar_topic}
    Student Word Count: {word_count} words (Required range: {min_w}-{max_w} words; Pre-calculated extension score: {pts_ext}/5.0).
    Student Summary:
    \"\"\"{texto_limpio}\"\"\"

    Score each of the first three criteria strictly using ONLY one of these exact point values: 5.0, 3.5, 2.0, or 1.0:
    1. Comprension y sintesis (5.0 = Excelente, 3.5 = Satisfactorio, 2.0 = En desarrollo, 1.0 = Insuficiente)
    2. Parafrasis y originalidad (5.0 = Excelente, 3.5 = Satisfactorio, 2.0 = En desarrollo, 1.0 = Insuficiente)
    3. Cohesion y gramatica (5.0 = Excelente, 3.5 = Satisfactorio, 2.0 = En desarrollo, 1.0 = Insuficiente)

    Respond in clear, constructive Spanish in the feedback fields. Return ONLY a valid JSON object:
    {{
      "comprension_pts": 5.0,
      "comprension_nivel": "Excelente",
      "comprension_feedback": "Retroalimentación específica sobre comprensión e ideas clave.",
      "parafrasis_pts": 3.5,
      "parafrasis_nivel": "Satisfactorio",
      "parafrasis_feedback": "Retroalimentación específica sobre reformulación léxica y originalidad.",
      "cohesion_pts": 5.0,
      "cohesion_nivel": "Excelente",
      "cohesion_feedback": "Retroalimentación específica sobre conectores, estructura y gramática del nivel.",
      "extension_feedback": "Retroalimentación específica sobre el conteo de {word_count} palabras frente al rango {min_w}-{max_w}.",
      "fortalezas": ["Fortaleza 1", "Fortaleza 2"],
      "areas_mejora": ["Acción concreta de mejora 1", "Acción concreta de mejora 2"],
      "ejemplo_apertura_20pts": "Ejemplo modelo en inglés (2-3 oraciones) calibrado a {crit['etiqueta']} sobre este video para obtener 20/20 puntos.",
      "ejemplo_parafrasis_20pts": "Ejemplo concreto en español/inglés: 'Frase simple' -> 'Versión académica mejorada de nivel {crit['etiqueta']}'."
    }}
    """

    modelos_eval = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.1-pro-preview", "gemini-3.0-flash"]
    excluidos = ("2.5", "2.0", "1.5", "embedding", "imagen", "tts", "audio", "robotics", "computer-use", "lyria", "veo")
    try:
        for m in gm.models.list():
            m_name = str(getattr(m, "name", "")).replace("models/", "").strip()
            if "gemini" in m_name and not any(ex in m_name for ex in excluidos) and m_name not in modelos_eval:
                modelos_eval.append(m_name)
    except Exception:
        pass

    ultimo_err = ""
    for mod in modelos_eval:
        try:
            resp = gm.models.generate_content(
                model=mod,
                contents=prompt_rubrica,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2)
            )
            raw = re.sub(r"^```(?:json)?|```$", "", str(getattr(resp, "text", "") or "").strip(), flags=re.MULTILINE).strip()
            m_obj = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if m_obj:
                raw = m_obj.group(0)
            data = json.loads(raw)

            valid_scores = (5.0, 3.5, 2.0, 1.0)
            c_pts = min(valid_scores, key=lambda x: abs(x - float(data.get("comprension_pts", 3.5))))
            p_pts = min(valid_scores, key=lambda x: abs(x - float(data.get("parafrasis_pts", 3.5))))
            g_pts = min(valid_scores, key=lambda x: abs(x - float(data.get("cohesion_pts", 3.5))))
            total_20 = round(c_pts + p_pts + g_pts + pts_ext, 2)
            score_100 = round((total_20 / 20.0) * 100.0, 1)

            return {
                "total_20": total_20,
                "score_100": score_100,
                "word_count": word_count,
                "rango_esperado": f"{min_w}–{max_w} palabras ({crit['etiqueta']})",
                "comprension_pts": c_pts,
                "comprension_nivel": str(data.get("comprension_nivel") or ""),
                "comprension_feedback": str(data.get("comprension_feedback") or ""),
                "parafrasis_pts": p_pts,
                "parafrasis_nivel": str(data.get("parafrasis_nivel") or ""),
                "parafrasis_feedback": str(data.get("parafrasis_feedback") or ""),
                "cohesion_pts": g_pts,
                "cohesion_nivel": str(data.get("cohesion_nivel") or ""),
                "cohesion_feedback": str(data.get("cohesion_feedback") or ""),
                "extension_pts": pts_ext,
                "extension_nivel": nivel_ext,
                "extension_feedback": str(data.get("extension_feedback") or f"Escribiste {word_count} palabras (rango solicitado: {min_w}–{max_w})."),
                "fortalezas": list(data.get("fortalezas") or []),
                "areas_mejora": list(data.get("areas_mejora") or []),
                "ejemplo_apertura_20pts": str(data.get("ejemplo_apertura_20pts") or ""),
                "ejemplo_parafrasis_20pts": str(data.get("ejemplo_parafrasis_20pts") or "")
            }
        except Exception as e_m:
            ultimo_err = f"{mod}: {e_m}"
            continue

    raise RuntimeError(f"No se pudo evaluar el resumen con la rúbrica: {ultimo_err}")
GLOBAL_PEDAGOGICAL_RESOURCES = {
    "A1-A2": [
        ("📘 British Council — A1/A2 Reading & Short Summaries", "https://britishcouncil.org"),
        ("📗 Cambridge English — Basic Connectors & Sentence Structure", "https://cambridgeenglish.org"),
        ("🎬 BBC Learning English — 6 Minute English (Listening & Vocabulary)", "https://bbc.co.uk"),
    ],
    "B1-B2": [
        ("📘 British Council — B1/B2 Structured Summaries & Essays", "https://britishcouncil.org"),
        ("📙 Purdue OWL — Paraphrasing & Summarizing Academic Sources", "https://purdue.edu"),
        ("🎬 TED-Ed — Interactive Lessons & Comprehension Quizzes", "https://ted.com"),
    ],
    "C1-C2": [
        ("📕 Harvard College Writing Center — Academic Synthesis & Rhetoric", "https://harvard.edu"),
        ("📘 British Council — C1 Advanced Critical Reading & Synthesis", "https://britishcouncil.org"),
        ("🎓 MIT OpenCourseWare — Advanced Academic Communication", "https://mit.edu"),
    ],
}


def render_resultado_rubrica_video(res_rub: dict, cefr_code: str = "B1"):
    """Muestra calificación sobre 20 pts, ejemplos para lograr el 100%, lecturas globales con enlaces y botón Try again."""
    c = str(cefr_code or "B1").strip().upper()
    grupo = "A1-A2" if c.startswith("A") else ("C1-C2" if c.startswith("C") else "B1-B2")
    recursos = GLOBAL_PEDAGOGICAL_RESOURCES[grupo]

    with st.container(border=True):
        st.markdown(
            f"#### 🏆 Calificación de Síntesis de Video: **{res_rub['total_20']} / 20.0 pts** "
            f"(`{res_rub['score_100']}%`) • Conteo: **{res_rub['word_count']} palabras** ({res_rub['rango_esperado']})"
        )
        st.markdown(f"- **1. Comprensión y síntesis ({res_rub['comprension_pts']} / 5 pts — {res_rub['comprension_nivel']}):** {res_rub['comprension_feedback']}")
        st.markdown(f"- **2. Paráfrasis y originalidad ({res_rub['parafrasis_pts']} / 5 pts — {res_rub['parafrasis_nivel']}):** {res_rub['parafrasis_feedback']}")
        st.markdown(f"- **3. Cohesión y gramática ({res_rub['cohesion_pts']} / 5 pts — {res_rub['cohesion_nivel']}):** {res_rub['cohesion_feedback']}")
        st.markdown(f"- **4. Cumplimiento de extensión ({res_rub['extension_pts']} / 5 pts — {res_rub['extension_nivel']}):** {res_rub['extension_feedback']}")

        if res_rub.get("fortalezas"):
            st.markdown("**✅ Fortalezas detectadas:** " + " | ".join(res_rub["fortalezas"]))

        if res_rub.get("areas_mejora"):
            st.markdown("**💡 Recomendaciones para mejorar:**")
            for tip in res_rub["areas_mejora"]:
                st.markdown(f"- {tip}")

        if res_rub.get("ejemplo_apertura_20pts") or res_rub.get("ejemplo_parafrasis_20pts"):
            with st.expander("🌟 Ejemplos Modelo para Lograr 20 / 20 pts (100%)", expanded=True):
                if res_rub.get("ejemplo_apertura_20pts"):
                    st.markdown(f"**✍️ Ejemplo de redacción de alto nivel sobre este video:**\n> *{res_rub['ejemplo_apertura_20pts']}*")
                if res_rub.get("ejemplo_parafrasis_20pts"):
                    st.markdown(f"**🔄 Mejora de paráfrasis y vocabulario:**\n> {res_rub['ejemplo_parafrasis_20pts']}")

        with st.expander(f"🌍 Lecturas y Recursos Pedagógicos Globales ({grupo})", expanded=False):
            for titulo_rec, url_rec in recursos:
                st.markdown(f"- [{titulo_rec}]({url_rec})")

        st.markdown("---")
        nonce_w = int(st.session_state.get("writing_attempt_nonce", 0))
        if st.button(
            "🔄 Try again / Intentar de nuevo (Aplicar mejoras y volver a calificar)",
            type="secondary",
            width="stretch",
            key=f"btn_try_again_writing_{nonce_w}"
        ):
            st.session_state.pop("video_rubric_result", None)
            st.session_state["writing_attempt_nonce"] = nonce_w + 1
            st.rerun()
def render_live_word_counter(res_text: str, min_w: int, max_w: int, label_nivel: str):
    """Muestra y actualiza el conteo de palabras tecla por tecla en tiempo real."""
    import streamlit.components.v1 as components

    cnt = len([w for w in re.findall(r"\b[\w'-]+\b", str(res_text or "").strip()) if w])
    ok = min_w <= cnt <= max_w
    bg = "#dcfce7" if ok else "#fef9c3"
    bd = "#22c55e" if ok else "#eab308"
    tx = "#166534" if ok else "#854d0e"
    msg = (
        f"✅ Conteo en vivo: <strong>{cnt} palabras</strong> (rango válido {label_nivel}: {min_w}–{max_w})."
        if ok else f"📏 Conteo en vivo: <strong>{cnt} palabras</strong> (rango requerido {label_nivel}: {min_w}–{max_w} palabras)."
    )
    components.html(
        f"""
        <div id="liveWordBadge" style="font-family:sans-serif;font-size:13.5px;padding:10px 14px;
             border-radius:10px;background:{bg};border:1.5px solid {bd};color:{tx};">{msg}</div>
        <script>
          (function() {{
            const minW = {min_w}, maxW = {max_w}, lbl = "{label_nivel}";
            const badge = document.getElementById("liveWordBadge");
            function bind() {{
              const areas = window.parent.document.querySelectorAll('textarea');
              let ta = Array.from(areas).find(t => (t.placeholder || '').toLowerCase().includes('academic summary in english'));
              if (!ta) return setTimeout(bind, 300);
              const upd = () => {{
                const m = (ta.value || '').trim().match(/\\b[\\w'-]+\\b/g);
                const c = m ? m.length : 0;
                const v = c >= minW && c <= maxW;
                badge.style.background = v ? "#dcfce7" : "#fef9c3";
                badge.style.borderColor = v ? "#22c55e" : "#eab308";
                badge.style.color = v ? "#166534" : "#854d0e";
                badge.innerHTML = (v ? "✅ Conteo en vivo: <strong>" : "📏 Conteo en vivo: <strong>") +
                  c + " palabras</strong> (" + (v ? "rango válido " : "rango requerido ") + lbl + ": " + minW + "–" + maxW + ").";
              }};
              if (!ta.dataset.ceiBound) {{
                ta.dataset.ceiBound = "1";
                ta.addEventListener("input", upd);
                ta.addEventListener("paste", () => setTimeout(upd, 30));
              }}
              upd();
            }}
            bind();
          }})();
        </script>
        """,
        height=52
    )
