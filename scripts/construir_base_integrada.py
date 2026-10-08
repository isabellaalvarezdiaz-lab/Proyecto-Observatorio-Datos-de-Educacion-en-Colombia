"""
construir_base_integrada.py — Base para el DEA (OE2 y OE3). Parte de la tabla maestra (OE1),
toma las sedes de las universidades públicas del PTE, las suma por universidad y le une el
presupuesto del PTE. Una fila por universidad (entidad del PTE) y año.

Entradas:
  resultados/tabla_maestra_2023_2024.csv       <- construir_tabla_maestra.py
  resultados/pte_universidades_2023_2024.csv   <- extraer_pte_universidades.py

Reglas:
  - Matrícula y graduados: suma de las sedes de cada universidad (ya vienen por semestre
    desde la tabla maestra; la matrícula no suma los dos semestres).
  - Saber Pro: promedio de las sedes ponderado por evaluados (global_b, por evaluados sin cero
    en Escrita). Puntaje recomendado para el DEA: global_c. Error por usar promedios de sede
    redondeados a 2 decimales: < 0,005 puntos (verificado contra los microdatos).
  - Cifras del PTE en pesos corrientes de cada año.

Salida: resultados/base_integrada_2023_2024.csv  (ver docs/diccionario_base_integrada.md)

Uso (desde la raíz del repositorio):
    python scripts/construir_base_integrada.py
"""
from pathlib import Path

import pandas as pd


def main():
    pte = pd.read_csv("resultados/pte_universidades_2023_2024.csv", dtype={"pte_codigo": str})
    t = pd.read_csv("resultados/tabla_maestra_2023_2024.csv", dtype={"cod_institucion": str, "pte_codigo": str})
    t = t[t.pte_codigo.notna()].copy()
    anios = sorted(pte.anio.unique())

    suma = [c for c in t.columns if c.startswith(("mat_", "grad_"))]
    t["n_sin_cero"] = t.n_evaluados - t.n_ceros_escrita
    t["ga"] = t.global_a * t.n_evaluados
    t["gb"] = t.global_b * t.n_sin_cero
    t["gc"] = t.global_c * t.n_evaluados
    g = t.groupby(["pte_codigo", "anio"])
    u = g[suma].sum()
    u["n_sedes_snies"] = g.en_snies.sum()
    u["n_sedes_saber_pro"] = g.en_saber_pro.sum()
    ev = g[["n_evaluados", "n_ceros_escrita", "n_sin_cero", "ga", "gb", "gc"]].sum(min_count=1)
    u["n_evaluados"] = ev.n_evaluados
    u["n_ceros_escrita"] = ev.n_ceros_escrita
    u["pct_ceros_escrita"] = 100 * ev.n_ceros_escrita / ev.n_evaluados
    u["global_a"] = ev.ga / ev.n_evaluados
    u["global_b"] = ev.gb / ev.n_sin_cero
    u["global_c"] = ev.gc / ev.n_evaluados

    base = (pte.set_index(["pte_codigo", "anio"])
            .drop(columns=["archivo", "hoja", "fila_excel"])
            .join(u)
            .reset_index())
    for c in [c for c in suma if not c.endswith("_prom")] + ["n_sedes_snies", "n_sedes_saber_pro"]:
        base[c] = base[c].astype("int64")
    for c in ["n_evaluados", "n_ceros_escrita"]:
        base[c] = base[c].astype("Int64")
    for c in ["apropiacion", "compromiso", "obligacion", "pago", "art86_obligacion"]:
        base[c + "_mm"] = base[c] / 1e9
    base["incluida_dea"] = (base.n_evaluados.notna() & base.mat_total_prom.gt(0)
                            & base.grad_total.gt(0) & base.obligacion.gt(0))
    notas = {
        "225734": "Sin evaluados en Saber Pro en el periodo",
        "225733": "Saber Pro la rotula no oficial; SNIES la registra en el sector oficial",
        "225725": "En SNIES es seccional de UFPS (IES PADRE 1209); el PTE la financia aparte",
    }
    base["nota"] = base.pte_codigo.map(notas).fillna("")
    for c in ["pct_ceros_escrita", "global_a", "global_b", "global_c", "mat_pregrado_prom",
              "mat_posgrado_prom", "mat_total_prom"]:
        base[c] = base[c].round(2)
    base = base.sort_values(["pte_codigo", "anio"])
    salida = Path("resultados") / f"base_integrada_{min(anios)}_{max(anios)}.csv"
    base.to_csv(salida, index=False, encoding="utf-8-sig")

    # ---------- controles ----------
    n_ent = pte.pte_codigo.nunique()
    print(f"Filas: {len(base)} (esperado {n_ent * len(anios)}) | universidades: {base.pte_codigo.nunique()}")
    print(f"Incluidas en el DEA: {base[base.incluida_dea].pte_codigo.nunique()} universidades, "
          f"{int(base.incluida_dea.sum())} observaciones")
    print("Excluidas:", base.loc[~base.incluida_dea, ["pte_codigo", "anio", "pte_nombre"]]
          .to_dict("records") or "ninguna")
    for c in ["obligacion", "mat_total_prom", "grad_total", "n_evaluados", "global_c"]:
        print(f"  faltantes en {c:16s}: {int(base[c].isna().sum())}")
    print("Totales por año:")
    print(base.groupby("anio")[["obligacion_mm", "mat_total_prom", "grad_total", "n_evaluados"]]
          .sum().round(1).to_string())
    print("Isotonicidad — correlación de Spearman entre obligación y cada producto (universidades del DEA):")
    d = base[base.incluida_dea]
    for a in anios:
        x = d[d.anio == a]
        rho = {p: float(round(x.obligacion.corr(x[p], method="spearman"), 2))
               for p in ("mat_total_prom", "grad_total", "global_c")}
        print(f"  {a} (n={len(x)}): {rho}")
    print(f"Guardado: {salida.as_posix()}")


if __name__ == "__main__":
    main()
