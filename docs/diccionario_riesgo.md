# Diccionario de resultados — Análisis de riesgo (integración con Teoría del Riesgo)

Dos análisis llevan herramientas del curso de Teoría del Riesgo al observatorio:

1. **Riesgo de cola del puntaje:** VaR y CVaR no paramétricos del puntaje de Saber Pro de cada universidad, por simulación histórica, con intervalos bootstrap y backtesting de Kupiec de 2023 a 2024.
2. **Stress testing del presupuesto:** escenarios sobre el insumo del DEA (la obligación de la Nación) y su efecto en la eficiencia y el orden de las universidades.

No es riesgo financiero. Es la misma herramienta aplicada a otra "pérdida": quedar con un puntaje bajo, en el primer análisis, y perder eficiencia relativa ante un cambio de presupuesto, en el segundo.

Se generan con:

```bash
python scripts/riesgo_puntaje.py     # necesita data/raw/saber_pro (≈ 30 s con 2.000 réplicas)
python scripts/riesgo_stress.py      # necesita data/raw/pte/2024 o --gratuidad-mm (segundos)
python scripts/verificar_riesgo.py   # recalcula todo por otro camino (≈ 20 s)
```

Cada corrida deja su salida en `docs/gobernanza/evidencias/`.

## 1. Riesgo de cola del puntaje

### Especificación

| | |
|---|---|
| Población | Evaluados con código de institución y puntaje global (la misma de `agregar_saber_pro.py`), asignados a las 33 universidades del DEA con `resultados/sedes_por_universidad.csv` |
| Puntaje | `global_c`: el mismo producto "puntaje" del DEA. A quien tiene 0 en Comunicación Escrita se le pone el promedio de sus otros cuatro módulos |
| Nivel | α = 0,05 (VaR y CVaR al 95 %) |
| Tamaño de la cola | k = ⌈α · n⌉ evaluados; la más pequeña tiene 12 (U. del Trópico Americano en 2023 y U. del Pacífico en 2024), por encima de K_MIN = 5 de `publicacion.py` |
| VaR | El k-ésimo puntaje más bajo: cuantil empírico α (`inverted_cdf`). Simulación histórica pura, sin suponer distribución |
| CVaR | Promedio de los k puntajes más bajos (Expected Shortfall) |
| Brecha de cola | Media − CVaR: cuánto se separan los más rezagados del promedio de su universidad |
| Intervalos | Bootstrap no paramétrico de percentiles, 2.000 réplicas por universidad y año, remuestreando evaluados; semilla 20261106 |

### `resultados/riesgo_puntaje.csv`

Una fila por universidad y año (66), más dos filas de referencia por año: `nacional` (todos los evaluados del país) y `33 universidades` (todos los evaluados de las 33).

| Columna | Significado |
|---|---|
| `anio`, `pte_codigo`, `pte_nombre` | Universidad y año; `pte_codigo` vacío en las filas de referencia |
| `n_evaluados` | Evaluados de la universidad en el año |
| `alfa`, `k_cola` | Nivel y número de evaluados en la cola |
| `media` | Puntaje promedio (`global_c`) |
| `var`, `var_ic_inf`, `var_ic_sup` | VaR al 95 % y su intervalo bootstrap del 95 % |
| `cvar`, `cvar_ic_inf`, `cvar_ic_sup` | CVaR al 95 % y su intervalo |
| `brecha_cola` | `media − cvar` |
| `suprimido` | `True` si la cola tuviera menos de K_MIN evaluados (no ocurre) |

### `resultados/riesgo_kupiec.csv` — backtesting 2023 → 2024

El VaR de 2023 se usa como pronóstico para la cohorte de 2024. Si la cola no cambió, la proporción de evaluados de 2024 por debajo del VaR de 2023 debe ser α. La prueba de proporción de fallas de Kupiec:

LR = −2 ln[(1−α)^(n−x) α^x] + 2 ln[(1−x/n)^(n−x) (x/n)^x] ~ χ²(1)

**Empates:** los puntajes son enteros, así que muchos evaluados empatan justo en el VaR. Los que empatan se cuentan con el peso w = (α·n₂₀₂₃ − #{<VaR}₂₀₂₃) / #{=VaR}₂₀₂₃, el mismo en los dos años (cuantil aleatorizado). Así, en 2023 la proporción es exactamente α. `verificar_riesgo.py` comprueba que, si los empates se sortean en vez de ponderarse, cada decisión se mantiene en al menos el 93 % de 500 sorteos.

**Cambio de cohorte:** con cientos de miles de evaluados, Kupiec detecta cambios muy pequeños. Por eso cada universidad se prueba dos veces: contra α (¿cambió su cola?) y contra la tasa nacional de 2024 (¿cambió más o menos que el país?).

| Columna | Significado |
|---|---|
| `var_2023` | VaR al 95 % de 2023 (el pronóstico) |
| `peso_empates` | w de la regla de empates |
| `tasa_2023` | Proporción en 2023 con la regla de empates; igual a α por construcción |
| `n_2024`, `fallas_2024`, `tasa_2024` | Evaluados de 2024, cuántos quedan por debajo del VaR de 2023 (empates ponderados) y su proporción |
| `lr_kupiec`, `p`, `p_holm`, `rechaza_5pct`, `direccion` | Prueba contra α; Holm entre las 33 universidades; "cola peor en 2024" si la tasa supera α |
| `tasa_ref_nacional`, `lr_relativo`, `p_relativo`, `p_relativo_holm`, `rechaza_relativo`, `direccion_relativa` | La misma prueba con la tasa nacional de 2024 como referencia |

### `resultados/riesgo_puntaje_asociaciones.csv`

Spearman exploratorios (33 universidades) entre `var`, `cvar` y `brecha_cola` y el % de evaluados en estratos 1 y 2 y la eficiencia corregida del modelo principal; además, `cvar` frente a `media`. Como en la segunda etapa del OE3, los p-valores son orientativos.

### Resultados principales

- **Referencia nacional 2024:** VaR = 112 y CVaR = 104,3. El 5 % más rezagado del país saca 112 o menos y, en promedio, 104,3.
- **Colas más bajas en 2024 (CVaR):**
  - U. Tecnológica del Chocó: 88,9 [86,5; 91,0]
  - U. de La Guajira: 99,8
  - U. del Pacífico: 99,8
  - U. del Tolima: 101,0
  - UNAD: 101,9
- **La cola sigue al perfil socioeconómico:** el CVaR tiene Spearman de −0,72 (2023) y −0,70 (2024) con el % en estratos 1 y 2, y de +0,79 y +0,80 con la eficiencia corregida del modelo principal.
- **Qué agrega frente al promedio:** el orden por CVaR se parece mucho al orden por media (Spearman 0,95), pero 5 universidades se mueven 5 puestos o más. En 2024, la U. del Valle pasa del puesto 7 por media al 14 por CVaR: su cola es más pesada de lo que sugiere su promedio. El Magdalena (21 → 28) y Cartagena (19 → 26) también bajan. El Trópico Americano sube (28 → 22).
- **La brecha de cola es mayor en las universidades de mejor promedio:** la UIS (50,6), la Nacional (46,6), el Valle (46,1) y Antioquia (45,4). Dentro de ellas hay más distancia entre el promedio y los más rezagados.
- **Backtesting:**
  - La cola de toda la cohorte mejoró un poco: el 4,62 % de los evaluados de 2024 quedó por debajo del VaR nacional de 2023, en vez del 5 %. Es significativo por el tamaño de la muestra, pero pequeño.
  - Contra α, 9 de 33 universidades rechazan con Holm: 7 con la cola mejor y 2 con la cola peor.
  - Contra el cambio nacional, 6 de 33 rechazan:
    - con la cola **peor** que el país: el Tolima (6,54 %) y la Tecnológica del Chocó (6,63 %);
    - con la cola **mejor** que el país: Antioquia (2,51 %), el Cauca (2,33 %), la Popular del Cesar (3,21 %) y el Atlántico (3,47 %).

### Lectura y límites

- El VaR del puntaje describe la cola de los evaluados. **No mide la calidad de la universidad:** sin el Saber 11 de los mismos estudiantes, no separa lo que aporta la universidad del perfil con el que llegan.
- El backtesting es de **un solo paso** (2023 → 2024) y supone que las dos cohortes son comparables. Un rechazo dice que la cola cambió, no por qué cambió.
- La significancia de Kupiec crece con el número de evaluados. Hay que leer la **tasa observada** para juzgar el tamaño del cambio.

## 2. Stress testing del presupuesto

### Especificación

En cada escenario se modifica el insumo (obligación de la Nación de 2024, en miles de millones) y se vuelve a estimar el DEA BCC orientado al producto con `dea.py`, en los tres modelos del OE3. Los productos no cambian. Se usa la eficiencia DEA estimada (δ = 1/φ), no la corregida por bootstrap. El escenario base reproduce exactamente la columna `eficiencia` de `oe3_eficiencia.csv` y `oe3_cobertura_sin_unad.csv`.

| Escenario | Insumo | Para qué |
|---|---|---|
| E0 | Actual | Base |
| E1, E2 | Recorte uniforme del 10 % y del 20 % | Comprobación: el DEA mide eficiencia relativa, así que un cambio igual para todas no cambia ninguna eficiencia |
| E3 | Recorte del 20 % a las universidades del orden nacional | Recorte focalizado |
| E4 | Recorte del 20 % a las del orden territorial | Recorte focalizado |
| E5 | Recorte del 10 % a las 8 menos eficientes de cada modelo | Efecto mecánico de recortar según el ordenamiento |
| E6 | + gratuidad 2024 repartida según la matrícula de pregrado | Limitación principal del informe: el insumo no es todo el presupuesto |
| E7 | + gratuidad 2024 repartida según matrícula de pregrado × % en estratos 1 y 2 | Ídem, con una aproximación a los beneficiarios |

- **Gratuidad 2024:** 2.744,311 mil millones de pesos. Fuente: PTE, Cuadro No. 7 acumulado a diciembre de 2024, rubro «POLÍTICA DE GRATUIDAD DE LA EDUCACIÓN SUPERIOR PÚBLICA», columna Obligación, fila 1758. E6 y E7 son una **cota superior**: la gratuidad también financia instituciones públicas que no son universidades, y el PTE no dice cuánto le tocó a cada una.
- **Orden:** sale de Saber Pro (`caracteristicas_universidades.py`). La U. del Trópico Americano no tiene orden asignado (Saber Pro la registra como no oficial), así que en E3 y E4 no se recorta.

### `resultados/riesgo_stress_resumen.csv`

Una fila por modelo y escenario.

| Columna | Significado |
|---|---|
| `insumo_total_mm` | Suma del insumo en el escenario |
| `eficiencia_media`, `cambio_media` | Eficiencia media y su cambio frente a la base |
| `n_frontera`, `frontera` | Universidades con eficiencia 1 |
| `spearman_con_base` | Correlación del orden con el de la base |
| `cambio_max`, `universidad_cambio_max` | El mayor cambio de eficiencia y de quién es |
| `n_cambian_5_puntos`, `n_cambian_puesto_5` | Universidades que cambian 0,05 o más, y que se mueven 5 puestos o más |

### `resultados/riesgo_stress_universidades.csv`

Una fila por modelo, escenario y universidad: `insumo_base_mm`, `insumo_escenario_mm`, `eficiencia_base`, `eficiencia_escenario`, `cambio`, `puesto_base` y `puesto_escenario`.

### Resultados principales (modelo principal salvo que se diga otra cosa)

- **Recortes uniformes (E1, E2):** ninguna eficiencia cambia, en ningún modelo. Un recorte igual para todas no hace a ninguna más o menos eficiente frente a las demás.
- **Recortes focalizados (E3, E4):** en el principal casi no mueven el orden (Spearman 0,98). En cobertura sí: con un recorte del 20 % a las nacionales, 10 universidades cambian 5 puntos o más y la Distrital baja 0,23, porque las nacionales pasan a producir lo mismo con menos dinero y la frontera se mueve.
- **Recortar a las menos eficientes (E5):** sube su eficiencia sin que produzcan más. La U. del Pacífico pasa de 0,824 a 0,851. Es la razón técnica de la recomendación de no usar el ordenamiento para recortar.
- **Con la gratuidad (E6):** el orden cambia de forma apreciable.
  - **Modelo principal:** Spearman de 0,86 con la base; la frontera pasa de 4 a 9 universidades; la U. de Sucre (puesto 19), el Colegio Mayor de Cundinamarca (14) y Cartagena (11) llegan a la frontera.
  - **Cobertura:** la media pasa de 0,416 a 0,661 y 29 de 33 universidades cambian 5 puntos o más.
  - **Repartida por beneficiarios (E7):** el cambio es menor, pero sigue (Spearman 0,94 en el principal).
  - **Conclusión:** la limitación del insumo no es menor. **Cómo se reparten los recursos que hoy no se ven puede cambiar quién está en la frontera.**

### Lectura y límites

- Cada escenario cambia el insumo con **la misma producción**: pregunta cómo se vería la eficiencia, no predice cómo responderían las universidades a un recorte.
- Los repartos de la gratuidad son supuestos razonables, no el reparto real. Esa información es justamente la que el informe recomienda publicar.
- Se usan las eficiencias estimadas, sin la corrección por sesgo del bootstrap.

## Verificación (`scripts/verificar_riesgo.py`)

Recalcula todo con código escrito aparte:
- el puntaje desde los módulos;
- el VaR y el CVaR por ordenamiento completo;
- los intervalos con otra semilla;
- Kupiec con la verosimilitud binomial y la función gamma incompleta;
- Holm paso a paso;
- los empates por sorteo;
- la gratuidad leída del PTE con openpyxl;
- todas las eficiencias de los escenarios con el programa dual y el método de punto interior.

Resultado: **TODO COINCIDE**. Se plantaron tres errores a propósito (un CVaR, un LR de Kupiec y una eficiencia de un escenario) y el verificador detectó los tres.

En la verificación apareció un dato: en 2023 hay un registro sin Inglés en el que el ICFES contó ese módulo como 0 en el puntaje global. En los demás registros con algún módulo vacío y nota en Escrita (124 en 2023 y 133 en 2024), el ICFES promedia los módulos presentes. No afecta el análisis, que usa el puntaje global oficial.
