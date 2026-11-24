from core.ai_engine import build_contextual_apa7_lesson_prompt
from modules.finance import calcular_desglose_iva, evaluar_estado_financiero_alumno


def test_calcular_desglose_iva():
    res = calcular_desglose_iva(1000.0, iva_pct=16.0, incluye_iva=False)
    assert res["subtotal"] == 1000.0
    assert res["iva_monto"] == 160.0
    assert res["total"] == 1160.0


def test_evaluar_estado_financiero_liquidado():
    st_fin = evaluar_estado_financiero_alumno("2026-01-01", pagos_realizados=9, mensualidad_base=1200.0)
    assert st_fin["en_mora"] is False
    assert st_fin["saldo_pendiente"] == 0.0
    assert "Liquidado" in st_fin["estatus"]


def test_build_contextual_apa7_lesson_prompt():
    p = build_contextual_apa7_lesson_prompt(
        usuario_login="vicente01",
        borrador_usuario="quiero aprender ingles para trabajar en aduana en agua prieta",
        cefr_form="B1",
        grado_form="Licenciatura",
        lugar_form="Agua Prieta, Sonora"
    )
    assert "B1" in p
    assert "Agua Prieta, Sonora" in p
    assert "APA 7" in p
 
