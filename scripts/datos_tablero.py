"""
datos_tablero.py — Prepara los datos del tablero interactivo a partir de los resultados del proyecto.

No estima nada nuevo. Une los CSV de resultados/, conserva sus valores numéricos tal como están,
renombra algunas columnas y agrega a cada fila una llave `id` y el nombre corto de la universidad
(la misma función de las figuras; también en la lista de pares). Los promedios, puestos y medianas
que muestra el tablero los calcula el propio tablero, a la vista de quien lo consulte.

Entradas: resultados/oe3_eficiencia.csv, oe3_cobertura_sin_unad.csv, oe2_malmquist.csv,
          oe3_segunda_etapa.csv, caracteristicas_universidades.csv, base_integrada_2023_2024.csv
Salida:   resultados/tablero/universidades.json   (eficiencia, intervalos, pares y metas por modelo y año)
          resultados/tablero/caracteristicas.json (insumo, productos y perfil por universidad y año)
          resultados/tablero/malmquist.json       (índice y descomposición por modelo y versión)
          resultados/tablero/segunda_etapa.json   (asociaciones de la segunda etapa)
Evidencia: docs/gobernanza/evidencias/datos_tablero_AAAA-MM-DD_HHMM.txt

Uso (desde la raíz del repositorio):
    python scripts/datos_tablero.py
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from graficos_oe2_oe3 import nombre_corto

SALIDA = Path("resultados/tablero")
LOG = []


def log(t=""):
    print(t, flush=True)
    LOG.append(str(t))


def pares_cortos(texto):
    """'universidad x (0.60); universidad y (0.40)' -> 'U. X (0,60); U. Y (0,40)'."""
    if not isinstance(texto, str) or not texto:
        return None
    partes = []
    for p in texto.split("; "):
        nombre, peso = p.rsplit(" (", 1)
        partes.append(f"{nombre_corto(nombre)} ({peso.rstrip(')').replace('.', ',')})")
    return "; ".join(partes)


def limpio(df):
    """Filas como diccionarios, con None en lugar de NaN para que el JSON sea válido."""
    return [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in df.to_dict("records")]


def escribir(nombre, filas):
    ruta = SALIDA / nombre
    ruta.write_text(json.dumps(filas, ensure_ascii=False, indent=0), encoding="utf-8")
    log(f"  {ruta}: {len(filas)} filas, {ruta.stat().st_size:,} bytes")


def main():
    log(f"##### Datos del tablero — {datetime.now():%Y-%m-%d %H:%M} #####")
    SALIDA.mkdir(parents=True, exist_ok=True)
    cod = {"pte_codigo": str}

    # 1. eficiencia por modelo y año
    ef = pd.concat([pd.read_csv("resultados/oe3_eficiencia.csv", dtype=cod),
                    pd.read_csv("resultados/oe3_cobertura_sin_unad.csv", dtype=cod)], ignore_index=True)
    u = pd.DataFrame({
        "id": ef.modelo + "-" + ef.anio.astype(str) + "-" + ef.pte_codigo,
        "modelo": ef.modelo, "anio": ef.anio, "pte_codigo": ef.pte_codigo,
        "universidad": ef.pte_nombre.map(nombre_corto),
        "eficiencia": ef.eficiencia, "eficiencia_corregida": ef.eficiencia_corregida,
        "ic95_inf": ef.ic95_inf, "ic95_sup": ef.ic95_sup, "en_frontera": ef.en_frontera.astype(bool),
        "pares": ef.pares.map(pares_cortos),
        "matricula_actual": ef.mat_total_prom_actual, "matricula_meta": ef.mat_total_prom_meta,
        "graduados_actual": ef.grad_total_actual, "graduados_meta": ef.grad_total_meta,
        "puntaje_actual": ef.global_c_actual, "puntaje_meta": ef.global_c_meta})
    assert u.id.is_unique
    assert (u.ic95_inf <= u.eficiencia_corregida).all() and (u.eficiencia_corregida <= u.ic95_sup).all()
    log(f"\nEficiencia: {len(u)} filas")
    for (m, a), g in u.groupby(["modelo", "anio"]):
        log(f"  {m:20s} {a}: {len(g)} universidades, {int(g.en_frontera.sum())} en la frontera, "
            f"media corregida {g.eficiencia_corregida.mean():.4f}")

    # 2. insumo, productos y perfil (las 33 universidades del DEA)
    base = pd.read_csv("resultados/base_integrada_2023_2024.csv", dtype=cod)
    base = base[base.incluida_dea]
    car = pd.read_csv("resultados/caracteristicas_universidades.csv", dtype=cod)
    c = base[["pte_codigo", "anio", "pte_nombre", "obligacion_mm", "mat_total_prom", "grad_total", "global_c"]].merge(
        car[["pte_codigo", "anio", "departamento_domicilio", "orden", "acreditada_institucional",
             "pct_mat_prog_acreditados", "pct_mat_distancia_virtual", "pct_mat_posgrado",
             "pct_estrato_1_2", "pct_madre_hasta_secundaria", "millones_por_estudiante"]],
        on=["pte_codigo", "anio"], how="left", validate="one_to_one")
    assert c.pct_estrato_1_2.notna().all()
    c.insert(0, "id", c.anio.astype(str) + "-" + c.pte_codigo)
    c.insert(3, "universidad", c.pop("pte_nombre").map(nombre_corto))
    assert c.id.is_unique
    log(f"\nCaracterísticas: {len(c)} filas ({c.groupby('anio').size().to_dict()})")

    # 3. Malmquist
    mq = pd.read_csv("resultados/oe2_malmquist.csv", dtype=cod)
    m = pd.DataFrame({"id": mq.modelo + "-" + mq.version + "-" + mq.pte_codigo, "modelo": mq.modelo,
                      "version": mq.version, "pte_codigo": mq.pte_codigo,
                      "universidad": mq.pte_nombre.map(nombre_corto), "malmquist": mq.malmquist,
                      "cambio_eficiencia": mq.cambio_eficiencia, "cambio_tecnologico": mq.cambio_tecnologico})
    assert m.id.is_unique
    log(f"\nMalmquist: {len(m)} filas ({m.groupby(['modelo', 'version']).size().to_dict()})")

    # 4. segunda etapa
    se = pd.read_csv("resultados/oe3_segunda_etapa.csv")
    se.insert(0, "id", se.modelo + "-" + se.anio.astype(str) + "-" + se.variable)
    assert se.id.is_unique
    log(f"\nSegunda etapa: {len(se)} filas")

    log("\nArchivos:")
    escribir("universidades.json", limpio(u))
    escribir("caracteristicas.json", limpio(c))
    escribir("malmquist.json", limpio(m))
    escribir("segunda_etapa.json", limpio(se))

    ev = Path("docs/gobernanza/evidencias") / f"datos_tablero_{datetime.now():%Y-%m-%d_%H%M}.txt"
    ev.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"\nEvidencia: {ev}")


if __name__ == "__main__":
    main()
