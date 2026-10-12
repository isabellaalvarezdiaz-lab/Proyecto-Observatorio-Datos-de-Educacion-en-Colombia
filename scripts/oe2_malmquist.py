"""
oe2_malmquist.py — OE2. Índice de productividad de Malmquist 2023→2024 por universidad pública,
orientado al producto, con rendimientos constantes (CRS), como recomiendan Vázquez Rojas y
Pérez-Esparrells (2016) para el Malmquist.

Distancias de Shephard orientadas al producto, D^s(x_t, y_t) = δ = 1/φ, de la universidad en el
año t evaluada contra la frontera CRS del año s (s, t ∈ {2023, 2024}):

  M  = sqrt[ (D^23(x24,y24) / D^23(x23,y23)) · (D^24(x24,y24) / D^24(x23,y23)) ]
  EC = D^24(x24,y24) / D^23(x23,y23)             cambio de eficiencia técnica ("catching up")
  TC = M / EC                                     cambio tecnológico ("shift frontier")

  M > 1 = progreso de productividad; M < 1 = retroceso de productividad (nunca "negativo").

Insumo deflactado: la obligación de 2024 se lleva a pesos de 2023 dividiéndola por 1,052,
la variación anual del IPC a diciembre de 2024 (5,20 %), según el DANE, Comunicado de prensa
IPC diciembre 2024, p. 1: https://www.dane.gov.co/files/operaciones/IPC/dic2024/cp-IPC-dic2024.pdf
Con un solo insumo y CRS, deflactar multiplica M y TC por el mismo factor (1,052) en todas las
universidades y no cambia EC ni el orden entre universidades; se reportan ambas versiones.

Entrada: resultados/base_integrada_2023_2024.csv (universidades con incluida_dea en los dos años)
Salida:  resultados/oe2_malmquist.csv
Evidencia: docs/gobernanza/evidencias/oe2_malmquist_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts/oe2_malmquist.py
"""
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dea  # noqa: E402

DEFLACTOR_2024 = 1.052
INSUMO = "obligacion_mm"
MODELOS = {
    "principal": ["mat_total_prom", "grad_total", "global_c"],
    "cobertura": ["mat_total_prom", "grad_total"],
}
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def distancias(X0, Y0, X1, Y1):
    """D^0(t0), D^0(t1), D^1(t0), D^1(t1) con CRS (D = δ = 1/φ)."""
    d00, _ = dea.eficiencia(X0, Y0, vrs=False)
    d11, _ = dea.eficiencia(X1, Y1, vrs=False)
    d01, _ = dea.eficiencia(X1, Y1, Xref=X0, Yref=Y0, vrs=False)   # 2024 contra frontera 2023
    d10, _ = dea.eficiencia(X0, Y0, Xref=X1, Yref=Y1, vrs=False)   # 2023 contra frontera 2024
    return d00, d01, d10, d11


def main():
    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    base = base[base.incluida_dea]
    ambos = base.groupby("pte_codigo").anio.nunique()
    base = base[base.pte_codigo.isin(ambos[ambos == 2].index)]
    a0 = base[base.anio == 2023].sort_values("pte_codigo").reset_index(drop=True)
    a1 = base[base.anio == 2024].sort_values("pte_codigo").reset_index(drop=True)
    assert (a0.pte_codigo.values == a1.pte_codigo.values).all()
    log(f"##### OE2 — Índice de Malmquist 2023→2024 (CRS, orientado al producto) — {datetime.now():%Y-%m-%d %H:%M} #####")
    log(f"Universidades con datos en los dos años: {len(a0)} | deflactor del insumo 2024: {DEFLACTOR_2024}")

    filas = []
    for modelo, prods in MODELOS.items():
        Y0, Y1 = a0[prods].to_numpy(float), a1[prods].to_numpy(float)
        for version, k in (("nominal", 1.0), ("real", DEFLACTOR_2024)):
            X0 = a0[[INSUMO]].to_numpy(float)
            X1 = a1[[INSUMO]].to_numpy(float) / k
            d00, d01, d10, d11 = distancias(X0, Y0, X1, Y1)
            M = np.sqrt((d01 / d00) * (d11 / d10))
            EC = d11 / d00
            TC = M / EC
            for i in range(len(a0)):
                filas.append(dict(modelo=modelo, version=version, pte_codigo=a0.pte_codigo[i],
                                  pte_nombre=a0.pte_nombre[i], malmquist=M[i], cambio_eficiencia=EC[i],
                                  cambio_tecnologico=TC[i], D23_23=d00[i], D23_24=d01[i],
                                  D24_23=d10[i], D24_24=d11[i]))
            gm = lambda v: float(np.exp(np.log(v).mean()))      # media geométrica
            log(f"\n=== {modelo} · {version} ===")
            log(f"  Malmquist (media geométrica) {gm(M):.4f} | cambio de eficiencia {gm(EC):.4f} | "
                f"cambio tecnológico {gm(TC):.4f}")
            log(f"  universidades con progreso (M > 1): {int((M > 1).sum())} | con retroceso (M < 1): {int((M < 1).sum())}")
            log(f"  control M = EC × TC: diferencia máxima {np.abs(M - EC * TC).max():.2e}")

    r = pd.DataFrame(filas)
    num = r.select_dtypes("number").columns
    r[num] = r[num].round(4)
    r.to_csv("resultados/oe2_malmquist.csv", index=False, encoding="utf-8-sig")
    # deflactar no cambia EC ni el orden: control
    for modelo in MODELOS:
        n_ = r[(r.modelo == modelo) & (r.version == "nominal")].set_index("pte_codigo")
        re = r[(r.modelo == modelo) & (r.version == "real")].set_index("pte_codigo")
        log(f"  [{modelo}] real/nominal de M: {(re.malmquist / n_.malmquist).min():.4f}–{(re.malmquist / n_.malmquist).max():.4f} | "
            f"EC igual: {np.allclose(re.cambio_eficiencia, n_.cambio_eficiencia, atol=1e-3)}")
    log("\nGuardado: resultados/oe2_malmquist.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"oe2_malmquist_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
