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
    try:
        return f"$ {float(valor):,.0f}".replace(",", ".")
    except:
        return str(valor)

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
            
            # Arreglo de la línea 51 que causaba el error
            col_cant, col_unid = st.columns()
            with col_cant:
                cantidad_raw = st.number_input("Cantidad cosechada", min_value=0.01)
            with col_unid:
                unidad = st.selectbox("Unidad", ["Kilos", "Libras", "Quintales", "Gramos"])
        
        # El botón DEBE estar dentro del bloque 'with st.form'
        boton = st.form_submit_button("🚀 Calcular y Guardar")

# 5. Lógica de cálculo y Eficiencia
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
        df_existente = pd.read_excel(archivo_db)
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
    else:
        df_final = nueva_fila
    
    df_final.to_excel(archivo_db, index=False)
    
    st.success(f"✅ ¡{nombre} guardado exitosamente!")
    
    # Análisis de Eficiencia
    datos_cultivo = df_final[df_final['Cultivo'] == cultivo_sel]
    promedio_sector = datos_cultivo['Precio_Seguro_x_Kg'].mean()
    
    st.markdown("### 📊 Indicador de Eficiencia por Cultivo")
    if len(datos_cultivo) > 1:
        dif_porc = ((precio_seguro - promedio_sector) / promedio_sector) * 100
        m1, m2, m3 = st.columns(3)
        m1.metric("Tu costo/Kg", formato_cop(precio_seguro))
        m2.metric("Promedio sector", formato_cop(promedio_sector))
        m3.metric("Diferencia", f"{dif_porc:+.1f}%", delta=f"{dif_porc:+.1f}%", delta_color="inverse")
        
        if precio_seguro <= promedio_sector:
            st.info("🟢 Tu costo está por DEBAJO del promedio.")
        else:
            st.warning(f"🟡 Tu costo es un {dif_porc:.1f}% superior al promedio.")
    else:
        st.info(f"💡 Eres el primer dato de **{cultivo_sel}**. ¡Gracias por iniciar la base!")

# 6. Historial
st.markdown("---")
if os.path.exists(archivo_db):
    df_mostrar = pd.read_excel(archivo_db)
    st.subheader("📋 Historial de Producción")
    df_vista = df_mostrar.copy()
    for col in ["Inversión", "Costo_Total", "Precio_Seguro_x_Kg"]:
        if col in df_vista.columns: df_vista[col] = df_vista[col].apply(formato_cop)
    if "Producción" in df_vista.columns: df_vista["Producción"] = df_vista["Producción"].apply(limpiar_produccion)
    if "Kilos_Totales" in df_vista.columns: df_vista = df_vista.drop(columns=["Kilos_Totales"])
    st.dataframe(df_vista, use_container_width=True)
    
