"""Capa 1 · datos: universidades del DEA (lectura desde la base)."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_universidades
from ..models import schemas as s
from ..services.eficiencia import UniversidadService

router = APIRouter(prefix="/universidades", tags=["Datos"])
Servicio = Annotated[UniversidadService, Depends(get_universidades)]


@router.get("", response_model=list[s.Universidad], summary="Universidades públicas del estudio")
def listar(servicio: Servicio,
           buscar: Annotated[str | None, Query(min_length=3, max_length=80,
                                               description="Parte del nombre, sin importar tildes")] = None):
    return servicio.listar(buscar)


@router.get("/{pte_codigo}", response_model=s.Universidad, responses={404: {"description": "No existe"}})
def obtener(pte_codigo: int, servicio: Servicio):
    u = servicio.obtener(pte_codigo)
    if u is None:
        raise HTTPException(status_code=404, detail=f"No hay una universidad con código PTE {pte_codigo}")
    return u
