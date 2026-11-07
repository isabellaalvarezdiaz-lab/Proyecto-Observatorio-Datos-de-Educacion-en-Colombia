"""Eficiencia (OE3), Malmquist (OE2) e imputación: la API devuelve lo mismo que los CSV."""
import pytest


@pytest.mark.parametrize("modelo,anio", [("principal", 2023), ("principal", 2024), ("cobertura", 2024),
                                         ("cobertura_sin_unad", 2024)])
def test_eficiencia_igual_al_csv(client, resultados, modelo, anio):
    archivo = "oe3_cobertura_sin_unad.csv" if modelo == "cobertura_sin_unad" else "oe3_eficiencia.csv"
    ref = resultados(archivo)
    ref = ref[(ref.modelo == modelo) & (ref.anio == anio)].set_index("pte_codigo")
    api = client.get("/eficiencia", params={"modelo": modelo, "anio": anio}).json()
    assert len(api) == len(ref)
    for f in api:
        assert f["eficiencia_corregida"] == pytest.approx(ref.loc[f["pte_codigo"], "eficiencia_corregida"])
        assert f["ic95"]["inf"] <= f["eficiencia_corregida"] <= f["ic95"]["sup"]
    assert sum(f["en_frontera"] for f in api) == int(ref.en_frontera.sum())


def test_eficiencia_ordenada_de_mayor_a_menor(client):
    v = [f["eficiencia_corregida"] for f in client.get("/eficiencia", params={"modelo": "principal", "anio": 2024}).json()]
    assert v == sorted(v, reverse=True)


@pytest.mark.parametrize("params", [{"anio": 2022}, {"anio": "dos mil"}, {"modelo": "otro"}])
def test_parametros_invalidos_dan_422(client, params):
    assert client.get("/eficiencia", params=params).status_code == 422


def test_eficiencia_de_universidad_sin_datos_da_404(client):
    assert client.get("/eficiencia/999999").status_code == 404


def test_malmquist(client, resultados):
    ref = resultados("oe2_malmquist.csv")
    ref = ref[(ref.modelo == "principal") & (ref.version == "nominal")].set_index("pte_codigo")
    api = client.get("/malmquist").json()
    assert len(api) == len(ref)
    for f in api:
        assert f["malmquist"] == pytest.approx(ref.loc[f["pte_codigo"], "malmquist"])
        # descomposición: Malmquist = cambio de eficiencia × cambio tecnológico
        assert f["malmquist"] == pytest.approx(f["cambio_eficiencia"] * f["cambio_tecnologico"], abs=2e-4)


def test_imputacion_escrita(client):
    filas = client.get("/imputacion/escrita", params={"anio": 2024}).json()
    nac = next(f for f in filas if f["nombre"] == "nacional")
    assert nac["global_d"] == pytest.approx(148.05) and nac["global_c"] == pytest.approx(147.98)
    assert all(f["n_evaluados"] >= 5 for f in filas)       # regla K_MIN de publicacion.py
