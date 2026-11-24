from core.database import get_user_delegated_caps_pg, save_user_delegated_caps_pg
from modules.franchises import DEFAULT_CAMPUS_ID, list_campuses_pg, upsert_campus_pg


def test_default_campus_id():
    assert DEFAULT_CAMPUS_ID == "CEI-AP-01"


def test_delegated_caps_empty_user_safe():
    assert get_user_delegated_caps_pg("") == {}
    ok, msg = save_user_delegated_caps_pg("", {"Emitir_Certificados": True}, "Owner")
    assert ok is False
    assert "inválido" in msg.lower()


def test_upsert_campus_validation():
    ok, msg = upsert_campus_pg("", "", "Hermosillo", "Calle 1")
    assert ok is False
    assert "obligatorios" in msg.lower()


def test_list_campuses_fallback():
    sedes = list_campuses_pg("Agua Prieta, Sonora")
    assert isinstance(sedes, list)
    assert len(sedes) >= 1
    assert sedes[0]["campus_id"] == "CEI-AP-01"
