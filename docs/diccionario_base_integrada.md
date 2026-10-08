# Diccionario de datos — `resultados/base_integrada_2023_2024.csv`

Una fila por universidad pública (entidad del PTE, Cuadro No. 7) y año: 34 universidades × 2 años = 68 filas. Hay 66 filas utilizables en el DEA (`incluida_dea = True`).

Sale de la tabla maestra (`resultados/tabla_maestra_2023_2024.csv`, ver `docs/diccionario_tabla_maestra.md`): se toman las sedes de las universidades del PTE, se suman por universidad y se les une el presupuesto. Se construye con `python scripts/correr_oe1.py` desde la raíz del repositorio. Cada corrida deja su evidencia en `docs/gobernanza/evidencias/oe1_base_integrada_AAAA-MM-DD_HHMM.txt`.

## Fuentes

| Fuente | Archivo en `data/raw/` | Ubicación dentro del archivo | Corte |
|---|---|---|---|
| PTE 2023 | `pte/2023/` (cualquier nombre) | hoja "Cuadro No. 7", filas de entidades `2257xx` | "Acumulada a Diciembre de 2023" (título de la hoja) |
| PTE 2024 | `pte/2024/` (cualquier nombre) | ídem | "Acumulada a Diciembre de 2024" |
| SNIES matriculados | `snies/snies_matriculados_AAAA_*.xlsx` (articles-421539 y 425151) | hoja "1.", encabezado en la fila 6 | 31 may 2024 / 31 may 2025 (pie de página) |
| SNIES graduados | `snies/snies_graduados_AAAA_*.xlsx` (articles-421535 y 425146) | ídem | ídem |
| Saber Pro | `saber_pro/Examen_Saber_Pro_Genericas_AAAA.txt` | separador `;` | periodos 20231–20234 y 20241–20244 |

El script del PTE identifica el año **por el título de la hoja**, no por el nombre del archivo ni por la carpeta. Si un archivo está en la carpeta de un año pero su título corresponde a otro, lo marca con `[REVISAR]`.

Cada fila de `resultados/pte_universidades_2023_2024.csv` guarda el archivo, la hoja y la fila de Excel de donde sale la cifra.

## Variables

| Columna | Descripción | Fuente / cálculo | Unidad |
|---|---|---|---|
| `pte_codigo` | Código de la entidad en el PTE (225701–225734). **No** es el código SNIES | PTE, Cuadro No. 7 | — |
| `anio` | Año | — | — |
| `pte_nombre` | Nombre de la entidad en el PTE | PTE, Cuadro No. 7 | — |
| `apropiacion`, `compromiso`, `obligacion`, `pago` | Ejecución del PGN de la universidad (fila total de la entidad) | PTE, Cuadro No. 7, columnas B–E | pesos corrientes |
| `art86_obligacion` | Obligación del rubro "A universidades para funcionamiento Ley 30 de 1992 artículo 86" | PTE, Cuadro No. 7, fila del rubro dentro del bloque de la entidad | pesos corrientes |
| `*_mm` | Las mismas cifras del PTE en miles de millones | columna / 10⁹ | miles de millones de pesos corrientes |
| `mat_pregrado_s1`, `mat_pregrado_s2`, `mat_pregrado_prom` | Matriculados de pregrado en el semestre 1, el semestre 2 y su promedio | SNIES, columna MATRICULADOS, NIVEL ACADÉMICO = Pregrado, suma de sedes | estudiantes |
| `mat_posgrado_s1`, `_s2`, `_prom` | Ídem para posgrado | SNIES | estudiantes |
| `mat_total_prom` | `mat_pregrado_prom + mat_posgrado_prom` | — | estudiantes |
| `n_sedes_snies` | Códigos de institución SNIES sumados | ver `resultados/sedes_por_universidad.csv` | — |
| `grad_pregrado`, `grad_posgrado`, `grad_total` | Graduados del año (se suman los dos semestres) | SNIES, columna GRADUADOS | personas |
| `n_evaluados` | Estudiantes evaluados en Saber Pro | tabla maestra, suma de sedes | estudiantes |
| `n_sedes_saber_pro` | Sedes con al menos un evaluado | ídem | — |
| `n_ceros_escrita`, `pct_ceros_escrita` | Evaluados con 0 en Comunicación Escrita | ídem | estudiantes / % |
| `global_a` | Promedio del `punt_global` del ICFES. **Incluye los ceros de Escrita** | promedio de sedes ponderado por evaluados | puntos — solo de referencia |
| `global_b` | Promedio del `punt_global` excluyendo a quienes tienen 0 en Escrita | ponderado por evaluados sin cero | puntos — sensibilidad |
| `global_c` | `punt_global`; para quien tiene 0 en Escrita, el promedio de sus otros 4 módulos | ponderado por evaluados | puntos — **usar en el DEA** |
| `incluida_dea` | Tiene insumo, matrícula, graduados y evaluados en Saber Pro | — | lógico |
| `nota` | Observación sobre casos particulares | — | texto |

Las definiciones de `global_a`, `global_b` y `global_c` están en `scripts/agregar_saber_pro.py`. Agregar los promedios de sede, que vienen redondeados a 2 decimales, produce una diferencia menor que 0,005 puntos frente a calcularlo desde los microdatos (verificado el 07-10-2026).

## Reglas de construcción

1. **Una universidad del PTE corresponde a varias sedes.** El PTE reporta la universidad completa; Saber Pro y SNIES tienen un código por sede. `scripts/cruce_sedes.py` asigna las sedes en tres pasos:
   - por nombre en Saber Pro;
   - por `IES PADRE` en SNIES;
   - en el caso de UAIIN-CRIC, por nombre en SNIES.

   El resultado queda en `resultados/sedes_por_universidad.csv`: 52 sedes, todas del sector oficial en SNIES. La Universidad Nacional tiene 7 códigos: 1101–1104, más 1125, 1126 y 9933, que solo se encuentran por `IES PADRE`. El 9933 tiene 74 evaluados en 2024.
2. **UFPS Cúcuta y UFPS Ocaña van separadas**, porque el PTE las financia aparte, aunque en SNIES Ocaña (1210) sea seccional de Cúcuta (IES PADRE 1209).
3. **UAIIN-CRIC (225734)** está en el PTE y en SNIES (código 9929), pero no tiene evaluados en Saber Pro 2023–2024. Queda fuera del DEA.
4. **Universidad del Trópico Americano (225733):** Saber Pro la rotula "no oficial – fundación"; el pie de página de SNIES aclara que pertenece al sector oficial desde 2021.
5. **Escuela Naval Almirante Padilla (9105)** es oficial en SNIES pero no está entre las 34 entidades del PTE. No entra.
6. **Matrícula:** no se suman los dos semestres, porque un estudiante matriculado en ambos se contaría dos veces.
7. **Pesos corrientes.** Para el Malmquist hay que deflactar el insumo (ver pendientes).

## Decisiones pendientes del equipo

- Medida del insumo: obligación (por defecto en la base), compromiso o apropiación.
- Matrícula: promedio de semestres (por defecto), semestre 1 o semestre 2.
- Deflactor del insumo para comparar 2023 con 2024: IPC del DANE (fuente por citar).
- Tratamiento de UNAD, Distrital y Militar Nueva Granada (ver isotonicidad abajo).

## Verificación de isotonicidad (Spearman, insumo = obligación)

| Año | Conjunto | Matrícula | Graduados | Puntaje (`global_c`) |
|---|---|---|---|---|
| 2023 | 33 universidades | 0,65 | 0,59 | 0,52 |
| 2023 | sin UNAD, Distrital, Militar (30) | 0,80 | 0,71 | 0,71 |
| 2024 | 33 universidades | 0,68 | 0,65 | 0,52 |
| 2024 | sin UNAD, Distrital, Militar (30) | 0,81 | 0,76 | 0,72 |

Todas las correlaciones son positivas: la relación insumo–producto se cumple, y se fortalece al retirar esos tres casos. En 2024, la UNAD tiene 1.308 matriculados por cada mil millones de pesos de la Nación; la Distrital, 388; la Militar, 295; la mediana es 111.
