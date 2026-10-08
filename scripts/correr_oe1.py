"""
correr_oe1.py — Construye la base integrada (OE1) de principio a fin, en orden, y guarda todo lo
que imprime como evidencia en docs/gobernanza/evidencias/oe1_base_integrada_AAAA-MM-DD_HHMM.txt

Archivos que debe tener en data/raw/ (data/ no se sube al repositorio):
  data/raw/pte/<año>/...xlsx|xlsm           informe del PTE ACUMULADO A DICIEMBRE de cada año
                                            (el script reconoce el año por el título, no por el nombre)
  data/raw/snies/snies_matriculados_AAAA_*.xlsx, data/raw/snies/snies_graduados_AAAA_*.xlsx
  data/raw/saber_pro/Examen_Saber_Pro_Genericas_AAAA.txt

Uso (desde la raíz del repositorio):
    python scripts/correr_oe1.py
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PASOS = [
    ("Saber Pro por sede y año", "agregar_saber_pro.py"),
    ("Presupuesto de las universidades públicas (PTE, Cuadro No. 7)", "extraer_pte_universidades.py"),
    ("SNIES matriculados y graduados", "cargar_snies.py"),
    ("Sedes que forman cada universidad del PTE", "cruce_sedes.py"),
    ("Tabla maestra SNIES + Saber Pro (todas las instituciones)", "construir_tabla_maestra.py"),
    ("Base integrada para el DEA (universidades del PTE)", "construir_base_integrada.py"),
]

if not Path("scripts").is_dir() or not Path("data", "raw").is_dir():
    sys.exit("Corra este script desde la raíz del repositorio (donde están las carpetas scripts/ y data/).")

env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
log = [f"##### OE1 — base integrada — {datetime.now():%Y-%m-%d %H:%M} #####"]
for i, (desc, script) in enumerate(PASOS, 1):
    cab = f"\n[{i}/{len(PASOS)}] {desc}  (scripts/{script})"
    print(cab, flush=True)
    log.append(cab)
    r = subprocess.run([sys.executable, str(Path("scripts") / script)], env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    print(r.stdout, end="", flush=True)
    log.append(r.stdout)
    if r.returncode != 0:
        log.append(f"Se detuvo en el paso {i}: scripts/{script}")
        print(f"\nSe detuvo en el paso {i}: scripts/{script}. Corrija el error antes de seguir.")
        break
else:
    log.append("\nListo.")
    print("\nListo: resultados/tabla_maestra_2023_2024.csv y resultados/base_integrada_2023_2024.csv")

carpeta = Path("docs") / "gobernanza" / "evidencias"
carpeta.mkdir(parents=True, exist_ok=True)
ev = carpeta / f"oe1_base_integrada_{datetime.now():%Y-%m-%d_%H%M}.txt"
ev.write_text("\n".join(log) + "\n", encoding="utf-8")
print(f"Evidencia: {ev.as_posix()}")
sys.exit(r.returncode)
