# extrae_pte_educacion_full.py
from pathlib import Path
import pandas as pd
import re, unicodedata

# ENTRADAS en PTE/data
CARPETA = Path("data")
# SALIDAS en PTE/salidas
SALIDAS = Path("salidas"); SALIDAS.mkdir(exist_ok=True)

MESES = {
    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
    "julio":7,"agosto":8,"septiembre":9,"setiembre":9,
    "octubre":10,"noviembre":11,"diciembre":12
}

def norm(s):
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii")
    return re.sub(r"\s+"," ", s).strip().lower()

def parse_fecha(nombre):
    s = norm(nombre)
    m = re.search(r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre).*?(20\d{2})", s)
    if not m: return None, None
    return int(m.group(2)), MESES[m.group(1)]

def limpiar_num(x):
    if pd.isna(x): return None
    s = re.sub(r"[^\d,.\-]", "", str(x))
    if "," in s and "." in s: s = s.replace(".","").replace(",",".")
    elif s.count(",")>1:      s = s.replace(",","")
    else:                     s = s.replace(",",".")
    try: return float(s)
    except: return None

def extrae_fila(path: Path):
    xl = pd.ExcelFile(path, engine="openpyxl")
    for sh in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=sh, header=None, engine="openpyxl")
        # localizar fila de encabezados con "sector"
        hdr_idx = None
        for i in range(min(40, len(df))):
            fila_norm = [norm(v) for v in df.iloc[i,:].tolist()]
            if any(v == "sector" or v.startswith("sector") for v in fila_norm):
                hdr_idx = i; break
        if hdr_idx is None: 
            continue
        # tabla con encabezados normalizados
        tabla = df.iloc[hdr_idx:, :].reset_index(drop=True)
        headers = [norm(h) for h in tabla.iloc[0].tolist()]
        tabla = tabla.iloc[1:, :]
        tabla.columns = headers
        tabla = tabla.loc[:, ~tabla.columns.duplicated(keep="first")]
        # fila del sector educación
        col_sector = next((c for c in tabla.columns if "sector" in c), None)
        if not col_sector: 
            continue
        fila = tabla[tabla[col_sector].astype(str).map(norm).str.contains(r"\beducacion\b", na=False)]
        if fila.empty:
            continue
        # limpiar números y fijar sector = "Educacion"
        datos = fila.iloc[0].to_dict()
        out = {"sector": "Educacion"}
        for k, v in datos.items():
            if k == col_sector: 
                continue
            out[k] = limpiar_num(v)
        return out
    return {}

def main():
    archivos = []
    for p in CARPETA.glob("*.xls*"):
        if p.is_file() and not p.name.lower().startswith("~$"):
            archivos.append(p)
    archivos = sorted(archivos)
    print(f"Archivos encontrados en data/: {len(archivos)}")

    regs = []
    for f in archivos:
        anio, mes = parse_fecha(f.name)
        fila = extrae_fila(f)
        fila.update({"anio": anio, "mes": mes})
        regs.append(fila)

    out = pd.DataFrame(regs)

    # limpiar nombres de columnas
    out.columns = [
        re.sub(r"[^0-9a-zA-Z_]+","_",
               unicodedata.normalize("NFKD", str(c)).encode("ascii","ignore").decode("ascii").lower()
        ).strip("_")
        for c in out.columns
    ]
    cols_drop = [c for c in out.columns if c == "nan" or c.startswith("unnamed")]
    out = out.drop(columns=cols_drop, errors="ignore").dropna(axis=1, how="all")

    if not out.empty:
        out["fecha"] = pd.to_datetime(dict(year=out["anio"], month=out["mes"], day=1), errors="coerce")
        out = out.sort_values(["fecha"])

    # Diccionario 
    desc = {
        "sector": ("Texto", "-", "Nombre del sector presupuestal. En este caso siempre será 'Educacion'."),
        "apropiacion_vigente": ("Numerico", "Millones de pesos", "Valor total del presupuesto aprobado vigente asignado al sector."),
        "compromiso": ("Numerico", "Millones de pesos", "Recursos del presupuesto que ya han sido comprometidos mediante contratos u obligaciones."),
        "obligacion": ("Numerico", "Millones de pesos", "Recursos reconocidos legalmente como obligación a pagar."),
        "pago": ("Numerico", "Millones de pesos", "Recursos efectivamente pagados dentro del periodo."),
        "apropiacion_sin_comprometer": ("Numerico", "Millones de pesos", "Saldo de la apropiación vigente que aún no ha sido comprometido."),
        "porcentaje_de_ejecucion": ("Numerico", "%", "Relación entre compromisos/obligaciones/pagos respecto a la apropiación."),
        "anio": ("Entero", "Año calendario", "Año correspondiente al archivo procesado (2021–2024)."),
        "mes": ("Entero", "Número de mes (1=Enero … 12=Diciembre)", "Mes correspondiente al archivo procesado."),
        "fecha": ("Fecha", "YYYY-MM-DD", "Fecha construida con el primer día del mes de cada archivo.")
    }
    filas_dicc = []
    for c in out.columns:
        if c in desc:
            t,u,d = desc[c]
        else:
            t,u,d = ("Numerico","-", "Campo numérico extraído del cuadro original.")
        filas_dicc.append({"variable": c, "tipo": t, "unidad": u, "descripcion": d})
    diccionario = pd.DataFrame(filas_dicc)

    # Exportar a un único XLSX con dos hojas
    xlsx_path = SALIDAS / "pte_educacion_full.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="Datos")
        diccionario.to_excel(writer, index=False, sheet_name="Diccionario")

    print(f"Guardado: {xlsx_path.resolve()}")
    print(out.head(8))

if __name__ == "__main__":
    main()

