import streamlit as st
import pandas as pd
import base64
import requests
import io
import time
from datetime import datetime

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 6 STANDALONE PARTS
# PART 1: EXTENSION PACKAGE MANAGERS, WEB GEOMETRIES, & MASTER SESSION CACHES
# FIXED WEB DATA INGESTION MATRIX • ENGLISHAUDIOUPLOAD.PY
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Secure Portal", layout="centered")

# Initialize global authentication session tracking variables if not present in short-term memory
if "authenticated_student_record" not in st.session_state:
    st.session_state.authenticated_student_record = None

# ----------------------------------------------------------------------------
# CRITICAL HARDCODED SYSTEM SECURITY PROTECTIONS INTERLOCK
# ----------------------------------------------------------------------------
# Your correct Google Web Publication Key Token String from the active account
TARGET_GOOGLE_SHEET_TOKEN = "2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP"

# FIXED EXPORT PATHWAY CONSTRUCTOR:
# Routes strictly via the native web-publishing endpoint rather than google.com root indices.
# This prevents the idna codec label overflow and strips HTML parsing duplicates entirely.
PUBLIC_CSV_EXPORT_URL = f"https://google.com{TARGET_GOOGLE_SHEET_TOKEN}/pub?output=csv"
# ============================================================================
# PART 2: FIREWALL-SAFE REAL-TIME CLOUD SYNCHRONIZATION ENGINE
# ============================================================================

@st.cache_data(ttl=2) # 2-second Time-To-Live forces Streamlit to constantly look for new student codes
def fetch_live_cloud_results_ledger(target_url):
    try:
        # Pulls the data cleanly as an isolated web request stream to clear URL label bugs
        web_response_packet = requests.get(target_url, timeout=10)
        if web_response_packet.status_code == 200:
            string_data_buffer = io.StringIO(web_response_packet.text)
            df = pd.read_csv(string_data_buffer, header=None)
            return df
        else:
            return None
    except Exception as err:
        st.warning(f"📡 Cloud Sync Notice: Syncing data records from cloud server channels... ({err})")
        return None

# Instantly pull the full cloud database rows list frame
sheet_raw_data_matrix = fetch_live_cloud_results_ledger(PUBLIC_CSV_EXPORT_URL)
# ============================================================================
# PART 3: UNBLOCKED FORM-STATE POPUP PASSWORD GATEKEEPER
# ============================================================================

# If no active student record token is currently authorized inside memory, lock down viewport layouts
if st.session_state.authenticated_student_record is None:
    st.markdown("<h3 style='text-align: center; color: #117A65; font-weight: bold;'>🔐 System Security Access Lock</h3>", unsafe_allow_html=True)
    st.write("Welcome to the CEI Master Toolsuite Archive. Please enter your unique Student ID Code to act as your access verification password:")
    
    # Encapsulated form layout forces immediate session state value submission on button click actions
    with st.form("cei_student_secure_password_gateway_form"):
        student_entered_password_string = st.text_input(
            label="🔑 Enter Student Code as Password:",
            placeholder="Type your personal IDE code here...",
            type="password"
        )
        submit_auth_trigger = st.form_submit_button("⚡ Verify Code Credentials & Open Dashboard")
        
        if submit_auth_trigger:
            if student_entered_password_string.strip() == "":
                st.error("Operation Aborted: Password input string cannot be blank.")
            elif sheet_raw_data_matrix is not None:
                clean_search_token = student_entered_password_string.strip().lower()
                
                timestamp_column_index = 0   # Column 1 (Index 0) -> Fecha Registro
                student_code_column_index = 1 # Column 2 (Index 1) -> STRICTLY POSITIONED AT: IDE
                audio_stream_column_index = 2 # Column 3 (Index 2) -> STRICTLY POSITIONED AT: Subir Evidencias
                
                temporary_match_holder = None
                
                # Sequentially process cloud entries, scanning for the entered student code inside column index 1
                for index, row in sheet_raw_data_matrix.iterrows():
                    if index == 0: 
                        continue # Skip row index 0 columns headers cleanly
                    if len(row) > max(student_code_column_index, audio_stream_column_index):
                        spreadsheet_registered_student_id = str(row.iloc[student_code_column_index]).strip().lower()
                        
                        if spreadsheet_registered_student_id == clean_search_token:
                            temporary_match_holder = {
                                "timestamp": str(row.iloc[timestamp_column_index]),
                                "code": str(row.iloc[student_code_column_index]),
                                "audio_data": str(row.iloc[audio_stream_column_index])
                            }
                            break
                
                if temporary_match_holder is not None:
                    st.session_state.authenticated_student_record = temporary_match_holder
                    st.toast("🔓 Access Granted! Unlocking your custom playback repository files panels...")
                    time.sleep(0.5)
                    st.rerun() # Refresh app canvas to clear login wall and reveal matching parameters
                else:
                    st.error("🔒 Security Lock: Invalid student verification token password access keys. Code not found inside dataset records.")
            else:
                st.error("🔒 Database connection offline. Please check your Google Sheet access permissions.")
                    
    st.caption("⚠️ *Notice: Unauthorized attempts to download or modify student vocal records data models are monitored.*")
    st.stop() # CRITICAL STOP INTERLOCK: Freeze app rendering right here if student fails password verification!

# ============================================================================
# APPS LAYOUT AREA (UNLOCKED ONLY PAST THE GATEKEEPER AUTHORIZATION MATRICES)
# ============================================================================
st.markdown("<h1 style='text-align: center; color: #117A65; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>Secure Playback Database Upload & Student Verification Desk</h4>", unsafe_allow_html=True)
# ============================================================================
# PART 4: SECURE STUDENT AUDIOS PLAYER DESK PANEL (WAV DECODING UNMUTED)
# ============================================================================
st.write("---")

# Pull down the authorized data packet logged into session state memories
current_active_student_record = st.session_state.authenticated_student_record

st.info(f"👤 **Student Code Profile Locked:** `{current_active_student_record['code']}` | **Logged On:** {current_active_student_record['timestamp']}")

try:
    raw_base64_string = current_active_student_record['audio_data'].strip()
    if "," in raw_base64_string: 
        raw_base64_string = raw_base64_string.split(",")[-1]
        
    # Calculates character lengths and auto-appends structural '=' string indicators 
    missing_padding_characters_count = len(raw_base64_string) % 4
    if missing_padding_characters_count != 0:
        raw_base64_string += "=" * (4 - missing_padding_characters_count)
        
    decoded_audio_bytes_payload = base64.b64decode(raw_base64_string)
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #117A65; margin-bottom: 2px;'>🔊 PLAYBACK TRACK CONSOLE:</p>", unsafe_allow_html=True)
    
    # HTML5 standard container player tracks layout unmuted via explicit type='audio/wav' mapping channels
    st.components.v1.html(f"""
        <div style='background-color: #E8F8F5; border: 1px solid #A3E4D7; border-radius: 6px; padding: 10px; text-align: center;'>
            <audio controls style='width: 100%; height: 40px;'>
                <source src='data:audio/wav;base64,{raw_base64_string}' type='audio/wav'>
                Your browser does not support unblocked local element audio vectors.
            </audio>
        </div>
    """, height=65)
    
    st.download_button(
        label=f"📥 Download Your Verified Sound Take ({current_active_student_record['code']}.wav)",
        data=decoded_audio_bytes_payload,
        file_name=f"{current_active_student_record['code']}_Verified_Take.wav",
        mime="audio/wav",
        key="student_direct_download_key_node"
    )
except Exception as data_err:
    st.error(f"Linguistic file block corrupted or written in an invalid format string structure ({data_err}).")
# ============================================================================
# PART 5: REORDERED SUBMISSION INTERFACE PANEL
# ============================================================================
st.write("---")
st.markdown("### 📥 My Recording Playback List")
st.write("Authorized users use this space to submit or check recorded oral entries.")

admin_target_student_id = st.text_input(label="📋 Target Student Code Mapping Assignment:", placeholder="e.g., CEI-2026-4402", key="admin_id_field")
uploaded_student_file_asset = st.file_uploader(label="📁 Uploading my new Recording Playbacks:", type=["mp3", "wav"])

compiled_base64_string_payload = ""

if uploaded_student_file_asset is not None:
    try:
        raw_uploaded_bytes_block = uploaded_student_file_asset.read()
        compiled_base64_string_payload = base64.b64encode(raw_uploaded_bytes_block).decode('utf-8')
        st.info(f"✨ File asset '{uploaded_student_file_asset.name}' loaded successfully inside browser memory.")
    except Exception as file_err:
        st.error(f"Error compiling structural file payload bytes ({file_err}).")
# ============================================================================
# PART 6: THE DYNAMIC AUTOMATED MONITOR TABLE SUMMARY
# ============================================================================
st.write("---")
st.markdown("### 📊 Stored Records Summary Ledger Matrix")

if sheet_raw_data_matrix is not None and not sheet_raw_data_matrix.empty:
    try:
        header_labels_row_list = sheet_raw_data_matrix.iloc[0].astype(str).str.strip().tolist()
        data_content_matrix_rows = sheet_raw_data_matrix.iloc[1:].copy()
        data_content_matrix_rows.columns = header_labels_row_list
        
        visible_summary_ledger_df = data_content_matrix_rows.copy()
        if "Subir Evidencias" in visible_summary_ledger_df.columns:
            visible_summary_ledger_df["Subir Evidencias"] = "🔒 Audio Blob Data Protected"
            
        st.dataframe(visible_summary_ledger_df, use_container_width=True, hide_index=True)
        st.caption(f"💡 *Total Stored Student Registrations active: {len(visible_summary_ledger_df)} files rows.*")
        
        csv_ledger_buffer = visible_summary_ledger_df.to_csv(index=False)
        st.download_button(label="📥 Download Clean Student Logs Overview (.csv)", data=csv_ledger_buffer.encode('utf-8'), file_name="CEI_Registered_Students_Report.csv", mime="text/csv")
    except Exception as display_err:
        st.error(f"Error mapping spreadsheet layout columns variables arrays ({display_err}).")
else:
    st.info("Awaiting active sheet row entries database packets updates data models...")
