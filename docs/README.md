# Proyecto Observatorio de Datos de Educación en Colombia

## Introducción
Consolidamos fuentes públicas 2021–2024 para construir una base integrada y generar análisis descriptivos. La primera fase fue **descargar, revisar y perfilar** las bases; luego **automatizar** con Selenium cuando fue posible y estandarizar campos para su integración.

## Objetivos
- Integrar **PTE/PGN Educación**, **Saber Pro** y **SNIES** en una tabla maestra documentada.
- Normalizar identificadores, años y nombres; crear un **diccionario de variables**.
- Implementar un **modelo estrella** (hechos: puntajes; 5 dimensiones) y preparar exploraciones.
- Entregar **figuras** y una **presentación** con hallazgos principales.

## Datos y alcance
- **PTE – PGN Educación (2021–2024)**: 48 archivos consolidados en una sola base. Nota: en **nov/2021** no hubo registro reportado.
- **Saber Pro (ICFES 2021–2024)**: puntajes e información de estudiantes/programas.
- **SNIES**: matrícula, instituciones y programas.

> Los archivos de datos **no se suben al repo** por tamaño. Se almacenan en OneDrive. 

## Estructura del repositorio
~~~text
.
├─ codigos/
│  ├─ exploracion.ipynb
│  ├─ exploracion.py
│  ├─ extrae_pte_educacion_full.py
│  ├─ scraper_snies.py
│  └─ saber_pro_2021_2024/
│     ├─ modelo_estrella.py
│     └─ database.py
├─ docs/
│  ├─ analisis_de_bases_seleccionadas.md
│  ├─ exploracion_analisis_univariado.md
│  ├─ exploracion_analisis_bivariado.md
│  ├─ exploracion_analisis_bivariado_parte_2.md
│  ├─ exploracion_analisis_multivariado.md
│  ├─ informe_final.md
│      
└─ README.md

~~~

## Codigos
**Requisitos**: Python ≥ 3.10; paquetes: `selenium`, `pandas`, `openpyxl`.

~~~bash
# 0) estructura local de datos 
mkdir -p data/raw data/interim data/processed

# 1) PTE/PGN Educación
# Si la web permite Selenium:
python "Códigos/extrae_pte_educacion_full.py"
# Si la web bloquea, realizar descarga manual a data/raw/pte/ y correr el script para consolidar.

# 2) SNIES
python "Códigos/scraper_snies.py"               # descarga
python "Códigos/snies_renamed_registros.py"     # renombrado/trazabilidad

# 3) Saber Pro / Exploración
python "Códigos/Exploración.py"  # o abrir Códigos/Exploración.ipynb
~~~

## Notas metodológicas cortas
- PGN: cuando la página bloqueó Selenium se usó **descarga manual** y un script que **une** las bases y extrae **PGN del sector educación** por año.
- El **modelo estrella** y la exploración posterior se montaron sobre **Saber Pro**.

## Resultados parciales
- **Base consolidada** PTE Educación 2021–2024 y diccionario (ver `docs/Analisis de Bases.md`).
- **Esquema estrella** operativo para puntajes de Saber Pro.
- **Exploraciones** con tablas y gráficas base (ver `docs/*` y `reports/figures/` si aplica).

## Licencia y uso de datos
El código se publica bajo la licencia definida por el equipo. Los datos siguen los términos de PTE, ICFES y MEN; el procedimiento de obtención queda documentado en `docs/`.
