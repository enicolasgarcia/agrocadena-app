import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CONFIGURACIÓN INICIAL (Como en tu Jupyter)
archivo_base = 'fincas_registradas.xlsx'

# Intentamos cargar el archivo, si no existe, creamos el DataFrame vacío
if os.path.exists(archivo_base):
    df_existente = pd.read_excel(archivo_base)
else:
    columnas = ['Nombre_Finca', 'Cultivo', 'Inversion_Inicial', 'Costo_Mensual', 'Meses', 'Costo_Total', 'Precio_Minimo']
    df_existente = pd.DataFrame(columns=columnas)

# --- INTERFAZ DE USUARIO ---
st.title("🚜 Consultoría Agrocadena: Punto de Equilibrio")

with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("registro_finca"):
        nombre = st.text_input("Nombre de la Finca")
        cultivo = st.text_input("Cultivo (ej: Mango, Lulo)")
        produccion = st.number_input("Producción esperada (Kg/Unidades)", min_value=1.0)
        inv_inicial = st.number_input("Inversión Inicial ($)", min_value=0.0)
        costo_mensual = st.number_input("Costo mensual operativo ($)", min_value=0.0)
        meses = st.number_input("Meses que dura el ciclo", min_value=1.0)
        
        submit = st.form_submit_button("🚀 Calcular y Guardar")

        if submit:
            if nombre:
                # LÓGICA DE TU JUPYTER
                gasto_total = inv_inicial + (costo_mensual * meses)
                precio_minimo = gasto_total / produccion
                
                # Crear nueva fila
                nueva_fila = pd.DataFrame([{
                    'Nombre_Finca': nombre,
                    'Cultivo': cultivo,
                    'Inversion_Inicial': inv_inicial,
                    'Costo_Mensual': costo_mensual,
                    'Meses': meses,
                    'Costo_Total': gasto_total,
                    'Precio_Minimo': precio_minimo
                }])

                # Combinar y guardar localmente
                df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
                df_final.to_excel(archivo_base, index=False)
                
                st.success(f"✅ ¡{nombre} guardado exitosamente!")
                st.balloons()
                st.rerun() # Refresca para mostrar la tabla actualizada
            else:
                st.error("⚠️ Por favor, ingresa el nombre de la finca.")

# --- MOSTRAR RESULTADOS EN PANTALLA PRINCIPAL ---
st.subheader("📋 Historial de Fincas")
# Mostramos los datos cargados o los nuevos
if os.path.exists(archivo_base):
    df_mostrar = pd.read_excel(archivo_base)
    st.dataframe(df_mostrar)
else:
    st.info("Aún no hay fincas registradas.")

# --- BOTÓN PARA DESCARGAR EL EXCEL A TU PC ---
st.sidebar.markdown("---")
if os.path.exists(archivo_base):
    with open(archivo_base, "rb") as f:
        st.sidebar.download_button(
            label="📥 Descargar Excel a mi PC",
            data=f,
            file_name="fincas_registradas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# --- SECCIÓN DE ANÁLISIS DE EFICIENCIA Y RENTABILIDAD ---
st.markdown("---")
st.header("📊 Análisis de Eficiencia y Sectorial")

# Usamos df_existente o df_mostrar (la que tengas definida arriba)
df_analisis = df_existente 

if not df_analisis.empty:
    # 1. MÉTRICAS GLOBALES
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gasto Promedio", f"${df_analisis['Costo_Total'].mean():,.0f}")
    with col2:
        st.metric("Precio Mínimo Promedio", f"${df_analisis['Precio_Minimo'].mean():,.0f}")
    with col3:
        st.metric("Total Fincas", len(df_analisis))

    # 2. GRÁFICO DE COSTOS POR CULTIVO
    st.subheader("📈 Inversión por Cultivo")
    st.bar_chart(df_analisis.groupby('Cultivo')['Costo_Total'].sum())

    # 3. BUSCADOR
    st.subheader("🔍 Buscador de Historial")
    busqueda = st.text_input("Filtrar por nombre o cultivo:")
    if busqueda:
        df_filtrado = df_analisis[df_analisis['Nombre_Finca'].str.contains(busqueda, case=False)]
        st.dataframe(df_filtrado)
else:
    st.info("Registra datos para ver el análisis.")

# --- BOTÓN DE DESCARGA (Esto ya lo tenías, déjalo al final) ---
if os.path.exists(archivo_base):
    # ... (tu código del botón de descarga)
