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
        # 1. ASEGÚRATE QUE ESTA URL TERMINE EN /exec
        URL_SCRIPT = "https://script.google.com/macros/s/AKfycbx3apgbRy4I_Wzx5OMJb3Wv1xcQXeDa3RqNUYxi41bkeauA0BeoWNH6AuPVFU7VywNo/exec" 
        
       # 2. Preparación de datos
        df_save = df.dropna(how="all").fillna("")
        data_list = df_save.values.tolist()
        payload = {"sheet": sheet_name, "data": data_list}
        
        # 3. Envío de datos
        with st.spinner('Guardando datos en la nube...'):
            response = requests.post(URL_SCRIPT, json=payload, timeout=15)
        
        # 4. Verificación de éxito 
        if response.status_code == 200:
            st.success(f"✅ ¡{sheet_name.capitalize()} actualizado con éxito!")
            # IMPORTANTE: Limpiamos la memoria para que el BANNER se actualice
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"Error del servidor: {response.status_code}")

    except Exception as e:
        st.error(f"Error de conexión: {e}")

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

df_deudas = load_data("deudas", cols_deudas).fillna("")
df_reuniones = load_data("reuniones", cols_reuniones).fillna("")
df_tareas = load_data("tareas", cols_tareas).fillna("")

# --- 5. INTERFAZ: BANNER DE MÉTRICAS (Versión Blindada) ---
st.title("📅 Mi Agenda Personal 24/7")

with st.container():
    m1, m2, m3 = st.columns(3)
    
    
    # ✅ TAREAS PENDIENTES (Suma y resta dinámica)
    val_tareas = 0
    if not df_tareas.empty:
        col_t = [c for c in df_tareas.columns if c.lower() == 'tarea']
        col_c = [c for c in df_tareas.columns if c.lower() == 'completado']
        if col_t and col_c:
            # Filtramos: que la tarea tenga texto Y que NO esté marcada como True
            pendientes = df_tareas[
                (df_tareas[col_t[0]].fillna("").astype(str).str.strip() != "") & 
                (df_tareas[col_c[0]].astype(str).str.lower() != "true")
            ]
            val_tareas = len(pendientes)
    m2.metric("✅ Tareas Pendientes", val_tareas)
    
    # 🎥 EVENTOS HOY (Reconocimiento de formato 13/2/2026)
    val_hoy = 0
    if not df_reuniones.empty:
        col_f = [c for c in df_reuniones.columns if c.lower() == 'fecha']
        if col_f:
            f_guiones = date.today().strftime('%Y-%m-%d')
            f_barras = date.today().strftime('%d/%m/%Y').replace('/0', '/')
            
            eventos_hoy = df_reuniones[
                (df_reuniones[col_f[0]].astype(str).str.contains(f_guiones, na=False)) |
                (df_reuniones[col_f[0]].astype(str).str.contains(f_barras, na=False))
            ]
            val_hoy = len(eventos_hoy)
    m3.metric("🎥 Eventos Hoy", val_hoy)
    
# --- 6. CUERPO DE LA APP (CALENDARIO + EDITORES) ---
col_guia, col_editores = st.columns([1, 2], gap="large")

# --- En la sección de col_guia ---
with col_guia:
    st.subheader("🗓️ Agenda Diaria")
    sel_date = st.date_input("Consultar fecha:", value=date.today())
    
    # --- Reemplazo de líneas 120-121 ---
    # Creamos dos formatos: uno con guiones (2026-02-13) y otro con barras (13/2/2026)
    f_guiones = str(sel_date)
    f_barras = sel_date.strftime('%d/%m/%Y').replace('/0', '/')

    # Filtramos la tabla buscando AMBOS formatos para que el banner y la lista funcionen
    reuniones_dia = df_reuniones[
        (df_reuniones['Fecha'].astype(str).str.contains(f_guiones, na=False)) |
        (df_reuniones['Fecha'].astype(str).str.contains(f_barras, na=False))
    ] if "Fecha" in df_reuniones.columns else pd.DataFrame()
    
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
                "Fecha": st.column_config.TextColumn("Fecha") # TextColumn evita el error
            }
        )
        if st.button("Guardar Deudas", key="btn_sd"): save_data(ed_deudas, "deudas")

    with tab_t:
        st.write("### ✅ Lista de Tareas")
        ed_tareas = st.data_editor(
            df_tareas, num_rows="dynamic", use_container_width=True, key="ed_t",
            column_config={
                "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Alta", "Media", "Baja"]),
                "Fecha Limite": st.column_config.TextColumn("Fecha Limite"), # TextColumn evita el error
                "Completado": st.column_config.CheckboxColumn("¿Listo?")
            }
        )
        if st.button("Guardar Tareas", key="btn_st"): save_data(ed_tareas, "tareas")

    with tab_r:
        st.write("### 🎥 Configuración de Reuniones")
        ed_reuniones = st.data_editor(
            df_reuniones, num_rows="dynamic", use_container_width=True, key="ed_r",
            column_config={
                "Fecha": st.column_config.TextColumn("Fecha"), # TextColumn evita el error
                "Hora": st.column_config.TextColumn("Hora")
            }
        )
        if st.button("Guardar Reuniones", key="btn_sr"): save_data(ed_reuniones, "reuniones")












