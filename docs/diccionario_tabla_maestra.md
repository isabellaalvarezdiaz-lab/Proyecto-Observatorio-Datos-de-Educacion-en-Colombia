# Diccionario de datos — `resultados/tabla_maestra_2023_2024.csv` (OE1)

Tabla maestra SNIES + Saber Pro. Tiene **todas** las instituciones de educación superior, públicas y privadas, con una fila por código de institución y año: 654 filas y 330 códigos distintos.

Es el recurso general del observatorio. La base para el DEA (`resultados/base_integrada_2023_2024.csv`) se construye a partir de ella.

El PTE no está en esta tabla, porque solo reporta presupuesto de las universidades públicas: en las demás filas quedaría vacío por diseño.

Se construye con `python scripts/correr_oe1.py` (paso 5, `scripts/construir_tabla_maestra.py`).

## Llave

`cod_institucion` = `CÓDIGO DE LA INSTITUCIÓN` (SNIES) = `inst_cod_institucion` (Saber Pro).

La unión es externa: si una institución está en una sola fuente, igual queda en la tabla, marcada con `en_snies` / `en_saber_pro`.

Cobertura de la llave (salida de la corrida del 08-10-2026; coincide con `docs/gobernanza/evidencias/verificacion_llave_2026-09-18_0235.txt`):

| Año | Códigos en Saber Pro | Con par en SNIES | % de códigos | % de evaluados |
|---|---|---|---|---|
| 2023 | 265 | 262 | 98,9 % | 99,96 % |
| 2024 | 270 | 270 | 100,0 % | 100,00 % |

En 2023 hay tres códigos de Saber Pro sin par en SNIES, todos privados, con 89 evaluados en total:
- 2809 Corporación Universitaria Tecnológica de Bolívar (1 evaluado)
- 2824 Corporación Universitaria de Colombia Ideas (35)
- 9931 Fundación Universitaria Patricio Symes (53)

## Variables

| Columna | Descripción | Fuente | Unidad |
|---|---|---|---|
| `cod_institucion` | Código de institución (sede o seccional) | SNIES / Saber Pro | — |
| `anio` | Año | — | — |
| `nombre` | Nombre en SNIES; si no está en SNIES, el de Saber Pro | SNIES | — |
| `ies_padre` | Código de la institución principal de la que depende la sede | SNIES, columna IES PADRE | — |
| `tipo_ies` | Principal o Seccional | SNIES, TIPO IES | — |
| `sector` | Oficial o Privado | SNIES, SECTOR IES | — |
| `caracter` | Universidad, Institución universitaria, etc. | SNIES, CARÁCTER IES | — |
| `pte_codigo` | Entidad del PTE a la que pertenece la sede (solo las 34 universidades públicas del PTE; vacío en el resto) | `resultados/sedes_por_universidad.csv` | — |
| `en_snies`, `en_saber_pro` | Si la institución aparece en cada fuente ese año | — | lógico |
| `mat_pregrado_s1`, `_s2`, `_prom` | Matriculados de pregrado en el semestre 1, el semestre 2 y su promedio | SNIES, MATRICULADOS | estudiantes |
| `mat_posgrado_s1`, `_s2`, `_prom` | Ídem para posgrado | SNIES | estudiantes |
| `mat_total_prom` | `mat_pregrado_prom + mat_posgrado_prom` | — | estudiantes |
| `grad_pregrado`, `grad_posgrado`, `grad_total` | Graduados del año (se suman los dos semestres) | SNIES, GRADUADOS | personas |
| `nombre_saber_pro` | Nombre de la institución en Saber Pro (incluye la ciudad) | Saber Pro | — |
| `n_evaluados` | Estudiantes evaluados | `resultados/saber_pro_institucion_anio.csv` | estudiantes |
| `n_ceros_escrita`, `pct_ceros_escrita` | Evaluados con 0 en Comunicación Escrita | ídem | estudiantes / % |
| `global_a`, `global_b`, `global_c` | Puntaje global promedio en sus tres versiones. `global_c` es la recomendada; ver `docs/diccionario_base_integrada.md` | ídem | puntos |

Si la institución no está en una fuente, las columnas de esa fuente quedan vacías: no se rellenan con cero.

## Reglas

1. **Matrícula:** no se suman los dos semestres, porque un estudiante matriculado en ambos se contaría dos veces.
2. **Graduados:** sí se suman, porque son eventos distintos.
3. **Una fila por código de sede.** Para hablar de una universidad completa hay que sumar sus sedes. Por ejemplo, la Universidad Nacional tiene 7 códigos con IES PADRE 1101. Para las universidades públicas del PTE, esa suma ya está hecha en la base integrada.
