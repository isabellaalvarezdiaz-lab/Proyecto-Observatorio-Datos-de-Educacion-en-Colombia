"""
revision_trabajo_previo.py — Cifras para la corrección anónima de las conclusiones del trabajo previo
(informe final del semestre 2025-2, docs/informe_final.md del repositorio
https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia, commit 0e5bffe).

Ese informe concluye que "Comunicación Escrita aparece rezagada y con mayor variabilidad" (línea 183).
Este script calcula, con los microdatos de Saber Pro 2023 y 2024 y la misma población que
agregar_saber_pro.py (registros con código de institución y puntaje global):
  - media y desviación estándar de cada módulo genérico;
  - cuántos evaluados tienen 0 en Comunicación Escrita y cuántos de esos ceros tienen nivel de desempeño;
  - media y desviación de Escrita sin esos ceros, y el puesto de Escrita entre los cinco módulos.
Los años 2021 y 2022 del trabajo previo no se revisan: el proyecto no tiene esos microdatos.

Necesita data/raw/saber_pro.
Salida:    resultados/revision_trabajo_previo.csv (una fila por año, módulo y población; el % de ceros
           es 1 − n(sin ceros) / n(todos) en Comunicación escrita)
Evidencia: docs/gobernanza/evidencias/revision_trabajo_previo_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts/revision_trabajo_previo.py
"""
from datetime import datetime
from pathlib import Path

import pandas as pd

MODULOS = {"mod_ingles_punt": "Inglés", "mod_lectura_critica_punt": "Lectura crítica",
           "mod_razona_cuantitat_punt": "Razonamiento cuantitativo",
           "mod_competen_ciudada_punt": "Competencias ciudadanas", "mod_comuni_escrita_punt": "Comunicación escrita"}
ESCRITA = "mod_comuni_escrita_punt"
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def main():
    log(f"##### Revisión del trabajo previo: Comunicación Escrita — {datetime.now():%Y-%m-%d %H:%M} #####")
    filas = []
    for anio in (2023, 2024):
        d = pd.read_csv(f"data/raw/saber_pro/Examen_Saber_Pro_Genericas_{anio}.txt", sep=";", low_memory=False,
                        usecols=list(MODULOS) + ["mod_comuni_escrita_desem", "punt_global", "inst_cod_institucion"])
        d = d.dropna(subset=["inst_cod_institucion", "punt_global"])     # misma población que agregar_saber_pro.py
        cero = d[ESCRITA].eq(0)
        con_nivel = int(d.loc[cero, "mod_comuni_escrita_desem"].notna().sum())
        log(f"\n=== {anio}: {len(d):,} evaluados | 0 en Escrita: {int(cero.sum()):,} ({100 * cero.mean():.2f} %) | "
            f"de esos ceros, con nivel de desempeño: {con_nivel}")
        for c, nombre in MODULOS.items():
            filas.append(dict(anio=anio, modulo=nombre, poblacion="todos los evaluados", n=int(d[c].notna().sum()),
                              media=d[c].mean(), de=d[c].std()))
        filas.append(dict(anio=anio, modulo="Comunicación escrita", poblacion="sin los ceros en Escrita",
                          n=int((~cero).sum()), media=d.loc[~cero, ESCRITA].mean(), de=d.loc[~cero, ESCRITA].std()))
        t = pd.DataFrame([f for f in filas if f["anio"] == anio])
        for r in t.itertuples():
            log(f"  {r.modulo:27s} {r.poblacion:25s} media {r.media:7.2f}  desviación {r.de:6.2f}")
        otros = t[(t.modulo != "Comunicación escrita")]
        sin = t[t.poblacion == "sin los ceros en Escrita"].iloc[0]
        log(f"  Escrita sin ceros: puesto por media {int((otros.media > sin.media).sum()) + 1} de 5; "
            f"puesto por desviación (1 = la mayor) {int((otros.de > sin.de).sum()) + 1} de 5")
    out = pd.DataFrame(filas)
    out[["media", "de"]] = out[["media", "de"]].round(4)
    out.to_csv("resultados/revision_trabajo_previo.csv", index=False, encoding="utf-8-sig")
    log("\nGuardado: resultados/revision_trabajo_previo.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"revision_trabajo_previo_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
