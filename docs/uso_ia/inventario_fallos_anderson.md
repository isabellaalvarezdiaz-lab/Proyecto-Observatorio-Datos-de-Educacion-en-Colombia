# INVENTARIO DE FALLOS — Anderson González

> Redactado con ayuda de la IA a partir de las salidas de PowerShell y de la
> bitácora (`docs/BITACORA_IA.md`); revisado y completado por Anderson.

## Fallo 1

- **Herramienta:** Claude (Anthropic), sesión del 12 de octubre de 2026.
- **Qué generó:** instrucciones de PowerShell para subir los resultados del OE2 y el OE3 que no excluían `__pycache__`.
- **Qué estaba mal:** el commit `9414a9f` subió a GitHub el archivo `scripts/__pycache__/dea.cpython-311.pyc`, que es un archivo compilado de Python y no debe estar en el repositorio.
- **Cómo se detectó:** la salida del commit lo listaba entre los archivos creados.
- **Qué me costó:** un commit adicional (`2fdded9`) para agregarlo al `.gitignore` y retirarlo.
- **Qué lo habría evitado:** revisar `git status` antes de cada commit y tener el `.gitignore` completo desde el inicio.

## Fallo 2

- **Herramienta:** Claude (Anthropic), sesión del 12 de octubre de 2026.
- **Qué generó:** instrucciones de PowerShell con una ruta de ejemplo (`cd "C:\ruta\Proyecto-..."`) en lugar de la ruta real, y la ubicación supuesta del zip en Descargas.
- **Qué estaba mal:** al ejecutarlas tal cual, el `cd` falló, el zip no se encontró y corrieron los scripts anteriores. Se subió el commit `1a84cef`, con el mensaje "OE3: cobertura sin UNAD y segunda etapa exploratoria", que solo contenía un archivo de evidencia.
- **Cómo lo detecté:** los errores en rojo de PowerShell ("No se encuentra la ruta de acceso" y "no existe o no es una ruta de acceso válida").
- **Qué me costó:** unos 25 minutos entre entender los errores y volver a correr todo, y un commit con un mensaje que no corresponde a su contenido.
- **Qué lo habría evitado:** buscar el archivo antes de usarlo y comprobar con `Test-Path` que los scripts llegaron, antes de correrlos y hacer el commit; ejecutar los comandos por bloques y no todos de una vez.

## Fallo 3

- **Herramienta:** Claude (Anthropic), sesiones del 12 de octubre de 2026.
- **Qué generó:** el cálculo de las correlaciones de Spearman en `oe3_dea_bootstrap.py` y `oe3_cobertura_sin_unad.py`.
- **Qué estaba mal:** no trataba como empatadas a las universidades de la frontera (eficiencia 1), porque el solver devuelve valores como 0,9999999998 y 1,0000000001. Las correlaciones de `oe3_deja_uno_fuera.csv`, `oe3_sensibilidad.csv` y del modelo sin la UNAD, ya subidas a GitHub, estaban desviadas hasta en 0,02.
- **Cómo se detectó:** la IA lo notó al recalcular las correlaciones desde los CSV para escribir el informe.
- **Qué me costó:** volver a correr el DEA con bootstrap y el modelo sin la UNAD (unos 15 minutos) y un commit de corrección (`5a8f02e`). Ninguna eficiencia cambió.
- **Qué lo habría evitado:** que el verificador revisara desde el principio también las correlaciones de Spearman; ahora lo hace.

## Fallo 4

- **Herramienta:** Claude (Anthropic), sesión del 13 de octubre de 2026.
- **Qué generó:** una cifra escrita a mano en el texto del informe final.
- **Qué estaba mal:** la eficiencia corregida de la Universidad Tecnológica del Chocó en 2024 aparecía como 0,688 [0,674; 0,699], pero la tabla calculada da 0,689 [0,673; 0,699].
- **Cómo se detectó:** la IA lo encontró al revisar el informe contra los CSV de resultados.
- **Qué me costó:** volver a generar el informe antes de entregarlo; el error no llegó a ninguna entrega.
- **Qué lo habría evitado:** que ninguna cifra del texto se escriba a mano. Ahora esa frase también se genera desde los CSV.

## Fallo 5

- **Herramienta:** Claude (Anthropic), sesión del 13 de octubre de 2026.
- **Qué generó:** la redacción del informe sobre la segunda etapa exploratoria.
- **Qué estaba mal:** decía que la acreditación institucional no pasaba el ajuste de Holm en ningún año, pero en 2023, en el modelo principal, su p ajustado es 0,046.
- **Cómo se detectó:** la IA lo encontró al comparar el texto con `resultados/oe3_segunda_etapa.csv`.
- **Qué me costó:** corregir la redacción y volver a generar el informe antes de entregarlo.
- **Qué lo habría evitado:** contrastar cada afirmación del texto con la tabla de la que sale, no con el recuerdo de los resultados.

## Fallo 6

- **Herramienta:** Claude (Anthropic), sesión del 13 de octubre de 2026.
- **Qué generó:** una cita de Visbal-Cadavid et al. (2017) en la discusión frente a la literatura.
- **Qué estaba mal:** atribuía el ordenamiento de las universidades a la página 1, pero está en la tabla 10, en las páginas 14 y 15.
- **Cómo se detectó:** la IA lo encontró al revisar las citas del informe.
- **Qué me costó:** corregir la cita antes de entregar el informe.
- **Qué lo habría evitado:** citar siempre con la página verificada en el PDF original, como pide la regla "nada sin fuente".
