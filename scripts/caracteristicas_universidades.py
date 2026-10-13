"""
caracteristicas_universidades.py — Características de cada universidad pública del PTE, para la
segunda etapa del OE3. Todas salen de columnas de los archivos originales; ninguna se asigna a mano.

Necesita los datos crudos (data/raw/snies y data/raw/saber_pro) y los resultados del OE1.

Variables (una fila por universidad y año):
  acreditada_institucional  SNIES "IES ACREDITADA" de la sede principal (Sí/No)
  pct_mat_prog_acreditados  % de la matrícula en programas con "PROGRAMA ACREDITADO" = Si
  pct_mat_distancia_virtual % de la matrícula con MODALIDAD "A distancia", "Virtual", "Virtual-A distancia"
                            o "Virtual-Dual"
  pct_mat_posgrado          % de la matrícula en posgrado
  n_departamentos_oferta    departamentos distintos en "DEPARTAMENTO DE OFERTA DEL PROGRAMA"
  domicilio_bogota          "DEPARTAMENTO DE DOMICILIO DE LA IES" de la sede principal = Bogotá D.C.
  orden                     nacional o territorial, según "inst_origen" de Saber Pro de la sede principal
                            (OFICIAL NACIONAL → nacional; OFICIAL DEPARTAMENTAL o MUNICIPAL → territorial;
                            otro valor → vacío)
  log_matricula             logaritmo natural de la matrícula promedio (tamaño)
  millones_por_estudiante   obligación del PTE / matrícula promedio, en millones de pesos corrientes
  pct_ceros_escrita         % de evaluados con 0 en Comunicación Escrita (Saber Pro)
  Contexto socioeconómico de los evaluados en Saber Pro (misma población que agregar_saber_pro.py:
  registros con código de institución y puntaje global; todas las sedes de la universidad):
  n_evaluados_saber_pro     número de evaluados (debe coincidir con n_evaluados de la base integrada)
  pct_estrato_1_2           % en estratos 1 y 2 (fami_estratovivienda) sobre quienes reportan estrato 1 a 6;
                            "Sin Estrato" y las respuestas vacías no entran en el denominador
  pct_madre_hasta_secundaria % cuya madre llegó como máximo a secundaria completa (fami_educacionmadre), sobre
                            quienes reportan un nivel; "No sabe", "No Aplica" y vacías no entran
  No se usa el índice socioeconómico del ICFES (estu_inse_individual): su relación con el estrato y con la
  educación de la madre cambia mucho entre 2023 y 2024. El script lo calcula solo como diagnóstico y deja
  esas correlaciones en la evidencia (ver docs/diccionario_resultados_oe2_oe3.md).
Sede principal = la sede cuyo código coincide con su IES PADRE; si ninguna (UFPS Ocaña), la de mayor matrícula.
Los porcentajes de matrícula suman los dos semestres (son proporciones, no conteos de estudiantes).

Salida: resultados/caracteristicas_universidades.csv
Evidencia: docs/gobernanza/evidencias/caracteristicas_universidades_AAAA-MM-DD_HHMM.txt
Uso (desde la raíz del repositorio):
    python scripts/caracteristicas_universidades.py
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

COD, PADRE = "CÓDIGO DE LA INSTITUCIÓN", "IES PADRE"
COLS = [COD, PADRE, "DEPARTAMENTO DE DOMICILIO DE LA IES", "IES ACREDITADA", "PROGRAMA ACREDITADO", "MODALIDAD",
        "DEPARTAMENTO DE OFERTA DEL PROGRAMA", "NIVEL ACADÉMICO", "AÑO", "MATRICULADOS"]
DISTANCIA = {"A distancia", "Virtual", "Virtual-A distancia", "Virtual-Dual"}
SP_COLS = ["inst_cod_institucion", "punt_global", "inst_origen", "fami_estratovivienda", "fami_educacionmadre",
           "estu_inse_individual"]   # el INSE solo se lee para el diagnóstico; no va al CSV
ESTRATOS = {f"Estrato {k}" for k in range(1, 7)}
ESTRATO_BAJO = {"Estrato 1", "Estrato 2"}
MADRE_HASTA_SEC = {"Ninguno", "Primaria incompleta", "Primaria completa",
                   "Secundaria (Bachillerato) incompleta", "Secundaria (Bachillerato) completa"}
MADRE_SUPERIOR = {"Técnica o tecnológica incompleta", "Técnica o tecnológica completa",
                  "Educación profesional incompleta", "Educación profesional completa", "Postgrado"}
SIN_DATO = {"Sin Estrato", "No sabe", "No Aplica"}
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def socioeconomico(sp, mapa):
    """Variables socioeconómicas por universidad a partir de los microdatos de Saber Pro."""
    for col, validas in (("fami_estratovivienda", ESTRATOS), ("fami_educacionmadre", MADRE_HASTA_SEC | MADRE_SUPERIOR)):
        otras = set(sp[col].dropna().str.strip()) - validas - SIN_DATO
        if otras:   # una categoría nueva no se clasifica en silencio
            raise SystemExit(f"[ERROR] {col}: categorías no previstas {sorted(otras)}")
    s = sp[sp.inst_cod_institucion.isin(mapa)].copy()
    s["u"] = s.inst_cod_institucion.map(mapa)
    e = s.fami_estratovivienda.str.strip()
    m = s.fami_educacionmadre.str.strip()
    s["estrato_valido"], s["estrato_bajo"] = e.isin(ESTRATOS), e.isin(ESTRATO_BAJO)
    s["madre_valida"], s["madre_hasta_sec"] = m.isin(MADRE_HASTA_SEC | MADRE_SUPERIOR), m.isin(MADRE_HASTA_SEC)
    s["inse"] = pd.to_numeric(s.estu_inse_individual, errors="coerce")
    g = s.groupby("u")
    out = pd.DataFrame({
        "n_evaluados_saber_pro": g.size(),
        "pct_estrato_1_2": 100 * g.estrato_bajo.sum() / g.estrato_valido.sum(),
        "pct_madre_hasta_secundaria": 100 * g.madre_hasta_sec.sum() / g.madre_valida.sum()})
    falta = pd.DataFrame({"estrato": 100 * (1 - g.estrato_valido.sum() / g.size()),
                          "madre": 100 * (1 - g.madre_valida.sum() / g.size())})
    return out, falta, g.inse.mean().rename("inse_promedio")


def main():
    sedes = pd.read_csv("resultados/sedes_por_universidad.csv", dtype=str)
    mapa = dict(zip(sedes.cod_institucion, sedes.pte_codigo))
    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})

    filas, socio, diag = [], [], []
    for anio in sorted(base.anio.unique()):
        f = next(Path("data/raw/snies").glob(f"snies_matriculados_{anio}_*.xlsx"))
        d = pd.read_excel(f, sheet_name="1.", header=5, dtype=str, usecols=COLS)
        d = d[d["AÑO"].notna() & d[COD].isin(mapa)].copy()
        d["MATRICULADOS"] = pd.to_numeric(d.MATRICULADOS)
        d["u"] = d[COD].map(mapa)
        sp = pd.read_csv(f"data/raw/saber_pro/Examen_Saber_Pro_Genericas_{anio}.txt", sep=";", dtype=str,
                         usecols=SP_COLS)
        sp = sp.dropna(subset=["inst_cod_institucion", "punt_global"])   # misma población que agregar_saber_pro.py
        origen = sp.dropna(subset=["inst_origen"]).drop_duplicates("inst_cod_institucion") \
            .set_index("inst_cod_institucion").inst_origen
        se, falta, inse = socioeconomico(sp, mapa)
        socio.append(se.assign(anio=int(anio)))
        diag.append(se.join(inse).assign(anio=int(anio)))
        nombres = sedes.drop_duplicates("pte_codigo").set_index("pte_codigo").pte_nombre
        for c in falta:
            log(f"{anio}: % sin dato de {c}: mediana entre universidades {falta[c].median():.1f} %, "
                f"máximo {falta[c].max():.1f} % ({nombres[falta[c].idxmax()]})")
        mat_sede = d.groupby(COD).MATRICULADOS.sum()
        for u, g in d.groupby("u"):
            tot = g.MATRICULADOS.sum()
            propias = g[g[COD] == g[PADRE]][COD].unique()
            principal = propias[0] if len(propias) == 1 else mat_sede.loc[g[COD].unique()].idxmax()
            gp = g[g[COD] == principal].iloc[0]
            o = origen.get(principal, "")
            orden = "nacional" if o == "OFICIAL NACIONAL" else (
                "territorial" if o in ("OFICIAL DEPARTAMENTAL", "OFICIAL MUNICIPAL") else None)
            filas.append(dict(
                pte_codigo=u, anio=int(anio), sede_principal=principal,
                acreditada_institucional=gp["IES ACREDITADA"].strip() == "Si",
                pct_mat_prog_acreditados=100 * g.loc[g["PROGRAMA ACREDITADO"].str.strip() == "Si", "MATRICULADOS"].sum() / tot,
                pct_mat_distancia_virtual=100 * g.loc[g.MODALIDAD.str.strip().isin(DISTANCIA), "MATRICULADOS"].sum() / tot,
                pct_mat_posgrado=100 * g.loc[g["NIVEL ACADÉMICO"].str.strip().str.lower() == "posgrado", "MATRICULADOS"].sum() / tot,
                n_departamentos_oferta=g["DEPARTAMENTO DE OFERTA DEL PROGRAMA"].nunique(),
                departamento_domicilio=gp["DEPARTAMENTO DE DOMICILIO DE LA IES"],
                domicilio_bogota=gp["DEPARTAMENTO DE DOMICILIO DE LA IES"].strip().upper().startswith("BOGOT"),
                orden=orden, origen_saber_pro=o))
        log(f"{anio}: {f.name} | {d[COD].nunique()} sedes | {len([x for x in filas if x['anio'] == anio])} universidades")

    c = pd.DataFrame(filas)
    se = pd.concat(socio).rename_axis("pte_codigo").reset_index()
    c = c.merge(se, on=["pte_codigo", "anio"], how="left")
    b = base.set_index(["pte_codigo", "anio"])
    c = c.join(b[["pte_nombre", "mat_total_prom", "obligacion", "pct_ceros_escrita", "n_evaluados"]],
               on=["pte_codigo", "anio"])
    dif = c[c.n_evaluados.fillna(0) != c.n_evaluados_saber_pro.fillna(0)]
    if len(dif):
        raise SystemExit(f"[ERROR] evaluados distintos a los de la base integrada:\n{dif[['pte_nombre', 'anio', 'n_evaluados', 'n_evaluados_saber_pro']]}")
    c = c.drop(columns=["n_evaluados"])
    c["log_matricula"] = np.log(c.mat_total_prom)
    c["millones_por_estudiante"] = c.obligacion / c.mat_total_prom / 1e6
    c = c.drop(columns=["obligacion"]).sort_values(["anio", "pte_codigo"])
    num = c.select_dtypes("number").columns.drop("anio")
    c[num] = c[num].round(4)
    c.to_csv("resultados/caracteristicas_universidades.csv", index=False, encoding="utf-8-sig")
    x = c[c.anio == c.anio.max()]
    log(f"Acreditadas: {int(x.acreditada_institucional.sum())} de {len(x)} | domicilio en Bogotá: "
        f"{int(x.domicilio_bogota.sum())} | orden: {x.orden.value_counts(dropna=False).to_dict()}")
    log(f"Sin orden asignado: {x.loc[x.orden.isna(), ['pte_nombre', 'origen_saber_pro']].to_dict('records') or 'ninguna'}")
    # diagnóstico del INSE: por qué no se usa
    dg = pd.concat(diag)
    log("\nDiagnóstico del INSE del ICFES (no se usa en el análisis), Spearman entre universidades:")
    for anio, g in dg.groupby("anio"):
        log(f"  {anio}: INSE vs % estratos 1-2 {g.inse_promedio.corr(g.pct_estrato_1_2, method='spearman'):+.2f} | "
            f"INSE vs % madre hasta secundaria {g.inse_promedio.corr(g.pct_madre_hasta_secundaria, method='spearman'):+.2f}")
    w = dg.rename_axis("u").reset_index().pivot(index="u", columns="anio")
    anios = sorted(dg.anio.unique())
    if len(anios) == 2:
        log("  mismo orden de universidades en los dos años (Spearman 2023 vs 2024): " + " | ".join(
            f"{v} {w[v][anios[0]].corr(w[v][anios[1]], method='spearman'):.2f}"
            for v in ("inse_promedio", "pct_estrato_1_2", "pct_madre_hasta_secundaria")))
    log("Guardado: resultados/caracteristicas_universidades.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"caracteristicas_universidades_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
