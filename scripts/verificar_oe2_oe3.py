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
  7. Cobertura sin la UNAD (oe3_cobertura_sin_unad.csv): la UNAD no está; eficiencias = dual;
     propiedades 2–4; y, como sacar una universidad de la muestra solo puede achicar la frontera,
     ninguna eficiencia sin la UNAD es menor que con ella.
  8. Características (caracteristicas_universidades.csv): una fila por universidad y año;
     porcentajes entre 0 y 100; tamaño, gasto por estudiante y % de ceros en Escrita recalculados
     desde la base integrada.
  9. Segunda etapa (oe3_segunda_etapa.csv): rho de Spearman, U de Mann-Whitney, el efecto, los p-valores y el
     ajuste de Holm recalculados con fórmulas escritas aquí (rangos, conteo de pares, distribución
     exacta de U por recursión, aproximación normal con corrección por empates), sin las funciones
     de scipy que usó el script original.

Uso (desde la raíz del repositorio, después de oe3_dea_bootstrap.py, oe2_malmquist.py,
oe3_cobertura_sin_unad.py y oe3_segunda_etapa.py):
    python scripts/verificar_oe2_oe3.py
"""
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, t as t_student

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


def u_exacta_cola(u, n1, n2):
    """P(U >= u) bajo H0, contando por recursión las ordenaciones de n1 + n2 elementos."""
    tope = n1 * n2
    f = [[None] * (n2 + 1) for _ in range(n1 + 1)]
    for i in range(n1 + 1):
        for j in range(n2 + 1):
            if i == 0 or j == 0:
                v = np.zeros(tope + 1)
                v[0] = 1
            else:
                v = f[i][j - 1].copy()          # el mayor elemento es de la muestra 2
                v[j:] += f[i - 1][j][:tope + 1 - j]   # el mayor es de la muestra 1: suma j
            f[i][j] = v
    c = f[n1][n2]
    return c[int(np.ceil(u - 1e-9)):].sum() / c.sum()


def mann_whitney_propio(a, b, exacta):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n1, n2 = len(a), len(b)
    u1 = (a[:, None] > b[None, :]).sum() + 0.5 * (a[:, None] == b[None, :]).sum()
    umax = max(u1, n1 * n2 - u1)
    if exacta:
        p = 2 * u_exacta_cola(umax, n1, n2)
    else:
        n = n1 + n2
        _, cuenta = np.unique(np.r_[a, b], return_counts=True)
        sigma = np.sqrt(n1 * n2 / 12 * ((n + 1) - (cuenta ** 3 - cuenta).sum() / (n * (n - 1))))
        p = 2 * norm.sf((umax - n1 * n2 / 2 - 0.5) / sigma)
    return u1, min(1.0, p)


def spearman_propio(x, y):
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    r = np.corrcoef(rx, ry)[0, 1]
    n = len(rx)
    tt = r * np.sqrt((n - 2) / (1 - r ** 2))
    return r, 2 * t_student.sf(abs(tt), n - 2)


def holm_propio(p):
    p = np.asarray(p, float)
    m, idx = len(p), np.argsort(p)
    ajust = np.minimum(1, np.maximum.accumulate((m - np.arange(m)) * p[idx]))
    out = np.empty(m)
    out[idx] = ajust
    return out


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

    log("\n7. Cobertura sin la UNAD (oe3_cobertura_sin_unad.csv)")
    su = pd.read_csv("resultados/oe3_cobertura_sin_unad.csv", dtype={"pte_codigo": str})
    check("la UNAD (225709) no está en el modelo", not (su.pte_codigo == "225709").any())
    for a in sorted(base.anio.unique()):
        d = base[(base.anio == a) & (base.pte_codigo != "225709")].reset_index(drop=True)
        X, Y = d[["obligacion_mm"]].to_numpy(float), d[MODELOS["cobertura"]].to_numpy(float)
        dd = dual(X, Y)
        e = su[su.anio == a].set_index("pte_codigo").loc[d.pte_codigo]
        check(f"sin UNAD {a}: {len(d)} universidades = las del DEA menos la UNAD",
              set(su[su.anio == a].pte_codigo) == set(d.pte_codigo))
        dif = np.abs(e.eficiencia.to_numpy() - dd)
        check(f"sin UNAD {a}: eficiencia = programa dual", dif.max() < TOL, f"diferencia máxima {dif.max():.1e}")
        check(f"sin UNAD {a}: eficiencias en (0, 1]", ((dd > 0) & (dd <= 1 + 1e-9)).all())
        okb = ((e.ic95_inf <= e.eficiencia_corregida + TOL) & (e.eficiencia_corregida <= e.ic95_sup + TOL)
               & (e.ic95_sup <= e.eficiencia + TOL)).all()
        check(f"sin UNAD {a}: ic inferior ≤ corregida ≤ ic superior ≤ original", bool(okb))
        okm = all((e[f"{p}_meta"] >= e[f"{p}_actual"] - TOL).all() for p in MODELOS["cobertura"])
        check(f"sin UNAD {a}: metas ≥ valor actual", okm)
        con = ef[(ef.modelo == "cobertura") & (ef.anio == a)].set_index("pte_codigo").loc[d.pte_codigo]
        check(f"sin UNAD {a}: ninguna eficiencia baja al sacar a la UNAD",
              bool((e.eficiencia.to_numpy() >= con.eficiencia.to_numpy() - TOL).all()))

    log("\n8. Características (caracteristicas_universidades.csv)")
    car = pd.read_csv("resultados/caracteristicas_universidades.csv", dtype={"pte_codigo": str})
    todas = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    k = car.merge(todas, on=["pte_codigo", "anio"], suffixes=("", "_b"))
    check("una fila por universidad y año, las mismas de la base integrada",
          len(car) == len(k) == len(todas) and not car.duplicated(["pte_codigo", "anio"]).any(),
          f"{len(car)} filas")
    pct = ["pct_mat_prog_acreditados", "pct_mat_distancia_virtual", "pct_mat_posgrado"]
    check("porcentajes entre 0 y 100", bool(((car[pct] >= 0) & (car[pct] <= 100)).all().all()))
    check("log_matricula = ln(matrícula promedio)",
          np.abs(k.log_matricula - np.log(k.mat_total_prom_b)).max() < TOL)
    check("millones_por_estudiante = obligación / matrícula / 10^6",
          np.abs(k.millones_por_estudiante - k.obligacion / k.mat_total_prom_b / 1e6).max() < TOL)
    check("% de ceros en Escrita = el de la base integrada",
          np.abs(k.pct_ceros_escrita - k.pct_ceros_escrita_b).max() < TOL)

    log("\n9. Segunda etapa (oe3_segunda_etapa.csv)")
    se = pd.read_csv("resultados/oe3_segunda_etapa.csv")
    todo = pd.concat([ef, su]).merge(car, on=["pte_codigo", "anio"], suffixes=("", "_c"))
    binarias = {"acreditada_institucional": (True, False), "domicilio_bogota": (True, False),
                "orden": ("nacional", "territorial")}
    peor_v = peor_p = peor_h = 0.0
    for (modelo, a), g in se.groupby(["modelo", "anio"]):
        t = todo[(todo.modelo == modelo) & (todo.anio == a)]
        y = t.eficiencia_corregida.to_numpy()
        vals, ps = [], []
        for r in g.itertuples():
            if r.tipo == "continua":
                v, p = spearman_propio(t[r.variable].to_numpy(float), y)
            else:
                va, vb = binarias[r.variable]
                v, p = mann_whitney_propio(y[(t[r.variable] == va).to_numpy()], y[(t[r.variable] == vb).to_numpy()],
                                           exacta="exacta" in r.estadistico)
            vals.append(v)
            ps.append(p)
        peor_v = max(peor_v, np.abs(np.array(vals) - g.valor.to_numpy()).max())
        n1n2 = np.array([1.0 if r.tipo == "continua" else
                         int(r.grupo_a.split("n=")[1][:-1]) * int(r.grupo_b.split("n=")[1][:-1]) for r in g.itertuples()])
        efecto = np.where(g.tipo == "continua", vals, 2 * np.array(vals) / n1n2 - 1)
        peor_v = max(peor_v, np.abs(efecto - g.efecto.to_numpy()).max())
        peor_p = max(peor_p, np.abs(np.array(ps) - g.p.to_numpy()).max())
        peor_h = max(peor_h, np.abs(holm_propio(ps) - g.p_holm.to_numpy()).max())
    check(f"{len(se)} estadísticos (rho, U y efecto) recalculados", peor_v < TOL, f"diferencia máxima {peor_v:.1e}")
    check("p-valores recalculados", peor_p < TOL, f"diferencia máxima {peor_p:.1e}")
    check("ajuste de Holm recalculado", peor_h < TOL, f"diferencia máxima {peor_h:.1e}")
    mec = se[se.mecanica].variable.unique().tolist()
    check("solo se marcan como mecánicas millones_por_estudiante y log_matricula",
          set(mec) <= {"millones_por_estudiante", "log_matricula"}, ", ".join(mec))

    log(f"\nRESULTADO: {'TODO COINCIDE' if not FALLAS else 'HAY DIFERENCIAS: ' + '; '.join(FALLAS)}")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"verificacion_oe2_oe3_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")
    raise SystemExit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
