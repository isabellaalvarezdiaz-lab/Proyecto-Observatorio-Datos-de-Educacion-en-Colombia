"""
revisar_snies.py — Verificación del contenido real de los archivos del SNIES.

Lee cada archivo Excel descargado del SNIES y reporta qué contiene según su
propio título interno, sin confiar en el nombre del archivo ni en el mapa de
identificadores del equipo anterior (snies_renamed_registros.py).

Para cada archivo imprime:
  - nombre del archivo
  - huella SHA-256 (primeros 16 caracteres), para detectar duplicados
    y confirmar que un archivo no cambió
  - nombres de las hojas del libro
  - años que aparecen en las primeras filas
  - texto de las primeras 8 filas de la primera hoja (título, fecha de
    corte, fuente)

Solo lee: no modifica, mueve ni borra ningún archivo.

Uso (desde la raíz del repositorio):
    python scripts\\revisar_snies.py
    python scripts\\revisar_snies.py --carpeta data\\raw

Por defecto revisa data/raw/snies y sus subcarpetas (incluida otros/).

Para guardar el resultado como evidencia:
    python scripts\\revisar_snies.py | Out-File -Encoding utf8 docs\\gobernanza\\evidencias\\revision_snies_contenido_AAAA-MM-DD.txt

Evidencia generada: docs/gobernanza/evidencias/revision_snies_contenido_2026-09-16.txt
(esa ejecución se hizo sobre data/raw, antes de ordenar los archivos en data/raw/snies).

Requiere: openpyxl.
"""
import argparse, glob, hashlib, os, re
from openpyxl import load_workbook

parser = argparse.ArgumentParser(description="Contenido real y huella de los archivos del SNIES")
parser.add_argument("--carpeta", default=os.path.join("data", "raw", "snies"),
                    help="Carpeta a revisar (incluye subcarpetas). Por defecto: data/raw/snies")
args = parser.parse_args()

rutas = sorted(glob.glob(os.path.join(args.carpeta, "**", "*.xlsx"), recursive=True))
if not rutas:
    print(f"No se encontraron archivos .xlsx en {args.carpeta}")

for ruta in rutas:
    nombre = os.path.relpath(ruta, args.carpeta)
    with open(ruta, "rb") as f:
        huella = hashlib.sha256(f.read()).hexdigest()
    try:
        wb = load_workbook(ruta, read_only=True)
        hojas = wb.sheetnames
        textos = []
        for fila in wb[hojas[0]].iter_rows(max_row=8, values_only=True):
            textos += [str(v).strip() for v in fila if v is not None and str(v).strip()]
        wb.close()
        resumen = " | ".join(textos)[:200]
        anios = sorted(set(re.findall(r"20[12]\d", resumen)))
        print(f"{nombre}  huella={huella[:16]}  hojas={hojas}  años={anios}\n    {resumen}\n")
    except Exception as e:
        print(f"{nombre}  huella={huella[:16]}  ERROR al abrir: {e}\n")