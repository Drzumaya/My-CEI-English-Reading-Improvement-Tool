import base64
import pandas as pd
import streamlit as st

# ==============================================================================
# PARTE 1: CONFIGURACIÓN DE LA INTERFAZ Y AJUSTES DE PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Visualizador de Evidencias",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Panel de Control y Streaming de Datos")
st.markdown("---")


# ==============================================================================
# PARTE 2: CONEXIÓN SEGURA Y DESCARGA DEL GOOGLE SHEET (VÍA EXPORTACIÓN CSV)
# ==============================================================================
SPREADSHEET_ID = "1vnRZDlb79scuC4kkdy0X3QNJKSLsVUFe_YoUe8GZlQU"
URL_SHEET = f"https://google.com{SPREADSHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)  # Sincronización automática de datos cada 10 segundos
def cargar_datos():
    try:
        # Descarga directa desde los servidores de Google omitiendo errores de host
        df = pd.read_csv(URL_SHEET)
        
        # ----------------------------------------------------------------------
        # PARTE 3: LIMPIEZA DE COLUMNAS VACÍAS Y DUPLICADOS (FILTRO ANTI-NAN)
        # ----------------------------------------------------------------------
        # Identifica y conserva únicamente las columnas que poseen títulos válidos
        columnas_validas = [col for col in df.columns if pd.notna(col) and not str(col).startswith('Unnamed:')]
        df = df[columnas_validas]
        
        # Remueve filas fantasmas totalmente en blanco al fondo del documento
        df = df.dropna(how='all')
        
        return df
    except Exception as e:
        st.error(f"Error de conexión al cargar la planilla: {e}")
        return None

# Inicialización y lectura de la tabla purificada
df_datos = cargar_datos()


# ==============================================================================
# PARTE 4: RENDERIZADO DE TABLAS Y ESTADÍSTICAS EN PANTALLA
# ==============================================================================
if df_datos is not None:
    st.success("✅ Conexión establecida con éxito con el objetivo.")
    
    # Despliegue de métricas superiores operativas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Registros", len(df_datos))
    with col2:
        st.metric("Última Fase Activa", df_datos['Fase'].iloc[-1] if 'Fase' in df_datos.columns else "N/A")
    with col3:
        st.metric("Columnas Mapeadas", len(df_datos.columns))

    st.markdown("### 📋 Vista General de Datos")
    # Renderizado interactivo del Dataframe limpio de errores de layout
    st.dataframe(df_datos, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎧 Reproductor Seguro de Evidencias de Audio")


    # ==============================================================================
    # PARTE 5: SELECCIÓN DINÁMICA DE REGISTROS POR IDENTIFICADOR (IDE)
    # ==============================================================================
    if 'IDE' in df_datos.columns and 'Subir evidencias' in df_datos.columns:
        # Construcción del menú desplegable para aislar filas
        opciones_registro = [f"ID: {row['IDE']} - Fecha: {row['Fecha']}" for _, row in df_datos.iterrows()]
        seleccion = st.selectbox("Selecciona un registro para escuchar el audio:", opciones_registro)
        
        # Extracción indexada de la fila seleccionada por el usuario
        idx_seleccionado = opciones_registro.index(seleccion)
        fila_actual = df_datos.iloc[idx_seleccionado]
        audio_data = fila_actual['Subir evidencias']
        
        st.info(f"**Procesando audio para el IDE:** {fila_actual['IDE']}")


        # ==============================================================================
        # PARTE 6: PARCHEO MATEMÁTICO DE BASE64 Y DECODIFICACIÓN BINARIA DE AUDIO
        # ==============================================================================
        if isinstance(audio_data, str) and audio_data.strip():
            # Bifurcación en caso de que sea un enlace web directo (Drive) o Base64 string
            if audio_data.startswith("http://") or audio_data.startswith("https://"):
                st.audio(audio_data)
                st.caption("Audio reproducido directamente desde enlace web/Drive.")
            else:
                try:
                    # Sanitización del string: remoción de espacios y saltos de línea de red
                    clean_base64 = audio_data.strip().replace("\n", "").replace("\r", "")
                    
                    # Eliminación de prefijos de metadata web en caso de existir
                    if "," in clean_base64:
                        clean_base64 = clean_base64.split(",")[-1]
                    
                    # Corrección del error matemático de longitud (Múltiplo de 4)
                    clean_base64 = clean_base64.rstrip('=')
                    residuo = len(clean_base64) % 4
                    if residuo > 0:
                        # Añade dinámicamente los bytes '=' faltantes para subsanar el corte abrupto
                        clean_base64 += "=" * (4 - residuo)
                    
                    # Transformación del bloque de texto reparado a binario puro
                    audio_bytes = base64.b64decode(clean_base64)
                    
                    # Inicialización del reproductor nativo HTML5 en el navegador
                    st.audio(audio_bytes, format='audio/wav')
                    st.success("🎉 Cadena Base64 reparada y decodificada con éxito.")
                    
                except Exception as error_decode:
                    st.error(f"❌ Estructura de archivo corrupta. La celda excede los 50,000 caracteres límites de Google Sheets.")
                    st.warning("Recomendación: Modifica tu Apps Script para almacenar los archivos en Google Drive.")
        else:
            st.warning("⚠️ No se detectó ninguna cadena de audio o enlace en la columna 'Subir evidencias' para esta fila.")
    else:
        st.error("❌ Columnas críticas ausentes. La hoja de cálculo debe contener las columnas 'IDE' y 'Subir evidencias'.")
else:
    st.warning("Refrescando la conexión con la base de datos de Google...")

# Herramienta lateral de reinicio manual y vaciado de caché
if st.sidebar.button("🔄 Forzar Sincronización (Limpiar Caché)"):
    st.cache_data.clear()
    st.rerun()
