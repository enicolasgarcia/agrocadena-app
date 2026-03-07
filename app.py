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
    # 1. Conversión de unidades a KG (Definimos la variable aquí primero)
    factores = {"Bultos": 50, "Toneladas": 1000, "Libras": 0.5, "Kilos": 1}
    cantidad_kg = cantidad * factores.get(unidad, 1)
    
    # 2. Cálculo de precios
    precio_ref = precios_market.get(cultivo_sel, 0)
    ingreso_est = cantidad_kg * precio_ref
    
    # Cálculo seguro del costo por kilo
    if cantidad_kg > 0:
        costo_kg = costo_total / cantidad_kg
    else:
        costo_kg = 0
        st.warning("⚠️ La cantidad es 0, el costo se registró como $0.")

    # 3. Crear el nuevo registro (Ahora cantidad_kg existe sí o sí)
    nuevo_dato = pd.DataFrame({
        "Fecha": [fecha_registro.strftime("%Y-%m-%d")],
        "Finca": [finca],
        "Cultivo": [cultivo_sel],
        "Costo_Total": [costo_total],
        "Cantidad_Kg": [cantidad_kg],
        "Precio_Costo_Kg": [costo_kg],
        "Venta_Estimada": [ingreso_est]
    })
    
    # 4. Guardar en Excel
    if os.path.exists(archivo_db):
        df_old = pd.read_excel(archivo_db)
        df_final = pd.concat([df_old, nuevo_dato], ignore_index=True)
    else:
        df_final = nuevo_dato
    
    df_final.to_excel(archivo_db, index=False)
    st.success(f"✅ ¡Registro de '{finca}' guardado con éxito!")

# --- 2. HISTORIAL GENERAL (AHORA DE PRIMERAS) ---
if os.path.exists(archivo_db):
    df_ver = pd.read_excel(archivo_db)
    st.divider()
    st.subheader("📝 1. Historial General de Registros")
    
    df_limpio = df_ver.copy()
    if "Fecha" not in df_limpio.columns:
        df_limpio["Fecha"] = datetime.date.today().strftime("%Y-%m-%d")
    
    try:
        df_limpio = df_limpio.sort_values(by="Fecha", ascending=False)
    except:
        pass

    cols_plata = ["Costo_Total", "Precio_Costo_Kg", "Precio_Seguro_x_Kg", "Venta_Estimada"]
    for col in cols_plata:
        if col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].apply(lambda x: f"$ {x:,.0f}" if pd.notnull(x) else "$ 0")

    st.dataframe(df_limpio, use_container_width=True)

    # --- 3. CONSULTA DETALLADA (SEGUNDO) ---
    st.divider()
    st.subheader("🔍 2. Consulta de Reporte Detallado")
    
    col_sel1, col_sel2 = st.columns(2)
    lista_fincas = df_ver["Finca"].unique()
    finca_elegida = col_sel1.selectbox("Seleccione una finca para analizar:", lista_fincas)

    if finca_elegida:
        cultivos_finca = df_ver[df_ver["Finca"] == finca_elegida]["Cultivo"].unique()
        cultivo_elegido = col_sel2.selectbox("Seleccione el cultivo:", cultivos_finca)
        
        if cultivo_elegido:
            datos_esp = df_ver[(df_ver["Finca"] == finca_elegida) & (df_ver["Cultivo"] == cultivo_elegido)]
            ultima = datos_esp.iloc[-1]
            
            # --- 4. ANÁLISIS DE EFICIENCIA (TERCERO) ---
            st.markdown(f"### 📊 3. Análisis de Eficiencia: {cultivo_elegido}")
            
            col_costo = "Precio_Costo_Kg" if "Precio_Costo_Kg" in df_ver.columns else "Precio_Seguro_x_Kg"
            costo_actual = ultima.get(col_costo, 0)
            promedio_historico = df_ver[df_ver["Cultivo"] == cultivo_elegido][col_costo].mean()

            m1, m2, m3 = st.columns(3)
            m1.metric("Costo Actual / Kg", formato_cop(costo_actual))
            m2.metric("Promedio Histórico", formato_cop(promedio_historico))
            
            if promedio_historico > 0:
                dif_pct = ((costo_actual - promedio_historico) / promedio_historico) * 100
                m3.metric("Diferencia", f"{dif_pct:+.1f}%", delta=f"{dif_pct:+.1f}%", delta_color="inverse")
                
                # --- 5. DIAGNÓSTICO DEL ASESOR (ÚLTIMO) ---
                st.markdown("---")
                st.subheader("💡 4. Diagnóstico del Asesor Virtual")
                
                if dif_pct > 10:
                    st.error(f"⚠️ **Análisis:** En **{finca_elegida}**, tus costos de **{cultivo_elegido}** están un {dif_pct:.1f}% por encima del promedio. Se recomienda revisar el gasto en insumos.")
                elif dif_pct < -10:
                    st.success(f"🌟 **Análisis:** ¡Excelente! Tu producción de **{cultivo_elegido}** es muy eficiente ({abs(dif_pct):.1f}% mejor que el promedio).")
                else:
                    st.info(f"✅ **Análisis:** Los costos de **{cultivo_elegido}** se mantienen estables respecto al promedio.")
else:
    st.info("👋 Registre su primera cosecha arriba para activar el historial y el análisis.")
