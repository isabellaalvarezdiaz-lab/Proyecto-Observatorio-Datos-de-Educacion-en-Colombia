# INVENTARIO DE FALLOS — Anderson González

> Borrador preparado con la IA a partir de las salidas de PowerShell de las
> sesiones del 12 y 13 de octubre de 2026. Anderson debe revisarlo y completar
> los campos entre corchetes antes de subirlo.

## Fallo 1

- **Herramienta:** Claude (Anthropic), sesión del 12 de octubre de 2026.
- **Qué generó:** instrucciones de PowerShell para subir los resultados del OE2 y el OE3 que no excluían `__pycache__`.
- **Qué estaba mal:** el commit `9414a9f` subió a GitHub el archivo `scripts/__pycache__/dea.cpython-311.pyc`, que es un archivo compilado de Python y no debe estar en el repositorio.
- **Cómo se detectó:** la salida del commit lo listaba entre los archivos creados.
- **Qué me costó:** un commit adicional (`2fdded9`) para agregarlo al `.gitignore` y retirarlo. [completar si hubo algo más]
- **Qué lo habría evitado:** revisar `git status` antes de cada commit y tener el `.gitignore` completo desde el inicio.

## Fallo 2

- **Herramienta:** Claude (Anthropic), sesión del 12 de octubre de 2026.
- **Qué generó:** instrucciones de PowerShell con una ruta de ejemplo (`cd "C:\ruta\Proyecto-..."`) en lugar de la ruta real, y la ubicación supuesta del zip en Descargas.
- **Qué estaba mal:** al ejecutarlas tal cual, el `cd` falló, el zip no se encontró y corrieron los scripts anteriores. Se subió el commit `1a84cef`, con el mensaje "OE3: cobertura sin UNAD y segunda etapa exploratoria", que solo contenía un archivo de evidencia.
- **Cómo lo detecté:** los errores en rojo de PowerShell ("No se encuentra la ruta de acceso" y "no existe o no es una ruta de acceso válida").
- **Qué me costó:** [tiempo de la corrida repetida]; un commit con un mensaje que no corresponde a su contenido.
- **Qué lo habría evitado:** buscar el archivo antes de usarlo y comprobar con `Test-Path` que los scripts llegaron, antes de correrlos y hacer el commit; ejecutar los comandos por bloques y no todos de una vez.

## Fallo 3

- **Herramienta:** Claude (Anthropic), sesiones del 12 de octubre de 2026.
- **Qué generó:** el cálculo de las correlaciones de Spearman en `oe3_dea_bootstrap.py` y `oe3_cobertura_sin_unad.py`.
- **Qué estaba mal:** no trataba como empatadas a las universidades de la frontera (eficiencia 1), porque el solver devuelve valores como 0,9999999998 y 1,0000000001. Las correlaciones de `oe3_deja_uno_fuera.csv`, `oe3_sensibilidad.csv` y del modelo sin la UNAD, ya subidas a GitHub, estaban desviadas hasta en 0,02.
- **Cómo se detectó:** la IA lo notó al recalcular las correlaciones desde los CSV para escribir el informe.
- **Qué me costó:** volver a correr el DEA con bootstrap y el modelo sin la UNAD (unos 15 minutos) y un commit de corrección (`5a8f02e`). Ninguna eficiencia cambió.
- **Qué lo habría evitado:** que el verificador revisara desde el principio también las correlaciones de Spearman; ahora lo hace.
