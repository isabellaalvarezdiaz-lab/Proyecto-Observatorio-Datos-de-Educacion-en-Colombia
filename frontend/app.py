"""Tablero del observatorio (Streamlit). Consume la API: no calcula nada por su cuenta.

Uso (con la API corriendo en otra terminal):
    streamlit run frontend/app.py
Variable de entorno: API_URL (por defecto http://localhost:8000).
"""
import pandas as pd
import streamlit as st

from cliente import ClienteAPI, ErrorAPI

st.set_page_config(page_title="Observatorio · eficiencia y riesgo", layout="wide")
api = ClienteAPI()

st.title("Eficiencia del gasto público y riesgo de cola en 33 universidades públicas")
st.caption("Proyecto de consultoría, Estadística USTA · 2023-2024 · Fuentes: SNIES, Saber Pro (ICFES) y PTE")

try:
    estado = api.salud()
except ErrorAPI as exc:
    st.error(str(exc))
    st.stop()

pest = st.tabs(["Eficiencia", "Riesgo de cola", "Backtesting", "Stress testing", "Imputar Escrita", "Asistente"])

with pest[0]:
    c1, c2 = st.columns(2)
    modelo = c1.selectbox("Modelo", ["principal", "cobertura", "cobertura_sin_unad"])
    anio = c2.selectbox("Año", [2024, 2023])
    efi = pd.DataFrame(api.eficiencia(modelo, anio))
    efi["ic95_inf"] = efi.ic95.map(lambda d: d["inf"])
    efi["ic95_sup"] = efi.ic95.map(lambda d: d["sup"])
    st.bar_chart(efi.set_index("universidad")["eficiencia_corregida"], horizontal=True, height=700)
    st.dataframe(efi[["universidad", "eficiencia", "eficiencia_corregida", "ic95_inf", "ic95_sup", "en_frontera"]],
                 hide_index=True, use_container_width=True)

with pest[1]:
    anio_c = st.selectbox("Año ", [2024, 2023], key="anio_cola")
    cola = pd.DataFrame(api.cola(anio_c))
    ref = cola[cola.pte_codigo.isna()]
    unis = cola[cola.pte_codigo.notna()].sort_values("cvar")
    for _, r in ref.iterrows():
        st.metric(f"CVaR 5 % · {r.nombre}", f"{r.cvar:.1f}", help=f"VaR {r['var']:.0f} · media {r.media:.1f}")
    st.bar_chart(unis.set_index("nombre")[["media", "cvar"]], horizontal=True, height=700)
    st.dataframe(unis[["nombre", "n_evaluados", "media", "var", "cvar", "cvar_ic_inf", "cvar_ic_sup", "brecha_cola"]],
                 hide_index=True, use_container_width=True)

with pest[2]:
    st.write("¿La cohorte 2024 cae por debajo del VaR 2023 más de lo esperado? Prueba de Kupiec contra la "
             "tasa nacional de 2024, con ajuste de Holm.")
    kup = pd.DataFrame(api.kupiec())
    st.dataframe(kup[["nombre", "tasa_2024", "tasa_ref_nacional", "p_relativo_holm", "rechaza_relativo",
                      "direccion_relativa"]], hide_index=True, use_container_width=True)

with pest[3]:
    modelo_s = st.selectbox("Modelo ", ["principal", "cobertura", "cobertura_sin_unad"], key="modelo_stress")
    st.subheader("Escenarios del informe")
    st.dataframe(pd.DataFrame(api.escenarios(modelo_s))[
        ["escenario", "eficiencia_media", "cambio_media", "n_frontera", "spearman_con_base", "n_cambian_5_puntos"]],
        hide_index=True, use_container_width=True)
    st.subheader("Escenario propio")
    c1, c2, c3 = st.columns(3)
    grupo = c1.selectbox("Recortar a", ["ninguna", "todas", "nacional", "territorial", "menos_eficientes"])
    pct = c2.slider("Recorte (%)", 1, 50, 20)
    n_bajas = c3.number_input("¿Cuántas menos eficientes?", 1, 32, 8)
    adicion = st.number_input("Recursos adicionales (miles de millones; 0 = ninguno)", 0.0, 20000.0, 0.0)
    reparto = st.radio("Reparto de la adición", ["matricula_pregrado", "pregrado_estratos_1_2", "uniforme"],
                       horizontal=True)
    if st.button("Simular"):
        esc: dict = {"modelo": modelo_s, "recortes": []}
        if grupo != "ninguna":
            r = {"grupo": grupo, "porcentaje": pct}
            if grupo == "menos_eficientes":
                r["n_menos_eficientes"] = int(n_bajas)
            esc["recortes"].append(r)
        if adicion > 0:
            esc["adicion"] = {"monto_mm": adicion, "reparto": reparto}
        if not esc["recortes"] and "adicion" not in esc:
            st.warning("Elija un recorte o una adición para armar el escenario.")
            st.stop()
        try:
            res = api.simular(esc)
            st.json(res["resumen"])
            st.dataframe(pd.DataFrame(res["universidades"]), hide_index=True, use_container_width=True)
        except ErrorAPI as exc:
            st.error(str(exc))

with pest[4]:
    st.write("Escrita esperada para un perfil con los otros cuatro módulos (modelo entrenado offline; "
             "útil para agregados, no para juzgar a una persona).")
    c = st.columns(4)
    perfil = {"ciudadanas": c[0].number_input("Ciudadanas", 1, 300, 150),
              "ingles": c[1].number_input("Inglés", 1, 300, 150),
              "lectura_critica": c[2].number_input("Lectura crítica", 1, 300, 150),
              "razonamiento": c[3].number_input("Razonamiento", 1, 300, 150), "anio": 2024}
    if st.button("Predecir"):
        p = api.predecir(perfil)
        st.metric("Escrita predicha", f"{p['escrita_predicha']:.1f}",
                  help=f"Intervalo 80 %: {p['intervalo_80']['inf']}–{p['intervalo_80']['sup']}")
        st.caption(p["advertencia"])

with pest[5]:
    pregunta = st.text_input("Pregunta sobre el proyecto", "¿Cuál es el CVaR de la Universidad del Tolima?")
    if st.button("Preguntar"):
        r = api.preguntar(pregunta)
        st.write(r["respuesta"])
        if r["cifras"]:
            st.dataframe(pd.DataFrame(r["cifras"]), hide_index=True, use_container_width=True)
        for f in r["fuentes"]:
            with st.expander(f"{f['documento']} · {f['ubicacion']}"):
                st.write(f["texto"])

st.caption(f"API: {api.url} · entorno {estado['entorno']} · modelo ML {estado['modelo_ml']}")
