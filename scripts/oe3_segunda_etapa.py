"""
oe3_segunda_etapa.py — Segunda etapa exploratoria del OE3: ¿qué características se asocian con la
eficiencia de las universidades públicas?

Con 32-33 universidades por año no se estima un modelo de regresión. Se usan pruebas no paramétricas:
  - variables continuas: correlación de Spearman con la eficiencia corregida por sesgo;
  - variables binarias: prueba de Mann-Whitney (dos colas) entre los dos grupos; exacta si un grupo
    tiene 8 o menos universidades y no hay empates, aproximación normal en otro caso.
Columna "efecto", en escala de -1 a 1 para poder comparar: rho en las continuas; en las binarias, la
correlación biserial de rangos r = 2U/(n_a·n_b) − 1 (positiva si el grupo A es más eficiente).
Los p-valores se ajustan por Holm dentro de cada modelo y año (10 pruebas). Es un análisis
EXPLORATORIO: las eficiencias DEA de una misma muestra no son independientes entre sí, así que los
p-valores son orientativos y no se interpretan como efectos causales.

Algunas asociaciones son MECÁNICAS (la variable se construye con el insumo o con un producto del
modelo) y se marcan como tales; no son hallazgos:
  millones_por_estudiante en todos los modelos; log_matricula en los modelos de cobertura.

Entradas: resultados/oe3_eficiencia.csv, resultados/oe3_cobertura_sin_unad.csv,
          resultados/caracteristicas_universidades.csv
Salida:   resultados/oe3_segunda_etapa.csv
Evidencia: docs/gobernanza/evidencias/oe3_segunda_etapa_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts/oe3_segunda_etapa.py
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

CONTINUAS = {
    "pct_mat_prog_acreditados": "% de matrícula en programas acreditados",
    "pct_mat_distancia_virtual": "% de matrícula a distancia o virtual",
    "pct_mat_posgrado": "% de matrícula en posgrado",
    "n_departamentos_oferta": "Departamentos donde ofrece programas",
    "log_matricula": "Tamaño (log de la matrícula)",
    "millones_por_estudiante": "Millones de pesos de la Nación por estudiante",
    "pct_ceros_escrita": "% de evaluados con 0 en Escrita",
}
BINARIAS = {
    "acreditada_institucional": ("Acreditación institucional", True, False, "acreditada", "no acreditada"),
    "domicilio_bogota": ("Domicilio en Bogotá", True, False, "Bogotá", "otro departamento"),
    "orden": ("Orden", "nacional", "territorial", "nacional", "territorial"),
}
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def holm(p):
    p = np.asarray(p, float)
    orden = np.argsort(p)
    m = len(p)
    ajust = np.empty(m)
    acum = 0.0
    for k, i in enumerate(orden):
        acum = max(acum, min(1.0, (m - k) * p[i]))
        ajust[i] = acum
    return ajust


def mecanica(var, modelo):
    return var == "millones_por_estudiante" or (var == "log_matricula" and modelo.startswith("cobertura"))


def main():
    ef = pd.concat([pd.read_csv("resultados/oe3_eficiencia.csv", dtype={"pte_codigo": str}),
                    pd.read_csv("resultados/oe3_cobertura_sin_unad.csv", dtype={"pte_codigo": str})])
    car = pd.read_csv("resultados/caracteristicas_universidades.csv", dtype={"pte_codigo": str})
    d = ef.merge(car, on=["pte_codigo", "anio"], how="left", suffixes=("", "_c"))
    faltan = d[d.pct_mat_posgrado.isna()]
    if len(faltan):
        raise SystemExit(f"[ERROR] universidades sin características: {faltan.pte_nombre.unique()}")
    log(f"##### OE3 — segunda etapa exploratoria — {datetime.now():%Y-%m-%d %H:%M} #####")

    filas = []
    for (modelo, anio), g in d.groupby(["modelo", "anio"]):
        y = g.eficiencia_corregida
        res = []
        for v, et in CONTINUAS.items():
            r, p = stats.spearmanr(g[v], y)
            res.append(dict(variable=v, etiqueta=et, tipo="continua", n=len(g), estadistico="Spearman rho",
                            valor=r, efecto=r, p=p, grupo_a="", mediana_a=np.nan, grupo_b="", mediana_b=np.nan))
        for v, (et, va, vb, na, nb) in BINARIAS.items():
            a = y[g[v] == va]
            b = y[g[v] == vb]
            # método explícito (no el "auto" de scipy, que cambia entre versiones): exacto si un grupo
            # tiene 8 o menos universidades y no hay empates; si no, normal con corrección por continuidad
            met = "exact" if min(len(a), len(b)) <= 8 and np.unique(np.r_[a, b]).size == len(a) + len(b) \
                else "asymptotic"
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided", method=met)
            res.append(dict(variable=v, etiqueta=et, tipo="binaria", n=len(a) + len(b),
                            estadistico=f"Mann-Whitney U ({'exacta' if met == 'exact' else 'normal'})", valor=u, efecto=2 * u / (len(a) * len(b)) - 1, p=p,
                            grupo_a=f"{na} (n={len(a)})", mediana_a=a.median(),
                            grupo_b=f"{nb} (n={len(b)})", mediana_b=b.median()))
        padj = holm([r["p"] for r in res])
        for r, pa in zip(res, padj):
            r.update(modelo=modelo, anio=anio, p_holm=pa, mecanica=mecanica(r["variable"], modelo))
            filas.append(r)
        log(f"\n=== {modelo} · {anio} (n = {len(g)}) ===")
        for r in sorted(res, key=lambda r: r["p"]):
            marca = " [mecánica]" if r["mecanica"] else ""
            if r["tipo"] == "continua":
                txt = f"rho = {r['valor']:+.2f}"
            else:
                txt = f"mediana {r['grupo_a']} {r['mediana_a']:.3f} vs {r['grupo_b']} {r['mediana_b']:.3f}"
            log(f"  {r['etiqueta']:47s} {txt:55s} p = {r['p']:.4f}  p Holm = {r['p_holm']:.4f}{marca}")

    out = pd.DataFrame(filas)[["modelo", "anio", "variable", "etiqueta", "tipo", "n", "estadistico", "valor", "efecto", "p",
                               "p_holm", "mecanica", "grupo_a", "mediana_a", "grupo_b", "mediana_b"]]
    num = ["valor", "efecto", "p", "p_holm", "mediana_a", "mediana_b"]
    out[num] = out[num].round(4)
    out.to_csv("resultados/oe3_segunda_etapa.csv", index=False, encoding="utf-8-sig")
    # asociaciones sustantivas (no mecánicas) significativas tras Holm en LOS DOS años
    s = out[(~out.mecanica) & (out.p_holm < 0.05)]
    robustas = s.groupby(["modelo", "variable"]).anio.nunique()
    log("\nAsociaciones no mecánicas con p Holm < 0,05 en los dos años:")
    for (m, v) in robustas[robustas == 2].index:
        x = out[(out.modelo == m) & (out.variable == v)]
        log(f"  {m}: {x.etiqueta.iloc[0]} — valores {x.valor.round(2).tolist()} (2023, 2024)")
    if not (robustas == 2).any():
        log("  ninguna")
    # contexto: una variable muy correlacionada con un producto del modelo repite, en buena parte,
    # la asociación de ese producto con la eficiencia
    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    b = base[base.incluida_dea].merge(car, on=["pte_codigo", "anio"], suffixes=("", "_c"))
    log("\nContexto — Spearman de cada variable continua con los productos (33 universidades del DEA):")
    for anio, g in b.groupby("anio"):
        for v in CONTINUAS:
            if v in ("millones_por_estudiante", "log_matricula"):
                continue
            r = {p: g[v].corr(g[p], method="spearman") for p in ("mat_total_prom", "grad_total", "global_c")}
            log(f"  {anio} {CONTINUAS[v]:47s} " + "  ".join(f"{p} {x:+.2f}" for p, x in r.items()))
    log("\nGuardado: resultados/oe3_segunda_etapa.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"oe3_segunda_etapa_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
