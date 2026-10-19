# INVENTARIO DE FALLOS — Isabella Álvarez

## Fallo 1

- **Herramienta:** Claude (Anthropic), sesión del 9 de septiembre de 2026.
- **Qué generó:** la cita "Rodrigues & Bermejo (2024), Cogent Education, 11(1)" para el estado del arte.
- **Qué estaba mal:** la referencia real es Almeida, J. P. L. de, Anjos, F. H. dos, Moreira, M. F., Bermejo, P. H. de S., Prata, D. N., & Rodrigues, W. (2024), Cogent Education, 12(1), art. 2445964. Faltaban cuatro de los seis autores y el volumen era incorrecto.
- **Cómo lo detecté:** al buscarla directamente en una sesión posterior, no aparecía con esos datos.
- **Qué me costó:** [tiempo de verificación; si alcanzó a entrar a algún borrador]
- **Qué lo habría evitado:** buscar el título en una base bibliográfica real y copiar los datos desde la página del artículo, no desde la respuesta de la IA.

## Fallo 2

- **Herramienta:** Claude (Anthropic), sesión del 16 y 17 de septiembre de 2026.
- **Qué generó:** el supuesto de trabajo de que el PTE desagrega el presupuesto de las 34 universidades públicas en todos los años del periodo 2021-2024, a partir de haberlo verificado solo en el archivo de diciembre de 2024.
- **Qué estaba mal:** la desagregación solo existe desde 2023. En 2022 las 9 entidades del sector Educación suman exactamente el total del sector (49.755.576.349.304 pesos), y el dinero de las universidades está en rubros globales del Ministerio de Educación, no por universidad.
- **Cómo lo detecté:** al correr el script de extracción sobre los archivos de 2022, 2023, 2024 y 2025, que encontró 0 universidades en 2022; luego lo confirmé listando todas las entidades del sector Educación de ese año.
- **Qué me costó:** el periodo del proyecto pasó de 2021-2024 a 2023-2024; OE3 bajó de 136 a 68 observaciones y OE2 dejó de ser viable como DEA nacional. Hay que ajustar el anteproyecto y comunicarlo al profesor.
- **Qué lo habría evitado:** verificar un hallazgo en todos los años del periodo antes de construir el diseño sobre él, no solo en el archivo disponible.

## Fallo 3

- **Herramienta:** Claude (Anthropic), sesión del 16 de septiembre de 2026.
- **Qué generó:** la primera versión de extraer_validar_pte.py.
- **Qué estaba mal:** no reconocía rubros con código tipo "02----" y los confundía con nombres de sector. Encontró 0 universidades en 2024 y marcó los 34 rubros del artículo 86 como externos a las universidades.
- **Cómo lo detecté:** al correr el script, la salida no coincidía con los valores ya verificados a mano para 2024 (34 universidades, 8,92% del sector Educación).
- **Qué me costó:** una corrida adicional, y la evidencia del error se perdió porque la segunda ejecución sobrescribió el archivo con el mismo nombre.
- **Qué lo habría evitado:** probar el script contra datos conocidos antes de usarlo con años nuevos (fue justamente lo que lo detectó) y nombrar las evidencias con fecha y hora para no sobrescribirlas.
