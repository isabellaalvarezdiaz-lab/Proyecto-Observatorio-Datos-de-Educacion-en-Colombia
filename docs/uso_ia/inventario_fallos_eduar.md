# INVENTARIO DE FALLOS — Eduar Caicedo

> Redactado con ayuda de la IA a partir de lo que recuerda Eduar y de las
> evidencias del repositorio (`docs/gobernanza/evidencias/`) y del experimento
> de la actividad «Nada sin fuente»; revisado y completado por Eduar.

## Fallo 1

- **Herramienta:** Claude (Anthropic), sesión del 16 de septiembre de 2026.
- **Qué generó:** el procedimiento para descargar las bases del SNIES siguiendo la forma en que lo hizo el equipo anterior: su scraper (`heredado/codigos/scraper_snies.py`) y su mapa de identificadores de archivos (`heredado/codigos/snies_renamed_registros.py`).
- **Qué estaba mal:** el método heredado no reconocía los archivos que publica hoy el SNIES. En la corrida del 16 de septiembre avisó, para cada año de 2021 a 2025, que faltaban todas las categorías (administrativos, docentes, admitidos, inscritos, matriculados y primer curso). De lo poco que reconoció, clasificó "Estudiantes Graduados 2022" como `Desconocido` y tomó "Metadatos bases consolidadas 2023" como si fuera una base de datos.
- **Cómo lo detecté:** por las advertencias del registro de la corrida y por el manifiesto de descargas (`scraper_snies_log_2026-09-16.txt` y `scraper_snies_manifest_2026-09-16.csv`).
- **Qué me costó:** revisar archivo por archivo qué contenía cada descarga, leyendo su título interno con `scripts/revisar_snies.py` (`revision_snies_contenido_2026-09-16.txt`). Esa revisión mostró además que dos descargas, `articles-421540` y `articles-425153`, son el mismo archivo con datos de 2023, aunque el segundo se publica con los de 2024.
- **Qué lo habría evitado:** no reutilizar el método del equipo anterior sin probarlo antes con los archivos actuales, y confirmar el contenido de cada archivo por su título interno, no por su nombre.

## Fallo 2

- **Herramienta:** Claude (Anthropic), septiembre de 2026.
- **Qué generó:** código para leer los archivos de matriculados y graduados del SNIES que saltaba un número fijo de filas de título antes del encabezado.
- **Qué estaba mal:** el encabezado no está en la misma fila todos los años: está en la fila 10 en 2021, en la 8 en 2022 y en la 5 en 2023 y 2024. Además, varias columnas cambiaron de nombre en 2023 (METODOLOGÍA pasó a MODALIDAD y PRINCIPAL O SECCIONAL a TIPO IES), algunas cambiaron de posición y los encabezados de Graduados 2022 tienen errores de escritura. Con filas fijas, los años distintos se leían mal.
- **Cómo se detectó:** no lo detecté yo al principio. Salió al revisar con la misma IA la estructura de los archivos de los cuatro años con `scripts/encabezados_snies.py` (`encabezados_snies_2026-09-16.txt`).
- **Qué me costó:** escribir ese script de revisión y cambiar la forma de cargar el SNIES: ahora se busca la fila del encabezado en cada archivo y las columnas se unen por nombre, con una tabla de equivalencias.
- **Qué lo habría evitado:** revisar la estructura de todos los años antes de escribir el código de carga, y no suponer que el formato de un año sirve para los demás.

## Fallo 3

- **Herramienta:** ChatGPT (OpenAI), tratamiento A ("chat sin fuentes") del experimento de la actividad «Nada sin fuente», septiembre de 2026.
- **Qué generó:** cinco referencias sobre aplicaciones del DEA a la eficiencia de universidades públicas en América Latina, con la afirmación que atribuía a cada una (filas R16 a R20 de `Experimento_Semana1_Final.xlsx`).
- **Qué estaba mal:** cuatro de las cinco no servían:
  - tres no existen: Melo-Becerra y Vásquez (2019), González y Callejas (2011) y Agasisti et al. (2016). De esta última solo se encontró un trabajo de uno de los autores, del mismo año y con otro título;
  - una existe pero no dice lo que afirmaba la IA: Ramanathan (2003), que según su resumen estudia empresas de China, no la base metodológica del DEA para universidades.

  Solo una, Johnes (2006), resultó utilizable. Dos de las cinco venían sin DOI ni URL, y otras dos con enlaces que no funcionaban.
- **Cómo lo detecté:** buscando cada referencia por título y autores en Google Académico y en el buscador web, y abriendo los enlaces que daba la IA.
- **Qué me costó:** el tiempo de verificar cada referencia a mano. Ninguna de las cuatro entró al estado del arte ni al informe.
- **Qué lo habría evitado:** no pedir referencias a un chat sin fuentes. Por eso el equipo eligió NotebookLM con los PDF verificados del estado del arte.
