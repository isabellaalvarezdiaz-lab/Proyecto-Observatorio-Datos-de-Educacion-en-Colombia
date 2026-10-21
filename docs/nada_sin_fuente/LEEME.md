# «Nada sin fuente» — gestión de la información y uso de IA (septiembre de 2026)

Actividad evaluada del curso (docente: Javier Mauricio Sierra). Es la estrategia de gestión de la
información del proyecto: cómo se eligió la herramienta para consultar el estado del arte, cómo se
verificó cada afirmación del anteproyecto contra el documento original y qué se corrigió.

Equipo: Isabella Álvarez, Eduar Caicedo, Anderson González.

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `Memoria_Final.docx` | Memoria de la actividad: diagnóstico, experimento y decisión, sistema, evaluación, correcciones al anteproyecto y declaración de uso de IA |
| `Inventario Fallos.docx` | Inventario de fallos de IA de los tres integrantes, firmado, con capturas |
| `Experimento_Semana.xlsx` | Experimento: 45 referencias (3 integrantes × 3 herramientas × 5), clasificación a ciegas, consolidado y resultados |
| `Banco_Evaluacion.xlsx` | Banco de 22 preguntas (19 con respuesta y 3 sin respuesta en el corpus), corrida y resultados |
| `protocolo_v1.md`, `protocolo_v2.md` | Protocolo de consulta del cuaderno de NotebookLM y su versión corregida |
| `corpus/README.md` | Procedencia de los 13 documentos del estado del arte (origen, licencia, quién lo verificó) |
| `corpus/observatorio-estado-del-arte.rdf` | Exportación de la biblioteca de Zotero |
| `anteproyecto_corregido_2026-10-04.pdf` | Anteproyecto con las seis afirmaciones corregidas (se entregó como `Consultoria_Ante_Poyecto.pdf`). El anteproyecto original está en `docs/Consultoria.pdf` |
| `Trazabilidad_Final.xlsx`, `Anexo_Pruebas_Herramienta.docx` | Tabla de trazabilidad y anexo de pruebas de herramienta, que cita la memoria |
| `scripts/extraer.py` | Verifica que los PDF del corpus tengan capa de texto |
| `scripts/prueba-via-propia/` | Sistema propio (Ollama + Chroma) que se construyó, se midió y se descartó |
| `tablero_nada_sin_fuente/app.R` | Tablero en R/Shiny con que se presentó la actividad (`shiny::runApp("tablero_nada_sin_fuente")`) |

## Qué no está y por qué

- **Los 13 PDF del corpus.** Varios no son de acceso abierto (por ejemplo, Charnes et al., 1978,
  de Elsevier) y no se pueden redistribuir. `corpus/README.md` dice de dónde sale cada uno.

## Procedencia de estos archivos

Todos salen del paquete que el equipo identificó como el entregado, salvo `Trazabilidad_Final.xlsx`,
`Anexo_Pruebas_Herramienta.docx` y `scripts/`, que salen del paquete preparado antes de la entrega,
porque el entregado no los trae aunque la memoria y el tablero los citan. Se subieron sin
modificar el 20-10-2026.

Quedaron sin completar en los archivos entregados, y se dejan así:
- `protocolo_v2.md`: los campos `[fecha]` y `[probada / pendiente]` de la última línea.
- `corpus/README.md`: la línea de la verificación con `extraer.py` dice «[1099] de 13 documentos
  con texto, [P] páginas»; el 1099 no puede ser un número de documentos. La misma línea cita
  `evidencias/extraer_salida.txt`, que no viene en ninguno de los dos paquetes.
