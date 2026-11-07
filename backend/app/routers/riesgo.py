"""Capa 2 · riesgo: VaR y CVaR no paramétricos del puntaje y backtesting de Kupiec."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_riesgo
from ..models import schemas as s
from ..services.riesgo import RiesgoService

router = APIRouter(prefix="/riesgo", tags=["Riesgo"])
Servicio = Annotated[RiesgoService, Depends(get_riesgo)]


@router.get("/cola", response_model=list[s.ColaFila], summary="VaR y CVaR 5 % por universidad (publicados)")
def cola(servicio: Servicio, anio: s.AnioQuery = None):
    return servicio.cola(anio)


@router.get("/cola/{pte_codigo}", response_model=list[s.ColaFila])
def cola_universidad(pte_codigo: int, servicio: Servicio):
    filas = servicio.cola(None, pte_codigo)
    if not filas:
        raise HTTPException(status_code=404, detail=f"No hay riesgo de cola para la universidad {pte_codigo}")
    return filas


@router.get("/backtesting/kupiec", response_model=list[s.KupiecFila], summary="Kupiec 2023 → 2024")
def kupiec(servicio: Servicio,
           solo_rechazos: Annotated[bool, Query(description="Solo las que rechazan (Holm, 5 %)")] = False,
           relativo: Annotated[bool, Query(description="Prueba contra la tasa nacional (True) o contra α")] = True):
    return servicio.kupiec(solo_rechazos, relativo)


@router.post("/var", response_model=s.VarResultado,
             summary="VaR y CVaR por simulación histórica de una lista de puntajes, con bootstrap y Kupiec")
def calcular(entrada: s.VarEntrada, servicio: Servicio):
    return servicio.calcular(entrada)
