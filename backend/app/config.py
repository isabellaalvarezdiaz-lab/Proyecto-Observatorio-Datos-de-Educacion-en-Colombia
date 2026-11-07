"""Configuración de la API con BaseSettings: todo sale de variables de entorno o de backend/.env.

Las rutas por defecto apuntan a las carpetas del repositorio (resultados/, modelos/, docs/), así
la API usa exactamente las tablas que producen los scripts de scripts/. Ninguna ruta apunta a
data/: la API nunca lee microdatos.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPO = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env",
                                      env_file_encoding="utf-8", extra="ignore")

    entorno: Literal["desarrollo", "produccion"] = Field(
        "desarrollo", description="En producción se ocultan los detalles de los errores internos")
    database_url: str = Field(f"sqlite:///{(RAIZ_REPO / 'backend' / 'observatorio.db').as_posix()}",
                              description="URL de SQLAlchemy de la base de resultados")
    resultados_dir: Path = Field(RAIZ_REPO / "resultados", description="CSV que producen los scripts")
    modelo_imputador: Path = Field(RAIZ_REPO / "modelos" / "imputador_escrita.json",
                                   description="Modelo de Escrita entrenado offline por scripts/imputar_escrita.py")
    docs_dir: Path = Field(RAIZ_REPO / "docs", description="Documentos que consulta el asistente")
    cargar_al_iniciar: bool = Field(True, description="Cargar los CSV a la base si está vacía al arrancar")

    # Stress testing: monto de la gratuidad 2024 en miles de millones de pesos.
    # Fuente: PTE, Cuadro No. 7 a diciembre de 2024, rubro «POLÍTICA DE GRATUIDAD DE LA EDUCACIÓN
    # SUPERIOR PÚBLICA», columna Obligación, fila 1758 (ver docs/diccionario_riesgo.md).
    gratuidad_2024_mm: float = Field(2744.311, gt=0)

    # Asistente: el LLM es opcional. Sin clave, el asistente responde con plantillas.
    llm_api_key: str | None = Field(None, description="Clave de la API de Anthropic (opcional)")
    llm_modelo: str = Field("claude-haiku-5-5", description="Modelo de lenguaje del asistente")
    llm_url: str = Field("https://api.anthropic.com/v1/messages")
    llm_timeout_s: float = Field(30.0, gt=0)

    log_level: str = Field("INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()
