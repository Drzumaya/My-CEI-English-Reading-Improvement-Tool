from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

TOTAL_PERIODOS_CURSO = 9
DIAS_POR_BLOQUE = 28


def calcular_desglose_iva(monto_base: float, iva_pct: float = 16.0, incluye_iva: bool = False) -> dict:
    """
    Calcula subtotal, monto de IVA y total con precisión financiera (2 decimales)
    adaptado a la tasa fiscal de cada plantel o escuela suscrita (campus_id).
    """
    base = Decimal(str(max(0.0, float(monto_base or 0.0))))
    tasa = Decimal(str(max(0.0, float(iva_pct or 0.0)))) / Decimal("100")

    if incluye_iva and tasa > 0:
        subtotal = (base / (Decimal("1") + tasa)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva_monto = (base - subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        subtotal = base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva_monto = (subtotal * tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + iva_monto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "subtotal": float(subtotal),
        "iva_pct": float(iva_pct or 0.0),
        "iva_monto": float(iva_monto),
        "total": float(total)
    }


def evaluar_estado_financiero_alumno(
    fecha_inicio_str: str,
    pagos_realizados: int,
    mensualidad_base: float,
    iva_pct: float = 16.0,
    recargo_mora_pct: float = 10.0,
    moneda: str = "MXN"
) -> dict:
    """
    Evalúa el avance de los 9 bloques de 28 días del estudiante, determina periodos vencidos,
    aplica recargos por mora si corresponde y calcula el saldo pendiente multi-divisa.
    """
    pagados = max(0, min(TOTAL_PERIODOS_CURSO, int(pagos_realizados or 0)))
    raw_fecha = str(fecha_inicio_str or "").strip()[:10]
    try:
        fecha_inicio = datetime.strptime(raw_fecha, "%Y-%m-%d").date()
    except ValueError:
        fecha_inicio = datetime.now().date()

    hoy = datetime.now().date()
    dias_transcurridos = max(0, (hoy - fecha_inicio).days)
    periodos_exigibles = min(TOTAL_PERIODOS_CURSO, (dias_transcurridos // DIAS_POR_BLOQUE) + 1)

    periodos_vencidos = max(0, periodos_exigibles - pagados)
    en_mora = periodos_vencidos > 0 and pagados < TOTAL_PERIODOS_CURSO

    desglose_normal = calcular_desglose_iva(mensualidad_base, iva_pct=iva_pct)
    factor_mora = Decimal("1") + (Decimal(str(max(0.0, float(recargo_mora_pct or 0.0)))) / Decimal("100"))
    monto_con_mora = float(
        (Decimal(str(desglose_normal["total"])) * factor_mora).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    ) if en_mora else desglose_normal["total"]

    saldo_pendiente = round(periodos_vencidos * monto_con_mora, 2)
    proximo_vencimiento = fecha_inicio + timedelta(days=pagados * DIAS_POR_BLOQUE)

    if pagados >= TOTAL_PERIODOS_CURSO:
        estatus = "Liquidado (9/9)"
    elif en_mora:
        estatus = f"Adeudo ({periodos_vencidos} bloque(s) vencido(s))"
    else:
        estatus = "Al Corriente"

    return {
        "estatus": estatus,
        "en_mora": en_mora,
        "pagos_realizados": pagados,
        "total_periodos": TOTAL_PERIODOS_CURSO,
        "periodos_exigibles": periodos_exigibles,
        "periodos_vencidos": periodos_vencidos,
        "cuota_normal": desglose_normal["total"],
        "cuota_actual": monto_con_mora,
        "saldo_pendiente": saldo_pendiente,
        "moneda": str(moneda or "MXN").strip().upper(),
        "proximo_vencimiento": proximo_vencimiento.strftime("%Y-%m-%d")
    }
