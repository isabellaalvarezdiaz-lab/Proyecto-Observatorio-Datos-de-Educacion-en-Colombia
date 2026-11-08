# Guía de `resultados/`

Todas las tablas son agregadas por institución o universidad: ninguna tiene datos de estudiantes. Cada una la produce un script de `scripts/`, y sus columnas están explicadas en el diccionario que se indica.

## Cómo se conectan

```text
Datos crudos (data/, no se suben): SNIES · Saber Pro · PTE
        │
        ▼
OE1  tabla_maestra_2023_2024.csv ──► base_integrada_2023_2024.csv   (33 universidades × 2 años)
        │
        ├──► OE3  oe3_eficiencia.csv  (DEA con bootstrap)  ──► pruebas de solidez del OE3
        ├──► OE2  oe2_malmquist.csv   (cambio de productividad)
        ├──► Riesgo  riesgo_*.csv     (VaR/CVaR, Kupiec, stress testing)
        └──► Imputación  imputacion_escrita_*.csv
                         │
                         ▼
          API (backend/) y tablero (frontend/) leen estas mismas tablas
```

## 1. Empiece aquí: los resultados principales del informe

| Archivo | Responde | Script | Diccionario |
|---|---|---|---|
| `oe3_eficiencia.csv` | ¿Qué tan eficiente es cada universidad en 2023 y 2024? Eficiencia DEA corregida, intervalo del 95 %, pares y metas; modelos principal y cobertura | `oe3_dea_bootstrap.py` | `docs/diccionario_resultados_oe2_oe3.md` |
| `oe2_malmquist.csv` | ¿Cambió la productividad entre 2023 y 2024? Índice de Malmquist y su descomposición | `oe2_malmquist.py` | `docs/diccionario_resultados_oe2_oe3.md` |
| `base_integrada_2023_2024.csv` | ¿Con qué datos se midió? Presupuesto, matrícula, graduados y puntaje de cada universidad | `construir_base_integrada.py` | `docs/diccionario_base_integrada.md` |
| `figuras/` | Las figuras del informe | `graficos_oe2_oe3.py` | — |

## 2. Solidez del OE3

| Archivo | Responde | Script |
|---|---|---|
| `oe3_cobertura_sin_unad.csv` | ¿Cambia el modelo de cobertura sin la UNAD? | `oe3_cobertura_sin_unad.py` |
| `oe3_deja_uno_fuera.csv` | ¿Cambia la evaluación si se quita una universidad? | `oe3_dea_bootstrap.py` |
| `oe3_sensibilidad.csv` | ¿Cambia el modelo principal si el puntaje se calcula sin los estudiantes con 0 en Escrita? | `oe3_dea_bootstrap.py` |
| `oe3_validacion_resumen.csv`, `oe3_validacion_universidades.csv` | ¿Se sostiene con universidades que el modelo no usó? | `oe3_validacion_fuera_muestra.py` |
| `oe3_segunda_etapa.csv`, `oe3_contexto_menos_eficientes.csv` | ¿Qué características se asocian con la eficiencia? (exploratorio) | `oe3_segunda_etapa.py` |
| `caracteristicas_universidades.csv` | Perfil de cada universidad: orden, acreditación, oferta a distancia, posgrado, estratos 1 y 2, educación de la madre | `caracteristicas_universidades.py` |

Diccionario: `docs/diccionario_resultados_oe2_oe3.md`.

## 3. Teoría del Riesgo

| Archivo | Responde | Script |
|---|---|---|
| `riesgo_puntaje.csv` | ¿Qué tan rezagado queda el 5 % más bajo de cada universidad? VaR y CVaR con intervalos | `riesgo_puntaje.py` |
| `riesgo_kupiec.csv` | ¿La cola de 2024 quedó donde la dejó el VaR de 2023? | `riesgo_puntaje.py` |
| `riesgo_puntaje_asociaciones.csv` | ¿El CVaR se asocia con los estratos o con la eficiencia? | `riesgo_puntaje.py` |
| `riesgo_stress_resumen.csv`, `riesgo_stress_universidades.csv` | ¿Cambia la eficiencia si cambia el presupuesto (recortes o gratuidad)? | `riesgo_stress.py` |

Diccionario: `docs/diccionario_riesgo.md`. Verificador: `verificar_riesgo.py`.

## 4. Imputación de los ceros de Escrita

| Archivo | Responde | Script |
|---|---|---|
| `imputacion_escrita_universidades.csv` | ¿Cuánto cambia el puntaje de cada universidad al imputar los ceros por perfiles similares? | `imputar_escrita.py` |
| `imputacion_escrita_sensibilidad.csv` | ¿Cambian el DEA o el CVaR con esa imputación? | `imputar_escrita.py` |

Diccionario: `docs/diccionario_imputacion.md`. Verificador: `verificar_imputacion.py`. El modelo está en `modelos/imputador_escrita.json`.

## 5. Corrección del trabajo previo

| Archivo | Responde | Script |
|---|---|---|
| `revision_trabajo_previo.csv` | Cifras de Comunicación Escrita que corrigen el informe 2025-2 | `revision_trabajo_previo.py` |

## 6. Tablas intermedias de construcción (OE1)

No responden una pregunta del informe por sí solas: son los pasos que llevan de los datos crudos a la base integrada. Se suben para que cualquiera pueda revisar cada paso sin tener los microdatos.

| Archivo | Qué es | Script |
|---|---|---|
| `tabla_maestra_2023_2024.csv` | SNIES + Saber Pro para todas las instituciones (entregable del OE1) | `construir_tabla_maestra.py` |
| `saber_pro_institucion_anio.csv` | Saber Pro agregado por institución y año | `agregar_saber_pro.py` |
| `pte_universidades_2023_2024.csv` | Presupuesto de las 34 universidades extraído del PTE | `extraer_pte_universidades.py` |
| `sedes_por_universidad.csv` | Qué códigos de institución (sedes) pertenecen a cada universidad del PTE | `cruce_sedes.py` |

Diccionarios: `docs/diccionario_tabla_maestra.md` y `docs/diccionario_base_integrada.md`.
