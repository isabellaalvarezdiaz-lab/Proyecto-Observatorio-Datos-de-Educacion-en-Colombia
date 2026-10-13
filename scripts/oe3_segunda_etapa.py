"""
oe3_segunda_etapa.py — Segunda etapa exploratoria del OE3: ¿qué características se asocian con la
eficiencia de las universidades públicas?

Con 32-33 universidades por año no se estima un modelo de regresión. Se usan pruebas no paramétricas:
  - variables continuas: correlación de Spearman con la eficiencia corregida por sesgo;
  - variables binarias: prueba de Mann-Whitney (dos colas) entre los dos grupos; exacta si un grupo
    tiene 8 o menos universidades y no hay empates, aproximación normal en otro caso.
Hay dos familias de pruebas, cada una con su propio ajuste de Holm (columna "familia"):
  - "institucional": las 10 características de siempre (7 continuas y 3 binarias);
  - "socioeconomica": 2 variables del perfil de los evaluados en Saber Pro (% en estratos 1 y 2 y % cuya
    madre llegó hasta secundaria). Responde al compromiso del anteproyecto de contextualizar las
    eficiencias bajas con variables socioeconómicas.
Además guarda, para cada modelo y año, las 5 universidades menos eficientes con su perfil
socioeconómico (resultados/oe3_contexto_menos_eficientes.csv).

Columna "efecto", en escala de -1 a 1 para poder comparar: rho en las continuas; en las binarias, la
correlación biserial de rangos r = 2U/(n_a·n_b) − 1 (positiva si el grupo A es más eficiente).
Los p-valores se ajustan por Holm dentro de cada modelo, año y familia. Es un análisis
EXPLORATORIO: las eficiencias DEA de una misma muestra no son independientes entre sí, así que los
p-valores son orientativos y no se interpretan como efectos causales.

Algunas asociaciones son MECÁNICAS (la variable se construye con el insumo o con un producto del
modelo) y se marcan como tales; no son hallazgos:
  millones_por_estudiante en todos los modelos; log_matricula en los modelos de cobertura.

Entradas: resultados/oe3_eficiencia.csv, resultados/oe3_cobertura_sin_unad.csv,
          resultados/caracteristicas_universidades.csv
Salidas:  resultados/oe3_segunda_etapa.csv, resultados/oe3_contexto_menos_eficientes.csv
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
SOCIO = {
    "pct_estrato_1_2": "% de evaluados en estratos 1 y 2",
    "pct_madre_hasta_secundaria": "% de evaluados con madre hasta secundaria",
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
            res.append(dict(familia="institucional", variable=v, etiqueta=et, tipo="continua", n=len(g),
                            estadistico="Spearman rho", valor=r, efecto=r, p=p,
                            grupo_a="", mediana_a=np.nan, grupo_b="", mediana_b=np.nan))
        for v, (et, va, vb, na, nb) in BINARIAS.items():
            a = y[g[v] == va]
            b = y[g[v] == vb]
            # método explícito (no el "auto" de scipy, que cambia entre versiones): exacto si un grupo
            # tiene 8 o menos universidades y no hay empates; si no, normal con corrección por continuidad
            met = "exact" if min(len(a), len(b)) <= 8 and np.unique(np.r_[a, b]).size == len(a) + len(b) \
                else "asymptotic"
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided", method=met)
            res.append(dict(familia="institucional", variable=v, etiqueta=et, tipo="binaria", n=len(a) + len(b),
                            estadistico=f"Mann-Whitney U ({'exacta' if met == 'exact' else 'normal'})", valor=u, efecto=2 * u / (len(a) * len(b)) - 1, p=p,
                            grupo_a=f"{na} (n={len(a)})", mediana_a=a.median(),
                            grupo_b=f"{nb} (n={len(b)})", mediana_b=b.median()))
        for v, et in SOCIO.items():
            r, p = stats.spearmanr(g[v], y)
            res.append(dict(familia="socioeconomica", variable=v, etiqueta=et, tipo="continua", n=len(g),
                            estadistico="Spearman rho", valor=r, efecto=r, p=p,
                            grupo_a="", mediana_a=np.nan, grupo_b="", mediana_b=np.nan))
        for fam in ("institucional", "socioeconomica"):
            rf = [r for r in res if r["familia"] == fam]
            for r, pa in zip(rf, holm([r["p"] for r in rf])):
                r.update(modelo=modelo, anio=anio, p_holm=pa, mecanica=mecanica(r["variable"], modelo))
        filas.extend(res)
        log(f"\n=== {modelo} · {anio} (n = {len(g)}) ===")
        for r in sorted(res, key=lambda r: r["p"]):
            marca = " [mecánica]" if r["mecanica"] else ""
            if r["tipo"] == "continua":
                txt = f"rho = {r['valor']:+.2f}"
            else:
                txt = f"mediana {r['grupo_a']} {r['mediana_a']:.3f} vs {r['grupo_b']} {r['mediana_b']:.3f}"
            fam = "  [socioeconómica]" if r["familia"] == "socioeconomica" else ""
            log(f"  {r['etiqueta']:47s} {txt:55s} p = {r['p']:.4f}  p Holm = {r['p_holm']:.4f}{marca}{fam}")

    out = pd.DataFrame(filas)[["modelo", "anio", "familia", "variable", "etiqueta", "tipo", "n", "estadistico", "valor", "efecto", "p",
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
        for v in list(CONTINUAS) + list(SOCIO):
            if v in ("millones_por_estudiante", "log_matricula"):
                continue
            r = {p: g[v].corr(g[p], method="spearman") for p in ("mat_total_prom", "grad_total", "global_c")}
            log(f"  {anio} {(CONTINUAS | SOCIO)[v]:47s} " + "  ".join(f"{p} {x:+.2f}" for p, x in r.items()))

    # contexto de las 5 menos eficientes de cada modelo y año (compromiso ético del anteproyecto)
    ctx = []
    for (modelo, anio), g in d.groupby(["modelo", "anio"]):
        g = g.copy()
        g["puesto_estrato_1_2"] = g.pct_estrato_1_2.rank(ascending=False, method="min").astype(int)
        g["puesto_madre_hasta_sec"] = g.pct_madre_hasta_secundaria.rank(ascending=False, method="min").astype(int)
        peores = g.nsmallest(5, "eficiencia_corregida")
        for k, r in enumerate(peores.itertuples(), 1):
            ctx.append(dict(modelo=modelo, anio=anio, puesto_eficiencia=k, n=len(g), pte_codigo=r.pte_codigo,
                            pte_nombre=r.pte_nombre, eficiencia_corregida=r.eficiencia_corregida,
                            ic95_inf=r.ic95_inf, ic95_sup=r.ic95_sup,
                            pct_estrato_1_2=r.pct_estrato_1_2, puesto_estrato_1_2=r.puesto_estrato_1_2,
                            pct_madre_hasta_secundaria=r.pct_madre_hasta_secundaria,
                            puesto_madre_hasta_sec=r.puesto_madre_hasta_sec,
                            mediana_estrato_1_2=g.pct_estrato_1_2.median(),
                            mediana_madre_hasta_sec=g.pct_madre_hasta_secundaria.median(),
                            departamento_domicilio=r.departamento_domicilio,
                            pct_mat_distancia_virtual=r.pct_mat_distancia_virtual))
    ctx = pd.DataFrame(ctx)
    num = ctx.select_dtypes("number").columns.drop(["anio", "puesto_eficiencia", "n", "puesto_estrato_1_2",
                                                     "puesto_madre_hasta_sec"])
    ctx[num] = ctx[num].round(4)
    ctx.to_csv("resultados/oe3_contexto_menos_eficientes.csv", index=False, encoding="utf-8-sig")
    log("\nLas 5 menos eficientes y su perfil (puesto 1 = mayor % entre las n universidades del modelo):")
    for (m, a), g in ctx.groupby(["modelo", "anio"]):
        log(f"  {m} {a} — medianas: estratos 1-2 {g.mediana_estrato_1_2.iloc[0]:.1f} %, "
            f"madre hasta secundaria {g.mediana_madre_hasta_sec.iloc[0]:.1f} %")
        for r in g.itertuples():
            log(f"    {r.puesto_eficiencia}. {r.pte_nombre:52s} ef. {r.eficiencia_corregida:.3f} | estratos 1-2 "
                f"{r.pct_estrato_1_2:5.1f} % (puesto {r.puesto_estrato_1_2:2d} de {r.n}) | madre hasta sec. "
                f"{r.pct_madre_hasta_secundaria:5.1f} % (puesto {r.puesto_madre_hasta_sec:2d})")
    log("Guardado: resultados/oe3_contexto_menos_eficientes.csv")
    log("\nGuardado: resultados/oe3_segunda_etapa.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"oe3_segunda_etapa_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
