"""
cargar_snies.py — Lee SNIES matriculados y graduados (hoja '1.', encabezado en la fila 6 del
Excel) y guarda una copia liviana en data/interim/ para no releer los Excel en cada paso.

Busca en data/raw/snies:
  snies_matriculados_AAAA_*.xlsx   y   snies_graduados_AAAA_*.xlsx

Salida (no se sube al repositorio, data/ está en .gitignore):
  data/interim/snies_matriculados.csv.gz, data/interim/snies_graduados.csv.gz

Uso (desde la raíz del repositorio):
    python scripts/cargar_snies.py
"""
import argparse
from pathlib import Path

import pandas as pd

COLS = ["CÓDIGO DE LA INSTITUCIÓN", "IES PADRE", "INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)", "TIPO IES",
        "SECTOR IES", "CARÁCTER IES", "CÓDIGO SNIES DEL PROGRAMA", "NIVEL ACADÉMICO", "NIVEL DE FORMACIÓN",
        "MODALIDAD", "AÑO", "SEMESTRE"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anios", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--snies-dir", default=str(Path("data") / "raw" / "snies"))
    args = ap.parse_args()
    Path("data/interim").mkdir(parents=True, exist_ok=True)

    for tipo, var in (("matriculados", "MATRICULADOS"), ("graduados", "GRADUADOS")):
        partes = []
        for anio in args.anios:
            cand = sorted(Path(args.snies_dir).glob(f"snies_{tipo}_{anio}_*.xlsx"))
            if len(cand) != 1:
                raise SystemExit(f"[ERROR] Se esperaba un archivo snies_{tipo}_{anio}_*.xlsx en "
                                 f"{args.snies_dir} y hay {len(cand)}: {[c.name for c in cand]}")
            f = cand[0]
            d = pd.read_excel(f, sheet_name="1.", header=5, dtype=str, usecols=COLS + [var])
            pie = d[d["AÑO"].isna()]["CÓDIGO DE LA INSTITUCIÓN"].dropna().astype(str).tolist()
            d = d[d["AÑO"].notna()].copy()
            d[var] = pd.to_numeric(d[var], errors="coerce")
            if set(d["AÑO"].astype(str).unique()) != {str(anio)}:
                raise SystemExit(f"[ERROR] {f.name}: la columna AÑO no es {anio}: {d['AÑO'].unique()}")
            print(f"{f.as_posix()}: {len(d):,} filas | {d[var].sum():,.0f} {var.lower()} | semestres "
                  f"{sorted(d.SEMESTRE.astype(str).unique())} | {d['CÓDIGO DE LA INSTITUCIÓN'].nunique()} "
                  f"códigos de institución")
            print("   pie de página:", " | ".join(p.strip() for p in pie))
            partes.append(d)
        salida = Path("data") / "interim" / f"snies_{tipo}.csv.gz"
        pd.concat(partes).to_csv(salida, index=False)
        print(f"Guardado: {salida.as_posix()}")


if __name__ == "__main__":
    main()
