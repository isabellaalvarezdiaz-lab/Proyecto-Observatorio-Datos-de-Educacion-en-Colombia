"""
imputar_escrita.py — Imputación de los ceros de Comunicación Escrita por perfiles similares
(predictive mean matching, PMM) y su efecto en el DEA y en el riesgo de cola. 2023-2024.

Problema
  En los microdatos, quien tiene 0 en Escrita tiene el nivel de desempeño VACÍO: el cero no es un
  puntaje, es un dato faltante (ver diagnostico_ceros_escrita.py). Hasta ahora el proyecto usa
  global_c: para esos evaluados, el global es el promedio de sus otros cuatro módulos. Eso equivale
  a suponer que su Escrita habría sido igual al promedio de sus otros módulos. Este script cambia
  ese supuesto por uno estimado con los datos, como sugirió el profesor: el valor faltante se toma
  de evaluados con un perfil parecido que sí tienen Escrita.

Método
  1. Modelo de perfil (lineal, mínimos cuadrados), ajustado con los evaluados que SÍ tienen Escrita
     (> 0) y sus otros cuatro módulos completos, 2023 y 2024 juntos:
         Escrita ≈ b0 + b1·Ciudadanas + b2·Inglés + b3·Lectura + b4·Razonamiento + b5·[año = 2024]
  2. PMM (predictive mean matching), con K_DONANTES donantes: para cada evaluado con cero se
     calcula su Escrita predicha; se buscan los K evaluados con Escrita observada cuya predicción
     es la más cercana (su "perfil" es el más parecido) y se toma al azar el puntaje REAL de uno
     de ellos. Así lo imputado siempre es un puntaje que alguien sacó, y se conserva la dispersión
     (la predicción sola daría a todos el promedio condicional y achicaría la cola).
  3. Imputación múltiple: M imputaciones con semillas distintas. Los agregados se promedian entre
     imputaciones y se reporta su desviación entre imputaciones.
  4. global_d = promedio de los cinco módulos con la Escrita imputada (el ICFES calcula el global
     como el promedio de los módulos presentes; para quien no tiene cero, global_d = punt_global).
     Si al evaluado con cero le falta otro módulo, no hay perfil completo y se deja global_c.

  ¿Por qué lineal y no KNN o un modelo más flexible? En una partición de validación (20 % de los
  evaluados con Escrita, que no entran al ajuste), el modelo lineal predice casi igual que un
  gradient boosting y mejor que KNN con 20 vecinos sobre los cuatro módulos; los tres son mucho
  mejores que el supuesto de global_c (ver el MAE en la evidencia). El lineal además se guarda en
  un JSON de pocos números, sin ningún registro individual, y así la API puede usarlo sin datos.

Validación del supuesto (no se puede verificar del todo)
  La validación solo usa evaluados que presentaron Escrita. Si los que tienen cero son distintos
  de los de su mismo perfil (supuesto MAR: dado el perfil, el faltante no depende del valor que
  habrían sacado), la imputación tiene sesgo. Por eso esto es un análisis de SENSIBILIDAD: se
  compara global_d con global_c en el DEA y en el CVaR, sin reemplazar los resultados principales.

Entradas: data/raw/saber_pro/Examen_Saber_Pro_Genericas_AAAA.txt (microdatos; no se suben),
          resultados/sedes_por_universidad.csv, resultados/base_integrada_2023_2024.csv,
          resultados/oe3_eficiencia.csv, resultados/riesgo_puntaje.csv
Salidas:  modelos/imputador_escrita.json                 coeficientes, residuos y métricas (sin datos individuales)
          resultados/imputacion_escrita_universidades.csv global_c frente a global_d por universidad y año
          resultados/imputacion_escrita_sensibilidad.csv  efecto en el DEA principal y en el CVaR
Evidencia: docs/gobernanza/evidencias/imputacion_escrita_AAAA-MM-DD_HHMM.txt

Publicación: el JSON solo tiene coeficientes, cuantiles de los residuos y conteos de más de
  200.000 evaluados; los CSV son agregados por universidad (la universidad más pequeña tiene
  más de K_MIN = 5 evaluados).

Uso (desde la raíz del repositorio; tarda menos de un minuto):
    python scripts/imputar_escrita.py
    python scripts/imputar_escrita.py --M 5 --donantes 5 --semilla 20261106

Requiere: pandas, numpy, scipy (y scikit-learn solo para las comparaciones de la validación).
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dea  # noqa: E402
from publicacion import K_MIN  # noqa: E402
from riesgo_puntaje import var_cvar  # noqa: E402

ESCRITA = "mod_comuni_escrita_punt"
MODULOS = ["mod_competen_ciudada_punt", ESCRITA, "mod_ingles_punt",
           "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"]
OTROS_4 = [m for m in MODULOS if m != ESCRITA]
NOMBRES = {"mod_competen_ciudada_punt": "ciudadanas", "mod_ingles_punt": "ingles",
           "mod_lectura_critica_punt": "lectura_critica", "mod_razona_cuantitat_punt": "razonamiento"}
ANIOS = (2023, 2024)
LOG = []


def log(t=""):
    print(t)
    LOG.append(str(t))


def leer(ruta, anio):
    """Misma población que agregar_saber_pro.py: evaluados con código de institución y global."""
    d = pd.read_csv(ruta, sep=";", low_memory=False,
                    usecols=MODULOS + ["punt_global", "inst_cod_institucion"])
    d = d.dropna(subset=["inst_cod_institucion", "punt_global"]).reset_index(drop=True)
    d["cod_institucion"] = d["inst_cod_institucion"].astype("int64")
    d["anio"] = anio
    d["cero"] = d[ESCRITA].eq(0)
    d["global_c"] = d["punt_global"].where(~d["cero"], d[OTROS_4].mean(axis=1))
    return d


def disenio(d):
    """Matriz del modelo: intercepto, los cuatro módulos y el indicador de 2024."""
    return np.column_stack([np.ones(len(d)), d[OTROS_4].to_numpy(float),
                            (d["anio"] == 2024).to_numpy(float)])


def pmm(pred_donantes, y_donantes, pred_receptores, k, rng):
    """Para cada receptor, un puntaje observado al azar entre los k donantes de predicción más
    cercana. Los donantes se ordenan por predicción y se busca la ventana de los k más cercanos."""
    orden = np.argsort(pred_donantes, kind="stable")
    p = pred_donantes[orden]
    y = y_donantes[orden]
    n = len(p)
    pos = np.searchsorted(p, pred_receptores)
    # ventana candidata de 2k alrededor de la posición; se eligen los k más cercanos dentro
    ini = np.clip(pos - k, 0, n - 2 * k)
    cand = ini[:, None] + np.arange(2 * k)[None, :]
    dist = np.abs(p[cand] - pred_receptores[:, None])
    cerc = np.take_along_axis(cand, np.argsort(dist, axis=1, kind="stable")[:, :k], axis=1)
    elegido = cerc[np.arange(len(cerc)), rng.integers(0, k, size=len(cerc))]
    return y[elegido]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--M", type=int, default=5, help="número de imputaciones")
    ap.add_argument("--donantes", type=int, default=5, help="donantes por receptor en el PMM")
    ap.add_argument("--semilla", type=int, default=20261106)
    ap.add_argument("--alfa", type=float, default=0.05, help="nivel del CVaR de la sensibilidad")
    ap.add_argument("--saber-dir", default=str(Path("data") / "raw" / "saber_pro"))
    args = ap.parse_args()
    rng = np.random.default_rng(args.semilla)
    res = Path("resultados")

    log(f"##### Imputación de ceros en Escrita por PMM — {datetime.now():%Y-%m-%d %H:%M} #####")
    log(f"M = {args.M} | donantes = {args.donantes} | semilla = {args.semilla}")

    d = pd.concat([leer(Path(args.saber_dir) / f"Examen_Saber_Pro_Genericas_{a}.txt", a) for a in ANIOS],
                  ignore_index=True)
    completos = d[OTROS_4].notna().all(axis=1)
    obs = (~d["cero"]) & d[ESCRITA].notna() & completos
    rec = d["cero"] & completos
    for a in ANIOS:
        s = d.anio == a
        log(f"{a}: evaluados {s.sum():,} | ceros en Escrita {(d.cero & s).sum():,} | "
            f"ceros con los otros 4 módulos completos {(rec & s).sum():,}")
    log(f"Ceros sin perfil completo (se quedan con global_c): {(d.cero & ~completos).sum():,}")

    # ------------------------------------------------- 1. validación (partición 80/20)
    idx = np.flatnonzero(obs.to_numpy())
    idx = rng.permutation(idx)
    n_val = len(idx) // 5
    val, ent = idx[:n_val], idx[n_val:]
    X = disenio(d)
    y = d[ESCRITA].to_numpy(float)
    b_ent, *_ = np.linalg.lstsq(X[ent], y[ent], rcond=None)

    def metricas(pred):
        e = pred - y[val]
        return dict(mae=float(np.abs(e).mean()), rmse=float(np.sqrt((e ** 2).mean())), sesgo=float(e.mean()))

    comp = {"supuesto_global_c": metricas(d.loc[val, OTROS_4].mean(axis=1).to_numpy()),
            "lineal_pmm": metricas(X[val] @ b_ent)}
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.neighbors import KNeighborsRegressor
        Xs = X[:, 1:]
        hgb = HistGradientBoostingRegressor(min_samples_leaf=50, random_state=1).fit(Xs[ent], y[ent])
        comp["gradient_boosting"] = metricas(hgb.predict(Xs[val]))
        knn = KNeighborsRegressor(20).fit(Xs[ent, :4], y[ent])
        comp["knn_20"] = metricas(knn.predict(Xs[val, :4]))
    except ImportError:
        log("  (scikit-learn no está instalado: se omiten las comparaciones con boosting y KNN)")
    sd_y = float(y[val].std())
    log(f"\n=== 1. Validación: {len(val):,} evaluados con Escrita que no entran al ajuste "
        f"(desviación de Escrita = {sd_y:.1f}) ===")
    for k, m in comp.items():
        log(f"  {k:20s} MAE {m['mae']:6.2f} | RMSE {m['rmse']:6.2f} | sesgo {m['sesgo']:+6.2f}")
    r2 = 1 - comp["lineal_pmm"]["rmse"] ** 2 / sd_y ** 2
    log(f"  R² del modelo lineal en validación: {r2:.3f}. Escrita se predice mal a nivel individual;")
    log("  por eso se imputa con PMM (puntajes reales de donantes) y se mira el efecto en agregados.")

    # ------------------------------------------------- 2. modelo final (todos los observados)
    b, *_ = np.linalg.lstsq(X[obs.to_numpy()], y[obs.to_numpy()], rcond=None)
    pred = X @ b
    resid = y[obs.to_numpy()] - pred[obs.to_numpy()]
    q = np.percentile(resid, [2.5, 10, 50, 90, 97.5])
    log("\n=== 2. Modelo final (todos los evaluados con Escrita) ===")
    log(f"  Escrita = {b[0]:.3f} " + " ".join(f"{c:+.4f}·{NOMBRES[m]}" for c, m in zip(b[1:5], OTROS_4))
        + f" {b[5]:+.3f}·[2024]")
    log(f"  residuos: desviación {resid.std():.2f} | cuantiles 2.5/10/50/90/97.5 = {np.round(q, 1).tolist()}")
    pred_ceros = pred[rec.to_numpy()]
    log(f"  Escrita predicha promedio de los ceros: {pred_ceros.mean():.1f} | lo que supone global_c: "
        f"{d.loc[rec, OTROS_4].mean(axis=1).mean():.1f}")

    modelo = {
        "nombre": "imputador_escrita",
        "version": datetime.now().strftime("%Y-%m-%d"),
        "descripcion": "Escrita (Saber Pro) predicha por un modelo lineal con los otros cuatro módulos y el año. "
                       "Ajustado con los evaluados con Escrita > 0, microdatos ICFES 2023-2024.",
        "variables": [NOMBRES[m] for m in OTROS_4] + ["anio_2024"],
        "intercepto": round(float(b[0]), 6),
        "coeficientes": {**{NOMBRES[m]: round(float(c), 6) for m, c in zip(OTROS_4, b[1:5])},
                         "anio_2024": round(float(b[5]), 6)},
        "residuos": {"desviacion": round(float(resid.std()), 4),
                     "cuantiles": {k: round(float(v), 4) for k, v in zip(["p2_5", "p10", "p50", "p90", "p97_5"], q)}},
        "rango_puntaje": [0, 300],
        "n_entrenamiento": int(obs.sum()),
        "validacion": {"n": int(len(val)), "r2_lineal": round(float(r2), 4),
                       **{k: {kk: round(vv, 4) for kk, vv in m.items()} for k, m in comp.items()}},
        "fuente": "ICFES, Examen Saber Pro Genéricas 2023 y 2024 (microdatos; no se publican)",
        "script": "scripts/imputar_escrita.py",
    }
    Path("modelos").mkdir(exist_ok=True)
    with open(Path("modelos") / "imputador_escrita.json", "w", encoding="utf-8") as f:
        json.dump(modelo, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------- 3. PMM con M imputaciones
    donantes_p, donantes_y = pred[obs.to_numpy()], y[obs.to_numpy()]
    imput = np.empty((args.M, int(rec.sum())))
    for m in range(args.M):
        imput[m] = pmm(donantes_p, donantes_y, pred_ceros, args.donantes, np.random.default_rng(args.semilla + m + 1))
    suma_otros = d.loc[rec, OTROS_4].sum(axis=1).to_numpy()
    globales_d = np.tile(d["global_c"].to_numpy(), (args.M, 1))
    globales_d[:, rec.to_numpy()] = (suma_otros[None, :] + imput) / 5
    log(f"\n=== 3. PMM: Escrita imputada promedio {imput.mean():.1f} "
        f"(entre imputaciones: {np.round(imput.mean(axis=1), 2).tolist()}) ===")

    # ------------------------------------------------- 4. agregados por universidad
    sedes = pd.read_csv(res / "sedes_por_universidad.csv")[["pte_codigo", "cod_institucion"]]
    base = pd.read_csv(res / "base_integrada_2023_2024.csv")
    base = base[base.incluida_dea]
    univ = base.drop_duplicates("pte_codigo").set_index("pte_codigo")["pte_nombre"]
    cod = d["cod_institucion"].map(sedes.set_index("cod_institucion")["pte_codigo"])
    filas = []
    for a in ANIOS:
        for clave in ["nacional", "33 universidades"] + list(univ.index):
            if clave == "nacional":
                s = (d.anio == a).to_numpy()
            elif clave == "33 universidades":
                s = ((d.anio == a) & cod.isin(univ.index)).to_numpy()
            else:
                s = ((d.anio == a) & (cod == clave)).to_numpy()
            gd = globales_d[:, s].mean(axis=1)
            filas.append(dict(anio=a, pte_codigo=None if isinstance(clave, str) else int(clave),
                              pte_nombre=clave if isinstance(clave, str) else univ[clave],
                              n_evaluados=int(s.sum()), n_ceros_escrita=int(d.cero.to_numpy()[s].sum()),
                              global_c=d["global_c"].to_numpy()[s].mean(), global_d=gd.mean(),
                              global_d_de_entre_imputaciones=gd.std(ddof=1) if args.M > 1 else 0.0))
    tabla = pd.DataFrame(filas)
    tabla["diferencia_d_menos_c"] = tabla.global_d - tabla.global_c
    tabla = tabla.round({"global_c": 2, "global_d": 2, "global_d_de_entre_imputaciones": 3, "diferencia_d_menos_c": 2})
    assert (tabla.loc[tabla.pte_codigo.notna(), "n_evaluados"] >= K_MIN).all()
    # la población reproduce la base integrada
    chk = tabla.dropna(subset=["pte_codigo"]).merge(base[["pte_codigo", "anio", "global_c"]],
                                                    on=["pte_codigo", "anio"], suffixes=("", "_base"))
    assert len(chk) == 2 * len(univ) and (chk.global_c - chk.global_c_base).abs().max() <= 0.01, "no reproduce global_c"
    tabla.to_csv(res / "imputacion_escrita_universidades.csv", index=False, encoding="utf-8-sig")
    log("\n=== 4. global_c frente a global_d (promedio de las M imputaciones) ===")
    for a in ANIOS:
        t = tabla[(tabla.anio == a) & tabla.pte_codigo.notna()]
        nac = tabla[(tabla.anio == a) & (tabla.pte_nombre == "nacional")].iloc[0]
        log(f"  {a}: nacional {nac.global_c:.2f} → {nac.global_d:.2f} | en las 33: diferencia media "
            f"{t.diferencia_d_menos_c.mean():+.2f}, máxima {t.diferencia_d_menos_c.max():+.2f} "
            f"({t.loc[t.diferencia_d_menos_c.idxmax(), 'pte_nombre']}) | Spearman c vs d "
            f"{dea.spearman(t.global_c.to_numpy(), t.global_d.to_numpy()):.4f}")

    # ------------------------------------------------- 5. sensibilidad: DEA principal y CVaR
    oe3 = pd.read_csv(res / "oe3_eficiencia.csv")
    oe3 = oe3[oe3.modelo == "principal"]
    rk = pd.read_csv(res / "riesgo_puntaje.csv")
    sens = []
    log("\n=== 5. Sensibilidad ===")
    for a in ANIOS:
        b_a = base[base.anio == a].sort_values("pte_codigo").merge(
            tabla[tabla.anio == a][["pte_codigo", "global_d"]], on="pte_codigo")
        Xd = b_a[["obligacion_mm"]].to_numpy(float)
        ef_c, _ = dea.eficiencia(Xd, b_a[["mat_total_prom", "grad_total", "global_c"]].to_numpy(float))
        ef_d, _ = dea.eficiencia(Xd, b_a[["mat_total_prom", "grad_total", "global_d"]].to_numpy(float))
        ref = b_a[["pte_codigo"]].merge(oe3[oe3.anio == a][["pte_codigo", "eficiencia"]], on="pte_codigo")
        assert np.abs(ef_c - ref.eficiencia.to_numpy()).max() <= 1e-4, "la base no reproduce el OE3"
        cambio = ef_d - ef_c
        i = int(np.argmax(np.abs(cambio)))
        sens.append(dict(anio=a, analisis="DEA principal (eficiencia)", spearman_c_vs_d=dea.spearman(ef_c, ef_d),
                         media_c=ef_c.mean(), media_d=ef_d.mean(),
                         n_frontera_c=int((ef_c > 1 - 1e-6).sum()), n_frontera_d=int((ef_d > 1 - 1e-6).sum()),
                         cambio_max=cambio[i], universidad_cambio_max=b_a.pte_nombre.iloc[i] if abs(cambio[i]) > 1e-6 else "ninguna"))
        log(f"  DEA {a}: Spearman {sens[-1]['spearman_c_vs_d']:.4f} | media {ef_c.mean():.4f} → {ef_d.mean():.4f} | "
            f"frontera {sens[-1]['n_frontera_c']} → {sens[-1]['n_frontera_d']} | cambio máximo "
            f"{cambio[i]:+.4f} ({sens[-1]['universidad_cambio_max']})")

        # CVaR con global_d (promedio sobre las M imputaciones) frente al CVaR publicado (global_c)
        cv_d = []
        for p in b_a.pte_codigo:
            s = ((d.anio == a) & (cod == p)).to_numpy()
            cv_d.append(np.mean([var_cvar(globales_d[m, s], args.alfa)[1] for m in range(args.M)]))
        cv_d = np.array(cv_d)
        cv_c = b_a[["pte_codigo"]].merge(rk[rk.anio == a][["pte_codigo", "cvar"]], on="pte_codigo").cvar.to_numpy()
        dif = cv_d - cv_c
        i = int(np.argmax(np.abs(dif)))
        sens.append(dict(anio=a, analisis=f"CVaR {args.alfa:.0%} del puntaje", spearman_c_vs_d=dea.spearman(cv_c, cv_d),
                         media_c=cv_c.mean(), media_d=cv_d.mean(), n_frontera_c=None, n_frontera_d=None,
                         cambio_max=dif[i], universidad_cambio_max=b_a.pte_nombre.iloc[i]))
        log(f"  CVaR {a}: Spearman {sens[-1]['spearman_c_vs_d']:.4f} | media {cv_c.mean():.2f} → {cv_d.mean():.2f} | "
            f"cambio máximo {dif[i]:+.2f} ({b_a.pte_nombre.iloc[i]})")
    s = pd.DataFrame(sens).round({"spearman_c_vs_d": 4, "media_c": 4, "media_d": 4, "cambio_max": 4})
    s.to_csv(res / "imputacion_escrita_sensibilidad.csv", index=False, encoding="utf-8-sig")

    log("\nSalidas: modelos/imputador_escrita.json, resultados/imputacion_escrita_universidades.csv, "
        "resultados/imputacion_escrita_sensibilidad.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"imputacion_escrita_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia guardada en {ev}")


if __name__ == "__main__":
    main()
