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

# Diccionario de precios de referencia actualizado
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
        finca = st.text_input("Nombre de la Finca:", value="Mi Finca")
        cultivo_sel = st.selectbox("Cultivo:", list(precios_market.keys()))
        fecha_registro = st.date_input("Fecha del Registro:", datetime.date.today())
        
    with col2:
        costo_total = st.number_input("Costo Total de Producción ($):", min_value=0, step=10000)
        col_cant, col_unid = st.columns([2, 1])
        cantidad = col_cant.number_input("Cantidad Cosechada:", min_value=0.1)
        unidad = col_unid.selectbox("Unidad:", ["Kilos", "Bultos", "Toneladas", "Libras", "Quintales"])

    boton = st.form_submit_button("🚀 Calcular y Guardar")

# --- LÓGICA DE PROCESAMIENTO ---
if boton:
    # 1. Conversión de unidades a KG
    if unidad == "Bultos" or unidad == "Quintales":
        cantidad_kg = cantidad * 50
    elif unidad == "Toneladas":
        cantidad_kg = cantidad * 1000
    elif unidad == "Libras":
        cantidad_kg = cantidad / 2
    else:
        cantidad_kg = cantidad

    # 2. Cálculo de Venta (Ingreso estimado) y Precio Seguro (Costo real por kg)
    precio_referencia = precios_market.get(cultivo_sel, 0)
    total_venta_estimada = cantidad_kg * precio_referencia
    precio_seguro = costo_total / cantidad_kg if cantidad_kg > 0 else 0
    
    # 3. Crear DataFrame para guardar
    nuevo_dato = pd.DataFrame({
        "Fecha": [fecha_registro.strftime("%Y-%m-%d")],
        "Finca": [finca],
        "Cultivo": [cultivo_sel],
        "Costo_Total": [costo_total],
        "Cantidad_Kg": [cantidad_kg],
        "Precio_Seguro_x_Kg": [precio_seguro],
        "Venta_Estimada": [total_venta_estimada]
    })
    
    # 4. Guardar en Excel
    if os.path.exists(archivo_db):
        df_existente = pd.read_excel(archivo_db)
        df_final = pd.concat([df_existente, nuevo_dato], ignore_index=True)
    else:
        df_final = nuevo_dato
        
    df_final.to_excel(archivo_db, index=False)
    st.success(f"✅ ¡Registro exitoso! Venta estimada en Corabastos: {formato_cop(total_venta_estimada)}")

    # --- INDICADOR DE EFICIENCIA ---
    st.divider()
    datos_cultivo = df_final[df_final["Cultivo"] == cultivo_sel]
    
    if len(datos_cultivo) > 1:
        promedio_sector = datos_cultivo["Precio_Seguro_x_Kg"].mean()
        dif = ((precio_seguro - promedio_sector) / promedio_sector) * 100 if promedio_sector > 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tu Costo / Kg", formato_cop(precio_seguro))
        m2.metric("Promedio Sector", formato_cop(promedio_sector))
        m3.metric("Diferencia", f"{dif:+.1f}%", delta=f"{dif:+.1f}%", delta_color="inverse")

# --- 3. HISTORIAL Y BUSCADOR ---
st.divider()
if os.path.exists(archivo_db):
    df_ver = pd.read_excel(archivo_db)
    
    st.subheader("📊 Historial General de Registros")
    # Limpiamos visualmente la tabla para el usuario
    df_mostrar = df_ver.copy()
    if "Costo_Total" in df_mostrar.columns:
        df_mostrar["Costo_Total"] = df_mostrar["Costo_Total"].apply(formato_cop)
    if "Precio_Seguro_x_Kg" in df_mostrar.columns:
        df_mostrar["Precio_Seguro_x_Kg"] = df_mostrar["Precio_Seguro_x_Kg"].apply(formato_cop)
    
    st.dataframe(df_mostrar, use_container_width=True)
    
    # --- 4. CONSULTAR REPORTE POR FINCA ---
    st.subheader("🔍 Consultar Reporte Detallado")
    lista_fincas = df_ver["Finca"].unique()
    finca_elegida = st.selectbox("1. Seleccione una finca:", lista_fincas)

    if finca_elegida:
        cultivos_finca = df_ver[df_ver["Finca"] == finca_elegida]["Cultivo"].unique()
        cultivo_elegido = st.selectbox("2. Seleccione el cultivo:", cultivos_finca)
        
        if cultivo_elegido:
            datos_esp = df_ver[(df_ver["Finca"] == finca_elegida) & (df_ver["Cultivo"] == cultivo_elegido)]
            ultima = datos_esp.iloc[-1]
            st.info(f"Análisis para {cultivo_elegido} en {finca_elegida}")
            st.write(f"Último costo por Kg: {formato_cop(ultima['Precio_Seguro_x_Kg'])}")
else:
    st.info("Aún no hay datos registrados. Use el formulario de arriba.")
