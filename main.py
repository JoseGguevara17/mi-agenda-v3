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
        
        # Formatear fechas antes de enviar para que Google Sheets las entienda siempre
        for col in df_save.columns:
            if any(key in col.lower() for key in ["fecha", "limite"]):
                df_save[col] = pd.to_datetime(df_save[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna("")
        
        data_list = df_save.values.tolist()
        payload = {"sheet": sheet_name, "data": data_list}
        response = requests.post(URL_SCRIPT, json=payload)
        
        if response.status_code == 200:
            st.success(f"✅ ¡{sheet_name.capitalize()} actualizado!")
            st.cache_data.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- 3. LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col_log1, col_log2, col_log3 = st.columns([1,2,1])
    with col_log2:
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

# --- 5. INTERFAZ: BANNER DE MÉTRICAS ---
st.title("📅 Mi Agenda Personal 24/7")

# Banner superior (KPIs)
with st.container():
    m1, m2, m3 = st.columns(3)
    # Cálculo de métricas con validación para evitar el error 'KeyError'
    val_deuda = pd.to_numeric(df_deudas["Monto"], errors='coerce').sum() if "Monto" in df_deudas.columns else 0
    m1.metric("💰 Deuda Total", f"${val_deuda:,.2f}")
    
    val_tareas = len(df_tareas[df_tareas["Completado"].isin([False, 0, "False"])]) if "Completado" in df_tareas.columns else 0
    m2.metric("✅ Tareas Pendientes", val_tareas)
    
    val_hoy = len(df_reuniones[df_reuniones["Fecha"].astype(str) == str(date.today())]) if "Fecha" in df_reuniones.columns else 0
    m3.metric("🎥 Eventos Hoy", val_hoy)

st.divider()

# --- 6. CUERPO DE LA APP (CALENDARIO + EDITORES) ---
col_guia, col_editores = st.columns([1, 2], gap="large")

with col_guia:
    st.subheader("🗓️ Agenda Diaria")
    sel_date = st.date_input("Consultar fecha:", value=date.today())
    
    reuniones_dia = df_reuniones[df_reuniones['Fecha'].astype(str) == str(sel_date)] if "Fecha" in df_reuniones.columns else pd.DataFrame()
    
    if not reuniones_dia.empty:
        for _, r in reuniones_dia.iterrows():
            with st.expander(f"⏰ {r.get('Hora','--:--')} - {r.get('Asunto','Evento')}"):
                st.write(f"**Notas:** {r.get('Notas','')}")
                link = r.get('Link', '')
                if pd.notnull(link) and "http" in str(link):
                    st.link_button("🔗 Abrir Reunión", str(link), use_container_width=True)
    else:
        st.info("Sin compromisos.")

with col_editores:
    tab_d, tab_t, tab_r = st.tabs(["💰 Deudas", "✅ Tareas", "🎥 Config. Reuniones"])
    
    with tab_d:
        st.write("### 💰 Control de Dinero")
        ed_deudas = st.data_editor(
            df_deudas, num_rows="dynamic", use_container_width=True, key="ed_d",
            column_config={
                "Monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Debo", "Me deben", "Pagado"]),
                "Fecha": st.column_config.DateColumn("Fecha")
            }
        )
        if st.button("Guardar Deudas", key="btn_sd"): save_data(ed_deudas, "deudas")

    with tab_t:
        st.write("### ✅ Lista de Tareas")
        ed_tareas = st.data_editor(
            df_tareas, num_rows="dynamic", use_container_width=True, key="ed_t",
            column_config={
                "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Alta", "Media", "Baja"]),
                "Fecha Limite": st.column_config.DateColumn("Fecha Limite"),
                "Completado": st.column_config.CheckboxColumn("¿Listo?")
            }
        )
        if st.button("Guardar Tareas", key="btn_st"): save_data(ed_tareas, "tareas")

    with tab_r:
        st.write("### 🎥 Configuración de Reuniones")
        ed_reuniones = st.data_editor(
            df_reuniones, num_rows="dynamic", use_container_width=True, key="ed_r",
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha"),
                "Hora": st.column_config.TimeColumn("Hora")
            }
        )
        if st.button("Guardar Reuniones", key="btn_sr"): save_data(ed_reuniones, "reuniones")
