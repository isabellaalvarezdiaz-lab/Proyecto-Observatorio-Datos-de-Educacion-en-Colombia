
import os, re, sys, time, csv, logging, shutil
from datetime import datetime
import pandas as pd

# === Rutas ===
DATA_RAW_DIR = "data/raw"
DATA_RENAMED_DIR = "data/renamed"
LOG_DIR = "logs"
OUT_DIR = "output"
MANIFEST_PATH = os.path.join(OUT_DIR, "manifest_renamed.csv")
LOG_PATH = os.path.join(LOG_DIR, "run_renamed.log")

os.makedirs(DATA_RENAMED_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH, level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("snies_rename")

# === MAP: identificador (sin extensión) -> nombre final (sin extensión) ===
MAP = {
    "articles-411252_recurso": "Estudiantes Matriculados 2021",
    "articles-411254_recurso": "Estudiantes Matriculados en primer curso 2021",
    "articles-411251_recurso": "Estudiantes Inscritos 2021",
    "articles-411250_recurso": "Estudiantes Graduados 2021",
    "articles-411249_recurso": "Estudiantes Admitidos 2021",
    "articles-411248_recurso": "Docentes 2021",
    "articles-411247_recurso": "Administrativos 2021",

    "articles-416250_recurso": "Administrativos 2022",
    "articles-416249_recurso": "Docentes 2022",
    "articles-416248_recurso": "Estudiantes Admitidos 2022",
    "articles-416247_recurso": "Estudiantes Graduados 2022",
    "articles-416246_recurso": "Estudiantes Inscritos 2022",
    "articles-416245_recurso": "Estudiantes Matriculados en primer curso 2022",
    "articles-416244_recurso": "Estudiantes Matriculados 2022",

    "articles-425153_recurso": "Estudiantes Admitidos 2023",
    "articles-421822_recurso": "Docentes 2023",
    "articles-421541_recurso": "Estudiantes Matriculados en primer curso 2023",
    "articles-421540_recurso": "Estudiantes Admitidos 2023",
    "articles-421539_recurso": "Estudiantes Matriculados 2023",
    "articles-421538_recurso": "Estudiantes Inscritos 2023",
    "articles-421537_recurso": "Administrativos 2023",
    "articles-421535_recurso": "Estudiantes Graduados 2023",
    "articles-417493_recurso": "Metadatos bases consolidadas 2023",

    "articles-425156_recurso": "Docentes 2024",
    "articles-425155_recurso": "Estudiantes Matriculados en primer curso 2024",
    "articles-425154_recurso": "Estudiantes Admitidos 2024",
    "articles-425151_recurso": "Estudiantes Matriculados 2024",
    "articles-425148_recurso": "Estudiantes Inscritos 2024",
    "articles-425147_recurso": "Administrativos 2024",
    "articles-425146_recurso": "Estudiantes Graduados 2024",
    "articles-425145_recurso": "Metadatos bases consolidadas 2024",
}

# === Utilidades ===
def sanitize_for_windows(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]+', ' ', name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def next_available_pretty(base_no_ext: str, ext: str) -> str:
    candidate = f"{base_no_ext}.{ext}"
    if not os.path.exists(candidate):
        return candidate
    k = 2
    while True:
        cand = f"{base_no_ext} ({k}).{ext}"
        if not os.path.exists(cand):
            return cand
        k += 1

def file_token_from_name(filename: str) -> str:
    """
    'articles-425151_recurso.xlsx'     -> 'articles-425151_recurso'
    'articles-425151_recurso (1).xls'  -> 'articles-425151_recurso'
    """
    base_no_ext = os.path.splitext(filename)[0]
    return re.sub(r"\s\(\d+\)$", "", base_no_ext)

def run():
    manifest = []

    if not os.path.isdir(DATA_RAW_DIR):
        print(f"No existe {DATA_RAW_DIR}")
        sys.exit(1)

    raw_files = [f for f in os.listdir(DATA_RAW_DIR) if os.path.isfile(os.path.join(DATA_RAW_DIR, f))]
    raw_files.sort()

    seen_tokens = set()
    for fname in raw_files:
        ts = datetime.now().isoformat(timespec="seconds")
        src = os.path.join(DATA_RAW_DIR, fname)
        token = file_token_from_name(fname)  # 'articles-######_recurso'

        desired = MAP.get(token)
        if not desired:
            manifest.append({
                "timestamp": ts, "raw_file": src, "token": token,
                "renamed_path": "", "status": "skip_not_in_map"
            })
            continue

        dest_base_no_ext = os.path.join(DATA_RENAMED_DIR, sanitize_for_windows(desired))
        ext = os.path.splitext(fname)[1].lstrip(".") or "xlsx"
        dest = next_available_pretty(dest_base_no_ext, ext)

        try:
            shutil.copyfile(src, dest)
            status = "ok"
        except Exception as e:
            logger.error(f"Error copiando {src} -> {dest}: {e}")
            dest = ""
            status = "copy_error"

        manifest.append({
            "timestamp": ts, "raw_file": src, "token": token,
            "renamed_path": dest, "status": status
        })
        seen_tokens.add(token)

    # Reporte de cobertura del MAP
    missing_in_raw = sorted([k for k in MAP.keys() if k not in seen_tokens])
    if missing_in_raw:
        logger.warning(f"Tokens del MAP que no se encontraron en raw: {missing_in_raw}")

    pd.DataFrame(manifest).to_csv(MANIFEST_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Copiados OK: {sum(1 for m in manifest if m['status']=='ok')} / {len(manifest)}")
    print(f"Inventario: {MANIFEST_PATH}")
    print(f"Log:        {LOG_PATH}")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

