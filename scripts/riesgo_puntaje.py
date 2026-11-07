"""
riesgo_puntaje.py — Riesgo de cola del desempeño en Saber Pro por universidad pública (2023-2024):
VaR y CVaR no paramétricos por simulación histórica, intervalos bootstrap y backtesting de Kupiec.

Idea
  En Teoría del Riesgo, el VaR resume la cola mala de una distribución de pérdidas y el CVaR
  (Expected Shortfall) dice cuánto se pierde en promedio dentro de esa cola. Aquí la "pérdida" es
  quedar con un puntaje bajo: la cola mala de cada universidad son sus evaluados de menor puntaje.
  No es riesgo financiero; es la misma herramienta aplicada al desempeño académico.

Definiciones (nivel α = 0,05 por defecto; n evaluados de la universidad en el año; k = ⌈α·n⌉)
  Puntaje: global_c, el mismo producto "puntaje" del DEA (si el evaluado tiene 0 en Comunicación
           Escrita, se usa el promedio de sus otros cuatro módulos; ver agregar_saber_pro.py).
  VaR_α  : el k-ésimo puntaje más bajo = cuantil empírico α (cuantil "inverted_cdf"). El 5 % más
           rezagado de los evaluados queda en ese puntaje o por debajo. Simulación histórica pura:
           no se supone ninguna distribución.
  CVaR_α : el promedio de los k puntajes más bajos (la cola del 5 %).
  Brecha de cola: media − CVaR_α. Cuánto se separan los más rezagados del promedio de su universidad.
  Intervalos: bootstrap no paramétrico de percentiles, remuestreando evaluados dentro de cada
           universidad (B réplicas, 95 %).

Backtesting de Kupiec (prueba de proporción de fallas, POF), 2023 → 2024
  Para cada universidad, el VaR de 2023 se usa como pronóstico para la cohorte de 2024: si la cola
  no cambió, la proporción de evaluados de 2024 por debajo del VaR de 2023 debe ser α.
      LR = −2 ln[(1−α)^(n−x) α^x] + 2 ln[(1−x/n)^(n−x) (x/n)^x]  ~  χ²(1)
  Los puntajes son enteros, así que muchos evaluados empatan justo en el VaR. Para que la
  frecuencia esperada sea exactamente α, los empates en el VaR se cuentan con el peso
  w = (α·n₂₀₂₃ − #{<VaR}₂₀₂₃) / #{=VaR}₂₀₂₃, el mismo en los dos años (cuantil aleatorizado):
      x = #{puntaje < VaR} + w · #{puntaje = VaR}
  Con w así, en 2023 la proporción es α por construcción. Los p-valores se ajustan por Holm entre
  las 33 universidades. Una proporción mayor que α indica que la cola de 2024 empeoró frente a la de
  2023; una menor, que mejoró.
  Cambio de cohorte: la misma prueba para el total nacional dice si TODA la cohorte se movió. Como
  con cientos de miles de evaluados Kupiec detecta cambios muy pequeños, se agrega una segunda
  prueba por universidad con la tasa nacional de 2024 como referencia (p₀ = tasa nacional en vez de
  α): rechazar ahí indica un cambio propio de la universidad, no de toda la cohorte. Se reporta la
  tasa observada para juzgar el tamaño del cambio, no solo su significancia.

Asociaciones (exploratorias, como la segunda etapa del OE3): Spearman entre las medidas de cola y
  el % de evaluados en estratos 1 y 2 y la eficiencia corregida del modelo principal.

Entradas: data/raw/saber_pro/Examen_Saber_Pro_Genericas_AAAA.txt (microdatos; no se suben),
          resultados/sedes_por_universidad.csv, resultados/base_integrada_2023_2024.csv,
          resultados/caracteristicas_universidades.csv, resultados/oe3_eficiencia.csv
Salidas:  resultados/riesgo_puntaje.csv              VaR, CVaR e intervalos por universidad y año
          resultados/riesgo_kupiec.csv               backtesting 2023 → 2024
          resultados/riesgo_puntaje_asociaciones.csv  Spearman exploratorios
Evidencia: docs/gobernanza/evidencias/riesgo_puntaje_AAAA-MM-DD_HHMM.txt

Publicación: las tablas son agregados por universidad. La cola más pequeña tiene 12 evaluados
  (U. del Trópico Americano en 2023 y U. del Pacífico en 2024; por encima de K_MIN = 5 de publicacion.py); si alguna quedara por
  debajo, su CVaR no se publica.

Uso (desde la raíz del repositorio; tarda menos de un minuto con B = 2000):
    python scripts/riesgo_puntaje.py
    python scripts/riesgo_puntaje.py --alfa 0.05 --B 2000 --semilla 20261106

Requiere: pandas, numpy, scipy.
"""
import argparse
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from publicacion import K_MIN

MODULOS = ["mod_competen_ciudada_punt", "mod_comuni_escrita_punt", "mod_ingles_punt",
           "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
OTROS_4 = [m for m in MODULOS if m != "mod_comuni_escrita_punt"]
LOG = []


def log(texto=""):
    print(texto)
    LOG.append(str(texto))


def leer_puntajes(ruta):
    """Evaluados con código de institución y puntaje global (misma población que
    agregar_saber_pro.py), con el puntaje global_c."""
    d = pd.read_csv(ruta, sep=";", low_memory=False,
                    usecols=MODULOS + ["punt_global", "inst_cod_institucion"])
    d = d.dropna(subset=["inst_cod_institucion", "punt_global"])
    cero = d["mod_comuni_escrita_punt"].eq(0)
    d["global_c"] = d["punt_global"].where(~cero, d[OTROS_4].mean(axis=1))
    d["cod_institucion"] = d["inst_cod_institucion"].astype("int64")
    return d[["cod_institucion", "global_c"]]


def var_cvar(x, alfa):
    """VaR (k-ésimo valor más bajo) y CVaR (promedio de los k más bajos), k = ⌈α·n⌉."""
    x = np.asarray(x, float)
    k = math.ceil(alfa * len(x))
    cola = np.partition(x, k - 1)[:k]
    return cola.max(), cola.mean(), k


def bootstrap_cola(x, alfa, B, rng):
    """Intervalos bootstrap de percentiles (95 %) del VaR y del CVaR."""
    x = np.asarray(x, float)
    n = len(x)
    k = math.ceil(alfa * n)
    v = np.empty(B)
    c = np.empty(B)
    for b in range(B):
        m = x[rng.integers(0, n, n)]
        cola = np.partition(m, k - 1)[:k]
        v[b] = cola.max()
        c[b] = cola.mean()
    return np.percentile(v, [2.5, 97.5]), np.percentile(c, [2.5, 97.5])


def kupiec(x, n, alfa):
    """Estadístico LR de proporción de fallas de Kupiec y su p-valor (χ² con 1 g.l.).
    x puede no ser entero (empates ponderados)."""
    p_hat = x / n

    def ll(p):
        a = (n - x) * math.log(1 - p) if n - x > 0 else 0.0
        b = x * math.log(p) if x > 0 else 0.0
        return a + b

    lr = -2 * (ll(alfa) - ll(p_hat)) if 0 < p_hat < 1 else -2 * (ll(alfa) - 0.0)
    lr = max(lr, 0.0)
    return lr, stats.chi2.sf(lr, 1)


def holm(p):
    p = np.asarray(p, float)
    m, idx = len(p), np.argsort(p)
    ajust = np.minimum(1, np.maximum.accumulate((m - np.arange(m)) * p[idx]))
    out = np.empty(m)
    out[idx] = ajust
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alfa", type=float, default=0.05)
    ap.add_argument("--B", type=int, default=2000, help="réplicas bootstrap por universidad y año")
    ap.add_argument("--semilla", type=int, default=20261106)
    ap.add_argument("--saber-dir", default=str(Path("data") / "raw" / "saber_pro"))
    args = ap.parse_args()
    a = args.alfa
    rng = np.random.default_rng(args.semilla)
    res = Path("resultados")

    log(f"##### Riesgo de cola del puntaje Saber Pro — {datetime.now():%Y-%m-%d %H:%M} #####")
    log(f"α = {a} | B = {args.B} | semilla = {args.semilla} | puntaje = global_c")

    sedes = pd.read_csv(res / "sedes_por_universidad.csv")[["pte_codigo", "cod_institucion"]]
    base = pd.read_csv(res / "base_integrada_2023_2024.csv")
    dea = base[base.incluida_dea][["pte_codigo", "anio", "pte_nombre"]]
    univ = dea.drop_duplicates("pte_codigo").set_index("pte_codigo")["pte_nombre"]
    log(f"Universidades del DEA: {len(univ)}")

    puntajes = {}
    for anio in (2023, 2024):
        d = leer_puntajes(Path(args.saber_dir) / f"Examen_Saber_Pro_Genericas_{anio}.txt")
        nac = d["global_c"].to_numpy()
        d = d.merge(sedes, on="cod_institucion", how="inner")
        d = d[d.pte_codigo.isin(univ.index)]
        puntajes[anio] = {"nacional": nac, "33 universidades": d["global_c"].to_numpy()}
        for cod, g in d.groupby("pte_codigo"):
            puntajes[anio][cod] = g["global_c"].to_numpy()
        n_u = {k: len(v) for k, v in puntajes[anio].items() if not isinstance(k, str)}
        log(f"\n{anio}: evaluados nacionales {len(nac):,} | en las 33 universidades {len(d):,} | "
            f"universidades con evaluados {len(n_u)} | mínimo por universidad {min(n_u.values())}")
        faltan = sorted(set(univ.index) - set(n_u))
        if faltan:
            log(f"  [REVISAR] universidades del DEA sin evaluados en {anio}: {faltan}")

    # ---------------------------------------------------------- VaR y CVaR
    filas = []
    for anio in (2023, 2024):
        for clave, x in puntajes[anio].items():
            v, c, k = var_cvar(x, a)
            ic_v, ic_c = bootstrap_cola(x, a, args.B, rng)
            nombre = clave if isinstance(clave, str) else univ[clave]
            filas.append(dict(
                anio=anio, pte_codigo=None if isinstance(clave, str) else int(clave),
                pte_nombre=nombre, n_evaluados=len(x), alfa=a, k_cola=k,
                media=x.mean(), var=v, var_ic_inf=ic_v[0], var_ic_sup=ic_v[1],
                cvar=c, cvar_ic_inf=ic_c[0], cvar_ic_sup=ic_c[1], brecha_cola=x.mean() - c))
    tabla = pd.DataFrame(filas)
    peq = tabla.k_cola < K_MIN
    for col in ("cvar", "cvar_ic_inf", "cvar_ic_sup", "brecha_cola"):
        tabla.loc[peq, col] = np.nan
    tabla["suprimido"] = peq
    num = ["media", "var", "var_ic_inf", "var_ic_sup", "cvar", "cvar_ic_inf", "cvar_ic_sup", "brecha_cola"]
    tabla[num] = tabla[num].round(2)

    for anio in (2023, 2024):
        t = tabla[(tabla.anio == anio) & tabla.pte_codigo.notna()]
        log(f"\n=== VaR y CVaR al {100 * (1 - a):.0f} %, {anio} (puntaje global_c) ===")
        for ref in ("nacional", "33 universidades"):
            r = tabla[(tabla.anio == anio) & (tabla.pte_nombre == ref)].iloc[0]
            log(f"  {ref:20s} n={r.n_evaluados:>7,} media={r.media:6.1f} VaR={r['var']:6.1f} "
                f"CVaR={r.cvar:6.1f} brecha={r.brecha_cola:5.1f}")
        log(f"  cola más pequeña: k = {t.k_cola.min()} evaluados (K_MIN = {K_MIN})")
        log("  5 universidades con la cola más baja (CVaR):")
        for _, r in t.nsmallest(5, "cvar").iterrows():
            log(f"    {r.pte_nombre[:48]:48s} n={r.n_evaluados:>6} VaR={r['var']:6.1f} "
                f"[{r.var_ic_inf:.0f}; {r.var_ic_sup:.0f}]  CVaR={r.cvar:6.1f} "
                f"[{r.cvar_ic_inf:.1f}; {r.cvar_ic_sup:.1f}]  brecha={r.brecha_cola:5.1f}")
        log("  5 universidades con la brecha de cola más grande (media − CVaR):")
        for _, r in t.nlargest(5, "brecha_cola").iterrows():
            log(f"    {r.pte_nombre[:48]:48s} media={r.media:6.1f} CVaR={r.cvar:6.1f} brecha={r.brecha_cola:5.1f}")

    # ------------------------------------------------- Kupiec 2023 → 2024
    kup = []
    for clave in puntajes[2023]:
        x23, x24 = puntajes[2023][clave], puntajes[2024].get(clave)
        if x24 is None:
            continue
        v, _, _ = var_cvar(x23, a)
        n23, lt23, eq23 = len(x23), int((x23 < v).sum()), int((x23 == v).sum())
        w = min(max((a * n23 - lt23) / eq23, 0.0), 1.0)
        n24, lt24, eq24 = len(x24), int((x24 < v).sum()), int((x24 == v).sum())
        x = lt24 + w * eq24
        lr, p = kupiec(x, n24, a)
        nombre = clave if isinstance(clave, str) else univ[clave]
        kup.append(dict(pte_codigo=None if isinstance(clave, str) else int(clave), pte_nombre=nombre,
                        alfa=a, var_2023=v, peso_empates=round(w, 4),
                        tasa_2023=round((lt23 + w * eq23) / n23, 4),
                        n_2024=n24, fallas_2024=round(x, 2), tasa_2024=round(x / n24, 4),
                        lr_kupiec=round(lr, 3), p=p, x_crudo=x))
    kup = pd.DataFrame(kup)
    nac = kup.pte_nombre == "nacional"
    tasa_nac = float(kup.loc[nac, "x_crudo"].iloc[0] / kup.loc[nac, "n_2024"].iloc[0])
    rel = [kupiec(r.x_crudo, r.n_2024, tasa_nac) for r in kup.itertuples()]
    kup["tasa_ref_nacional"] = round(tasa_nac, 4)
    kup["lr_relativo"] = [round(l, 3) for l, _ in rel]
    kup["p_relativo"] = [q for _, q in rel]
    kup = kup.drop(columns="x_crudo")
    es_u = kup.pte_codigo.notna()
    kup["p_holm"] = np.nan
    kup.loc[es_u, "p_holm"] = holm(kup.loc[es_u, "p"])
    kup["rechaza_5pct"] = np.where(es_u, kup.p_holm < 0.05, kup.p < 0.05)
    kup["direccion"] = np.where(kup.tasa_2024 > a, "cola peor en 2024", "cola mejor en 2024")
    kup.loc[~kup.rechaza_5pct, "direccion"] = "sin cambio detectable"
    kup["p_relativo_holm"] = np.nan
    kup.loc[es_u, "p_relativo_holm"] = holm(kup.loc[es_u, "p_relativo"])
    kup["rechaza_relativo"] = es_u & (kup.p_relativo_holm < 0.05)
    kup["direccion_relativa"] = np.where(kup.tasa_2024 > tasa_nac, "peor que el cambio nacional",
                                         "mejor que el cambio nacional")
    kup.loc[~kup.rechaza_relativo, "direccion_relativa"] = "como el cambio nacional"
    kup.loc[~es_u, "direccion_relativa"] = ""
    for c in ("p", "p_holm", "p_relativo", "p_relativo_holm"):
        kup[c] = kup[c].round(6)

    log(f"\n=== Backtesting de Kupiec: VaR de 2023 frente a la cohorte de 2024 (α = {a}) ===")
    for ref in ("nacional", "33 universidades"):
        r = kup[kup.pte_nombre == ref].iloc[0]
        log(f"  {ref:20s} VaR2023={r.var_2023:.1f} tasa2024={100 * r.tasa_2024:.2f} % "
            f"LR={r.lr_kupiec:.2f} p={r.p:.4f}")
    ku = kup[es_u]
    log(f"  Universidades: {int(ku.rechaza_5pct.sum())} de {len(ku)} rechazan con Holm al 5 % "
        f"({int((ku.direccion == 'cola peor en 2024').sum())} peor, "
        f"{int((ku.direccion == 'cola mejor en 2024').sum())} mejor)")
    log(f"  comprobación: tasa de 2023 = α en todas: {bool(np.allclose(ku.tasa_2023, a, atol=1e-4))}")
    for _, r in ku[ku.rechaza_5pct].sort_values("p").iterrows():
        log(f"    {r.pte_nombre[:48]:48s} tasa2024={100 * r.tasa_2024:5.2f} % LR={r.lr_kupiec:7.2f} "
            f"p_holm={r.p_holm:.4f} → {r.direccion}")
    log(f"  Frente al cambio nacional (p₀ = {100 * tasa_nac:.2f} %): {int(ku.rechaza_relativo.sum())} de "
        f"{len(ku)} rechazan con Holm al 5 %")
    for _, r in ku[ku.rechaza_relativo].sort_values("p_relativo").iterrows():
        log(f"    {r.pte_nombre[:48]:48s} tasa2024={100 * r.tasa_2024:5.2f} % LR={r.lr_relativo:7.2f} "
            f"p_holm={r.p_relativo_holm:.4f} → {r.direccion_relativa}")

    # ------------------------------------------------------- asociaciones
    car = pd.read_csv(res / "caracteristicas_universidades.csv")[["pte_codigo", "anio", "pct_estrato_1_2"]]
    ef = pd.read_csv(res / "oe3_eficiencia.csv")
    ef = ef[ef.modelo == "principal"][["pte_codigo", "anio", "eficiencia_corregida"]]
    tu = tabla[tabla.pte_codigo.notna()].copy()
    tu["pte_codigo"] = tu.pte_codigo.astype(int)
    tu = tu.merge(car, on=["pte_codigo", "anio"]).merge(ef, on=["pte_codigo", "anio"])
    aso = []
    log("\n=== Asociaciones exploratorias (Spearman, 33 universidades) ===")
    for anio in (2023, 2024):
        t = tu[tu.anio == anio]
        for medida in ("var", "cvar", "brecha_cola"):
            for otra in ("pct_estrato_1_2", "eficiencia_corregida"):
                rho, p = stats.spearmanr(t[medida], t[otra])
                aso.append(dict(anio=anio, medida=medida, variable=otra, n=len(t),
                                rho=round(rho, 4), p=round(p, 6)))
                log(f"  {anio} {medida:12s} vs {otra:21s} rho={rho:+.3f} p={p:.4f}")
    aso = pd.DataFrame(aso)

    log("\n=== ¿Qué agrega la cola frente al promedio? (puesto por media vs. puesto por CVaR) ===")
    for anio in (2023, 2024):
        t = tu[tu.anio == anio].copy()
        rho, _ = stats.spearmanr(t.media, t.cvar)
        t["puesto_media"] = t.media.rank(ascending=False, method="min").astype(int)
        t["puesto_cvar"] = t.cvar.rank(ascending=False, method="min").astype(int)
        t["salto"] = t.puesto_media - t.puesto_cvar
        log(f"  {anio}: Spearman media vs CVaR = {rho:.3f}; universidades que se mueven 5 puestos o más: "
            f"{int((t.salto.abs() >= 5).sum())}")
        for _, r in t.reindex(t.salto.abs().sort_values(ascending=False).index).head(4).iterrows():
            log(f"    {r.pte_nombre[:48]:48s} puesto por media {r.puesto_media:2d} → por CVaR {r.puesto_cvar:2d}")
        aso.loc[len(aso)] = dict(anio=anio, medida="cvar", variable="media", n=len(t),
                                 rho=round(rho, 4), p=np.nan)

    tabla.to_csv(res / "riesgo_puntaje.csv", index=False, encoding="utf-8-sig")
    kup.to_csv(res / "riesgo_kupiec.csv", index=False, encoding="utf-8-sig")
    aso.to_csv(res / "riesgo_puntaje_asociaciones.csv", index=False, encoding="utf-8-sig")
    log("\nGuardados: resultados/riesgo_puntaje.csv, riesgo_kupiec.csv, riesgo_puntaje_asociaciones.csv")

    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"riesgo_puntaje_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"\nEvidencia guardada en {ev}")


if __name__ == "__main__":
    main()
