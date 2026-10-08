"""
extraer_pte_universidades.py — Presupuesto de las universidades públicas (entidades 2257xx)
del Cuadro No. 7 del PTE, informe acumulado a DICIEMBRE de cada año.

No confía en el nombre del archivo ni en la carpeta: abre todos los Excel de data/raw/pte
(y subcarpetas), lee el título de la hoja del Cuadro No. 7 y se queda con el que dice
"Acumulada a Diciembre de AAAA". Si una carpeta tiene un archivo de otro año, lo avisa.

Salida (agregada, se puede subir al repositorio):
  resultados/pte_universidades_2023_2024.csv  — una fila por universidad y año, con el
  archivo, la hoja y la fila de Excel de donde sale cada cifra.

Uso (desde la raíz del repositorio):
    python scripts/extraer_pte_universidades.py
    python scripts/extraer_pte_universidades.py --anios 2023 2024
"""
import argparse
import re
from pathlib import Path

import pandas as pd

TITULO_C7 = "detallado por sector, entidad"


def corte_del_archivo(ruta):
    """Devuelve (hoja del Cuadro 7, año del corte de diciembre o None, título) del archivo."""
    try:
        x = pd.ExcelFile(ruta)
    except Exception as e:  # archivo dañado o temporal de Excel
        return None, None, f"no se pudo abrir: {e}"
    for hoja in x.sheet_names:
        cab = pd.read_excel(x, sheet_name=hoja, header=None, nrows=4, dtype=str)
        titulo = " ".join(cab[0].dropna().astype(str))
        if TITULO_C7 in titulo:
            m = re.search(r"Acumulada a (\w+) (?:de )?(\d{4})", titulo)
            if m and m.group(1).lower() == "diciembre":
                return hoja, int(m.group(2)), titulo
            return hoja, None, titulo
    return None, None, "sin hoja del Cuadro No. 7"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anios", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--pte-dir", default=str(Path("data") / "raw" / "pte"))
    args = ap.parse_args()

    archivos = sorted(p for p in Path(args.pte_dir).rglob("*")
                      if p.suffix.lower() in (".xlsx", ".xlsm") and not p.name.startswith("~$"))
    print(f"Archivos Excel en {args.pte_dir}: {len(archivos)}")
    por_anio = {}
    for p in archivos:
        hoja, anio, titulo = corte_del_archivo(p)
        carpeta = p.parent.name
        aviso = ""
        if anio is not None and carpeta.isdigit() and int(carpeta) != anio:
            aviso = f"   <-- [REVISAR] está en la carpeta {carpeta} pero su corte es diciembre de {anio}"
        print(f"  {p.as_posix()}: {'diciembre de ' + str(anio) if anio else titulo[:80]}{aviso}")
        if anio is not None:
            por_anio.setdefault(anio, []).append((p, hoja))

    filas = []
    for anio in args.anios:
        cand = por_anio.get(anio, [])
        if len(cand) != 1:
            raise SystemExit(f"\n[ERROR] Para {anio} se necesita exactamente un archivo con corte "
                             f"'Acumulada a Diciembre de {anio}' y hay {len(cand)}: "
                             f"{[c[0].as_posix() for c in cand]}")
        ruta, hoja = cand[0]
        d = pd.read_excel(ruta, sheet_name=hoja, header=None, dtype=str)
        enc = d.iloc[4, :6].astype(str).tolist()
        if not ("Apropiación" in enc[1] and "Pago" in enc[4]):
            raise SystemExit(f"[ERROR] {ruta}: encabezado inesperado en la fila 5: {enc}")
        col0 = d[0].fillna("").astype(str).str.strip()
        idx = [i for i, v in enumerate(col0) if re.match(r"^2257\d{2}\s", v)]
        for k, i in enumerate(idx):
            fin = idx[k + 1] if k + 1 < len(idx) else i + 40
            bloque = d.iloc[i:fin]
            art86 = bloque[bloque[0].fillna("").astype(str).str.contains("ARTÍCULO 86")]
            cod, nombre = col0[i].split(" ", 1)
            num = lambda v: float(v) if pd.notna(v) else None
            filas.append(dict(
                anio=anio, pte_codigo=cod,
                pte_nombre=nombre.replace("universidades públicas - ", "").strip(),
                apropiacion=num(d.iat[i, 1]), compromiso=num(d.iat[i, 2]),
                obligacion=num(d.iat[i, 3]), pago=num(d.iat[i, 4]),
                art86_obligacion=num(art86.iat[0, 3]) if len(art86) else None,
                archivo=ruta.as_posix(), hoja=hoja, fila_excel=i + 1))
        print(f"\n{anio}: {ruta.as_posix()} | hoja '{hoja}' | {len(idx)} universidades")

    pte = pd.DataFrame(filas)
    cods = [set(pte[pte.anio == a].pte_codigo) for a in args.anios]
    print("Mismo conjunto de códigos en todos los años:", all(c == cods[0] for c in cods))
    w = pte.pivot(index="pte_codigo", columns="anio", values="pte_nombre")
    dif = w[w.nunique(axis=1) > 1]
    print("Códigos cuyo nombre cambia entre años:", dif.to_dict("index") if len(dif) else "ninguno")

    Path("resultados").mkdir(exist_ok=True)
    salida = Path("resultados") / f"pte_universidades_{min(args.anios)}_{max(args.anios)}.csv"
    pte.to_csv(salida, index=False, encoding="utf-8-sig")
    t = pte.pivot(index="pte_codigo", columns="anio", values="obligacion") / 1e9
    print(f"Obligación total (miles de millones): {t.sum().round(1).to_dict()}")
    print(f"Guardado: {salida.as_posix()} ({len(pte)} filas)")


if __name__ == "__main__":
    main()
