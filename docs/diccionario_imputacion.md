# Imputación de los ceros de Comunicación Escrita por perfiles similares

Script: `scripts/imputar_escrita.py`. Verificador: `scripts/verificar_imputacion.py`. Evidencia: `docs/gobernanza/evidencias/imputacion_escrita_*.txt` y `verificacion_imputacion_*.txt`.

## Por qué

Quien tiene 0 en Escrita tiene el nivel de desempeño vacío: el cero no es un puntaje, es un dato faltante (`diagnostico_ceros_escrita.py`). Hasta ahora el proyecto usa `global_c`, que para esos evaluados toma el promedio de sus otros cuatro módulos. Eso equivale a suponer que su Escrita habría sido igual a ese promedio. El docente sugirió imputar el faltante con estudiantes de perfil similar; este análisis lo hace y mide si cambia las conclusiones.

## Método

| Paso | Detalle |
|---|---|
| Población | La misma de `agregar_saber_pro.py`: evaluados con código de institución y puntaje global, 2023 y 2024 |
| Modelo de perfil | Mínimos cuadrados: Escrita ≈ b0 + b1·Ciudadanas + b2·Inglés + b3·Lectura + b4·Razonamiento + b5·[2024], ajustado con los 485.580 evaluados con Escrita > 0 y los otros cuatro módulos completos |
| Perfiles similares (PMM) | Para cada evaluado con cero se buscan los 5 evaluados con Escrita observada cuya predicción es la más cercana a la suya, y se toma al azar el puntaje real de uno de ellos (*predictive mean matching*) |
| Imputación múltiple | 5 imputaciones con semillas distintas (semilla base 20261106); los agregados se promedian |
| `global_d` | Promedio de los cinco módulos con la Escrita imputada. Para quien no tiene cero, `global_d` = puntaje global oficial |
| Sin perfil completo | 61 evaluados con cero a los que además les falta otro módulo se quedan con `global_c` |

PMM, y no la predicción sola, porque la predicción le daría a todos el promedio condicional y achicaría la cola, que es justamente lo que mide el CVaR.

## Validación

En una partición del 20 % de los evaluados con Escrita (97.116, que no entran al ajuste):

| Método | MAE | RMSE | Sesgo |
|---|---|---|---|
| Supuesto de `global_c` (Escrita = promedio de los otros cuatro) | 24,76 | 31,85 | +3,69 |
| Modelo lineal (el que usa el PMM) | 19,75 | 25,65 | +0,24 |
| Gradient boosting (referencia) | 19,67 | 25,59 | +0,24 |
| KNN con 20 vecinos (referencia) | 20,24 | 26,30 | +0,15 |

- El modelo lineal predice casi igual que el boosting y mejor que KNN.
- Se guarda en `modelos/imputador_escrita.json`: coeficientes, cuantiles de los residuos y métricas, 1,4 KB, sin ningún registro individual.
- Un KNN guardado con pickle o joblib llevaría dentro los datos de entrenamiento, es decir, los microdatos.
- El R² en validación es 0,096: Escrita se predice mal a nivel individual. Sirve para agregados y como imputación, no para juzgar a un estudiante.

## Resultados

- A los evaluados con cero, el modelo les predice en promedio 139,8 en Escrita, frente a 132,7 que supone `global_c`. El supuesto de `global_c` los subestimaba.
- En los promedios por universidad, el efecto es pequeño. En el nacional, el global pasa de 146,22 a 146,31 (2023) y de 147,98 a 148,05 (2024). El cambio máximo por universidad es +0,82 (2023) y +0,62 (2024), ambos en la Tecnológica del Chocó.
- **DEA, modelo principal:**
  - Spearman entre `global_c` y `global_d`: 1,000 en los dos años.
  - La frontera no cambia (6 universidades en 2023 y 4 en 2024).
  - La eficiencia media pasa de 0,9127 a 0,9134 (2023) y de 0,9156 a 0,9161 (2024).
- **CVaR 5 %:**
  - Spearman 0,996 (2023) y 0,996 (2024).
  - El promedio sube de 109,30 a 109,94 (2023) y de 110,64 a 111,40 (2024).
  - El cambio máximo es +3,15 (Pacífico, 2023) y +3,45 (Tecnológica del Chocó, 2024).

**Lectura:** las conclusiones del informe no dependen de cómo se traten los ceros de Escrita. Esto es un análisis de sensibilidad: `global_c` sigue siendo el puntaje de los resultados principales.

## Límite

La validación solo usa evaluados que sí presentaron Escrita. Si los que tienen cero son distintos de otros con el mismo perfil en los otros cuatro módulos, la imputación tiene sesgo. Ese supuesto (MAR: dado el perfil, el faltante no depende del puntaje que habrían sacado) no se puede comprobar con estos datos.

## Columnas

`resultados/imputacion_escrita_universidades.csv`, una fila por universidad y año, más las filas de referencia `nacional` y `33 universidades`:

| Columna | Qué es |
|---|---|
| `anio`, `pte_codigo`, `pte_nombre` | año y universidad (código PTE vacío en las filas de referencia) |
| `n_evaluados`, `n_ceros_escrita` | evaluados y evaluados con cero en Escrita |
| `global_c` | global con el promedio de los otros cuatro módulos en los ceros (el de los resultados principales) |
| `global_d` | global con la Escrita imputada por PMM, promedio de las 5 imputaciones |
| `global_d_de_entre_imputaciones` | desviación de `global_d` entre imputaciones |
| `diferencia_d_menos_c` | `global_d` − `global_c` |

`resultados/imputacion_escrita_sensibilidad.csv`, una fila por año y análisis (DEA principal y CVaR 5 %):

| Columna | Qué es |
|---|---|
| `spearman_c_vs_d` | correlación de Spearman entre los resultados con `global_c` y con `global_d` |
| `media_c`, `media_d` | promedio de las 33 universidades con cada puntaje |
| `n_frontera_c`, `n_frontera_d` | universidades en la frontera (solo DEA) |
| `cambio_max`, `universidad_cambio_max` | el mayor cambio y en qué universidad |

## Verificación

`verificar_imputacion.py` recalcula por otro camino. Resultado: TODO COINCIDE. Se plantaron dos errores (un coeficiente y un `global_d`) y los detectó.

- Coeficientes con `scipy.linalg.lstsq`.
- Residuos.
- Que el JSON solo tenga parámetros.
- `global_c` contra la base integrada.
- `global_d`: el valor esperado del PMM se calcula buscando los donantes por fuerza bruta, con tolerancia de 4 errores estándar.
- Las eficiencias con `global_d` por el programa de multiplicadores del DEA.
