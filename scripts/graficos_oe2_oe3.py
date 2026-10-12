"""
graficos_oe2_oe3.py — Figuras para el informe a partir de resultados/oe3_eficiencia.csv y
resultados/oe2_malmquist.csv. Guarda PNG en resultados/figuras/.

  fig1_eficiencia_principal_<año>.png   eficiencia corregida con intervalo del 95 % (modelo principal)
  fig2_eficiencia_cobertura_<año>.png   ídem, modelo de cobertura
  fig3_malmquist_<modelo>.png           índice de Malmquist 2023→2024 (versión real) y su descomposición

Uso (desde la raíz del repositorio):
    python scripts/graficos_oe2_oe3.py
Requiere: matplotlib.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

AZUL, NARANJA, GRIS, TINTA, TINTA2 = "#2a78d6", "#eb6834", "#a3a29c", "#0b0b0b", "#52514e"
SUPERFICIE = "#fcfcfb"
OUT = Path("resultados") / "figuras"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": GRIS,
                     "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA,
                     "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE})


MINUSCULAS = {"de", "del", "la", "los", "y", "a"}
REEMPLAZOS = {"Nacional Abierta Y A Distancia Unad": "Nacional Abierta y a Distancia (UNAD)",
              "Pedagogica Y Tecnologica De Colombia": "Pedagógica y Tecnológica (UPTC)",
              "Tecnologica Del Choco Diego Luis Cordoba": "Tecnológica del Chocó",
              "Distrital Francisco Jose De Caldas": "Distrital Francisco José de Caldas",
              "Francisco De Paula Santander Seccional Ocaña": "Francisco de Paula Santander (Ocaña)",
              "Internacional Del Tropico Americano": "Internacional del Trópico Americano"}
TILDES = {"Pedagogica": "Pedagógica", "Tecnologica": "Tecnológica", "Atlantico": "Atlántico",
          "Cordoba": "Córdoba", "Quindio": "Quindío", "Pacifico": "Pacífico", "Narino": "Nariño"}


def nombre_corto(s):
    resto = s.replace("universidad ", "", 1)
    t = " ".join(w.capitalize() for w in resto.split())
    for a, b in REEMPLAZOS.items():
        t = t.replace(a, b)
    t = " ".join(w.lower() if w.lower() in MINUSCULAS else TILDES.get(w, w)
                 for i, w in enumerate(t.split()))
    return "U. " + t


def eficiencia(ef, modelo, anio, archivo):
    d = ef[(ef.modelo == modelo) & (ef.anio == anio)].sort_values("eficiencia_corregida")
    y = range(len(d))
    fig, ax = plt.subplots(figsize=(7.2, 7.6))
    ax.hlines(y, d.ic95_inf, d.ic95_sup, color=AZUL, lw=2, alpha=0.55, zorder=2)
    ax.scatter(d.eficiencia_corregida, y, s=34, color=AZUL, edgecolor=SUPERFICIE, lw=1.5, zorder=3,
               label="Eficiencia corregida por sesgo (bootstrap)")
    ax.scatter(d.eficiencia, y, s=26, marker="|", color=TINTA2, lw=1.4, zorder=3,
               label="Estimación DEA original")
    ax.set_yticks(list(y), [nombre_corto(n) for n in d.pte_nombre])
    ax.set_xlabel("Eficiencia (1 = frontera)")
    x0 = max(0.0, (d.ic95_inf.min() - 0.05) // 0.1 * 0.1)
    ax.set_xlim(x0, 1.02)
    ax.grid(axis="x", color="#e6e5e0", lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    titulo = {"principal": "matrícula, graduados y puntaje Saber Pro", "cobertura": "matrícula y graduados"}[modelo]
    fig.suptitle(f"Eficiencia DEA {anio} — productos: {titulo}", x=0.01, ha="left", fontsize=10, color=TINTA)
    fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.01, 0.97), ncol=2,
               frameon=False, fontsize=8)
    ax.set_xlabel("Eficiencia (1 = frontera) · barra: intervalo de confianza del 95 %")
    fig.tight_layout(rect=(0, 0, 1, 0.945))
    fig.savefig(OUT / archivo, dpi=200)
    plt.close(fig)


def malmquist(mq, modelo, archivo):
    d = mq[(mq.modelo == modelo) & (mq.version == "real")].sort_values("malmquist")
    y = range(len(d))
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 7.6), sharey=True)
    cols = [("malmquist", "Índice de Malmquist (M)"), ("cambio_eficiencia", "Cambio de eficiencia (EC)"),
            ("cambio_tecnologico", "Cambio tecnológico (TC)")]
    lo = min(d[c].min() for c, _ in cols) - 0.03
    hi = max(d[c].max() for c, _ in cols) + 0.03
    for ax, (c, t) in zip(axes, cols):
        ax.axvline(1, color=TINTA2, lw=1, zorder=1)
        ax.hlines(y, 1, d[c], color=AZUL, lw=2, alpha=0.45, zorder=2)
        ax.scatter(d[c], y, s=30, color=AZUL, edgecolor=SUPERFICIE, lw=1.5, zorder=3)
        ax.set_title(t, fontsize=9, color=TINTA, loc="left")
        ax.set_xlim(lo, hi)
        ax.grid(axis="x", color="#e6e5e0", lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(list(y), [nombre_corto(n) for n in d.pte_nombre])
    axes[1].set_xlabel("> 1 mejora · < 1 retroceso (2023→2024, insumo en pesos de 2023)")
    titulo = {"principal": "matrícula, graduados y puntaje", "cobertura": "matrícula y graduados"}[modelo]
    fig.suptitle(f"Cambio de productividad 2023→2024 — productos: {titulo}  (M = EC × TC)",
                 x=0.01, ha="left", fontsize=10, color=TINTA)
    fig.tight_layout()
    fig.savefig(OUT / archivo, dpi=200)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ef = pd.read_csv("resultados/oe3_eficiencia.csv")
    mq = pd.read_csv("resultados/oe2_malmquist.csv")
    for a in sorted(ef.anio.unique()):
        eficiencia(ef, "principal", a, f"fig1_eficiencia_principal_{a}.png")
        eficiencia(ef, "cobertura", a, f"fig2_eficiencia_cobertura_{a}.png")
    for m in ("principal", "cobertura"):
        malmquist(mq, m, f"fig3_malmquist_{m}.png")
    print("Figuras guardadas en", OUT.as_posix(), ":", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
