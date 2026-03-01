import streamlit as st
import pandas as pd
import os
import re

# 1. Configuración de página
st.set_page_config(page_title="App Agrícola Pro", layout="wide")

# 2. Diccionario de cultivos con precios de Corabastos
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
    """Convierte números en formato de moneda colombiana $ 10.000"""
    try:
        return f"$ {float(valor):,.0f}".replace(",", ".")
    except:
        return str(valor)

def limpiar_produccion(texto):
    """Limpia los decimales largos de la producción (ej: 0.6000004 -> 0.6)"""
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
            cultivo = st.selectbox("Seleccione el Cultivo", sorted(precios_market.keys()))
            meses = st.slider("Ciclo del cultivo (meses)", 1, 24, 6)
            
        with c2:
            inversion = st.number_input("Inversión Inicial", min_value=0.0, step=100000.0)
            mantenimiento = st.number_input("Mantenimiento Mensual", min_value=0.0, step=10000.0)
            
            col_cant, col_unid = st.columns()
            with col_cant:
                cantidad_raw = st.number_input("Cantidad cosechada", min_value=0.01)
            with col_unid:
                unidad = st.selectbox("Unidad", ["Kilos", "Libras", "Quintales", "Gramos"])
            
        boton = st.form_submit_button("🚀 Calcular y Guardar")

# 5. Lógica de cálculo y Visualización de Resultados Actuales
if boton:
    # Conversiones internas a Kilos
    conv = {"Kilos": 1.0, "Libras": 0.5, "Quintales": 50.0, "Gramos": 0.001}
    produccion_en_kilos = cantidad_raw * conv[unidad]
    
    # Cálculos financieros actuales
    costo_total = inversion + (mantenimiento * meses)
    precio_seguro = costo_total / produccion_en_kilos
    
    # Guardado en Excel
    nueva_fila = pd.DataFrame([{
        "Finca": nombre,
        "Cultivo": cultivo,
        "Tiempo (Meses)": meses,
        "Inversión": inversion,
        "Costo_Total": costo_total,
        "Precio_Seguro_x_Kg": precio_seguro,
        "Producción": f"{cantidad_raw} {unidad}",
        "Kilos_Totales": produccion_en_kilos # Columna oculta para cálculos
    }])
    
    if os.path.exists(archivo_db):
        df_existente = pd.read_excel(archivo_db)
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
    else:
        df_final = nueva_fila
    
    df_final.to_excel(archivo_db, index=False)
    
    # --- NUEVA SECCIÓN: INDICADOR DE EFICIENCIA ---
    st.success(f"✅ ¡{nombre} guardado exitosamente!")
    
    # Filtrar datos del mismo cultivo para el promedio
    datos_cultivo = df_final[df_final['Cultivo'] == cultivo]
    promedio_sector = datos_cultivo['Precio_Seguro_x_Kg'].mean()
    
    st.markdown("### 📊 Indicador de Eficiencia por Cultivo")
    
    if len(datos_cultivo) > 1:
        dif_porc = ((precio_seguro - promedio_sector) / promedio_sector) * 100
        
        col_met1, col_met2, col_met3 = st.columns(3)
        col_met1.metric("Tu costo por kilo", formato_cop(precio_seguro))
        col_met2.metric("Promedio sector", formato_cop(promedio_sector))
        col_met3.metric("Diferencia", f"{dif_porc:+.1f}%", delta=f"{dif_porc:+.1f}%", delta_color="inverse")
        
        if precio_seguro <= promedio_sector:
            st.info(f"🟢 **Eficiencia Alta:** Tu costo está por DEBAJO del promedio del sector.")
        else:
            st.warning(f"🟡 **Eficiencia Media:** Tu costo es un {dif_porc:.1f}% superior al promedio. Revisa tus gastos de mantenimiento.")
    else:
        st.info(f"💡 Eres el primer productor de **{cultivo}** en el sistema. ¡Tu dato de **{formato_cop(precio_seguro)}** servirá de referencia!")

# 6. Visualización del Historial
st.markdown("---")
if os.path.exists(archivo_db):
    df_mostrar = pd.read_excel(archivo_db)
    st.subheader("📋 Historial de Producción")
    
    df_vista = df_mostrar.copy()
    
    # Formatear dinero para la tabla
    cols_dinero = ["Inversión", "Costo_Total", "Precio_Seguro_x_Kg"]
    for col in cols_dinero:
        if col in df_vista.columns:
            df_vista[col] = df_vista[col].apply(formato_cop)
    
    # Formatear producción
    if "Producción" in df_vista.columns:
        df_vista["Producción"] = df_vista["Producción"].apply(limpiar_produccion)
        
    # No mostrar la columna técnica de Kilos_Totales en la tabla
    if "Kilos_Totales" in df_vista.columns:
        df_vista = df_vista.drop(columns=["Kilos_Totales"])
        
    st.dataframe(df_vista, use_container_width=True)
else:
    st.write("Aún no hay registros. ¡Ingresa el primero arriba!")
    
