"""Asistente: las cifras salen de la base, las fuentes se citan, y una redacción del LLM con un
número inventado se descarta (regla "Nada sin fuente")."""
import pytest

from app.dependencies import get_llm
from app.main import app


class LLMFalso:
    def __init__(self, texto: str | None = None, error: bool = False) -> None:
        self.texto, self.error, self.llamadas = texto, error, 0

    async def redactar(self, sistema: str, usuario: str) -> str:
        self.llamadas += 1
        if self.error:
            raise TimeoutError("sin red")
        return self.texto


def preguntar(client, pregunta: str, **extra):
    r = client.post("/asistente/preguntar", json={"pregunta": pregunta, **extra})
    assert r.status_code == 200, r.text
    return r.json()


def test_cifra_de_la_base_con_fuente(client):
    r = preguntar(client, "¿Cuál es el CVaR de la Universidad Tecnológica del Chocó?")
    cvar = next(c for c in r["cifras"] if c["descripcion"].startswith("CVaR"))
    db = next(f for f in client.get("/riesgo/cola/225729").json() if f["anio"] == 2024)
    assert cvar["valor"] == db["cvar"] and "riesgo_puntaje.csv" in cvar["fuente"]
    assert "88,89" in r["respuesta"] and r["modo"] == "plantilla" and r["fuentes"]


@pytest.mark.parametrize("pregunta,codigo", [("eficiencia de la universidad nacional", 225701),
                                             ("stress de la UNAD con la gratuidad", 225709),
                                             ("malmquist de la universidad de antioquia", 225702),
                                             ("eficiencia de la pedagógica nacional", None)])
def test_reconoce_la_universidad(client, pregunta, codigo):
    from app.services.asistente import Herramientas
    from app.dependencies import get_db
    db = next(get_db(app.state.bd))
    u = Herramientas(db).universidad(pregunta)
    if codigo is None:
        assert u is not None and "pedagogica nacional" in u.nombre
    else:
        assert u.pte_codigo == codigo


def test_pregunta_ajena_no_inventa(client):
    r = preguntar(client, "¿Cuál es la capital de Francia?")
    assert r["cifras"] == [] and r["fuentes"] == [] and "sin fuente" in r["respuesta"]


def test_pregunta_conceptual_cita_documento(client):
    r = preguntar(client, "¿Qué limitaciones tiene el insumo presupuestal?")
    assert r["fuentes"] and r["respuesta"].startswith("Según")


def test_llm_con_numeros_de_la_fuente_se_acepta(client):
    falso = LLMFalso("Según la API, el CVaR 2024 de la Tecnológica del Chocó es 88,89, el más bajo.")
    app.dependency_overrides[get_llm] = lambda: falso
    r = preguntar(client, "CVaR de la Universidad Tecnológica del Chocó")
    assert r["modo"] == "llm" and falso.llamadas == 1


def test_llm_que_inventa_un_numero_se_descarta(client):
    app.dependency_overrides[get_llm] = lambda: LLMFalso("El CVaR del Chocó es 73,2 puntos.")
    r = preguntar(client, "CVaR de la Universidad Tecnológica del Chocó")
    assert r["modo"] == "llm_rechazado" and "88,89" in r["respuesta"] and "73,2" not in r["respuesta"]


def test_llm_caido_no_tumba_la_api(client):
    app.dependency_overrides[get_llm] = lambda: LLMFalso(error=True)
    r = preguntar(client, "CVaR de la Universidad Tecnológica del Chocó")
    assert r["modo"] == "plantilla"


def test_usar_llm_falso_no_lo_llama(client):
    falso = LLMFalso("texto")
    app.dependency_overrides[get_llm] = lambda: falso
    preguntar(client, "CVaR de la Universidad Tecnológica del Chocó", usar_llm=False)
    assert falso.llamadas == 0


def test_pregunta_vacia_da_422(client):
    assert client.post("/asistente/preguntar", json={"pregunta": "   "}).status_code == 422
