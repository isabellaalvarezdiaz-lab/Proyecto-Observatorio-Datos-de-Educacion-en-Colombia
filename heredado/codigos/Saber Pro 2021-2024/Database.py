import sqlite3
import pandas as pd
import os

# -------------------------------------------------
# 1. Definir ruta de archivos y nombres de tablas
# -------------------------------------------------
# Supongamos que tienes 5 archivos .txt en el directorio actual
archivos_txt = [

    ("SaberPro2021", os.path.join("Datos", "Examen_Saber_Pro_Genericas_2021.txt")),
    ("SaberPro2022", os.path.join("Datos", "Examen_Saber_Pro_Genericas_2022.txt")),
    ("SaberPro2023", os.path.join("Datos", "Examen_Saber_Pro_Genericas_2023.txt")),
    ("SaberPro2024", os.path.join("Datos", "Examen_Saber_Pro_Genericas_2024.txt")),
]

# -------------------------------------------------
# 2. Crear/conectar la base de datos SQLite
# -------------------------------------------------
nombre_db = "SaberPro2021_2024.db"
conn = sqlite3.connect(nombre_db)
cursor = conn.cursor()

# -------------------------------------------------
# 3. Cargar cada archivo .txt en un DataFrame
# -------------------------------------------------
# Nota: Ajusta los parámetros de read_csv según tu formato de .txt
#       (por ejemplo delimitador = "\t", encoding, header, etc.)
for nombre_tabla, archivo in archivos_txt:
    if os.path.exists(archivo):
        df = pd.read_csv(archivo, sep=";", encoding="utf-8")  # ejemplo con tabulador
        print(f"Cargando {archivo} en la tabla {nombre_tabla}...")

        # -------------------------------------------------
        # 4. Insertar el DataFrame en la base de datos
        # -------------------------------------------------
        df.to_sql(nombre_tabla, conn, if_exists="replace", index=False)
    else:
        print(f"⚠️ El archivo {archivo} no se encontró. Saltando...")

# -------------------------------------------------
# 5. Confirmar cambios y cerrar conexión
# -------------------------------------------------
conn.commit()
conn.close()


print(f"✅ Base de datos '{nombre_db}' creada con las 4 tablas.")

#-------------------------------------------------
# Nota: Puedes verificar las tablas creadas usando herramientas como DB Browser for SQLite
#       o mediante consultas SQL en Python.
#-------------------------------------------------
# Ejemplo para verificar tablas:
conn = sqlite3.connect(nombre_db)
cursor = conn.cursor()
query = "SELECT name FROM sqlite_master WHERE type='table';"
cursor.execute(query)
tablas = cursor.fetchall()
print("Tablas en la base de datos:", tablas)

# Ejemplo: leer toda la tabla "SaberPro2021"
df_1 = pd.read_sql("SELECT * FROM SaberPro2021;", conn)
print(df_1.columns )