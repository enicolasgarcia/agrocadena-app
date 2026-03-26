import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1️⃣ CONFIGURACIÓN DE GOOGLE SHEETS
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds_dict = st.secrets["GOOGLE_CREDS"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)
sheet = client.open("agro").sheet1

# 🔥 TRAER DATOS DESDE GOOGLE SHEETS
data = sheet.get_all_records()
df_existente = pd.DataFrame(data)

# 2️⃣ BASE CLIMÁTICA
base_clima = {
    "Cundinamarca": 19, "Antioquia": 22, "Valle del Cauca": 24,
    "Huila": 25, "Tolima": 26, "Santander": 23, "Boyacá": 16,
    "Magdalena": 28, "Meta": 26, "Nariño": 18, "Casanare": 27,
    "Quindío": 21, "Caldas": 21, "Risaralda": 21, "Bolívar": 28
}

# --- INTERFAZ ---
st.set_page_config(page_title="Agrocadena Pro", layout="wide")
st.title("🚜 Consultoría Agrocadena")

with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("registro_finca"):
        nombre = st.text_input("Nombre de la Finca")
        cultivo = st.text_input("Cultivo")
        departamento = st.selectbox("Departamento", options=sorted(list(base_clima.keys())))
        produccion = st.number_input("Producción", min_value=1.0)
        inv_inicial = st.number_input("Inversión Inicial", min_value=0.0)
        costo_mensual = st.number_input("Costo mensual", min_value=0.0)
        meses = st.number_input("Meses", min_value=1.0)

        submit = st.form_submit_button("🚀 Guardar")

        if submit:
            if nombre and cultivo:
                gasto_total = inv_inicial + (costo_mensual * meses)
                precio_minimo = gasto_total / produccion
                temp_finca = base_clima[departamento]

                # 🔥 IMPORTANTE: incluir Cantidad_kg
                nueva_fila = [
                    nombre, cultivo, departamento,
                    produccion,  # 👈 clave para el análisis
                    inv_inicial, costo_mensual,
                    meses, gasto_total, precio_minimo
                ]

                try:
                    sheet.append_row(nueva_fila)
                    st.success("✅ Guardado en Google Sheets")
                except Exception as e:
                    st.error(f"Error: {e}")

                if temp_finca > 27:
                    st.warning("🔥 Riesgo de calor")
                elif temp_finca < 17:
                    st.info("❄️ Crecimiento lento")

                st.rerun()
            else:
                st.error("Completa los datos")

# --- TABLA ---
st.subheader("📊 Historial")

if not df_existente.empty:
    st.dataframe(df_existente)
else:
    st.info("No hay datos aún")

# ==============================
# 🗑️ ELIMINAR REGISTROS
# ==============================

st.divider()
st.subheader("🗑️ Eliminar registro")

if not df_existente.empty:

    df_existente = df_existente.copy()

    df_existente["ID"] = df_existente["Nombre_Finca"] + " - " + df_existente["Cultivo"]

    seleccion = st.selectbox(
        "Selecciona el registro a eliminar",
        df_existente["ID"]
    )

    if st.button("Eliminar registro"):
        df_nuevo = df_existente[df_existente["ID"] != seleccion]

        sheet.clear()
        sheet.append_row(list(df_nuevo.drop(columns=["ID"]).columns))

        for _, row in df_nuevo.drop(columns=["ID"]).iterrows():
            sheet.append_row(row.tolist())

        st.success("✅ Registro eliminado correctamente")
        st.rerun()
# ==============================
# 🔥 ANÁLISIS INTELIGENTE
# ==============================

st.divider()
st.header("📊 Análisis Inteligente")

if df_existente.empty:
    st.warning("⚠️ No hay datos suficientes para análisis")
else:
    df = df_existente.copy()
    df = df.dropna()

    # 🔥 Cálculo con tu columna correcta
    df["Costo_por_Kg"] = df["Costo_Total"] / df["Cantidad_Kg"]

    # Promedio por cultivo
    promedios = df.groupby("Cultivo")["Costo_por_Kg"].mean().reset_index()
    promedios.rename(columns={"Costo_por_Kg": "Promedio_Cultivo"}, inplace=True)

    df = df.merge(promedios, on="Cultivo", how="left")

    # Eficiencia
    df["Eficiencia_%"] = ((df["Costo_por_Kg"] - df["Promedio_Cultivo"]) / df["Promedio_Cultivo"]) * 100

    # --- SELECTOR ---
    st.subheader("🔎 Análisis por finca")

    finca_seleccionada = st.selectbox(
        "Selecciona una finca",
        df["Nombre_Finca"].unique()
    )

    datos_finca = df[df["Nombre_Finca"] == finca_seleccionada]
    row = datos_finca.iloc[0]

    # --- MÉTRICAS ---
    col1, col2, col3 = st.columns(3)

    col1.metric("Costo por Kg", f"${row['Costo_por_Kg']:,.0f}")
    col2.metric("Promedio del cultivo", f"${row['Promedio_Cultivo']:,.0f}")
    col3.metric("Eficiencia", f"{row['Eficiencia_%']:.1f}%")

    # --- DIAGNÓSTICO ---
    st.subheader("💡 Diagnóstico")

    if row["Eficiencia_%"] <= 0:
        st.success("✅ Estás por debajo del promedio (buena eficiencia)")
    else:
        st.error("⚠️ Estás por encima del promedio (costos altos)")

    # --- RECOMENDACIÓN ---
    st.subheader("📌 Recomendación")

    if row["Eficiencia_%"] > 10:
        st.warning("Reduce costos (insumos o mano de obra)")
    elif row["Eficiencia_%"] < -10:
        st.success("Muy eficiente, podrías aumentar producción")
    else:
        st.info("Estás en un nivel promedio")
