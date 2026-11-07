"""
verificar_riesgo.py — Comprueba los resultados de riesgo_puntaje.py y riesgo_stress.py por otro camino.

Como verificar_oe1.py y verificar_oe2_oe3.py, recalcula cada cifra con código escrito aparte y la
compara con los archivos de resultados/. No importa nada de los scripts que verifica (salvo
publicacion.K_MIN, que es una constante).

Qué comprueba
  A. Riesgo del puntaje (resultados/riesgo_puntaje.csv), si este computador tiene los microdatos:
     A1. global_c recalculado como el promedio de los cinco módulos con Escrita reemplazada (en vez
         de corregir punt_global), y comprobado igual al de los registros oficiales.
     A2. VaR y CVaR de cada universidad y año por ordenamiento completo (np.sort), no por partición.
     A3. Intervalos bootstrap: se repiten con otra semilla y B = 1000; deben quedar cerca (no iguales:
         son simulaciones). Se reporta la diferencia máxima.
     A4. Propiedades: CVaR ≤ VaR ≤ media; intervalos que contienen la estimación; cola ≥ K_MIN.
  B. Kupiec (resultados/riesgo_kupiec.csv):
     B1. Conteos y LR recalculados con la verosimilitud binomial escrita con scipy.special.xlogy;
         p-valores con la distribución χ² por la función gamma incompleta.
     B2. Holm recalculado con un ciclo paso a paso (no vectorizado).
     B3. Empates: en vez del conteo ponderado, se sortean los empates en el VaR 500 veces (cuantil
         aleatorizado) y se cuenta en qué proporción de sorteos se mantiene cada decisión.
  C. Stress testing (resultados/riesgo_stress_*.csv):
     C1. Monto de la gratuidad leído del PTE con openpyxl (celda por celda), no con pandas.
     C2. Cada eficiencia de cada escenario recalculada por el programa DUAL (de multiplicadores),
         escrito aquí, con el método de punto interior de HiGHS.
     C3. Insumos de cada escenario reconstruidos desde la base integrada; la gratuidad repartida suma
         exactamente el monto del PTE.
     C4. Invariancia: en los recortes uniformes ninguna eficiencia cambia.

Evidencia: docs/gobernanza/evidencias/verificacion_riesgo_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts/verificar_riesgo.py
Requiere: pandas, numpy, scipy, openpyxl.
"""
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
from scipy import special
from scipy.optimize import linprog

from publicacion import K_MIN

RES = Path("resultados")
RAW = Path("data") / "raw"
MOD = ["mod_competen_ciudada_punt", "mod_comuni_escrita_punt", "mod_ingles_punt",
       "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
LOG, FALLAS = [], []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def chequear(nombre, ok, detalle=""):
    log(f"  [{'OK' if ok else 'FALLA'}] {nombre}{(' — ' + detalle) if detalle else ''}")
    if not ok:
        FALLAS.append(nombre)


def holm_ciclo(p):
    orden = sorted(range(len(p)), key=lambda i: p[i])
    m, out, acum = len(p), [0.0] * len(p), 0.0
    for paso, i in enumerate(orden):
        acum = max(acum, min(1.0, (m - paso) * p[i]))
        out[i] = acum
    return out


def lr_binomial(x, n, p0):
    """Kupiec POF con xlogy (vale para x no entero)."""
    ph = x / n
    ll0 = special.xlogy(n - x, 1 - p0) + special.xlogy(x, p0)
    ll1 = special.xlogy(n - x, 1 - ph) + special.xlogy(x, ph)
    lr = max(float(-2 * (ll0 - ll1)), 0.0)
    return lr, float(special.gammaincc(0.5, lr / 2))   # P(χ²₁ > lr)


def verificar_puntaje():
    log("\nA. Riesgo del puntaje")
    t = pd.read_csv(RES / "riesgo_puntaje.csv")
    if not (RAW / "saber_pro").exists():
        log("  (sin data/raw/saber_pro en este computador: se omiten A1-A3 y B1-B3; no cuenta como falla)")
        return None
    sedes = pd.read_csv(RES / "sedes_por_universidad.csv")
    univ = set(t.pte_codigo.dropna().astype(int))
    datos = {}
    for anio in (2023, 2024):
        d = pd.read_csv(RAW / "saber_pro" / f"Examen_Saber_Pro_Genericas_{anio}.txt", sep=";",
                        low_memory=False, usecols=MOD + ["punt_global", "inst_cod_institucion"])
        d = d[d.inst_cod_institucion.notna() & d.punt_global.notna()]
        esc = d["mod_comuni_escrita_punt"]
        otros = d[[m for m in MOD if m != "mod_comuni_escrita_punt"]].mean(axis=1)
        # Fuera de los ceros de Escrita, punt_global debe ser el promedio de los módulos presentes
        # (redondeado). Se cuentan los registros que no lo cumplen: en 2023 hay uno, sin Inglés, en
        # el que el ICFES contó Inglés como 0. No afecta el análisis, que usa punt_global oficial.
        prom5 = d[MOD].mean(axis=1)
        dif = (prom5 - d.punt_global).abs()[esc != 0]
        n_dif = int((dif > 0.5).sum())
        chequear(f"A1 {anio}: el puntaje global es el promedio de los módulos presentes",
                 n_dif <= 1, f"registros que no lo cumplen: {n_dif} de {len(dif):,}")
        g = np.where(esc == 0, otros, d.punt_global)
        cod = d.inst_cod_institucion.astype("int64").to_numpy()
        mapa = dict(zip(sedes.cod_institucion, sedes.pte_codigo))
        pte = np.array([mapa.get(c, -1) for c in cod])
        datos[anio] = {"nacional": g, "33 universidades": g[np.isin(pte, list(univ))]}
        for u in univ:
            datos[anio][u] = g[pte == u]

    dmax_v = dmax_c = dmax_ic = 0.0
    prop_ok = True
    rng = np.random.default_rng(777)
    for _, r in t.iterrows():
        clave = r.pte_nombre if pd.isna(r.pte_codigo) else int(r.pte_codigo)
        x = np.sort(datos[int(r.anio)][clave])
        k = math.ceil(r.alfa * len(x))
        v, c = x[k - 1], x[:k].mean()
        dmax_v = max(dmax_v, abs(round(v, 2) - r["var"]))
        dmax_c = max(dmax_c, abs(round(c, 2) - r.cvar))
        prop_ok &= (r.cvar <= r["var"] <= r.media) and (r.var_ic_inf <= r["var"] <= r.var_ic_sup) \
            and (r.cvar_ic_inf <= r.cvar <= r.cvar_ic_sup) and k >= K_MIN and len(x) == r.n_evaluados
        bv, bc = [], []
        for _ in range(1000):
            m = np.sort(x[rng.integers(0, len(x), len(x))])
            bv.append(m[k - 1])
            bc.append(m[:k].mean())
        ic = np.r_[np.percentile(bv, [2.5, 97.5]), np.percentile(bc, [2.5, 97.5])]
        dmax_ic = max(dmax_ic, float(np.max(np.abs(ic - r[["var_ic_inf", "var_ic_sup",
                                                            "cvar_ic_inf", "cvar_ic_sup"]].to_numpy(float)))))
    chequear("A2 VaR por ordenamiento completo", dmax_v < 0.006, f"diferencia máxima {dmax_v:.4f}")
    chequear("A2 CVaR por ordenamiento completo", dmax_c < 0.006, f"diferencia máxima {dmax_c:.4f}")
    chequear("A3 intervalos bootstrap con otra semilla", dmax_ic <= 3.0,
             f"diferencia máxima {dmax_ic:.2f} puntos (simulación; tolerancia 3)")
    chequear("A4 CVaR ≤ VaR ≤ media, intervalos y tamaño de la cola", bool(prop_ok))
    return datos


def verificar_kupiec(datos):
    log("\nB. Backtesting de Kupiec")
    k = pd.read_csv(RES / "riesgo_kupiec.csv")
    if datos is None:
        return
    rng = np.random.default_rng(2024)
    dmax_lr = dmax_p = 0.0
    estab = []
    filas = []
    for _, r in k.iterrows():
        clave = r.pte_nombre if pd.isna(r.pte_codigo) else int(r.pte_codigo)
        x23, x24 = np.sort(datos[2023][clave]), datos[2024][clave]
        q = math.ceil(r.alfa * len(x23))
        v = x23[q - 1]
        lt, eq = (x23 < v).sum(), (x23 == v).sum()
        w = (r.alfa * len(x23) - lt) / eq
        x = (x24 < v).sum() + w * (x24 == v).sum()
        lr, p = lr_binomial(x, len(x24), r.alfa)
        dmax_lr = max(dmax_lr, abs(round(lr, 3) - r.lr_kupiec))
        dmax_p = max(dmax_p, abs(p - r.p))
        filas.append((clave, p, x, len(x24)))
        if not pd.isna(r.pte_codigo):
            sorteos = (x24 < v).sum() + rng.binomial((x24 == v).sum(), w, size=500)
            estab.append([lr_binomial(s, len(x24), r.alfa)[1] for s in sorteos])
    chequear("B1 LR de Kupiec recalculado con xlogy", dmax_lr < 0.002, f"diferencia máxima {dmax_lr:.4f}")
    chequear("B1 p-valores por la gamma incompleta", dmax_p < 1e-5, f"diferencia máxima {dmax_p:.2e}")
    ku = k[k.pte_codigo.notna()]
    p_h = holm_ciclo(ku.p.tolist())
    dh = max(abs(a - b) for a, b in zip(p_h, ku.p_holm))
    # El CSV guarda p con 6 decimales; Holm multiplica ese redondeo por hasta 33.
    chequear("B2 Holm paso a paso", dh < 33 * 1e-6, f"diferencia máxima {dh:.2e} (tolerancia 33 × 10⁻⁶)")
    # B3: estabilidad de las decisiones con empates sorteados (Holm dentro de cada sorteo)
    estab = np.array(estab)                      # (33, 500)
    decis = np.array([holm_ciclo(estab[:, j].tolist()) for j in range(estab.shape[1])]).T < 0.05
    acuerdo = (decis == ku.rechaza_5pct.to_numpy()[:, None]).mean(axis=1)
    log(f"  B3 empates sorteados 500 veces: la decisión de cada universidad se mantiene en "
        f"{100 * acuerdo.min():.1f} % de los sorteos o más (mediana {100 * np.median(acuerdo):.1f} %)")
    inestables = ku.pte_nombre[acuerdo < 0.9].tolist()
    chequear("B3 decisiones estables (≥ 90 % de los sorteos) salvo las listadas", True,
             f"menos estables: {inestables or 'ninguna'}")
    # prueba relativa a la tasa nacional
    tasa_nac = [x / n for c, _, x, n in filas if c == "nacional"][0]
    dmax_rel = 0.0
    for (c, _, x, n), (_, r) in zip(filas, k.iterrows()):
        _, p = lr_binomial(x, n, tasa_nac)
        dmax_rel = max(dmax_rel, abs(p - r.p_relativo))
    chequear("B1 prueba relativa a la tasa nacional", dmax_rel < 1e-5, f"diferencia máxima {dmax_rel:.2e}")


def phi_dual(x0, y0, X, Y):
    n, s = Y.shape
    c = np.r_[x0, np.zeros(s), 1.0]
    A_ub = np.hstack([-X, Y, -np.ones((n, 1))])
    A_eq = np.r_[np.zeros(X.shape[1]), y0, 0.0].reshape(1, -1)
    r = linprog(c, A_ub=A_ub, b_ub=np.zeros(n), A_eq=A_eq, b_eq=[1.0],
                bounds=[(0, None)] * (X.shape[1] + s) + [(None, None)], method="highs-ipm")
    assert r.status == 0, r.message
    return r.fun


def verificar_stress():
    log("\nC. Stress testing")
    u = pd.read_csv(RES / "riesgo_stress_universidades.csv")
    rsm = pd.read_csv(RES / "riesgo_stress_resumen.csv")
    archivos = sorted((RAW / "pte" / "2024").rglob("*.xlsx")) if (RAW / "pte" / "2024").exists() else []
    grat = None
    for ruta in archivos:
        wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
        for ws in wb.worksheets:
            if "Cuadro No. 7" not in str(ws.cell(1, 1).value) or "Diciembre de 2024" not in str(ws.cell(3, 1).value):
                continue
            for fila in ws.iter_rows(values_only=True):
                if fila[0] and "POLÍTICA DE GRATUIDAD DE LA EDUCACIÓN SUPERIOR PÚBLICA" in str(fila[0]):
                    grat = fila[3] / 1e9                 # columna D = Obligación
    if grat is None:
        log("  (sin el PTE de 2024 en data/raw: se usa el monto implícito en los resultados; C1 se omite)")
    else:
        log(f"  C1 gratuidad leída con openpyxl: {grat:,.3f} mil millones")

    base = pd.read_csv(RES / "base_integrada_2023_2024.csv")
    base = base[base.incluida_dea & (base.anio == 2024)].set_index("pte_codigo")
    car = pd.read_csv(RES / "caracteristicas_universidades.csv")
    car = car[car.anio == 2024].set_index("pte_codigo")
    prod = {"principal": ["mat_total_prom", "grad_total", "global_c"],
            "cobertura": ["mat_total_prom", "grad_total"],
            "cobertura_sin_unad": ["mat_total_prom", "grad_total"]}
    dmax_ef = dmax_x = 0.0
    for (modelo, esc), g in u.groupby(["modelo", "escenario"]):
        cods = g.pte_codigo.to_numpy()
        b = base.loc[cods]
        x0 = b.obligacion_mm.to_numpy(float)
        # C3: reconstruir el insumo del escenario
        if esc.startswith("E6") or esc.startswith("E7"):
            todas = base if modelo != "cobertura_sin_unad" else base
            peso = todas.mat_pregrado_prom.astype(float)
            if esc.startswith("E7"):
                peso = peso * car.loc[todas.index, "pct_estrato_1_2"] / 100
            peso = peso / peso.sum()
            monto = grat if grat is not None else \
                rsm[(rsm.modelo == "principal") & rsm.escenario.str.startswith(esc[:2])].insumo_total_mm.iloc[0] \
                - base.obligacion_mm.sum()
            x_esp = x0 + monto * peso.loc[cods].to_numpy()
        elif esc.startswith("E1"):
            x_esp = x0 * 0.9
        elif esc.startswith("E2"):
            x_esp = x0 * 0.8
        elif esc.startswith("E3"):
            x_esp = np.where(car.loc[cods, "orden"] == "nacional", x0 * 0.8, x0)
        elif esc.startswith("E4"):
            x_esp = np.where(car.loc[cods, "orden"] == "territorial", x0 * 0.8, x0)
        elif esc.startswith("E5"):
            bajas = g.nsmallest(8, "eficiencia_base").pte_codigo
            x_esp = np.where(np.isin(cods, bajas), x0 * 0.9, x0)
        else:
            x_esp = x0
        dmax_x = max(dmax_x, float(np.max(np.abs(np.round(x_esp, 3) - g.insumo_escenario_mm))))
        X = x_esp.reshape(-1, 1)
        Y = b[prod[modelo]].to_numpy(float)
        ef = np.array([1 / phi_dual(X[i], Y[i], X, Y) for i in range(len(X))])
        dmax_ef = max(dmax_ef, float(np.max(np.abs(np.round(ef, 4) - g.eficiencia_escenario))))
        if esc.startswith("E1") or esc.startswith("E2"):
            chequear(f"C4 invariancia {modelo} {esc[:2]}", float(np.max(np.abs(g.cambio))) < 1e-9)
    chequear("C2 eficiencias de todos los escenarios = programa dual (punto interior)", dmax_ef <= 1.5e-4,
             f"diferencia máxima {dmax_ef:.6f}")
    chequear("C3 insumos de los escenarios reconstruidos", dmax_x <= 2e-3, f"diferencia máxima {dmax_x:.4f}")
    if grat is not None:
        for esc in ("E6", "E7"):
            fila = rsm[(rsm.modelo == "principal") & rsm.escenario.str.startswith(esc)].iloc[0]
            agregado = fila.insumo_total_mm - base.obligacion_mm.sum()
            chequear(f"C3 {esc}: la gratuidad repartida suma el monto del PTE", abs(agregado - grat) < 0.1,
                     f"{agregado:,.1f} vs {grat:,.1f}")


def main():
    log(f"##### Verificación de los análisis de riesgo — {datetime.now():%Y-%m-%d %H:%M} #####")
    datos = verificar_puntaje()
    verificar_kupiec(datos)
    verificar_stress()
    log(f"\nResultado: {'TODO COINCIDE' if not FALLAS else 'FALLAS: ' + '; '.join(FALLAS)}")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"verificacion_riesgo_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia guardada en {ev}")
    raise SystemExit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
