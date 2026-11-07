"""Asistente RAG con herramientas: cifras de la base y fragmentos citados de los documentos."""
from typing import Annotated

from fastapi import APIRouter, Depends

from ..dependencies import get_asistente
from ..models import schemas as s
from ..services.asistente import Asistente

router = APIRouter(prefix="/asistente", tags=["Asistente"])


@router.post("/preguntar", response_model=s.Respuesta,
             summary="Pregunta en lenguaje natural; responde con cifras de la base y fuentes citadas")
async def preguntar(p: s.Pregunta, asistente: Annotated[Asistente, Depends(get_asistente)]):
    return await asistente.responder(p)
