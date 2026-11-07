"""Capa 1: la base se carga completa y las rutas de lectura responden con los códigos correctos."""


def test_salud_reporta_las_tablas_cargadas(client):
    r = client.get("/salud")
    assert r.status_code == 200
    t = r.json()["tablas"]
    assert t["universidades"] == 34 and t["riesgo_cola"] == 70 and t["stress_resumen"] == 24
    assert r.json()["modelo_ml"] is not None
    assert "X-Tiempo-ms" in r.headers


def test_las_33_universidades_del_dea_estan_en_la_base(client, resultados):
    base = resultados("base_integrada_2023_2024.csv")
    codigos = {u["pte_codigo"] for u in client.get("/universidades").json()}
    assert set(base.loc[base.incluida_dea, "pte_codigo"]) <= codigos


def test_buscar_universidad_sin_tildes(client):
    r = client.get("/universidades", params={"buscar": "Chocó"})
    assert [u["pte_codigo"] for u in r.json()] == [225729]


def test_universidad_inexistente_da_404(client):
    r = client.get("/universidades/1")
    assert r.status_code == 404 and "1" in r.json()["detail"]


def test_busqueda_demasiado_corta_da_422(client):
    assert client.get("/universidades", params={"buscar": "u"}).status_code == 422
