"""Stress testing del presupuesto sobre el DEA: escenarios publicados y escenarios a la medida.

El DEA es el mismo de scripts/dea.py (BCC orientado al producto, forma envolvente) y el
escenario base reproduce resultados/oe3_eficiencia.csv; los tests lo comprueban, y comprueban
que los escenarios E1 a E7 armados con la API reproducen resultados/riesgo_stress_*.csv.
"""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..decoradores import medir_tiempo
from ..models import db_models as m
from ..models import schemas as s

UNAD = 225709
PRODUCTOS = {"principal": ["mat_total_prom", "grad_total", "global_c"],
             "cobertura": ["mat_total_prom", "grad_total"],
             "cobertura_sin_unad": ["mat_total_prom", "grad_total"]}


class DEA:
    """Eficiencia técnica BCC orientada al producto: δ = 1/φ, con φ del programa envolvente."""

    @staticmethod
    def phi(x0: np.ndarray, y0: np.ndarray, X: np.ndarray, Y: np.ndarray) -> float:
        n, mi = X.shape
        so = Y.shape[1]
        c = np.zeros(n + 1)
        c[0] = -1.0
        A_ub = np.vstack([np.hstack([np.zeros((mi, 1)), X.T]),
                          np.hstack([y0.reshape(so, 1), -Y.T])])
        b_ub = np.concatenate([x0, np.zeros(so)])
        A_eq = np.hstack([[0.0], np.ones(n)]).reshape(1, -1)
        r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=[1.0],
                    bounds=[(0, None)] * (n + 1), method="highs")
        if r.status != 0:
            raise RuntimeError(f"El programa lineal no se resolvió: {r.message}")
        return float(r.x[0])

    @classmethod
    def eficiencia(cls, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
        return np.array([1.0 / cls.phi(X[o], Y[o], X, Y) for o in range(len(X))])


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    return float(pd.Series(np.round(a, 6)).corr(pd.Series(np.round(b, 6)), method="spearman"))


def puestos(d: np.ndarray) -> np.ndarray:
    return pd.Series(np.round(d, 6)).rank(ascending=False, method="min").astype(int).to_numpy()


class StressService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ publicados
    def resumen(self, modelo: str | None) -> list[m.StressResumen]:
        q = select(m.StressResumen)
        if modelo:
            q = q.where(m.StressResumen.modelo == modelo)
        return list(self.db.scalars(q.order_by(m.StressResumen.id)))

    def detalle(self, escenario: str, modelo: str) -> list[tuple[m.StressUniversidad, str, str | None]]:
        q = (select(m.StressUniversidad, m.Universidad.nombre, m.Universidad.orden)
             .join(m.Universidad, m.Universidad.pte_codigo == m.StressUniversidad.pte_codigo)
             .where(m.StressUniversidad.escenario == escenario, m.StressUniversidad.modelo == modelo)
             .order_by(m.StressUniversidad.puesto_escenario))
        return [(fila, nombre, orden) for fila, nombre, orden in self.db.execute(q).all()]

    # ------------------------------------------------------------------ a la medida
    def datos(self, modelo: str, anio: int) -> pd.DataFrame:
        q = (select(m.Observacion, m.Universidad.nombre, m.Universidad.orden)
             .join(m.Universidad).where(m.Observacion.anio == anio, m.Observacion.incluida_dea.is_(True))
             .order_by(m.Observacion.pte_codigo))
        filas = [dict(pte_codigo=o.pte_codigo, nombre=nombre, orden=orden, obligacion_mm=o.obligacion_mm,
                      mat_total_prom=o.mat_total_prom, mat_pregrado_prom=o.mat_pregrado_prom,
                      grad_total=o.grad_total, global_c=o.global_c, pct_estrato_1_2=o.pct_estrato_1_2)
                 for o, nombre, orden in self.db.execute(q).all()]
        df = pd.DataFrame(filas)
        if modelo == "cobertura_sin_unad":
            df = df[df.pte_codigo != UNAD]
        return df.reset_index(drop=True)

    @staticmethod
    def insumo_escenario(df: pd.DataFrame, d0: np.ndarray, e: s.EscenarioEntrada,
                         todas: pd.DataFrame) -> np.ndarray:
        """Insumo del escenario. La adición se reparte entre TODAS las universidades del año
        ('todas'), como en scripts/riesgo_stress.py: cada universidad recibe lo mismo en cualquier
        modelo, y en cobertura_sin_unad la parte de la UNAD simplemente no entra."""
        x0 = df.obligacion_mm.to_numpy(float)
        factor = np.ones(len(df))
        for r in e.recortes:
            if r.grupo == "todas":
                sel = np.ones(len(df), bool)
            elif r.grupo in ("nacional", "territorial"):
                sel = (df.orden == r.grupo).to_numpy()
            elif r.grupo == "menos_eficientes":
                sel = np.zeros(len(df), bool)
                sel[np.argsort(d0)[: r.n_menos_eficientes]] = True
            else:
                sel = (df.pte_codigo == r.pte_codigo).to_numpy()
            factor = np.where(sel, factor * (1 - r.porcentaje / 100), factor)
        x = x0 * factor
        if e.adicion is not None:
            if e.adicion.reparto == "matricula_pregrado":
                peso = todas.mat_pregrado_prom
            elif e.adicion.reparto == "pregrado_estratos_1_2":
                peso = todas.mat_pregrado_prom * todas.pct_estrato_1_2 / 100
            else:
                peso = pd.Series(1.0, index=todas.index)
            parte = (e.adicion.monto_mm * peso / peso.sum()).set_axis(todas.pte_codigo)
            x = x + parte.loc[df.pte_codigo].to_numpy(float)
        return x

    @medir_tiempo
    def simular(self, e: s.EscenarioEntrada) -> s.EscenarioResultado:
        df = self.datos(e.modelo, e.anio)
        if df.empty:
            raise LookupError(f"No hay observaciones del DEA para {e.anio}")
        for r in e.recortes:
            if r.grupo == "universidad" and r.pte_codigo not in set(df.pte_codigo):
                if self.db.get(m.Universidad, r.pte_codigo) is None:
                    raise LookupError(f"No existe la universidad {r.pte_codigo}")
                raise ValueError(f"La universidad {r.pte_codigo} existe pero no está en el modelo {e.modelo} "
                                 f"de {e.anio} (por ejemplo, la UNAD en cobertura_sin_unad)")
        Y = df[PRODUCTOS[e.modelo]].to_numpy(float)
        x0 = df.obligacion_mm.to_numpy(float)
        d0 = DEA.eficiencia(x0.reshape(-1, 1), Y)
        x1 = self.insumo_escenario(df, d0, e, self.datos("principal", e.anio))
        d1 = DEA.eficiencia(x1.reshape(-1, 1), Y)
        cambio = d1 - d0
        p0, p1 = puestos(d0), puestos(d1)
        i = int(np.argmax(np.abs(cambio)))
        unis = [s.StressFila(pte_codigo=int(df.pte_codigo[j]), universidad=df.nombre[j],
                             orden=None if pd.isna(df.orden[j]) else df.orden[j],
                             insumo_base_mm=round(float(x0[j]), 3), insumo_escenario_mm=round(float(x1[j]), 3),
                             eficiencia_base=round(float(d0[j]), 4), eficiencia_escenario=round(float(d1[j]), 4),
                             cambio=round(float(cambio[j]), 4), puesto_base=int(p0[j]), puesto_escenario=int(p1[j]))
                for j in np.argsort(p1, kind="stable")]
        resumen = s.StressMetricas(
            n=len(df), insumo_total_mm=round(float(x1.sum()), 1), eficiencia_media=round(float(d1.mean()), 4),
            cambio_media=round(float(d1.mean() - d0.mean()), 4), n_frontera=int((np.round(d1, 6) >= 1).sum()),
            spearman_con_base=round(spearman(d0, d1), 4), cambio_max=round(float(cambio[i]), 4),
            universidad_cambio_max=df.nombre[i] if abs(cambio[i]) > 1e-9 else "ninguna",
            n_cambian_5_puntos=int((np.abs(cambio) >= 0.05).sum()),
            n_cambian_puesto_5=int((np.abs(p1 - p0) >= 5).sum()))
        return s.EscenarioResultado(modelo=e.modelo, anio=e.anio, resumen=resumen, universidades=unis)
