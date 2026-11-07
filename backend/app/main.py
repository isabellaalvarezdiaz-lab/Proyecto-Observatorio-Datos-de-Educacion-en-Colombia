"""API del Observatorio de Datos de Educación: eficiencia del gasto público en universidades,
riesgo de cola del puntaje Saber Pro, stress testing del presupuesto, imputación de Escrita y
un asistente con fuentes.

Arranque (desde backend/):
    uvicorn app.main:app --reload
Documentación interactiva: /docs (Swagger) y /redoc.
"""
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from . import etl
from .config import get_settings
from .database import BaseDeDatos
from .ml.predictor import ImputadorEscrita, ModeloNoDisponible
from .models import db_models as m
from .models import schemas as s
from .routers import asistente, eficiencia, ml, riesgo, stress, universidades

log = logging.getLogger("observatorio")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    config = get_settings()
    logging.basicConfig(level=config.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    bd = BaseDeDatos(config.database_url)
    bd.crear_tablas()
    with bd.SesionLocal() as db:
        if config.cargar_al_iniciar and etl.base_vacia(db):
            log.info("Base vacía: cargando los CSV de %s", config.resultados_dir)
            etl.cargar(db, config.resultados_dir)
    app.state.bd = bd
    log.info("API lista (entorno=%s)", config.entorno)
    yield
    bd.motor.dispose()


app = FastAPI(
    title="Observatorio de Datos de Educación · API",
    version="1.0.0",
    description=("Resultados del proyecto de consultoría (USTA, Estadística): eficiencia DEA con bootstrap, "
                 "Malmquist, riesgo de cola del puntaje Saber Pro (VaR/CVaR con Kupiec), stress testing del "
                 "presupuesto, imputación de los ceros de Escrita y un asistente que cita sus fuentes. "
                 "La API solo expone agregados por universidad: los microdatos nunca salen de data/."),
    lifespan=ciclo_de_vida,
)


@app.middleware("http")
async def tiempo_de_respuesta(request: Request, call_next):
    inicio = time.perf_counter()
    respuesta = await call_next(request)
    ms = (time.perf_counter() - inicio) * 1000
    respuesta.headers["X-Tiempo-ms"] = f"{ms:.1f}"
    log.info("%s %s → %d (%.1f ms)", request.method, request.url.path, respuesta.status_code, ms)
    return respuesta


@app.exception_handler(Exception)
async def error_interno(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Error no controlado en %s", request.url.path)
    detalle = "Error interno" if get_settings().entorno == "produccion" else f"{type(exc).__name__}: {exc}"
    return JSONResponse(status_code=500, content={"detail": detalle})


@app.get("/", include_in_schema=False)
def inicio() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/salud", response_model=s.Salud, tags=["Datos"], summary="Estado de la API y de la base")
def salud(request: Request) -> s.Salud:
    with request.app.state.bd.SesionLocal() as db:
        tablas = {t.__tablename__: db.query(t).count() for t in (
            m.Universidad, m.Eficiencia, m.RiesgoCola, m.Kupiec, m.StressResumen, m.Prediccion)}
    try:
        version = ImputadorEscrita(get_settings().modelo_imputador).version
    except ModeloNoDisponible:
        version = None
    return s.Salud(estado="ok", entorno=get_settings().entorno, tablas=tablas, modelo_ml=version)


for r in (universidades.router, eficiencia.router, riesgo.router, stress.router, ml.router, asistente.router):
    app.include_router(r)
