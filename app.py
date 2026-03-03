import streamlit as st
import pandas as pd
import os
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Asesor Agrícola Pro", layout="wide")

# --- FUNCIONES DE APOYO ---
def formato_cop(valor):
    return f"$ {valor:,.0f}".replace(",", ".")

archivo_db = "fincas_registradas.xlsx"

# Diccionario de precios de referencia (Corabastos aproximado)
precios_market = {
    "Papa Sabanera": 7500,
    "Frijol Verde": 4500,
    "Aguacate Hass": 8500,
    "Cebolla Larga": 3200,
    "Tomate Chonto": 3800
}

# --- TÍTULO ---
st.title("🚜 Sistema de Gestión y Eficiencia Agrícola")
st.markdown("Registre sus costos y compare su rendimiento histórico.")

# --- 1. FORMULARIO DE REGISTRO ---
with st.form("registro_finca"):
    st.subheader("📋 Registro de Nueva Cosecha")
    
    col1, col2 = st.columns(2)
    
    with col1:
        finca = st.text_input("Nombre de la Finca:")
        cultivo_sel = st.selectbox("Cultivo:", list(precios_market.keys()))
        # NUEVO: Selector de Fecha
        fecha_registro = st.date_input("Fecha del Registro:", datetime.date.today())
        
    with col2:
        costo_total = st.number_input("Costo Total de Producción ($):", min_value=0, step=10000)
        col_cant, col_unid = st.columns([2, 1])
        cantidad = col_cant.number_input("Cantidad Cosechada:", min_value=0.1)
        unidad = col_unid.selectbox("Unidad:", ["Kilos", "Bultos", "Toneladas"])

    boton = st.form_submit_button("🚀 Calcular y Guardar")

if boton:
    # Conversión a Kilos (Base estándar)
    cantidad_kg = cantidad
    if unidad == "Bultos": cantidad_kg = cantidad * 50
    if unidad == "Toneladas": cantidad_kg = cantidad * 1000
    
    precio_seguro = costo_total / cantidad_kg
    
    # Crear DataFrame con el nuevo registro incluyendo FECHA
    nuevo_dato = pd.DataFrame({
        "Fecha": [fecha_registro.strftime("%Y-%m-%d")],
        "Finca": [finca],
        "Cultivo": [cultivo_sel],
        "Costo_Total": [costo_total],
        "Cantidad_Kg": [cantidad_kg],
        "Precio_Seguro_x_Kg": [precio_seguro]
    })
    
    # Guardar en Excel
    if os.path.exists(archivo_db):
        df_existente = pd.read_excel(archivo_db)
        df_final = pd.concat([df_existente, nuevo_dato], ignore_index=True)
    else:
        df_final = nuevo_dato
        
    df_final.to_excel(archivo_db, index=False)
    st.success(f"✅ Registro de '{finca}' guardado con éxito.")

    # --- 2. INDICADOR DE EFICIENCIA EN TIEMPO REAL ---
    st.divider()
    datos_cultivo = df_final[df_final["Cultivo"] == cultivo_sel]
    
    if len(datos_cultivo) > 1:
        promedio_sector = datos_cultivo["Precio_Seguro_x_Kg"].mean()
        dif = ((precio_seguro - promedio_sector) / promedio_sector) * 100
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tu Costo / Kg", formato_cop(precio_seguro))
        m2.metric("Promedio Sector", formato_cop(promedio_sector))
        m3.metric("Diferencia", f"{dif:+.1f}%", delta=f"{dif:+.1f}%", delta_color="inverse")
        
        # Asesor Virtual
        st.markdown("#### 💡 Recomendación del Asesor Virtual")
        if dif > 20:
            st.error(f"⚠️ **Alerta de Sobrecosto:** Tus costos están muy por encima del promedio. Revisa desperdicios.")
        elif 0 < dif <= 20:
            st.warning(f"🧐 **Oportunidad de Mejora:** Estás cerca del promedio, podrías optimizar.")
        else:
            st.success(f"🌟 **¡Excelente Gestión!** Eres más eficiente que el promedio.")
    else:
        st.info(f"💡 Eres el primer dato registrado para {cultivo_sel}. ¡Sigue así!")

# --- 3. HISTORIAL Y BUSCADOR ---
st.divider()
if os.path.exists(archivo_db):
  df_ver = pd.read_excel(archivo_db)
    
    # --- RESCATE DE DATOS ANTIGUOS ---
    if 'Fecha' not in df_ver.columns:
        df_ver['Fecha'] = "2026-02-14"
    else:
        df_ver['Fecha'] = df_ver['Fecha'].fillna("2026-02-14")
    # --------------------------------
    
    st.subheader("📊 Historial General de Registros")
    st.dataframe(df_ver, use_container_width=True)
    # --- 4. CONSULTAR REPORTE POR FINCA (CON FECHAS) ---
    st.subheader("🔍 Consultar Reporte por Finca")
    lista_fincas = df_ver["Finca"].unique()
    finca_elegida = st.selectbox("Seleccione una finca:", lista_fincas)
    
    if finca_elegida:
        datos_finca = df_ver[df_ver["Finca"] == finca_elegida].sort_values(by="Fecha")
        ultima_finca = datos_finca.iloc[-1]
        
        st.info(f"📅 Mostrando último análisis para **{finca_elegida}** (Fecha: {ultima_finca['Fecha']})")
        
        # Lógica de Diagnóstico
        prom_actual = df_ver[df_ver["Cultivo"] == ultima_finca["Cultivo"]]["Precio_Seguro_x_Kg"].mean()
        dif_h = ((ultima_finca["Precio_Seguro_x_Kg"] - prom_actual) / prom_actual) * 100
        
        col_h1, col_h2 = st.columns(2)
        col_h1.metric("Costo Registrado", formato_cop(ultima_finca["Precio_Seguro_x_Kg"]))
        col_h2.metric("Estado vs Actualidad", f"{dif_h:+.1f}%", delta=f"{dif_h:+.1f}%", delta_color="inverse")

        if dif_h > 20:
            st.error(f"### 🔴 Análisis de Sobrecosto\n**📌 Posible causa:** Rendimiento bajo en la fecha {ultima_finca['Fecha']}.\n**📌 Acción:** Revisar insumos de ese periodo.")
        else:
            st.success(f"### 🟢 Análisis de Eficiencia\n**📌 Posible causa:** Buen manejo de recursos en este ciclo.\n**📌 Acción:** Replicar este método en la próxima siembra.")
