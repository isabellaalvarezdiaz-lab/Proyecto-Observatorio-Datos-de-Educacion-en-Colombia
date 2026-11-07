"""Fixtures: la API con una base SQLite en memoria, cargada con los CSV de resultados/.

Los CSV están en el repositorio (son agregados, sin microdatos), así que los tests corren igual
en cualquier computador y en GitHub Actions.
"""
import os

os.environ["DATABASE_URL"] = "sqlite://"          # en memoria; antes de importar la app
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ["LLM_API_KEY"] = ""                    # los tests nunca llaman a un LLM real (gana a .env)

import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.ml.predictor import ImputadorEscrita  # noqa: E402

get_settings.cache_clear()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def limpiar_overrides():
    yield
    app.dependency_overrides.clear()
    ImputadorEscrita.reiniciar()


@pytest.fixture(scope="session")
def resultados():
    """Lee un CSV de resultados/ (la fuente contra la que se comparan las respuestas)."""
    carpeta = get_settings().resultados_dir
    return lambda nombre: pd.read_csv(carpeta / nombre, encoding="utf-8-sig")
