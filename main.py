import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Agenda Pro 24/7", page_icon="🚀", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    return conn.read(worksheet=sheet_name)

def save_data(df, sheet_name):
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear()

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Acceso")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if pw == "admin123":
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- Cargar datos ---
df_deudas = load_data("deudas")
df_reuniones = load_data("reuniones")
df_tareas = load_data("tareas")

# --- INTERFAZ (Tu diseño profesional) ---
st.title("📅 Mi Agenda Profesional 24/7")

col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.subheader("🗓️ Calendario")
    sel_date = st.date_input("Selecciona un día", value=date.today())
    
    # 3. Verificación de seguridad para evitar el NameError
    if 'df_reuniones' in locals():
        day_reunions = df_reuniones[df_reuniones['Fecha'].astype(str) == str(sel_date)]
        if not day_reunions.empty:
            for _, r in day_reunions.iterrows():
                # Usamos .get() por si la columna se llama 'Asunto' o 'Título'
                asunto = r.get('Asunto', r.get('Título', 'Sin asunto'))
                st.success(f"⏰ {r.get('Hora', '00:00')} - {asunto}")
        else:
            st.info("No hay eventos para hoy.")

with col_right:
    # Banner de Deuda
    total_deuda = pd.to_numeric(df_deudas[df_deudas["Tipo"]=="Debo"]["Monto"], errors='coerce').sum()
    st.markdown(f"""
        <div style="background-color:#ff4b4b;padding:20px;border-radius:10px;color:white;text-align:center;">
            <h2 style="color:white;">💸 Deuda Total Pendiente</h2>
            <h1 style="color:white;font-size:3.5em;">${total_deuda:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("📋 Registro de Deudas")
    # Editor de datos que guarda en Google Sheets
    ed_deudas = st.data_editor(df_deudas, num_rows="dynamic", use_container_width=True)
    if st.button("Guardar Cambios en Deudas"):
        save_data(ed_deudas, "deudas")

        st.toast("¡Datos guardados en Google Sheets!")




