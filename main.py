import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda Pro 24/7", page_icon="🚀", layout="wide")

# --- 2. MOTOR DE CONEXIÓN (Apps Script) ---
# Tu ID de hoja ya está aquí basado en tus capturas
SHEET_ID = "AKfycbz-aXx79hgZEsAOAE44y2vvAuqx-u0sn9bTPn0doHFHb6bCGOZm6hLorr_A8yWPSYtz"

def load_data(sheet_name, default_cols):
    try:
        # Lectura rápida vía CSV público
        url = f"https://docs.google.com/spreadsheets/d/AKfycbz-aXx79hgZEsAOAE44y2vvAuqx-u0sn9bTPn0doHFHb6bCGOZm6hLorr_A8yWPSYtz/gviz/tq?tqx=out:csv&sheet=Base_Datos_Agenda"
        df = pd.read_csv(url)
        # Limpiar nombres de columnas por si acaso
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame(columns=default_cols)

def save_data(df, sheet_name):
    try:
        # --- PEGA AQUÍ TU URL DE GOOGLE APPS SCRIPT ---
        URL_SCRIPT = "https://script.google.com/macros/s/AKfycbz-aXx79hgZEsAOAE44y2vvAuqx-u0sn9bTPn0doHFHb6bCGOZm6hLorr_A8yWPSYtz/exec"
        
        if URL_SCRIPT == "https://script.google.com/macros/s/AKfycbz-aXx79hgZEsAOAE44y2vvAuqx-u0sn9bTPn0doHFHb6bCGOZm6hLorr_A8yWPSYtz/exec":
            st.error("⚠️ Falta pegar la URL del Apps Script en el código.")
            return

        # Limpieza de datos
        df_save = df.dropna(how="all").fillna("")
        
        # Convertir fechas a texto para que Google no las corrompa
        for col in df_save.columns:
            if "fecha" in col.lower() or "limite" in col.lower():
                df_save[col] = df_save[col].astype(str)

        data_list = df_save.values.tolist()
        payload = {"sheet": sheet_name, "data": data_list}
        
        response = requests.post(URL_SCRIPT, json=payload)
        
        if response.status_code == 200:
            st.success(f"✅ ¡{sheet_name.capitalize()} guardado con éxito!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("❌ Error de servidor al guardar.")
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

# --- 4. CARGA DE DATOS ---
cols_deudas = ["Concepto", "Monto", "Tipo", "Persona", "Fecha"]
cols_reuniones = ["Asunto", "Fecha", "Hora", "Link", "Notas"]
cols_tareas = ["Tarea", "Prioridad", "Fecha Limite", "Completado"]

df_deudas = load_data("deudas", cols_deudas)
df_reuniones = load_data("reuniones", cols_reuniones)
df_tareas = load_data("tareas", cols_tareas)

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🚀 Panel de Control Personal")
st.caption(f"Hoy es: {date.today().strftime('%A, %d de %B %Y')}")

# Métricas de resumen (Le da el toque profesional)
m1, m2, m3 = st.columns(3)
with m1:
    total_deuda = pd.to_numeric(df_deudas[df_deudas["Tipo"]=="Debo"]["Monto"], errors='coerce').sum()
    st.metric("Deuda Total", f"${total_deuda:,.2f}")
with m2:
    pendientes = len(df_tareas[df_tareas["Completado"] == False])
    st.metric("Tareas Pendientes", pendientes)
with m3:
    reuniones_hoy = len(df_reuniones[df_reuniones["Fecha"].astype(str) == str(date.today())])
    st.metric("Eventos hoy", reuniones_hoy)

st.divider()

col_left, col_right = st.columns([1, 2], gap="large")

# --- COLUMNA IZQUIERDA: CALENDARIO ---
with col_left:
    with st.container(border=True):
        st.subheader("🗓️ Agenda del Día")
        sel_date = st.date_input("Selecciona fecha:", value=date.today())
        
        day_reunions = df_reuniones[df_reuniones['Fecha'].astype(str) == str(sel_date)]
        if not day_reunions.empty:
            for _, r in day_reunions.iterrows():
                st.info(f"**{r['Hora']}** - {r['Asunto']}")
                if r.get('Link') and "http" in str(r['Link']):
                    st.link_button("🔗 Unirse", r['Link'], use_container_width=True)
        else:
            st.write("Libre de compromisos.")

# --- COLUMNA DERECHA: GESTIÓN POR PESTAÑAS ---
with col_right:
    tab_deudas, tab_tareas, tab_reuniones = st.tabs(["💰 Deudas", "✅ Tareas", "🎥 Config. Reuniones"])
    
    with tab_deudas:
        st.write("### Registro Financiero")
        ed_deudas = st.data_editor(df_deudas, num_rows="dynamic", use_container_width=True, key="ed_deudas")
        if st.button("Guardar Cambios en Deudas", key="btn_d"):
            save_data(ed_deudas, "deudas")

    with tab_tareas:
        st.write("### Lista de Pendientes")
        ed_tareas = st.data_editor(df_tareas, num_rows="dynamic", use_container_width=True, key="ed_tareas")
        if st.button("Guardar Cambios en Tareas", key="btn_t"):
            save_data(ed_tareas, "tareas")

    with tab_reuniones:
        st.write("### Base de Datos de Reuniones")
        ed_reuniones = st.data_editor(df_reuniones, num_rows="dynamic", use_container_width=True, key="ed_r")
        if st.button("Guardar Cambios en Reuniones", key="btn_r"):
            save_data(ed_reuniones, "reuniones")

with st.sidebar:
    st.title("⚙️ Sistema")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.auth = False
        st.rerun()
