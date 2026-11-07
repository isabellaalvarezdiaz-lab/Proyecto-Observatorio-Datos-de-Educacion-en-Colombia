"""Dependencias inyectadas con Depends(): configuración, sesión, servicios, modelo ML y asistente.

Las rutas no tienen lógica de negocio: reciben los servicios ya construidos desde aquí. En los
tests se reemplazan con app.dependency_overrides (por ejemplo, un LLM falso).
"""
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .database import BaseDeDatos
from .ml.predictor import ImputadorEscrita, ModeloNoDisponible
from .services.asistente import LLM, Asistente, IndiceBM25, LLMAnthropic
from .services.eficiencia import EficienciaService, UniversidadService
from .services.riesgo import RiesgoService
from .services.stress import StressService

ConfigDep = Annotated[Settings, Depends(get_settings)]


def get_bd(request: Request) -> BaseDeDatos:
    return request.app.state.bd


def get_db(bd: Annotated[BaseDeDatos, Depends(get_bd)]) -> Iterator[Session]:
    yield from bd.sesion()


DbDep = Annotated[Session, Depends(get_db)]


def get_universidades(db: DbDep) -> UniversidadService:
    return UniversidadService(db)


def get_eficiencia(db: DbDep) -> EficienciaService:
    return EficienciaService(db)


def get_riesgo(db: DbDep) -> RiesgoService:
    return RiesgoService(db)


def get_stress(db: DbDep) -> StressService:
    return StressService(db)


def get_imputador(config: ConfigDep) -> ImputadorEscrita:
    try:
        return ImputadorEscrita(config.modelo_imputador)
    except ModeloNoDisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@lru_cache
def _indice(raiz: str) -> IndiceBM25:
    """El índice se construye una vez por proceso (leer el PDF tarda unos segundos)."""
    return IndiceBM25.desde_repo(Path(raiz))


def get_indice(config: ConfigDep) -> IndiceBM25:
    return _indice(str(config.docs_dir.parent))


def get_llm(config: ConfigDep) -> LLM | None:
    if not config.llm_api_key:
        return None
    return LLMAnthropic(config.llm_api_key, config.llm_modelo, config.llm_url, config.llm_timeout_s)


def get_asistente(db: DbDep, indice: Annotated[IndiceBM25, Depends(get_indice)],
                  llm: Annotated[LLM | None, Depends(get_llm)]) -> Asistente:
    return Asistente(db, indice, llm)
