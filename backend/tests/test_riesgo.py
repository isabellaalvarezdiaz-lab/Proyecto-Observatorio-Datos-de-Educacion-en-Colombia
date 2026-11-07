"""Capa 2: VaR, CVaR y Kupiec. Lo publicado coincide con los CSV y el cálculo bajo demanda
cumple las definiciones (comprobadas con cuentas hechas a mano y con scipy)."""
import math

import numpy as np
import pytest
from scipy import stats

from app.services.riesgo import RiskCalculator


def test_cola_nacional_2024(client):
    nac = next(f for f in client.get("/riesgo/cola", params={"anio": 2024}).json() if f["nombre"] == "nacional")
    assert nac["var"] == 112 and nac["cvar"] == pytest.approx(104.27)


def test_cola_igual_al_csv(client, resultados):
    ref = resultados("riesgo_puntaje.csv").dropna(subset=["pte_codigo"])
    for _, r in ref.iterrows():
        api = client.get(f"/riesgo/cola/{int(r.pte_codigo)}").json()
        fila = next(f for f in api if f["anio"] == r.anio)
        assert fila["cvar"] == pytest.approx(r.cvar) and fila["var"] == r["var"]
        assert fila["k_cola"] == math.ceil(0.05 * fila["n_evaluados"])


def test_kupiec_relativo_seis_rechazos(client):
    filas = client.get("/riesgo/backtesting/kupiec", params={"solo_rechazos": True}).json()
    nombres = {f["nombre"] for f in filas}
    assert len(filas) == 6 and "universidad del tolima" in nombres
    assert all(f["p_relativo_holm"] < 0.05 for f in filas)


def test_var_cvar_a_mano(client):
    # 20 puntajes, α = 0,10 → k = 2: los dos más bajos son 100 y 110
    x = [100, 110] + list(range(150, 168))
    r = client.post("/riesgo/var", json={"puntajes": x, "alfa": 0.10, "B": 200}).json()
    assert r["k_cola"] == 2 and r["var"] == 110 and r["cvar"] == 105
    assert r["var_ic95"]["inf"] <= r["var"] <= r["var_ic95"]["sup"]
    assert r["brecha_cola"] == pytest.approx(np.mean(x) - 105, abs=0.01)


def test_kupiec_misma_cohorte_no_rechaza():
    # contra sí misma, con empates ponderados, la tasa de fallas es exactamente α
    rng = np.random.default_rng(1)
    x = rng.integers(80, 220, 5000).astype(float)
    k = RiskCalculator(0.05).kupiec(x, x)
    assert k.tasa_fallas == pytest.approx(0.05, abs=1e-4) and not k.rechaza_5pct


def test_lr_kupiec_coincide_con_scipy():
    n, x, p0 = 1000, 70, 0.05
    lr, p = RiskCalculator.lr_pof(x, n, p0)
    ph = x / n
    esperado = -2 * (stats.binom.logpmf(x, n, p0) - stats.binom.logpmf(x, n, ph))
    assert lr == pytest.approx(esperado) and p == pytest.approx(stats.chi2.sf(esperado, 1))


def test_backtest_detecta_cola_peor(client):
    ref = list(range(100, 300))
    peor = [v - 15 for v in ref]
    r = client.post("/riesgo/var", json={"puntajes": ref, "puntajes_backtest": peor, "B": 100}).json()
    assert r["backtest"]["rechaza_5pct"] and r["backtest"]["direccion"] == "cola peor que la referencia"


@pytest.mark.parametrize("cuerpo", [
    {"puntajes": [150] * 19},                                  # menos de 20
    {"puntajes": [150] * 30 + [301]},                          # fuera de 0-300
    {"puntajes": [150] * 30, "alfa": 0.5},                     # α demasiado grande
    {"puntajes": [150] * 30, "alfa": 0.01},                    # la cola queda vacía
    {"puntajes": [150] * 30, "B": 10},                         # pocas réplicas
])
def test_entradas_invalidas_dan_422(client, cuerpo):
    assert client.post("/riesgo/var", json=cuerpo).status_code == 422
