import base64
import pandas as pd
import streamlit as st

# ==============================================================================
# PARTE 1: CONFIGURACIÓN E INICIALIZACIÓN DE SESIÓN
# ==============================================================================
st.set_page_config(
    page_title="Portal de Grabaciones",
    page_icon="🔒",
    layout="wide"
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "student_code" not in st.session_state:
    st.session_state.student_code = None

# URL de exportación directa de tu Google Sheet
SPREADSHEET_ID = "2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP/pub?output=csv"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP/pub?output=csv"


# ==============================================================================
# PARTE 2: CARGA Y LIMPIEZA ULTRA-ESTRICTA DE DATOS
# ==============================================================================
@st.cache_data(ttl=2)  # Actualización rápida de datos
def cargar_y_limpiar_datos():
    try:
        df = pd.read_csv(URL_SHEET)
        # Limpieza automática de columnas fantasma (evita errores 'nan')
        columnas_validas = [col for col in df.columns if pd.notna(col) and not str(col).startswith('Unnamed:')]
        df = df[columnas_validas]
        
        if 'IDE' in df.columns:
            df['IDE'] = df['IDE'].astype(str).str.strip()
            
        return df
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return None

df_source = cargar_y_limpiar_datos()


# ==============================================================================
# PARTE 3: PROCESADOR DE AUDIO COMPATIBLE (ACTIVA PISTAS CAÍDAS)
# ==============================================================================
def procesar_evidencia_audio(audio_data, file_index):
    """Procesa el audio, activa el reproductor y genera el botón de descarga."""
    if not isinstance(audio_data, str) or not audio_data.strip():
        st.warning("⚠️ No hay archivo de audio registrado para este registro.")
        return

    # Caso A: Si es un enlace directo de Web o Google Drive
    if audio_data.startswith("http://") or audio_data.startswith("https://"):
        st.audio(audio_data)
        st.markdown(f'<a href="{audio_data}" target="_blank"><button style="width:100%; padding:10px; background-color:#2e7d32; color:white; border:none; border-radius:5px; cursor:pointer;">📥 Descargar Archivo desde Enlace</button></a>', unsafe_allow_html=True)
    
    # Caso B: Si es una cadena Base64 (Reparación de pista inactiva)
    else:
        try:
            # Sanitización absoluta de la cadena
            clean_b64 = audio_data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",")[-1]
            
            # Re-ajuste estricto de múltiplos de 4 (Corrige error de longitud)
            clean_b64 = clean_b64.rstrip('=')
            modulo = len(clean_b64) % 4
            if modulo > 0:
                clean_b64 += "=" * (4 - modulo)
            
            # Decodificación a bytes binarios puros
            audio_bytes = base64.b64decode(clean_b64)
            
            # 1. REPRODUCTOR COMPATIBLE: Forzamos la reproducción directa inyectando el componente
            st.audio(audio_bytes, format='audio/wav')
            
            # 2. BOTÓN DE DESCARGA: Permite descargar localmente la evidencia de audio
            st.download_button(
                label="📥 Descargar Grabación (WAV)",
                data=audio_bytes,
                file_name=f"grabacion_estudiante_{st.session_state.student_code}_{file_index}.wav",
                mime="audio/wav",
                key=f"btn_dl_{file_index}",
                use_container_width=True
            )
        except Exception:
            st.error("❌ La pista está inactiva porque el texto Base64 superó los 50k caracteres en Google Sheets y se guardó incompleto.")


# ==============================================================================
# PARTE 4: VENTANA POPUP DE AUTENTICACIÓN (LOGIN)
# ==============================================================================
@st.dialog("🔒 Autenticación de Acceso")
def popup_login():
    st.write("Ingresa tu código de estudiante para verificar tus registros en la base de datos.")
    input_code = st.text_input("Código de Estudiante (IDE):", type="password").strip()
    
    if st.button("Verificar Identidad", type="primary", use_container_width=True):
        if df_source is not None and 'IDE' in df_source.columns:
            if input_code in df_source['IDE'].values:
                st.session_state.authenticated = True
                st.session_state.student_code = input_code
                st.success("¡Acceso concedido! Cargando panel seguro...")
                st.rerun()
            else:
                st.error("❌ Código inválido. Verifica los caracteres o contacta al administrador.")
        else:
            st.error("Error del sistema. No se pudo verificar la base de datos de Google Sheets.")


# ==============================================================================
# PARTE 5: CONTROL DE ACCESO GENERAL RESTRINGIDO
# ==============================================================================
if not st.session_state.authenticated:
    st.info("👋 Bienvenido al Sistema de Evidencias de Audio.")
    st.markdown("### Acceso Restringido")
    st.write("Para ver y descargar tus archivos de audio, por favor abre la terminal de seguridad.")
    
    if st.button("🔐 Iniciar Sesión con mi Código", type="primary"):
        popup_login()
    st.stop()


# ==============================================================================
# PARTE 6: PANEL PRINCIPAL CON BOTÓN DE SALIDA (LOGOUT)
# ==============================================================================
with col_salir:
    # BOTÓN PARA SALIR / ABANDONAR LA PÁGINA (Con una clave única y segura)
    if st.button("❌ Salir / Terminar", key="main_logout_unique_key", type="danger", use_container_width=True):
        cerrar_sesion()


# --- BARRA LATERAL (Sidebar) ---
st.sidebar.markdown(f"### 👤 Perfil Activo")
st.sidebar.info(f"**Estudiante:** `{st.session_state.student_code}`")
if st.sidebar.button("🚪 Salir de la Aplicación", key="sidebar_logout", type="secondary"):
    cerrar_sesion()

# --- PANEL CENTRAL PRINCIPAL ---
# Filtrar registros que pertenezcan únicamente al código autenticado
registros_estudiante = df_source[df_source['IDE'] == st.session_state.student_code]

# Encabezado principal con botón de Salida Destacado
col_titulo, col_salir = st.columns([4, 1])
with col_titulo:
    st.success(f"🔓 Sesión segura para el código: **{st.session_state.student_code}**")
with col_salir:
    # BOTÓN PARA SALIR / ABANDONAR LA PÁGINA SI SE DESEA
    if st.button("❌ Salir / Terminar", key="main_logout", type="danger", use_container_width=True):
        cerrar_sesion()

st.markdown(f"### 🎧 Tus Grabaciones de Audio ({len(registros_estudiante)} encontradas)")
st.markdown("A continuación se enlistan tus evidencias. Puedes reproducirlas directamente o descargarlas usando el botón correspondiente.")
st.markdown("---")

if not registros_estudiante.empty and 'Subir evidencias' in registros_estudiante.columns:
    for index, row in registros_estudiante.iterrows():
        fecha = row['Fecha'] if 'Fecha' in row else "No registrada"
        fase = row['Fase'] if 'Fase' in row else "No definida"
        
        with st.container(border=True):
            col_meta, col_media = st.columns([1, 1])
            
            with col_meta:
                st.markdown(f"##### 📋 Grabación Registro N° {index}")
                st.write(f"📅 **Fecha de Envío:** {fecha}")
                st.write(f"🎯 **Fase Actual:** {fase}")
                if 'Enlace Sitio Web' in row and pd.notna(row['Enlace Sitio Web']):
                    st.markdown(f"🔗 [Ver Sitio Web Relacionado]({row['Enlace Sitio Web']})")
            
            with col_media:
                st.markdown("**Controles de Audio y Descarga:**")
                # Llama a la función que fuerza la reproducción y dibuja el botón de descarga
                procesar_evidencia_audio(row['Subir evidencias'], index)
else:
    st.info("No se encontraron archivos multimedia vinculados a tu código de estudiante.")
