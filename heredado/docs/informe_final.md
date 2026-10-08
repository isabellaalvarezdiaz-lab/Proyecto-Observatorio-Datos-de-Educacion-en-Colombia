<div align="center">

# Proyecto Observatorio de datos de Educacion en Colombia 🎓📊📝 

Proyecto del curso <b>Consultoría e Investigación</b> – Facultad de Estadística  
<b>Informe Final</b> · <b>Universidad Santo Tomás</b> · <b>Octavo Semestre (2025-2)</b>
<br/>

<b>Equipo:</b> Yeimy Alarcón · Carlos Diaz · Vanessa Cortes 

</div>

> **Estado:** En progreso · **Repositorio:** _[Link Repositorio](https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia.git)_ · **Última actualización:** 2025-11-17

---
## Introducción

El sistema educativo colombiano genera una gran cantidad de información cada año. Sin embargo, estos datos no solo están dispersos en varios portales, sino que también vienen en formatos muy diferentes que hacen difícil analizarlos y, en muchos casos, incluso acceder a ellos de manera sencilla. Frente a este problema, este proyecto nace con la idea de organizar esa información de una forma más clara y ordenada, para que sea más fácil trabajar con ella y para que se pueda actualizar sin complicaciones cuando aparezcan nuevos datos.

El trabajo se concentra en tres fuentes oficiales que permiten ver la educación desde diferentes ángulos. El SNIES muestra cómo se comportan los estudiantes, las instituciones y los programas. El PTE permite seguir el movimiento del presupuesto destinado al sector educación mes a mes. El ICFES, a través de Saber Pro, ofrece información detallada sobre los estudiantes que presentan el examen de competencias genéricas. Aunque estas fuentes tienen datos de muchos otros años, nosotros elegimos trabajar con el periodo 2021 a 2024, porque son los años más recientes, completos y manejables para el análisis que se quería realizar.

En este informe explicamos cómo se organizaron estas bases, cómo se construyó un modelo que facilita su manejo y cuáles fueron los principales resultados obtenidos al explorar los datos de Saber Pro, que fue la base más sólida y completa para este análisis.

---
## Justificación y antecedentes

Los portales públicos del sector educación son valiosos, pero trabajar directamente con ellos puede ser difícil. Cada fuente tiene su propio formato, sus propios niveles de información y diferentes formas de nombrar variables y categorías. Esto complica los análisis y hace que aunque los datos existan, analizarlos pueda tomar mucho tiempo y esfuerzo.

Este proyecto busca solucionar ese problema creando un observatorio que permita tener toda la información organizada desde el principio. La idea es contar con un sistema donde los datos ya estén limpios, estandarizados y listos para usarse, y que además se pueda actualizar sin dificultad cuando salgan nuevos años.

Las tres fuentes que usamos son confiables y se publican con una frecuencia estable. El SNIES y Saber Pro se actualizan cada año, mientras que el presupuesto del sector educación se publica cada mes. Gracias a esto, podemos construir un sistema que se mantiene al día de forma sencilla, ya que solo requiere agregar la información nueva sin tener que repetir todo el proceso desde cero.

Además, Saber Pro es una de las bases más completas que existen en Colombia sobre educación superior. Tiene información de más de un millón de estudiantes, con puntajes en cinco competencias y datos sobre su contexto familiar, institucional y académico. Esto la convierte en la mejor base que permite entender mejor cómo son los estudiantes, cómo les va en las pruebas y qué factores pueden estar relacionados con sus resultados.

---
## Objetivos

### Objetivo general

Crear un observatorio de datos que permita reunir, organizar y preparar la información del sistema educativo colombiano entre 2021 y 2024 de una manera clara y ordenada. La idea es construir una base sólida y fácil de entender, que ayude a analizar estos datos sin dificultad y que pueda seguir creciendo con el paso del tiempo sin necesidad de empezar desde cero cada vez que alguien quiera agregar un año nuevo.

#### Objetivos específicos

• Reunir los datos del SNIES, del PTE y de Saber Pro y crear un sistema que facilite su acceso y manejo. Esto incluye descargar los archivos de forma automática, organizarlos con nombres claros, documentar cada uno y dejarlos listos para trabajar, sin tener que buscarlos uno por uno ni repetir el proceso para cada año. 

• Construir un modelo estrella que integre toda la información de Saber Pro y que permita manejar más de un millón de registros de forma eficiente. Este modelo debe facilitar la exploración de los datos para entender quiénes presentan el examen, cómo les va en cada módulo y qué características pueden estar relacionadas con sus resultados.

• Dejar un sistema preparado para incorporar nuevos años sin rehacer todo el proceso inicial, de modo que el observatorio pueda mantenerse actualizado de manera sencilla. También asegurar que su estructura sea lo suficientemente clara para que otros puedan usarlo, ampliarlo o adaptarlo en análisis futuros.

---
## Metodología

El proyecto se desarrolló en varias etapas. Primero se exploraron los portales del SNIES, del PTE y del ICFES para conocer su estructura, frecuencia de actualización, la calidad de los datos y su vía de acceso. Luego se descargaron las bases oficiales de los años 2021 a 2024.

En el caso del SNIES, se desarrolló un programa que recorre la página del Ministerio de Educación y descarga todas las bases consolidadas. El programa también renombra los archivos de manera clara y deja registrada la ruta original y la ruta final. Esto evita tener que identificar manualmente cada archivo y garantiza orden desde el principio.

Para el PTE se descargaron los archivos mensuales de presupuesto y se creó un programa que selecciona solo el sector educación y une todos los meses en una única tabla. Así se obtiene la información de apropiación, compromisos, obligaciones y pagos sin necesidad de revisar archivo por archivo.

El trabajo más profundo se realizó con Saber Pro. Esta base tiene más de un millón de estudiantes entre 2021 y 2024 y contiene noventa variables. Para manejar esta cantidad de información se creó un modelo estrella que se observa a continuación:

<p align="center">
  <img width="1252" height="454" alt="Figura . Modelo Estrella" src="https://github.com/user-attachments/assets/6a1885f5-c095-4d6d-99ec-1a025f714530" />
  <br>
  <strong>Figura 1.</strong> Modelo Estrella
</p>

En el centro del modelo está la tabla donde guardamos los puntajes de cada estudiante. A su alrededor están las dimensiones, que son tablas más pequeñas que describen información básica como quién es el estudiante, en qué institución estudia, cuál es su programa, cómo es su hogar y a qué año corresponde el registro. Al unir estas tablas se forma la tabla de hechos, que es la que conecta toda la información y guarda los resultados del examen. Esta organización ayuda a manejar bien la cantidad de datos y hace que el análisis sea más fácil y ordenado.

Una vez construido el modelo, se realizaron tres tipos de análisis: univariado, bivariado y multivariado. En el análisis univariado se revisaron las distribuciones de las variables, los valores atípicos, los tipos de datos y la presencia de duplicados o inconsistencias. En el análisis bivariado se compararon relaciones entre variables numéricas y categóricas. Finalmente, se exploraron métodos como componentes principales y análisis factorial con el fin de identificar patrones en los datos.

---

## Resultados

### 1) Alcance y composición de la base 

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Distrib%20sexo.png" alt="Figura 2. Distribución Género" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 2.</strong> Distribución Género
</p>

En el grupo de estudiantes que presentó el Saber Pro entre 2021 y 2024 vemos que participaron más mujeres que hombres. De 1.015.276 personas, 588.790 son mujeres aproximadamente un 58% y 426.486 son hombres aproximadamente un 42%. Esto quiere decir que, en estos años, las mujeres fueron mayoría entre quienes presentaron el examen.

### 2) Niveles de desempeño por módulo

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Distrib%20puntajes.png" alt="Figura 3. Distribución puntajes" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 3.</strong> Distribución Puntajes
</p>

El orden de los puntajes promedio muestra un patrón claro: Inglés es el módulo con mejores resultados, seguido por Lectura Crítica. Más abajo aparecen Razonamiento Cuantitativo y Competencias Ciudadanas, que tienen niveles muy parecidos. El puntaje más bajo es el de Comunicación Escrita, que además es el módulo donde los resultados están más dispersos, lo que indica mayor variabilidad entre los estudiantes.

### 3) Evolución temporal 2021–2024

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Puntajes%20anuales.png" alt="Figura 4. Promedio Anual" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 4.</strong> Promedio Anual
</p>

- **Inglés**: nivel alto y estable, con su mejor resultado en 2024.
- **Lectura Crítica**: mejora constante a lo largo de los cuatro años.
- **Razonamiento Cuantitativo**: comportamiento casi igual en todo el periodo.
- **Competencias Ciudadanas**: baja en 2023 y se recupera en 2024.
- **Comunicación Escrita**: la más inestable, con caídas y recuperaciones sin una tendencia clara.

### 4) Participación institucional y modalidad

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Universidades.jpg" alt="Figura 5. Universidades" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 5.</strong> Universidades
</p>

Las instituciones con mayor participación en la cohorte son Uniminuto y el Politécnico Grancolombiano, ya que aportan una parte importante de los estudiantes evaluados. Cuando se comparan las modalidades, los programas presenciales muestran resultados un poco más altos en Razonamiento Cuantitativo. La educación virtual y a distancia se ubica en un punto intermedio, mientras que la semipresencial queda un poco más abajo. Aun así, las diferencias no son muy grandes y los rangos entre modalidades se mezclan bastante.

### 5) Participación departamental

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Departamentos.jpg" alt="Figura 6. Departemnetos" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 6.</strong> Departamentos
</p>

La gráfica evidencia que Bogotá concentra la mayor cantidad de estudiantes por amplio margen, seguida por Antioquia y varios departamentos con volúmenes moderados. En general, la distribución es muy desigual, con un fuerte predominio de las principales ciudades del país en la presentación del SABER-PRO.

### 6) Factores del hogar y brechas asociadas

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/FAMD.png" alt="Figura 7. Componentes" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 7.</strong> Componentes
</p>

En este análisis se observa que las variables del hogar tienen un papel importante en la forma en que se organizan los datos. Las que más pesan son el estrato de vivienda y la educación de la madre y del padre; también cuentan si la familia tiene internet y tiene computador. Todas quedan hacia el lado derecho y un poco arriba, así que la Dimensión 1 puede leerse como un eje socioeconómico/educativo se podría decir que a mayor estrato y mayor educación de los padres, más se ubican los casos hacia ese lado. En ese mismo sentido aparece el puntaje de Inglés, que se alinea sobre todo con la Dimensión 1. El resto de variables como género, nivel del programa, carácter académico y los otros puntajes, queda cerca del centro, por lo que en este plano aportan poco.

### 7) Relaciones entre módulos

<p align="center">
  <img src="https://github.com/ustadistica/Proyecto-Observatorio-Datos-de-Educacion-en-Colombia/blob/main/Imagenes/Correlaciones.png" alt="Figura 8. Relaciones" width="80%" style="border-radius: 8px; border: 1px solid #ccc;">
  <br>
  <strong>Figura 8.</strong> Relaciones
</p>

Los resultados muestran que Lectura Crítica, Razonamiento Cuantitativo y Competencias Ciudadanas suelen moverse juntas: cuando un estudiante tiene buen desempeño en una de estas áreas, normalmente también le va bien en las otras. En cambio, Comunicación Escrita no se relaciona tanto con los demás módulos, lo que indica que su comportamiento es más independiente.

### 8) Análisis multivariado (FAMD)

El análisis muestra que la información no se concentra en un solo eje. La primera dimensión explica alrededor del 6,6%, las dos primeras juntas llegan al 10,9% y las seis primeras alcanzan cerca del 28%. Esto quiere decir que no hay una única línea que ordene completamente los datos. La Dimensión 1 está muy relacionada con las condiciones del hogar, como el estrato, la educación de los padres y el acceso a internet y computador. En esa misma dirección aparece el módulo de Inglés, que es el que más se conecta con este nivel socioeconómico.

---

## Análisis de resultados

El análisis muestra que el desempeño académico está relacionado con varios factores del contexto. Una de las diferencias más claras aparece en el nivel socioeconómico. Los estudiantes que viven en hogares con mejores condiciones suelen obtener puntajes más altos, lo que refleja desigualdades que no nacen en el examen sino que vienen de todo su proceso educativo. Este patrón se ve en los módulos, pero es más marcado en Inglés, que es la prueba donde aparecen las brechas más grandes.

Cuando se mira la base completa, que reúne más de un millón de estudiantes entre 2021 y 2024, se ve que tiene la fuerza suficiente para analizar diferencias por instituciones, por modalidad, por estrato y por regiones. La distribución por género es amplia y equilibrada, por lo que no requiere ajustes adicionales. Esto permite trabajar con la base sin miedo a que pequeñas variaciones cambien los resultados de manera artificial.

Sobre los puntajes, se mantiene un patrón constante se observo que inglés es el módulo con el promedio más alto, seguido por Lectura Crítica. Luego vienen Razonamiento Cuantitativo y Competencias Ciudadanas, que están en un punto intermedio. Comunicación Escrita queda como el módulo más bajo y también el más variable, lo que muestra que esta competencia presenta mayores retos para la mayoría de estudiantes. Esto puede ser una señal para orientar esfuerzos que fortalezcan la escritura académica, que es una habilidad fundamental para el desarrollo profesional.

Cuando se recorren los años, las tendencias son estables. Inglés se mantiene alto y mejora en 2024. Lectura avanza de forma constante. Razonamiento cuantitativo prácticamente no cambia. Competencias ciudadanas baja en 2023 pero se recupera en 2024. Comunicación Escrita es la que más sube y baja, por lo que su comportamiento es más difícil de anticipar. En lugar de quedarse solo con lo que pasa en un año, es mejor mirar cómo se comporta cada módulo en el tiempo y si mantiene una tendencia clara o no.

A nivel institucional, el peso de algunas universidades es muy grande. Instituciones como Uniminuto o el Politécnico Grancolombiano aportan una parte importante de los estudiantes evaluados, lo que influye en la composición general de la base. Cuando se comparan modalidades, la mayoría sigue siendo presencial. Aunque se observan pequeñas diferencias entre presencial, virtual y distancia, estas diferencias no son lo suficientemente grandes como para decir que la modalidad, por sí sola, explica el rendimiento, ya que detrás también hay variaciones por área, nivel del programa y perfiles de los estudiantes.

En el análisis por departamentos, la mayor concentración se encuentra en Bogotá, que supera ampliamente a cualquier otra región del país. Antioquia ocupa el segundo lugar, y después vienen departamentos como Atlántico, Valle y Santander. Esto muestra que la población evaluada se concentra en las grandes zonas urbanas, donde también se agrupa buena parte de la oferta educativa.

Los datos muestran que el hogar sí marca diferencias. El estrato, la educación de los padres y tener internet y computador en casa están asociados con mejores resultados. Estas variables reflejan un nivel socioeconómico más alto, y hacia ese mismo lado se mueve el puntaje de Inglés, que es el que más se relaciona con estas ventajas. En cambio, variables como el género, el nivel del programa o el tipo de institución casi no cambian la forma en que se agrupan los estudiantes en este análisis.

Cuando se analizan las relaciones entre módulos, se observa que Lectura Crítica es un punto de conexión importante. Tiende a moverse junto con Razonamiento Cuantitativo y Competencias Ciudadanas, lo que sugiere que quienes leen y comprenden mejor también suelen tener buenos resultados en las demás competencias. Inglés también tiene cierta relación con estas habilidades, aunque es más sensible al contexto socioeconómico. Comunicación Escrita, por el contrario, tiene una relación más débil con los otros módulos y sigue un patrón más independiente.

Aunque este proyecto también trabajó con SNIES y con el PTE, en esta fase no se unieron esas bases con los datos de Saber Pro. Cada fuente maneja un nivel distinto: Saber Pro trabaja a nivel de estudiante, SNIES a nivel de instituciones y programas, y el PTE a nivel de sector presupuestal. Estas estructuras no tienen llaves que permitan unirlas sin correr el riesgo de mezclar información incorrecta. Por esa razón, los resultados presentados en esta parte se basan únicamente en Saber Pro, que es la base más sólida y homogénea.

Sin embargo, el trabajo realizado con las otras dos fuentes no se pierde. Los datos de SNIES y del PTE ya quedaron descargados, limpios y documentados, y el sistema está preparado para recibir nuevos años sin repetir todo el proceso. Esto permite que, en el futuro, se puedan integrar análisis más amplios que combinen cobertura, calidad y presupuesto. El observatorio que se construyó queda como una base para que este tipo de estudios crezca y se fortalezca con el tiempo.

---

## Conclusión 

El proyecto alcanza su propósito al entregar un observatorio de datos del sistema educativo para 2021 a 2024 que integra fuentes oficiales, estandariza formatos y deja un flujo reproducible de ingesta, limpieza y validación listo para incorporar nuevos años sin rehacer procesos. El modelo en estrella construido sobre Saber Pro, con más de un millón de registros y noventa variables, permite consultas eficientes y análisis consistentes, mientras que los controles de calidad y la documentación técnica aseguran trazabilidad, auditoría y transferencia a otros equipos.

El examen de resultados muestra un sistema estable en el que Inglés se mantiene sólido, Lectura Crítica mejora de manera sostenida, Razonamiento Cuantitativo y Competencias Ciudadanas se ubican en una franja media y Comunicación Escrita aparece rezagada y con mayor variabilidad. Las diferencias asociadas al contexto del hogar se observan de forma consistente pero con magnitud moderada, y las variaciones por modalidad existen aunque presentan alto solapamiento, por lo que conviene interpretar comparaciones con controles adecuados. La estructura multivariada confirma un comportamiento verdaderamente multidimensional, con Lectura como eje articulador del desempeño y Escrita como dimensión que exige acciones específicas.

El valor para la gestión queda claro al contar con una línea base confiable, métricas estandarizadas y un camino de actualización simple que reduce tiempos operativos y mejora la comparabilidad entre periodos y grupos. El alcance de esta versión prioriza el análisis profundo de Saber Pro y deja SNIES y PTE preparados para usos agregados y futuros cruces, reconociendo que los vínculos a nivel individual no se implementaron por diferencias de granularidad y que las relaciones reportadas son asociativas. Con esta base, la organización queda en posición de integrar 2025 con mínimo esfuerzo, profundizar en intervenciones sobre Comunicación Escrita y ampliar los análisis con las demás fuentes para sostener una mejora continua y equitativa.

---

## Bibliografía

- ICFES. (2024). Examen Saber Pro – Competencias Genéricas 2024. SharePoint institucional del ICFES.
- ICFES. (2023). Examen Saber Pro – Competencias Genéricas 2023. SharePoint institucional del ICFES.
- ICFES. (2022). Examen Saber Pro – Competencias Genéricas 2022. SharePoint institucional del ICFES.
- ICFES. (2021). Examen Saber Pro – Competencias Genéricas 2021. SharePoint institucional del ICFES.


