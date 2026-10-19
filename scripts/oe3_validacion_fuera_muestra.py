"""
oe3_validacion_fuera_muestra.py — OE3. ¿El modelo sirve para universidades que no usó?

Pedido del docente: dejar una parte de los datos fuera del modelo para comprobar que funciona con
datos que no tocó. En el DEA no hay una variable que predecir; lo que se puede comprobar es si la
evaluación de una universidad cambia cuando la frontera se estima SIN ella y sin otras.

Procedimiento, para cada modelo (principal, cobertura, cobertura sin la UNAD) y año:
  1. Se sortean k ≈ 20 % de las universidades (7 de 33; 6 de 32), que quedan reservadas.
  2. La frontera se estima solo con las demás (≈ 80 %).
  3. Cada reservada se evalúa contra esa frontera (DEA BCC orientado al producto, como en el OE3).
     Puede quedar por encima de la frontera de entrenamiento (eficiencia > 1). Si su presupuesto
     es menor que el de todas las de entrenamiento, ninguna combinación de ellas usa tan poco y
     no se puede evaluar con rendimientos variables: se cuenta como "fuera del soporte".
  4. Se repite R veces (por defecto 1.000) con semilla fija. Con 33 universidades, los modelos
     principal y de cobertura usan los mismos sorteos.
Se compara la eficiencia fuera de muestra con la del modelo completo (columna eficiencia de
oe3_eficiencia.csv y oe3_cobertura_sin_unad.csv). Sacar universidades solo puede bajar la
frontera, así que la eficiencia fuera de muestra nunca es menor; la pregunta es cuánto sube y si
el orden se mantiene. Se compara la eficiencia original: repetir el bootstrap en cada sorteo
costaría 2.000 réplicas por sorteo.

Indicadores (resultados/oe3_validacion_resumen.csv, una fila por modelo y año):
  interior_*        evaluaciones de universidades que NO están en la frontera del modelo completo:
                    % sin ningún cambio (diferencia < 10^-6), cambio medio, percentil 95 del cambio
                    y % que fuera de muestra parecen eficientes (eficiencia ≥ 1).
  spearman_mediana, spearman_p05   correlación de Spearman, en cada sorteo, entre la eficiencia
                    fuera de muestra y la del modelo completo de las reservadas (mediana y
                    percentil 5 entre los sorteos).
  spearman_agregado Spearman entre la mediana de la eficiencia fuera de muestra de cada universidad
                    (sobre todos los sorteos en que quedó reservada) y su eficiencia completa.
Detalle por universidad: resultados/oe3_validacion_universidades.csv.
Evidencia: docs/gobernanza/evidencias/oe3_validacion_fuera_muestra_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio; ≈ 2 min):
    python scripts/oe3_validacion_fuera_muestra.py
    python scripts/oe3_validacion_fuera_muestra.py --R 200      (prueba rápida)
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
MODELOS = {"principal": ["mat_total_prom", "grad_total", "global_c"],
           "cobertura": ["mat_total_prom", "grad_total"],
           "cobertura_sin_unad": ["mat_total_prom", "grad_total"]}
SIN_CAMBIO = 1e-6
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def datos_modelo(base, modelo, anio):
    d = base[base.anio == anio]
    if modelo == "cobertura_sin_unad":
        d = d[d.pte_codigo != UNAD]
    d = d.reset_index(drop=True)
    return d, d[["obligacion_mm"]].to_numpy(float), d[MODELOS[modelo]].to_numpy(float)


def evaluar_fuera(X, Y, reservadas):
    """Eficiencia de cada universidad reservada contra la frontera de las demás (NaN = fuera del soporte)."""
    entreno = np.setdiff1d(np.arange(len(X)), reservadas)
    out = np.full(len(reservadas), np.nan)
    for i, o in enumerate(reservadas):
        if X[o, 0] < X[entreno, 0].min():
            continue
        phi, _ = dea.phi_envolvente(X[o], Y[o], X[entreno], Y[entreno])
        out[i] = 1 / phi
    return out


def resumir(modelo, anio, d, completa, parts, fuera, semilla):
    """Indicadores del modelo y año, y detalle por universidad, a partir de todas las evaluaciones."""
    n, k = len(d), parts.shape[1]
    ev = pd.DataFrame({"o": parts.ravel(), "fuera": fuera.ravel()})
    ev["completa"] = completa[ev.o]
    ev["frontera"] = ev.completa > 1 - 1e-9
    ev["cambio"] = ev.fuera - ev.completa
    ok = ev.fuera.notna()
    inte = ev[ok & ~ev.frontera]
    rhos = []
    for r in range(parts.shape[0]):
        f, c = fuera[r], completa[parts[r]]
        m = ~np.isnan(f)
        if m.sum() >= 3 and np.ptp(np.round(c[m], 6)) > 0:
            rhos.append(dea.spearman(f[m], c[m]))
    rhos = np.array(rhos)
    med = ev[ok].groupby("o").fuera.median()
    fila = dict(modelo=modelo, anio=anio, n=n, reservadas=k, repeticiones=parts.shape[0], semilla=semilla,
                evaluaciones=len(ev), fuera_soporte=int((~ok).sum()),
                interior_evaluaciones=len(inte),
                interior_sin_cambio_pct=100 * (inte.cambio.abs() < SIN_CAMBIO).mean(),
                interior_cambio_medio=inte.cambio.mean(), interior_cambio_p95=inte.cambio.quantile(0.95),
                interior_parecen_eficientes_pct=100 * (inte.fuera >= 1 - SIN_CAMBIO).mean(),
                frontera_evaluaciones=int((ok & ev.frontera).sum()),
                spearman_mediana=np.nanmedian(rhos), spearman_p05=np.nanquantile(rhos, 0.05),
                spearman_agregado=dea.spearman(med.to_numpy(), completa[med.index]),
                universidades_agregado=len(med))
    det = []
    for o in range(n):
        e = ev[ev.o == o]
        eo = e[e.fuera.notna()]
        det.append(dict(modelo=modelo, anio=anio, pte_codigo=d.pte_codigo[o], pte_nombre=d.pte_nombre[o],
                        eficiencia=completa[o], en_frontera=bool(completa[o] > 1 - 1e-9),
                        veces_reservada=len(e), veces_fuera_soporte=int(e.fuera.isna().sum()),
                        eficiencia_fuera_mediana=eo.fuera.median() if len(eo) else np.nan,
                        cambio_medio=eo.cambio.mean() if len(eo) else np.nan,
                        sin_cambio_pct=100 * (eo.cambio.abs() < SIN_CAMBIO).mean() if len(eo) else np.nan,
                        parece_eficiente_pct=(100 * (eo.fuera >= 1 - SIN_CAMBIO).mean()
                                              if len(eo) and completa[o] <= 1 - 1e-9 else np.nan)))
    return fila, pd.DataFrame(det)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--R", type=int, default=1000, help="sorteos por modelo y año")
    ap.add_argument("--semilla", type=int, default=20261013)
    ap.add_argument("--fraccion", type=float, default=0.2, help="fracción reservada en cada sorteo")
    args = ap.parse_args()

    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype={"pte_codigo": str})
    base = base[base.incluida_dea]
    previas = pd.concat([pd.read_csv("resultados/oe3_eficiencia.csv", dtype={"pte_codigo": str}),
                         pd.read_csv("resultados/oe3_cobertura_sin_unad.csv", dtype={"pte_codigo": str})])
    log(f"##### OE3 — validación fuera de muestra — {datetime.now():%Y-%m-%d %H:%M} #####")
    log(f"sorteos R = {args.R} | semilla = {args.semilla} | fracción reservada = {args.fraccion}")

    resumen, detalle = [], []
    for modelo in MODELOS:
        for a in sorted(base.anio.unique()):
            d, X, Y = datos_modelo(base, modelo, a)
            n = len(d)
            k = int(round(args.fraccion * n))
            completa, _ = dea.eficiencia(X, Y)
            ant = previas[(previas.modelo == modelo) & (previas.anio == a)].set_index("pte_codigo").loc[d.pte_codigo]
            dif = np.abs(ant.eficiencia.to_numpy() - completa).max()
            if dif > 5e-5:
                raise SystemExit(f"La eficiencia completa de {modelo} {a} no coincide con resultados/ ({dif:.1e}).")
            parts = dea.particiones(n, k, args.R, args.semilla)
            fuera = np.vstack([evaluar_fuera(X, Y, p) for p in parts])
            fila, det = resumir(modelo, a, d, completa, parts, fuera, args.semilla)
            resumen.append(fila)
            detalle.append(det)
            log(f"\n=== {modelo} · {a} (n = {n}; se reservan {k} en cada sorteo) ===")
            log(f"  evaluaciones: {fila['evaluaciones']:,}; fuera del soporte: {fila['fuera_soporte']} "
                f"({', '.join(det.loc[det.veces_fuera_soporte > 0, 'pte_nombre'])})")
            log(f"  universidades que no están en la frontera ({fila['interior_evaluaciones']:,} evaluaciones): "
                f"sin ningún cambio {fila['interior_sin_cambio_pct']:.1f} %; cambio medio {fila['interior_cambio_medio']:.4f}; "
                f"percentil 95 {fila['interior_cambio_p95']:.4f}; parecen eficientes {fila['interior_parecen_eficientes_pct']:.1f} %")
            log(f"  Spearman por sorteo: mediana {fila['spearman_mediana']:.3f}, percentil 5 {fila['spearman_p05']:.3f} | "
                f"agregado ({fila['universidades_agregado']} universidades): {fila['spearman_agregado']:.3f}")
            top = det[~det.en_frontera].nlargest(3, "cambio_medio")
            log("  más sensibles a quién queda en la frontera: " + "; ".join(
                f"{r.pte_nombre} (cambio medio {r.cambio_medio:.3f})" for r in top.itertuples()))

    out = Path("resultados")
    res = pd.DataFrame(resumen)
    num = res.select_dtypes("number").columns.drop(["anio", "n", "reservadas", "repeticiones", "semilla", "evaluaciones",
                                                     "fuera_soporte", "interior_evaluaciones", "frontera_evaluaciones",
                                                     "universidades_agregado"])
    res[num] = res[num].round(4)
    res.to_csv(out / "oe3_validacion_resumen.csv", index=False, encoding="utf-8-sig")
    det = pd.concat(detalle, ignore_index=True)
    numd = ["eficiencia", "eficiencia_fuera_mediana", "cambio_medio", "sin_cambio_pct", "parece_eficiente_pct"]
    det[numd] = det[numd].round(4)
    det.to_csv(out / "oe3_validacion_universidades.csv", index=False, encoding="utf-8-sig")
    log("\nGuardado: resultados/oe3_validacion_resumen.csv, oe3_validacion_universidades.csv")
    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"oe3_validacion_fuera_muestra_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"Evidencia: {ev.as_posix()}")


if __name__ == "__main__":
    main()
