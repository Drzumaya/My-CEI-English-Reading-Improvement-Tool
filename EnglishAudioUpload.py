import base64
import pandas as pd
import streamlit as st

# ==============================================================================
# PARTE 1: CONFIGURACIÓN E INICIALIZACIÓN DE SESIÓN SECURE
# ==============================================================================
st.set_page_config(
    page_title="Portal de Grabaciones de Inglés",
    page_icon="🔒",
    layout="wide"
)

# Inicializar estados de sesión para el control de accesos
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "student_code" not in st.session_state:
    st.session_state.student_code = None

# Configuración del puente con el Google Sheet usando tu ID verificado
SPREADSHEET_ID = "2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP/pub?output=csv"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP/pub?output=csv"


# ==============================================================================
# PARTE 2: CARGA ULTRA SEGURA DE DATOS (FILTRO ANTI-NAN)
# ==============================================================================
@st.cache_data(ttl=3)  # Refresco rápido de caché de datos en segundos
def cargar_y_sanitizar_datos():
    try:
        df = pd.read_csv(URL_SHEET)
        
        # Elimina columnas sin nombre en el encabezado (los fantasmas 'nan' del archivo)
        columnas_validas = [col for col in df.columns if pd.notna(col) and not str(col).startswith('Unnamed:')]
        df = df[columnas_validas]
        
        # Sanitizar espacios en blanco en la columna de códigos de alumnos
        if 'IDE' in df.columns:
            df['IDE'] = df['IDE'].astype(str).str.strip()
            
        return df
    except Exception as e:
        st.error(f"Error crítico en el enlace de la base de datos: {e}")
        return None

df_source = cargar_y_sanitizar_datos()


# ==============================================================================
# PARTE 3: REPRODUCTOR RESILIENTE Y GESTOR DE DESCARGAS
# ==============================================================================
def renderizar_reproductor_audio(audio_data, file_index):
    """Repara cadenas Base64 incompletas y habilita descarga/reproducción sin bloqueos."""
    if not isinstance(audio_data, str) or not audio_data.strip():
        st.warning("⚠️ Este registro no cuenta con una evidencia multimedia válida.")
        return

    # Escenario A: Es un enlace web completo (ej. Google Drive)
    if audio_data.startswith("http://") or audio_data.startswith("https://"):
        st.audio(audio_data)
        st.markdown(
            f'<a href="{audio_data}" target="_blank">'
            f'<button style="width:100%; padding:10px; background-color:#1e7e34; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">'
            f'📥 Descargar desde Enlace Externo</button></a>', 
            unsafe_allow_html=True
        )
    
    # Escenario B: Es una cadena de texto Base64 embebida
    else:
        try:
            # Sanitizar saltos de línea de transmisión web y espacios ocultos
            clean_b64 = audio_data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",")[-1]
            
            # Ajuste de relleno matemático sobre base de 4 bits
            clean_b64 = clean_b64.rstrip('=')
            modulo = len(clean_b64) % 4
            if modulo > 0:
                clean_b64 += "=" * (4 - modulo)
            
            # Decodificación a datos binarios legibles
            audio_bytes = base64.b64decode(clean_b64)
            
            # Renderizar reproductor de audio integrado nativo del navegador
            st.audio(audio_bytes, format='audio/wav')
            
            # Desplegar botón de descarga local independiente
            st.download_button(
                label="📥 Descargar Archivo de Grabación (WAV)",
                data=audio_bytes,
                file_name=f"recording_student_{st.session_state.student_code}_{file_index}.wav",
                mime="audio/wav",
                key=f"download_trigger_widget_{file_index}",
                use_container_width=True
            )
        except Exception:
            st.error("❌ Pista inactiva. El archivo Base64 sobrepasó los 50,000 caracteres límites en la celda de Google Sheets.")


# ==============================================================================
# PARTE 4: POPUP DE SEGURIDAD (CUADRO DE DIÁLOGO EMERGENTE)
# ==============================================================================
@st.dialog("🔒 Autenticación de Acceso del Estudiante")
def popup_autenticacion():
    st.write("Digita tu código personal registrado en la columna **IDE** de la planilla para validar tu acceso.")
    
    # Campo de contraseña oculta para mayor confidencialidad
    input_code = st.text_input("Código de Estudiante (IDE):", type="password", key="modal_password_input").strip()
    
    if st.button("Verificar Credenciales", type="primary", use_container_width=True, key="modal_submit_button"):
        if df_source is not None and 'IDE' in df_source.columns:
            # Comprobar la existencia del código ingresado en los registros del Google Sheet
            if input_code in df_source['IDE'].values:
                st.session_state.authenticated = True
                st.session_state.student_code = input_code
                st.success("¡Identidad confirmada con éxito!")
                st.rerun()  # Cierra la ventana emergente y actualiza la interfaz
            else:
                st.error("❌ Código de estudiante no encontrado. Por favor intente de nuevo.")
        else:
            st.error("La base de datos de validación no está disponible temporalmente.")


# ==============================================================================
# PARTE 5: SISTEMA DE BLOQUEO PERMANENTE ANTES DEL INGRESO
# ==============================================================================
if not st.session_state.authenticated:
    st.info("👋 Bienvenido al Portal Evaluativo de Grabaciones.")
    st.markdown("### Control de Acceso Requerido")
    st.write("Los recursos multimedia de esta plataforma están restringidos. Por favor, inicia sesión con tu identificador.")
    
    if st.button("🔐 Abrir Terminal de Autenticación", type="primary", key="gatekeeper_start_button"):
        popup_autenticacion()
        
    st.stop()  # Detiene la lectura del script restante si la sesión no está verificada


# ==============================================================================
# PARTE 6: PANEL PRINCIPAL Y SISTEMA DE CIERRE SEGURO (SOLUCIÓN AL COMPILADOR)
# ==============================================================================
def procesar_cierre_de_sesion():
    st.session_state.authenticated = False
    st.session_state.student_code = None
    st.cache_data.clear()
    st.rerun()

# --- PANEL DE CONTROL LATERAL (Sidebar) ---
st.sidebar.markdown(f"### 👤 Perfil Verificado")
st.sidebar.info(f"**IDE Activo:** `{st.session_state.student_code}`")
if st.sidebar.button("🚪 Cerrar Sesión", key="logout_sidebar_unique_action", type="secondary"):
    procesar_cierre_de_sesion()

# --- CUERPO PRINCIPAL DE LA PÁGINA ---
# Filtrar registros en memoria que correspondan solo al estudiante activo
data_filtrada_estudiante = df_source[df_source['IDE'] == st.session_state.student_code]

# Fila del título y botón de abandono superior coordinado
col_cabecera, col_salir_pagina = st.columns([3, 1])

with col_cabecera:
    st.success(f"🔓 Canal seguro de información asignado al IDE: **{st.session_state.student_code}**")

with col_salir_pagina:
    # CLAVE ÚNICA MODIFICADA PARA EVITAR EL ERROR STREAMLITAPIEXCEPTION
    if st.button("❌ Salir / Terminar", key="main_logout_secure_unique_key", type="danger", use_container_width=True):
        procesar_cierre_de_sesion()

st.markdown(f"### 🎧 Historial de Grabaciones Registradas ({len(data_filtrada_estudiante)} registros)")
st.markdown("Usa los controles multimedia integrados en cada bloque para reproducir o respaldar tus archivos localmente.")
st.markdown("---")

if not data_filtrada_estudiante.empty and 'Subir evidencias' in data_filtrada_estudiante.columns:
    for indice, fila in data_filtrada_estudiante.iterrows():
        fecha_registro = fila['Fecha'] if 'Fecha' in fila else "No disponible"
        fase_registro = fila['Fase'] if 'Fase' in fila else "No disponible"
        
        with st.container(border=True):
            col_metadatos, col_reproductor_area = st.columns()
            
            with col_metadatos:
                st.markdown(f"##### 📋 Evidencia de Lectura N° {indice}")
                st.write(f"📅 **Fecha de Carga:** {fecha_registro}")
                st.write(f"🎯 **Etapa evaluada:** {fase_registro}")
                if 'Enlace Sitio Web' in fila and pd.notna(fila['Enlace Sitio Web']):
                    st.markdown(f"🔗 [Ir al Sitio del Proyecto]({fila['Enlace Sitio Web']})")
                    
            with col_reproductor_area:
                st.markdown("**Controles de Audio Disponibles:**")
                # Invoca de forma segura al renderizador usando el índice numérico incremental
                renderizar_reproductor_audio(fila['Subir evidencias'], indice)
else:
    st.info("No se registran bitácoras ni archivos cargados asociados a este identificador.")
