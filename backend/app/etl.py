"""Carga los CSV de resultados/ a la base de la API.

Los CSV los producen los scripts de scripts/ y ya están en el repositorio; son agregados por
universidad, sin microdatos. Cargar es idempotente: borra y vuelve a llenar cada tabla.

Uso (desde backend/):
    python -m app.etl
"""
import logging
import math
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from .config import get_settings
from .database import BaseDeDatos
from .models import db_models as m

log = logging.getLogger("observatorio")

ARCHIVOS = ["base_integrada_2023_2024.csv", "caracteristicas_universidades.csv", "oe3_eficiencia.csv",
            "oe3_cobertura_sin_unad.csv", "oe2_malmquist.csv", "riesgo_puntaje.csv", "riesgo_kupiec.csv",
            "riesgo_stress_resumen.csv", "riesgo_stress_universidades.csv",
            "imputacion_escrita_universidades.csv"]


def _limpio(v: Any) -> Any:
    """NaN de pandas → None de SQL; tipos de numpy → tipos de Python."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):
        v = v.item()
        if isinstance(v, float) and math.isnan(v):
            return None
    return v


def _filas(df: pd.DataFrame, columnas: dict[str, str]) -> list[dict[str, Any]]:
    """Registros con las columnas renombradas {columna_csv: atributo_orm}."""
    sub = df[list(columnas)].rename(columns=columnas)
    return [{k: _limpio(v) for k, v in r.items()} for r in sub.to_dict(orient="records")]


def _codigo(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pte_codigo"] = df["pte_codigo"].astype("Int64").astype(object).where(df["pte_codigo"].notna(), None)
    return df


def leer(carpeta: Path, nombre: str) -> pd.DataFrame:
    ruta = carpeta / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta}: corra primero el script que lo produce (ver README)")
    return pd.read_csv(ruta, encoding="utf-8-sig")


def cargar(db: Session, carpeta: Path) -> dict[str, int]:
    """Vacía y llena todas las tablas de resultados. Devuelve cuántas filas cargó en cada una."""
    base = leer(carpeta, "base_integrada_2023_2024.csv")
    car = leer(carpeta, "caracteristicas_universidades.csv")
    efi = pd.concat([leer(carpeta, "oe3_eficiencia.csv"), leer(carpeta, "oe3_cobertura_sin_unad.csv")])
    mal = leer(carpeta, "oe2_malmquist.csv")
    rp = _codigo(leer(carpeta, "riesgo_puntaje.csv"))
    rk = _codigo(leer(carpeta, "riesgo_kupiec.csv"))
    sr = leer(carpeta, "riesgo_stress_resumen.csv")
    su = leer(carpeta, "riesgo_stress_universidades.csv")
    im = _codigo(leer(carpeta, "imputacion_escrita_universidades.csv"))

    for tabla in (m.Prediccion, m.StressUniversidad, m.StressResumen, m.Kupiec, m.RiesgoCola,
                  m.ImputacionUniversidad, m.Malmquist, m.Eficiencia, m.Observacion, m.Universidad):
        if tabla is not m.Prediccion:          # las predicciones son historial: no se borran
            db.query(tabla).delete()

    c24 = car.sort_values("anio").drop_duplicates("pte_codigo", keep="last")
    u = base.drop_duplicates("pte_codigo")[["pte_codigo", "pte_nombre"]].merge(
        c24[["pte_codigo", "orden", "departamento_domicilio"]], on="pte_codigo", how="left")
    db.bulk_insert_mappings(m.Universidad, _filas(u, {"pte_codigo": "pte_codigo", "pte_nombre": "nombre",
                                                      "orden": "orden", "departamento_domicilio": "departamento"}))
    obs = base.merge(car[["pte_codigo", "anio", "pct_estrato_1_2"]], on=["pte_codigo", "anio"], how="left")
    db.bulk_insert_mappings(m.Observacion, _filas(obs, {c: c for c in (
        "pte_codigo", "anio", "obligacion_mm", "mat_total_prom", "mat_pregrado_prom", "grad_total",
        "global_c", "pct_estrato_1_2", "incluida_dea")}))
    db.bulk_insert_mappings(m.Eficiencia, _filas(efi, {c: c for c in (
        "modelo", "anio", "pte_codigo", "eficiencia", "eficiencia_corregida", "ic95_inf", "ic95_sup",
        "en_frontera", "pares")}))
    db.bulk_insert_mappings(m.Malmquist, _filas(mal, {c: c for c in (
        "modelo", "version", "pte_codigo", "malmquist", "cambio_eficiencia", "cambio_tecnologico")}))
    db.bulk_insert_mappings(m.RiesgoCola, _filas(rp, {**{c: c for c in (
        "anio", "pte_codigo", "n_evaluados", "alfa", "k_cola", "media", "var", "var_ic_inf", "var_ic_sup",
        "cvar", "cvar_ic_inf", "cvar_ic_sup", "brecha_cola", "suprimido")}, "pte_nombre": "nombre"}))
    db.bulk_insert_mappings(m.Kupiec, _filas(rk, {**{c: c for c in (
        "pte_codigo", "alfa", "var_2023", "n_2024", "fallas_2024", "tasa_2024", "lr_kupiec", "p", "p_holm",
        "rechaza_5pct", "direccion", "tasa_ref_nacional", "lr_relativo", "p_relativo", "p_relativo_holm",
        "rechaza_relativo", "direccion_relativa")}, "pte_nombre": "nombre"}))
    db.bulk_insert_mappings(m.StressResumen, _filas(sr, {c: c for c in (
        "modelo", "escenario", "n", "insumo_total_mm", "eficiencia_media", "cambio_media", "n_frontera",
        "spearman_con_base", "cambio_max", "universidad_cambio_max", "n_cambian_5_puntos",
        "n_cambian_puesto_5")}))
    db.bulk_insert_mappings(m.StressUniversidad, _filas(su, {c: c for c in (
        "modelo", "escenario", "pte_codigo", "insumo_base_mm", "insumo_escenario_mm", "eficiencia_base",
        "eficiencia_escenario", "cambio", "puesto_base", "puesto_escenario")}))
    db.bulk_insert_mappings(m.ImputacionUniversidad, _filas(im, {**{c: c for c in (
        "anio", "pte_codigo", "n_evaluados", "n_ceros_escrita", "global_c", "global_d",
        "diferencia_d_menos_c")}, "pte_nombre": "nombre"}))
    db.commit()
    conteo = {t.__tablename__: db.query(t).count() for t in (
        m.Universidad, m.Observacion, m.Eficiencia, m.Malmquist, m.RiesgoCola, m.Kupiec,
        m.StressResumen, m.StressUniversidad, m.ImputacionUniversidad)}
    log.info("Carga terminada: %s", conteo)
    return conteo


def base_vacia(db: Session) -> bool:
    return db.query(m.Universidad).first() is None


def main() -> None:
    logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")
    s = get_settings()
    bd = BaseDeDatos(s.database_url)
    bd.crear_tablas()
    with bd.SesionLocal() as db:
        for tabla, n in cargar(db, s.resultados_dir).items():
            print(f"{tabla:24s} {n:5d} filas")


if __name__ == "__main__":
    main()
