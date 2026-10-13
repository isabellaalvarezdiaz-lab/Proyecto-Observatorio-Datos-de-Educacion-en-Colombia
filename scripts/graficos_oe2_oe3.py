"""
graficos_oe2_oe3.py — Figuras para el informe a partir de resultados/oe3_eficiencia.csv,
resultados/oe3_cobertura_sin_unad.csv, resultados/oe2_malmquist.csv y resultados/oe3_segunda_etapa.csv.
Guarda PNG en resultados/figuras/.

  fig1_eficiencia_principal_<año>.png   eficiencia corregida con intervalo del 95 % (modelo principal)
  fig2_eficiencia_cobertura_<año>.png   ídem, modelo de cobertura
  fig3_malmquist_<modelo>.png           índice de Malmquist 2023→2024 (versión real) y su descomposición
  fig4_eficiencia_cobertura_sin_unad_<año>.png   ídem fig2, sin la UNAD (32 universidades)
  fig5_segunda_etapa.png                 asociación de cada característica (institucional y socioeconómica)
                                         con la eficiencia corregida

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
    titulo = {"principal": "matrícula, graduados y puntaje Saber Pro", "cobertura": "matrícula y graduados",
              "cobertura_sin_unad": "matrícula y graduados, sin la UNAD"}[modelo]
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


def segunda_etapa(se, archivo):
    modelos = [("principal", "Principal\n(matrícula, graduados, puntaje)"),
               ("cobertura", "Cobertura\n(con la UNAD)"), ("cobertura_sin_unad", "Cobertura\n(sin la UNAD)")]
    orden = se[se.modelo == "principal"].drop_duplicates("variable")
    fam = orden.familia if "familia" in orden else pd.Series("institucional", index=orden.index)
    inst = orden[fam == "institucional"]
    orden = pd.concat([inst[inst.tipo == "continua"], inst[inst.tipo == "binaria"], orden[fam != "institucional"]])
    n_socio = int((fam != "institucional").sum())
    etiquetas = []
    for r in orden.itertuples():
        e = r.etiqueta
        if r.tipo == "binaria":
            e += f" ({r.grupo_a.split(' (')[0]} vs {r.grupo_b.split(' (')[0]})"
        etiquetas.append(e)
    pos = {v: i for i, v in enumerate(orden.variable[::-1])}
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 5.6 + 0.4 * n_socio), sharey=True)
    for ax, (m, t) in zip(axes, modelos):
        ax.axvline(0, color=TINTA2, lw=1, zorder=1)
        if n_socio:   # separa la familia socioeconómica (Holm propio) de la institucional
            ax.axhline(n_socio - 0.5, color=GRIS, lw=0.8, ls=(0, (3, 3)), zorder=1)
        for anio, col, dy in ((2023, GRIS, 0.15), (2024, AZUL, -0.15)):
            d = se[(se.modelo == m) & (se.anio == anio)]
            for r in d.itertuples():
                y = pos[r.variable] + dy
                if r.mecanica:
                    ax.scatter(r.efecto, y, s=30, marker="x", color=col, lw=1.3, zorder=3)
                else:
                    sig = r.p_holm < 0.05
                    ax.scatter(r.efecto, y, s=38, color=col if sig else SUPERFICIE, edgecolor=col, lw=1.5, zorder=3)
        ax.set_title(t, fontsize=9, color=TINTA, loc="left")
        ax.set_xlim(-1.05, 1.05)
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.grid(axis="x", color="#e6e5e0", lw=0.8)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="y", length=0)
    nlab = [etiquetas[::-1][i] for i in range(len(etiquetas))]
    axes[0].set_yticks(range(len(nlab)), nlab)
    axes[1].set_xlabel("Asociación con la eficiencia corregida (rho de Spearman; en las binarias, "
                       "correlación biserial de rangos)")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=GRIS, ms=6, label="2023"),
         Line2D([], [], marker="o", ls="", color=AZUL, ms=6, label="2024"),
         Line2D([], [], marker="o", ls="", color=TINTA2, ms=6, label="relleno: p Holm < 0,05 (Holm por familia)"),
         Line2D([], [], marker="o", ls="", mfc=SUPERFICIE, mec=TINTA2, ms=6, label="vacío: no significativo"),
         Line2D([], [], marker="x", ls="", color=TINTA2, ms=6, label="asociación mecánica (no es hallazgo)")]
    fig.suptitle("Segunda etapa: ¿qué se asocia con la eficiencia? (análisis exploratorio)",
                 x=0.01, ha="left", fontsize=10, color=TINTA)
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.01, 0.96), ncol=5, frameon=False, fontsize=8)
    if n_socio:
        fig.text(0.01, 0.01, "Debajo de la línea punteada: perfil socioeconómico de los evaluados en Saber Pro "
                 "(familia aparte, con su propio ajuste de Holm).", fontsize=7.5, color=TINTA2)
    fig.tight_layout(rect=(0, 0.025 if n_socio else 0, 1, 0.94))
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
    su = Path("resultados/oe3_cobertura_sin_unad.csv")
    if su.exists():
        su = pd.read_csv(su)
        for a in sorted(su.anio.unique()):
            eficiencia(su, "cobertura_sin_unad", a, f"fig4_eficiencia_cobertura_sin_unad_{a}.png")
    se = Path("resultados/oe3_segunda_etapa.csv")
    if se.exists():
        segunda_etapa(pd.read_csv(se), "fig5_segunda_etapa.png")
    print("Figuras guardadas en", OUT.as_posix(), ":", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
