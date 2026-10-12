"""
oe3_cobertura_sin_unad.py — OE3, modelo de cobertura SIN la UNAD.

Por qué: en el análisis "deja uno fuera" (resultados/oe3_deja_uno_fuera.csv), sacar a la UNAD del
modelo de cobertura sube más de 5 puntos la eficiencia de 25 de 32 universidades en 2023 y de 29 de
32 en 2024. La UNAD tiene el 100 % de su matrícula a distancia o virtual (SNIES, columna MODALIDAD)
y fija una frontera de matrícula y graduados por peso que ninguna otra alcanza. Este modelo compara
a las 32 restantes entre sí, con la misma especificación (DEA BCC orientado al producto + bootstrap
de Simar y Wilson, 1998). Ojo: las 32 no son todas presenciales; varias tienen una parte grande de
su matrícula a distancia (ver resultados/caracteristicas_universidades.csv).

Entrada: resultados/base_integrada_2023_2024.csv, resultados/oe3_eficiencia.csv (para comparar)
Salida:  resultados/oe3_cobertura_sin_unad.csv (mismas columnas que oe3_eficiencia.csv)
Evidencia: docs/gobernanza/evidencias/oe3_cobertura_sin_unad_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio; ≈ 4 min con B = 2000):
    python scripts/oe3_cobertura_sin_unad.py
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dea  # noqa: E402

UNAD = "225709"
PRODS = ["mat_total_prom", "grad_total"]
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--semilla", type=int, default=20261011)
    args = ap.parse_args()

    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    base = base[base.incluida_dea & (base.pte_codigo != UNAD)]
    con = pd.read_csv("resultados/oe3_eficiencia.csv", dtype={"pte_codigo": str})
    con = con[con.modelo == "cobertura"]
    log(f"##### OE3 — modelo de cobertura sin la UNAD — {datetime.now():%Y-%m-%d %H:%M} #####")
    log(f"B = {args.B} | semilla = {args.semilla} | universidades por año: {base.groupby('anio').size().to_dict()}")

    filas = []
    for a in sorted(base.anio.unique()):
        d = base[base.anio == a].reset_index(drop=True)
        X, Y = d[["obligacion_mm"]].to_numpy(float), d[PRODS].to_numpy(float)
        bs = dea.bootstrap_simar_wilson(X, Y, B=args.B, semilla=args.semilla)
        for o in range(len(d)):
            meta, _, _, lam = dea.metas(X[o], Y[o], X, Y, 1 / bs["delta"][o])
            pares = "; ".join(f"{d.pte_nombre[j]} ({lam[j]:.2f})"
                              for j in np.argsort(-lam) if lam[j] > 1e-6 and j != o)
            fila = dict(modelo="cobertura_sin_unad", anio=a, pte_codigo=d.pte_codigo[o], pte_nombre=d.pte_nombre[o],
                        eficiencia=bs["delta"][o], eficiencia_corregida=bs["delta_corregida"][o],
                        ic95_inf=bs["ic_inf"][o], ic95_sup=bs["ic_sup"][o], sesgo_phi=bs["sesgo_phi"][o],
                        en_frontera=bs["delta"][o] > 1 - 1e-9, pares=pares)
            for k, p in enumerate(PRODS):
                fila[f"{p}_actual"], fila[f"{p}_meta"] = Y[o, k], meta[k]
            filas.append(fila)
        ef = pd.DataFrame([f for f in filas if f["anio"] == a])
        c = con[con.anio == a].set_index("pte_codigo").loc[ef.pte_codigo]
        rho = pd.Series(ef.eficiencia.to_numpy()).corr(pd.Series(c.eficiencia.to_numpy()), method="spearman")
        log(f"\n=== {a} (n = {len(d)}) | h = {bs['h']:.4f}")
        log(f"  eficiencia media {ef.eficiencia.mean():.3f} (corregida {ef.eficiencia_corregida.mean():.3f}); "
            f"con la UNAD era {c.eficiencia.mean():.3f} ({c.eficiencia_corregida.mean():.3f})")
        log("  frontera: " + ", ".join(ef.loc[ef.en_frontera, "pte_nombre"]))
        log(f"  Spearman con el modelo de cobertura con UNAD: {rho:.3f}")
        peor = ef.loc[ef.eficiencia_corregida.idxmin()]
        log(f"  menor eficiencia corregida: {peor.pte_nombre} {peor.eficiencia_corregida:.3f} "
            f"[{peor.ic95_inf:.3f}; {peor.ic95_sup:.3f}]")

    out = pd.DataFrame(filas)
    num = out.select_dtypes("number").columns.drop("anio")
    out[num] = out[num].round(4)
    out.to_csv("resultados/oe3_cobertura_sin_unad.csv", index=False, encoding="utf-8-sig")
    log("\nGuardado: resultados/oe3_cobertura_sin_unad.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"oe3_cobertura_sin_unad_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
