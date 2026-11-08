"""
inventario.py — Indexación de activos de información del proyecto.

Recorre el repositorio (y opcionalmente una carpeta de datos fuera de él) y
genera un CSV con: ruta, tipo, tamaño, fecha, huella SHA-256, si está
versionado en Git y alertas de gobernanza. Además reporta archivos con
contenido idéntico (misma huella). Solo lee: no modifica, mueve ni borra nada.

Uso (desde la raíz del repositorio):
    python scripts\\inventario.py --responsable Isabella
    python scripts\\inventario.py --responsable Isabella --datos "C:\\ruta\\otros_datos"

Por defecto guarda en docs/gobernanza/evidencias/inventario_AAAA-MM-DD_<responsable>.csv
Solo biblioteca estándar de Python (>= 3.8).
"""
import argparse
import csv
import hashlib
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

IGNORAR = {".git", "venv", ".venv", "__pycache__", ".ipynb_checkpoints", ".obsidian", "node_modules"}
TIPOS = {
    "dato": {".csv", ".xlsx", ".xls", ".parquet", ".txt", ".json", ".sav", ".dta", ".rds", ".rdata", ".zip", ".db", ".sqlite"},
    "codigo": {".py", ".ipynb", ".r", ".rmd", ".qmd", ".sql", ".bat", ".sh"},
    "documento": {".pdf", ".docx", ".doc", ".md", ".tex", ".bib", ".pptx", ".html"},
    "imagen": {".png", ".jpg", ".jpeg", ".svg", ".gif"},
}
PALABRAS_MICRODATO = ("saber", "icfes", "estudiante", "microdato")
LIMITE_GITHUB_MB = 100


def tipo_de(ruta: Path) -> str:
    ext = ruta.suffix.lower()
    for tipo, extensiones in TIPOS.items():
        if ext in extensiones:
            return tipo
    return "otro"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def archivos_en_git(repo: Path) -> set:
    try:
        salida = subprocess.run(["git", "ls-files", "-z"], cwd=repo,
                                capture_output=True, check=True).stdout
        return {p for p in salida.decode("utf-8").split("\0") if p}
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Aviso: no se pudo consultar Git; la columna en_git quedará como 'no'.")
        return set()


def alertas(tipo: str, en_git: bool, tamano_mb: float, nombre: str) -> str:
    avisos = []
    if tipo == "dato" and en_git:
        avisos.append("DATO EN REPO PUBLICO: revisar si puede publicarse")
        if any(p in nombre.lower() for p in PALABRAS_MICRODATO):
            avisos.append("POSIBLE MICRODATO SABER PRO EN GIT")
    if en_git and tamano_mb > LIMITE_GITHUB_MB * 0.5:
        avisos.append(f"archivo grande en Git ({tamano_mb:.1f} MB; limite GitHub {LIMITE_GITHUB_MB} MB)")
    return " | ".join(avisos)


def recorrer(raiz: Path, ubicacion: str, en_git_set: set, responsable: str, excluir: Path):
    for ruta in sorted(raiz.rglob("*")):
        if not ruta.is_file() or any(parte in IGNORAR for parte in ruta.parts):
            continue
        if ruta.resolve() == excluir:
            continue
        relativa = ruta.relative_to(raiz).as_posix()
        tipo = tipo_de(ruta)
        tamano_mb = ruta.stat().st_size / (1024 * 1024)
        en_git = relativa in en_git_set if ubicacion == "repositorio" else False
        print(f"  leyendo {relativa}")
        yield {
            "ubicacion": ubicacion,
            "ruta": relativa,
            "carpeta": relativa.split("/")[0] if "/" in relativa else "(raiz)",
            "tipo": tipo,
            "extension": ruta.suffix.lower(),
            "tamano_mb": round(tamano_mb, 3),
            "modificado": datetime.fromtimestamp(ruta.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            "sha256": sha256(ruta),
            "en_git": "si" if en_git else "no",
            "inventariado_por": responsable,
            "alertas": alertas(tipo, en_git, tamano_mb, relativa),
        }


def main():
    parser = argparse.ArgumentParser(description="Inventario de activos de información")
    parser.add_argument("--repo", default=".", help="Raíz del repositorio (por defecto: carpeta actual)")
    parser.add_argument("--datos", default=None, help="Carpeta de datos fuera del repositorio (opcional)")
    parser.add_argument("--responsable", required=True, help="Nombre de quien corre el inventario")
    parser.add_argument("--salida", default=None, help="Ruta del CSV de salida")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    fecha = datetime.now().strftime("%Y-%m-%d")
    salida = Path(args.salida) if args.salida else \
        repo / "docs" / "gobernanza" / "evidencias" / f"inventario_{fecha}_{args.responsable}.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)

    print("Recorriendo archivos (los datos grandes pueden tardar unos minutos)...")
    filas = list(recorrer(repo, "repositorio", archivos_en_git(repo), args.responsable, salida.resolve()))
    if args.datos:
        filas += list(recorrer(Path(args.datos).resolve(), "datos_externos", set(), args.responsable, salida.resolve()))

    if not filas:
        print("No se encontraron archivos. Revisa que estés en la raíz del repositorio.")
        return

    with open(salida, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"\nInventario generado: {salida}  ({len(filas)} archivos)\n")
    conteo = defaultdict(int)
    for fila in filas:
        conteo[(fila["ubicacion"], fila["tipo"])] += 1
    for (ubicacion, tipo), n in sorted(conteo.items()):
        print(f"  {ubicacion:<16} {tipo:<10} {n:>4}")

    con_alerta = [f for f in filas if f["alertas"]]
    print(f"\nArchivos con alertas: {len(con_alerta)}")
    for fila in con_alerta:
        print(f"  - {fila['ruta']}: {fila['alertas']}")

    por_huella = defaultdict(list)
    for fila in filas:
        por_huella[fila["sha256"]].append(fila["ruta"])
    duplicados = {h: rutas for h, rutas in por_huella.items() if len(rutas) > 1}
    print(f"\nGrupos de archivos con contenido idéntico (misma huella): {len(duplicados)}")
    for h, rutas in duplicados.items():
        print(f"  huella {h[:12]}...:")
        for r in rutas:
            print(f"      {r}")


if __name__ == "__main__":
    main()
