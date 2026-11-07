# API del observatorio (integración con Python para APIs e IA)

La API pone los resultados del proyecto detrás de un servicio web. El backend está hecho con FastAPI, Pydantic v2 y SQLAlchemy. El tablero, en Streamlit, solo consume la API. Hay tests con pytest, Docker multi-stage, despliegue en Render y CI en GitHub Actions.

**La API nunca lee microdatos.** Carga los CSV de `resultados/`, que son agregados por universidad y ya están en el repositorio, y el modelo `modelos/imputador_escrita.json`, que no trae registros individuales. Por eso los tests y la imagen de Docker funcionan sin `data/`.

## Arquitectura en cinco capas

| Capa | Qué hace aquí | Archivos |
|---|---|---|
| 1 · Datos y persistencia | carga los CSV a SQLite con SQLAlchemy ORM y los sirve | `app/etl.py`, `app/database.py`, `app/models/db_models.py` |
| 2 · Análisis de riesgo | VaR y CVaR no paramétricos, bootstrap y Kupiec, publicados y bajo demanda | `app/services/riesgo.py` (`RiskCalculator`) |
| 3 · Stress testing | escenarios E0–E7 y escenarios a la medida con el DEA recalculado | `app/services/stress.py` (`DEA`, `StressService`) |
| 4 · Machine learning | imputador de Escrita entrenado offline, servido con Singleton en `/predict`; cada predicción se guarda | `app/ml/predictor.py` (`ImputadorEscrita`), `scripts/imputar_escrita.py` |
| 5 · Infraestructura | pytest + TestClient, Docker, Render, GitHub Actions, logs | `tests/`, `Dockerfile`, `docker-compose.yml`, `../render.yaml`, `../.github/workflows/ci.yml` |

Además está el **asistente** (`app/services/asistente.py`): RAG sobre el informe final en PDF, el README y los diccionarios, más herramientas que leen la base. Sigue la regla "Nada sin fuente" del protocolo v2 del equipo:

- Las cifras salen solo de la base.
- Cada fragmento lleva su documento y su sección o página.
- El LLM es opcional y solo redacta. Si su respuesta trae un número que no está en las fuentes, se descarta y se responde con la plantilla.

## Endpoints

| Método | Ruta | Capa | Qué devuelve |
|---|---|---|---|
| GET | `/salud` | 1 | estado, filas por tabla y versión del modelo |
| GET | `/universidades`, `/universidades/{pte_codigo}` | 1 | las 34 universidades (búsqueda sin tildes con `?buscar=`) |
| GET | `/eficiencia`, `/eficiencia/{pte_codigo}` | 1 | eficiencia DEA corregida con su IC 95 % (`?modelo=&anio=`) |
| GET | `/malmquist` | 1 | índice de Malmquist 2023→2024 y su descomposición |
| GET | `/imputacion/escrita` | 1 | `global_c` frente a `global_d` por universidad |
| GET | `/riesgo/cola`, `/riesgo/cola/{pte_codigo}` | 2 | VaR y CVaR 5 % publicados, con intervalos bootstrap |
| GET | `/riesgo/backtesting/kupiec` | 2 | backtesting 2023→2024 (`?solo_rechazos=true&relativo=true`) |
| POST | `/riesgo/var` | 2 | VaR, CVaR, bootstrap y Kupiec de una lista de puntajes |
| GET | `/stress/escenarios`, `/stress/escenarios/{E0…E7}` | 3 | escenarios publicados |
| POST | `/stress` | 3 | escenario a la medida (recortes por grupo y adiciones) con el DEA recalculado |
| POST | `/predict` | 4 | Escrita esperada para un perfil, con intervalos de predicción |
| GET | `/predict/modelo`, `/predict/historial` | 4 | metadatos del modelo y predicciones guardadas |
| POST | `/asistente/preguntar` | — | respuesta con cifras de la base y fragmentos citados |

La documentación interactiva está en `/docs` (Swagger) y `/redoc`.

Códigos de estado:

| Código | Cuándo |
|---|---|
| 400 | la universidad existe pero no está en ese modelo |
| 404 | no existe |
| 422 | la validación de Pydantic falló |
| 503 | no hay modelo de ML |
| 500 | error interno (en producción, sin detalles) |

**Ejemplo de escenario a la medida:** un recorte del 20 % a las nacionales y la gratuidad repartida por matrícula de pregrado. Las adiciones se reparten entre todas las universidades del año, igual que en `scripts/riesgo_stress.py`.

```json
{"modelo": "principal", "anio": 2024,
 "recortes": [{"grupo": "nacional", "porcentaje": 20}],
 "adicion": {"monto_mm": 2744.311, "reparto": "matricula_pregrado"}}
```

## Cómo correrla (desde `backend/`)

```bash
python -m venv .venv
source .venv/Scripts/activate      # Git Bash en Windows; en Linux o Mac: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q                # 85 tests
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

Al arrancar, si la base está vacía, la API carga los CSV. Para recargarlos después de volver a correr los scripts:

```bash
python -m app.etl
```

Tablero (otra terminal, desde la raíz del repositorio):

```bash
python -m pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Docker (desde `backend/`). Levanta la API en el puerto 8000 y el tablero en el 8501:

```bash
docker compose up --build
```

Render: el archivo `render.yaml` de la raíz despliega la API desde el Dockerfile; Render inyecta `$PORT`. La base vive en `/tmp`, así que en el plan gratuito el historial de predicciones se reinicia con cada despliegue.

## Variables de entorno

Se leen con `BaseSettings` desde el entorno o desde `backend/.env`. El archivo `backend/.env.example` trae las variables documentadas; ninguna es obligatoria.

| Variable | Por defecto | Para qué |
|---|---|---|
| `ENTORNO` | `desarrollo` | en `produccion`, los errores 500 no muestran detalles; la imagen de Docker usa `produccion` |
| `DATABASE_URL` | `sqlite:///backend/observatorio.db` | base de resultados |
| `CARGAR_AL_INICIAR` | `true` | cargar los CSV si la base está vacía |
| `RESULTADOS_DIR`, `MODELO_IMPUTADOR`, `DOCS_DIR` | carpetas del repositorio | rutas de los CSV, del modelo y de los documentos |
| `GRATUIDAD_2024_MM` | `2744.311` | gratuidad 2024 en miles de millones (PTE, Cuadro No. 7, fila 1758) |
| `LLM_API_KEY` | vacía | clave de Anthropic para que el asistente redacte; sin clave responde con plantillas |
| `LLM_MODELO` | `claude-haiku-5-5` | modelo del asistente |
| `LOG_LEVEL` | `INFO` | nivel del log |

## Buenas prácticas pedidas por el curso

| Práctica | Dónde está |
|---|---|
| Decorador propio | `@medir_tiempo` (`app/decoradores.py`), sobre los cálculos de los servicios; además, un middleware agrega el encabezado `X-Tiempo-ms` |
| Clases | `RiskCalculator`, `DEA`, `StressService`, `ImputadorEscrita`, `IndiceBM25`, `Asistente` |
| Validadores propios (`@field_validator`) | rango 0–300 de Saber Pro, un 0 en un módulo no es perfil, pregunta no vacía |
| Validadores de modelo | la cola no puede quedar vacía, los campos según el grupo del recorte, el escenario no puede venir vacío |
| `Depends()` | configuración, sesión, servicios, modelo ML y LLM (`app/dependencies.py`); los tests los reemplazan con `dependency_overrides` |
| Ruta asíncrona | `/asistente/preguntar`, porque llama al LLM externo con `httpx.AsyncClient` |
| Cálculos en rutas `def` | el DEA y el bootstrap son trabajo de CPU, así que FastAPI los corre en su pool de hilos |
| Singleton | `ImputadorEscrita.__new__` con candado: el modelo se lee una vez por proceso |
| Versiones fijas (`==`) | `requirements.txt`, con Python 3.11.9 |

Los tests comprueban que la API dice lo mismo que los scripts:

- la eficiencia, el Malmquist, el VaR, el CVaR y Kupiec son iguales a los CSV;
- los siete escenarios armados con `POST /stress` reproducen los de `riesgo_stress.py` en los tres modelos;
- el LR de Kupiec coincide con scipy;
- `/predict` aplica la fórmula del JSON y guarda cada predicción;
- el asistente descarta una redacción con un número inventado.
