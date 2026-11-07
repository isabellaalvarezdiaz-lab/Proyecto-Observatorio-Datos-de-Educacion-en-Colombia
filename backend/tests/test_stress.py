"""Capa 3: los escenarios armados con POST /stress reproducen los de scripts/riesgo_stress.py,
y el escenario base reproduce la eficiencia del OE3: el DEA de la API es el mismo."""
import pytest

GRAT = 2744.311
ESCENARIOS = {
    "E1 recorte uniforme 10 %": {"recortes": [{"grupo": "todas", "porcentaje": 10}]},
    "E2 recorte uniforme 20 %": {"recortes": [{"grupo": "todas", "porcentaje": 20}]},
    "E3 recorte 20 % orden nacional": {"recortes": [{"grupo": "nacional", "porcentaje": 20}]},
    "E4 recorte 20 % orden territorial": {"recortes": [{"grupo": "territorial", "porcentaje": 20}]},
    "E5 recorte 10 % a las 8 menos eficientes": {"recortes": [{"grupo": "menos_eficientes", "porcentaje": 10,
                                                               "n_menos_eficientes": 8}]},
    "E6 + gratuidad por matrícula de pregrado": {"adicion": {"monto_mm": GRAT, "reparto": "matricula_pregrado"}},
    "E7 + gratuidad por pregrado × % estratos 1 y 2": {"adicion": {"monto_mm": GRAT,
                                                                    "reparto": "pregrado_estratos_1_2"}},
}


@pytest.mark.parametrize("modelo", ["principal", "cobertura", "cobertura_sin_unad"])
@pytest.mark.parametrize("escenario", list(ESCENARIOS))
def test_escenario_reproduce_el_script(client, resultados, modelo, escenario):
    r = client.post("/stress", json={"modelo": modelo, **ESCENARIOS[escenario]})
    assert r.status_code == 200, r.text
    api = r.json()
    res = resultados("riesgo_stress_resumen.csv")
    ref = res[(res.modelo == modelo) & (res.escenario == escenario)].iloc[0]
    for campo in ("eficiencia_media", "cambio_media", "spearman_con_base", "cambio_max"):
        assert api["resumen"][campo] == pytest.approx(ref[campo], abs=1e-4), campo
    for campo in ("n", "n_frontera", "n_cambian_5_puntos", "n_cambian_puesto_5"):
        assert api["resumen"][campo] == ref[campo], campo
    uni = resultados("riesgo_stress_universidades.csv")
    uni = uni[(uni.modelo == modelo) & (uni.escenario == escenario)].set_index("pte_codigo")
    for f in api["universidades"]:
        assert f["eficiencia_escenario"] == pytest.approx(uni.loc[f["pte_codigo"], "eficiencia_escenario"], abs=1e-4)
        assert f["eficiencia_base"] == pytest.approx(uni.loc[f["pte_codigo"], "eficiencia_base"], abs=1e-4)


def test_base_reproduce_oe3(client, resultados):
    ref = resultados("oe3_eficiencia.csv")
    ref = ref[(ref.modelo == "principal") & (ref.anio == 2023)].set_index("pte_codigo")
    # un recorte uniforme no cambia nada, así que la eficiencia del escenario es la base
    api = client.post("/stress", json={"anio": 2023, "recortes": [{"grupo": "todas", "porcentaje": 5}]}).json()
    for f in api["universidades"]:
        assert f["eficiencia_base"] == pytest.approx(ref.loc[f["pte_codigo"], "eficiencia"], abs=1e-4)
        assert f["cambio"] == pytest.approx(0, abs=1e-6)


def test_recorte_a_una_universidad_la_baja_o_la_deja(client):
    api = client.post("/stress", json={"modelo": "cobertura",
                                       "recortes": [{"grupo": "universidad", "pte_codigo": 225701,
                                                     "porcentaje": 30}]}).json()
    nal = next(f for f in api["universidades"] if f["pte_codigo"] == 225701)
    assert nal["insumo_escenario_mm"] == pytest.approx(nal["insumo_base_mm"] * 0.7, abs=1e-3)
    assert nal["eficiencia_escenario"] >= nal["eficiencia_base"] - 1e-9   # menos insumo nunca empeora la propia


def test_escenarios_publicados(client):
    assert len(client.get("/stress/escenarios").json()) == 24
    e6 = client.get("/stress/escenarios/E6").json()
    assert len(e6) == 33 and e6[0]["puesto_escenario"] == 1
    assert client.get("/stress/escenarios/E9").status_code == 404


@pytest.mark.parametrize("cuerpo,codigo", [
    ({}, 422),                                                                      # escenario vacío
    ({"recortes": [{"grupo": "menos_eficientes", "porcentaje": 10}]}, 422),         # falta n
    ({"recortes": [{"grupo": "todas", "porcentaje": 10, "pte_codigo": 225701}]}, 422),
    ({"recortes": [{"grupo": "todas", "porcentaje": 95}]}, 422),                    # más del 90 %
    ({"adicion": {"monto_mm": -5, "reparto": "uniforme"}}, 422),
    ({"anio": 2022, "recortes": [{"grupo": "todas", "porcentaje": 10}]}, 422),
    ({"recortes": [{"grupo": "universidad", "pte_codigo": 1, "porcentaje": 10}]}, 404),
    ({"modelo": "cobertura_sin_unad",                                               # existe, pero no entra
      "recortes": [{"grupo": "universidad", "pte_codigo": 225709, "porcentaje": 10}]}, 400),
])
def test_validacion_del_escenario(client, cuerpo, codigo):
    assert client.post("/stress", json=cuerpo).status_code == codigo
