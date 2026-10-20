"""
publicacion.py — Regla para publicar las tablas de Saber Pro por institución o sede.

Cuando un grupo tiene muy pocos evaluados, su promedio expone a las personas: con un
solo evaluado, el promedio ES el puntaje de esa persona. Por eso, en las tablas que se
suben a resultados/, las columnas de puntaje y de ceros en Escrita se dejan en blanco
cuando el grupo tiene menos de K_MIN evaluados. El número de evaluados sí se publica.

Las versiones completas se guardan en data/interim/ (no se sube) y son las que usan los
cálculos: la base integrada y el DEA se calculan con TODOS los evaluados, así que esta
regla no cambia ningún resultado.

La usan agregar_saber_pro.py, construir_tabla_maestra.py y verificar_oe1.py.
"""
import pandas as pd

K_MIN = 5   # evaluados mínimos para publicar un promedio (umbral convencional; ver README)
SENSIBLES = ["n_ceros_escrita", "pct_ceros_escrita", "global_a", "global_b", "global_c"]


def suprimir(tabla):
    """Copia de la tabla con las columnas sensibles en blanco donde n_evaluados < K_MIN,
    y la columna 'suprimido' que marca esas filas."""
    t = tabla.copy()
    peq = t["n_evaluados"].notna() & (t["n_evaluados"] < K_MIN)
    for c in SENSIBLES:
        if c in t.columns:
            t[c] = t[c].mask(peq)
    t["suprimido"] = peq
    return t
