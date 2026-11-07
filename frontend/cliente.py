"""Cliente HTTP del tablero: todas las cifras las calcula la API, el tablero solo las muestra."""
import os
from typing import Any

import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")


class ErrorAPI(RuntimeError):
    pass


class ClienteAPI:
    def __init__(self, url: str = API_URL, timeout: float = 60) -> None:
        self.url, self.timeout = url.rstrip("/"), timeout
        self.sesion = requests.Session()

    def _pedir(self, metodo: str, ruta: str, **kw: Any) -> Any:
        try:
            r = self.sesion.request(metodo, f"{self.url}{ruta}", timeout=self.timeout, **kw)
        except requests.RequestException as exc:
            raise ErrorAPI(f"No se pudo conectar con la API en {self.url}: {exc}") from exc
        if r.status_code >= 400:
            try:
                detalle = r.json().get("detail")
            except ValueError:
                detalle = r.text
            raise ErrorAPI(f"La API respondió {r.status_code}: {detalle}")
        return r.json()

    def salud(self) -> dict:
        return self._pedir("GET", "/salud")

    def eficiencia(self, modelo: str, anio: int) -> list[dict]:
        return self._pedir("GET", "/eficiencia", params={"modelo": modelo, "anio": anio})

    def cola(self, anio: int) -> list[dict]:
        return self._pedir("GET", "/riesgo/cola", params={"anio": anio})

    def kupiec(self) -> list[dict]:
        return self._pedir("GET", "/riesgo/backtesting/kupiec")

    def escenarios(self, modelo: str) -> list[dict]:
        return self._pedir("GET", "/stress/escenarios", params={"modelo": modelo})

    def simular(self, escenario: dict) -> dict:
        return self._pedir("POST", "/stress", json=escenario)

    def predecir(self, perfil: dict) -> dict:
        return self._pedir("POST", "/predict", json=perfil)

    def preguntar(self, pregunta: str) -> dict:
        return self._pedir("POST", "/asistente/preguntar", json={"pregunta": pregunta})
