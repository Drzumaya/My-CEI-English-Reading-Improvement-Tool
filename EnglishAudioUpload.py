import base64
import pandas as pd
import streamlit as st

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Visualizador de Evidencias",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Panel de Control y Streaming de Datos")
st.markdown("---")

# 1. DIRECCIÓN DE TU GOOGLE SHEET (Actualizado con tu ID correcto)
# Usamos el formato /export?format=csv para que Pandas lo lea directamente sin fallar en los hosts
SPREADSHEET_ID = "1vnRZDlb79scuC4kkdy0X3QNJKSLsVUFe_YoUe8GZlQU"
URL_SHEET = f"https://google.com{SPREADSHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)  # Se actualiza automáticamente cada 10 segundos
def cargar_datos():
    try:
        # Cargar los datos directo de la URL de exportación
        df = pd.read_csv(URL_SHEET)
        
        # 2. LIMPIEZA DE COLUMNAS DUPLICADAS O VACÍAS (Evita el error 'nan')
        # Filtramos para quedarnos solo con columnas que tengan un nombre real y válido
        columnas_validas = [col for col in df.columns if pd.notna(col) and not str(col).startswith('Unnamed:')]
        df = df[columnas_validas]
        
        # Eliminar filas completamente vacías que puedan alterar el orden
        df = df.dropna(how='all')
        
        return df
    except Exception as e:
        st.error(f"Error de conexión al cargar la planilla: {e}")
        return None

# Carga de datos al inicializar la app
df_datos = cargar_datos()

if df_datos is not None:
    st.success("✅ Conexión establecida con éxito con el objetivo.")
    
    # Mostrar métricas rápidas de tu tabla
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Registros", len(df_datos))
    with col2:
        st.metric("Última Fase Activa", df_datos['Fase'].iloc[-1] if 'Fase' in df_datos.columns else "N/A")
    with col3:
        st.metric("Columnas Mapeadas", len(df_datos.columns))

    st.markdown("### 📋 Vista General de Datos")
    # Mostramos la tabla limpia en la interfaz
    st.dataframe(df_datos, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎧 Reproductor Seguro de Evidencias de Audio")

    # Crear un selector dinámico para revisar fila por fila los audios
    if 'IDE' in df_datos.columns and 'Subir evidencias' in df_datos.columns:
        opciones_registro = [f"ID: {row['IDE']} - Fecha: {row['Fecha']}" for _, row in df_datos.iterrows()]
        
        seleccion = st.selectbox("Selecciona un registro para escuchar el audio:", opciones_registro)
        
        # Obtener el índice de la fila seleccionada
        idx_seleccionado = opciones_registro.index(seleccion)
        fila_actual = df_datos.iloc[idx_seleccionado]
        
        audio_data = fila_actual['Subir evidencias']
        
        st.info(f"**Procesando audio para el IDE:** {fila_actual['IDE']}")

        # 3. BLOQUE DE REPARACIÓN DE STRING BASE64 CORRUPTO (Múltiplos de 4)
        if isinstance(audio_data, str) and audio_data.strip():
            # Validar si es un enlace de Drive o un texto Base64
            if audio_data.startswith("http://") or audio_data.startswith("https://"):
                st.audio(audio_data)
                st.caption("Audio reproducido directamente desde enlace web/Drive.")
            else:
                try:
                    # Limpieza absoluta de espacios y caracteres de escape
                    clean_base64 = audio_data.strip().replace("\n", "").replace("\r", "")
                    
                    # Remover metadatos de encabezado de audio web si existen
                    if "," in clean_base64:
                        clean_base64 = clean_base64.split(",")[-1]
                    
                    # Remover rellenos viejos para recalcular la estructura exacta de 4 bits
                    clean_base64 = clean_base64.rstrip('=')
                    residuo = len(clean_base64) % 4
                    if residuo > 0:
                        # Corrige el error de "1 more than a multiple of 4" añadiendo los faltantes
                        clean_base64 += "=" * (4 - residuo)
                    
                    # Convertir el bloque corregido a binario ejecutable por el reproductor
                    audio_bytes = base64.b64decode(clean_base64)
                    
                    # Desplegar reproductor de audio nativo en el navegador
                    st.audio(audio_bytes, format='audio/wav')
                    st.success("🎉 Cadena Base64 reparada y decodificada con éxito.")
                    
                except Exception as error_decode:
                    st.error(f"❌ Estructura de archivo corrupta. La celda excede los 50,000 caracteres límites de Google Sheets.")
                    st.warning("Recomendación: Cambia tu Apps Script para guardar los archivos de audio pesados en Google Drive.")
        else:
            st.warning("⚠️ No se detectó ninguna cadena de audio o enlace en la columna 'Subir evidencias' para esta fila.")
    else:
        st.error("❌ Columnas críticas ausentes. La hoja de cálculo debe contener las columnas 'IDE' y 'Subir evidencias'.")

else:
    st.warning("Refrescando la conexión con la base de datos de Google...")

# Botón manual en la barra lateral para vaciar memoria caché del navegador de Streamlit
if st.sidebar.button("🔄 Forzar Sincronización (Limpiar Caché)"):
    st.cache_data.clear()
    st.rerun()
