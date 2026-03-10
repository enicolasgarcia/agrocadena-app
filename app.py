import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Agrocadena Pro - Google Sheets", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        return pd.DataFrame(columns=["Fecha", "Finca", "Cultivo", "Costo_Total", "Cantidad_Kg", "Precio_Kg"])

df_existente = cargar_datos()

if df_existente.empty:
    st.info("Aún no tienes datos. Registra tu primera finca en el menú de la izquierda.")
else:
    st.write("### Registros Actuales")
    st.dataframe(df_existente)

st.title("🚜 Gestión Agrícola Permanente")
st.markdown("Los datos se guardan automáticamente en tu Google Sheets.")

# --- FORMULARIO DE REGISTRO ---
with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("registro_finca"):
        finca_nombre = st.text_input("Nombre de la Finca")
        cultivo_tipo = st.selectbox("Cultivo", ["Mango Tommy", "Aguacate", "Limón"])
        costo_t = st.number_input("Costo Total ($)", min_value=0)
        cantidad_k = st.number_input("Cantidad (Kg)", min_value=1)
        
        if st.form_submit_button("🚀 Guardar y Analizar"):
            nueva_fila = pd.DataFrame([{
               "Fecha": datetime.now().strftime("%Y-%m-%d"),
               "Finca": finca_nombre,
               "Cultivo": cultivo_tipo,
               "Costo_Total": costo_t,
               "Cantidad_Kg": cantidad_k,
               "Precio_Kg": costo_t / cantidad_k
            }])

            datos_actuales = conn.read(worksheet="Sheet1")
        
            df_actualizado = pd.concat([datos_actuales, nueva_fila], ignore_index=True)
        
            conn.update(
               worksheet="Sheet1",
               data=df_actualizado
            )

            st.success("¡Datos guardados!")
            st.balloons()
            st.rerun()

# --- LÓGICA DE ANÁLISIS (Tu cerebro de la App) ---
if not df_existente.empty:
    st.write("### Registros Actuales")
    st.dataframe(df_existente)
    
    # 1. Historial
    st.subheader("📝 Historial de Producción")
    st.dataframe(df_existente, use_container_width=True)

    # 2. Análisis de Eficiencia
    st.divider()
    st.subheader("📊 Análisis de Eficiencia")
    
    col_f, col_c = st.columns(2)
    finca_sel = col_f.selectbox("Selecciona Finca para analizar", df_existente["Finca"].unique())
    cultivo_sel = col_c.selectbox(
        "Selecciona Cultivo",
        df[df["Finca"] == finca_sel]["Cultivo"].unique()
    )

    # Filtrar datos para el análisis
    datos_finca = df_existente[(df_existente["Finca"] == finca_sel) & (df_existente["Cultivo"] == cultivo_sel)]
    precio_actual = datos_finca["Precio_Kg"].iloc[-1]
    
    # Calcular promedio histórico de ese cultivo en TODAS las fincas
    promedio_historico = df_existente[df_existente["Cultivo"] == cultivo_sel]["Precio_Kg"].mean()
    diferencia = ((precio_actual - promedio_historico) / promedio_historico) * 100

    # 3. Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Costo Actual ($/Kg)", f"${precio_actual:,.2f}")
    m2.metric("Promedio Histórico", f"${promedio_historico:,.2f}")
    m3.metric("Eficiencia", f"{diferencia:+.2f}%", delta_color="inverse")

    # 4. Diagnóstico del Asesor
    st.info("💡 **Diagnóstico del Asesor:**")
    if diferencia <= 0:
        st.success(f"¡Excelente! En {finca_sel}, el costo de {cultivo_sel} está un {abs(diferencia):.1f}% por DEBAJO del promedio. Vas por buen camino.")
    else:
        st.error(f"Atención: El costo en {finca_sel} es un {diferencia:.1f}% más ALTO que el promedio. Revisa insumos o mano de obra.")

else:
    st.info("Aún no tienes datos. Registra tu primera finca en el menú de la izquierda.")
