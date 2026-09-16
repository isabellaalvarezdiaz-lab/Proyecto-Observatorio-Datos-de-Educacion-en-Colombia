import glob, os
import pandas as pd

for ruta in sorted(glob.glob(os.path.join("data", "raw", "snies", "snies_*.xlsx"))):
    nombre = os.path.basename(ruta)
    hojas = pd.ExcelFile(ruta).sheet_names
    hoja = "1." if "1." in hojas else hojas[0]
    d = pd.read_excel(ruta, sheet_name=hoja, header=None, nrows=25)
    fila = d.astype(str).apply(lambda r: r.str.contains("DIGO DE LA INSTITUCI", case=False).any(), axis=1)
    if not fila.any():
        print(f"{nombre} | hoja={hoja} | NO aparece 'CÓDIGO DE LA INSTITUCIÓN' en las primeras 25 filas\n")
        continue
    i = int(fila.idxmax())
    columnas = [str(c).strip() for c in d.iloc[i].dropna()]
    print(f"{nombre} | hoja={hoja} | encabezado en la fila {i} (0 = primera) | {len(columnas)} columnas")
    print("    " + " ; ".join(columnas) + "\n")