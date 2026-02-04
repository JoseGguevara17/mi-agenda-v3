import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda Pro 24/7", page_icon="🚀", layout="wide")

# --- 2. MOTOR DE CONEXIÓN ---
# ID de tu Excel (Sacado de tu captura)
SHEET_ID = "1nR83Cu842oXPnQThcYvw0WAXP6Bwnc9Fr2QefdrznFk"

def load_data(sheet_name, default_cols):
    try:
        # Construimos la URL usando el nombre de la pestaña (sheet_name)
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
        # URL de tu Apps Script (la que termina en /exec)
        URL_SCRIPT = "https://script.google.com/macros/s/AKfycbz-aXx79hgZEsAOAE44y2vvAuqx-u0sn9bTPn0doHFHb6bGCOZm6hLorr_A8yWPSYTz/exec"
        
        df_save = df.dropna(how="all").fillna("")
        
        # Convertimos fechas a texto para evitar errores en Google Sheets
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
        else:
            st.error("❌ Error al guardar. Verifica que el Script esté publicado como 'Cualquier persona'.")
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
            else:
                st.error("Contraseña incorrecta")
    st.stop()

# --- 4. CARGA DE DATOS (NOMBRES DE PESTAÑAS INTEGRADOS) ---
cols_deudas = ["Concepto", "Monto", "Tipo", "Persona", "Fecha"]
cols_reuniones = ["Asunto", "Fecha", "Hora", "Link", "Notas"]
cols_tareas = ["Tarea", "Prioridad", "Fecha Limite", "Completado"]

# Cargamos cada pestaña por su nombre exacto
df_deudas = load_data("deudas", cols_deudas)
df_reuniones = load_data("reuniones", cols_reuniones)
df_tareas = load_data("tareas", cols_tareas)

# --- 5. INTERFAZ Y DASHBOARD ---
st.title("🚀 Panel de Control Personal")

# Métricas para que se vea profesional
c1, c2 = st.columns(2)
with c1:
    # Evita error si la columna Monto no es numérica todavía
    monto_total = pd.to_numeric(df_deudas["Monto"], errors='coerce').sum()
    st.metric("Deudas Registradas", f"${monto_total:,.2f}")
with c2:
    # Verificamos si existe la columna para no dar KeyError
    if "Completado" in df_tareas.columns:
        pendientes = len(df_tareas[df_tareas["Completado"] == False])
        st.metric("Tareas Pendientes", pendientes)

st.divider()

# Pestañas de navegación
t1, t2, t3 = st.tabs(["💰 Deudas", "✅ Tareas", "🎥 Reuniones"])

with t1:
    st.subheader("Control de Deudas")
    ed_deudas = st.data_editor(df_deudas, num_rows="dynamic", use_container_width=True, key="edit_deudas")
    if st.button("Guardar Deudas", key="sv_deudas"):
        save_data(ed_deudas, "deudas")

with t2:
    st.subheader("Lista de Tareas")
    ed_tareas = st.data_editor(df_tareas, num_rows="dynamic", use_container_width=True, key="edit_tareas")
    if st.button("Guardar Tareas", key="sv_tareas"):
        save_data(ed_tareas, "tareas")

with t3:
    st.subheader("Calendario de Reuniones")
    ed_reuniones = st.data_editor(df_reuniones, num_rows="dynamic", use_container_width=True, key="edit_reuniones")
    if st.button("Guardar Reuniones", key="sv_reuniones"):
        save_data(ed_reuniones, "reuniones")
