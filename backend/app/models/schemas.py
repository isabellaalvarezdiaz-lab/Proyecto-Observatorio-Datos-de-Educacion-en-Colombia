"""Modelos Pydantic v2 de entrada y salida. Field(description=...) documenta /docs y /redoc."""
from datetime import datetime
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Modelo = Literal["principal", "cobertura", "cobertura_sin_unad"]
Anio = Literal[2023, 2024]
# En la URL el año llega como texto: se valida como entero en el rango del estudio.
AnioQuery = Annotated[int | None, Query(ge=2023, le=2024, description="Año (2023 o 2024)")]


class Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------- generales
class Salud(BaseModel):
    estado: Literal["ok"]
    entorno: str
    tablas: dict[str, int] = Field(description="Filas cargadas por tabla")
    modelo_ml: str | None = Field(description="Versión del imputador cargado, o None si no hay modelo")


class Universidad(Orm):
    pte_codigo: int = Field(description="Código de la entidad en el PTE (Ministerio de Hacienda)")
    nombre: str
    orden: str | None = Field(description="nacional o territorial (según Saber Pro)")
    departamento: str | None


class Intervalo(BaseModel):
    inf: float
    sup: float


# ---------------------------------------------------------------- eficiencia
class EficienciaFila(Orm):
    modelo: str
    anio: int
    pte_codigo: int
    universidad: str
    eficiencia: float = Field(description="δ = 1/φ del DEA BCC orientado al producto (1 = frontera)")
    eficiencia_corregida: float = Field(description="Corregida por sesgo con el bootstrap de Simar y Wilson")
    ic95: Intervalo
    en_frontera: bool
    pares: str | None = Field(description="Universidades de referencia y sus pesos")


class MalmquistFila(Orm):
    modelo: str
    version: str = Field(description="nominal (pesos corrientes) o real (pesos constantes)")
    pte_codigo: int
    universidad: str
    malmquist: float = Field(description=">1 avance de productividad, <1 retroceso")
    cambio_eficiencia: float
    cambio_tecnologico: float


# ---------------------------------------------------------------- riesgo
class ColaFila(Orm):
    anio: int
    pte_codigo: int | None
    nombre: str
    n_evaluados: int
    alfa: float
    k_cola: int = Field(description="Evaluados en la cola: ⌈α·n⌉")
    media: float
    var: float = Field(description="VaR: k-ésimo puntaje más bajo (simulación histórica)")
    var_ic_inf: float
    var_ic_sup: float
    cvar: float | None = Field(description="CVaR: promedio de los k puntajes más bajos")
    cvar_ic_inf: float | None
    cvar_ic_sup: float | None
    brecha_cola: float | None = Field(description="media − CVaR")
    suprimido: bool


class KupiecFila(Orm):
    pte_codigo: int | None
    nombre: str
    alfa: float
    var_2023: float
    n_2024: int
    fallas_2024: float = Field(description="Evaluados de 2024 por debajo del VaR de 2023 (empates ponderados)")
    tasa_2024: float
    lr_kupiec: float
    p: float
    p_holm: float | None
    rechaza_5pct: bool
    direccion: str | None
    tasa_ref_nacional: float = Field(description="Tasa nacional de 2024: referencia de la prueba relativa")
    lr_relativo: float
    p_relativo: float
    p_relativo_holm: float | None
    rechaza_relativo: bool
    direccion_relativa: str | None


class VarEntrada(BaseModel):
    """Puntajes de una población (por ejemplo, una cohorte) para calcular su riesgo de cola."""
    puntajes: list[float] = Field(min_length=20, max_length=300_000,
                                  description="Puntajes globales Saber Pro (0 a 300)")
    alfa: float = Field(0.05, gt=0, le=0.25, description="Nivel de la cola (0,05 = el 5 % más bajo)")
    B: int = Field(1000, ge=100, le=5000, description="Réplicas bootstrap")
    semilla: int = Field(20261106, ge=0)
    puntajes_backtest: list[float] | None = Field(
        None, min_length=20, max_length=300_000,
        description="Puntajes de otra cohorte para el backtesting de Kupiec contra el VaR de 'puntajes'")

    @field_validator("puntajes", "puntajes_backtest")
    @classmethod
    def rango_saber_pro(cls, v: list[float] | None) -> list[float] | None:
        if v is not None and any(not 0 <= p <= 300 for p in v):
            raise ValueError("los puntajes de Saber Pro van de 0 a 300")
        return v

    @model_validator(mode="after")
    def cola_suficiente(self) -> "VarEntrada":
        if self.alfa * len(self.puntajes) < 1:
            raise ValueError("con tan pocos puntajes la cola queda vacía: aumente n o α")
        return self


class KupiecCalculado(BaseModel):
    var_referencia: float
    peso_empates: float = Field(description="w: peso de los empates en el VaR (cuantil aleatorizado)")
    n_prueba: int
    fallas: float
    tasa_fallas: float
    lr: float
    p_valor: float
    rechaza_5pct: bool
    direccion: str | None


class VarResultado(BaseModel):
    n: int
    alfa: float
    k_cola: int
    media: float
    var: float
    cvar: float
    var_ic95: Intervalo
    cvar_ic95: Intervalo
    brecha_cola: float
    backtest: KupiecCalculado | None


# ---------------------------------------------------------------- stress
class Recorte(BaseModel):
    grupo: Literal["todas", "nacional", "territorial", "menos_eficientes", "universidad"]
    porcentaje: float = Field(gt=0, le=90, description="Recorte del presupuesto, en %")
    n_menos_eficientes: int | None = Field(None, ge=1, le=32,
                                           description="Solo con grupo = menos_eficientes")
    pte_codigo: int | None = Field(None, description="Solo con grupo = universidad")

    @model_validator(mode="after")
    def campos_del_grupo(self) -> "Recorte":
        if (self.grupo == "menos_eficientes") != (self.n_menos_eficientes is not None):
            raise ValueError("n_menos_eficientes va solo, y siempre, con grupo = menos_eficientes")
        if (self.grupo == "universidad") != (self.pte_codigo is not None):
            raise ValueError("pte_codigo va solo, y siempre, con grupo = universidad")
        return self


class Adicion(BaseModel):
    monto_mm: float = Field(gt=0, le=20_000, description="Recursos adicionales en miles de millones")
    reparto: Literal["matricula_pregrado", "pregrado_estratos_1_2", "uniforme"]


class EscenarioEntrada(BaseModel):
    modelo: Modelo = "principal"
    anio: Anio = 2024
    recortes: list[Recorte] = Field(default_factory=list, max_length=10)
    adicion: Adicion | None = None

    @model_validator(mode="after")
    def no_vacio(self) -> "EscenarioEntrada":
        if not self.recortes and self.adicion is None:
            raise ValueError("el escenario necesita al menos un recorte o una adición")
        return self


class StressMetricas(BaseModel):
    n: int
    insumo_total_mm: float
    eficiencia_media: float
    cambio_media: float
    n_frontera: int
    spearman_con_base: float = Field(description="Spearman entre el orden base y el del escenario")
    cambio_max: float
    universidad_cambio_max: str
    n_cambian_5_puntos: int
    n_cambian_puesto_5: int


class StressResumenFila(StressMetricas, Orm):
    modelo: str
    escenario: str


class StressFila(Orm):
    pte_codigo: int
    universidad: str
    orden: str | None
    insumo_base_mm: float
    insumo_escenario_mm: float
    eficiencia_base: float
    eficiencia_escenario: float
    cambio: float
    puesto_base: int
    puesto_escenario: int


class EscenarioResultado(BaseModel):
    modelo: str
    anio: int
    resumen: StressMetricas
    universidades: list[StressFila]


# ---------------------------------------------------------------- ML
class PrediccionEntrada(BaseModel):
    """Puntajes de los otros cuatro módulos de un evaluado (0 a 300)."""
    ciudadanas: float = Field(ge=0, le=300, description="Competencias ciudadanas")
    ingles: float = Field(ge=0, le=300)
    lectura_critica: float = Field(ge=0, le=300)
    razonamiento: float = Field(ge=0, le=300, description="Razonamiento cuantitativo")
    anio: Anio = 2024

    @field_validator("ciudadanas", "ingles", "lectura_critica", "razonamiento")
    @classmethod
    def no_cero(cls, v: float) -> float:
        if v == 0:
            raise ValueError("un 0 en un módulo es un dato faltante, no un puntaje: no se puede usar de perfil")
        return v


class PrediccionSalida(BaseModel):
    escrita_predicha: float = Field(description="Escrita esperada para ese perfil (media condicional)")
    intervalo_80: Intervalo = Field(description="Intervalo de predicción con los residuos del ajuste")
    intervalo_95: Intervalo
    global_estimado: float = Field(description="Promedio de los cinco módulos con la Escrita predicha")
    modelo_version: str
    advertencia: str
    id_prediccion: int


class PrediccionRegistro(Orm):
    id: int
    creada: datetime
    ciudadanas: float
    ingles: float
    lectura_critica: float
    razonamiento: float
    anio: int
    escrita_predicha: float
    global_estimado: float
    modelo_version: str
    tiempo_ms: float


class ImputacionFila(Orm):
    anio: int
    pte_codigo: int | None
    nombre: str
    n_evaluados: int
    n_ceros_escrita: int
    global_c: float = Field(description="Global con el promedio de los otros cuatro módulos en los ceros")
    global_d: float = Field(description="Global con la Escrita imputada por perfiles similares (PMM)")
    diferencia_d_menos_c: float


# ---------------------------------------------------------------- asistente
class Pregunta(BaseModel):
    pregunta: str = Field(min_length=5, max_length=500)
    usar_llm: bool = Field(True, description="Redactar con el modelo de lenguaje si hay clave configurada")

    @field_validator("pregunta")
    @classmethod
    def sin_espacios(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 5:
            raise ValueError("la pregunta es demasiado corta")
        return v


class Cifra(BaseModel):
    descripcion: str
    valor: float
    fuente: str = Field(description="Endpoint y tabla de donde sale la cifra")


class Fragmento(BaseModel):
    documento: str
    ubicacion: str = Field(description="Sección del documento o página del PDF")
    texto: str
    puntaje: float


class Respuesta(BaseModel):
    respuesta: str
    modo: Literal["plantilla", "llm", "llm_rechazado"]
    cifras: list[Cifra]
    fuentes: list[Fragmento]
