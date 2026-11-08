"""
diagnostico_ceros_escrita.py — Diagnóstico de los puntajes cero en
Comunicación Escrita (Saber Pro) y de su efecto en el puntaje global.

Contexto (verificado con los microdatos 2023-2024): todos los registros con
mod_comuni_escrita_punt = 0 tienen el nivel de desempeño VACÍO; ningún cero
tiene nivel 1 a 4. Este script responde tres preguntas más:

  1. ¿El puntaje global es el promedio de los cinco módulos? Si lo es, un cero
     en Escrita baja el puntaje global del estudiante.
  2. ¿Cuánto cambia el puntaje global promedio si se excluyen esos registros
     o si se recalcula con los otros cuatro módulos?
  3. ¿Los ceros se concentran en algunas instituciones? Si es así, afectan la
     comparación entre universidades en el DEA.

Solo lee. Evidencia en docs/gobernanza/evidencias/diagnostico_ceros_escrita_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts\\diagnostico_ceros_escrita.py
    python scripts\\diagnostico_ceros_escrita.py --anios 2023 2024

Requiere: pandas.
"""
import argparse
import os
from datetime import datetime

import pandas as pd

MODULOS = ["mod_competen_ciudada_punt", "mod_comuni_escrita_punt", "mod_ingles_punt",
           "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
LOG = []


def log(texto=""):
    print(texto)
    LOG.append(str(texto))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anios", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--saber-dir", default=os.path.join("data", "raw", "saber_pro"))
    ap.add_argument("--min-registros", type=int, default=100)
    args = ap.parse_args()

    log(f"##### Diagnóstico de ceros en Comunicación Escrita — {datetime.now():%Y-%m-%d %H:%M} #####")
    for anio in args.anios:
        ruta = os.path.join(args.saber_dir, f"Examen_Saber_Pro_Genericas_{anio}.txt")
        d = pd.read_csv(ruta, sep=";", low_memory=False,
                        usecols=MODULOS + ["punt_global", "inst_cod_institucion", "inst_nombre_institucion"])
        cero = d["mod_comuni_escrita_punt"].eq(0)
        log(f"\n=== AÑO {anio} === registros={len(d):,}  ceros en Escrita={cero.sum():,} ({100 * cero.mean():.2f}%)")

        # 1. ¿punt_global = promedio de los 5 módulos?
        c = d.dropna(subset=MODULOS + ["punt_global"])
        prom5 = c[MODULOS].mean(axis=1)
        dif = (prom5 - c["punt_global"]).abs()
        log("  1. Puntaje global frente al promedio de los 5 módulos (registros completos):")
        log(f"     diferencia absoluta media={dif.mean():.3f} | máxima={dif.max():.3f} | "
            f"% con diferencia <= 0.5: {100 * (dif <= 0.5).mean():.2f}%")
        c0 = c[c["mod_comuni_escrita_punt"].eq(0)]
        if len(c0):
            dif0 = (c0[MODULOS].mean(axis=1) - c0["punt_global"]).abs()
            log(f"     solo registros con cero en Escrita: % con diferencia <= 0.5: {100 * (dif0 <= 0.5).mean():.2f}%")

        # 2. Efecto en el promedio del puntaje global
        prom4 = c[[m for m in MODULOS if m != "mod_comuni_escrita_punt"]].mean(axis=1)
        global_ajustado = c["punt_global"].where(~c["mod_comuni_escrita_punt"].eq(0), prom4)
        log("  2. Puntaje global promedio según tratamiento del cero:")
        log(f"     a) tal cual (cero incluido):                      {c['punt_global'].mean():.2f}")
        log(f"     b) excluyendo registros con cero en Escrita:      {c.loc[~c['mod_comuni_escrita_punt'].eq(0), 'punt_global'].mean():.2f}")
        log(f"     c) promedio de 4 módulos para los registros cero: {global_ajustado.mean():.2f}")

        # 3. Concentración por institución
        g = (d.dropna(subset=["inst_cod_institucion"])
               .assign(cero=lambda x: x["mod_comuni_escrita_punt"].eq(0))
               .groupby("inst_cod_institucion")
               .agg(nombre=("inst_nombre_institucion", "first"), registros=("cero", "size"), pct_ceros=("cero", "mean")))
        g = g[g["registros"] >= args.min_registros]
        g["pct_ceros"] = (100 * g["pct_ceros"]).round(1)
        q = g["pct_ceros"].quantile([0.1, 0.5, 0.9]).round(1).to_dict()
        log(f"  3. % de ceros por institución (instituciones con >= {args.min_registros} registros: {len(g)}):")
        log(f"     percentil 10={q[0.1]}% | mediana={q[0.5]}% | percentil 90={q[0.9]}% | máximo={g['pct_ceros'].max()}%")
        log("     10 instituciones con mayor % de ceros:")
        for cod, fila in g.sort_values("pct_ceros", ascending=False).head(10).iterrows():
            log(f"       {int(cod)} | {fila['nombre']} | {fila['registros']:,} registros | {fila['pct_ceros']}%")

    carpeta = os.path.join("docs", "gobernanza", "evidencias")
    os.makedirs(carpeta, exist_ok=True)
    ev = os.path.join(carpeta, f"diagnostico_ceros_escrita_{datetime.now():%Y-%m-%d_%H%M}.txt")
    with open(ev, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
    print(f"\nEvidencia guardada en {ev}")


if __name__ == "__main__":
    main()
