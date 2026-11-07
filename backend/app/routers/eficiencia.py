"""Eficiencia DEA con bootstrap (OE3), Malmquist (OE2) e imputación de Escrita."""
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_eficiencia
from ..models import schemas as s
from ..services.eficiencia import EficienciaService

router = APIRouter(tags=["Eficiencia"])
Servicio = Annotated[EficienciaService, Depends(get_eficiencia)]


@router.get("/eficiencia", response_model=list[s.EficienciaFila], summary="Eficiencia por universidad y año")
def eficiencia(servicio: Servicio, modelo: s.Modelo | None = None, anio: s.AnioQuery = None):
    return servicio.listar(modelo, anio)


@router.get("/eficiencia/{pte_codigo}", response_model=list[s.EficienciaFila])
def eficiencia_universidad(pte_codigo: int, servicio: Servicio, modelo: s.Modelo | None = None):
    filas = servicio.listar(modelo, None, pte_codigo)
    if not filas:
        raise HTTPException(status_code=404, detail=f"No hay eficiencias para la universidad {pte_codigo}")
    return filas


@router.get("/malmquist", response_model=list[s.MalmquistFila], summary="Índice de Malmquist 2023→2024")
def malmquist(servicio: Servicio, modelo: s.Modelo | None = "principal",
              version: Annotated[Literal["nominal", "real"] | None, Query()] = "nominal"):
    return servicio.malmquist(modelo, version)


@router.get("/imputacion/escrita", response_model=list[s.ImputacionFila],
            summary="Global con los ceros de Escrita imputados por perfiles similares (PMM)")
def imputacion(servicio: Servicio, anio: s.AnioQuery = None):
    return servicio.imputacion(anio)
