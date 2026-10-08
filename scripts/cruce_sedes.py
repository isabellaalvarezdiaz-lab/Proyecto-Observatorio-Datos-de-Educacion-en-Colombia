"""
cruce_sedes.py — Qué códigos de institución (Saber Pro / SNIES) forman cada universidad del PTE.

El PTE reporta la universidad completa (una entidad 2257xx); Saber Pro y SNIES tienen un código
por sede. El código del PTE (ej. 225702) NO es el de SNIES/Saber Pro (ej. 1201), por eso el cruce
se hace así:
  1. Por nombre: cada entidad del PTE se busca en los nombres de Saber Pro (patrones de abajo).
  2. Por IES PADRE en SNIES: se agregan las sedes SNIES con el mismo IES PADRE que no estén
     asignadas a otra entidad (sedes sin evaluados en Saber Pro, pero con matrícula).
  3. UAIIN-CRIC no tiene evaluados en Saber Pro: se busca por nombre en SNIES.

Entradas: resultados/pte_universidades_2023_2024.csv, resultados/saber_pro_institucion_anio.csv,
          data/interim/snies_matriculados.csv.gz
Salida:   resultados/sedes_por_universidad.csv

Uso (desde la raíz del repositorio):
    python scripts/cruce_sedes.py
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

# patrón (sobre el nombre de Saber Pro sin tildes y en mayúsculas) de cada entidad del PTE
PATRONES = {
    "225701": r"^UNIVERSIDAD NACIONAL DE COLOMBIA-",
    "225702": r"^UNIVERSIDAD DE ANTIOQUIA-",
    "225703": r"^UNIVERSIDAD DEL VALLE-",
    "225704": r"^UNIVERSIDAD INDUSTRIAL DE SANTANDER",
    "225705": r"^UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA",
    "225706": r"^UNIVERSIDAD DISTRITAL ?FRANCISCO JOSE DE CALDAS",
    "225707": r"^UNIVERSIDAD DE CARTAGENA-",
    "225708": r"^UNIVERSIDAD DE NARINO-",
    "225709": r"^UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA",
    "225710": r"^UNIVERSIDAD DEL MAGDALENA",
    "225711": r"^UNIVERSIDAD DEL CAUCA-",
    "225712": r"^UNIVERSIDAD TECNOLOGICA DE PEREIRA",
    "225713": r"^UNIVERSIDAD DE PAMPLONA-",
    "225714": r"^UNIVERSIDAD SURCOLOMBIANA-",
    "225715": r"^UNIVERSIDAD PEDAGOGICA NACIONAL-",
    "225716": r"^UNIVERSIDAD DE CALDAS-",
    "225717": r"^UNIVERSIDAD MILITAR ?NUEVA GRANADA",
    "225718": r"^UNIVERSIDAD DEL ATLANTICO-",
    "225719": r"^UNIVERSIDAD DEL TOLIMA-",
    "225720": r"^UNIVERSIDAD DE CORDOBA-",
    "225721": r"^UNIVERSIDAD DEL QUINDIO-",
    "225722": r"^UNIVERSIDAD POPULAR DEL CESAR-",
    "225723": r"^UNIVERSIDAD DE LOS LLANOS-",
    "225724": r"^UNIVERSIDAD FRANCISCO DE PAULA SANTANDER-(?!OCANA)",
    "225725": r"^UNIVERSIDAD FRANCISCO DE PAULA SANTANDER-OCANA",
    "225726": r"^UNIVERSIDAD DE LA AMAZONIA-",
    "225727": r"^UNIVERSIDAD-?COLEGIO MAYOR DE CUNDINAMARCA",
    "225728": r"^UNIVERSIDAD DE CUNDINAMARCA",
    "225729": r"^UNIVERSIDAD TECNOLOGICA DEL CHOCO",
    "225730": r"^UNIVERSIDAD DE SUCRE-",
    "225731": r"^UNIVERSIDAD DE LA GUAJIRA-",
    "225732": r"^UNIVERSIDAD DEL PACIFICO-",
    "225733": r"^UNIVERSIDAD INTERNACIONAL DEL TROPICO AMERICANO",
}
SOLO_SNIES = {"225734": r"INDIGENA INTERCULTURAL|UAIIN"}   # sin evaluados en Saber Pro

COD, PADRE, NOM, SECTOR = ("CÓDIGO DE LA INSTITUCIÓN", "IES PADRE",
                           "INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)", "SECTOR IES")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", s).strip()


def main():
    pte = pd.read_csv("resultados/pte_universidades_2023_2024.csv", dtype={"pte_codigo": str})
    ent = pte.drop_duplicates("pte_codigo").set_index("pte_codigo").pte_nombre
    faltan = set(ent.index) - set(PATRONES) - set(SOLO_SNIES)
    if faltan:
        raise SystemExit(f"[ERROR] Entidades del PTE sin patrón de búsqueda: {sorted(faltan)}")

    sp = pd.read_csv("resultados/saber_pro_institucion_anio.csv", dtype={"codigo_ies": str})
    sp = sp.drop_duplicates("codigo_ies")[["codigo_ies", "nombre_ies"]]
    sp["nom"] = sp.nombre_ies.map(norm)

    sn = pd.read_csv("data/interim/snies_matriculados.csv.gz", dtype=str)
    sn = sn.sort_values("AÑO").drop_duplicates(COD, keep="last").set_index(COD)

    # 1. por nombre en Saber Pro
    filas = []
    for cod_pte, pat in PATRONES.items():
        for _, r in sp[sp.nom.str.contains(pat, regex=True)].iterrows():
            filas.append(dict(pte_codigo=cod_pte, cod_institucion=r.codigo_ies,
                              nombre_saber_pro=r.nombre_ies, regla="nombre en Saber Pro"))
    # 3. UAIIN por nombre en SNIES
    for cod_pte, pat in SOLO_SNIES.items():
        for c in sn.index[sn[NOM].map(norm).str.contains(pat, regex=True)]:
            filas.append(dict(pte_codigo=cod_pte, cod_institucion=c, nombre_saber_pro=None,
                              regla="nombre en SNIES (sin evaluados en Saber Pro)"))
    s = pd.DataFrame(filas)
    # 2. sedes SNIES con el mismo IES PADRE
    padre_ent = {}
    for c, e in zip(s.cod_institucion, s.pte_codigo):
        if c in sn.index:
            padre_ent.setdefault(sn.at[c, PADRE], set()).add(e)
    extra = []
    for c, p in sn[PADRE].items():
        if c in set(s.cod_institucion) or p not in padre_ent:
            continue
        if len(padre_ent[p]) > 1:
            raise SystemExit(f"[ERROR] La sede SNIES {c} tiene IES PADRE {p}, compartido por {padre_ent[p]}")
        extra.append(dict(pte_codigo=next(iter(padre_ent[p])), cod_institucion=c, nombre_saber_pro=None,
                          regla="mismo IES PADRE en SNIES"))
    s = pd.concat([s, pd.DataFrame(extra)], ignore_index=True)
    s.insert(1, "pte_nombre", s.pte_codigo.map(ent))
    s["en_snies"] = s.cod_institucion.isin(sn.index)
    s["ies_padre_snies"] = s.cod_institucion.map(sn[PADRE])
    s["nombre_snies"] = s.cod_institucion.map(sn[NOM])
    s["sector_snies"] = s.cod_institucion.map(sn[SECTOR])
    s = s.sort_values(["pte_codigo", "cod_institucion"])

    # controles
    print(f"Entidades del PTE: {len(ent)} | con al menos una sede: {s.pte_codigo.nunique()}")
    dup = s.groupby("cod_institucion").pte_codigo.nunique()
    if (dup > 1).any():
        raise SystemExit(f"[ERROR] Códigos asignados a más de una entidad: {dup[dup > 1].to_dict()}")
    print(f"Sedes asignadas: {len(s)} | por regla: {s.regla.value_counts().to_dict()}")
    print("Sedes de Saber Pro que no aparecen en SNIES:", s.loc[~s.en_snies, "cod_institucion"].tolist() or "ninguna")
    print("Sector en SNIES de las sedes asignadas:", s.sector_snies.value_counts(dropna=False).to_dict())
    n_sedes = s.groupby("pte_codigo").size()
    print("Universidades con más de una sede:",
          {ent[k]: int(v) for k, v in n_sedes[n_sedes > 1].items()})
    oficiales = sn[(sn[SECTOR].str.lower() == "oficial") & sn["CARÁCTER IES"].str.contains("Universidad", case=False)]
    fuera = oficiales[~oficiales.index.isin(s.cod_institucion)]
    print("Universidades oficiales de SNIES que no están entre las del PTE:")
    for c, r in fuera.iterrows():
        print(f"   {c}  {r[NOM]}")

    salida = Path("resultados") / "sedes_por_universidad.csv"
    s.to_csv(salida, index=False, encoding="utf-8-sig")
    print(f"Guardado: {salida.as_posix()}")


if __name__ == "__main__":
    main()
