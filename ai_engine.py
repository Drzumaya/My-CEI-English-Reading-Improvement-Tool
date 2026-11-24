import os
from google import genai
import streamlit as st
from modules.pedagogy import normalize_cefr_code

DEFAULT_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def get_gemini_api_key() -> str:
    """Obtiene la llave API de Google Gemini desde Streamlit Secrets o variables de entorno."""
    try:
        direct = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        if direct:
            return direct
        for sec in st.secrets.values():
            if isinstance(sec, dict) and str(sec.get("GEMINI_API_KEY", "")).strip():
                return str(sec["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    return str(os.environ.get("GEMINI_API_KEY", "")).strip()


def build_contextual_apa7_lesson_prompt(
    usuario_login: str,
    borrador_usuario: str,
    cefr_form: str = "B1",
    grado_form: str = "Licenciatura / Universidad",
    lugar_form: str = "Agua Prieta, Sonora, Mexico",
    contexto_form: str = "Academic and Professional Communication",
    asunto_form: str = "",
    campus_nombre: str = "Career English Institute (CEI)",
    extras_form: str = ""
) -> str:
    """
    Construye el prompt maestro APA 7th Edition que honra fielmente la idea/borrador del estudiante
    (sin importar errores iniciales) y la adapta a su perfil de inscripción y sede multi-tenant.
    """
    nivel_final = normalize_cefr_code(cefr_form)
    grado_final = str(grado_form or "Licenciatura / Universidad").strip()
    lugar_final = str(lugar_form or "Agua Prieta, Sonora, Mexico").strip()
    contexto_final = str(contexto_form or "Academic and Professional Communication").strip()
    asunto_final = str(asunto_form or "").strip()
    institucion_final = str(campus_nombre or "Career English Institute (CEI)").strip()

    return f"""
You are an expert English language educator and APA 7th Edition academic editor at {institucion_final}.

=== STUDENT ENROLLMENT PROFILE & MULTI-TENANT CONTEXT ===
- Student Identifier: {usuario_login}
- Target English Proficiency (CEFR): {nivel_final}
- Academic Level / Degree: {grado_final}
- Geographic / Cultural Setting: {lugar_final}
- Professional / Personal Context: {contexto_final}
- Subject / Focus Area: {asunto_final or "Derived from student draft"}
- Additional Form Parameters: {extras_form or "Standard CEI curriculum"}

=== STUDENT'S RAW IDEA / DRAFT INPUT (THEMATIC GUIDE) ===
\"\"\"{borrador_usuario}\"\"\"

=== MANDATORY PEDAGOGICAL & APA 7TH EDITION RULES ===
1. HONOR THE STUDENT'S IDEA: Treat the student's raw input as the core thematic guide. Even if it contains spelling mistakes, grammar errors, Spanish words, or Spanglish, preserve their exact message, examples, and intent—never replace their idea with an unrelated generic topic.
2. CONTEXTUAL ADAPTATION: Tailor vocabulary, examples, and tone to fit their enrollment profile ({grado_final}, {contexto_final}, {lugar_final}) while strictly matching CEFR level {nivel_final}.
3. APA 7TH EDITION STYLING:
   - Line 1 MUST be a polished, concise APA 7 Title Case heading (`# Title`) that faithfully elevates the student's topic.
   - Body paragraphs must follow objective, formal, bias-free APA 7 academic writing conventions.
   - End with a `## Bibliography` section containing 2 to 3 real, verifiable APA 7th Edition references supporting the student's topic and context.
4. Do not criticize or lecture about the student's input errors inside the reading text; deliver a seamless, inspiring model text ready for reading, audio synthesis, and comprehension assessment.
""".strip()


def generate_lesson_text_gemini(prompt_text: str, models: list[str] | None = None) -> str:
    """Ejecuta la generación de texto con fallback automático entre modelos Gemini."""
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("Falta configurar GEMINI_API_KEY en Secrets.")
    client = genai.Client(api_key=api_key)
    last_err = None
    for model_name in (models or DEFAULT_GEMINI_MODELS):
        try:
            resp = client.models.generate_content(model=model_name, contents=prompt_text)
            txt = str(getattr(resp, "text", "") or "").strip()
            if txt:
                return txt
        except Exception as e:
            last_err = e
    raise RuntimeError(f"No se pudo generar contenido con Gemini: {last_err}")
