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
# MASTER DUMP-CACHE DIRECT PIPELINE MATRIX • ENGLISHAUDIOUPLOAD.PY
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

st.set_page_config(page_title="CEI Secure Portal", layout="centered")

if "authenticated_student_record" not in st.session_state:
    st.session_state.authenticated_student_record = None

# Unified master account publication key token string
MASTER_COMPLIANCE_TOKEN = "h2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP"
# Native Google Sheets raw stream publishing endpoint query route path
FINAL_UNTAINTED_NET_URL = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP/pub?gid=2026091417&single=true&output=csv"

# ============================================================================
# PART 2: UNCACHED UNMUTED DOCKER PIPELINE NETWORK READ STRACTION
# ============================================================================
@st.cache_data(ttl=1)
def extract_live_sheets_matrix_uncached(target_url):
    try:
        # Pull data as a clean raw web packet stream to force reset broken server labels
        server_raw_packet = requests.get(target_url, timeout=12)
        if server_raw_packet.status_code == 200:
            string_io_buffer = io.StringIO(server_raw_packet.text)
            df = pd.read_csv(string_io_buffer, header=None)
            return df
        return None
    except Exception as network_error:
        st.error(f"📡 System Connection Notice: Streaming target spreadsheet... ({network_error})")
        return None

sheet_raw_data_matrix = extract_live_sheets_matrix_uncached(FINAL_UNTAINTED_NET_URL)

# ============================================================================
# PART 3: UNBLOCKED FORM-STATE POPUP PASSWORD GATEKEEPER
# ============================================================================
if st.session_state.authenticated_student_record is None:
    st.markdown("<h3 style='text-align: center; color: #117A65; font-weight: bold;'>🔐 System Security Access Lock</h3>", unsafe_allow_html=True)
    st.write("Welcome to the CEI Master Toolsuite Archive. Please enter your unique Student ID Code to act as your access verification password:")
    
    with st.form("cei_student_secure_password_gateway_form"):
        student_entered_password_string = st.text_input(label="🔑 Enter Student Code as Password:", placeholder="Type your personal IDE code here...", type="password")
        submit_auth_trigger = st.form_submit_button("⚡ Verify Code Credentials & Open Dashboard")
        
        if submit_auth_trigger:
            if student_entered_password_string.strip() == "":
                st.error("Operation Aborted: Password input string cannot be blank.")
            elif sheet_raw_data_matrix is not None:
                clean_search_token = student_entered_password_string.strip().lower()
                
                timestamp_column_index = 0   
                student_code_column_index = 1 
                audio_stream_column_index = 2 
                
                temporary_match_holder = None
                
                for index, row in sheet_raw_data_matrix.iterrows():
                    if index == 0: continue 
                    if len(row) > max(student_code_column_index, audio_stream_column_index):
                        if str(row.iloc[student_code_column_index]).strip().lower() == clean_search_token:
                            temporary_match_holder = {
                                "timestamp": str(row.iloc[timestamp_column_index]),
                                "code": str(row.iloc[student_code_column_index]),
                                "audio_data": str(row.iloc[audio_stream_column_index])
                            }
                            break
                
                if temporary_match_holder is not None:
                    st.session_state.authenticated_student_record = temporary_match_holder
                    st.toast("🔓 Access Granted!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("🔒 Security Lock: Code not found inside dataset records.")
            else:
                st.error("🔒 Database connection offline. Clear your app container storage on share.streamlit.io.")
                    
    st.caption("⚠️ *Notice: Unauthorized attempts to download or modify student vocal records data models are monitored.*")
    st.stop() 

# Unlocked application interface zone canvas parameters views
st.markdown("<h1 style='text-align: center; color: #117A65; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>Secure Playback Database Upload & Student Verification Desk</h4>", unsafe_allow_html=True)

# ============================================================================
# PART 4: SECURE STUDENT AUDIOS DISPLAYER DESK PANEL (WAV DECODING UNMUTED)
# ============================================================================
st.write("---")
current_active_student_record = st.session_state.authenticated_student_record
st.info(f"👤 **Student Code Profile Locked:** `{current_active_student_record['code']}` | **Logged On:** {current_active_student_record['timestamp']}")

try:
    raw_base64_string = current_active_student_record['audio_data'].strip()
    if "," in raw_base64_string: raw_base64_string = raw_base64_string.split(",")[-1]
        
    missing_padding_characters_count = len(raw_base64_string) % 4
    if missing_padding_characters_count != 0: raw_base64_string += "=" * (4 - missing_padding_characters_count)
        
    decoded_audio_bytes_payload = base64.b64decode(raw_base64_string)
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #117A65; margin-bottom: 2px;'>🔊 PLAYBACK TRACK CONSOLE:</p>", unsafe_allow_html=True)
    
    st.components.v1.html(f"""
        <div style='background-color: #E8F8F5; border: 1px solid #A3E4D7; border-radius: 6px; padding: 10px; text-align: center;'>
            <audio controls style='width: 100%; height: 40px;'>
                <source src='data:audio/wav;base64,{raw_base64_string}' type='audio/wav'>
                Your browser does not support unblocked local element audio vectors.
            </audio>
        </div>
    """, height=65)
    
    st.download_button(label=f"📥 Download Your Verified Sound Take ({current_active_student_record['code']}.wav)", data=decoded_audio_bytes_payload, file_name=f"{current_active_student_record['code']}_Verified_Take.wav", mime="audio/wav")
except Exception as data_err:
    st.error(f"Linguistic file block corrupted format string structure ({data_err}).")

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
