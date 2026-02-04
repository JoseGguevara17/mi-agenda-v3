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
        return df
    except Exception:
        return pd.DataFrame(columns=default_cols)

def save_data(df, sheet_name):
    try:
        URL_SCRIPT = "https://script.google.com/macros/s/AKfycbz-aXx79hgZEsAOAE44y2vvAuqx-u0sn9bTPn0doHFHb6bGCOZm6hLorr_A8yWPSYTz/exec"
        df_save = df.dropna(how="all").fillna("")
        # Formatear fechas antes de enviar a Google para evitar errores
        for col in df_save.columns:
            if "fecha" in col.lower() or "limite" in col.lower():
                df_save[col] = pd.to_datetime(df_save[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna("")
        
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

# --- BANNER DE MÉTRICAS (LO QUE PEDISTE) ---
m1, m2, m3 = st.columns(3)
with m1:
    total_deuda = pd.to_numeric(df_deudas["Monto"], errors='coerce').sum()
    st.metric("💰 Deuda Total", f"${total_deuda:,.2f}")
with m2:
    if "Completado" in df_tareas.columns:
        pendientes = len(df_tareas[df_tareas["Completado"].isin([False, "False", 0])])
        st.metric("✅ Tareas Pendientes", pendientes)
with m3:
    hoy_str = str(date.today())
    reuniones_hoy = len(df_reuniones[df_reuniones["Fecha"].astype(str) == hoy_str])
    st.metric("🎥 Eventos Hoy", reuniones_hoy)

st.divider()

col_guia, col_editores = st.columns([1, 2], gap="large")

# --- COLUMNA IZQUIERDA: GUÍA/CALENDARIO ---
with col_guia:
    st.subheader("🗓️ Agenda del Día")
    sel_date = st.date_input("Selecciona fecha:", value=date.today())
    
    day_reunions = df_reuniones[df_reuniones['Fecha'].astype(str) == str(sel_date)]
    if not day_reunions.empty:
        for _, r in day_reunions.iterrows():
            with st.expander(f"⏰ {r.get('Hora', '00:00')} - {r.get('Asunto', 'Evento')}"):
                st.write(f"**Notas:** {r.get('Notas', '')}")
                if r.get('Link') and "http" in str(r['Link']):
                    st.link_button("Ir a la reunión", r['Link'], use_container_width=True)
    else:
        st.info("No hay compromisos para esta fecha.")

# --- COLUMNA DERECHA: GESTIÓN CON FORMATOS AVANZADOS ---
with col_editores:
    tab1, tab2, tab3 = st.tabs(["💰 Deudas", "✅ Tareas", "🎥 Config. Reuniones"])
    
    with tab1:
        st.write("### Control de Deudas")
        ed_deudas = st.data_editor(
            df_deudas, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="ed_deudas",
            column_config={
                "Monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Debo", "Me deben", "Pagado"]),
                "Fecha": st.column_config.DateColumn("Fecha")
            }
        )
        if st.button("Guardar Deudas", key="sv_d"):
            save_data(ed_deudas, "deudas")

    with tab2:
        st.write("### Lista de Tareas")
        ed_tareas = st.data_editor(
            df_tareas, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="ed_tareas",
            column_config={
                "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Alta", "Media", "Baja"]),
                "Fecha Limite": st.column_config.DateColumn("Fecha Limite"),
                "Completado": st.column_config.CheckboxColumn("¿Listo?")
            }
        )
        if st.button("Guardar Tareas", key="sv_t"):
            save_data(ed_tareas, "tareas")

    with tab3:
        st.write("### Base de Reuniones")
        ed_reuniones = st.data_editor(
            df_reuniones, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="ed_reuniones",
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha"),
                "Hora": st.column_config.TimeColumn("Hora")
            }
        )
        if st.button("Guardar Reuniones", key="sv_r"):
            save_data(ed_reuniones, "reuniones")
