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

# 2️⃣ BASE CLIMÁTICA Y DE MERCADO (CORABASTOS 19 MARZO)
base_clima = {
    "Cundinamarca": 19, "Antioquia": 22, "Valle del Cauca": 24,
    "Huila": 25, "Tolima": 26, "Santander": 23, "Boyacá": 16,
    "Magdalena": 28, "Meta": 26, "Nariño": 18, "Casanare": 27,
    "Quindío": 21, "Caldas": 21, "Risaralda": 21, "Bolívar": 28
}

# Precios extraídos de tu boletín (Precio por Kg)
precios_corabastos = {
    "pepino": 5000,
    "lulo": 5200,
    "mango tommy": 9091,
    "mango de azucar": 6000,
    "tomate de arbol": 2800,
    "papa pastusa": 1500,
    "cebolla": 1100,
    "aguacate": 5000,
    "fresa": 6500,
    "banano": 2000,
    "cafe": 11000 # Precio referencial por Kg según boletín
}

# --- INTERFAZ ---
st.set_page_config(page_title="Agrocadena Pro", layout="wide")
st.title("🚜 Consultoría Agrocadena: Inteligencia Agrícola")

with st.sidebar:
    st.header("📝 Nuevo Registro")
    with st.form("registro_finca"):
        nombre = st.text_input("Nombre de la Finca")
        cultivo = st.text_input("Cultivo (Ej: Pepino, Lulo, Papa Pastusa)")
        departamento = st.selectbox("Departamento", options=sorted(list(base_clima.keys())))
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            unidad = st.selectbox("Unidad de medida", ["Kg", "Quintales (50kg)", "Bultos (50kg)", "Libras"])
        with col_u2:
            produccion_input = st.number_input("Cantidad", min_value=1.0)
        
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

# --- ANÁLISIS INTELIGENTE ---
st.divider()
st.header("📊 Análisis y Diagnóstico")

if not df_existente.empty:
    df = df_existente.copy()
    for c in ["Precio_Venta", "Cantidad_Kg", "Costo_Total", "Ganancia", "Precio_Minimo"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    
    df["Costo_por_Kg"] = df["Costo_Total"] / df["Cantidad_Kg"].replace(0, 1)
    
    promedios = df.groupby("Cultivo")["Costo_por_Kg"].mean().reset_index()
    promedios.rename(columns={"Costo_por_Kg": "Promedio_Cultivo"}, inplace=True)
    df = df.merge(promedios, on="Cultivo", how="left")
    df["Eficiencia_%"] = ((df["Costo_por_Kg"] - df["Promedio_Cultivo"]) / df["Promedio_Cultivo"].replace(0, 1)) * 100

    st.subheader("🔎 Análisis por finca")
    finca_sel = st.selectbox("Selecciona una finca para diagnóstico", df["Nombre_Finca"].unique())
    row = df[df["Nombre_Finca"] == finca_sel].iloc[0]
    
    ganancia_f = float(row["Ganancia"])
    eficiencia_f = float(row["Eficiencia_%"])
    precio_v_f = float(row["Precio_Venta"])
    precio_m_f = float(row["Precio_Minimo"])
    temp_f = base_clima.get(row["Departamento"], 20)

    # MÉTRICAS VISUALES
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Costo/Kg", f"${row['Costo_por_Kg']:,.0f}")
    m2.metric("Producción", f"{row['Cantidad_Kg']:,.0f} Kg", f"{row['Cantidad_Kg']/50:.1f} bultos/qq")
    m3.metric("Eficiencia", f"{eficiencia_f:.1f}%", delta_color="inverse")
    m4.metric("Ganancia Est.", f"${ganancia_f:,.0f}")

    # --- COMPARATIVA DE MERCADO (INTELIGENTE) ---
    st.markdown("---")
    st.subheader("⚖️ Comparativa Corabastos vs Tu Finca")
    
    # Función para quitar tildes y limpiar texto
    def limpiar_texto(t):
        import unicodedata
        t = str(t).lower().strip()
        # Esto quita tildes: transforma 'é' en 'e'
        return "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')

    cultivo_usuario = limpiar_texto(row["Cultivo"])
    p_corabastos = 0
    nombre_oficial = ""

    # Buscamos si alguna palabra clave está en lo que escribió el usuario
    for clave, precio in precios_corabastos.items():
        if clave in cultivo_usuario:
            p_corabastos = precio
            nombre_oficial = clave.capitalize()
            break

    if p_corabastos > 0:
        diferencia = p_corabastos - precio_v_f
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Corabastos ({nombre_oficial})", f"${p_corabastos:,.0f}/Kg")
        c2.metric("Tu Precio Venta", f"${precio_v_f:,.0f}/Kg")
        c3.metric("Brecha de Mercado", f"${diferencia:,.0f}/Kg", delta=-diferencia, delta_color="inverse")
        
        if diferencia > 0:
            st.warning(f"⚠️ Estás vendiendo ${diferencia:,.0f} por debajo del mercado.")
        else:
            st.success(f"✅ Tu precio está excelente frente a la central.")
    else:
        st.info(f"🔍 No encontré referencia para '{row['Cultivo']}'. Intenta usar nombres simples como: Cafe, Aguacate, Lulo o Pepino.")

    # --- BLOQUE DE DIAGNÓSTICO Y PLAN DE ACCIÓN ---
    st.markdown("---")
    st.subheader("💡 Recomendación de Consultoría")
    
    if ganancia_f > 0:
        st.success(f"🟢 La finca {finca_sel} es RENTABLE.")
    else:
        st.error(f"🔴 La finca {finca_sel} presenta PÉRDIDA.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Análisis de Costos:**")
        if eficiencia_f <= 0:
            st.info(f"✅ Eficiencia: Costos {abs(eficiencia_f):.1f}% menores al promedio.")
        else:
            st.warning(f"⚠️ Costos: {eficiencia_f:.1f}% superiores al promedio.")

    with col_b:
        st.markdown("**Plan de Acción:**")
        if ganancia_f < 0 and eficiencia_f > 0:
            st.write("👉 **Urgente:** Reduce costos de producción.")
        elif ganancia_f < 0 and eficiencia_f <= 0:
            st.write("👉 **Mercado:** Tu costo es bueno, pero el precio de venta es bajo. Busca venta directa.")
        else:
            st.write("👉 **Escala:** Buen manejo. Podrías aumentar área de siembra.")

# --- MANTENIMIENTO: ELIMINAR REGISTROS ---
st.divider()
st.subheader("🗑️ Zona de Corrección")
if not df_existente.empty:
    df_borrar = df_existente.copy()
    df_borrar["ID_Visual"] = df_borrar["Nombre_Finca"].astype(str) + " - " + df_borrar["Cultivo"].astype(str)
    seleccion = st.selectbox("Selecciona registro para borrar", options=df_borrar["ID_Visual"].unique())
    if st.button("❌ Eliminar Permanentemente"):
        df_nuevo = df_borrar[df_borrar["ID_Visual"] != seleccion].drop(columns=["ID_Visual"])
        sheet.clear()
        sheet.append_row(list(df_nuevo.columns))
        if not df_nuevo.empty:
            sheet.append_rows(df_nuevo.values.tolist())
        st.success("Registro eliminado.")
        st.rerun()
