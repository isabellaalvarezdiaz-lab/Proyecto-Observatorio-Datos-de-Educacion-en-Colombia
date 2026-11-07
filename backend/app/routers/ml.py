"""Capa 4 · ML: imputador de Escrita servido con Singleton; cada predicción queda en la base."""
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from ..dependencies import DbDep, get_imputador
from ..ml.predictor import ImputadorEscrita
from ..models import db_models as m
from ..models import schemas as s

router = APIRouter(tags=["Machine learning"])

ADVERTENCIA = ("Predicción para un perfil, no para una persona: el R² en validación es bajo (ver "
               "/predict/modelo). Úsela para agregados o como imputación, no para juzgar a un estudiante.")


@router.post("/predict", response_model=s.PrediccionSalida, status_code=201,
             summary="Escrita esperada a partir de los otros cuatro módulos",
             responses={503: {"description": "El modelo no está disponible"}})
def predecir(entrada: s.PrediccionEntrada, db: DbDep,
             modelo: Annotated[ImputadorEscrita, Depends(get_imputador)]):
    inicio = time.perf_counter()
    y, i80, i95, glob = modelo.predecir(entrada)
    ms = (time.perf_counter() - inicio) * 1000
    reg = m.Prediccion(**entrada.model_dump(), escrita_predicha=y, global_estimado=glob,
                       modelo_version=modelo.version, tiempo_ms=round(ms, 3))
    db.add(reg)
    db.commit()
    return s.PrediccionSalida(escrita_predicha=y, intervalo_80=i80, intervalo_95=i95, global_estimado=glob,
                              modelo_version=modelo.version, advertencia=ADVERTENCIA, id_prediccion=reg.id)


@router.get("/predict/modelo", summary="Metadatos y validación del modelo cargado")
def metadatos(modelo: Annotated[ImputadorEscrita, Depends(get_imputador)]) -> dict:
    return modelo.meta


@router.get("/predict/historial", response_model=list[s.PrediccionRegistro],
            summary="Últimas predicciones guardadas (monitoreo)")
def historial(db: DbDep, limite: Annotated[int, Query(ge=1, le=500)] = 50):
    return list(db.scalars(select(m.Prediccion).order_by(m.Prediccion.id.desc()).limit(limite)))
