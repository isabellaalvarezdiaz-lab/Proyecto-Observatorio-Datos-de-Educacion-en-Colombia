# Bitácora de uso de IA — Proyecto Observatorio de Educación en Colombia

**Agente utilizado:** Claude (Anthropic), interfaz de chat.
**Modalidad de uso:** conversación única, sostenida durante toda la Fase 1, con
los tres integrantes del equipo participando directamente (formulando
preguntas, cuestionando afirmaciones y verificando resultados) — no una
consulta puntual ni delegación de una sola sección a la IA.
**Principio seguido durante todo el proceso:** ningún hallazgo, cita o
decisión metodológica se aceptó sin verificación independiente contra la
fuente original, el código real del proyecto auditado, o los archivos de
datos reales.

---

## 1. Diagnóstico inicial y comprensión del repositorio base

**Prompts representativos:**
- "Analiza qué se hizo y qué falta en este repositorio de GitHub..."
- "¿Dónde puedo ver eso, cómo se accede a esa información?"

**Qué se obtuvo:** lectura del README y estructura del repositorio original;
identificación inicial de fortalezas (esquema estrella, análisis descriptivo)
y vacíos aparentes (sin integración de fuentes, sin modelado explicativo).

**Verificación aplicada:** en esta etapa el diagnóstico se basó en lectura
directa del README público — las afirmaciones más fuertes (como la
inexistencia de una llave con SNIES) se identificaron aquí como pendientes
de verificar con el código real, no se aceptaron todavía como definitivas.

---

## 2. Auditoría del código real del proyecto anterior

**Prompts representativos:**
- "¿No se supone que ya habías visto todo el repositorio?"
- Carga directa de `database.py`, `modelo_estrella.py`, `Exploración.py` e
  `informe_final.md` del repositorio original.

**Qué se obtuvo:** confirmación de que el informe final admite no haber
integrado SNIES ni el PTE, y que sus relaciones son asociativas, no
explicativas. Identificación de la columna `inst_cod_institucion` como
candidata a llave de integración con SNIES, contradiciendo la afirmación
del informe de que esa llave no existía.

**Verificación aplicada:** lectura directa del código fuente, no solo del
informe — la fuente de la corrección más importante de todo el proyecto.

---

## 3. Validación empírica de la llave SNIES–Saber Pro

**Prompts representativos:**
- "¿Cómo sabe uno que sí se puede unir?"
- "Dame el código completo para pegarlo y correrlo."

**Qué se obtuvo:** script `verificar_llave.py`, corrido por el equipo contra
archivos reales de dos años no consecutivos: 99,2 % de coincidencia (2021,
261 códigos) y 98,9 % (2024, 270 códigos), confirmado además comparando
nombres de institución de cada lado.

**Verificación aplicada:** resultado obtenido corriendo el script sobre
datos reales del equipo, no una simulación ni un cálculo hecho por la IA.

---

## 4. Descarga y verificación de las fuentes (SNIES, Saber Pro, PTE)

**Prompts representativos:**
- "¿Qué debo descargar de cada portal?"
- "El PTE es mensual, entonces ¿ese pantallazo era solo diciembre?"
- Carga directa del archivo real del PTE (`02__Cuadros_informe_de_
  ejecución_Diciembre.xlsx`).

**Qué se obtuvo:** enlaces verificados de descarga directa para SNIES y
Saber Pro; confirmación de que "acumulada a diciembre" es el cierre del año
completo; identificación de que el PTE sí desagrega presupuesto por
institución, pero solo para 34 universidades públicas (Cuadro N.º 7).

**Verificación aplicada:** cada enlace de descarga se verificó por fetch
directo contra el portal correspondiente antes de entregarlo; la estructura
del PTE se confirmó abriendo y procesando el archivo real subido por el
equipo, no por descripción de terceros.

---

## 5. Diseño metodológico del análisis de eficiencia (DEA)

**Prompts representativos:**
- "¿Qué es el DEA?" / "¿Cómo se implementaría?"
- "¿No crees que el análisis envolvente de datos se queda corto?"

**Qué se obtuvo:** definición de insumo/resultado, orientación a resultados,
rendimientos variables a escala (VRS), verificación de tamaño de muestra
frente a la regla convencional (3× la suma de variables), y el diseño de
dos niveles de análisis (macro nacional-año, micro institución-año).

**Verificación aplicada:** la regla de tamaño de muestra y la elección de
VRS se justificaron con el detalle real de la muestra (4 observaciones en
macro, 130+ en micro), no de forma genérica.

---

## 6. Corrección de un error de diseño propio

**Prompt que lo detectó:**
- "Entonces sería obvio que una universidad con más presupuesto tendría
  mejor desempeño, ¿no? Entonces no entiendo cómo se comparan los puntajes
  de eficiencia."

**Qué se obtuvo:** identificación de que el diseño inicial del DEA macro
comparaba presupuesto exclusivamente público contra el resultado agregado
de todo el país (público y privado), invalidando la comparación. Se
corrigió para que ambos lados del análisis correspondan solo al subconjunto
público.

**Verificación aplicada:** corrección basada en razonamiento metodológico
propio del equipo, no en una fuente externa — ejemplo directo de por qué
cuestionar cada resultado, no solo aceptarlo.

---

## 7. Verificación bibliográfica (estado del arte)

**Prompts representativos:**
- "Dame los links de donde sacabas esos artículos."
- Carga de hallazgos de otra sesión de IA para verificación cruzada.

**Qué se obtuvo:** ocho fuentes verificadas de forma independiente
(Galvis-Aponte 2015; Maza Ávila et al. 2017; Melo-Becerra et al. 2017;
Morales-Piñero et al. 2022; Almeida et al. 2024; SITEAL; SPADIES; ISCE), más
Charnes et al. (1978) como referencia metodológica fundacional.

**Verificación aplicada:** se detectó y corrigió un error de citación
heredado de otra sesión de IA (autores y volumen incorrectos en Almeida et
al., 2024) mediante búsqueda directa contra la fuente original — caso
explícito de no aceptar una verificación ajena sin repetirla.

---

## 8. Adaptación a la rúbrica de evaluación real

**Prompts representativos:**
- Carga del documento completo de la rúbrica (Javier Mauricio Sierra,
  Consultoría Estadística).
- "¿Qué cosas me faltan de la rúbrica?"

**Qué se obtuvo:** identificación y construcción de los elementos que no se
habían trabajado: cronograma con hitos y riesgos (D5), declaración de uso
de IA con casos concretos (S3), modalidad del proyecto como datos abiertos,
portada, y la pregunta explícita del problema (D1).

**Verificación aplicada:** revisión repetida de la rúbrica completa contra
lo ya construido, encontrando en cada pasada elementos adicionales
faltantes antes de darla por completa.

---

## 9. Ensamblaje de entregables

**Qué se produjo:**
- Documento del anteproyecto en Word (portada, D1–D5, S3, referencias APA 7).
- Versión en LaTeX del mismo documento, para Overleaf.
- Tablero interactivo en R/Shiny con seis secciones.
- Scripts de Python: `verificar_llave.py`, `extraer_pte.py`,
  `cargar_saber_pro.py`.

**Verificación aplicada:** el documento Word se validó estructuralmente
(sin errores de esquema) y se confirmó su extensión real convirtiéndolo a
PDF, en vez de asumir el conteo de páginas.

---

## Resumen de lo descartado por verificación

| Afirmación inicial (propia o de otra fuente) | Resultado de verificar |
|---|---|
| El proyecto anterior tenía razón: no hay llave SNIES–Saber Pro | Falsa — 99,2 % / 98,9 % de coincidencia real |
| Nadie ha aplicado DEA a educación superior en Colombia | Falsa — al menos 3 estudios colombianos existentes |
| El PTE no desagrega presupuesto por institución | Falsa — sí lo hace, para 34 universidades públicas |
| Cita de Almeida et al. (2024): 2 autores, volumen 11 | Falsa — 6 autores, volumen 12 |
| DEA macro: insumo público vs. resultado de todo el país | Diseño inválido — corregido a insumo y resultado solo públicos |
