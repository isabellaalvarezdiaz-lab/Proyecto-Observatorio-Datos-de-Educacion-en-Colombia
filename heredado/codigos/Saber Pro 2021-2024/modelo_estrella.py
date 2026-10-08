import sqlite3
import pandas as pd
from graphviz import Digraph

### Conectar con el database
nombre_db = "SaberPro2021_2024.db"
conn = sqlite3.connect(nombre_db)
cursor = conn.cursor()


### Tablas de dimensiones

# Tablas por año
tablas = ["SaberPro2021", "SaberPro2022", "SaberPro2023", "SaberPro2024"]

# Extraer columnas de cada tabla
columnas_por_tabla = {}
for t in tablas:
    cols = pd.read_sql(f"PRAGMA table_info({t});", conn)["name"].tolist()
    columnas_por_tabla[t] = cols

# Calcular la intersección de columnas
columnas_comunes = set(columnas_por_tabla[tablas[0]])
for t in tablas[1:]:
    columnas_comunes = columnas_comunes.intersection(columnas_por_tabla[t])

columnas_comunes = sorted(list(columnas_comunes))  # orden alfabético para consistencia
print("Columnas comunes:", columnas_comunes)

# Crear el query de UNION ALL solo con las comunes
query = " UNION ALL ".join([
    f"SELECT {','.join(columnas_comunes)}, '{anio}' as anio FROM SaberPro{anio}"
    for anio in ["2021", "2022", "2023", "2024"]
])

# Ejecutar y cargar el dataframe final
df_all = pd.read_sql(query, conn)

# Borrar tablas si ya existen (evita duplicados durante pruebas)
cursor.executescript("""
DROP TABLE IF EXISTS fact_resultados;
DROP TABLE IF EXISTS dim_estudiante;
DROP TABLE IF EXISTS dim_institucion;
DROP TABLE IF EXISTS dim_programa;
DROP TABLE IF EXISTS dim_familia;
DROP TABLE IF EXISTS dim_tiempo;
""")

# Crear tablas de dimensiones
cursor.execute("""
CREATE TABLE dim_estudiante (
    id_estudiante INTEGER PRIMARY KEY AUTOINCREMENT,
    estu_consecutivo TEXT,
    estu_tipodocumento TEXT,
    estu_genero TEXT,
    estu_etnia TEXT,
    estu_nacionalidad TEXT,
    estu_fechanacimiento TEXT,
    estu_discapacidad TEXT,
    estu_exterior TEXT,
    estu_horassemanatrabaja INTEGER
);
""")

cursor.execute("""
CREATE TABLE dim_institucion (
    id_institucion INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_cod_institucion TEXT,
    inst_nombre_institucion TEXT,
    inst_departamento TEXT,
    inst_municipio TEXT,
    inst_caracter_academico TEXT,
    inst_origen TEXT
);
""")

cursor.execute("""
CREATE TABLE dim_programa (
    id_programa INTEGER PRIMARY KEY AUTOINCREMENT,
    estu_snies_prgmacademico TEXT,
    estu_prgm_academico TEXT,
    estu_nivel_prgm_academico TEXT,
    estu_metodo_prgm TEXT,
    estu_nucleo_pregrado TEXT
);
""")

cursor.execute("""
CREATE TABLE dim_familia (
    id_familia INTEGER PRIMARY KEY AUTOINCREMENT,
    estu_consecutivo TEXT,
    fami_estratovivienda TEXT,
    fami_educacionpadre TEXT,
    fami_educacionmadre TEXT,
    fami_ocupacionpadre TEXT,
    fami_ocupacionmadre TEXT,
    fami_tieneinternet TEXT,
    fami_tienecomputador TEXT,
    fami_tieneserviciotv TEXT,
    fami_tienemotocicleta TEXT,
    fami_tienelavadora TEXT,
    fami_tieneautomovil TEXT,
    fami_tieneconsolavideojuegos TEXT,
    fami_tienehornomicroogas TEXT
);
""")

cursor.execute("""
CREATE TABLE dim_tiempo (
    id_tiempo INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo TEXT,
    anio TEXT
);
""")

# Crear tabla de hechos
cursor.execute("""
CREATE TABLE fact_resultados (
    id_resultado INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante INTEGER,
    id_institucion INTEGER,
    id_programa INTEGER,
    id_familia INTEGER,
    id_tiempo INTEGER,
    mod_competen_ciudada_punt REAL,
    mod_comuni_escrita_punt REAL,
    mod_ingles_punt REAL,
    mod_lectura_critica_punt REAL,
    mod_razona_cuantitat_punt REAL,
    FOREIGN KEY (id_estudiante) REFERENCES dim_estudiante(id_estudiante),
    FOREIGN KEY (id_institucion) REFERENCES dim_institucion(id_institucion),
    FOREIGN KEY (id_programa) REFERENCES dim_programa(id_programa),
    FOREIGN KEY (id_familia) REFERENCES dim_familia(id_familia),
    FOREIGN KEY (id_tiempo) REFERENCES dim_tiempo(id_tiempo)
);
""")

# Dim Estudiante
dim_estudiante_cols = [
    "estu_consecutivo", "estu_tipodocumento", "estu_genero", "estu_etnia",
    "estu_nacionalidad", "estu_fechanacimiento", "estu_discapacidad",
    "estu_exterior", "estu_horassemanatrabaja"
]
df_dim_estudiante = df_all[dim_estudiante_cols].drop_duplicates()
df_dim_estudiante.to_sql("dim_estudiante", conn, if_exists="append", index=False)

# Dim Institución
dim_institucion_cols = [
    "inst_cod_institucion", "inst_nombre_institucion",
    "inst_departamento", "inst_municipio",
    "inst_caracter_academico", "inst_origen"
]
df_dim_institucion = df_all[
    ["inst_cod_institucion", "inst_nombre_institucion",
     "estu_inst_departamento", "estu_inst_municipio",
     "inst_caracter_academico", "inst_origen"]
].drop_duplicates("inst_cod_institucion")
df_dim_institucion.columns = dim_institucion_cols  # Renombrar columnas
df_dim_institucion.to_sql("dim_institucion", conn, if_exists="append", index=False)

# Dim Programa
dim_programa_cols = [
    "estu_snies_prgmacademico", "estu_prgm_academico",
    "estu_nivel_prgm_academico", "estu_metodo_prgm",
    "estu_nucleo_pregrado"
]
df_dim_programa = df_all[dim_programa_cols].drop_duplicates("estu_snies_prgmacademico")
df_dim_programa.to_sql("dim_programa", conn, if_exists="append", index=False)

# Dim Familia
dim_familia_cols = [
    "estu_consecutivo", "fami_estratovivienda", "fami_educacionpadre",
    "fami_educacionmadre", "fami_ocupacionpadre", "fami_ocupacionmadre",
    "fami_tieneinternet", "fami_tienecomputador", "fami_tieneserviciotv",
    "fami_tienemotocicleta", "fami_tienelavadora", "fami_tieneautomovil",
    "fami_tieneconsolavideojuegos", "fami_tienehornomicroogas"
]
df_dim_familia = df_all[dim_familia_cols].drop_duplicates()
df_dim_familia.to_sql("dim_familia", conn, if_exists="append", index=False)

# Dim Tiempo
dim_tiempo_cols = ["periodo", "anio"]
df_dim_tiempo = df_all[dim_tiempo_cols].drop_duplicates()
df_dim_tiempo.to_sql("dim_tiempo", conn, if_exists="append", index=False)

conn.commit()

# Poblar tabla de hechos
# Necesitamos mapear los ids de cada dimensión

df_fact = pd.DataFrame()
fact_cols = [
    "estu_consecutivo", "inst_cod_institucion", "estu_snies_prgmacademico",
    "periodo", "anio",
    "mod_competen_ciudada_punt", "mod_comuni_escrita_punt",
    "mod_ingles_punt", "mod_lectura_critica_punt",
    "mod_razona_cuantitat_punt"
]
df_fact = df_all[fact_cols].copy()
df_fact[["inst_cod_institucion", "estu_snies_prgmacademico", "periodo"]] = df_fact[["inst_cod_institucion", 
                                                                                    "estu_snies_prgmacademico", "periodo"]].astype(str)
df_fact.dtypes


# Mapear id_estudiante
df_fact = df_fact.merge(
    pd.read_sql("SELECT id_estudiante, estu_consecutivo FROM dim_estudiante", conn),
    on="estu_consecutivo", how="left"
)

# Mapear id_institucion
df_fact = df_fact.merge(
    pd.read_sql("SELECT id_institucion, inst_cod_institucion FROM dim_institucion", conn),
    on="inst_cod_institucion", how="left"
)

# Mapear id_programa
df_fact = df_fact.merge(
    pd.read_sql("SELECT id_programa, estu_snies_prgmacademico FROM dim_programa", conn),
    on="estu_snies_prgmacademico", how="left"
)

# Mapear id_tiempo
df_fact = df_fact.merge(
    pd.read_sql("SELECT id_tiempo, periodo, anio FROM dim_tiempo", conn),
    on=["periodo", "anio"], how="left"
)

# Mapear id_familia (por consecutivo del estudiante)
df_fact = df_fact.merge(
    pd.read_sql("SELECT id_familia, estu_consecutivo FROM dim_familia", conn),
    on="estu_consecutivo", how="left", suffixes=("", "_fam")
)

# Seleccionamos solo las columnas necesarias para fact_resultados
df_fact_final = df_fact[[
    "id_estudiante", "id_institucion", "id_programa", "id_familia", "id_tiempo",
    "mod_competen_ciudada_punt", "mod_comuni_escrita_punt",
    "mod_ingles_punt", "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"
]].drop_duplicates()

# Insertar en fact_resultados
df_fact_final.to_sql("fact_resultados", conn, if_exists="append", index=False)
conn.commit()

### Visusalización de tablas

pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
pd.read_sql("SELECT * FROM dim_estudiante;", conn)
pd.read_sql("SELECT * FROM dim_institucion;", conn)
pd.read_sql("SELECT * FROM dim_programa;", conn)
pd.read_sql("SELECT * FROM dim_familia;", conn)
pd.read_sql("SELECT * FROM dim_tiempo;", conn)
pd.read_sql("SELECT * FROM fact_resultados;", conn)
pd.read_sql("SELECT * FROM sqlite_sequence;", conn)

conn.close()
print("✅ Modelo estrella creado exitosamente en la base de datos.")

### Graficar el modelo estrella

# Crear el grafo
dot = Digraph("StarSchema", format="png")
dot.attr(rankdir="LR", splines="spline")

# --- Fact table ---
fact_cols = [
    "id_estudiante", "id_institucion", "id_programa", "id_familia", "id_tiempo",
    "mod_competen_ciudada_punt", "mod_comuni_escrita_punt",
    "mod_ingles_punt", "mod_lectura_critica_punt", "mod_razona_cuantitat_punt"
]
fact_pk = []  # no hay PK explícita, pero usamos los ids como FK

fact_label = f"""<
<b>fact_resultados</b><br/>
---------------------<br/>
{"<br/>".join(fact_cols)}
>"""

dot.node("fact", fact_label, shape="record", style="filled", fillcolor="#ffd966", fontname="Arial")

# --- Dim estudiante ---
estudiante_cols = [
    "id_estudiante (PK)", "estu_consecutivo", "estu_estudiante", "estu_tipodocumento", "estu_genero",
    "estu_etnia", "estu_nacionalidad", "estu_fechanacimiento", "estu_estadocivil", "estu_discapacidad"
]

dot.node("dim_estudiante", f"""<
<b>dim_estudiante</b><br/>
---------------------<br/>
{"<br/>".join(estudiante_cols)}
>""", shape="record", style="filled", fillcolor="#cfe2f3", fontname="Arial")

# --- Dim institución ---
institucion_cols = [
    "id_institucion (PK)", "inst_cod_institucion", "inst_nombre_institucion",
    "inst_caracter_academico", "inst_origen"
]

dot.node("dim_institucion", f"""<
<b>dim_institucion</b><br/>
---------------------<br/>
{"<br/>".join(institucion_cols)}
>""", shape="record", style="filled", fillcolor="#d9ead3", fontname="Arial")

# --- Dim programa ---
programa_cols = [
    "id_programa (PK)", "estu_snies_prgmacademico", "estu_prgm_academico",
    "estu_nivel_prgm_academico", "estu_metodo_prgm", "estu_nucleo_pregrado"
]

dot.node("dim_programa", f"""<
<b>dim_programa</b><br/>
---------------------<br/>
{"<br/>".join(programa_cols)}
>""", shape="record", style="filled", fillcolor="#f4cccc", fontname="Arial")

# --- Dim familia ---
familia_cols = [
    "id_familia (PK)", "fami_educacionmadre", "fami_educacionpadre",
    "fami_ocupacionmadre", "fami_ocupacionpadre", "fami_estratovivienda",
    "fami_tieneinternet", "fami_tienecomputador", "fami_tieneautomovil", "fami_tienemotocicleta"
]

dot.node("dim_familia", f"""<
<b>dim_familia</b><br/>
---------------------<br/>
{"<br/>".join(familia_cols)}
>""", shape="record", style="filled", fillcolor="#e6b8af", fontname="Arial")

# --- Dim tiempo ---
tiempo_cols = [
    "id_tiempo (PK)", "periodo", "anio"
]

dot.node("dim_tiempo", f"""<
<b>dim_tiempo</b><br/>
---------------------<br/>
{"<br/>".join(tiempo_cols)}
>""", shape="record", style="filled", fillcolor="#d9d2e9", fontname="Arial")

# --- Relaciones ---
dot.edge("dim_estudiante", "fact", label="id_estudiante")
dot.edge("dim_institucion", "fact", label="id_institucion")
dot.edge("dim_programa", "fact", label="id_programa")
dot.edge("dim_familia", "fact", label="id_familia")
dot.edge("dim_tiempo", "fact", label="id_tiempo")

# Exportar
dot.render("modelo_estrella", view=True)

