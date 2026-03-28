import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1️⃣ CONFIGURACIÓN DE GOOGLE SHEETS
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["GOOGLE_CREDS"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("agro").sheet1

# 🔥 CARGAR DATOS
data = sheet.get_all_records()
df_existente = pd.DataFrame(data)

# 2️⃣ BASE CLIMÁTICA
base_clima = {
    "Cundinamarca": 19, "Antioquia": 22, "Valle del Cauca": 24,
    "Huila": 25, "Tolima": 26, "Santander": 23, "Boyacá": 16,
    "Magdalena": 28, "Meta": 26, "Nariño": 18, "Casanare": 27,
    "Quindío": 21, "Caldas": 21, "Risaralda": 21, "Bolívar": 28
}

# --- INTERFAZ ---
st.set_page_config(page_title="Agrocadena Pro", layout="wide")
st.title("🚜 Consultoría Agrocadena: Inteligencia Agrícola")

with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("registro_finca"):
        nombre = st.text_input("Nombre de la Finca")
        cultivo = st.text_input("Cultivo")
        departamento = st.selectbox("Departamento", options=sorted(list(base_clima.keys())))
        
        # --- SECCIÓN DE UNIDADES ACTUALIZADA ---
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            # Aquí añadimos todas las unidades que pediste
            unidad = st.selectbox("Unidad de medida", ["Kg", "Quintales (50kg)", "Bultos (50kg)", "Libras"])
        with col_u2:
            produccion_input = st.number_input("Cantidad", min_value=1.0)
        
        # Conversión lógica a Kg
        if unidad == "Libras":
            produccion_kg = produccion_input * 0.5
        elif unidad in ["Quintales (50kg)", "Bultos (50kg)"]:
            produccion_kg = produccion_input * 50
        else:
            produccion_kg = produccion_input
            
        precio_venta = st.number_input("Precio de venta por Kg", min_value=0.0)
        inv_inicial = st.number_input("Inversión Inicial", min_value=0.0)
        costo_mensual = st.number_input("Costo mensual", min_value=0.0)
        meses = st.number_input("Meses", min_value=1.0)

        submit = st.form_submit_button("🚀 Calcular y Guardar")

        if submit:
            if nombre and cultivo:
                gasto_total = inv_inicial + (costo_mensual * meses)
                precio_minimo = gasto_total / produccion_kg
                ingreso = precio_venta * produccion_kg
                ganancia = ingreso - gasto_total
                
                nueva_fila = [
                    nombre, cultivo, departamento, produccion_kg,
                    inv_inicial, costo_mensual, meses, gasto_total,
                    precio_minimo, precio_venta, ingreso, ganancia
                ]
                
                sheet.append_row(nueva_fila)
                st.success("✅ Guardado en la nube")
                st.rerun()

# --- TABLA DE HISTORIAL ---
st.subheader("📋 Historial de Producción")
if not df_existente.empty:
    df_tabla = df_existente.copy()
    cols_dinero = ["Inversion_Inicial", "Costo_Mensual", "Costo_Total", "Precio_Minimo", "Precio_Venta", "Ingreso", "Ganancia"]
    for col in cols_dinero:
        if col in df_tabla.columns:
            df_tabla[col] = pd.to_numeric(df_tabla[col], errors='coerce').fillna(0)
    
    st.dataframe(df_tabla.style.format({
        "Inversion_Inicial": "${:,.0f}", "Costo_Mensual": "${:,.0f}",
        "Costo_Total": "${:,.0f}", "Precio_Minimo": "${:,.0f}",
        "Precio_Venta": "${:,.0f}", "Ingreso": "${:,.0f}", "Ganancia": "${:,.0f}",
        "Cantidad_Kg": "{:,.1f} kg"
    }), use_container_width=True)

# --- ANÁLISIS INTELIGENTE (EL PLAN DE ACCIÓN ESTÁ AQUÍ) ---
st.divider()
st.header("📊 Análisis y Diagnóstico")

if not df_existente.empty:
    df = df_existente.copy()
    for c in ["Precio_Venta", "Cantidad_Kg", "Costo_Total", "Ganancia"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    
    df["Costo_por_Kg"] = df["Costo_Total"] / df["Cantidad_Kg"].replace(0, 1)
    
    promedios = df.groupby("Cultivo")["Costo_por_Kg"].mean().reset_index()
    promedios.rename(columns={"Costo_por_Kg": "Promedio_Cultivo"}, inplace=True)
    df = df.merge(promedios, on="Cultivo", how="left")
    df["Eficiencia_%"] = ((df["Costo_por_Kg"] - df["Promedio_Cultivo"]) / df["Promedio_Cultivo"].replace(0, 1)) * 100

    st.subheader("🔎 Análisis por finca")
    finca_sel = st.selectbox("Selecciona una finca para diagnóstico", df["Nombre_Finca"].unique())
    row = df[df["Nombre_Finca"] == finca_sel].iloc[0]
    
    # Aseguramos que los valores sean tratables
    ganancia_f = float(row["Ganancia"])
    eficiencia_f = float(row["Eficiencia_%"])
    temp_f = base_clima.get(row["Departamento"], 20)

    # MÉTRICAS VISUALES
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Costo/Kg", f"${row['Costo_por_Kg']:,.0f}")
    m2.metric("Producción", f"{row['Cantidad_Kg']:,.0f} Kg", f"{row['Cantidad_Kg']/50:.1f} bultos/qq")
    m3.metric("Eficiencia", f"{eficiencia_f:.1f}%", delta_color="inverse")
    m4.metric("Ganancia Est.", f"${ganancia_f:,.0f}")

    # --- BLOQUE DE DIAGNÓSTICO Y PLAN DE ACCIÓN ---
    st.markdown("---")
    st.subheader("💡 Recomendación de Consultoría")
    
    # 1. Resultado Financiero (El cuadro que viste en rojo/verde)
    if ganancia_f > 0:
        st.success(f"🟢 La finca {finca_sel} está operando con GANANCIA.")
    elif ganancia_f < 0:
        st.error(f"🔴 La finca {finca_sel} está operando con PÉRDIDA.")
    else:
        st.info(f"🟡 La finca {finca_sel} está en punto de equilibrio.")

    # 2. Recomendación según Eficiencia
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Análisis de Costos:**")
        if eficiencia_f <= 0:
            st.info(f"✅ Eres eficiente: Tus costos son un {abs(eficiencia_f):.1f}% menores al promedio.")
        else:
            st.warning(f"⚠️ Costos elevados: Estás un {eficiencia_f:.1f}% por encima del promedio del sector.")

    with col_b:
        st.markdown("**Plan de Acción:**")
        # Aquí está la lógica del plan que te faltaba
        if ganancia_f < 0 and eficiencia_f > 0:
            st.write("👉 **Urgente:** Reduce costos fijos y revisa el precio de los insumos.")
        elif ganancia_f < 0 and eficiencia_f <= 0:
            st.write("👉 **Estrategia:** Tu costo es bueno, pero el precio de venta es muy bajo. ¡Busca mejores mercados!")
        elif ganancia_f > 0 and eficiencia_f > 10:
            st.write("👉 **Optimización:** Ganas dinero, pero podrías ganar mucho más si controlas mejor los gastos.")
        else:
            st.write("👉 **Escalabilidad:** ¡Buen trabajo! Considera aumentar tu área de producción.")

    # 3. Nota Climática (Basada en tu infografía)
    st.info(f"🌡️ **Dato Climático:** En {row['Departamento']} la temp. promedio es {temp_f}°C. Ajusta tu riego según la guía técnica.")
