import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda Pro 24/7", page_icon="🚀", layout="wide")

# --- 2. MOTOR DE CONEXIÓN ---
SHEET_ID = "1nR83Cu842oXPnQThcYvw0WAXP6Bwnc9Fr2QefdrznFk"

def load_data(sheet_name, default_cols):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        if df.empty:
            return pd.DataFrame(columns=default_cols)
        return df
    except Exception:
        return pd.DataFrame(columns=default_cols)

def save_data(df, sheet_name):
    try:
        URL_SCRIPT = "https://script.google.com/macros/s/AKfycbz-aXx79hgZEsAOAE44y2vvAuqx-u0sn9bTPn0doHFHb6bGCOZm6hLorr_A8yWPSYTz/exec"
        df_save = df.dropna(how="all").fillna("")
        for col in df_save.columns:
            if "fecha" in col.lower() or "limite" in col.lower():
                df_save[col] = df_save[col].astype(str)
        data_list = df_save.values.tolist()
        payload = {"sheet": sheet_name, "data": data_list}
        response = requests.post(URL_SCRIPT, json=payload)
        if response.status_code == 200:
            st.success(f"✅ ¡Pestaña '{sheet_name}' actualizada!")
            st.cache_data.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Error crítico: {e}")

# --- 3. LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Acceso Agenda")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Entrar", use_container_width=True):
            if pw == "admin123":
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- 4. CARGA DE DATOS ---
cols_deudas = ["Concepto", "Monto", "Tipo", "Persona", "Fecha"]
cols_reuniones = ["Asunto", "Fecha", "Hora", "Link", "Notas"]
cols_tareas = ["Tarea", "Prioridad", "Fecha Limite", "Completado"]

df_deudas = load_data("deudas", cols_deudas)
df_reuniones = load_data("reuniones", cols_reuniones)
df_tareas = load_data("tareas", cols_tareas)

# --- 5. INTERFAZ PRINCIPAL ---
st.title("📅 Mi Agenda Personal 24/7")
st.divider()

# Creamos dos columnas: Izquierda (Atajo/Calendario) y Derecha (Editores)
col_guia, col_editores = st.columns([1, 2], gap="large")

# --- COLUMNA IZQUIERDA: TU GUÍA DE REUNIONES ---
with col_guia:
    st.subheader("🗓️ Atajo de Reuniones")
    sel_date = st.date_input("Ver agenda del día:", value=date.today())
    
    # Filtramos las reuniones del día seleccionado
    if not df_reuniones.empty and 'Fecha' in df_reuniones.columns:
        day_reunions = df_reuniones[df_reuniones['Fecha'].astype(str) == str(sel_date)]
        
        if not day_reunions.empty:
            for _, r in day_reunions.iterrows():
                with st.expander(f"⏰ {r.get('Hora', '00:00')} - {r.get('Asunto', 'Reunión')}", expanded=True):
                    st.write(f"**Notas:** {r.get('Notas', 'Sin notas')}")
                    if r.get('Link') and "http" in str(r['Link']):
                        st.link_button("🔗 Abrir Enlace", r['Link'], use_container_width=True)
        else:
            st.info("No hay reuniones para este día.")
    else:
        st.warning("No se encontraron datos en la pestaña 'reuniones'.")

# --- COLUMNA DERECHA: GESTIÓN (TABS) ---
with col_editores:
    tab1, tab2, tab3 = st.tabs(["💰 Deudas", "✅ Tareas", "🎥 Config. Reuniones"])
    
    with tab1:
        st.write("### 💰 Control de Deudas")
        ed_deudas = st.data_editor(df_deudas, num_rows="dynamic", use_container_width=True, key="ed_deudas")
        if st.button("Guardar Deudas", key="sv_d"):
            save_data(ed_deudas, "deudas")

    with tab2:
        st.write("### ✅ Lista de Tareas")
        ed_tareas = st.data_editor(df_tareas, num_rows="dynamic", use_container_width=True, key="ed_tareas")
        if st.button("Guardar Tareas", key="sv_t"):
            save_data(ed_tareas, "tareas")

    with tab3:
        st.write("### 🎥 Editar Base de Reuniones")
        st.caption("Agrega o modifica aquí para que aparezcan en el calendario de la izquierda.")
        ed_reuniones = st.data_editor(df_reuniones, num_rows="dynamic", use_container_width=True, key="ed_reuniones")
        if st.button("Guardar Reuniones", key="sv_r"):
            save_data(ed_reuniones, "reuniones")
