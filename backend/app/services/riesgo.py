"""Riesgo de cola del puntaje: consulta de los resultados publicados y cálculo bajo demanda.

RiskCalculator usa las MISMAS definiciones que scripts/riesgo_puntaje.py (simulación histórica):
  k = ⌈α·n⌉; VaR = k-ésimo puntaje más bajo; CVaR = promedio de los k más bajos;
  intervalo bootstrap de percentiles; Kupiec POF con empates en el VaR ponderados por w.
Los tests comprueban que reproduce resultados/riesgo_puntaje.csv a partir de una muestra.
"""
import math

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..decoradores import medir_tiempo
from ..models import db_models as m
from ..models import schemas as s


class RiskCalculator:
    """VaR y CVaR no paramétricos, bootstrap y backtesting de Kupiec."""

    def __init__(self, alfa: float) -> None:
        self.alfa = alfa

    def k_cola(self, n: int) -> int:
        return max(1, math.ceil(round(self.alfa * n, 9)))

    def var_cvar(self, x: np.ndarray) -> tuple[float, float, int]:
        k = self.k_cola(len(x))
        cola = np.partition(x, k - 1)[:k]
        return float(cola.max()), float(cola.mean()), k

    def bootstrap(self, x: np.ndarray, B: int, semilla: int) -> tuple[list[float], list[float]]:
        rng = np.random.default_rng(semilla)
        k = self.k_cola(len(x))
        v, c = np.empty(B), np.empty(B)
        for b in range(B):
            cola = np.partition(rng.choice(x, size=len(x), replace=True), k - 1)[:k]
            v[b], c[b] = cola.max(), cola.mean()
        return np.percentile(v, [2.5, 97.5]).tolist(), np.percentile(c, [2.5, 97.5]).tolist()

    @staticmethod
    def lr_pof(x: float, n: int, p0: float) -> tuple[float, float]:
        """Estadístico de Kupiec y su p-valor χ²(1). x puede ser fraccionario (empates ponderados)."""
        def ll(p: float) -> float:
            a = (n - x) * math.log(1 - p) if n - x > 0 else 0.0
            b = x * math.log(p) if x > 0 else 0.0
            return a + b
        ph = x / n
        lr = max(0.0, -2 * ll(p0) + 2 * (ll(ph) if 0 < ph < 1 else 0.0))
        return lr, math.erfc(math.sqrt(lr / 2))          # sf de χ²(1)

    def kupiec(self, referencia: np.ndarray, prueba: np.ndarray) -> s.KupiecCalculado:
        var, _, _ = self.var_cvar(referencia)
        debajo, en = int((referencia < var).sum()), int((referencia == var).sum())
        w = min(max((self.alfa * len(referencia) - debajo) / en, 0.0), 1.0)
        x = float((prueba < var).sum() + w * (prueba == var).sum())
        lr, p = self.lr_pof(x, len(prueba), self.alfa)
        tasa = x / len(prueba)
        return s.KupiecCalculado(var_referencia=var, peso_empates=round(w, 4), n_prueba=len(prueba),
                                 fallas=round(x, 2), tasa_fallas=round(tasa, 4), lr=round(lr, 3),
                                 p_valor=round(p, 6), rechaza_5pct=p < 0.05,
                                 direccion=None if p >= 0.05 else
                                 ("cola peor que la referencia" if tasa > self.alfa else "cola mejor que la referencia"))


class RiesgoService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def cola(self, anio: int | None, pte_codigo: int | None = None) -> list[m.RiesgoCola]:
        q = select(m.RiesgoCola)
        if anio is not None:
            q = q.where(m.RiesgoCola.anio == anio)
        if pte_codigo is not None:
            q = q.where(m.RiesgoCola.pte_codigo == pte_codigo)
        return list(self.db.scalars(q.order_by(m.RiesgoCola.anio, m.RiesgoCola.cvar)))

    def kupiec(self, solo_rechazos: bool = False, relativo: bool = True) -> list[m.Kupiec]:
        q = select(m.Kupiec)
        if solo_rechazos:
            q = q.where(m.Kupiec.rechaza_relativo if relativo else m.Kupiec.rechaza_5pct)
        return list(self.db.scalars(q.order_by(m.Kupiec.tasa_2024.desc())))

    @medir_tiempo
    def calcular(self, entrada: s.VarEntrada) -> s.VarResultado:
        calc = RiskCalculator(entrada.alfa)
        x = np.asarray(entrada.puntajes, dtype=float)
        var, cvar, k = calc.var_cvar(x)
        ic_v, ic_c = calc.bootstrap(x, entrada.B, entrada.semilla)
        back = None
        if entrada.puntajes_backtest:
            back = calc.kupiec(x, np.asarray(entrada.puntajes_backtest, dtype=float))
        return s.VarResultado(n=len(x), alfa=entrada.alfa, k_cola=k, media=round(float(x.mean()), 2),
                              var=var, cvar=round(cvar, 2),
                              var_ic95=s.Intervalo(inf=round(ic_v[0], 2), sup=round(ic_v[1], 2)),
                              cvar_ic95=s.Intervalo(inf=round(ic_c[0], 2), sup=round(ic_c[1], 2)),
                              brecha_cola=round(float(x.mean()) - cvar, 2), backtest=back)
