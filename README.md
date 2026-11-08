# Observatorio de Datos de Educación en Colombia — eficiencia del gasto en universidades públicas

Consultoría Estadística · Universidad Santo Tomás · 2026-II
Equipo: Isabella Álvarez, Anderson González, Eduar Caicedo · Docente: Javier Mauricio Sierra

Medimos con qué eficiencia las 33 universidades públicas convierten los recursos de la Nación en cobertura, graduados y desempeño en Saber Pro, en 2023 y 2024. Para eso integramos tres fuentes (SNIES, Saber Pro y el presupuesto del PTE) y aplicamos DEA con bootstrap, el índice de Malmquist, herramientas de teoría del riesgo y una API en Python con los resultados.

Este trabajo continúa el [proyecto del semestre anterior](https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia), que no alcanzó a integrar las fuentes. El periodo es 2023–2024 porque el PTE desagrega el presupuesto por universidad solo desde 2023.

## Entregables

- **Informe final:** `docs/informe_final.pdf`
- **Presentación:** `docs/presentacion_sustentacion.pdf`
- **Tablero interactivo:** https://observatorio-tablero.onrender.com
- **API:** https://observatorio-api-fuk3.onrender.com/docs

El tablero y la API están en el plan gratuito de Render: si llevan un rato sin uso, la primera carga tarda cerca de un minuto.

## Cómo ejecutarlo

### Sin los datos crudos: la API, el tablero y las pruebas

Funciona con lo que está en el repositorio. Requiere Python 3.11.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows (Git Bash); en Linux o Mac: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q                  # 85 pruebas
uvicorn app.main:app --reload        # API en http://localhost:8000/docs
```

Para ver el tablero, deje la API corriendo y en otra terminal, desde la raíz:

```bash
python -m pip install -r frontend/requirements.txt
streamlit run frontend/app.py        # http://localhost:8501
```

Con Docker, `docker compose up --build` desde `backend/` levanta las dos.

### Con los datos crudos: rehacer todos los resultados

Los microdatos de Saber Pro son de acceso institucional y no se suben. Con los archivos en `data/raw/` (ver `docs/REPRODUCIR.md`), los pasos son, en orden:

```bash
python -m pip install -r requirements.txt
python scripts/correr_oe1.py                    # OE1: tabla maestra y base integrada
python scripts/oe3_dea_bootstrap.py             # OE3: DEA con bootstrap (≈ 10 min)
python scripts/oe2_malmquist.py                 # OE2: índice de Malmquist
python scripts/oe3_cobertura_sin_unad.py        # pruebas de solidez del OE3
python scripts/caracteristicas_universidades.py
python scripts/oe3_segunda_etapa.py
python scripts/oe3_validacion_fuera_muestra.py
python scripts/graficos_oe2_oe3.py              # figuras del informe
python scripts/revision_trabajo_previo.py       # corrección del trabajo 2025-2
python scripts/riesgo_puntaje.py                # VaR, CVaR y Kupiec
python scripts/riesgo_stress.py                 # stress testing del presupuesto
python scripts/imputar_escrita.py               # imputación de los ceros de Escrita
```

Cada resultado tiene un verificador que lo recalcula por otro camino: `verificar_oe1.py`, `verificar_oe2_oe3.py`, `verificar_riesgo.py` y `verificar_imputacion.py`. La guía completa, con tiempos y opciones, está en `docs/REPRODUCIR.md`.

## Qué hay en el repositorio

```text
resultados/   tablas de resultados, agregadas por universidad; empiece por resultados/README.md
scripts/      el código de los análisis (scripts/fase1/: diagnóstico de las fuentes, septiembre)
backend/      API (FastAPI + SQLAlchemy) con sus pruebas y Docker; ver backend/README.md
frontend/     tablero en Streamlit
modelos/      modelo de imputación de Escrita (solo coeficientes)
docs/         informe, presentación, diccionarios de datos, guía de reproducción y bitácora de IA
heredado/     archivos del equipo 2025-2, sin cambios
```

En `docs/` también están `gobernanza/evidencias/` (la salida de cada corrida), `uso_ia/` (los inventarios de fallos de IA de cada integrante) y `nada_sin_fuente/` (la actividad de verificación de fuentes de septiembre).

## Datos y licencias

Los datos son públicos (PTE – MinHacienda; SNIES – MEN) o de acceso institucional (Saber Pro – ICFES) y no se redistribuyen aquí. Este repositorio publica solo tablas agregadas por institución, sin información de estudiantes. Cuando una sede tiene menos de 5 evaluados en Saber Pro en un año, sus promedios no se publican, porque con tan pocos estudiantes el promedio deja ver el puntaje de una persona; los cálculos sí usan a todos los evaluados (ver `scripts/publicacion.py` y la regla 4 de `docs/diccionario_tabla_maestra.md`). Los valores de esas filas siguen en el historial de git anterior al 20-10-2026.
