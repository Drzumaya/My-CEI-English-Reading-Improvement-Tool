import base64
import pandas as pd
import streamlit as st

# ==============================================================================
# 🧩 PARTE 1: CONFIGURACIÓN, INICIALIZACIÓN Y SEGURIDAD (CONEXIÓN Y LOGIN)
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

@st.dialog("🔒 Autenticación de Acceso del Estudiante")
def popup_autenticacion():
    st.write("Digita tu código personal registrado en la columna **IDE** de la planilla para validar tu acceso.")
    input_code = st.text_input("Código de Estudiante (IDE):", type="password", key="modal_password_input").strip()
    
    if st.button("Verificar Credenciales", type="primary", use_container_width=True, key="modal_submit_button"):
        if df_source is not None and 'IDE' in df_source.columns:
            if input_code in df_source['IDE'].values:
                st.session_state.authenticated = True
                st.session_state.student_code = input_code
                st.success("¡Identidad confirmada con éxito!")
                st.rerun()
            else:
                st.error("❌ Código de estudiante no encontrado. Por favor intente de nuevo.")
        else:
            st.error("La base de datos de validación no está disponible temporalmente.")

# Sistema de bloqueo permanente antes del ingreso
if not st.session_state.authenticated:
    st.info("👋 Bienvenido al Portal Evaluativo de Grabaciones.")
    st.markdown("### Control de Acceso Requerido")
    st.write("Los recursos multimedia de esta plataforma están restringidos. Por favor, inicia sesión con tu identificador.")
    if st.button("🔐 Abrir Terminal de Autenticación", type="primary", key="gatekeeper_start_button"):
        popup_autenticacion()
    st.stop()


# ==============================================================================
# 🧩 PARTE 2: NÚCLEO DE PROCESAMIENTO MULTIMEDIA (REPARADOR DE AUDIO Y DESCARGAS)
# ==============================================================================
def renderizar_reproductor_audio(audio_data, file_index):
    """Repara cadenas Base64, extrae formatos de forma segura y elimina el mensaje de ERROR."""
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
            # 1. Sanitización total de la cadena de texto
            clean_b64 = audio_data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            
            # 2. EXTRACCIÓN SEGURA DEL FORMATO MIME
            # Usamos 'audio/mpeg' por defecto porque es el formato más tolerante en navegadores
            formato_nativo = 'audio/mpeg' 
            
            if "data:audio/" in clean_b64 and ";base64," in clean_b64:
                partes = clean_b64.split(";base64,")
                # Extraemos correctamente el tipo MIME del elemento [0]
                formato_nativo = partes[0].replace("data:", "")
                # Nos quedamos solo con la data Base64 pura del elemento [1]
                clean_b64 = partes[1]
            elif "," in clean_b64:
                clean_b64 = clean_b64.split(",")[-1]
            
            # 3. Ajuste estricto de relleno matemático de 4 bits
            clean_b64 = clean_b64.rstrip('=')
            modulo = len(clean_b64) % 4
            if modulo > 0:
                clean_b64 += "=" * (4 - modulo)
            
            # 4. Decodificación a datos binarios puros
            audio_bytes = base64.b64decode(clean_b64)
            
            # 5. REPRODUCTOR RESILIENTE (Elimina el aviso de ERROR interno)
            # Pasamos los bytes limpios y asignamos el formato nativo exacto analizado
            st.audio(audio_bytes, format=formato_nativo)
            
            # 6. BOTÓN DE DESCARGA SEGURO
            extension_archivo = formato_nativo.split("/")[-1] if "/" in formato_nativo else "mp3"
            st.download_button(
                label=f"📥 Descargar Archivo de Grabación ({extension_archivo.upper()})",
                data=audio_bytes,
                file_name=f"recording_student_{st.session_state.student_code}_{file_index}.{extension_archivo}",
                mime=formato_nativo,
                key=f"download_trigger_widget_{file_index}",
                use_container_width=True
            )
            
        except Exception as error_fatal:
            st.error(f"❌ Estructura de audio no legible en el navegador.")
            st.caption(f"Detalle técnico preliminar: {str(error_fatal)}")

# ==============================================================================
# 🧩 PARTE 3: PANEL DE USUARIO E INTERFAZ GRÁFICA (VISTA DE REGISTROS FILTRADOS)
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

# Banner superior de confirmación de canal seguro
st.success(f"🔓 Canal seguro de información asignado al IDE: **{st.session_state.student_code}**")

st.markdown(f"### 🎧 Historial de Grabaciones Registradas ({len(data_filtrada_estudiante)} registros)")
st.markdown("Usa los controles multimedia integrados en cada bloque para reproducir o respaldar tus archivos localmente.")
st.markdown("---")

if not data_filtrada_estudiante.empty and 'Subir evidencias' in data_filtrada_estudiante.columns:
    for indice, fila in data_filtrada_estudiante.iterrows():
        fecha_recording = fila['Fecha'] if 'Fecha' in fila else "No disponible"
        fase_recording = fila['Fase'] if 'Fase' in fila else "No disponible"
        
        with st.container(border=True):
            # SOLUCIÓN COMPILADOR: Agregamos el número '2' para definir el número de columnas
            col_metadatos, col_reproductor_area = st.columns(2)
            
            with col_metadatos:
                st.markdown(f"##### 📋 Evidencia de Lectura N° {indice}")
                st.write(f"📅 **Fecha de Carga:** {fecha_recording}")
                st.write(f"🎯 **Etapa evaluada:** {fase_recording}")
                if 'Enlace Sitio Web' in fila and pd.notna(fila['Enlace Sitio Web']):
                    st.markdown(f"🔗 [Ir al Sitio del Proyecto]({fila['Enlace Sitio Web']})")
                    
            with col_reproductor_area:
                st.markdown("**Controles de Audio Disponibles:**")
                # Invoca al renderizador usando el índice numérico de la fila
                renderizar_reproductor_audio(fila['Subir evidencias'], indice)
else:
    st.info("No se registran bitácoras ni archivos cargados asociados a este identificador.")
