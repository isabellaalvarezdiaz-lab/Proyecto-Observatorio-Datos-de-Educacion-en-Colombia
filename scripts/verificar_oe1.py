"""
verificar_oe1.py — Comprueba la tabla maestra y la base integrada contra los ARCHIVOS ORIGINALES.

Recalcula todo por un camino distinto al de los scripts que construyen las tablas: lee los Excel
y los .txt crudos directamente (no las copias de data/interim ni las tablas intermedias de
resultados/) y compara cifra por cifra. Si algo no coincide, lo dice con la universidad y la columna.

Qué comprueba:
  1. PTE: que la fila de Excel citada en resultados/pte_universidades_2023_2024.csv contenga de
     verdad el código de esa universidad y que su obligación sea la misma de la base.
  2. SNIES: matrícula por semestre y graduados de cada universidad, sumando sus sedes desde el Excel.
  3. Saber Pro: evaluados, ceros en Escrita y puntaje global_c de cada universidad, calculados
     estudiante por estudiante desde el .txt (sin pasar por los promedios redondeados por sede).
  4. Tabla maestra: que sus totales nacionales sean los de los archivos originales.

Uso (desde la raíz del repositorio, después de correr_oe1.py):
    python scripts/verificar_oe1.py
"""
from datetime import datetime
from pathlib import Path

import pandas as pd

COD = "CÓDIGO DE LA INSTITUCIÓN"
MOD = ["mod_competen_ciudada_punt", "mod_comuni_escrita_punt", "mod_ingles_punt",
       "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
LOG, FALLAS = [], []


def log(t=""):
    print(t)
    LOG.append(str(t))


def comparar(nombre, esperado, obtenido, tol=0.0):
    """esperado/obtenido: Series con el mismo índice (universidad, año)."""
    def norm(s):
        s = s.astype(float).copy()
        s.index = pd.MultiIndex.from_tuples([(str(u), int(a)) for u, a in s.index])
        return s
    e, o = norm(esperado).align(norm(obtenido), join="outer")
    dif = (e - o).abs()
    malas = dif[(dif > tol) | (e.isna() != o.isna())]
    if len(malas):
        FALLAS.append(nombre)
        log(f"  FALLA  {nombre}: {len(malas)} diferencias")
        for k in malas.index[:5]:
            log(f"         {k}: archivo original={e[k]} | tabla={o[k]}")
    else:
        log(f"  PASA   {nombre} ({len(e)} valores, diferencia máxima {dif.max():.4g})")


def main():
    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    base = base.set_index(["pte_codigo", "anio"])
    sedes = pd.read_csv("resultados/sedes_por_universidad.csv", dtype=str)
    mapa = dict(zip(sedes.cod_institucion, sedes.pte_codigo))
    pte = pd.read_csv("resultados/pte_universidades_2023_2024.csv", dtype={"pte_codigo": str})
    anios = sorted(pte.anio.unique())
    log(f"##### Verificación del OE1 contra los archivos originales — {datetime.now():%Y-%m-%d %H:%M} #####")

    # 1. PTE: la fila citada contiene la universidad y su obligación
    log("\n1. PTE (fila de Excel citada → obligación)")
    obl, citas_malas = {}, []
    for (archivo, hoja), g in pte.groupby(["archivo", "hoja"]):
        d = pd.read_excel(archivo, sheet_name=hoja, header=None, dtype=str)
        for r in g.itertuples():
            celda = str(d.iat[r.fila_excel - 1, 0]).strip()
            if not celda.startswith(r.pte_codigo):
                citas_malas.append(f"{archivo} fila {r.fila_excel}: '{celda[:60]}' (se esperaba {r.pte_codigo})")
            obl[(r.pte_codigo, r.anio)] = float(d.iat[r.fila_excel - 1, 3])
    if citas_malas:
        FALLAS.append("citas PTE")
        log("  FALLA  filas citadas que no corresponden:\n         " + "\n         ".join(citas_malas[:5]))
    else:
        log(f"  PASA   las {len(pte)} filas citadas contienen el código de su universidad")
    comparar("obligación (pesos)", pd.Series(obl), base.obligacion)

    # 2. SNIES desde el Excel original
    log("\n2. SNIES (Excel original → suma de sedes por universidad)")
    tot_snies = {}
    for tipo, var in (("matriculados", "MATRICULADOS"), ("graduados", "GRADUADOS")):
        partes = []
        for a in anios:
            f = next(Path("data/raw/snies").glob(f"snies_{tipo}_{a}_*.xlsx"))
            d = pd.read_excel(f, sheet_name="1.", header=5, dtype=str,
                              usecols=[COD, "NIVEL ACADÉMICO", "SEMESTRE", "AÑO", var])
            d = d[d["AÑO"].notna()]
            d[var] = pd.to_numeric(d[var])
            tot_snies[(tipo, a)] = d[var].sum()
            partes.append(d)
        d = pd.concat(partes)
        d = d[d[COD].isin(mapa)]
        d["u"] = d[COD].map(mapa)
        d["anio"] = d["AÑO"].astype(int)
        d["niv"] = d["NIVEL ACADÉMICO"].str.strip().str.lower()
        if tipo == "matriculados":
            for niv in ("pregrado", "posgrado"):
                for sem in ("1", "2"):
                    x = d[(d.niv == niv) & (d.SEMESTRE.astype(str) == sem)].groupby(["u", "anio"])[var].sum()
                    x = x.reindex(base.index, fill_value=0)
                    comparar(f"matriculados {niv} semestre {sem}", x, base[f"mat_{niv}_s{sem}"])
        else:
            x = d.groupby(["u", "anio"])[var].sum().reindex(base.index, fill_value=0)
            comparar("graduados total", x, base.grad_total)

    # 3. Saber Pro desde el .txt, estudiante por estudiante
    log("\n3. Saber Pro (.txt original → estudiante por estudiante)")
    partes, tot_sp = [], {}
    for a in anios:
        d = pd.read_csv(f"data/raw/saber_pro/Examen_Saber_Pro_Genericas_{a}.txt", sep=";", low_memory=False,
                        usecols=MOD + ["punt_global", "inst_cod_institucion"])
        d = d.dropna(subset=["inst_cod_institucion", "punt_global"])
        tot_sp[a] = len(d)
        d["cod"] = d.inst_cod_institucion.astype("int64").astype(str)
        d["anio"] = a
        partes.append(d)
    d = pd.concat(partes)
    d = d[d.cod.isin(mapa)]
    d["u"] = d.cod.map(mapa)
    cero = d.mod_comuni_escrita_punt.eq(0)
    d["gc"] = d.punt_global.where(~cero, d[[m for m in MOD if m != "mod_comuni_escrita_punt"]].mean(axis=1))
    d["cero"] = cero
    g = d.groupby(["u", "anio"])
    comparar("evaluados", g.size().astype(float), base.n_evaluados.dropna())
    comparar("ceros en Escrita", g.cero.sum().astype(float), base.n_ceros_escrita.dropna())
    comparar("puntaje global_c (tolerancia 0,01 por redondeo)", g.gc.mean(), base.global_c.dropna(), tol=0.01)

    # 4. Tabla maestra: totales nacionales
    log("\n4. Tabla maestra (totales nacionales contra los archivos originales)")
    tm = pd.read_csv("resultados/tabla_maestra_2023_2024.csv", dtype={"cod_institucion": str})
    for a in anios:
        x = tm[tm.anio == a]
        mat = x.mat_pregrado_s1.sum() + x.mat_pregrado_s2.sum() + x.mat_posgrado_s1.sum() + x.mat_posgrado_s2.sum()
        for nombre, orig, tabla in [(f"{a} matriculados (s1+s2)", tot_snies[("matriculados", a)], mat),
                                    (f"{a} graduados", tot_snies[("graduados", a)], x.grad_total.sum()),
                                    (f"{a} evaluados Saber Pro con código", tot_sp[a], x.n_evaluados.sum())]:
            ok = abs(orig - tabla) < 0.5
            if not ok:
                FALLAS.append(nombre)
            log(f"  {'PASA ' if ok else 'FALLA'}  {nombre}: archivo original={orig:,.0f} | tabla maestra={tabla:,.0f}")

    log(f"\nRESULTADO: {'TODO COINCIDE' if not FALLAS else 'HAY DIFERENCIAS: ' + ', '.join(FALLAS)}")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"verificacion_oe1_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")
    raise SystemExit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
