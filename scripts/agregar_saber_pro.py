"""
agregar_saber_pro.py — Tabla de Saber Pro por institución y año (2023-2024),
que es el producto "puntaje" del DEA.

Decisiones que aplica, todas verificadas con los microdatos:
  - Excluye los registros sin código de institución (no tienen código ni
    nombre ni programa, así que no se pueden asignar a ninguna universidad).
  - Trata el cero de Comunicación Escrita como "sin calificación", porque
    ningún cero tiene nivel de desempeño. Calcula tres versiones del puntaje
    para poder comparar:
      global_a = punt_global tal cual (cero incluido)
      global_b = punt_global excluyendo a los estudiantes con cero en Escrita
      global_c = punt_global, reemplazado por el promedio de los otros 4
                 módulos en los estudiantes con cero en Escrita  (recomendada)
  - No filtra por nivel de formación: solo reporta cuántos registros hay de
    cada nivel, para que el equipo decida después.

Salida (agregada, sin datos de estudiantes; se puede subir al repositorio):
  resultados/saber_pro_institucion_anio.csv

Evidencia: docs/gobernanza/evidencias/agregacion_saber_pro_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts\\agregar_saber_pro.py
    python scripts\\agregar_saber_pro.py --anios 2023 2024

Requiere: pandas.
"""
import argparse
import os
from datetime import datetime

import pandas as pd

MODULOS = ["mod_competen_ciudada_punt", "mod_comuni_escrita_punt", "mod_ingles_punt",
           "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
OTROS_4 = [m for m in MODULOS if m != "mod_comuni_escrita_punt"]
LOG = []


def log(texto=""):
    print(texto)
    LOG.append(str(texto))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anios", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--saber-dir", default=os.path.join("data", "raw", "saber_pro"))
    args = ap.parse_args()

    log(f"##### Agregación de Saber Pro por institución y año — {datetime.now():%Y-%m-%d %H:%M} #####")
    tablas = []
    for anio in args.anios:
        ruta = os.path.join(args.saber_dir, f"Examen_Saber_Pro_Genericas_{anio}.txt")
        d = pd.read_csv(ruta, sep=";", low_memory=False,
                        usecols=MODULOS + ["punt_global", "inst_cod_institucion",
                                           "inst_nombre_institucion", "estu_nivel_prgm_academico"])
        total = len(d)
        d = d.dropna(subset=["inst_cod_institucion", "punt_global"])
        d["codigo_ies"] = d["inst_cod_institucion"].astype("int64")
        cero = d["mod_comuni_escrita_punt"].eq(0)

        log(f"\n=== AÑO {anio} ===")
        log(f"  registros={total:,} | con código y puntaje global={len(d):,} | "
            f"ceros en Escrita={cero.sum():,} ({100 * cero.mean():.2f}%)")
        log(f"  niveles de formación presentes: {d['estu_nivel_prgm_academico'].value_counts(dropna=False).to_dict()}")

        d["global_c"] = d["punt_global"].where(~cero, d[OTROS_4].mean(axis=1))
        g = d.groupby("codigo_ies").agg(
            nombre_ies=("inst_nombre_institucion", "first"),
            n_evaluados=("punt_global", "size"),
            n_ceros_escrita=("mod_comuni_escrita_punt", lambda s: int(s.eq(0).sum())),
            global_a=("punt_global", "mean"),
            global_c=("global_c", "mean"),
        )
        sin_cero = d[~cero].groupby("codigo_ies")["punt_global"].mean().rename("global_b")
        g = g.join(sin_cero)
        g["pct_ceros_escrita"] = (100 * g["n_ceros_escrita"] / g["n_evaluados"]).round(2)
        for c in ("global_a", "global_b", "global_c"):
            g[c] = g[c].round(2)
        g.insert(0, "anio", anio)
        tablas.append(g.reset_index())
        log(f"  instituciones con evaluados: {len(g)}")
        log(f"  puntaje promedio (ponderado por evaluados): a={d['punt_global'].mean():.2f} | "
            f"c={d['global_c'].mean():.2f}")

    tabla = pd.concat(tablas, ignore_index=True)
    os.makedirs("resultados", exist_ok=True)
    salida = os.path.join("resultados", "saber_pro_institucion_anio.csv")
    tabla.to_csv(salida, index=False, encoding="utf-8-sig")
    log(f"\nTabla guardada en {salida} ({len(tabla)} filas)")

    if len(args.anios) > 1:
        por_anio = tabla.groupby("anio")["codigo_ies"].apply(set)
        comunes = set.intersection(*por_anio)
        log(f"  instituciones presentes en todos los años: {len(comunes)}")
        for anio, cods in por_anio.items():
            faltan = sorted(cods - comunes)
            if faltan:
                log(f"  [REVISAR] {anio}: códigos que no están en todos los años: {faltan}")

    carpeta = os.path.join("docs", "gobernanza", "evidencias")
    os.makedirs(carpeta, exist_ok=True)
    ev = os.path.join(carpeta, f"agregacion_saber_pro_{datetime.now():%Y-%m-%d_%H%M}.txt")
    with open(ev, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
    print(f"\nEvidencia guardada en {ev}")


if __name__ == "__main__":
    main()
