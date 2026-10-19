"""
verificar_llave.py — Verificación de la llave de integración SNIES <-> Saber Pro
(código de institución), por año.

Reemplaza a la versión anterior, que no está en el repositorio y cuya lectura
del SNIES 2021 no coincide con el formato actual del archivo.

Qué hace, para cada año indicado:
  1. Saber Pro: toma los códigos de institución (inst_cod_institucion) y
     cuenta cuántos registros tienen código.
  2. SNIES (matriculados y graduados): detecta la hoja y la fila del
     encabezado (el formato cambia entre años) y toma CÓDIGO DE LA INSTITUCIÓN.
  3. Calcula la coincidencia en los dos sentidos:
       - % de códigos de Saber Pro que existen en el SNIES
       - % de registros de Saber Pro cuyo código existe en el SNIES
       - % de códigos del SNIES que aparecen en Saber Pro
  4. Lista los códigos de Saber Pro que no están en el SNIES, con su nombre.
  5. Resume por sector (columna SECTOR IES del SNIES) los códigos del SNIES
     que no aparecen en Saber Pro.

Solo lee. Escribe la evidencia en:
  docs/gobernanza/evidencias/verificacion_llave_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts\\verificar_llave.py
    python scripts\\verificar_llave.py --anios 2023 2024

Espera los archivos:
  data/raw/saber_pro/Examen_Saber_Pro_Genericas_AAAA.txt
  data/raw/snies/snies_matriculados_AAAA_*.xlsx
  data/raw/snies/snies_graduados_AAAA_*.xlsx

Requiere: pandas, openpyxl.
"""
import argparse
import glob
import os
import unicodedata
from datetime import datetime

import pandas as pd

LOG = []


def log(texto=""):
    print(texto)
    LOG.append(str(texto))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.split()).upper()


def a_codigo(serie):
    return pd.to_numeric(serie, errors="coerce").dropna().astype("int64")


def leer_snies(ruta):
    """Detecta hoja y encabezado; devuelve DataFrame con nombres de columna normalizados."""
    hojas = pd.ExcelFile(ruta).sheet_names
    hoja = "1." if "1." in hojas else hojas[0]
    muestra = pd.read_excel(ruta, sheet_name=hoja, header=None, nrows=25)
    fila = muestra.astype(str).apply(lambda r: r.map(norm).str.contains("CODIGO DE LA INSTITUCION").any(), axis=1)
    if not fila.any():
        raise ValueError(f"No se encontró 'CÓDIGO DE LA INSTITUCIÓN' en {os.path.basename(ruta)}")
    i = int(fila.idxmax())
    df = pd.read_excel(ruta, sheet_name=hoja, header=i)
    df.columns = [norm(c) for c in df.columns]
    return df, hoja, i


def main():
    ap = argparse.ArgumentParser(description="Verificación de la llave SNIES-Saber Pro")
    ap.add_argument("--anios", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--saber-dir", default=os.path.join("data", "raw", "saber_pro"))
    ap.add_argument("--snies-dir", default=os.path.join("data", "raw", "snies"))
    args = ap.parse_args()

    log(f"##### Verificación de la llave SNIES-Saber Pro — {datetime.now():%Y-%m-%d %H:%M} #####")

    for anio in args.anios:
        log(f"\n=== AÑO {anio} ===")
        ruta_sp = os.path.join(args.saber_dir, f"Examen_Saber_Pro_Genericas_{anio}.txt")
        if not os.path.exists(ruta_sp):
            log(f"  [ERROR] No existe {ruta_sp}")
            continue
        sp = pd.read_csv(ruta_sp, sep=";", usecols=["inst_cod_institucion", "inst_nombre_institucion"],
                         low_memory=False)
        sp_con_codigo = sp.dropna(subset=["inst_cod_institucion"]).copy()
        sp_con_codigo["codigo"] = sp_con_codigo["inst_cod_institucion"].astype("int64")
        cod_sp = set(sp_con_codigo["codigo"])
        log(f"  Saber Pro: {len(sp):,} registros; {len(sp_con_codigo):,} con código; {len(cod_sp)} códigos únicos")

        for categoria in ("matriculados", "graduados"):
            rutas = sorted(glob.glob(os.path.join(args.snies_dir, f"snies_{categoria}_{anio}_*.xlsx")))
            if not rutas:
                log(f"  [ERROR] No hay archivo SNIES de {categoria} {anio} en {args.snies_dir}")
                continue
            ruta_sn = rutas[0]
            sn, hoja, fila = leer_snies(ruta_sn)
            col_cod = next(c for c in sn.columns if "CODIGO DE LA INSTITUCION" in c)
            col_sector = next((c for c in sn.columns if c == "SECTOR IES"), None)
            cod_sn = set(a_codigo(sn[col_cod]))

            comunes = cod_sp & cod_sn
            registros_ok = sp_con_codigo["codigo"].isin(cod_sn).sum()
            log(f"\n  --- SNIES {categoria}: {os.path.basename(ruta_sn)} (hoja '{hoja}', encabezado fila {fila}) ---")
            log(f"  Códigos únicos SNIES: {len(cod_sn)} | en común con Saber Pro: {len(comunes)}")
            log(f"  % códigos de Saber Pro presentes en SNIES:    {100 * len(comunes) / len(cod_sp):.1f}%")
            log(f"  % registros de Saber Pro con código en SNIES: {100 * registros_ok / len(sp_con_codigo):.1f}%")
            log(f"  % códigos del SNIES presentes en Saber Pro:   {100 * len(comunes) / len(cod_sn):.1f}%")

            faltan = sorted(cod_sp - cod_sn)
            if faltan:
                nombres = sp_con_codigo.drop_duplicates("codigo").set_index("codigo")["inst_nombre_institucion"]
                conteo = sp_con_codigo["codigo"].value_counts()
                log(f"  Códigos de Saber Pro que NO están en SNIES {categoria} ({len(faltan)}):")
                for c in faltan:
                    log(f"      {c} | {nombres.get(c, '?')} | {conteo.get(c, 0):,} registros")

            if col_sector:
                sin_sp = sn[a_codigo(sn[col_cod]).reindex(sn.index).isin(cod_sn - cod_sp)]
                resumen = sin_sp.drop_duplicates(col_cod)[col_sector].value_counts().to_dict()
                log(f"  Códigos del SNIES sin registros en Saber Pro, por sector: {resumen}")

    carpeta = os.path.join("docs", "gobernanza", "evidencias")
    os.makedirs(carpeta, exist_ok=True)
    ev = os.path.join(carpeta, f"verificacion_llave_{datetime.now():%Y-%m-%d_%H%M}.txt")
    with open(ev, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
    print(f"\nEvidencia guardada en {ev}")


if __name__ == "__main__":
    main()
