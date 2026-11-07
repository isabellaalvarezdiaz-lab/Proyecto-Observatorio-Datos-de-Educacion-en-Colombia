"""
riesgo_stress.py — Stress testing del presupuesto sobre el DEA (OE3), 2024.

Pregunta: ¿qué les pasa a la eficiencia y al orden de las universidades si el presupuesto de la
Nación cambia, o si se le suman recursos que hoy no están en el insumo? Responde con escenarios a
la limitación principal del informe (el insumo no es todo el presupuesto, sección 8) y a la
recomendación de no usar el ordenamiento para recortar (sección 10).

Método
  Para cada escenario se modifica el insumo (obligación de la Nación, en miles de millones) y se
  vuelve a estimar el DEA BCC orientado al producto con las funciones de dea.py, en los tres modelos
  del OE3 (principal, cobertura y cobertura sin la UNAD). Los productos no cambian: el escenario
  pregunta cómo se vería la eficiencia con ese presupuesto y la misma producción.
  Se usa la eficiencia DEA estimada (δ = 1/φ), no la corregida por bootstrap: el bootstrap tarda
  unos 10 minutos por escenario y corrige el nivel, no la comparación entre escenarios. Como
  comprobación, el escenario base debe reproducir exactamente la columna "eficiencia" de
  resultados/oe3_eficiencia.csv y oe3_cobertura_sin_unad.csv.

Escenarios (2024)
  E0  base                         el insumo actual.
  E1  recorte uniforme del 10 %    a todas las universidades.
  E2  recorte uniforme del 20 %    a todas. E1 y E2 son una comprobación: el DEA mide eficiencia
                                   RELATIVA, así que un cambio igual para todas no cambia ninguna
                                   eficiencia (las restricciones del insumo son homogéneas).
  E3  recorte del 20 % a las universidades del orden nacional.
  E4  recorte del 20 % a las universidades del orden territorial.
      El orden sale de Saber Pro (caracteristicas_universidades.py). La U. del Trópico Americano no
      tiene orden asignado (Saber Pro la registra como no oficial), así que en E3 y E4 no se recorta.
  E5  recorte del 10 % a las 8 menos eficientes de cada modelo (cuartil inferior). Muestra el efecto
      mecánico de recortar según el ordenamiento: con menos insumo y la misma producción, la
      eficiencia sube sin que la universidad produzca más.
  E6  gratuidad 2024 sumada al insumo, repartida según la matrícula de pregrado.
  E7  gratuidad 2024 sumada al insumo, repartida según la matrícula de pregrado × % de evaluados en
      estratos 1 y 2 (aproximación a los beneficiarios: la política cubre sobre todo estratos 1 a 3).
      E6 y E7 son una cota superior: la gratuidad también financia instituciones públicas que no son
      universidades, y el PTE no dice cuánto le tocó a cada una.
  El monto de la gratuidad se lee del PTE (Cuadro No. 7 a diciembre de 2024, rubro "POLÍTICA DE
  GRATUIDAD DE LA EDUCACIÓN SUPERIOR PÚBLICA", columna Obligación). Si el archivo no está, se puede
  pasar con --gratuidad-mm.

Medidas por escenario y modelo: eficiencia media, universidades en la frontera, Spearman con el
orden base, cambio máximo y número de universidades que cambian 5 puntos (0,05) o más.

Entradas: resultados/base_integrada_2023_2024.csv, resultados/caracteristicas_universidades.csv,
          resultados/oe3_eficiencia.csv, resultados/oe3_cobertura_sin_unad.csv,
          data/raw/pte/2024/*.xlsx (solo para el monto de la gratuidad)
Salidas:  resultados/riesgo_stress_resumen.csv        una fila por modelo y escenario
          resultados/riesgo_stress_universidades.csv  una fila por modelo, escenario y universidad
Evidencia: docs/gobernanza/evidencias/riesgo_stress_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio; tarda menos de un minuto):
    python scripts/riesgo_stress.py
    python scripts/riesgo_stress.py --gratuidad-mm 2744.311

Requiere: pandas, numpy, scipy, openpyxl.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dea  # noqa: E402

ANIO = 2024
UNAD = 225709
INSUMO = "obligacion_mm"
MODELOS = {
    "principal": ["mat_total_prom", "grad_total", "global_c"],
    "cobertura": ["mat_total_prom", "grad_total"],
    "cobertura_sin_unad": ["mat_total_prom", "grad_total"],
}
RUBRO_GRATUIDAD = "POLÍTICA DE GRATUIDAD DE LA EDUCACIÓN SUPERIOR PÚBLICA"
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def gratuidad_del_pte(carpeta):
    """Obligación del rubro de gratuidad en el Cuadro No. 7 a diciembre de 2024, en miles de
    millones, con su procedencia (archivo y fila de Excel)."""
    for ruta in sorted(Path(carpeta).rglob("*.xlsx")):
        x = pd.ExcelFile(ruta)
        for hoja in x.sheet_names:
            d = pd.read_excel(x, sheet_name=hoja, header=None)
            titulo = " ".join(str(v) for v in d.iloc[:4, 0].tolist())
            if "Cuadro No. 7" not in titulo or f"Diciembre de {ANIO}" not in titulo:
                continue
            fila = d[d[0].astype(str).str.contains(RUBRO_GRATUIDAD, regex=False)]
            if len(fila) != 1:
                raise SystemExit(f"Se esperaba 1 fila de gratuidad en {ruta}, hay {len(fila)}")
            cab = d.iloc[4].astype(str).tolist()
            col = next(i for i, c in enumerate(cab) if c.strip().startswith("Obligaci"))
            valor = float(fila.iloc[0, col]) / 1e9
            return valor, f"{ruta.as_posix()} | hoja {hoja} | fila {fila.index[0] + 1}"
    return None, None


def estimar(df, productos):
    X = df[[INSUMO]].to_numpy(float)
    Y = df[productos].to_numpy(float)
    delta, _ = dea.eficiencia(X, Y, vrs=True)
    return delta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gratuidad-mm", type=float, default=None,
                    help="monto de la gratuidad 2024 en miles de millones (si no hay PTE)")
    ap.add_argument("--pte-dir", default=str(Path("data") / "raw" / "pte" / str(ANIO)))
    args = ap.parse_args()
    res = Path("resultados")

    log(f"##### Stress testing del presupuesto sobre el DEA, {ANIO} — {datetime.now():%Y-%m-%d %H:%M} #####")
    if args.gratuidad_mm is not None:
        grat, origen = args.gratuidad_mm, "argumento --gratuidad-mm"
    else:
        grat, origen = gratuidad_del_pte(args.pte_dir)
        if grat is None:
            raise SystemExit(f"No se encontró el Cuadro No. 7 de {ANIO} en {args.pte_dir}; "
                             "use --gratuidad-mm")
    log(f"Gratuidad {ANIO}: {grat:,.3f} mil millones ({origen})")

    base = pd.read_csv(res / "base_integrada_2023_2024.csv")
    base = base[base.incluida_dea & (base.anio == ANIO)].copy()
    car = pd.read_csv(res / "caracteristicas_universidades.csv")
    car = car[car.anio == ANIO][["pte_codigo", "orden", "pct_estrato_1_2"]]
    base = base.merge(car, on="pte_codigo", how="left").reset_index(drop=True)
    assert len(base) == 33 and base.pct_estrato_1_2.notna().all()
    sin_orden = base.pte_nombre[base.orden.isna()].tolist()
    log(f"Universidades: {len(base)} | orden nacional {int((base.orden == 'nacional').sum())}, "
        f"territorial {int((base.orden == 'territorial').sum())}, sin orden {len(sin_orden)} "
        f"{sin_orden} | insumo total {base[INSUMO].sum():,.1f} mil millones")
    if sin_orden:
        log("  Sin orden: Saber Pro no la registra como oficial nacional ni territorial; en E3 y E4 "
            "no se le aplica recorte.")

    ref = pd.concat([pd.read_csv(res / "oe3_eficiencia.csv"), pd.read_csv(res / "oe3_cobertura_sin_unad.csv")])
    ref = ref[ref.anio == ANIO]

    pesos_e6 = base.mat_pregrado_prom / base.mat_pregrado_prom.sum()
    benef = base.mat_pregrado_prom * base.pct_estrato_1_2 / 100
    pesos_e7 = benef / benef.sum()

    filas, resumen = [], []
    for modelo, productos in MODELOS.items():
        df = base[base.pte_codigo != UNAD].reset_index(drop=True) if modelo == "cobertura_sin_unad" \
            else base.copy()
        d0 = estimar(df, productos)
        r = ref[ref.modelo == modelo].set_index("pte_codigo").loc[df.pte_codigo, "eficiencia"].to_numpy()
        dif = np.abs(np.round(d0, 4) - r).max()
        log(f"\n=== Modelo {modelo} ({len(df)} universidades) ===")
        log(f"  comprobación: el escenario base reproduce oe3 (diferencia máxima {dif:.5f})")
        assert dif <= 1e-4, f"el escenario base no reproduce los resultados de {modelo}"

        bajas = np.argsort(d0)[:8]
        w6 = pesos_e6.loc[df.index] if modelo != "cobertura_sin_unad" else \
            pesos_e6[base.pte_codigo != UNAD].reset_index(drop=True)
        w7 = pesos_e7.loc[df.index] if modelo != "cobertura_sin_unad" else \
            pesos_e7[base.pte_codigo != UNAD].reset_index(drop=True)
        x0 = df[INSUMO].to_numpy(float)
        nac = (df.orden == "nacional").to_numpy()
        ter = (df.orden == "territorial").to_numpy()
        e5 = np.ones(len(df))
        e5[bajas] = 0.9
        escenarios = {
            "E0 base": x0,
            "E1 recorte uniforme 10 %": x0 * 0.9,
            "E2 recorte uniforme 20 %": x0 * 0.8,
            "E3 recorte 20 % orden nacional": np.where(nac, x0 * 0.8, x0),
            "E4 recorte 20 % orden territorial": np.where(ter, x0 * 0.8, x0),
            "E5 recorte 10 % a las 8 menos eficientes": x0 * e5,
            "E6 + gratuidad por matrícula de pregrado": x0 + grat * np.asarray(w6),
            "E7 + gratuidad por pregrado × % estratos 1 y 2": x0 + grat * np.asarray(w7),
        }
        for nombre, x in escenarios.items():
            dfe = df.copy()
            dfe[INSUMO] = x
            d1 = estimar(dfe, productos)
            cambio = d1 - d0
            puesto0 = pd.Series(d0).round(6).rank(ascending=False, method="min").astype(int)
            puesto1 = pd.Series(d1).round(6).rank(ascending=False, method="min").astype(int)
            front = df.pte_nombre[np.round(d1, 6) >= 1].tolist()
            i_max = int(np.argmax(np.abs(cambio)))
            resumen.append(dict(
                modelo=modelo, escenario=nombre, n=len(df), insumo_total_mm=round(x.sum(), 1),
                eficiencia_media=round(d1.mean(), 4), cambio_media=round(d1.mean() - d0.mean(), 4),
                n_frontera=len(front), frontera="; ".join(front),
                spearman_con_base=round(dea.spearman(d0, d1), 4),
                cambio_max=round(cambio[i_max], 4),
                universidad_cambio_max=df.pte_nombre[i_max] if abs(cambio[i_max]) > 1e-9 else "ninguna",
                n_cambian_5_puntos=int((np.abs(cambio) >= 0.05).sum()),
                n_cambian_puesto_5=int((np.abs(puesto1 - puesto0) >= 5).sum())))
            for i in range(len(df)):
                filas.append(dict(modelo=modelo, escenario=nombre, pte_codigo=int(df.pte_codigo[i]),
                                  pte_nombre=df.pte_nombre[i], orden=df.orden[i],
                                  insumo_base_mm=round(x0[i], 3), insumo_escenario_mm=round(x[i], 3),
                                  eficiencia_base=round(d0[i], 4), eficiencia_escenario=round(d1[i], 4),
                                  cambio=round(cambio[i], 4), puesto_base=int(puesto0[i]),
                                  puesto_escenario=int(puesto1[i])))
            s = resumen[-1]
            log(f"  {nombre:48s} media {s['eficiencia_media']:.3f} ({s['cambio_media']:+.3f}) | "
                f"frontera {s['n_frontera']} | Spearman {s['spearman_con_base']:.3f} | "
                f"Δ5pts {s['n_cambian_5_puntos']:2d} | máx {s['cambio_max']:+.3f} "
                f"({s['universidad_cambio_max'][:30]})")
        for nombre in ("E1 recorte uniforme 10 %", "E2 recorte uniforme 20 %"):
            s = next(r for r in resumen if r["modelo"] == modelo and r["escenario"] == nombre)
            ok = abs(s["cambio_max"]) < 1e-6
            log(f"  comprobación de invariancia ({nombre[:2]}): {'sí, ninguna eficiencia cambia' if ok else 'NO'}")
            assert ok

    resumen = pd.DataFrame(resumen)
    filas = pd.DataFrame(filas)
    resumen.to_csv(res / "riesgo_stress_resumen.csv", index=False, encoding="utf-8-sig")
    filas.to_csv(res / "riesgo_stress_universidades.csv", index=False, encoding="utf-8-sig")

    log("\n=== Universidades que más cambian con la gratuidad (E6, modelo principal) ===")
    t = filas[(filas.modelo == "principal") & filas.escenario.str.startswith("E6")]
    for _, r in t.reindex(t.cambio.abs().sort_values(ascending=False).index).head(6).iterrows():
        log(f"  {r.pte_nombre[:48]:48s} {r.eficiencia_base:.3f} → {r.eficiencia_escenario:.3f} "
            f"(puesto {r.puesto_base} → {r.puesto_escenario})")
    log("\nGuardados: resultados/riesgo_stress_resumen.csv y riesgo_stress_universidades.csv")

    carpeta = Path("docs") / "gobernanza" / "evidencias"
    carpeta.mkdir(parents=True, exist_ok=True)
    ev = carpeta / f"riesgo_stress_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"\nEvidencia guardada en {ev}")


if __name__ == "__main__":
    main()
