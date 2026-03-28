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
        
        # --- NUEVA SECCIÓN DE UNIDADES (QUINTALES) ---
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            unidad = st.radio("Unidad de medida", ["Kg", "Quintales (50kg)"])
        with col_u2:
            produccion_input = st.number_input("Cantidad", min_value=1.0)
        
        # Convertimos a Kg para el cálculo interno
        produccion_kg = produccion_input * 50 if unidad == "Quintales (50kg)" else produccion_input
        
        precio_venta = st.number_input("Precio de venta por Kg", min_value=0.0)
        inv_inicial = st.number_input("Inversión Inicial", min_value=0.0)
        costo_mensual = st.number_input("Costo mensual", min_value=0.0)
        meses = st.number_input("Meses", min_value=1.0)

        submit = st.form_submit_button("🚀 Guardar")

        if submit:
            if nombre and cultivo:
                gasto_total = inv_inicial + (costo_mensual * meses)
                precio_minimo = gasto_total / produccion_kg
                ingreso = precio_venta * produccion_kg
                ganancia = ingreso - gasto_total
                temp_finca = base_clima[departamento]

                # Nueva fila para Google Sheets
                nueva_fila = [
                    nombre, cultivo, departamento,
                    produccion_kg, # Guardamos siempre en Kg para consistencia
                    inv_inicial, costo_mensual,
                    meses, gasto_total, 
                    precio_minimo,
                    precio_venta,
                    ingreso,
                    ganancia
                ]

                try:
                    sheet.append_row(nueva_fila)
                    st.success(f"✅ Guardado: {produccion_kg} Kg registrados")
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
st.subheader("📊 Historial de Producción")

if not df_existente.empty:
    # Creamos una copia para no dañar los datos originales
    df_tabla = df_existente.copy()
    
    # Columnas que queremos formatear con $
    cols_dinero = ["Inversion_Inicial", "Costo_Mensual", "Costo_Total", "Precio_Minimo", "Precio_Venta", "Ingreso", "Ganancia"]
    
    # Limpieza: Convertimos a número, si hay error ponemos 0
    for col in cols_dinero:
        if col in df_tabla.columns:
            df_tabla[col] = pd.to_numeric(df_tabla[col], errors='coerce').fillna(0)
    
    # Formateo seguro
    st.dataframe(df_tabla.style.format({
        "Inversion_Inicial": "${:,.0f}",
        "Costo_Mensual": "${:,.0f}",
        "Costo_Total": "${:,.0f}",
        "Precio_Minimo": "${:,.0f}",
        "Precio_Venta": "${:,.0f}",
        "Ingreso": "${:,.0f}",
        "Ganancia": "${:,.0f}"
    }), use_container_width=True)
else:
    st.info("No hay datos aún")

# ... (El resto de tu código de ELIMINAR REGISTROS y ANÁLISIS INTELIGENTE sigue igual)
# Solo asegúrate de que en el análisis inteligente use "Cantidad_Kg" como nombre de columna.

st.divider()
st.header("📊 Análisis Inteligente")

if df_existente.empty:
    st.warning("⚠️ No hay datos suficientes para análisis")
else:
    df = df_existente.copy()
    
    # Aseguramos que los nombres de columnas coincidan con el Sheets
    # Si en tu Sheets la columna se llama 'Produccion', cámbiala aquí:
    col_prod = "Cantidad_Kg" if "Cantidad_Kg" in df.columns else "Produccion"

    # Convertir a numérico y limpiar
    columnas_num = ["Precio_Venta", col_prod, "Costo_Total"]
    for col in columnas_num:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df[col_prod] = df[col_prod].replace(0, 1)

    # Cálculos
    df["Costo_por_Kg"] = df["Costo_Total"] / df[col_prod]
    df["Ganancia"] = (df["Precio_Venta"] * df[col_prod]) - df["Costo_Total"]

    # Promedios
    promedios = df.groupby("Cultivo")["Costo_por_Kg"].mean().reset_index()
    promedios.rename(columns={"Costo_por_Kg": "Promedio_Cultivo"}, inplace=True)
    df = df.merge(promedios, on="Cultivo", how="left")
    
    df["Eficiencia_%"] = ((df["Costo_por_Kg"] - df["Promedio_Cultivo"]) / df["Promedio_Cultivo"]) * 100

    st.subheader("🔎 Análisis por finca")
    finca_sel = st.selectbox("Selecciona una finca", df["Nombre_Finca"].unique())
    row = df[df["Nombre_Finca"] == finca_sel].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Costo por Kg", f"${row['Costo_por_Kg']:,.0f}")
    c2.metric("Producción Total", f"{row[col_prod]:,.0f} Kg", f"{row[col_prod]/50:.1f} qq")
    c3.metric("Eficiencia", f"{row['Eficiencia_%']:.1f}%", delta_color="inverse")
    c4.metric("Ganancia Est.", f"${row['Ganancia']:,.0f}")
    
    # Diagnóstico rápido
    if row["Ganancia"] > 0:
        st.success(f"🟢 La finca {finca_sel} es RENTABLE.")
    else:
        st.error(f"🔴 La finca {finca_sel} está operando con PÉRDIDA.")
