"""
encabezados_snies.py — Revisión de la estructura de columnas de los archivos
SNIES de matriculados y graduados (2021-2024).

Los archivos del SNIES no tienen el mismo formato en todos los años. Este
script detecta, para cada archivo:
  - la hoja donde están los datos: "1." si existe (2023-2024); si no,
    la primera hoja (2021-2022)
  - la fila donde está el encabezado, buscando la columna
    "CÓDIGO DE LA INSTITUCIÓN" en las primeras 25 filas
  - la cantidad y el nombre de las columnas, en su orden real

Hallazgos que motivaron el script (ver evidencia):
  - el encabezado está en la fila 10 (2021), 8 (2022) y 5 (2023-2024),
    contando desde 0
  - varias columnas cambiaron de nombre en 2023 (p. ej. METODOLOGÍA ->
    MODALIDAD, PRINCIPAL O SECCIONAL -> TIPO IES) y algunas cambiaron de
    posición (IES ACREDITADA pasó de la posición 7 a la 13)
  - Graduados 2022 tiene errores de escritura en sus encabezados
  Por eso la carga debe detectar el encabezado y unir por nombre de columna
  con una tabla de equivalencias, nunca por posición ni saltando filas fijas.

Solo lee: no modifica, mueve ni borra ningún archivo.

Uso (desde la raíz del repositorio):
    python scripts\\encabezados_snies.py

Revisa los archivos data/raw/snies/snies_*.xlsx.

Para guardar el resultado como evidencia:
    python scripts\\encabezados_snies.py | Out-File -Encoding utf8 docs\\gobernanza\\evidencias\\encabezados_snies_AAAA-MM-DD.txt

Evidencia generada: docs/gobernanza/evidencias/encabezados_snies_2026-09-16.txt

Requiere: pandas, openpyxl.
"""
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