# Diccionario de resultados — OE3 (DEA con bootstrap) y OE2 (Malmquist)

Todos parten de `resultados/base_integrada_2023_2024.csv`: 33 universidades con `incluida_dea = True` en cada año. La UAIIN-CRIC queda fuera porque no tiene evaluados en Saber Pro.

Se generan con:

```bash
python scripts/oe3_dea_bootstrap.py     # ≈ 10 min con 2.000 réplicas
python scripts/oe2_malmquist.py         # segundos
python scripts/oe3_cobertura_sin_unad.py        # ≈ 4 min
python scripts/caracteristicas_universidades.py  # necesita data/raw (SNIES y Saber Pro)
python scripts/oe3_segunda_etapa.py             # segundos
python scripts/verificar_oe2_oe3.py     # comprueba todo por otro camino
```

Cada corrida deja su salida en `docs/gobernanza/evidencias/`.

## Especificación

| | OE3 · DEA | OE2 · Malmquist |
|---|---|---|
| Orientación | al producto | al producto |
| Rendimientos | variables (BCC) | constantes (CRS) |
| Insumo | obligación del PTE (miles de millones de pesos corrientes) | ídem; en la versión "real", 2024 dividido por 1,052 |
| Corrección | bootstrap de Simar y Wilson (1998), 2.000 réplicas, semilla 20261011 | — |

Para la versión "real" del Malmquist se usa 1,052, que es la variación anual del IPC a diciembre de 2024 (5,20 %). Fuente: DANE, Comunicado de prensa IPC diciembre 2024, p. 1, <https://www.dane.gov.co/files/operaciones/IPC/dic2024/cp-IPC-dic2024.pdf>.

| Modelo | Productos | Para qué |
|---|---|---|
| `principal` | matrícula promedio, graduados, puntaje `global_c` | Cobertura y calidad juntas, como se planteó |
| `cobertura` | matrícula promedio, graduados | Cobertura sola |
| `cobertura_sin_unad` | matrícula promedio, graduados; 32 universidades (sin la UNAD) | Cobertura sin la universidad que más mueve la frontera |

El modelo de cobertura existe por esto: el puntaje varía poco entre universidades (coeficiente de variación ≈ 0,08; la mejor tiene 1,5 veces el de la peor). En un DEA radial, que expande todos los productos en la misma proporción, el puntaje limita la expansión y deja las brechas de matrícula y graduados como holguras. Galvis-Aponte (2015) también reporta por separado la eficiencia en cobertura y en calidad.

## `resultados/oe3_eficiencia.csv`

Una fila por modelo, año y universidad.

| Columna | Significado |
|---|---|
| `eficiencia` | δ = 1/φ ∈ (0, 1]. 1 = en la frontera. 0,80 = produce el 80 % de lo que logran sus pares con el mismo presupuesto, es decir, podría multiplicar sus productos por 1/0,80 = 1,25 |
| `eficiencia_corregida` | Eficiencia corregida por el sesgo del DEA con el bootstrap. Es menor o igual que la original, porque la frontera estimada con la muestra queda por debajo de la verdadera |
| `ic95_inf`, `ic95_sup` | Intervalo de confianza del 95 % de la eficiencia |
| `sesgo_phi` | Sesgo estimado en la escala φ |
| `en_frontera` | Eficiencia original = 1 |
| `pares` | Universidades de la frontera con las que se compara, con su peso λ |
| `<producto>_actual`, `<producto>_meta` | Valor actual y meta: lo que lograría si funcionara como la combinación de sus pares. Incluye la expansión radial y las holguras |

## `resultados/oe3_deja_uno_fuera.csv`

Se saca una por una cada universidad de la frontera y se vuelve a calcular la eficiencia de las demás. Solo hace falta con las de la frontera, porque una universidad ineficiente no define la frontera y quitarla no cambia la eficiencia de nadie.

| Columna | Significado |
|---|---|
| `sale` | Universidad que se saca |
| `cambio_medio`, `cambio_max` | Cambio de la eficiencia de las demás (en proporción: 0,05 = 5 puntos) |
| `universidad_cambio_max` | La que más cambia |
| `n_cambian_mas_5_puntos` | Cuántas suben más de 5 puntos |
| `spearman_ranking` | Correlación de Spearman entre el orden de las universidades con y sin ella. Las universidades de la frontera cuentan como empatadas en 1: las eficiencias se redondean a 6 decimales antes de ordenar, porque el solver deja diferencias de 1e-10 que romperían el empate al azar |

## `resultados/oe3_sensibilidad.csv`

Modelo principal con `global_b` (puntaje sin los estudiantes con 0 en Escrita) en lugar de `global_c`.

## `resultados/oe2_malmquist.csv`

Una fila por modelo, versión (nominal o real) y universidad.

| Columna | Significado |
|---|---|
| `malmquist` | M > 1 = la productividad mejoró entre 2023 y 2024; M < 1 = retroceso de productividad |
| `cambio_eficiencia` | EC: cuánto se acercó (> 1) o se alejó (< 1) la universidad de la frontera |
| `cambio_tecnologico` | TC: cuánto se movió la frontera completa (> 1 = las mejores producen más con lo mismo) |
| `D23_23`, `D23_24`, `D24_23`, `D24_24` | Distancias de Shephard con rendimientos constantes: `Dxx_yy` = universidad en el año yy evaluada contra la frontera del año xx |

M = EC × TC. Con un solo insumo y rendimientos constantes, deflactar multiplica M y TC por 1,052 en todas las universidades y no cambia EC ni el orden entre universidades.

## `resultados/oe3_cobertura_sin_unad.csv`

Mismas columnas que `oe3_eficiencia.csv`, con `modelo = cobertura_sin_unad`. Mismo método, misma semilla.

Por qué existe: en `oe3_deja_uno_fuera.csv`, sacar a la UNAD del modelo de cobertura sube más de 5 puntos la eficiencia de 25 de 32 universidades en 2023 y de 29 de 32 en 2024. La UNAD tiene el 100 % de su matrícula a distancia o virtual y fija una frontera que ninguna otra alcanza. Sin ella, las demás se comparan entre sí.

Ojo: las 32 restantes **no** son todas presenciales. Varias tienen una parte grande de su matrícula a distancia o virtual (columna `pct_mat_distancia_virtual` de `caracteristicas_universidades.csv`).

## `resultados/caracteristicas_universidades.csv`

Una fila por universidad y año (las 34 de la base integrada). Todas las variables salen de columnas de los archivos originales; ninguna se asigna a mano. Se genera con `scripts/caracteristicas_universidades.py`, que necesita `data/raw/snies` y `data/raw/saber_pro`.

**Sede principal.** Es la sede cuyo código coincide con su IES PADRE en el SNIES. Si ninguna coincide (UFPS Ocaña), es la de mayor matrícula.

| Columna | Origen |
|---|---|
| `acreditada_institucional` | SNIES matriculados, columna `IES ACREDITADA` de la sede principal (`Si` → True) |
| `pct_mat_prog_acreditados` | % de la matrícula (suma de los dos semestres) en filas con `PROGRAMA ACREDITADO` = `Si` |
| `pct_mat_distancia_virtual` | % de la matrícula con `MODALIDAD` = A distancia, Virtual, Virtual-A distancia o Virtual-Dual. Presencial-Virtual e Híbrida (Presencial-Virtual) no se cuentan; en las universidades públicas son 29 filas en 2023 y 56 en 2024 |
| `pct_mat_posgrado` | % de la matrícula con `NIVEL ACADÉMICO` = Posgrado |
| `n_departamentos_oferta` | número de valores distintos de `DEPARTAMENTO DE OFERTA DEL PROGRAMA` |
| `departamento_domicilio`, `domicilio_bogota` | `DEPARTAMENTO DE DOMICILIO DE LA IES` de la sede principal |
| `origen_saber_pro`, `orden` | `inst_origen` de Saber Pro de la sede principal. OFICIAL NACIONAL → `nacional`; OFICIAL DEPARTAMENTAL u OFICIAL MUNICIPAL → `territorial`; otro valor → vacío. Quedan vacías la U. Internacional del Trópico Americano (Saber Pro la registra como `NO OFICIAL - FUNDACIÓN`) y la UAIIN-CRIC (sin evaluados) |
| `log_matricula` | logaritmo natural de `mat_total_prom` (tamaño) |
| `millones_por_estudiante` | `obligacion` / `mat_total_prom` / 10⁶, pesos corrientes |
| `pct_ceros_escrita` | igual que en la base integrada |
| `n_evaluados_saber_pro` | evaluados en Saber Pro de todas las sedes (registros con código de institución y puntaje global, como en `agregar_saber_pro.py`). Coincide con `n_evaluados` de la base integrada |
| `pct_estrato_1_2` | % de evaluados en estratos 1 y 2 (`fami_estratovivienda`), sobre quienes reportan estrato 1 a 6. "Sin Estrato" y las respuestas vacías no entran en el denominador |
| `pct_madre_hasta_secundaria` | % de evaluados cuya madre llegó como máximo a secundaria completa (`fami_educacionmadre`: Ninguno, Primaria incompleta o completa, Secundaria incompleta o completa), sobre quienes reportan un nivel. "No sabe", "No Aplica" y vacías no entran |

Las cifras de los dos párrafos siguientes están en la evidencia que deja `caracteristicas_universidades.py` (`docs/gobernanza/evidencias/caracteristicas_universidades_<fecha>.txt`).

**Datos faltantes del perfil socioeconómico.** La mediana entre universidades es 4,7 % sin estrato y 3,4 % sin educación de la madre en 2023 (3,0 % y 2,8 % en 2024). El caso más alto es la Tecnológica del Chocó: 14,8 % sin estrato en 2023 y 7,6 % en 2024.

**Por qué no se usa el índice socioeconómico del ICFES** (`estu_inse_individual`). Su relación con las otras dos variables cambia mucho entre años:
- con el % en estratos 1 y 2, Spearman −0,54 en 2023 y −0,95 en 2024;
- con el % de madres hasta secundaria, −0,83 y −0,56.

Además, el orden de las universidades por INSE se parece poco entre 2023 y 2024 (Spearman 0,69). Por el estrato es 0,99 y por la educación de la madre, 0,92. Esto sugiere que el índice se construyó distinto cada año, pero no se encontró la documentación del ICFES que lo confirme. Por eso se prefirieron las dos respuestas directas del cuestionario.

## `resultados/oe3_segunda_etapa.csv`

Segunda etapa **exploratoria**: qué características se asocian con la eficiencia corregida. Con 32–33 universidades no se estima una regresión; se usan pruebas no paramétricas.

- Variables continuas: correlación de Spearman.
- Binarias: Mann-Whitney de dos colas. Es exacta si un grupo tiene 8 o menos universidades y no hay empates; si no, aproximación normal.
- Hay dos familias de pruebas, cada una con su propio ajuste de Holm dentro de cada modelo y año (columna `familia`):
  - `institucional`: las 10 características de la universidad (7 continuas y 3 binarias);
  - `socioeconomica`: el % en estratos 1 y 2 y el % de madres hasta secundaria (2 pruebas). Responde al compromiso del anteproyecto de interpretar las eficiencias bajas considerando variables regionales y socioeconómicas (sección 6, riesgos éticos).

Una fila por modelo, año y variable.

| Columna | Significado |
|---|---|
| `valor` | rho de Spearman o U de Mann-Whitney (del grupo A) |
| `efecto` | escala de −1 a 1 para comparar: rho en las continuas; en las binarias, correlación biserial de rangos 2U/(n_A·n_B) − 1, positiva si el grupo A es más eficiente |
| `p`, `p_holm` | p-valor sin ajustar y ajustado por Holm |
| `mecanica` | True si la variable se construye con el insumo o con un producto del modelo, así que la asociación es aritmética y no un hallazgo. Se marcan `millones_por_estudiante` en todos los modelos y `log_matricula` en los de cobertura |
| `grupo_a`, `mediana_a`, `grupo_b`, `mediana_b` | en las binarias, los grupos con su tamaño y la mediana de la eficiencia corregida |

Cómo leerla:

- Las eficiencias DEA de una misma muestra no son independientes entre sí (dependen de la misma frontera), así que los p-valores son **orientativos**.
- Ninguna asociación es causal.
- Algunas variables no se construyen con los productos, pero están muy correlacionadas con uno de ellos. Entonces su asociación con la eficiencia repite, en buena parte, la de ese producto. El script imprime esas correlaciones al final de su evidencia (bloque "Contexto").
  - En el modelo principal, el % de matrícula en programas acreditados, el % en posgrado y el % de ceros en Escrita se mueven con el puntaje `global_c`.
  - Leerlas así: las universidades con marcadores de calidad más altos (programas acreditados, posgrado, menos ceros en Escrita) son las que el modelo principal ubica más cerca de la frontera. Eso no aísla un efecto propio de cada variable.
- Lo mismo pasa con el perfil socioeconómico. El % en estratos 1 y 2 tiene Spearman −0,77 (2023) y −0,74 (2024) con `global_c` (bloque "Contexto" de la evidencia de `oe3_segunda_etapa.py`). Entonces, en el modelo principal, una eficiencia baja puede reflejar en parte el perfil con el que llegan los estudiantes, y no solo la gestión de la universidad.

## `resultados/oe3_contexto_menos_eficientes.csv`

Para cada modelo y año, las 5 universidades con menor eficiencia corregida y su perfil. Es el contexto que pide el anteproyecto para leer las eficiencias bajas.

| Columna | Significado |
|---|---|
| `puesto_eficiencia` | 1 = la menos eficiente |
| `n` | universidades en el modelo ese año |
| `pct_estrato_1_2`, `puesto_estrato_1_2` | % en estratos 1 y 2, y su puesto entre las `n` (1 = el mayor %) |
| `pct_madre_hasta_secundaria`, `puesto_madre_hasta_sec` | ídem para la educación de la madre |
| `mediana_estrato_1_2`, `mediana_madre_hasta_sec` | medianas de las `n` universidades del modelo ese año, como referencia |
| `departamento_domicilio`, `pct_mat_distancia_virtual` | contexto regional y de modalidad |

## `resultados/oe3_validacion_resumen.csv` y `oe3_validacion_universidades.csv`

Validación fuera de muestra, pedida por el docente para comprobar que el modelo funciona con datos que no usó. La produce `scripts/oe3_validacion_fuera_muestra.py`. En cada sorteo se reserva cerca del 20 % de las universidades (7 de 33; 6 de 32 sin la UNAD), la frontera se estima con las demás y cada reservada se evalúa contra ella con el mismo DEA. Se hacen 1.000 sorteos por modelo y año con semilla fija; con 33 universidades, los modelos principal y de cobertura usan los mismos sorteos.

Cómo leerla:

- Sacar universidades solo puede bajar la frontera, así que la eficiencia fuera de muestra nunca es menor que la del modelo completo. Lo que interesa es cuánto sube y si el orden se mantiene.
- Una universidad cuyos pares siguen todos en la muestra no cambia. Por eso la mayoría de las evaluaciones no cambia nada.
- Las universidades de la frontera, al quedar reservadas, quedan en la frontera de entrenamiento o por encima (eficiencia ≥ 1).
- Si la reservada tiene menos presupuesto que todas las de entrenamiento, no se puede evaluar con rendimientos variables ("fuera del soporte"). Solo les pasa a las tres de menor presupuesto: U. del Trópico Americano, U. del Pacífico y U. de Cundinamarca.
- Se compara la eficiencia original, no la corregida: repetir el bootstrap en cada sorteo costaría 2.000 réplicas por sorteo.

`oe3_validacion_resumen.csv` (una fila por modelo y año):

| Columna | Significado |
|---|---|
| `n`, `reservadas`, `repeticiones`, `semilla` | universidades del modelo, reservadas por sorteo, número de sorteos y semilla |
| `evaluaciones`, `fuera_soporte` | evaluaciones hechas (reservadas × sorteos) y las que no se pudieron hacer |
| `interior_evaluaciones` | evaluaciones de universidades que no están en la frontera del modelo completo |
| `interior_sin_cambio_pct` | % de esas evaluaciones en las que la eficiencia no cambia (diferencia < 10⁻⁶) |
| `interior_cambio_medio`, `interior_cambio_p95` | cambio medio y percentil 95 del cambio (eficiencia fuera de muestra − completa) |
| `interior_parecen_eficientes_pct` | % de esas evaluaciones en las que la universidad parece eficiente (eficiencia ≥ 1) |
| `frontera_evaluaciones` | evaluaciones de universidades de la frontera |
| `spearman_mediana`, `spearman_p05` | Spearman, en cada sorteo, entre la eficiencia fuera de muestra y la completa de las reservadas: mediana y percentil 5 entre los sorteos |
| `spearman_agregado`, `universidades_agregado` | Spearman entre la mediana de la eficiencia fuera de muestra de cada universidad y su eficiencia completa, y cuántas universidades entran |

`oe3_validacion_universidades.csv` (una fila por modelo, año y universidad): `eficiencia` (modelo completo), `en_frontera`, `veces_reservada`, `veces_fuera_soporte`, `eficiencia_fuera_mediana`, `cambio_medio`, `sin_cambio_pct` y `parece_eficiente_pct` (este último solo para las que no están en la frontera).

`verificar_oe2_oe3.py` (sección 11) repite todos los sorteos con el programa dual, comprueba las propiedades de arriba y recalcula cada indicador.

## `resultados/revision_trabajo_previo.csv`

Cifras para la corrección anónima de las conclusiones del trabajo previo (informe final del semestre 2025-2, `docs/informe_final.md` de su repositorio, línea 183). Las produce `scripts/revision_trabajo_previo.py` con los microdatos de Saber Pro y la misma población que `agregar_saber_pro.py` (registros con código de institución y puntaje global). Una fila por año, módulo y población.

| Columna | Significado |
|---|---|
| `anio` | 2023 o 2024 |
| `modulo` | módulo genérico de Saber Pro |
| `poblacion` | `todos los evaluados`, o `sin los ceros en Escrita` (solo en Comunicación escrita) |
| `n` | evaluados con puntaje en el módulo |
| `media`, `de` | media y desviación estándar del puntaje del módulo |

El % de evaluados con 0 en Escrita es 1 − n(sin los ceros) / n(todos) en Comunicación escrita. Ninguno de esos ceros tiene nivel de desempeño (lo imprime la evidencia `revision_trabajo_previo_<fecha>.txt`), así que son pruebas sin calificar. Los años 2021 y 2022 del trabajo previo no se revisan: el proyecto no tiene esos microdatos.

## `resultados/tablero/*.json`

Datos del tablero interactivo. `scripts/datos_tablero.py` los arma desde los CSV de `resultados/` sin cambiar ningún valor numérico: agrega una llave `id` y el nombre corto de cada universidad (la misma función de las figuras) y renombra algunas columnas, como se indica abajo. Cada archivo es una lista de filas en JSON.

| Archivo | Una fila por | Llave `id` | Viene de |
|---|---|---|---|
| `universidades.json` | modelo, año y universidad | `modelo-año-código PTE` | `oe3_eficiencia.csv` y `oe3_cobertura_sin_unad.csv` |
| `caracteristicas.json` | año y universidad (las 33 del DEA) | `año-código PTE` | `base_integrada_2023_2024.csv` y `caracteristicas_universidades.csv` |
| `malmquist.json` | modelo, versión y universidad | `modelo-versión-código PTE` | `oe2_malmquist.csv` |
| `segunda_etapa.json` | modelo, año y variable | `modelo-año-variable` | `oe3_segunda_etapa.csv` |

En `universidades.json`, `matricula_*`, `graduados_*` y `puntaje_*` son las columnas `mat_total_prom_*`, `grad_total_*` y `global_c_*` de `oe3_eficiencia.csv`, y `pares` lleva los nombres cortos con el peso de cada par. Los promedios, los puestos y las medianas que muestra el tablero no están en estos archivos: los calcula el tablero, y quien lo consulte puede ver cada fórmula.

## Limitaciones de lectura

- Con 33 universidades, los intervalos son anchos. Compare universidades por sus intervalos, no solo por el valor puntual.
- En el DEA BCC orientado al producto, quedan en la frontera por construcción la universidad con menor insumo y la de mayor valor en cada producto. Su 100 % no significa lo mismo que el de una universidad mediana.
- El insumo es la obligación que el PTE registra en la entidad de cada universidad (2257xx). No incluye los recursos propios ni los que la Nación gira a las instituciones públicas desde el Ministerio de Educación sin desagregar por universidad. En el Cuadro No. 7 de diciembre de 2024, por ejemplo, la gratuidad tuvo obligaciones por 2.744 mil millones (fila 1758) y la concurrencia pensional por 475 mil millones (fila 1729), frente a 6.155 mil millones en las 34 universidades. Las universidades con más recursos fuera del insumo parecen más eficientes de lo que son; el análisis deja uno fuera mide cuánto pesa la UNAD.
- El bootstrap de Simar y Wilson (1998) es homogéneo: supone que la ineficiencia se distribuye igual en todas las universidades. Simar y Wilson (2000) proponen una versión heterogénea, que no se implementó.
- El Malmquist no tiene intervalos: el método original de bootstrap para Malmquist (Simar y Wilson, 1999) no se consiguió en texto completo.
