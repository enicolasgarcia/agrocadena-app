import streamlit as st
import pandas as pd
import os
import re

# 1. Configuración de página
st.set_page_config(page_title="App Agrícola Pro", layout="wide")

# 2. Diccionario de cultivos
precios_market = {
    "café": 15000, "aguacate papelillo": 10550, "granadilla": 7666, "patilla": 1900,
    "ahuyama": 1650, "pimentón": 5500, "uchuva": 5500, "lulo": 5400,
    "guanábana": 4750, "piña gold": 2500, "banano criollo": 2350,
    "plátano hartón": 4625, "cebolla junca": 2250, "tomate chonto": 2613,
    "frijol verde": 4900, "aguacate hass": 6500, "mango tommy": 2700,
    "mandarina arrayana": 4318, "papa": 2800, "fresa": 8500
}

# 3. Funciones de formato
def formato_cop(valor):
    try:
        return f"$ {float(valor):,.0f}".replace(",", ".")
    except: return str(valor)

def limpiar_produccion(texto):
    if pd.isna(texto): return ""
    texto = str(texto)
    return re.sub(r'(\.\d{1,2})\d+', r'\1', texto)

# 4. Interfaz Principal
st.title("🚜 Aplicación Agrícola Pro")
st.markdown("---")
archivo_db = "fincas_registradas.xlsx"

with st.expander("📝 Registrar Nuevo Lote", expanded=True):
    with st.form("registro_pro"):
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre de la Finca/Lote")
            cultivo_sel = st.selectbox("Seleccione el Cultivo", sorted(precios_market.keys()))
            meses = st.slider("Ciclo del cultivo (meses)", 1, 24, 6)
        with c2:
            inversion = st.number_input("Inversión Inicial", min_value=0.0, step=100000.0)
            mantenimiento = st.number_input("Mantenimiento Mensual", min_value=0.0, step=10000.0)
            
            # CORRECCIÓN DEFINITIVA DE COLUMNAS
            col_cant, col_unid = st.columns(2)
            with col_cant:
                cantidad_raw = st.number_input("Cantidad cosechada", min_value=0.01)
            with col_unid:
                unidad = st.selectbox("Unidad", ["Kilos", "Libras", "Quintales", "Gramos"])
        
        # Botón dentro del formulario
        boton = st.form_submit_button("🚀 Calcular y Guardar")

# 5. Lógica de cálculo
if boton:
    conv = {"Kilos": 1.0, "Libras": 0.5, "Quintales": 50.0, "Gramos": 0.001}
    produccion_en_kilos = cantidad_raw * conv[unidad]
    costo_total = inversion + (mantenimiento * meses)
    precio_seguro = costo_total / produccion_en_kilos
    
    nueva_fila = pd.DataFrame([{
        "Finca": nombre, "Cultivo": cultivo_sel, "Tiempo (Meses)": meses,
        "Inversión": inversion, "Costo_Total": costo_total,
        "Precio_Seguro_x_Kg": precio_seguro, "Producción": f"{cantidad_raw} {unidad}",
        "Kilos_Totales": produccion_en_kilos
    }])
    
    if os.path.exists(archivo_db):
        df_ex = pd.read_excel(archivo_db)
        df_final = pd.concat([df_ex, nueva_fila], ignore_index=True)
    else: 
        df_final = nueva_fila
    
    df_final.to_excel(archivo_db, index=False)
    st.success(f"✅ ¡{nombre} guardado!")

    # Indicador de Eficiencia
    datos_cultivo = df_final[df_final['Cultivo'] == cultivo_sel]
    promedio_sector = datos_cultivo['Precio_Seguro_x_Kg'].mean()
    
    st.markdown("### 📊 Indicador de Eficiencia")
    if len(datos_cultivo) > 1:
        dif = ((precio_seguro - promedio_sector) / promedio_sector) * 100
        m1, m2, m3 = st.columns(3)
        m1.metric("Tu costo/Kg", formato_cop(precio_seguro))
        m2.metric("Promedio sector", formato_cop(promedio_sector))
        m3.metric("Diferencia", f"{dif:+.1f}%", delta=f"{dif:+.1f}%", delta_color="inverse")

    # --- NUEVA SECCIÓN: INTERPRETACIÓN AUTOMÁTICA ---
        st.markdown("#### 💡 Recomendación del Asesor Virtual")
        
        # Interpretación de eficiencia
        if dif > 20:
            st.error(f"⚠️ **Alerta de Sobrecosto:** Tus costos están muy por encima del promedio. Revisa desperdicios o insumos caros.")
        elif 0 < dif <= 20:
            st.warning(f"🧐 **Oportunidad de Mejora:** Estás cerca del promedio, pero puedes optimizar gastos.")
        else:
            st.success(f"🌟 **¡Excelente Gestión!** Eres más eficiente que el promedio de la zona.")

        # Comparativa con el Precio de Mercado (Corabastos)
        precio_mercado = precios_market.get(cultivo_sel, 0)
        if precio_mercado > 0:
            margen = precio_mercado - precio_seguro
            if margen > 0:
                st.info(f"💰 **Análisis de Ganancia:** El precio en Corabastos es {formato_cop(precio_mercado)}. Ganarías **{formato_cop(margen)}** por kilo.")
            else:
                st.error(f"📉 **Riesgo:** El precio de mercado ({formato_cop(precio_mercado)}) no cubre tus costos actuales.")
    else:
        st.info(f"💡 Eres el primer dato de {cultivo_sel}. ¡Tu costo servirá de referencia!")

# 6. Historial
st.markdown("---")
if os.path.exists(archivo_db):
    try:
        df_vista = pd.read_excel(archivo_db)
        st.subheader("📋 Historial de Producción")
        for col in ["Inversión", "Costo_Total", "Precio_Seguro_x_Kg"]:
            if col in df_vista.columns: 
                df_vista[col] = df_vista[col].apply(formato_cop)
        st.dataframe(df_vista.drop(columns=["Kilos_Totales"], errors='ignore'), use_container_width=True)
    except:
        st.error("Error al leer la base de datos. Asegúrate de registrar una finca primero.")
    
