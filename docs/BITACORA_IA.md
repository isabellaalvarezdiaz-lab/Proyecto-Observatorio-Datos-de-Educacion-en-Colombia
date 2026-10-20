# Bitácora de uso de IA — Proyecto Observatorio de Educación en Colombia

**Agente utilizado:** Claude (Anthropic), interfaz de chat.

**Modalidad de uso:** interacción sostenida por parte de los tres
integrantes del equipo, quienes formularon requerimientos, cuestionaron
resultados y validaron hallazgos de manera conjunta — no se trató de una
consulta puntual ni de la delegación de una sección específica a un único
integrante.

**Continuidad del proceso (fase 1):** el desarrollo de esta fase se llevó a cabo a
lo largo de **tres sesiones de conversación diferenciadas** con el agente
de IA. En cada una de ellas, el equipo suministró explícitamente el
contexto acumulado del proyecto —diagnóstico realizado, decisiones
metodológicas ya adoptadas y hallazgos previamente verificados— con el
propósito de que las respuestas obtenidas fueran coherentes con el estado
real de avance y pertinentes a las necesidades específicas de cada etapa,
evitando partir de supuestos genéricos o desligados del trabajo
previamente construido.

**Principio metodológico transversal:** ningún hallazgo, referencia
bibliográfica o decisión metodológica sugerida por la IA se incorporó al
proyecto sin una verificación independiente, realizada por el equipo,
contra la fuente original, el código fuente del proyecto auditado o los
archivos de datos reales.

Chat 1 — Diagnóstico, auditoría y validación empírica

"Vamos a desarrollar la Fase 1 de una consultoría estadística sobre el repositorio [enlace de GitHub], un proyecto del mismo curso que intentó construir un observatorio de datos de educación superior en Colombia integrando tres fuentes: SNIES, Saber Pro y el PTE (Portal de Transparencia Económica).

Necesito que primero hagas un diagnóstico crítico del repositorio: qué se propuso, qué se logró realmente, y qué vacíos o afirmaciones metodológicas sin evidencia hay detrás — revisando no solo el informe final, sino el código fuente real (scripts de carga y construcción del modelo).

Con ese diagnóstico, necesito que me ayudes a verificar empíricamente —no a suponer— cualquier afirmación sobre si las fuentes se pueden integrar entre sí, construyendo el código necesario para probarlo contra datos reales. También necesito que identifiquemos y organicemos el acceso a las tres fuentes: de dónde se descargan, con qué periodicidad, y qué limitaciones de acceso tiene cada una.

Antes de dar cualquier hallazgo por cierto, verifícalo contra la fuente real, no lo asumas porque suene razonable."

Entregable de este chat: diagnóstico completo, llave de integración validada con datos reales, y las tres fuentes identificadas y accesibles.

Chat 2 — Diseño metodológico, objetivos y estado del arte

"Continuamos la consultoría del Proyecto Observatorio de Datos de Educación en Colombia. Te resumo lo ya resuelto en la etapa anterior: [pegar el diagnóstico, el resultado de la validación de la llave con sus porcentajes, y qué fuentes de datos están confirmadas y accesibles].

Nuestro profesor sugirió orientar el proyecto hacia el ángulo de economía y consumo de recursos —eficiencia del gasto público—. Necesito que, con esa base, me ayudes a definir un objetivo general y objetivos específicos verificables, y a diseñar en detalle la técnica de Análisis Envolvente de Datos aplicada a este problema —insumos, resultados, orientación del modelo, supuestos y verificación de tamaño de muestra—.

Con los objetivos ya definidos, necesito que construyas el estado del arte: literatura que sustente específicamente estos objetivos, no una revisión general del tema — verificando cada fuente de forma independiente antes de citarla, incluyendo autores, año y datos exactos contra la fuente original."

Entregable de este chat: objetivos específicos definidos, diseño metodológico completo del DEA, y estado del arte con fuentes verificadas una por una.

Chat 3 — Adaptación a la rúbrica y ensamblaje de entregables**

"Cerramos la Fase 1 de la consultoría del Proyecto Observatorio de Datos de Educación en Colombia. Te resumo lo desarrollado hasta ahora: [pegar o adjuntar el diagnóstico, la llave validada, los objetivos específicos, el diseño del DEA, y el estado del arte ya construidos].

Adjunto también la rúbrica real de evaluación de mi profesor [adjuntar documento]. Necesito que la revises criterio por criterio contra todo lo que ya tenemos, identifiques qué falta o qué no cumple el nivel esperado, y me ayudes a completarlo — incluyendo cronograma, declaración de uso de IA, y cualquier otro elemento exigido que no hayamos trabajado todavía.

Con todo eso completo, necesito que ensambles el documento final del anteproyecto respetando el formato, extensión y citación exigidos, y que generes los guiones necesarios para la sustentación oral."

Entregable de este chat: documento final del anteproyecto, ajustado a la rúbrica, y material listo para la sustentación.

---

## 1. Diagnóstico inicial y comprensión del repositorio base

**Prompt representativo:** Solicitud de análisis comparativo del
repositorio del proyecto antecesor, orientado a identificar los
componentes efectivamente desarrollados, las brechas metodológicas
existentes frente a sus propios objetivos declarados, y los mecanismos
disponibles para acceder y consultar los resultados generados.

**Qué se obtuvo:** una lectura estructurada del README y de la arquitectura
general del repositorio original, que permitió identificar fortalezas
concretas —la construcción de un esquema dimensional y un análisis
descriptivo progresivo— junto con vacíos aparentes en materia de
integración de fuentes y de modelado explicativo.

**Verificación aplicada:** en esta etapa inicial, el diagnóstico se
fundamentó en la lectura directa de la documentación pública del
repositorio. Las afirmaciones de mayor peso metodológico —en particular,
la presunta inexistencia de una llave de integración con el SNIES— se
identificaron explícitamente como pendientes de contrastar contra el
código fuente, sin aceptarse todavía como concluyentes.

---

## 2. Auditoría del código fuente del proyecto antecesor

**Prompt representativo:** Requerimiento de verificación exhaustiva del
código fuente del proyecto antecesor —scripts de carga de datos,
construcción del modelo dimensional e informe final—, entendida como
complemento indispensable de la revisión documental inicial, dado que esta
última no permite validar por sí sola la totalidad de las decisiones
técnicas efectivamente adoptadas.

**Qué se obtuvo:** la confirmación, mediante lectura directa del código y
no solo del informe, de que el proyecto antecesor no integró el SNIES ni el
PTE con los datos de Saber Pro, y de que las relaciones documentadas son de
naturaleza asociativa, no explicativa. Adicionalmente, se identificó la
columna `inst_cod_institucion` como candidata plausible a llave de
integración con el SNIES, en contradicción directa con lo afirmado en el
informe final de dicho proyecto.

**Verificación aplicada:** el hallazgo se sustenta en la lectura directa
del código fuente del repositorio auditado —no en su documentación
narrativa—, constituyendo la base metodológica de la corrección más
relevante realizada sobre el proyecto antecesor a lo largo de esta fase.

---

## 3. Validación empírica de la llave de integración SNIES–Saber Pro

**Prompt representativo:** Requerimiento de una metodología de
verificación empírica —no inferencial— para establecer la validez de la
llave de integración identificada entre las fuentes SNIES y Saber Pro,
junto con la construcción de un script reproducible que permitiera
ejecutar dicha verificación directamente sobre los datos reales del
proyecto.

**Qué se obtuvo:** el script `verificar_llave.py`, ejecutado por el equipo
contra archivos reales correspondientes a dos años no consecutivos, que
arrojó una coincidencia del 99,2 % (2021, sobre 261 códigos de institución)
y del 98,9 % (2024, sobre 270 códigos), corroborada adicionalmente mediante
comparación manual de los nombres de institución asociados a cada código.

**Verificación aplicada:** el resultado se obtuvo mediante la ejecución
directa del script sobre los datos reales disponibles al equipo, sin que
en ningún momento mediara una simulación, estimación o cálculo realizado
por la IA en nombre del equipo.

**Nota de trazabilidad (13-10-2026):** esa corrida se hizo con la versión
del script entregada en el chat, que no está en el repositorio, y su salida
tampoco; por eso el 99,2 % de 2021 no tiene evidencia en el repositorio. El
script se rehízo el 17-09-2026 (`scripts/verificar_llave.py`) y su corrida
sobre el periodo del proyecto quedó en
`docs/gobernanza/evidencias/verificacion_llave_2026-09-18_0235.txt`: el
98,9 % de los códigos de Saber Pro (262 de 265) está en el SNIES de
matriculados en 2023, y el 100 % (270 de 270) en 2024. El 98,9 % de 2024
citado arriba corresponde a la comparación con el SNIES de graduados (267
de 270), que esa misma evidencia reproduce.

---

## 4. Descarga y verificación de las fuentes de información (SNIES, Saber Pro, PTE)

**Prompt representativo:** Solicitud de un mapeo detallado de las fuentes
de información institucional requeridas por el proyecto —SNIES, Saber Pro
y PTE—, especificando procedencia, periodicidad, nivel de granularidad y
condiciones de acceso, así como la verificación puntual de la naturaleza
acumulativa de los reportes de ejecución presupuestal publicados por el
Ministerio de Hacienda.

**Qué se obtuvo:** enlaces de descarga directa verificados para las bases
del SNIES y de Saber Pro; confirmación documentada de que la expresión
"acumulada a diciembre" corresponde al cierre completo del año fiscal, y no
a la ejecución de ese mes en particular; e identificación de que el PTE sí
desagrega la ejecución presupuestal por institución, aunque circunscrita a
las treinta y cuatro universidades de naturaleza pública (Cuadro N.º 7 del
informe de ejecución).

**Verificación aplicada:** cada enlace de descarga suministrado se
verificó mediante consulta directa al portal correspondiente antes de ser
entregado al equipo; la estructura interna del PTE se confirmó procesando
el archivo real aportado por el equipo, y no a partir de descripciones de
terceros sobre dicho portal.

---

## 5. Diseño metodológico del análisis de eficiencia (DEA)

**Prompt representativo:** Solicitud de fundamentación conceptual y
metodológica del Análisis Envolvente de Datos como técnica de medición de
eficiencia relativa, incluyendo su especificación técnica —orientación del
modelo, supuesto de rendimientos a escala— y una evaluación crítica sobre
la suficiencia del alcance metodológico propuesto en relación con el nivel
académico y el tiempo disponible para el proyecto.

**Qué se obtuvo:** la definición operativa de insumo y resultado aplicable
al proyecto, la selección justificada de una orientación a resultados y de
rendimientos variables a escala, la verificación del tamaño de muestra
frente a la regla convencional de al menos tres veces la suma de variables
del modelo, y el diseño diferenciado de dos niveles de análisis —nacional
(macro) e institucional (micro)—.

**Verificación aplicada:** tanto la regla de tamaño de muestra como la
pertinencia del supuesto de rendimientos variables a escala se
contrastaron contra las características reales de la muestra disponible
—cuatro observaciones a nivel macro, más de ciento treinta a nivel
micro—, en lugar de asumirse de manera genérica.

---

## 6. Identificación y corrección de una inconsistencia metodológica propia

**Prompt que originó la corrección:** Cuestionamiento directo sobre la
coherencia interna del diseño inicial del análisis de eficiencia a nivel
macro, orientado a esclarecer si resultaba metodológicamente válido que
una institución con mayor presupuesto exhibiera, por esa sola razón, un
mejor desempeño relativo.

**Qué se obtuvo:** la identificación de que el diseño inicial del análisis
macro comparaba un insumo circunscrito exclusivamente al sector público
contra un resultado agregado correspondiente a la totalidad del sistema
educativo —público y privado—, lo cual invalidaba la comparación al no
corresponder ambos términos al mismo universo institucional. En
consecuencia, el diseño se ajustó para que tanto el insumo como el
resultado se restrinjan al subconjunto de instituciones públicas.

**Verificación aplicada:** la corrección se originó en el razonamiento
metodológico propio del equipo, no en una fuente externa, y constituye
evidencia directa de un proceso de revisión crítica de los resultados
sugeridos por la IA, y no de su aceptación automática.

---

## 7. Verificación bibliográfica del estado del arte

**Prompt representativo:** Solicitud de verificación primaria e
independiente de cada referencia bibliográfica incorporada al estado del
arte, incluyendo la validación cruzada de hallazgos bibliográficos
obtenidos en una sesión de trabajo distinta, con el propósito de garantizar
la exactitud y trazabilidad de la información citada en el documento final.

**Qué se obtuvo:** un conjunto de ocho fuentes verificadas de manera
independiente (Galvis-Aponte, 2015; Maza Ávila et al., 2017; Melo-Becerra
et al., 2017; Morales-Piñero et al., 2022; Almeida et al., 2024; SITEAL;
SPADIES; ISCE), complementado con Charnes et al. (1978) como referencia
metodológica fundacional de la técnica aplicada.

**Verificación aplicada:** se identificó y corrigió un error de citación
—autores incompletos y volumen incorrecto en la referencia de Almeida et
al. (2024)— heredado de una verificación previa realizada en una sesión de
trabajo distinta, mediante búsqueda directa contra la fuente original. Este
caso constituye evidencia explícita de que ninguna verificación externa,
incluida la de otra sesión de IA, se aceptó sin ser replicada por el
equipo.

---

## 8. Adaptación del proyecto a la rúbrica oficial de evaluación

**Prompt representativo:** Solicitud de análisis comparativo, criterio por
criterio, entre el contenido desarrollado hasta el momento y los
requerimientos establecidos en el instrumento oficial de evaluación,
orientada a identificar de manera sistemática los vacíos y las áreas de
mejora pendientes antes de la entrega formal del anteproyecto.

**Qué se obtuvo:** la identificación y posterior construcción de los
elementos que no habían sido trabajados hasta ese momento —cronograma con
hitos, entregables y riesgos con su respectiva contingencia (D5);
declaración de uso de IA sustentada en casos concretos y verificables
(S3); declaración explícita de la modalidad del proyecto como de datos
abiertos; portada institucional; y la formulación explícita del problema
como pregunta estadística respondible (D1)—.

**Verificación aplicada:** la revisión de la rúbrica se realizó en más de
una ocasión sobre el mismo contenido ya construido, identificándose en
cada revisión elementos adicionales pendientes antes de considerar el
documento completo frente a los criterios oficiales de evaluación.

---

## 9. Ensamblaje de los entregables finales

**Prompt representativo:** Solicitud de consolidación de la totalidad del
contenido desarrollado en un documento formal ajustado a los lineamientos
de extensión, formato de citación y estructura exigidos por la rúbrica, así
como la generación de versiones complementarias del mismo contenido en
distintos formatos de presentación, orientadas a la sustentación oral y al
seguimiento técnico del proyecto.

**Qué se obtuvo:** el documento del anteproyecto en formato Word (portada,
criterios D1 a D5, S3 y referencias en formato APA 7); su versión
equivalente en LaTeX para edición en Overleaf; un tablero interactivo
desarrollado en R/Shiny; y los scripts de Python `verificar_llave.py`,
`extraer_pte.py` y `cargar_saber_pro.py`.

**Verificación aplicada:** el documento en Word se sometió a validación
estructural para descartar errores de esquema, y su extensión real se
confirmó mediante conversión a PDF, en lugar de asumirse a partir de un
conteo estimado de palabras.

**Nota de trazabilidad (13-10-2026):** las versiones de esos tres scripts
que se entregaron en el chat, y el tablero en R/Shiny, nunca estuvieron en
el repositorio. `verificar_llave.py` se rehízo el 17-09-2026 (ver la nota
de la entrada 3); la extracción del PTE y la agregación de Saber Pro las
hacen hoy `scripts/extraer_pte_universidades.py` y
`scripts/agregar_saber_pro.py`, dentro de `scripts/correr_oe1.py`. El
tablero de la entrega final es el de la entrada 15.

---

# Fase 2 — Ejecución de los objetivos específicos (octubre de 2026)

**Agente utilizado:** Claude (Anthropic), en una sesión con un entorno de
ejecución de código, en la que el agente corrió los scripts sobre copias de
los datos aportados por el equipo.

**Integrantes que interactuaron en esta fase:** Isabella Álvarez y Anderson
González.

**Punto de partida:** la sesión arrancó de un resumen de traspaso con las
decisiones ya verificadas, redactado bajo la regla "nada sin fuente": toda
afirmación debe poder rastrearse a un documento y a una ubicación dentro de
él, y lo que no esté verificado se dice explícitamente.

**Cómo se verificó en esta fase:** cada resultado sale de un script del
repositorio y se comprobó por tres vías:

1. un verificador independiente que recalcula las cifras por otro camino
   (`verificar_oe1.py` y `verificar_oe2_oe3.py`) y responde PASA o FALLA;
2. errores plantados a propósito en copias de los resultados, para comprobar
   que el verificador los detecta;
3. la reproducción completa en un segundo computador del equipo, que obtuvo
   las mismas cifras.

Cada corrida deja su salida con fecha y hora en `docs/gobernanza/evidencias/`.

---

## 10. Tabla maestra y base integrada (OE1)

**Prompt representativo:** solicitud de concentrar el trabajo en cumplir los
objetivos específicos, a partir de los archivos del PTE, el SNIES y Saber Pro
ya descargados por el equipo, con un repositorio reiniciado de forma limpia.

**Qué se obtuvo:** los scripts `agregar_saber_pro.py`,
`extraer_pte_universidades.py`, `cargar_snies.py`, `cruce_sedes.py`,
`construir_tabla_maestra.py`, `construir_base_integrada.py` y `correr_oe1.py`.
La tabla maestra tiene 654 filas y 330 códigos de institución; la base
integrada reúne las 34 universidades públicas del PTE a partir de 52 sedes.

**Verificación aplicada:** `verificar_oe1.py` recalcula cada cifra desde los
archivos originales y respondió TODO COINCIDE, también en el segundo
computador.

**Fallos de la IA detectados y corregidos:**

- Los primeros scripts buscaban los datos en una carpeta `raw/` en la raíz
  del repositorio, que no coincidía con la estructura acordada
  (`data/raw/...`). Se detectó al correrlos y se reescribieron.
- El paquete entregado tras reiniciar el repositorio no incluía
  `agregar_saber_pro.py`. Se detectó porque el primer paso de `correr_oe1.py`
  falló, y se entregó el archivo.
- El primer cruce por nombre omitió la sede 9933 de la Universidad Nacional,
  con 74 evaluados en 2024. Se detectó al comparar los conteos con una corrida
  anterior y se corrigió asignando las sedes por la columna IES PADRE del SNIES.

---

## 11. DEA con bootstrap (OE3) e índice de Malmquist (OE2)

**Prompt representativo:** solicitud de terminar el 70 % del trabajo en la
semana, con instrucciones paso a paso para ejecutarlo en PowerShell y con
todo verificado.

**Qué se obtuvo:** `dea.py`, `oe3_dea_bootstrap.py`, `oe2_malmquist.py`,
`verificar_oe2_oe3.py` y `graficos_oe2_oe3.py`, con los diccionarios de
resultados y el informe de avance en LaTeX.

**Verificación aplicada:** el verificador resuelve el programa dual con el
algoritmo de punto interior, en lugar del programa de envolvente con el
símplex, y comprueba las propiedades que la teoría garantiza. Detectó todos
los errores plantados, y el segundo computador reprodujo las cifras.

**Fallos de la IA detectados y corregidos:**

- La primera versión del bootstrap suavizaba en la escala de eficiencia (0 a
  1) y produjo eficiencias corregidas negativas en el modelo de cobertura
  (hasta −606). Se detectó con un control de coherencia y se corrigió
  trabajando en la escala de Farrell (φ ≥ 1) con reflexión en 1.
- El verificador tenía dos errores de código (alineación de índices y
  precedencia de operadores) que aparecieron al correrlo y se corrigieron
  antes de la entrega.
- Las instrucciones de subida no excluían `__pycache__`, que quedó en GitHub
  (commit `9414a9f`). Se agregó al `.gitignore` y se retiró en el commit
  `2fdded9`.

---

## 12. Cobertura sin la UNAD y segunda etapa exploratoria

**Prompt representativo:** solicitud de avanzar en dos resultados: el modelo
de cobertura sin la UNAD como resultado formal, y qué caracteriza a las
universidades menos eficientes, con pruebas no paramétricas y no con
regresión. Después, solicitud de agregar el contexto socioeconómico que el
anteproyecto había prometido.

**Qué se obtuvo:** `oe3_cobertura_sin_unad.py`,
`caracteristicas_universidades.py` y `oe3_segunda_etapa.py` (Spearman y
Mann-Whitney con ajuste de Holm), con las figuras 4 y 5 y la tabla del perfil
de las cinco universidades menos eficientes.

**Verificación aplicada:** el verificador recalcula los estadísticos, los
p-valores y el ajuste de Holm con fórmulas propias, sin las funciones de
`scipy`. En el computador que tiene los datos crudos, también recalcula
desde el SNIES y Saber Pro originales cada característica de las
universidades. El índice socioeconómico del ICFES (INSE) se descartó tras
comprobar con los datos que su relación con el estrato cambia de −0,54 en
2023 a −0,95 en 2024.

**Fallos de la IA detectados y corregidos:**

- La IA describió el modelo sin la UNAD como una comparación entre
  universidades presenciales. El SNIES muestra que en 2024 el Tolima tiene el
  68 %, Cartagena el 53 % y el Magdalena el 34 % de su matrícula a distancia o
  virtual. Se corrigió la descripción.
- La IA presentó tres asociaciones del modelo principal (ceros en Escrita,
  programas acreditados y posgrado) como hallazgos independientes. Al
  calcular su correlación con los productos se vio que las tres siguen al
  puntaje de Saber Pro, y se cambió la interpretación.
- Unas instrucciones de PowerShell traían una ruta de ejemplo
  (`C:\ruta\...`) en lugar de la real. Al ejecutarlas tal cual, el zip no se
  descomprimió, corrieron los scripts anteriores y se subió un commit
  (`1a84cef`) cuyo mensaje no corresponde a su contenido. No dañó resultados;
  desde entonces las instrucciones buscan el archivo y comprueban con
  `Test-Path` que llegó antes de seguir.

---

## 13. Revisión crítica de todo lo hecho

**Prompt representativo:** "¿todo lo que hemos hecho está bien?".

**Qué se obtuvo:** una revisión de los supuestos y de la interpretación, además
de los cálculos. En una corrida de revisión hecha por el agente (no incluida
en el repositorio) se comprobó que en todas las universidades el sesgo del
bootstrap es al menos 1,7 veces su desviación estándar, lo que justifica
reportar la eficiencia corregida. No se pudo verificar en el texto original
el umbral que la literatura atribuye a Simar y Wilson para esa decisión, así
que no se cita.

**Fallos de la IA detectados y corregidos:**

- El informe decía que el insumo era "lo que gira la Nación". Revisando el
  Cuadro No. 7 del PTE se vio que es solo lo registrado en la entidad de cada
  universidad: en diciembre de 2024, la gratuidad (2.744 mil millones de
  pesos, fila 1758) y la concurrencia pensional (475 mil millones, fila 1729)
  están en el Ministerio de Educación sin desagregar. Se corrigió la
  limitación.
- El informe decía que cuatro universidades mejoraron su productividad. Dos
  de ellas (la Nacional, 1,005, y Cartagena, 1,004) están prácticamente en 1 y
  el Malmquist no tiene intervalos, así que se cambió la redacción.
- Las correlaciones de Spearman del análisis deja uno fuera, de la
  sensibilidad y del modelo sin la UNAD no trataban como empatadas a las
  universidades de la frontera: el ruido numérico del solver rompía el
  empate. Se detectó al recalcularlas desde los CSV para el informe. Se
  corrigió en los scripts (commit `5a8f02e`): los valores cambiaron hasta en
  0,02, ninguna eficiencia cambió y ahora el verificador revisa esas
  correlaciones.

---

## 14. Informe y discusión frente a la literatura

**Prompt representativo:** solicitud de redactar las secciones nuevas del
informe y la comparación con los estudios colombianos, a partir de los PDF
aportados por el equipo.

**Qué se obtuvo:** el informe en LaTeX generado a partir de los CSV del
repositorio, sin transcribir cifras a mano, y la discusión frente a Maza
Ávila et al. (2017), Visbal-Cadavid et al. (2017) y Melo-Becerra et al.
(2017), con la página de cada cifra citada.

**Verificación aplicada:** los tres artículos se leyeron completos antes de
citarlos. Uno de los PDF aportados (Marques et al., 2020) no correspondía a
los solicitados y no se usó. La referencia de Maza Ávila et al. se corrigió
con el nombre exacto de la revista (*Investigación & Desarrollo*) y su DOI,
tomados del propio artículo.

**Fallos menores de la IA:** errores de LaTeX detectados al compilar (citas
con `\citet` sin el paquete natbib, una coma introducida por un reemplazo
global en "U, Distrital" y figuras que dejaban huecos en la página),
corregidos antes de la entrega.

---

## 15. Corrección del trabajo previo, informe final y material de la sustentación

**Prompt representativo:** "realiza lo que puedas hacer ya".

**Qué se obtuvo:** `scripts/revision_trabajo_previo.py`, con su tabla y su
evidencia, para corregir la afirmación del informe 2025-2 sobre Comunicación
Escrita; las secciones finales del informe (cumplimiento de los objetivos,
corrección del trabajo previo, conclusiones y recomendaciones); una
presentación para la sustentación, un tablero interactivo y una guía de
preguntas. Las cifras de la presentación y del tablero salen de los CSV del
repositorio con el mismo cálculo que usa el informe; los datos del tablero los
prepara `scripts/datos_tablero.py`.

**Verificación aplicada:** el informe se generó otra vez desde los CSV y
compiló sin advertencias. El formato de números del tablero se comparó con el
del informe en 8.128 valores, sin ninguna diferencia. `datos_tablero.py`
comprueba que cada llave sea única y que el intervalo contenga la eficiencia
corregida.

**Fallos de la IA detectados y corregidos:**

- Una cifra escrita a mano en el texto del informe no coincidía con su tabla:
  la eficiencia del Chocó aparecía como 0,688 [0,674; 0,699] y la tabla
  calculada da 0,689 [0,673; 0,699]. Ahora esa frase también se genera desde
  los CSV.
- El informe decía que la acreditación institucional no pasaba el ajuste de
  Holm en ningún año, pero en 2023 su p ajustado es 0,046. Se corrigió la
  redacción.
- Una afirmación sobre el ordenamiento de Visbal-Cadavid et al. citaba la
  página 1; el ordenamiento está en la tabla 10 (pp. 14–15). Se corrigió la
  cita.
- Riesgo detectado antes de entregar: el formato de números del navegador
  redondea 0,6735 a 0,674, mientras que el informe muestra 0,673, porque
  Python redondea el valor binario exacto. El tablero usa un formato propio
  que reproduce el del informe.

---

## 16. Sugerencias del docente: modelo principal y validación fuera de muestra

**Prompt representativo:** el docente indicó dejar como principal el modelo con mayor eficiencia, "siempre y cuando no tuviera un sobreajuste", y dejar un porcentaje de los datos que el modelo no toque para validar que sirve. También mencionó un ensamblaje de modelos (k-means y luego otro modelo) y una clasificación con regresión logística.

**Qué se obtuvo:** el agente explicó que esas sugerencias vienen de los modelos predictivos y las adaptó al DEA, que no predice una variable conocida.

- Se mantuvo el modelo principal: es el de mayor eficiencia y no está sobreajustado (cumple la regla del tamaño de muestra y deja solo 4 de 33 universidades en la frontera en 2024).
- Se agregó `scripts/oe3_validacion_fuera_muestra.py`. En 1.000 sorteos por modelo y año reserva el 20 % de las universidades, estima la frontera con las demás y evalúa a las reservadas.
  - En el modelo principal, la eficiencia de las que no están en la frontera no cambia en el 60,9 % y el 62,2 % de las evaluaciones (2023 y 2024).
  - El 95 % de los cambios es menor de 0,048 y 0,106, y el orden se mantiene (Spearman agregado de 1,00).
  - El modelo de cobertura con la UNAD es el más sensible.
- No se hizo el ensamblaje: sin una variable objetivo no hay error que reducir combinando modelos.
- No se hizo el k-means previo: con 33 universidades caben como máximo 2 grupos en el modelo principal, y el modelo sin la UNAD ya separa a la universidad más distinta.
- No se hizo la regresión logística: hay solo 4 a 6 universidades en la frontera por año, las eficiencias no son independientes y el anteproyecto excluyó una segunda etapa formal. Con esas razones se acordó no hacerlos.

**Verificación aplicada:** `verificar_oe2_oe3.py` (sección 11) repite todos los sorteos con el programa dual. Comprueba que los casos fuera del soporte corresponden a programas infactibles, que ninguna eficiencia baja al sacar universidades y que no cambia la de una universidad cuyos pares siguen en la muestra. Además recalcula cada indicador: TODO COINCIDE. Se plantaron dos errores en los archivos de la validación y el verificador detectó los dos.

**Fallos menores de la IA:** una expresión mal escrita en el script y un tipo de dato distinto en el generador del informe, detectados al correrlos, y un salto de línea de LaTeX que el compilador rechazó. Se corrigieron antes de entregar.

---

## 17. Revisión del repositorio antes de la entrega

**Prompt representativo:** solicitud de revisar si el repositorio está bien organizado y si falta algo que debería estar en él.

**Qué se obtuvo:** una comparación de lo que hay en GitHub con lo que citan el README, la bitácora, los diccionarios, el informe, la presentación y el tablero.

- En el commit `ffb2454` (8-10-2026), además de pasar lo heredado a `heredado/`, se borraron 22 archivos. Tres de ellos los citan documentos vigentes:
  - `docs/uso_ia/inventario_fallos_isabella.md`, en la tabla "Afirmaciones del informe 2025-2 y lo que muestran los datos" del informe;
  - `docs/gobernanza/evidencias/verificacion_llave_2026-09-18_0235.txt`, en el diccionario de la tabla maestra;
  - `scripts/verificar_llave.py`, en la entrada 3.
- Se restauraron sin cambios 21 de los 22; el que falta, `docs/.gitkeep`, no hace falta.
- El README ahora describe `heredado/` y los scripts de la fase 1, y se agregó `requirements.txt`.

**Verificación aplicada:**

- Cada archivo restaurado tiene la misma huella de git que en la versión anterior a ese commit.
- Existe toda ruta que citan esos documentos, salvo las de archivos que no tienen por qué estar: los que nunca se subieron (nota de la entrada 9), los que describen los inventarios de fallos y `docs/informe_final.md`, que se cita como archivo del repositorio del equipo 2025-2 (aquí está en `heredado/docs/`).
- Los 25 scripts compilan.
- Los archivos de `heredado/` son idénticos a los del último commit del equipo 2025-2 (`0e5bffe`).
- Las salidas del cuaderno `heredado/codigos/Exploración.ipynb` muestran conteos, nombres de columnas, estadísticas agregadas y gráficos; ninguna lista registros de estudiantes.

**Afirmación sin respaldo detectada:** la entrada 3 atribuye a `verificar_llave.py` una coincidencia del 99,2 % en 2021 que no tiene evidencia en el repositorio. Se dejó una nota con las cifras que sí la tienen.

---

## 18. Promedios de grupos con muy pocos evaluados

**Prompt representativo:** solicitud de explicar, también desde el punto de vista matemático, qué hacer con las filas de Saber Pro que tienen un solo evaluado.

**Qué se obtuvo:** en `resultados/saber_pro_institucion_anio.csv` y en la tabla maestra había 3 filas con un solo evaluado y una con tres. Con $n = 1$ el promedio es el puntaje de esa persona, y su error estándar, $\sigma/\sqrt{n}$, es igual a la dispersión de un estudiante cualquiera: el dato expone a alguien y no describe a la institución. Se decidió no publicar los promedios de grupos con menos de 5 evaluados.

- `scripts/publicacion.py` define la regla (`K_MIN = 5`).
- `agregar_saber_pro.py` y `construir_tabla_maestra.py` guardan la versión completa en `data/interim/` (no se sube) y publican en `resultados/` la versión con esas 4 filas en blanco y la columna `suprimido`.
- `construir_base_integrada.py` lee la versión completa, así que la base integrada y todos los resultados del DEA quedan idénticos.

**Verificación aplicada:** se corrió el OE1 completo con los datos crudos. La base integrada, la tabla del PTE y la de sedes salieron idénticas byte a byte a las anteriores, y las filas no suprimidas de las dos tablas publicadas no cambiaron. `verificar_oe1.py` tiene una sección 5 nueva que recalcula desde el .txt original los evaluados y el puntaje de cada sede y comprueba que los blancos estén exactamente donde hay menos de 5 evaluados: TODO COINCIDE. Se plantaron dos errores (un puntaje publicado en una fila suprimida y una marca de supresión en una fila grande) y el verificador detectó los dos.

**Límite declarado:** el puntaje de la sede de Santa Fe de Antioquia (1 evaluado en 2023) podría intentar despejarse con el total de la Universidad de Antioquia y sus demás sedes. Como los promedios se publican con 2 decimales y la universidad tiene 3.196 evaluados, el despeje tiene un error posible de ±32 puntos; con los datos reales el despeje dio 151 frente a un valor real de 161. Además, los valores de esas filas siguen en el historial de git anterior a este cambio.

---

## Resumen de afirmaciones descartadas mediante verificación

La siguiente tabla sintetiza los casos en los que una afirmación inicial
—propia o proveniente de una fuente externa— fue puesta a prueba y
refutada mediante evidencia directa, en lugar de ser incorporada al
proyecto sin contraste:

| Afirmación inicial (propia o de otra fuente) | Resultado de la verificación |
|---|---|
| El proyecto antecesor tenía razón al afirmar que no existía llave de integración entre SNIES y Saber Pro | Refutada — coincidencia empírica del 99,2 % (2021) y 98,9 % (2024); la corrida que quedó en el repositorio da 98,9 % (2023) y 100 % (2024) (nota de la entrada 3) |
| No existen antecedentes de aplicación del DEA a la educación superior en Colombia | Refutada — se identificaron al menos tres estudios colombianos previos |
| El PTE no desagrega la ejecución presupuestal por institución | Refutada — sí lo hace, para el conjunto de treinta y cuatro universidades públicas |
| Referencia de Almeida et al. (2024): dos autores, volumen 11 | Refutada — el estudio corresponde a seis autores, volumen 12 |
| Diseño inicial del DEA macro: insumo exclusivamente público frente a resultado del sistema educativo completo | Diseño inválido — corregido para restringir insumo y resultado al mismo universo institucional |
| El modelo de cobertura sin la UNAD compara universidades presenciales | Refutada — en 2024 el Tolima tiene el 68 %, Cartagena el 53 % y el Magdalena el 34 % de su matrícula a distancia o virtual (SNIES) |
| Las asociaciones del modelo principal con los ceros en Escrita, los programas acreditados y el posgrado son hallazgos independientes | Refutada — las tres siguen al puntaje de Saber Pro, que es un producto del modelo |
| El insumo recoge todo lo que la Nación gira a cada universidad | Refutada — la gratuidad y la concurrencia pensional están en el Ministerio de Educación sin desagregar (PTE, Cuadro No. 7, diciembre de 2024, filas 1758 y 1729) |
| Cuatro universidades mejoraron su productividad entre 2023 y 2024 | Matizada — la Nacional (1,005) y Cartagena (1,004) quedan prácticamente en 1; solo la UNAD y el Magdalena superan 1 con claridad |
| Las correlaciones de Spearman del análisis deja uno fuera estaban bien calculadas | Refutada — los empates de la frontera se rompían por ruido numérico; corregidas, cambian hasta en 0,02 |
| El bootstrap puede suavizarse en la escala de eficiencia (0 a 1) | Refutada — produjo eficiencias corregidas negativas en el modelo de cobertura |
| El primer cruce por nombre encontró todas las sedes | Refutada — faltaba la sede 9933 de la Universidad Nacional (74 evaluados en 2024) |
| El índice socioeconómico del ICFES (INSE) sirve para comparar universidades entre años | Descartado — su relación con el estrato cambia de −0,54 (2023) a −0,95 (2024) |
| Las cifras escritas en el texto del informe coinciden con sus tablas | Refutada — la del Chocó no coincidía (0,688 frente a 0,689); ahora se genera desde los CSV |
| La acreditación institucional no pasa el ajuste de Holm en ningún año | Refutada — su p ajustado es 0,046 en 2023 |
| El modelo de mayor eficiencia podría estar sobreajustado | Descartado — se sostiene fuera de muestra: al reservar el 20 % de las universidades, el orden se mantiene (Spearman agregado de 1,00 en el modelo principal) |
| El repositorio de GitHub tiene todo lo que citan el informe, la bitácora y los diccionarios | Refutada — tres archivos citados se habían borrado en el commit `ffb2454`; se restauraron sin cambios |
| Las tablas agregadas por institución no contienen información de estudiantes | Refutada — 3 filas tenían un solo evaluado, cuyo promedio es el puntaje de esa persona; ahora no se publican los promedios de grupos con menos de 5 |
