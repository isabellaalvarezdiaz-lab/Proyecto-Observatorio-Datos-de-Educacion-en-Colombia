"""Imputador de Comunicación Escrita, servido con el patrón Singleton.

El modelo lo entrena offline scripts/imputar_escrita.py con los microdatos (que nunca salen de
data/). Lo que llega a la API es modelos/imputador_escrita.json: coeficientes, cuantiles de los
residuos y métricas de validación, sin ningún registro individual. Por eso se guarda en JSON y no
en pickle/joblib: un pickle de un modelo de vecinos guardaría los datos de entrenamiento, y el JSON
además no depende de la versión de scikit-learn.

El Singleton garantiza que el archivo se lee una sola vez por proceso, no en cada request.
"""
import json
import threading
from pathlib import Path
from typing import Any

from ..models import schemas as s

ORDEN = ["ciudadanas", "ingles", "lectura_critica", "razonamiento"]


class ModeloNoDisponible(RuntimeError):
    pass


class ImputadorEscrita:
    _instancia: "ImputadorEscrita | None" = None
    _candado = threading.Lock()

    def __new__(cls, ruta: Path) -> "ImputadorEscrita":
        with cls._candado:
            if cls._instancia is None:
                inst = super().__new__(cls)
                inst._cargar(Path(ruta))
                cls._instancia = inst
        return cls._instancia

    def _cargar(self, ruta: Path) -> None:
        if not ruta.exists():
            raise ModeloNoDisponible(f"No existe {ruta}: corra scripts/imputar_escrita.py")
        with open(ruta, encoding="utf-8") as f:
            self.meta: dict[str, Any] = json.load(f)
        faltan = set(ORDEN + ["anio_2024"]) - set(self.meta["coeficientes"])
        if faltan:
            raise ModeloNoDisponible(f"El modelo no tiene los coeficientes {sorted(faltan)}")
        self.version: str = self.meta["version"]
        self.ruta = ruta

    @classmethod
    def reiniciar(cls) -> None:
        """Solo para tests: olvida la instancia cargada."""
        with cls._candado:
            cls._instancia = None

    def predecir(self, e: s.PrediccionEntrada) -> tuple[float, s.Intervalo, s.Intervalo, float]:
        c = self.meta["coeficientes"]
        y = self.meta["intercepto"] + sum(c[k] * getattr(e, k) for k in ORDEN) + c["anio_2024"] * (e.anio == 2024)
        q = self.meta["residuos"]["cuantiles"]
        lo, hi = self.meta["rango_puntaje"]

        def acotar(v: float) -> float:
            return round(min(max(v, lo), hi), 1)

        i80 = s.Intervalo(inf=acotar(y + q["p10"]), sup=acotar(y + q["p90"]))
        i95 = s.Intervalo(inf=acotar(y + q["p2_5"]), sup=acotar(y + q["p97_5"]))
        y = acotar(y)
        global_est = round((sum(getattr(e, k) for k in ORDEN) + y) / 5, 2)
        return y, i80, i95, global_est
