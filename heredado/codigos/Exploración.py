import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

### Conectar con el database
nombre_db = "SaberPro2021_2024.db"
conn = sqlite3.connect(nombre_db)
cursor = conn.cursor()

# --- Resumen de tamaño de tablas ---
tables = ["dim_estudiante", "dim_institucion", "dim_programa", "dim_tiempo", "dim_familia", "fact_resultados"]

for t in tables:
    df = pd.read_sql(f"SELECT * FROM {t}", conn)
    print(f"\nTabla: {t}")
    print("Registros totales:", len(df))
    print("Columnas:", list(df.columns))

# --- Distribución de variables clave en dimensiones ---
# Género
dim_estudiante = pd.read_sql("SELECT * FROM dim_estudiante WHERE estu_genero <> 'L'", conn)
print("\nDistribución de género:")
print(dim_estudiante["estu_genero"].value_counts(dropna=True))

sns.countplot(data=dim_estudiante, x="estu_genero", order=dim_estudiante["estu_genero"].value_counts().index)
plt.title("Distribución de género")
plt.show()

# Etnia
print("\nDistribución de etnia:")
print(dim_estudiante[dim_estudiante["estu_etnia"] != 'Ninguno']["estu_etnia"].value_counts(dropna=True).head(10))

sns.countplot(data=dim_estudiante[dim_estudiante["estu_etnia"] != 'Ninguno'], x="estu_etnia", order=dim_estudiante[dim_estudiante["estu_etnia"] != 'Ninguno']["estu_etnia"].value_counts().head(10).index)
plt.title("Principales etnias (top 10)")
plt.xticks(rotation=45)
plt.show()



# --- Estadísticas descriptivas de la fact table ---
fact = pd.read_sql("SELECT * FROM fact_resultados", conn)

print("\nEstadísticas descriptivas de los puntajes:")
print(fact[[
    "mod_competen_ciudada_punt", "mod_comuni_escrita_punt", 
    "mod_ingles_punt", "mod_lectura_critica_punt", 
    "mod_razona_cuantitat_punt"
]].describe().applymap(lambda x: f"{x:.0f}" if float(x).is_integer() else f"{x:.2f}"))

sns.pairplot(fact[[
    "mod_competen_ciudada_punt", "mod_comuni_escrita_punt", 
    "mod_ingles_punt", "mod_lectura_critica_punt", 
    "mod_razona_cuantitat_punt"
]].rename(columns={
    "mod_competen_ciudada_punt": "Ciudadana",
    "mod_comuni_escrita_punt": "Escrita",
    "mod_ingles_punt": "Inglés",
    "mod_lectura_critica_punt": "Lectura",
    "mod_razona_cuantitat_punt": "Cuantitativo"
}).sample(500, random_state=42))  # muestra para que no explote
plt.title("Relaciones entre puntajes")
plt.show()

# --- Cruce: Puntaje global por año ---
query = """
SELECT t.anio, 
       AVG(f.mod_competen_ciudada_punt) AS avg_ciudadana,
       AVG(f.mod_comuni_escrita_punt) AS avg_comunicacion,
       AVG(f.mod_ingles_punt) AS avg_ingles,
       AVG(f.mod_lectura_critica_punt) AS avg_lectura,
       AVG(f.mod_razona_cuantitat_punt) AS avg_razonamiento
FROM fact_resultados f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
GROUP BY t.anio
ORDER BY t.anio;
"""
df_year = pd.read_sql(query, conn)
print("\nPromedios de puntaje por año:")
print(df_year)

df_year.set_index("anio").plot(kind="bar", figsize=(10,6))
plt.title("Evolución de los puntajes promedio por año")
plt.ylabel("Puntaje promedio")
plt.show()
