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
        unidad = st.selectbox("Unidad de producción",["Kg", "Bultos (50kg)", "Libras (0.5kg)", "Quintales (50kg)"])
        precio_venta = st.number_input("Precio de venta por Kg", min_value=0.0)
        inv_inicial = st.number_input("Inversión Inicial", min_value=0.0)
        costo_mensual = st.number_input("Costo mensual", min_value=0.0)
        meses = st.number_input("Meses", min_value=1.0)

        submit = st.form_submit_button("🚀 Guardar")

if submit:
    if nombre and cultivo:

        # 🔥 CONVERSIÓN A KG
        if unidad == "Kg":
            produccion_kg = produccion
        elif unidad == "Bultos":
            produccion_kg = produccion * 50
        elif unidad == "Libras":
            produccion_kg = produccion * 0.5
        elif unidad == "Quintales":
            produccion_kg = produccion * 50

        gasto_total = inv_inicial + (costo_mensual * meses)

        # 🔥 CÁLCULOS CON KG
        precio_minimo = gasto_total / produccion_kg
        ingreso = precio_venta * produccion_kg
        ganancia = ingreso - gasto_total

        temp_finca = base_clima[departamento]

        nueva_fila = [
            nombre, cultivo, departamento,
            produccion_kg,
            inv_inicial, costo_mensual,
            meses, gasto_total,
            precio_minimo,
            precio_venta,
            ingreso,
            ganancia
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
    st.dataframe(df_existente.style.format({
    "Inversion_Inicial": "{:,.0f}",
    "Costo_Mensual": "{:,.0f}",
    "Costo_Total": "{:,.0f}",
    "Precio_Minimo": "{:,.0f}",
    "Cantidad_Kg": "{:,.0f}"
}))
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

    # 🔥 Asegurar columnas (por si faltan)
    columnas = ["Precio_Venta", "Cantidad_Kg", "Costo_Total"]
    for col in columnas:
        if col not in df.columns:
            df[col] = 0

    # 🔥 Convertir a numérico
    for col in columnas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.fillna(0)

    # 🔥 Evitar división por 0
    df["Cantidad_Kg"] = df["Cantidad_Kg"].replace(0, 1)

    # 🔥 Cálculos
    df["Costo_por_Kg"] = df["Costo_Total"] / df["Cantidad_Kg"]
    df["Ingreso"] = df["Precio_Venta"] * df["Cantidad_Kg"]
    df["Ganancia"] = df["Ingreso"] - df["Costo_Total"]

    # 🔥 Promedio por cultivo
    promedios = df.groupby("Cultivo")["Costo_por_Kg"].mean().reset_index()
    promedios.rename(columns={"Costo_por_Kg": "Promedio_Cultivo"}, inplace=True)

    df = df.merge(promedios, on="Cultivo", how="left")

    # 🔥 Evitar división por 0 en eficiencia
    df["Promedio_Cultivo"] = df["Promedio_Cultivo"].replace(0, 1)

    df["Eficiencia_%"] = (
        (df["Costo_por_Kg"] - df["Promedio_Cultivo"])
        / df["Promedio_Cultivo"]
    ) * 100

    # --- SELECTOR ---
    st.subheader("🔎 Análisis por finca")

    finca_seleccionada = st.selectbox(
        "Selecciona una finca",
        df["Nombre_Finca"].unique()
    )

    datos_finca = df[df["Nombre_Finca"] == finca_seleccionada]
    row = datos_finca.iloc[0]

    # --- MÉTRICAS ---
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Costo por Kg", f"${row['Costo_por_Kg']:,.0f}")
    col2.metric("Promedio del cultivo", f"${row['Promedio_Cultivo']:,.0f}")
    col3.metric("Eficiencia", f"{row['Eficiencia_%']:.1f}%")

    ganancia_valor = row.get("Ganancia", 0)

    try:
        ganancia_valor = float(ganancia_valor)
    except:
        ganancia_valor = 0

    col4.metric("Ganancia", f"${ganancia_valor:,.0f}")

    # --- DIAGNÓSTICO ---
    st.subheader("💡 Diagnóstico")

    if row["Eficiencia_%"] <= 0:
        st.success("✅ Estás por debajo del promedio (buena eficiencia)")
    else:
        st.error("⚠️ Estás por encima del promedio (costos altos)")

    # --- RESULTADO FINANCIERO ---
    st.subheader("💰 Resultado financiero")

    if ganancia_valor > 0:
        st.success("🟢 Estás generando GANANCIA")
    elif ganancia_valor < 0:
        st.error("🔴 Estás generando PÉRDIDA")
    else:
        st.info("🟡 Estás en punto de equilibrio")

    # --- RECOMENDACIÓN ---
    st.subheader("📌 Recomendación")

    if row["Eficiencia_%"] > 10:
        st.warning("Reduce costos (insumos o mano de obra)")
    elif row["Eficiencia_%"] < -10:
        st.success("Muy eficiente, podrías aumentar producción")
    else:
        st.info("Estás en un nivel promedio")
