"""Errores HTTP: un fallo interno da 500, y en producción no expone detalles."""
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import get_stress
from app.main import app


class StressRoto:
    def resumen(self, modelo):
        raise RuntimeError("detalle interno que no debe salir")


@pytest.mark.parametrize("entorno,esperado", [("desarrollo", "RuntimeError: detalle interno"),
                                              ("produccion", "Error interno")])
def test_error_interno(client, monkeypatch, entorno, esperado):
    app.dependency_overrides[get_stress] = lambda: StressRoto()
    monkeypatch.setattr("app.main.get_settings", lambda: Settings(entorno=entorno))
    # sin "with": no vuelve a correr el arranque y usa la base que ya cargó la fixture
    r = TestClient(app, raise_server_exceptions=False).get("/stress/escenarios")
    assert r.status_code == 500 and r.json()["detail"].startswith(esperado)
    get_settings.cache_clear()


def test_json_malformado_da_422(client):
    r = client.post("/predict", content="{no es json", headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_raiz_lleva_a_la_documentacion(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/docs"
    assert client.get("/openapi.json").json()["info"]["title"].startswith("Observatorio")
