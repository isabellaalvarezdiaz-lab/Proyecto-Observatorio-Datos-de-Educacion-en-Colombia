"""
construir_tabla_maestra.py — OE1. Tabla maestra SNIES + Saber Pro de TODAS las instituciones de
educación superior (públicas y privadas), una fila por código de institución y año.

Llave: CÓDIGO DE LA INSTITUCIÓN (SNIES) = inst_cod_institucion (Saber Pro).
El PTE NO entra aquí (solo cubre las universidades públicas); se une después, en
construir_base_integrada.py, que parte de esta tabla.

Entradas: data/interim/snies_*.csv.gz          <- cargar_snies.py
          resultados/saber_pro_institucion_anio.csv <- agregar_saber_pro.py
          resultados/sedes_por_universidad.csv       <- cruce_sedes.py (solo para marcar las 34 del PTE)
Salida:   resultados/tabla_maestra_2023_2024.csv  (ver docs/diccionario_tabla_maestra.md)

Reglas:
  - Matrícula: por semestre; NO se suman los dos semestres. Se guardan s1, s2 y su promedio.
  - Graduados: se suman los dos semestres.
  - Unión externa: quedan las instituciones que están en una sola fuente, marcadas con
    en_snies / en_saber_pro, para que la cobertura de la llave quede a la vista.

Uso (desde la raíz del repositorio):
    python scripts/construir_tabla_maestra.py
"""
from pathlib import Path

import pandas as pd

COD = "CÓDIGO DE LA INSTITUCIÓN"
ATRIB = {"IES PADRE": "ies_padre", "INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)": "nombre_snies",
         "TIPO IES": "tipo_ies", "SECTOR IES": "sector", "CARÁCTER IES": "caracter"}


def snies():
    m = pd.read_csv("data/interim/snies_matriculados.csv.gz", dtype=str)
    g = pd.read_csv("data/interim/snies_graduados.csv.gz", dtype=str)
    m["MATRICULADOS"] = pd.to_numeric(m.MATRICULADOS)
    g["GRADUADOS"] = pd.to_numeric(g.GRADUADOS)
    for d in (m, g):
        d["anio"] = d["AÑO"].astype(int)
        d["nivel"] = d["NIVEL ACADÉMICO"].str.strip().str.lower()
        if not set(d.nivel) <= {"pregrado", "posgrado"}:
            raise SystemExit(f"[ERROR] Niveles académicos inesperados: {set(d.nivel)}")

    tm = m.pivot_table(index=[COD, "anio"], columns=["nivel", "SEMESTRE"], values="MATRICULADOS",
                       aggfunc="sum", fill_value=0)
    out = pd.DataFrame(index=tm.index)
    for niv in ("pregrado", "posgrado"):
        s1 = tm[(niv, "1")] if (niv, "1") in tm.columns else 0
        s2 = tm[(niv, "2")] if (niv, "2") in tm.columns else 0
        out[f"mat_{niv}_s1"], out[f"mat_{niv}_s2"] = s1, s2
        out[f"mat_{niv}_prom"] = (s1 + s2) / 2
    out["mat_total_prom"] = out.mat_pregrado_prom + out.mat_posgrado_prom

    tg = g.pivot_table(index=[COD, "anio"], columns="nivel", values="GRADUADOS", aggfunc="sum", fill_value=0)
    gr = pd.DataFrame(index=tg.index)
    for niv in ("pregrado", "posgrado"):
        gr[f"grad_{niv}"] = tg[niv] if niv in tg.columns else 0
    gr["grad_total"] = gr.grad_pregrado + gr.grad_posgrado

    # atributos de la institución: los del archivo de matriculados; si no está, los de graduados
    at = (pd.concat([m, g]).drop_duplicates([COD, "anio"])
          .set_index([COD, "anio"])[list(ATRIB)].rename(columns=ATRIB))
    s = at.join(out, how="outer").join(gr, how="outer")
    s.index.names = ["cod_institucion", "anio"]
    for c in [c for c in s.columns if c.startswith(("mat_", "grad_"))]:
        s[c] = s[c].fillna(0)        # institución en un solo archivo de SNIES: 0 en el otro
        if not c.endswith("_prom"):
            s[c] = s[c].astype("int64")
    return s


def saber_pro():
    sp = pd.read_csv("resultados/saber_pro_institucion_anio.csv", dtype={"codigo_ies": str})
    sp = sp.rename(columns={"codigo_ies": "cod_institucion", "nombre_ies": "nombre_saber_pro"})
    cols = ["nombre_saber_pro", "n_evaluados", "n_ceros_escrita", "pct_ceros_escrita",
            "global_a", "global_b", "global_c"]
    return sp.set_index(["cod_institucion", "anio"])[cols]


def main():
    sn, sp = snies(), saber_pro()
    t = sn.join(sp, how="outer")
    enteros = [c for c in t.columns if c.startswith(("mat_", "grad_")) and not c.endswith("_prom")]
    for c in enteros + ["n_evaluados", "n_ceros_escrita"]:
        t[c] = t[c].astype("Int64")   # entero que admite vacío (institución ausente de una fuente)
    t["en_snies"] = t.index.isin(sn.index)
    t["en_saber_pro"] = t.index.isin(sp.index)
    sedes = pd.read_csv("resultados/sedes_por_universidad.csv", dtype=str)
    t = t.reset_index()
    t["pte_codigo"] = t.cod_institucion.map(dict(zip(sedes.cod_institucion, sedes.pte_codigo)))
    t["nombre"] = t.nombre_snies.fillna(t.nombre_saber_pro)
    orden = ["cod_institucion", "anio", "nombre", "ies_padre", "tipo_ies", "sector", "caracter",
             "pte_codigo", "en_snies", "en_saber_pro"]
    t = t[orden + [c for c in t.columns if c not in orden + ["nombre_snies"]]]
    t = t.sort_values(["anio", "cod_institucion"], key=lambda c: c.astype(int) if c.name == "cod_institucion" else c)

    salida = Path("resultados") / "tabla_maestra_2023_2024.csv"
    t.to_csv(salida, index=False, encoding="utf-8-sig")

    # ---------- controles: cobertura de la llave ----------
    print(f"Filas: {len(t):,} | códigos de institución distintos: {t.cod_institucion.nunique()}")
    for a, x in t.groupby("anio"):
        ns, nb = int(x.en_saber_pro.sum()), int((x.en_saber_pro & x.en_snies).sum())
        eval_tot = x.n_evaluados.sum()
        eval_cruz = x.loc[x.en_snies, "n_evaluados"].sum()
        print(f"  {a}: {int(x.en_snies.sum())} en SNIES | {ns} en Saber Pro | {nb} en ambas → "
              f"{100 * nb / ns:.1f} % de los códigos de Saber Pro y {100 * eval_cruz / eval_tot:.2f} % "
              f"de sus evaluados tienen par en SNIES")
        solo = x[x.en_saber_pro & ~x.en_snies]
        if len(solo):
            print("     solo en Saber Pro:",
                  "; ".join(f"{r.cod_institucion} {r.nombre} ({int(r.n_evaluados)})" for r in solo.itertuples()))
    sec = t.assign(sector=t.sector.fillna("sin dato (solo en Saber Pro)")).groupby(["anio", "sector"]).size()
    print("Filas por sector (SNIES):", {a: sec[a].to_dict() for a in sec.index.levels[0]})
    print(f"Filas que pertenecen a las universidades del PTE: {t.pte_codigo.notna().sum()}")
    print(f"Guardado: {salida.as_posix()}")


if __name__ == "__main__":
    main()
