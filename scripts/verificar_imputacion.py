"""
verificar_imputacion.py — Verificación independiente de imputar_escrita.py: recalcula por otro
camino lo que se publica y avisa si algo no coincide.

  A1  Coeficientes del modelo: mínimos cuadrados con scipy.linalg.lstsq (no numpy) sobre la misma
      población, comparados con modelos/imputador_escrita.json.
  A2  Residuos: desviación y cuantiles recalculados.
  A3  El JSON no trae registros individuales: solo las claves esperadas, y pesa menos de 5 KB.
  B1  global_c por universidad: igual a la base integrada.
  B2  global_d: con PMM, lo imputado a cada receptor es al azar uno de sus k donantes, así que su
      valor ESPERADO es el promedio de esos k donantes. Se buscan los k donantes por fuerza bruta
      (argpartition sobre las distancias, no la ventana ordenada del script), se calcula el
      global_d esperado de cada universidad y se compara con el publicado (promedio de M
      imputaciones) con una tolerancia de 4 errores estándar de muestreo de las M imputaciones.
  C1  Sensibilidad del DEA: eficiencias con global_d por el programa de MULTIPLICADORES (dual, no
      el envolvente del script), comparadas con imputacion_escrita_sensibilidad.csv.

Uso (desde la raíz del repositorio; tarda unos 4 minutos por la búsqueda de donantes por fuerza bruta):
    python scripts/verificar_imputacion.py
Evidencia: docs/gobernanza/evidencias/verificacion_imputacion_AAAA-MM-DD_HHMM.txt
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dea  # noqa: E402

ESCRITA = "mod_comuni_escrita_punt"
OTROS = ["mod_competen_ciudada_punt", "mod_ingles_punt", "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
NOMBRES = ["ciudadanas", "ingles", "lectura_critica", "razonamiento"]
LOG, FALLAS = [], []


def log(t=""):
    print(t)
    LOG.append(str(t))


def chequeo(nombre, ok, detalle=""):
    log(f"  [{'OK' if ok else 'FALLA'}] {nombre}{(' — ' + detalle) if detalle else ''}")
    if not ok:
        FALLAS.append(nombre)


def main():
    res = Path("resultados")
    meta = json.loads((Path("modelos") / "imputador_escrita.json").read_text(encoding="utf-8"))
    tabla = pd.read_csv(res / "imputacion_escrita_universidades.csv")
    sens = pd.read_csv(res / "imputacion_escrita_sensibilidad.csv")
    log(f"##### Verificación de la imputación de Escrita — {datetime.now():%Y-%m-%d %H:%M} #####")

    partes = []
    for anio in (2023, 2024):
        d = pd.read_csv(Path("data") / "raw" / "saber_pro" / f"Examen_Saber_Pro_Genericas_{anio}.txt", sep=";",
                        usecols=OTROS + [ESCRITA, "punt_global", "inst_cod_institucion"], low_memory=False)
        d = d.dropna(subset=["inst_cod_institucion", "punt_global"])
        d["anio"] = anio
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    d["cod"] = d.inst_cod_institucion.astype("int64")
    completos = d[OTROS].notna().all(axis=1)
    obs = d[ESCRITA].gt(0) & completos
    rec = d[ESCRITA].eq(0) & completos

    # ---------------------------------------------------------------- A. modelo
    log("\nA. Modelo")
    X = np.column_stack([np.ones(len(d)), d[OTROS].to_numpy(float), (d.anio == 2024).to_numpy(float)])
    y = d[ESCRITA].to_numpy(float)
    b, *_ = linalg.lstsq(X[obs.to_numpy()], y[obs.to_numpy()])
    publicados = np.array([meta["intercepto"]] + [meta["coeficientes"][k] for k in NOMBRES + ["anio_2024"]])
    dif = np.abs(b - publicados).max()
    chequeo("A1 coeficientes (scipy.linalg.lstsq)", dif < 1e-5, f"diferencia máxima {dif:.2e}")
    resid = y[obs.to_numpy()] - X[obs.to_numpy()] @ b
    q = np.percentile(resid, [2.5, 10, 50, 90, 97.5])
    qp = np.array(list(meta["residuos"]["cuantiles"].values()))
    chequeo("A2 residuos (desviación y cuantiles)",
            abs(resid.std() - meta["residuos"]["desviacion"]) < 1e-3 and np.abs(q - qp).max() < 1e-3,
            f"desviación {resid.std():.4f} vs {meta['residuos']['desviacion']}")
    claves = {"nombre", "version", "descripcion", "variables", "intercepto", "coeficientes", "residuos",
              "rango_puntaje", "n_entrenamiento", "validacion", "fuente", "script"}
    tam = (Path("modelos") / "imputador_escrita.json").stat().st_size
    chequeo("A3 el JSON solo tiene parámetros y métricas", set(meta) == claves and tam < 5000, f"{tam} bytes")
    chequeo("A3 n de entrenamiento", meta["n_entrenamiento"] == int(obs.sum()), f"{int(obs.sum()):,}")

    # ---------------------------------------------------------------- B. agregados
    log("\nB. Agregados por universidad")
    sedes = pd.read_csv(res / "sedes_por_universidad.csv")[["pte_codigo", "cod_institucion"]]
    d["pte"] = d.cod.map(sedes.set_index("cod_institucion").pte_codigo)
    cero = d[ESCRITA].eq(0)
    d["global_c"] = d.punt_global.where(~cero, d[OTROS].mean(axis=1))
    base = pd.read_csv(res / "base_integrada_2023_2024.csv")
    base = base[base.incluida_dea]
    gc = d[d.pte.isin(base.pte_codigo)].groupby(["pte", "anio"]).global_c.mean()
    t = tabla.dropna(subset=["pte_codigo"]).set_index(["pte_codigo", "anio"])
    dif_c = np.abs(gc.reindex(t.index).to_numpy() - t.global_c.to_numpy()).max()
    chequeo("B1 global_c", dif_c <= 0.006, f"diferencia máxima {dif_c:.4f}")

    # donantes por fuerza bruta, en bloques
    k, M = 5, 5
    pd_don = X[obs.to_numpy()] @ b
    y_don = y[obs.to_numpy()]
    pr = X[rec.to_numpy()] @ b
    esperado = np.empty(len(pr))
    var_don = np.empty(len(pr))
    for i in range(0, len(pr), 100):
        bloque = pr[i:i + 100]
        dist = np.abs(pd_don[None, :] - bloque[:, None])
        idx = np.argpartition(dist, k, axis=1)[:, :k]
        vals = y_don[idx]
        esperado[i:i + 100] = vals.mean(axis=1)
        var_don[i:i + 100] = vals.var(axis=1)
    d["gd_esp"] = d.global_c
    d["gd_var"] = 0.0
    d.loc[rec, "gd_esp"] = (d.loc[rec, OTROS].sum(axis=1).to_numpy() + esperado) / 5
    d.loc[rec, "gd_var"] = var_don / 25 / M          # varianza del promedio de M imputaciones
    g = d[d.pte.isin(base.pte_codigo)].groupby(["pte", "anio"]).agg(esp=("gd_esp", "mean"), v=("gd_var", "sum"),
                                                                    n=("gd_esp", "size"))
    g = g.reindex(t.index)
    se = np.sqrt(g.v / g.n ** 2)
    z = (t.global_d - g.esp) / np.maximum(se, 1e-9)
    # tolerancia: 4 errores estándar, más 0,006 por el redondeo a 2 decimales
    ok = (np.abs(t.global_d - g.esp) <= 4 * se + 0.006)
    chequeo("B2 global_d esperado por PMM de fuerza bruta", bool(ok.all()),
            f"|z| máximo {np.abs(z[se > 0]).max():.2f}; universidades fuera de tolerancia {int((~ok).sum())}")
    nac = tabla[tabla.pte_nombre == "nacional"].set_index("anio")
    for anio in (2023, 2024):
        s = d.anio == anio
        chequeo(f"B2 global_d nacional {anio}", abs(d.loc[s, "gd_esp"].mean() - nac.loc[anio, "global_d"]) < 0.02,
                f"esperado {d.loc[s, 'gd_esp'].mean():.3f} vs publicado {nac.loc[anio, 'global_d']}")

    # ---------------------------------------------------------------- C. DEA con global_d
    log("\nC. Sensibilidad del DEA (programa de multiplicadores)")
    for anio in (2023, 2024):
        b_a = base[base.anio == anio].merge(tabla[tabla.anio == anio][["pte_codigo", "global_d"]], on="pte_codigo")
        Xd = b_a[["obligacion_mm"]].to_numpy(float)
        Yd = b_a[["mat_total_prom", "grad_total", "global_d"]].to_numpy(float)
        ef = np.array([1 / dea.phi_multiplicadores(Xd[o], Yd[o], Xd, Yd, metodo="highs-ipm") for o in range(len(Xd))])
        fila = sens[(sens.anio == anio) & sens.analisis.str.startswith("DEA")].iloc[0]
        chequeo(f"C1 eficiencia media {anio} con global_d", abs(ef.mean() - fila.media_d) < 1e-4,
                f"{ef.mean():.4f} vs {fila.media_d}")
        chequeo(f"C1 frontera {anio} con global_d", int((ef > 1 - 1e-6).sum()) == int(fila.n_frontera_d),
                f"{int((ef > 1 - 1e-6).sum())} vs {int(fila.n_frontera_d)}")

    log(f"\nResultado: {'TODO COINCIDE' if not FALLAS else 'HAY DIFERENCIAS: ' + ', '.join(FALLAS)}")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"verificacion_imputacion_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia guardada en {ev}")
    sys.exit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
