"""
oe3_dea_bootstrap.py — OE3. Eficiencia de las universidades públicas en 2023 y 2024 con DEA
orientado al producto y rendimientos variables (BCC), corregida por sesgo con el bootstrap de
Simar y Wilson (1998). Incluye pares, metas y análisis de sensibilidad.

Entrada:  resultados/base_integrada_2023_2024.csv (filas con incluida_dea = True)
Modelos:
  principal  insumo: obligación (PTE)  →  productos: matrícula promedio, graduados, puntaje global_c
  cobertura  insumo: obligación (PTE)  →  productos: matrícula promedio, graduados
             (el puntaje varía poco entre universidades — coef. de variación ≈ 0,08 — y en un
             modelo radial limita la expansión de todos los productos; este modelo muestra la
             eficiencia en cobertura por separado, como Galvis-Aponte (2015) separa cobertura y calidad)
Salidas (resultados/):
  oe3_eficiencia.csv            una fila por universidad, año y modelo: eficiencia, corregida,
                                intervalo 95 %, pares, metas y holguras
  oe3_deja_uno_fuera.csv        efecto de sacar cada universidad de la frontera
  oe3_sensibilidad.csv          principal con global_b (sin los estudiantes con 0 en Escrita)
Evidencia: docs/gobernanza/evidencias/oe3_dea_bootstrap_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio; tarda unos 10 minutos con B = 2000):
    python scripts/oe3_dea_bootstrap.py
    python scripts/oe3_dea_bootstrap.py --B 200      (prueba rápida)
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dea  # noqa: E402

INSUMO = ["obligacion_mm"]
MODELOS = {
    "principal": ["mat_total_prom", "grad_total", "global_c"],
    "cobertura": ["mat_total_prom", "grad_total"],
}
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=2000, help="réplicas bootstrap")
    ap.add_argument("--semilla", type=int, default=20261011)
    args = ap.parse_args()

    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    base = base[base.incluida_dea].copy()
    anios = sorted(base.anio.unique())
    log(f"##### OE3 — DEA BCC orientado al producto + bootstrap Simar-Wilson — {datetime.now():%Y-%m-%d %H:%M} #####")
    log(f"Réplicas bootstrap B = {args.B} | semilla = {args.semilla} | universidades por año: "
        f"{base.groupby('anio').size().to_dict()}")

    filas, loo, sens = [], [], []
    for modelo, prods in MODELOS.items():
        for a in anios:
            d = base[base.anio == a].reset_index(drop=True)
            X = d[INSUMO].to_numpy(float)
            Y = d[prods].to_numpy(float)
            n = len(d)
            log(f"\n=== Modelo {modelo} · {a} (n = {n}) ===")
            bs = dea.bootstrap_simar_wilson(X, Y, B=args.B, semilla=args.semilla)
            log(f"  ancho de banda h = {bs['h']:.4f}")
            for o in range(n):
                phi = 1 / bs["delta"][o]
                meta, hs, _, lam = dea.metas(X[o], Y[o], X, Y, phi)
                pares = "; ".join(f"{d.pte_nombre[j]} ({lam[j]:.2f})"
                                  for j in np.argsort(-lam) if lam[j] > 1e-6 and j != o)
                fila = dict(modelo=modelo, anio=a, pte_codigo=d.pte_codigo[o], pte_nombre=d.pte_nombre[o],
                            eficiencia=bs["delta"][o], eficiencia_corregida=bs["delta_corregida"][o],
                            ic95_inf=bs["ic_inf"][o], ic95_sup=bs["ic_sup"][o], sesgo_phi=bs["sesgo_phi"][o],
                            en_frontera=bs["delta"][o] > 1 - 1e-9, pares=pares)
                for k, p in enumerate(prods):
                    fila[f"{p}_actual"] = Y[o, k]
                    fila[f"{p}_meta"] = meta[k]
                filas.append(fila)
            ef = pd.DataFrame([f for f in filas if f["modelo"] == modelo and f["anio"] == a])
            log(f"  eficiencia media {ef.eficiencia.mean():.3f} (corregida {ef.eficiencia_corregida.mean():.3f}) | "
                f"mínima {ef.eficiencia.min():.3f} | en la frontera: {int(ef.en_frontera.sum())}")
            log("  frontera: " + ", ".join(ef.loc[ef.en_frontera, "pte_nombre"]))

            # --- deja uno fuera: solo las de la frontera pueden cambiar a las demás
            for j in np.where(bs["delta"] > 1 - 1e-9)[0]:
                keep = np.arange(n) != j
                dj, _ = dea.eficiencia(X[keep], Y[keep])
                cambio = dj - bs["delta"][keep]
                rho = pd.Series(bs["delta"][keep]).corr(pd.Series(dj), method="spearman")
                k = int(np.argmax(cambio))
                loo.append(dict(modelo=modelo, anio=a, sale=d.pte_nombre[j],
                                cambio_medio=cambio.mean(), cambio_max=cambio.max(),
                                universidad_cambio_max=d.pte_nombre[keep].iloc[k],
                                n_cambian_mas_5_puntos=int((cambio > 0.05).sum()),
                                spearman_ranking=rho))
            r = pd.DataFrame([x for x in loo if x["modelo"] == modelo and x["anio"] == a])
            for x in r.itertuples():
                log(f"  sin {x.sale}: cambio medio {x.cambio_medio:+.3f}, máximo {x.cambio_max:+.3f} "
                    f"({x.universidad_cambio_max}), {x.n_cambian_mas_5_puntos} suben > 5 puntos, Spearman {x.spearman_ranking:.3f}")

            # --- sensibilidad: puntaje sin los estudiantes con 0 en Escrita
            if modelo == "principal":
                Yb = d[["mat_total_prom", "grad_total", "global_b"]].to_numpy(float)
                db, _ = dea.eficiencia(X, Yb)
                rho = pd.Series(bs["delta"]).corr(pd.Series(db), method="spearman")
                sens.append(dict(anio=a, variante="global_b en vez de global_c",
                                 eficiencia_media=db.mean(), cambio_medio=(db - bs["delta"]).mean(),
                                 cambio_max_abs=np.abs(db - bs["delta"]).max(), spearman_ranking=rho))
                log(f"  sensibilidad global_b: cambio medio {(db - bs['delta']).mean():+.4f}, "
                    f"máximo absoluto {np.abs(db - bs['delta']).max():.4f}, Spearman {rho:.3f}")

    out = Path("resultados")
    ef = pd.DataFrame(filas)
    num = ef.select_dtypes("number").columns.drop("anio")
    ef[num] = ef[num].round(4)
    ef.to_csv(out / "oe3_eficiencia.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(loo).round(4).to_csv(out / "oe3_deja_uno_fuera.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(sens).round(4).to_csv(out / "oe3_sensibilidad.csv", index=False, encoding="utf-8-sig")
    log("\nGuardado: resultados/oe3_eficiencia.csv, oe3_deja_uno_fuera.csv, oe3_sensibilidad.csv")

    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"oe3_dea_bootstrap_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
