import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda Pro 24/7", page_icon="🚀", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name, default_cols):
    try:
        # ttl="0" para asegurar que siempre traiga datos frescos al recargar
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=default_cols)
        return df
    except Exception:
        return pd.DataFrame(columns=default_cols)

def save_data(df, sheet_name):
    try:
        # Limpieza: eliminamos filas vacías y convertimos fechas a texto para Sheets
        df_save = df.dropna(how="all").copy()
        for col in df_save.columns:
            if pd.api.types.is_datetime64_any_dtype(df_save[col]):
                df_save[col] = df_save[col].dt.strftime('%Y-%m-%d')
        
        conn.update(worksheet=sheet_name, data=df_save)
        st.cache_data.clear()
        st.success(f"¡Datos de {sheet_name} actualizados!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar en {sheet_name}: {e}")

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Acceso Agenda")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if pw == "admin123":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

# --- DEFINICIÓN DE COLUMNAS (Basado en tu Sheets) ---
cols_deudas = ["Concepto", "Monto", "Tipo", "Persona", "Fecha"]
cols_reuniones = ["Asunto", "Fecha", "Hora", "Link", "Notas"]
cols_tareas = ["Tarea", "Prioridad", "Fecha Limite", "Completado"]

# Carga de datos
df_deudas = load_data("deudas", cols_deudas)
df_reuniones = load_data("reuniones", cols_reuniones)
df_tareas = load_data("tareas", cols_tareas)

with st.sidebar:
    st.title("⚙️ Opciones")
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("📅 Agenda Personal 24/7")
st.divider()

col_left, col_right = st.columns([1, 2], gap="large")

# --- COLUMNA IZQUIERDA: CALENDARIO ---
with col_left:
    st.subheader("🗓️ Eventos del Día")
    sel_date = st.date_input("Ver agenda del día:", value=date.today())
    
    if not df_reuniones.empty and 'Fecha' in df_reuniones.columns:
        # Filtramos asegurando que ambos sean strings para comparar
        day_reunions = df_reuniones[df_reuniones['Fecha'].astype(str) == str(sel_date)]
        if not day_reunions.empty:
            for _, r in day_reunions.iterrows():
                st.info(f"⏰ **{r.get('Hora', '00:00')}** - {r.get('Asunto', 'Sin título')}")
                if r.get('Link') and r['Link'] != "":
                    st.link_button("Ir a la reunión", r['Link'])
        else:
            st.write("No tienes eventos programados.")
    else:
        st.info("La hoja de reuniones está vacía.")

# --- COLUMNA DERECHA: GESTIÓN ---
with col_right:
    # BANNER DE DEUDAS
    monto_valido = pd.to_numeric(df_deudas["Monto"], errors='coerce').fillna(0)
    total_deuda = monto_valido[df_deudas["Tipo"] == "Debo"].sum()
    
    st.markdown(f"""
        <div style="background-color:#ff4b4b;padding:20px;border-radius:10px;color:white;text-align:center;margin-bottom:20px;">
            <h2 style="color:white;margin:0;">💸 Deuda Total Pendiente</h2>
            <h1 style="color:white;font-size:3em;margin:0;">${total_deuda:,.2f}</h1>
        </div>
    """, unsafe_allow_html=True)

    # EDITOR DE DEUDAS
    with st.expander("💰 Gestionar Deudas", expanded=True):
        ed_deudas = st.data_editor(
            df_deudas, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Debo", "Me deben", "Pagado"], required=True),
                "Monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
                "Fecha": st.column_config.DateColumn("Fecha")
            }
        )
        if st.button("Guardar Deudas"):
            save_data(ed_deudas, "deudas")

    # EDITOR DE TAREAS
    with st.expander("✅ Lista de Tareas", expanded=True):
        ed_tareas = st.data_editor(
            df_tareas,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Alta", "Media", "Baja"]),
                "Fecha Limite": st.column_config.DateColumn("Fecha Limite"),
                "Completado": st.column_config.CheckboxColumn("¿Listo?")
            }
        )
        if st.button("Guardar Tareas"):
            save_data(ed_tareas, "tareas")

    # EDITOR DE REUNIONES (Para agregar nuevas)
    with st.expander("🎥 Programar Reuniones"):
        ed_reuniones = st.data_editor(
            df_reuniones,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha"),
                "Hora": st.column_config.TimeColumn("Hora")
            }
        )
        if st.button("Guardar Reuniones"):
            save_data(ed_reuniones, "reuniones")




