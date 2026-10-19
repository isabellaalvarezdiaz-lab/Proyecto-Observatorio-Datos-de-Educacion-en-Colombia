"""
verificar_herencia.py — Cierra los puntos PENDIENTES de 01_auditoria_herencia.md
con los datos reales. No modifica ningún archivo de datos: solo lee y reporta.

Uso (cada bloque es opcional; corran los que tengan datos):
  python verificar_herencia.py --saber-dir "C:/ruta/Datos"
  python verificar_herencia.py --pte-file "C:/ruta/02__Cuadros_informe_de_ejecución_Diciembre.xlsx"
  python verificar_herencia.py --revisar-archivo "C:/ruta/data/raw/articles-425153_recurso.xlsx"
  python verificar_herencia.py --pte-dir "C:/ruta/PTE/data"

Todo lo impreso queda también en verificacion_herencia.txt (evidencia para la bitácora).
Requiere: pandas, openpyxl.
"""
import argparse
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

SALIDA = Path("verificacion_herencia.txt")
MODULOS = ["mod_competen_ciudada_punt", "mod_comuni_escrita_punt", "mod_ingles_punt",
           "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
COLS_INTERES = ["inst_cod_institucion", "inst_nombre_institucion", "estu_snies_prgmacademico",
                "estu_inst_departamento", "estu_genero", "punt_global"] + MODULOS


def log(*args):
    texto = " ".join(str(a) for a in args)
    print(texto)
    with open(SALIDA, "a", encoding="utf-8") as f:
        f.write(texto + "\n")


def norm(s):
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip().lower()


def leer_txt(ruta, **kw):
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(ruta, sep=";", encoding=enc, low_memory=False, **kw), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {ruta}")


# ---------------------------------------------------------------- Saber Pro
def verificar_saber(carpeta: Path):
    log("\n=== SABER PRO (R02, R03, R05, R07) ===")
    tipos_codigo = {}
    for anio in (2021, 2022, 2023, 2024):
        ruta = carpeta / f"Examen_Saber_Pro_Genericas_{anio}.txt"
        if not ruta.exists():
            log(f"[{anio}] no encontrado: {ruta}")
            continue
        encabezado, enc = leer_txt(ruta, nrows=0)
        columnas = list(encabezado.columns)
        usar = [c for c in COLS_INTERES if c in columnas]
        faltan = [c for c in COLS_INTERES if c not in columnas]
        df, _ = leer_txt(ruta, usecols=usar)  # tipos inferidos por pandas, como en Database.py

        log(f"\n[{anio}] filas={len(df):,}  columnas totales={len(columnas)}  codificación={enc}")
        if faltan:
            log(f"  columnas esperadas ausentes: {faltan}")

        if "inst_cod_institucion" in df:
            col = df["inst_cod_institucion"]
            tipos_codigo[anio] = str(col.dtype)
            log(f"  R02 inst_cod_institucion: tipo inferido={col.dtype}, nulos={col.isna().sum():,}, "
                f"códigos únicos={col.nunique():,}")
        if "estu_snies_prgmacademico" in df:
            log(f"  R02 estu_snies_prgmacademico: tipo={df['estu_snies_prgmacademico'].dtype}, "
                f"nulos={df['estu_snies_prgmacademico'].isna().sum():,}")

        if {"inst_cod_institucion", "estu_inst_departamento"} <= set(df.columns):
            deptos = df.groupby("inst_cod_institucion")["estu_inst_departamento"].nunique()
            multi = deptos[deptos > 1].sort_values(ascending=False)
            log(f"  R03 instituciones con estudiantes en más de un departamento: {len(multi)} de {len(deptos)}")
            if "inst_nombre_institucion" in df:
                nombres = df.drop_duplicates("inst_cod_institucion").set_index("inst_cod_institucion")["inst_nombre_institucion"]
                for cod, n in multi.head(5).items():
                    log(f"      {cod} ({nombres.get(cod, '?')}): {n} departamentos")

        if "estu_genero" in df:
            log(f"  R05 estu_genero: {df['estu_genero'].value_counts(dropna=False).to_dict()}")

        for m in [c for c in MODULOS + ["punt_global"] if c in df]:
            ceros = (df[m] == 0).sum()
            log(f"  R07 {m}: ceros={ceros:,} ({ceros / len(df):.2%}), nulos={df[m].isna().sum():,}")

    if tipos_codigo:
        log(f"\n  R02 tipos de inst_cod_institucion por año: {tipos_codigo}")
        if len(set(tipos_codigo.values())) > 1:
            log("  -> TIPOS DISTINTOS ENTRE AÑOS: compatible con la hipótesis de cruces fallidos en modelo_estrella.py")


# ---------------------------------------------------------------- PTE
def verificar_pte_archivo(ruta: Path):
    """Replica la selección de hoja de extrae_pte_educacion_full.py (R11)."""
    log(f"\n=== PTE (R11): {ruta.name} ===")
    xl = pd.ExcelFile(ruta, engine="openpyxl")
    log(f"  hojas: {xl.sheet_names}")
    for hoja in xl.sheet_names:
        df = pd.read_excel(ruta, sheet_name=hoja, header=None, engine="openpyxl")
        for i in range(min(40, len(df))):
            fila = [norm(v) for v in df.iloc[i, :].tolist()]
            if any(v == "sector" or v.startswith("sector") for v in fila):
                log(f"  HOJA QUE TOMA EL SCRIPT HEREDADO: '{hoja}' (encabezado en fila {i})")
                titulo = " | ".join(str(v) for v in df.iloc[:i, 0].dropna().tolist())[:300]
                log(f"  texto sobre el encabezado (título/unidades): {titulo}")
                tabla = df.iloc[i + 1:, :]
                col_sector = next(j for j, v in enumerate(fila) if "sector" in v)
                mask = tabla.iloc[:, col_sector].astype(str).map(norm).str.contains(r"\beducacion\b", na=False)
                if mask.any():
                    valores = tabla[mask].iloc[0].tolist()
                    log(f"  encabezados: {df.iloc[i, :].tolist()}")
                    log(f"  fila Educación (valor | tipo de celda):")
                    for v in valores:
                        log(f"      {v!r} | {type(v).__name__}")
                return
    log("  ninguna hoja tiene encabezado 'sector': el script heredado devolvería una fila vacía")


def contar_pte(carpeta: Path):
    log(f"\n=== PTE (R11b): archivos en {carpeta} ===")
    archivos = sorted(p for p in carpeta.glob("*.xls*") if not p.name.startswith("~$"))
    log(f"  total archivos Excel: {len(archivos)}")
    for p in archivos:
        log(f"      {p.name}")


# ---------------------------------------------------------------- SNIES
def revisar_archivo(ruta: Path):
    """Muestra hojas y primeras filas para confirmar el contenido real (R09)."""
    log(f"\n=== REVISIÓN DE ARCHIVO (R09): {ruta.name} ===")
    xl = pd.ExcelFile(ruta)
    for hoja in xl.sheet_names:
        df = pd.read_excel(ruta, sheet_name=hoja, header=None, nrows=8)
        log(f"  hoja '{hoja}':")
        for _, fila in df.iterrows():
            log("      " + " | ".join(str(v) for v in fila.dropna().tolist())[:250])
        anios = sorted(set(re.findall(r"20\d{2}", df.to_string())))
        log(f"  años mencionados en las primeras filas: {anios}")


def main():
    ap = argparse.ArgumentParser(description="Verificación de pendientes del material heredado")
    ap.add_argument("--saber-dir", type=Path)
    ap.add_argument("--pte-file", type=Path)
    ap.add_argument("--pte-dir", type=Path)
    ap.add_argument("--revisar-archivo", type=Path)
    args = ap.parse_args()

    log(f"\n##### Ejecución {datetime.now():%Y-%m-%d %H:%M} #####")
    if args.saber_dir:
        verificar_saber(args.saber_dir)
    if args.pte_file:
        verificar_pte_archivo(args.pte_file)
    if args.pte_dir:
        contar_pte(args.pte_dir)
    if args.revisar_archivo:
        revisar_archivo(args.revisar_archivo)
    if not any(vars(args).values()):
        ap.print_help()
    log(f"\nResultado guardado en {SALIDA.resolve()}")


if __name__ == "__main__":
    main()
