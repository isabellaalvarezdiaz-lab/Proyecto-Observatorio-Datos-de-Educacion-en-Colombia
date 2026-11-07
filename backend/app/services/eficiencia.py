"""Consultas de universidades, eficiencia (OE3), Malmquist (OE2) e imputación de Escrita."""
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import db_models as m
from ..models import schemas as s


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para buscar universidades por nombre."""
    t = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


class UniversidadService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, buscar: str | None = None) -> list[m.Universidad]:
        filas = list(self.db.scalars(select(m.Universidad).order_by(m.Universidad.nombre)))
        if buscar:
            b = normalizar(buscar)
            filas = [u for u in filas if b in normalizar(u.nombre)]
        return filas

    def obtener(self, pte_codigo: int) -> m.Universidad | None:
        return self.db.get(m.Universidad, pte_codigo)


class EficienciaService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, modelo: str | None, anio: int | None, pte_codigo: int | None = None) -> list[s.EficienciaFila]:
        q = select(m.Eficiencia, m.Universidad.nombre).join(
            m.Universidad, m.Universidad.pte_codigo == m.Eficiencia.pte_codigo)
        if modelo:
            q = q.where(m.Eficiencia.modelo == modelo)
        if anio:
            q = q.where(m.Eficiencia.anio == anio)
        if pte_codigo:
            q = q.where(m.Eficiencia.pte_codigo == pte_codigo)
        q = q.order_by(m.Eficiencia.modelo, m.Eficiencia.anio, m.Eficiencia.eficiencia_corregida.desc())
        return [s.EficienciaFila(modelo=e.modelo, anio=e.anio, pte_codigo=e.pte_codigo, universidad=nombre,
                                 eficiencia=e.eficiencia, eficiencia_corregida=e.eficiencia_corregida,
                                 ic95=s.Intervalo(inf=e.ic95_inf, sup=e.ic95_sup), en_frontera=e.en_frontera,
                                 pares=e.pares)
                for e, nombre in self.db.execute(q).all()]

    def malmquist(self, modelo: str | None, version: str | None) -> list[s.MalmquistFila]:
        q = select(m.Malmquist, m.Universidad.nombre).join(
            m.Universidad, m.Universidad.pte_codigo == m.Malmquist.pte_codigo)
        if modelo:
            q = q.where(m.Malmquist.modelo == modelo)
        if version:
            q = q.where(m.Malmquist.version == version)
        return [s.MalmquistFila(modelo=x.modelo, version=x.version, pte_codigo=x.pte_codigo, universidad=nombre,
                                malmquist=x.malmquist, cambio_eficiencia=x.cambio_eficiencia,
                                cambio_tecnologico=x.cambio_tecnologico)
                for x, nombre in self.db.execute(q.order_by(m.Malmquist.malmquist.desc())).all()]

    def imputacion(self, anio: int | None) -> list[m.ImputacionUniversidad]:
        q = select(m.ImputacionUniversidad)
        if anio:
            q = q.where(m.ImputacionUniversidad.anio == anio)
        return list(self.db.scalars(q.order_by(m.ImputacionUniversidad.anio,
                                               m.ImputacionUniversidad.diferencia_d_menos_c.desc())))
