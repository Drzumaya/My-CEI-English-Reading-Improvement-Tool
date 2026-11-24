from datetime import datetime, timedelta
import urllib.parse

CEFR_LEVELS_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

CEFR_DESCRIPTIONS = {
    "A1": "Beginner — Basic everyday expressions, personal details, and simple interactions.",
    "A2": "Elementary — Routine tasks, familiar topics, and immediate practical needs.",
    "B1": "Intermediate — Main points on work, school, leisure, and connected narrative text.",
    "B2": "Upper-Intermediate — Complex texts, technical discussions, and spontaneous fluency.",
    "C1": "Advanced — Demanding academic/professional texts, implicit meaning, and structured argument.",
    "C2": "Proficiency — Near-native precision, nuanced synthesis, and scholarly expression."
}


def normalize_cefr_code(raw_level: str) -> str:
    """Extracts a clean canonical CEFR code (A1..C2) from any formatted label."""
    txt = str(raw_level or "B1").strip().upper()
    for code in CEFR_LEVELS_ORDER:
        if code in txt:
            return code
    return "B1"


def calcular_categoria_automatica_estudiante(
    folios_completados: int,
    promedio_global: float,
    racha_semanas: int = 0
) -> dict:
    """
    Determines the student's automatic academic category (Bronce, Plata, or Oro)
    based on completed folios, weighted average score (0-100), and consecutive weekly streak.
    """
    folios = max(0, int(folios_completados or 0))
    prom = max(0.0, min(100.0, float(promedio_global or 0.0)))
    racha = max(0, int(racha_semanas or 0))

    if folios >= 12 and prom >= 90.0 and racha >= 4:
        return {
            "categoria": "Oro",
            "badge": "🥇 Categoría Oro — Excelencia Académica CEI",
            "color": "#d97706",
            "siguiente_meta": "¡Nivel máximo alcanzado! Mantén tu racha semanal activa."
        }
    if folios >= 5 and prom >= 80.0:
        faltan_f = max(0, 12 - folios)
        faltan_r = max(0, 4 - racha)
        return {
            "categoria": "Plata",
            "badge": "🥈 Categoría Plata — Progreso Destacado CEI",
            "color": "#475569",
            "siguiente_meta": (
                f"Para Oro: completa {faltan_f} folios más, mantén promedio ≥ 90% "
                f"y {faltan_r} semanas extra de racha."
            )
        }
    faltan_f_plata = max(0, 5 - folios)
    return {
        "categoria": "Bronce",
        "badge": "🥉 Categoría Bronce — En Desarrollo Activo",
        "color": "#92400e",
        "siguiente_meta": f"Para Plata: completa {faltan_f_plata} folios más con promedio ≥ 80%."
    }


def calcular_racha_semanal(fechas_actividad: list[str]) -> dict:
    """
    Calculates consecutive active ISO study weeks up to the current week
    from a list of timestamp strings ('YYYY-MM-DD...').
    """
    semanas_activas = set()
    for f_str in (fechas_actividad or []):
        raw = str(f_str or "").strip()[:10]
        if not raw:
            continue
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d").date()
            iso_y, iso_w, _ = dt.isocalendar()
            semanas_activas.add((iso_y, iso_w))
        except ValueError:
            continue

    if not semanas_activas:
        return {"racha_actual": 0, "total_semanas": 0, "activo_esta_semana": False}

    hoy = datetime.now().date()
    curr_y, curr_w, _ = hoy.isocalendar()
    prev_dt = hoy - timedelta(days=7)
    prev_y, prev_w, _ = prev_dt.isocalendar()

    activo_hoy = (curr_y, curr_w) in semanas_activas
    cursor_dt = hoy if activo_hoy else (prev_dt if (prev_y, prev_w) in semanas_activas else None)

    racha = 0
    while cursor_dt is not None:
        cy, cw, _ = cursor_dt.isocalendar()
        if (cy, cw) in semanas_activas:
            racha += 1
            cursor_dt -= timedelta(days=7)
        else:
            break

    return {
        "racha_actual": racha,
        "total_semanas": len(semanas_activas),
        "activo_esta_semana": activo_hoy
    }


def build_whatsapp_motivation_link(
    telefono: str,
    nombre_estudiante: str,
    racha_semanas: int,
    categoria: str,
    app_url: str = "https://streamlit.app"
) -> str:
    """Generates a pre-filled WhatsApp motivation link for faculty or affiliate follow-up."""
    digits = "".join(ch for ch in str(telefono or "") if ch.isdigit())
    if len(digits) == 10:
        digits = f"52{digits}"
    if not digits:
        return ""

    nombre = str(nombre_estudiante or "Estudiante").strip()
    if racha_semanas > 0:
        msg = (
            f"¡Hola {nombre}! 👋 Te saludamos de *Career English Institute (CEI)*. "
            f"Felicidades por tu racha de *{racha_semanas} semana(s)* en *Categoría {categoria}* 🏅. "
            f"Continúa tu siguiente lección aquí: {app_url}"
        )
    else:
        msg = (
            f"¡Hola {nombre}! 👋 Te extrañamos en *Career English Institute (CEI)*. "
            f"Activa hoy tu racha semanal en *Categoría {categoria}* completando un Folio: {app_url}"
        )
    return f"https://wa.me{digits}?text={urllib.parse.quote(msg)}"
