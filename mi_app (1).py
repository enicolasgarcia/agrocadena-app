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
    # Busca números con más de 2 decimales y los recorta
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
            
            # Fila de producción y unidades
            col_cant, col_unid = st.columns([2, 1])
            with col_cant:
                cantidad_raw = st.number_input("Cantidad cosechada", min_value=0.01)
            with col_unid:
                unidad = st.selectbox("Unidad", ["Kilos", "Libras", "Quintales", "Gramos"])
            
        boton = st.form_submit_button("🚀 Calcular y Guardar")

# 5. Lógica de cálculo
if boton:
    # Conversiones internas a Kilos
    conv = {"Kilos": 1.0, "Libras": 0.5, "Quintales": 50.0, "Gramos": 0.001}
    produccion_en_kilos = cantidad_raw * conv[unidad]
    
    # Cálculos financieros
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
        "Producción": f"{cantidad_raw} {unidad}"
    }])
    
    if os.path.exists(archivo_db):
        df_existente = pd.read_excel(archivo_db)
        pd.concat([df_existente, nueva_fila], ignore_index=True).to_excel(archivo_db, index=False)
    else:
        nueva_fila.to_excel(archivo_db, index=False)
    
    st.success(f"✅ ¡{nombre} guardado exitosamente!")
    st.info(f"💡 **Análisis:** Para no perder dinero en **{meses} meses**, vende el kilo de **{cultivo}** a mínimo **{formato_cop(precio_seguro)}**.")

# 6. Visualización del Historial
st.markdown("---")
if os.path.exists(archivo_db):
    df_mostrar = pd.read_excel(archivo_db)
    st.subheader("📋 Historial de Producción")
    
    # Limpieza visual para la tabla
    df_vista = df_mostrar.copy()
    
    # Formatear dinero
    cols_dinero = ["Inversión", "Costo_Total", "Precio_Seguro_x_Kg"]
    for col in cols_dinero:
        if col in df_vista.columns:
            df_vista[col] = df_vista[col].apply(formato_cop)
    
    # Formatear producción (quitar decimales infinitos)
    if "Producción" in df_vista.columns:
        df_vista["Producción"] = df_vista["Producción"].apply(limpiar_produccion)
        
    st.dataframe(df_vista, use_container_width=True)
else:
    st.write("Aún no hay registros. ¡Ingresa el primero arriba!")
    