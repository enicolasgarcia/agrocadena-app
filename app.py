import streamlit as st
import pandas as pd
import os

# 1. CONFIGURACIÓN INICIAL Y BASE DE DATOS CLIMÁTICA
archivo_base = "https://docs.google.com/spreadsheets/d/11i4eNs0dj2veqdfYWTDizF3zbCsJzQx9N9iKaYntYNg/edit?gid=513628329#gid=513628329"

# Diccionario de temperaturas promedio por departamento (Basado en tus imágenes)
base_clima = {
    "Cundinamarca": 19, "Antioquia": 22, "Valle del Cauca": 24,
    "Huila": 25, "Tolima": 26, "Santander": 23, "Boyacá": 16,
    "Magdalena": 28, "Meta": 26, "Nariño": 18, "Casanare": 27,
    "Quindío": 21, "Caldas": 21, "Risaralda": 21, "Bolívar": 28
}

# Intentamos cargar el archivo, si no existe, creamos el DataFrame con la nueva columna 'Departamento'
if os.path.exists(archivo_base):
    df_existente = pd.read_excel(archivo_base)
else:
    st.info("No se encuentra archivo.")
    columnas = ['Nombre_Finca', 'Cultivo', 'Departamento', 'Inversion_Inicial', 'Costo_Mensual', 'Meses', 'Costo_Total', 'Precio_Minimo']
    df_existente = pd.DataFrame(columns=columnas)

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Agrocadena Pro", layout="wide")
st.title("🚜 Consultoría Agrocadena: Punto de Equilibrio Inteligente")

with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("registro_finca"):
        nombre = st.text_input("Nombre de la Finca")
        cultivo = st.text_input("Cultivo (ej: Pepino, Mango)")
        
        # NUEVO: Selector de Departamento
        departamento = st.selectbox("Ubicación (Departamento)", options=sorted(list(base_clima.keys())))
        
        produccion = st.number_input("Producción esperada (Kg/Unidades)", min_value=1.0)
        inv_inicial = st.number_input("Inversión Inicial ($)", min_value=0.0)
        costo_mensual = st.number_input("Costo mensual operativo ($)", min_value=0.0)
        meses = st.number_input("Meses que dura el ciclo", min_value=1.0)
        
        submit = st.form_submit_button("🚀 Calcular y Guardar")

        if submit:
            if nombre and cultivo:
                # LÓGICA DE CÁLCULO
                gasto_total = inv_inicial + (costo_mensual * meses)
                precio_minimo = gasto_total / produccion
                
                # LÓGICA CLIMÁTICA (Basada en tus imágenes)
                temp_finca = base_clima[departamento]
                
                # Crear nueva fila con Departamento
                nueva_fila = pd.DataFrame([{
                    'Nombre_Finca': nombre,
                    'Cultivo': cultivo,
                    'Departamento': departamento,
                    'Inversion_Inicial': inv_inicial,
                    'Costo_Mensual': costo_mensual,
                    'Meses': meses,
                    'Costo_Total': gasto_total,
                    'Precio_Minimo': precio_minimo
                }])

                # Combinar y guardar
                df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
                #df_final.to_excel(archivo_base, index=False)
                
                st.success(f"✅ ¡{nombre} en {departamento} guardado!")
                
                # Alerta Climática Inmediata
                if temp_finca > 27:
                    st.warning(f"🔥 Alerta en {departamento}: Temp de {temp_finca}°C. Riesgo de estrés hídrico.")
                elif temp_finca < 17:
                    st.info(f"❄️ Alerta en {departamento}: Temp de {temp_finca}°C. Crecimiento más lento.")
                
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ Por favor, completa nombre y cultivo.")

# --- CUERPO PRINCIPAL ---
col_tabla, col_guia = st.columns([2, 1])

with col_tabla:
    st.subheader("Historial de Fincas")
    if not df_existente.empty:
        st.dataframe(df_existente, use_container_width=True)
    else:
        st.info("Aún no hay fincas registradas.")

with col_guia:
    st.subheader("🌱 Guía Técnica")
    # Mostramos las imágenes que encontraste
    if os.path.exists("1000023360.jpg"):
        st.image("1000023360.jpg", caption="Ciclo de Vida del Cultivo")
    if os.path.exists("1000023362.jpg"):
        st.image("1000023362.jpg", caption="Impacto del Clima")

# --- SECCIÓN DE ANÁLISIS ---
st.markdown("---")
st.header("📊 Análisis de Eficiencia y Sectorial")

if not df_existente.empty:
    # 1. MÉTRICAS GLOBALES
    m1, m2, m3 = st.columns(3)
    m1.metric("Gasto Promedio", f"${df_existente['Costo_Total'].mean():,.0f}")
    m2.metric("Precio Mínimo Promedio", f"${df_existente['Precio_Minimo'].mean():,.0f}")
    m3.metric("Total Fincas", len(df_existente))

    # 2. GRÁFICO POR DEPARTAMENTO (NUEVO)
    st.subheader("🌎 Costos por Departamento")
    costos_dept = df_existente.groupby('Departamento')['Costo_Total'].sum()
    st.bar_chart(costos_dept)

    # 3. BUSCADOR
    st.subheader("🔍 Buscador")
    busqueda = st.text_input("Buscar finca, cultivo o departamento:")
    if busqueda:
        mask = df_existente.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        st.dataframe(df_existente[mask])

# --- BOTÓN DESCARGA ---
st.sidebar.markdown("---")
if os.path.exists(archivo_base):
    with open(archivo_base, "rb") as f:
        st.sidebar.download_button(
            label="📥 Descargar Excel actualizado",
            data=f,
            file_name="fincas_agrocadena.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_descarga_unico"
        )
