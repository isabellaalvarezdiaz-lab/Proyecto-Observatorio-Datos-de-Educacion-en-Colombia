# Observatorio de Datos de Educación en Colombia — eficiencia del gasto en universidades públicas

Consultoría Estadística · Universidad Santo Tomás · 2026-II
Equipo: Isabella Álvarez, Anderson González, Eduar Caicedo · Docente: Javier Mauricio Sierra

Continúa el [proyecto del semestre anterior](https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia), cuyo informe reconoce que no integró sus tres fuentes. Aquí se integran y se mide la eficiencia con la que las universidades públicas convierten los recursos de la Nación en cobertura, graduados y desempeño en Saber Pro.

El periodo es **2023–2024**. Lo fija la intersección de las fuentes: el PTE desagrega el presupuesto por universidad solo desde 2023, y Saber Pro está disponible hasta 2024.

| Objetivo | Qué produce | Dónde |
|---|---|---|
| OE1 · Tabla maestra SNIES + Saber Pro (todas las instituciones) | una fila por institución y año | `resultados/tabla_maestra_2023_2024.csv` |
| OE1 · Base para el DEA: tabla maestra + PTE (universidades públicas) | una fila por universidad y año | `resultados/base_integrada_2023_2024.csv` |
| OE2 · Índice de Malmquist 2023→2024 | cambio de productividad por universidad | `resultados/oe2_malmquist.csv` |
| OE3 · DEA con bootstrap (Simar y Wilson, 1998) | eficiencia con intervalos, pares, metas y sensibilidad | `resultados/oe3_eficiencia.csv`, `oe3_deja_uno_fuera.csv`, `oe3_sensibilidad.csv` |
| OE3 · Cobertura sin la UNAD | eficiencia de las otras 32 universidades | `resultados/oe3_cobertura_sin_unad.csv` |
| OE3 · Validación fuera de muestra | si la evaluación se sostiene con universidades que el modelo no usó | `resultados/oe3_validacion_resumen.csv`, `oe3_validacion_universidades.csv` |
| OE3 · Segunda etapa (exploratoria) | qué características, institucionales y socioeconómicas, se asocian con la eficiencia, y el perfil de las menos eficientes | `resultados/caracteristicas_universidades.csv`, `oe3_segunda_etapa.csv`, `oe3_contexto_menos_eficientes.csv` |
| Corrección del trabajo previo | cifras de Comunicación Escrita 2023–2024 que corrigen el informe 2025-2 | `resultados/revision_trabajo_previo.csv` |
| Tablero interactivo | los datos que lee el tablero, tomados de las tablas anteriores | `resultados/tablero/*.json` |

## Estructura

```text
.
├─ scripts/        código; todo se corre desde la raíz del repositorio
├─ resultados/     tablas agregadas, sin datos de estudiantes (sí se suben)
│  ├─ figuras/     las que genera graficos_oe2_oe3.py
│  └─ tablero/     los datos que lee el tablero interactivo
├─ docs/
│  ├─ diccionario_tabla_maestra.md, diccionario_base_integrada.md, diccionario_resultados_oe2_oe3.md
│  ├─ gobernanza/evidencias/   salida de cada corrida, con fecha y hora
│  ├─ uso_ia/                  inventarios de fallos de IA
│  ├─ nada_sin_fuente/         actividad de gestión de la información e IA (septiembre); ver su LEEME.md
│  ├─ BITACORA_IA.md
│  └─ Consultoria.pdf          anteproyecto
├─ heredado/       los archivos del equipo 2025-2, sin cambios; su README quedó como README_equipo_anterior.md
├─ requirements.txt
└─ data/           datos crudos; NO se sube (está en .gitignore)
   ├─ raw/pte/2023/, raw/pte/2024/   informe del PTE acumulado a diciembre
   ├─ raw/snies/                      snies_matriculados_AAAA_*.xlsx, snies_graduados_AAAA_*.xlsx
   ├─ raw/saber_pro/                  Examen_Saber_Pro_Genericas_AAAA.txt
   └─ interim/                        copias intermedias que generan los scripts
```

## Cómo reproducir la base integrada (OE1)

Requisitos: Python ≥ 3.10, `pandas` y `openpyxl`. Para instalar de una vez todo lo que usan los scripts: `python -m pip install -r requirements.txt`.

1. Ponga los archivos crudos en `data/raw/` como se indica arriba.
   - **PTE:** use el informe *acumulado a diciembre* de cada año. El script reconoce el año por el título de la hoja, así que el nombre del archivo no importa.
   - **SNIES:** descarga directa del portal del MEN. Matriculados: articles-421539 (2023) y 425151 (2024). Graduados: articles-421535 (2023) y 425146 (2024).
   - **Saber Pro:** microdatos de las pruebas genéricas, obtenidos por acceso institucional en DataIcfes.
2. Desde la raíz del repositorio corra:

```bash
python scripts/correr_oe1.py
```

El script corre seis pasos en orden (≈ 1–2 min) y se detiene en el primero que falle:

1. `agregar_saber_pro.py`
2. `extraer_pte_universidades.py`
3. `cargar_snies.py`
4. `cruce_sedes.py`
5. `construir_tabla_maestra.py`
6. `construir_base_integrada.py`

Todo lo que imprime queda en `docs/gobernanza/evidencias/oe1_base_integrada_<fecha>.txt`.

Para comprobar las dos tablas contra los archivos originales corra `python scripts/verificar_oe1.py`. El script recalcula cada cifra por otro camino y responde PASA o FALLA, con la universidad y la columna que no coincide. Su salida queda en `docs/gobernanza/evidencias/verificacion_oe1_<fecha>.txt`.

Las reglas de construcción y el significado de cada columna están en `docs/diccionario_tabla_maestra.md` y `docs/diccionario_base_integrada.md`.

## Cómo reproducir el DEA (OE3) y el Malmquist (OE2)

Se corren después del OE1, desde la raíz del repositorio. Además de `pandas`, requieren `numpy`, `scipy` y `matplotlib`.

```bash
python scripts/oe3_dea_bootstrap.py     # DEA + bootstrap (2.000 réplicas, ≈ 10 min); --B 200 para una prueba rápida
python scripts/oe2_malmquist.py         # índice de Malmquist (segundos)
python scripts/oe3_cobertura_sin_unad.py         # cobertura sin la UNAD (≈ 4 min)
python scripts/caracteristicas_universidades.py  # características por universidad; necesita data/raw
python scripts/oe3_segunda_etapa.py              # Spearman y Mann-Whitney con ajuste de Holm (segundos)
python scripts/oe3_validacion_fuera_muestra.py   # 1.000 sorteos reservando el 20 % de las universidades (≈ 2 min)
python scripts/verificar_oe2_oe3.py     # recalcula todo por otro camino y responde PASA o FALLA (≈ 4 min)
                                        # (si hay data/raw, también recalcula las características desde los crudos)
python scripts/graficos_oe2_oe3.py      # figuras en resultados/figuras/
```

El bootstrap usa una semilla fija (20261011), así que cualquiera que lo corra obtiene los mismos números. `caracteristicas_universidades.py` lee los archivos crudos; quien no los tenga puede usar el `resultados/caracteristicas_universidades.csv` que está en el repositorio y seguir con `oe3_segunda_etapa.py`. La especificación, las columnas y cómo leerlas están en `docs/diccionario_resultados_oe2_oe3.md`.

## Corrección del trabajo previo y tablero

```bash
python scripts/revision_trabajo_previo.py   # cifras de Comunicación Escrita del informe 2025-2; necesita data/raw
python scripts/datos_tablero.py             # datos del tablero interactivo (segundos)
```

`revision_trabajo_previo.py` calcula, con la misma población que la agregación de Saber Pro, la media y la desviación estándar de cada módulo, y las de Comunicación Escrita sin los ceros que no tienen nivel de desempeño. `datos_tablero.py` no estima nada: une las tablas de `resultados/` y les agrega una llave y el nombre corto de cada universidad. El tablero interactivo lee solo esos cuatro archivos y calcula a la vista los promedios, los puestos y las medianas que muestra.

## Fase 1: diagnóstico de las fuentes (septiembre de 2026)

Antes del OE1 se revisaron las fuentes y el código heredado con los scripts de esta tabla. No hacen parte del flujo final (`correr_oe1.py` no los usa) y algunos leen archivos de 2021 y 2022, que quedaron fuera del periodo. Su salida está en `docs/gobernanza/evidencias/`.

| Script | Qué revisa | Evidencia |
|---|---|---|
| `inventario.py` | los archivos del proyecto, con su huella SHA-256 | `inventario_2026-09-16_Eduar.csv`, `inventario_2026-09-17_Anderson.csv` |
| `verificar_herencia.py` | los supuestos del código heredado sobre el PTE y Saber Pro | `verificacion_pte_cuadro4_2026-09-15.txt`, `verificacion_saberpro_2026-09-15.txt`, `verificacion_saberpro_repositorio_2026-09-17.txt` |
| `revisar_snies.py` | qué contiene cada archivo descargado del SNIES, según su título interno | `revision_snies_contenido_2026-09-16.txt` |
| `encabezados_snies.py` | la hoja y la fila del encabezado de los archivos del SNIES 2021–2024 | `encabezados_snies_2026-09-16.txt` |
| `diagnostico_ceros_escrita.py` | los ceros de Comunicación Escrita y su efecto en el puntaje global | `diagnostico_ceros_escrita_2026-09-17_0256.txt` |
| `verificar_llave.py` | la coincidencia de los códigos de institución del SNIES y de Saber Pro, 2023–2024 | `verificacion_llave_2026-09-18_0235.txt` |

De esa fase también son la corrida del scraper heredado (`scraper_snies_log_2026-09-16.txt` y `scraper_snies_manifest_2026-09-16.csv`) y la revisión del Cuadro 7 del PTE de 2024 (`revision_pte_cuadro7_estructura_2026-09-15.txt` y `revision_pte_cuadro7_universidades_2026-09-15.txt`). `traceback_modelo_estrella_2026-09-17.txt` está vacío desde que se subió.

Estos archivos y `docs/uso_ia/inventario_fallos_isabella.md` se borraron en el commit `ffb2454` (8-10-2026) y se restauraron sin cambios el 13-10-2026: el informe, la bitácora y el diccionario de la tabla maestra citan algunos de ellos, y los demás son el respaldo del diagnóstico de septiembre.

## Datos y licencias

Los datos son públicos (PTE – MinHacienda; SNIES – MEN) o de acceso institucional (Saber Pro – ICFES) y no se redistribuyen aquí. Este repositorio publica solo tablas agregadas por institución, sin información de estudiantes. Cuando una sede tiene menos de 5 evaluados en Saber Pro en un año, sus promedios no se publican, porque con tan pocos estudiantes el promedio deja ver el puntaje de una persona; los cálculos sí usan a todos los evaluados (ver `scripts/publicacion.py` y la regla 4 de `docs/diccionario_tabla_maestra.md`). Los valores de esas filas siguen en el historial de git anterior al 20-10-2026.
