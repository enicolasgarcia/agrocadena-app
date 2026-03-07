import streamlit as st
import pandas as pd
import os
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="App Agricola", layout="wide")

# --- FUNCIONES DE APOYO ---
def formato_cop(valor):
    return f"$ {valor:,.0f}".replace(",", ".")

archivo_db = "fincas_registradas.xlsx"

# Diccionario de precios
precios_market = {
    "Papa Sabanera": 2200, "Frijol Verde": 4500, "Aguacate Hass": 6000,
    "Cebolla Larga": 4400, "Tomate Chonto": 6000, "Cafe": 15000,
    "Fresa": 8000, "Uchuva": 7000, "Arveja Verde": 4800,
    "Habichuela": 4800, "Lulo": 5200, "Zanahoria": 1800,
    "Cebolla Cabezona Blanca": 2400, "Tomate de Arbol": 3600,
    "Papa Criolla": 2500, "Pimenton": 3000, "Mora de Castilla": 4000,
    "Mango Tomy": 5000, "Maracuya": 4500, "Banano Uraba": 2200,
    "Papaya Maradol": 3000, "Piña Oro Miel": 3500, "Banano Criollo": 2500,
    "mazorca": 1800
}

# --- TÍTULO ---
st.title("🚜 App Agricola")
st.markdown("Registre sus costos y compare su rendimiento histórico.")

# --- 1. FORMULARIO DE REGISTRO ---
with st.form("registro_finca"):
    st.subheader("📋 Registro de Nueva Cosecha")
    col1, col2 = st.columns(2)
    with col1:
        finca = st.text_input("Nombre de la Finca:", value="Principal")
        cultivo_sel = st.selectbox("Cultivo:", list(precios_market.keys()))
        fecha_registro = st.date_input("Fecha:", datetime.date.today())
    with col2:
        costo_total = st.number_input("Costo Total Producción ($):", min_value=0, step=10000)
        c1, c2 = st.columns([2, 1])
        cantidad = c1.number_input("Cantidad:", min_value=0.1)
        unidad = c2.selectbox("Unidad:", ["Kilos", "Bultos", "Toneladas", "Libras"])
    
    boton = st.form_submit_button("🚀 Calcular y Guardar")

# --- LÓGICA DE PROCESAMIENTO ---
if boton:
    # Conversión
    factores = {"Bultos": 50, "Toneladas": 1000, "Libras": 0.5, "Kilos": 1}
    cantidad_kg = cantidad * factores.get(unidad, 1)
    
    precio_ref = precios_market.get(cultivo_sel, 0)
    ingreso_est = cantidad_kg * precio_ref
    costo_kg = costo_total / cantidad_kg if cantidad_kg > 0 else 0
    
    nuevo_dato = pd.DataFrame({
        "Fecha": [fecha_registro.strftime("%Y-%m-%d")],
        "Finca": [finca],
        "Cultivo": [cultivo_sel],
        "Costo_Total": [costo_total],
        "Cantidad_Kg": [cantidad_kg],
        "Precio_Costo_Kg": [costo_kg],
        "Venta_Estimada": [ingreso_est]
    })
    
    if os.path.exists(archivo_db):
        df_old = pd.read_excel(archivo_db)
        df_final = pd.concat([df_old, nuevo_dato], ignore_index=True)
    else:
        df_final = nuevo_dato
    
    df_final.to_excel(archivo_db, index=False)
    st.success(f"✅ Guardado. Costo por Kg: {formato_cop(costo_kg)}")

# --- 2. ANÁLISIS Y MÉTRICAS (AQUÍ ESTÁ LO QUE TE FALTABA) ---
if os.path.exists(archivo_db):
    df_analisis = pd.read_excel(archivo_db)
    st.divider()
    st.subheader("📊 Análisis de Eficiencia")
    
    # Seleccionar último registro para el análisis rápido
    ultimo = df_analisis.iloc[-1]
    cultivo_actual = ultimo["Cultivo"]
    costo_actual = ultimo["Precio_Costo_Kg"]
    
    # Comparar con el promedio de ese mismo cultivo
    promedio_cultivo = df_analisis[df_analisis["Cultivo"] == cultivo_actual]["Precio_Costo_Kg"].mean()
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Tu Costo actual / Kg", formato_cop(costo_actual))
    col_m2.metric("Promedio Histórico", formato_cop(promedio_cultivo))
    
    if promedio_cultivo > 0:
        dif_pct = ((costo_actual - promedio_cultivo) / promedio_cultivo) * 100
        col_m3.metric("Diferencia", f"{dif_pct:+.1f}%", delta=f"{dif_pct:+.1f}%", delta_color="inverse")
        
        # --- ASESOR VIRTUAL ---
        st.markdown("### 💡 Diagnóstico del Asesor")
        if dif_pct > 10:
            st.error(f"Tus costos de **{cultivo_actual}** están por encima del promedio. Revisa si hubo aumento en precio de insumos o fletes.")
        elif dif_pct < -10:
            st.success(f"¡Excelente! Estás produciendo **{cultivo_actual}** de forma más eficiente que en cosechas anteriores.")
        else:
            st.info("Tus costos se mantienen en el promedio normal de producción.")

    # --- 3. TABLA HISTÓRICA ---
    st.divider()
    st.subheader("📝 Historial de Registros")
    st.dataframe(df_analisis.sort_values(by="Fecha", ascending=False), use_container_width=True)
