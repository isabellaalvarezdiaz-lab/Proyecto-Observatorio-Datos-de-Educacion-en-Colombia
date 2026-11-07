"""Tablas ORM. Cada tabla de resultados es la copia de un CSV de resultados/ (ver app/etl.py);
la tabla 'predicciones' guarda cada llamada a /predict para monitorear el modelo."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Universidad(Base):
    __tablename__ = "universidades"
    pte_codigo: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    orden: Mapped[str | None] = mapped_column(String(20))
    departamento: Mapped[str | None] = mapped_column(String(80))
    observaciones: Mapped[list["Observacion"]] = relationship(back_populates="universidad")


class Observacion(Base):
    """Insumo y productos del DEA por universidad y año (base_integrada + características)."""
    __tablename__ = "observaciones"
    __table_args__ = (UniqueConstraint("pte_codigo", "anio"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pte_codigo: Mapped[int] = mapped_column(ForeignKey("universidades.pte_codigo"), index=True)
    anio: Mapped[int] = mapped_column(Integer, index=True)
    obligacion_mm: Mapped[float] = mapped_column(Float)
    mat_total_prom: Mapped[float] = mapped_column(Float)
    mat_pregrado_prom: Mapped[float] = mapped_column(Float)
    grad_total: Mapped[float] = mapped_column(Float)
    global_c: Mapped[float | None] = mapped_column(Float)
    pct_estrato_1_2: Mapped[float | None] = mapped_column(Float)
    incluida_dea: Mapped[bool] = mapped_column(Boolean)
    universidad: Mapped[Universidad] = relationship(back_populates="observaciones")


class Eficiencia(Base):
    __tablename__ = "eficiencias"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    modelo: Mapped[str] = mapped_column(String(30), index=True)
    anio: Mapped[int] = mapped_column(Integer, index=True)
    pte_codigo: Mapped[int] = mapped_column(ForeignKey("universidades.pte_codigo"), index=True)
    eficiencia: Mapped[float] = mapped_column(Float)
    eficiencia_corregida: Mapped[float] = mapped_column(Float)
    ic95_inf: Mapped[float] = mapped_column(Float)
    ic95_sup: Mapped[float] = mapped_column(Float)
    en_frontera: Mapped[bool] = mapped_column(Boolean)
    pares: Mapped[str | None] = mapped_column(String(500))


class Malmquist(Base):
    __tablename__ = "malmquist"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    modelo: Mapped[str] = mapped_column(String(30))
    version: Mapped[str] = mapped_column(String(20))
    pte_codigo: Mapped[int] = mapped_column(ForeignKey("universidades.pte_codigo"), index=True)
    malmquist: Mapped[float] = mapped_column(Float)
    cambio_eficiencia: Mapped[float] = mapped_column(Float)
    cambio_tecnologico: Mapped[float] = mapped_column(Float)


class RiesgoCola(Base):
    """VaR y CVaR no paramétricos del puntaje (resultados/riesgo_puntaje.csv)."""
    __tablename__ = "riesgo_cola"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anio: Mapped[int] = mapped_column(Integer, index=True)
    pte_codigo: Mapped[int | None] = mapped_column(ForeignKey("universidades.pte_codigo"), index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    n_evaluados: Mapped[int] = mapped_column(Integer)
    alfa: Mapped[float] = mapped_column(Float)
    k_cola: Mapped[int] = mapped_column(Integer)
    media: Mapped[float] = mapped_column(Float)
    var: Mapped[float] = mapped_column(Float)
    var_ic_inf: Mapped[float] = mapped_column(Float)
    var_ic_sup: Mapped[float] = mapped_column(Float)
    cvar: Mapped[float | None] = mapped_column(Float)
    cvar_ic_inf: Mapped[float | None] = mapped_column(Float)
    cvar_ic_sup: Mapped[float | None] = mapped_column(Float)
    brecha_cola: Mapped[float | None] = mapped_column(Float)
    suprimido: Mapped[bool] = mapped_column(Boolean)


class Kupiec(Base):
    """Backtesting 2023 → 2024 (resultados/riesgo_kupiec.csv)."""
    __tablename__ = "kupiec"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pte_codigo: Mapped[int | None] = mapped_column(ForeignKey("universidades.pte_codigo"), index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    alfa: Mapped[float] = mapped_column(Float)
    var_2023: Mapped[float] = mapped_column(Float)
    n_2024: Mapped[int] = mapped_column(Integer)
    fallas_2024: Mapped[float] = mapped_column(Float)
    tasa_2024: Mapped[float] = mapped_column(Float)
    lr_kupiec: Mapped[float] = mapped_column(Float)
    p: Mapped[float] = mapped_column(Float)
    p_holm: Mapped[float | None] = mapped_column(Float)
    rechaza_5pct: Mapped[bool] = mapped_column(Boolean)
    direccion: Mapped[str | None] = mapped_column(String(40))
    tasa_ref_nacional: Mapped[float] = mapped_column(Float)
    lr_relativo: Mapped[float] = mapped_column(Float)
    p_relativo: Mapped[float] = mapped_column(Float)
    p_relativo_holm: Mapped[float | None] = mapped_column(Float)
    rechaza_relativo: Mapped[bool] = mapped_column(Boolean)
    direccion_relativa: Mapped[str | None] = mapped_column(String(40))


class StressResumen(Base):
    __tablename__ = "stress_resumen"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    modelo: Mapped[str] = mapped_column(String(30), index=True)
    escenario: Mapped[str] = mapped_column(String(80), index=True)
    n: Mapped[int] = mapped_column(Integer)
    insumo_total_mm: Mapped[float] = mapped_column(Float)
    eficiencia_media: Mapped[float] = mapped_column(Float)
    cambio_media: Mapped[float] = mapped_column(Float)
    n_frontera: Mapped[int] = mapped_column(Integer)
    spearman_con_base: Mapped[float] = mapped_column(Float)
    cambio_max: Mapped[float] = mapped_column(Float)
    universidad_cambio_max: Mapped[str] = mapped_column(String(200))
    n_cambian_5_puntos: Mapped[int] = mapped_column(Integer)
    n_cambian_puesto_5: Mapped[int] = mapped_column(Integer)


class StressUniversidad(Base):
    __tablename__ = "stress_universidades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    modelo: Mapped[str] = mapped_column(String(30), index=True)
    escenario: Mapped[str] = mapped_column(String(80), index=True)
    pte_codigo: Mapped[int] = mapped_column(ForeignKey("universidades.pte_codigo"), index=True)
    insumo_base_mm: Mapped[float] = mapped_column(Float)
    insumo_escenario_mm: Mapped[float] = mapped_column(Float)
    eficiencia_base: Mapped[float] = mapped_column(Float)
    eficiencia_escenario: Mapped[float] = mapped_column(Float)
    cambio: Mapped[float] = mapped_column(Float)
    puesto_base: Mapped[int] = mapped_column(Integer)
    puesto_escenario: Mapped[int] = mapped_column(Integer)


class ImputacionUniversidad(Base):
    __tablename__ = "imputacion_escrita"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anio: Mapped[int] = mapped_column(Integer, index=True)
    pte_codigo: Mapped[int | None] = mapped_column(ForeignKey("universidades.pte_codigo"), index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    n_evaluados: Mapped[int] = mapped_column(Integer)
    n_ceros_escrita: Mapped[int] = mapped_column(Integer)
    global_c: Mapped[float] = mapped_column(Float)
    global_d: Mapped[float] = mapped_column(Float)
    diferencia_d_menos_c: Mapped[float] = mapped_column(Float)


class Prediccion(Base):
    """Cada predicción de /predict, para monitorear el modelo (entradas, salida y versión)."""
    __tablename__ = "predicciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creada: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                             default=lambda: datetime.now(timezone.utc))
    ciudadanas: Mapped[float] = mapped_column(Float)
    ingles: Mapped[float] = mapped_column(Float)
    lectura_critica: Mapped[float] = mapped_column(Float)
    razonamiento: Mapped[float] = mapped_column(Float)
    anio: Mapped[int] = mapped_column(Integer)
    escrita_predicha: Mapped[float] = mapped_column(Float)
    global_estimado: Mapped[float] = mapped_column(Float)
    modelo_version: Mapped[str] = mapped_column(String(20))
    tiempo_ms: Mapped[float] = mapped_column(Float)
