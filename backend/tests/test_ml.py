"""Capa 4: el imputador se sirve con Singleton, predice con la fórmula del JSON y guarda cada
predicción en la base."""
import json
from pathlib import Path

import pytest

from app.config import Settings, get_settings
from app.ml.predictor import ImputadorEscrita

PERFIL = {"ciudadanas": 150, "ingles": 160, "lectura_critica": 155, "razonamiento": 148, "anio": 2024}


def test_predict_usa_la_formula_del_modelo(client):
    meta = json.loads(Path(get_settings().modelo_imputador).read_text(encoding="utf-8"))
    c = meta["coeficientes"]
    esperado = meta["intercepto"] + sum(c[k] * PERFIL[k] for k in ("ciudadanas", "ingles", "lectura_critica",
                                                                    "razonamiento")) + c["anio_2024"]
    r = client.post("/predict", json=PERFIL)
    assert r.status_code == 201
    p = r.json()
    assert p["escrita_predicha"] == pytest.approx(esperado, abs=0.05)
    assert p["intervalo_95"]["inf"] < p["intervalo_80"]["inf"] < p["escrita_predicha"] < p["intervalo_80"]["sup"]
    assert p["global_estimado"] == pytest.approx((150 + 160 + 155 + 148 + p["escrita_predicha"]) / 5, abs=0.01)


def test_cada_prediccion_queda_guardada(client):
    antes = len(client.get("/predict/historial", params={"limite": 500}).json())
    id_nuevo = client.post("/predict", json=PERFIL).json()["id_prediccion"]
    hist = client.get("/predict/historial", params={"limite": 500}).json()
    assert len(hist) == antes + 1 and hist[0]["id"] == id_nuevo


def test_singleton_carga_una_sola_vez():
    ruta = get_settings().modelo_imputador
    assert ImputadorEscrita(ruta) is ImputadorEscrita(ruta)


def test_modelo_no_guarda_datos_individuales():
    meta = json.loads(Path(get_settings().modelo_imputador).read_text(encoding="utf-8"))
    assert set(meta) >= {"coeficientes", "residuos", "validacion"}
    assert meta["n_entrenamiento"] > 100_000
    assert meta["validacion"]["lineal_pmm"]["mae"] < meta["validacion"]["supuesto_global_c"]["mae"]


@pytest.mark.parametrize("cambio", [{"ingles": 0}, {"ingles": 301}, {"anio": 2022}, {"razonamiento": "alto"}])
def test_entradas_invalidas_dan_422(client, cambio):
    assert client.post("/predict", json={**PERFIL, **cambio}).status_code == 422


def test_sin_modelo_da_503(client, tmp_path):
    from app.main import app
    ImputadorEscrita.reiniciar()
    app.dependency_overrides[get_settings] = lambda: Settings(modelo_imputador=tmp_path / "no_existe.json")
    r = client.post("/predict", json=PERFIL)
    assert r.status_code == 503 and "imputar_escrita.py" in r.json()["detail"]
