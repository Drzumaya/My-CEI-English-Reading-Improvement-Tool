import base64
import pandas as pd
import streamlit as st

# ==============================================================================
# PART 1: PAGE CONFIGURATION & SESSION STATE INITIALIZATION
# ==============================================================================
st.set_page_config(
    page_title="Student Recording Portal",
    page_icon="🔒",
    layout="wide"
)

# Initialize secure session states to track user authentication status
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "student_code" not in st.session_state:
    st.session_state.student_code = None

# Google Sheet Configuration
SPREADSHEET_ID = "2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP/pub?output=csv"


# ==============================================================================
# PART 2: SECURE DATA FETCHING AND CLEANING
# ==============================================================================
@st.cache_data(ttl=5)  # Quick cache refresh to fetch new sheet rows dynamically
def load_and_clean_data():
    try:
        df = pd.read_csv(URL_SHEET)
        
        # Remove unnamed phantom columns (nan headers) causing mapping issues
        valid_columns = [col for col in df.columns if pd.notna(col) and not str(col).startswith('Unnamed:')]
        df = df[valid_columns]
        
        # Strip string values in 'IDE' to avoid trailing space matching issues
        if 'IDE' in df.columns:
            df['IDE'] = df['IDE'].astype(str).str.strip()
            
        return df
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

df_source = load_and_clean_data()


# ==============================================================================
# PART 3: REPLAY COMPONENT FOR BASE64 OR URL ENCODED AUDIOS
# ==============================================================================
def render_audio_player(audio_data, file_index):
    """Parses, sanitizes, and renders a web player + download button for audio."""
    if not isinstance(audio_data, str) or not audio_data.strip():
        st.warning("⚠️ Empty playback file found for this record.")
        return

    # Check if the data is a clean URL link
    if audio_data.startswith("http://") or audio_data.startswith("https://"):
        st.audio(audio_data)
        st.caption("Streamed directly from web link source.")
    else:
        # It's an inline Base64 data string
        try:
            clean_b64 = audio_data.strip().replace("\n", "").replace("\r", "")
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",")[-1]
            
            # Pad binary block using length modulo of 4
            clean_b64 = clean_b64.rstrip('=')
            modulo = len(clean_b64) % 4
            if modulo > 0:
                clean_b64 += "=" * (4 - modulo)
            
            audio_bytes = base64.b64decode(clean_b64)
            
            # Render built-in native HTML5 audio stream layout player
            st.audio(audio_bytes, format='audio/wav')
            
            # Explicitly provide a downloadable button element for the audio file
            st.download_button(
                label="📥 Download Recording File",
                data=audio_bytes,
                file_name=f"recording_evidence_{file_index}.wav",
                mime="audio/wav",
                key=f"dl_{file_index}"
            )
        except Exception:
            st.error("❌ Audio data stream block corrupted or exceeds Google Sheet character capacities.")


# ==============================================================================
# PART 4: POPUP PASSWORD WINDOW DIALOG
# ==============================================================================
@st.dialog("🔒 Student Access Authentication")
def login_popup():
    st.write("Please enter your assigned Student Code matching the spreadsheet records to unlock your playbacks.")
    
    input_code = st.text_input("Student Code (IDE):", type="password", help="Case-sensitive code identifier").strip()
    
    if st.button("Verify Identity", type="primary", use_container_width=True):
        if df_source is not None and 'IDE' in df_source.columns:
            # Check if input string matches any valid code existing in the sheet
            if input_code in df_source['IDE'].values:
                st.session_state.authenticated = True
                st.session_state.student_code = input_code
                st.success("Access Granted! Loading profile...")
                st.rerun()  # Forces app layout refresh to wipe the dialog window away
            else:
                st.error("❌ Invalid Student Code. Check spelling or contact system admin.")
        else:
            st.error("System connection down. Unable to cross-reference access credentials.")


# ==============================================================================
# PART 5: PAGE ACCESS CONTROL LOGIC ROUTER
# ==============================================================================
if not st.session_state.authenticated:
    # Page remains locked down with clean graphics until popup window authentication resolves
    st.info("👋 Welcome to the Evaluation Database.")
    st.markdown("### Authentication Required")
    st.write("Click the button below to complete validation security checkpoints.")
    
    if st.button("🔐 Open Login Terminal", type="primary"):
        login_popup()
        
    st.stop()  # Aborts script execution for non-logged-in sessions completely


# ==============================================================================
# PART 6: SECURE DASHBOARD DESKTOP (POST-LOGIN INTERFACE)
# ==============================================================================
# If execution reaches this block, user validation has succeeded
st.sidebar.markdown(f"### 👤 Logged In Account")
st.sidebar.info(f"**Student IDE:** `{st.session_state.student_code}`")

if st.sidebar.button("🚪 Log Out and Lock Session", type="secondary"):
    st.session_state.authenticated = False
    st.session_state.student_code = None
    st.cache_data.clear()
    st.rerun()

# Isolate matching target data matching current authorized profile criteria
student_records = df_source[df_source['IDE'] == st.session_state.student_code]

st.success(f"🔓 Secure access established for student ID: **{st.session_state.student_code}**")
st.markdown(f"### 🎧 Your Playback Evaluation Panel ({len(student_records)} records found)")
st.markdown("All assets below are securely fetched, playable online, and authorized for download.")
st.markdown("---")

if not student_records.empty and 'Subir evidencias' in student_records.columns:
    # Iterate over filtered assignments to construct visual control blocks
    for index, row in student_records.iterrows():
        # Clean date parsing or general fallback layout definitions
        fecha_display = row['Fecha'] if 'Fecha' in row else "Unknown Date"
        fase_display = row['Fase'] if 'Fase' in row else "Unknown Phase"
        web_link = row['Enlace Sitio Web'] if 'Enlace Sitio Web' in row else "N/A"
        
        with st.container(border=True):
            col_info, col_player = st.columns([1, 2])
            
            with col_info:
                st.markdown(f"##### 📋 Recording Instance #{index}")
                st.write(f"📅 **Date Submited:** {fecha_display}")
                st.write(f"🎯 **Project Phase:** {fase_display}")
                if web_link != "N/A":
                    st.markdown(f"🔗 [Project External Link]({web_link})")
            
            with col_player:
                st.markdown("**Media Asset Player:**")
                render_audio_player(row['Subir evidencias'], index)
else:
    st.info("No uploaded tracking playbacks mapped against your student code file index yet.")
