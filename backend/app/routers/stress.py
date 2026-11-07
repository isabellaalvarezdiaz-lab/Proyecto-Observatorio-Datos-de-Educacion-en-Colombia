"""Capa 3 · stress testing del presupuesto sobre el DEA."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_stress
from ..models import schemas as s
from ..services.stress import StressService

router = APIRouter(prefix="/stress", tags=["Stress testing"])
Servicio = Annotated[StressService, Depends(get_stress)]


@router.get("/escenarios", response_model=list[s.StressResumenFila], summary="Escenarios E0 a E7 publicados")
def escenarios(servicio: Servicio, modelo: s.Modelo | None = None):
    return servicio.resumen(modelo)


@router.get("/escenarios/{escenario}", response_model=list[s.StressFila],
            summary="Detalle por universidad de un escenario publicado (por ejemplo: E6)")
def escenario(escenario: str, servicio: Servicio, modelo: s.Modelo = "principal"):
    clave = next((r.escenario for r in servicio.resumen(modelo) if r.escenario.split()[0] == escenario.upper()
                  or r.escenario == escenario), None)
    if clave is None:
        raise HTTPException(status_code=404, detail=f"No existe el escenario {escenario!r} (use E0 a E7)")
    return [s.StressFila(pte_codigo=f.pte_codigo, universidad=nombre, orden=orden,
                         insumo_base_mm=f.insumo_base_mm, insumo_escenario_mm=f.insumo_escenario_mm,
                         eficiencia_base=f.eficiencia_base, eficiencia_escenario=f.eficiencia_escenario,
                         cambio=f.cambio, puesto_base=f.puesto_base, puesto_escenario=f.puesto_escenario)
            for f, nombre, orden in servicio.detalle(clave, modelo)]


@router.post("", response_model=s.EscenarioResultado,
             summary="Escenario a la medida: recortes y adiciones, con el DEA recalculado",
             responses={400: {"description": "La universidad existe pero no está en ese modelo"},
                        404: {"description": "Universidad o año sin datos"}})
def simular(entrada: s.EscenarioEntrada, servicio: Servicio):
    try:
        return servicio.simular(entrada)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
