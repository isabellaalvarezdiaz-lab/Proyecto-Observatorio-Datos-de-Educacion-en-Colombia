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
Sede principal = la sede cuyo código coincide con su IES PADRE; si ninguna (UFPS Ocaña), la de mayor matrícula.
Los porcentajes de matrícula suman los dos semestres (son proporciones, no conteos de estudiantes).

Salida: resultados/caracteristicas_universidades.csv
Uso (desde la raíz del repositorio):
    python scripts/caracteristicas_universidades.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

COD, PADRE = "CÓDIGO DE LA INSTITUCIÓN", "IES PADRE"
COLS = [COD, PADRE, "DEPARTAMENTO DE DOMICILIO DE LA IES", "IES ACREDITADA", "PROGRAMA ACREDITADO", "MODALIDAD",
        "DEPARTAMENTO DE OFERTA DEL PROGRAMA", "NIVEL ACADÉMICO", "AÑO", "MATRICULADOS"]
DISTANCIA = {"A distancia", "Virtual", "Virtual-A distancia", "Virtual-Dual"}


def main():
    sedes = pd.read_csv("resultados/sedes_por_universidad.csv", dtype=str)
    mapa = dict(zip(sedes.cod_institucion, sedes.pte_codigo))
    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})

    filas = []
    for anio in sorted(base.anio.unique()):
        f = next(Path("data/raw/snies").glob(f"snies_matriculados_{anio}_*.xlsx"))
        d = pd.read_excel(f, sheet_name="1.", header=5, dtype=str, usecols=COLS)
        d = d[d["AÑO"].notna() & d[COD].isin(mapa)].copy()
        d["MATRICULADOS"] = pd.to_numeric(d.MATRICULADOS)
        d["u"] = d[COD].map(mapa)
        sp = pd.read_csv(f"data/raw/saber_pro/Examen_Saber_Pro_Genericas_{anio}.txt", sep=";", dtype=str,
                         usecols=["inst_cod_institucion", "inst_origen"]).dropna().drop_duplicates()
        origen = sp.drop_duplicates("inst_cod_institucion").set_index("inst_cod_institucion").inst_origen
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
        print(f"{anio}: {f.name} | {d[COD].nunique()} sedes | {len([x for x in filas if x['anio'] == anio])} universidades")

    c = pd.DataFrame(filas)
    b = base.set_index(["pte_codigo", "anio"])
    c = c.join(b[["pte_nombre", "mat_total_prom", "obligacion", "pct_ceros_escrita"]], on=["pte_codigo", "anio"])
    c["log_matricula"] = np.log(c.mat_total_prom)
    c["millones_por_estudiante"] = c.obligacion / c.mat_total_prom / 1e6
    c = c.drop(columns=["obligacion"]).sort_values(["anio", "pte_codigo"])
    num = c.select_dtypes("number").columns.drop("anio")
    c[num] = c[num].round(4)
    c.to_csv("resultados/caracteristicas_universidades.csv", index=False, encoding="utf-8-sig")
    x = c[c.anio == c.anio.max()]
    print(f"Acreditadas: {int(x.acreditada_institucional.sum())} de {len(x)} | domicilio en Bogotá: "
          f"{int(x.domicilio_bogota.sum())} | orden: {x.orden.value_counts(dropna=False).to_dict()}")
    print("Sin orden asignado:", x.loc[x.orden.isna(), ["pte_nombre", "origen_saber_pro"]].to_dict("records") or "ninguna")
    print("Guardado: resultados/caracteristicas_universidades.csv")


if __name__ == "__main__":
    main()
