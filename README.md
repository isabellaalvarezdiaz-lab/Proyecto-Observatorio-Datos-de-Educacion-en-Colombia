# Observatorio de Datos de Educación en Colombia — eficiencia del gasto en universidades públicas

Consultoría Estadística · Universidad Santo Tomás · 2026-II
Equipo: Isabella Álvarez, Anderson González, Eduar Caicedo · Docente: Javier Mauricio Sierra

Continúa el [proyecto del semestre anterior](https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia), cuyo informe reconoce que no integró sus tres fuentes. Aquí se integran y se mide la eficiencia con la que las universidades públicas convierten los recursos de la Nación en cobertura, graduados y desempeño en Saber Pro.

El periodo es **2023–2024**. Lo fija la intersección de las fuentes: el PTE desagrega el presupuesto por universidad solo desde 2023, y Saber Pro está disponible hasta 2024.

| Objetivo | Qué produce | Dónde |
|---|---|---|
| OE1 · Tabla maestra SNIES + Saber Pro (todas las instituciones) | una fila por institución y año | `resultados/tabla_maestra_2023_2024.csv` |
| OE1 · Base para el DEA: tabla maestra + PTE (universidades públicas) | una fila por universidad y año | `resultados/base_integrada_2023_2024.csv` |
| OE2 · Índice de Malmquist 2023→2024 | cambio de productividad por universidad | pendiente |
| OE3 · DEA con bootstrap (Simar y Wilson, 1998) | eficiencia con intervalos | pendiente |

## Estructura

```text
.
├─ scripts/        código; todo se corre desde la raíz del repositorio
├─ resultados/     tablas agregadas, sin datos de estudiantes (sí se suben)
├─ docs/
│  ├─ diccionario_tabla_maestra.md, diccionario_base_integrada.md
│  ├─ gobernanza/evidencias/   salida de cada corrida, con fecha y hora
│  ├─ uso_ia/                  inventarios de fallos de IA
│  ├─ BITACORA_IA.md
│  └─ Consultoria.pdf          anteproyecto
└─ data/           datos crudos; NO se sube (está en .gitignore)
   ├─ raw/pte/2023/, raw/pte/2024/   informe del PTE acumulado a diciembre
   ├─ raw/snies/                      snies_matriculados_AAAA_*.xlsx, snies_graduados_AAAA_*.xlsx
   ├─ raw/saber_pro/                  Examen_Saber_Pro_Genericas_AAAA.txt
   └─ interim/                        copias intermedias que generan los scripts
```

## Cómo reproducir la base integrada (OE1)

Requisitos: Python ≥ 3.10, `pandas` y `openpyxl`.

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

## Datos y licencias

Los datos son públicos (PTE – MinHacienda; SNIES – MEN) o de acceso institucional (Saber Pro – ICFES) y no se redistribuyen aquí. Este repositorio publica solo tablas agregadas por institución, sin información de estudiantes.
