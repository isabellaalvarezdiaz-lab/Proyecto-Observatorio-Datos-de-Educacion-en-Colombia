"""
verificar_oe2_oe3.py — Comprueba los resultados del DEA (OE3) y del Malmquist (OE2).

Recalcula todo por un camino distinto al de los scripts que los produjeron: resuelve el programa
DUAL (de multiplicadores) en lugar del de envolvente, con el algoritmo de punto interior de HiGHS
en lugar del símplex, y lo compara cifra por cifra con los archivos de resultados/. Además revisa
propiedades que la teoría garantiza.

Qué comprueba:
  1. Eficiencias de oe3_eficiencia.csv = las del programa dual (por modelo, año y universidad).
  2. Propiedades del DEA BCC orientado al producto: eficiencias en (0, 1]; la universidad con el
     menor insumo y la de mayor valor en cada producto quedan en la frontera.
  3. Bootstrap: intervalo inferior ≤ eficiencia corregida ≤ intervalo superior ≤ eficiencia original.
  4. Metas: cada meta ≥ valor actual.
  5. Deja uno fuera: cada fila de oe3_deja_uno_fuera.csv recalculada por el dual.
  6. Malmquist: las cuatro distancias recalculadas por el dual; M = EC × TC; M y EC recalculados
     desde las distancias; versión real = nominal × 1,052 en M y TC; EC igual en las dos.

Uso (desde la raíz del repositorio, después de oe3_dea_bootstrap.py y oe2_malmquist.py):
    python scripts/verificar_oe2_oe3.py
"""
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dea  # noqa: E402

MODELOS = {"principal": ["mat_total_prom", "grad_total", "global_c"],
           "cobertura": ["mat_total_prom", "grad_total"]}
TOL = 1e-3            # los resultados se guardaron redondeados a 4 decimales
LOG, FALLAS = [], []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def check(nombre, ok, detalle=""):
    if not ok:
        FALLAS.append(nombre)
    log(f"  {'PASA ' if ok else 'FALLA'}  {nombre}{(' — ' + detalle) if detalle else ''}")


def dual(X, Y, Xref=None, Yref=None, vrs=True):
    Xref = X if Xref is None else Xref
    Yref = Y if Yref is None else Yref
    return np.array([1 / dea.phi_multiplicadores(X[o], Y[o], Xref, Yref, vrs=vrs, metodo="highs-ipm")
                     for o in range(len(X))])


def main():
    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    base = base[base.incluida_dea]
    ef = pd.read_csv("resultados/oe3_eficiencia.csv", dtype={"pte_codigo": str})
    loo = pd.read_csv("resultados/oe3_deja_uno_fuera.csv")
    mq = pd.read_csv("resultados/oe2_malmquist.csv", dtype={"pte_codigo": str})
    log(f"##### Verificación OE2 y OE3 (programa dual, punto interior) — {datetime.now():%Y-%m-%d %H:%M} #####")

    log("\n1–4. DEA y bootstrap (oe3_eficiencia.csv)")
    for modelo, prods in MODELOS.items():
        for a in sorted(base.anio.unique()):
            d = base[base.anio == a].reset_index(drop=True)
            X, Y = d[["obligacion_mm"]].to_numpy(float), d[prods].to_numpy(float)
            dd = dual(X, Y)
            e = ef[(ef.modelo == modelo) & (ef.anio == a)].set_index("pte_codigo").loc[d.pte_codigo]
            dif = np.abs(e.eficiencia.to_numpy() - dd)
            check(f"{modelo} {a}: eficiencia = programa dual", dif.max() < TOL, f"diferencia máxima {dif.max():.1e}")
            check(f"{modelo} {a}: eficiencias en (0, 1]", ((dd > 0) & (dd <= 1 + 1e-9)).all())
            extremos = {int(np.argmin(X[:, 0])): "menor insumo"}
            for k, p in enumerate(prods):
                extremos[int(np.argmax(Y[:, k]))] = f"mayor {p}"
            ok = all(dd[i] > 1 - 1e-6 for i in extremos)
            check(f"{modelo} {a}: extremos en la frontera", ok,
                  ", ".join(f"{d.pte_nombre[i]} ({r})" for i, r in extremos.items()))
            okb = ((e.ic95_inf <= e.eficiencia_corregida + TOL) & (e.eficiencia_corregida <= e.ic95_sup + TOL)
                   & (e.ic95_sup <= e.eficiencia + TOL)).all()
            check(f"{modelo} {a}: ic inferior ≤ corregida ≤ ic superior ≤ original", bool(okb))
            okm = all((e[f"{p}_meta"] >= e[f"{p}_actual"] - TOL).all() for p in prods)
            check(f"{modelo} {a}: metas ≥ valor actual", okm)

    log("\n5. Deja uno fuera (oe3_deja_uno_fuera.csv)")
    peor = 0.0
    for r in loo.itertuples():
        d = base[base.anio == r.anio].reset_index(drop=True)
        X, Y = d[["obligacion_mm"]].to_numpy(float), d[MODELOS[r.modelo]].to_numpy(float)
        full = dual(X, Y)
        keep = (d.pte_nombre != r.sale).to_numpy()
        sin = dual(X[keep], Y[keep])
        cambio = sin - full[keep]
        peor = max(peor, abs(cambio.mean() - r.cambio_medio), abs(cambio.max() - r.cambio_max))
    check(f"{len(loo)} filas recalculadas (cambio medio y máximo)", peor < TOL, f"diferencia máxima {peor:.1e}")

    log("\n6. Malmquist (oe2_malmquist.csv)")
    amb = base.groupby("pte_codigo").anio.nunique()
    b = base[base.pte_codigo.isin(amb[amb == 2].index)]
    a0 = b[b.anio == 2023].sort_values("pte_codigo").reset_index(drop=True)
    a1 = b[b.anio == 2024].sort_values("pte_codigo").reset_index(drop=True)
    for modelo, prods in MODELOS.items():
        for version, k in (("nominal", 1.0), ("real", 1.052)):
            X0 = a0[["obligacion_mm"]].to_numpy(float)
            X1 = a1[["obligacion_mm"]].to_numpy(float) / k
            Y0, Y1 = a0[prods].to_numpy(float), a1[prods].to_numpy(float)
            D = {"D23_23": dual(X0, Y0, vrs=False), "D24_24": dual(X1, Y1, vrs=False),
                 "D23_24": dual(X1, Y1, X0, Y0, vrs=False), "D24_23": dual(X0, Y0, X1, Y1, vrs=False)}
            m = mq[(mq.modelo == modelo) & (mq.version == version)].set_index("pte_codigo").loc[a0.pte_codigo]
            dmax = max(np.abs(m[c].to_numpy() - v).max() for c, v in D.items())
            check(f"{modelo} {version}: cuatro distancias = programa dual", dmax < TOL, f"diferencia máxima {dmax:.1e}")
            M = np.sqrt(D["D23_24"] / D["D23_23"] * D["D24_24"] / D["D24_23"])
            EC = D["D24_24"] / D["D23_23"]
            check(f"{modelo} {version}: M y EC recalculados", np.abs(m.malmquist - M).max() < TOL
                  and np.abs(m.cambio_eficiencia - EC).max() < TOL)
            check(f"{modelo} {version}: M = EC × TC",
                  np.abs(m.malmquist - m.cambio_eficiencia * m.cambio_tecnologico).max() < TOL)
        n_ = mq[(mq.modelo == modelo) & (mq.version == "nominal")].set_index("pte_codigo")
        r_ = mq[(mq.modelo == modelo) & (mq.version == "real")].set_index("pte_codigo")
        razon = (r_.malmquist / n_.malmquist)
        check(f"{modelo}: deflactar multiplica M por 1,052 y no cambia EC",
              np.allclose(razon, 1.052, atol=TOL) and np.allclose(r_.cambio_eficiencia, n_.cambio_eficiencia, atol=TOL),
              f"razón M real/nominal {razon.min():.4f}–{razon.max():.4f}")

    log(f"\nRESULTADO: {'TODO COINCIDE' if not FALLAS else 'HAY DIFERENCIAS: ' + '; '.join(FALLAS)}")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"verificacion_oe2_oe3_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")
    raise SystemExit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
