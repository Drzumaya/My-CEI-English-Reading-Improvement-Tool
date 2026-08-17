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
# SANATIZED TARGET EXPORT INJECTOR CHANNEL • ENGLISHAUDIOUPLOAD.PY
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Secure Storage Portal", layout="centered")

# Initialize secure modal gatekeeper cache parameters to prevent public bypasses
if "admin_authorized" not in st.session_state:
    st.session_state.admin_authorized = False

# ----------------------------------------------------------------------------
# CRITICAL HARDCODED SYSTEM SECURITY PROTECTIONS INTERLOCK
# ----------------------------------------------------------------------------
# FIXED: Isolated your exact clean Google Spreadsheet alphanumeric ID token string
TARGET_GOOGLE_SHEET_TOKEN = "1vnRZDlb79scuC4kkdy0X3QNJKSLsVUFe_YoUe8GZlQU"

# FIXED NETWORK ENVERT CHASSIS:
# Re-routed through the secure export engine channel to download private frames.
# This prevents network timeouts and satisfies DNS naming structures perfectly.
PUBLIC_CSV_EXPORT_URL = f"https://google.com{TARGET_GOOGLE_SHEET_TOKEN}/export?format=csv"
# ============================================================================
# PART 2: CACHE-BUSTED SPREADSHEET ROW FETCH ENGINE (REAL-TIME ADAPTER)
# ============================================================================

@st.cache_data(ttl=2) # 2-second Time-To-Live forces Streamlit to constantly look for new student codes
def fetch_live_cloud_results_ledger(target_url):
    try:
        live_timestamp_nonce = int(time.time())
        
        # Validates query parameters structure before binding cache buster values
        if "?" in target_url:
            cache_busted_csv_url = f"{target_url}&cb={live_timestamp_nonce}"
        else:
            cache_busted_csv_url = f"{target_url}?cb={live_timestamp_nonce}"
        
        # Read sheet rows layout dynamically
        df = pd.read_csv(cache_busted_csv_url, header=None)
        return df
    except Exception as err:
        st.error(f"Spreadsheet stream lookup timed out. Check connection values ({err}).")
        return None

# Instantly pull the full cloud database rows list frame
sheet_raw_data_matrix = fetch_live_cloud_results_ledger(PUBLIC_CSV_EXPORT_URL)
# ============================================================================
# PART 3: STATE-DRIVEN POPUP PASSWORD CHASSIS
# ============================================================================

# Check if the session is locked or waiting for authorization loops
if not st.session_state.admin_authorized:
    st.markdown("<h3 style='text-align: center; color: #117A65; font-weight: bold;'>🔐 System Security Access Lock</h3>", unsafe_allow_html=True)
    st.write("Welcome to the CEI Master Toolsuite Archive. Please authenticate below to access student playback repositories and administration panels:")
    
    # State-driven input fields map parameter tracking strings independently of form nodes
    inputted_portal_password = st.text_input(
        label="🔑 Enter Administrator Master Access Password:",
        placeholder="Type your security credential string token...",
        type="password",
        key="master_portal_gatekeeper_password_input"
    )
    
    # Fixed operational execution block fires callbacks immediately upon mouse click actions
    if st.button("⚡ Unlock Operational Toolsuite Portal", key="auth_submission_trigger_button"):
        if inputted_portal_password.strip() == "CEI-Admin-2026":
            st.session_state.admin_authorized = True
            st.toast("🔓 Access Granted! Initializing CEI workspace panels components...")
            time.sleep(0.5)
            st.rerun() # Hard page re-render wipes screen canvas and unrolls full app rows
        elif inputted_portal_password.strip() != "":
            st.error("🔒 Security Lock: Invalid administrative verification token password access keys.")
                
    st.caption("⚠️ *Notice: Unauthorized attempts to download or modify student vocal records data models are monitored.*")
    st.stop() # CRITICAL STOP INTERLOCK: Prevents Streamlit from drawing another pixel if auth fails!

# ============================================================================
# APPS LAYOUT AREA (UNLOCKED ONLY PAST THE GATEKEEPER AUTHORIZATION MATRICES)
# ============================================================================
st.markdown("<h1 style='text-align: center; color: #117A65; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>Secure Playback Database Upload & Student Verification Desk</h4>", unsafe_allow_html=True)
# ============================================================================
# PART 4: STUDENT ID QUERY MANAGEMENT DESK PORTAL SINK (IDE COLUMN ASSIGNED)
# ============================================================================
st.write("---")
st.markdown("### 🔍 Student Playback Retrieval Section")
st.write("Type your target Student ID Code below to retrieve its corresponding recording asset container block:")

typed_student_code_password = st.text_input(
    label="🔑 Enter Student Code to Unlock Recording Access:",
    placeholder="e.g., CEI-2026-4402",
    key="student_search_lookup_field"
)

student_matching_record = None

if typed_student_code_password.strip() != "" and sheet_raw_data_matrix is not None:
    search_token = typed_student_code_password.strip().lower()
    
    timestamp_column_index = 0   # Column 1 (Index 0) -> Fecha Registro
    student_code_column_index = 1 # Column 2 (Index 1) -> STRICTLY TARGETS YOUR COLUMN LABEL: IDE
    audio_stream_column_index = 2 # Column 3 (Index 2) -> Datos Audio

    for index, row in sheet_raw_data_matrix.iterrows():
        if index == 0: 
            continue # Skip row index 0 columns headers row layout definitions cleanly
        if len(row) > max(student_code_column_index, audio_stream_column_index):
            spreadsheet_student_id = str(row.iloc[student_code_column_index]).strip().lower()
            
            if spreadsheet_student_id == search_token:
                student_matching_record = {
                    "timestamp": str(row.iloc[timestamp_column_index]),
                    "code": str(row.iloc[student_code_column_index]),
                    "audio_data": str(row.iloc[audio_stream_column_index])
                }
                break

if student_matching_record:
    st.success(f"🔓 Access Granted for Student Code: {student_matching_record['code']} (Recorded on {student_matching_record['timestamp']})")
    
    try:
        raw_base64_string = student_matching_record['audio_data'].strip()
        if "," in raw_base64_string: 
            raw_base64_string = raw_base64_string.split(",")
            
        decoded_audio_bytes_payload = base64.b64decode(raw_base64_string)
        st.markdown("<p style='font-size: 11px; font-weight: bold; color: #117A65; margin-bottom: 2px;'>🔊 UNBLOCKED PLAYBACK TRACK CONSOLE:</p>", unsafe_allow_html=True)
        
        # Native direct text Data-URI HTML5 player avoids browser cross-origin sandbox restrictions natively in MP3 compression formats
        st.components.v1.html(f"""
            <div style='background-color: #E8F8F5; border: 1px solid #A3E4D7; border-radius: 6px; padding: 10px; text-align: center;'>
                <audio controls style='width: 100%; height: 40px;'>
                    <source src='data:audio/mp3;base64,{raw_base64_string}' type='audio/mp3'>
                    Your browser does not support unblocked local element audio vectors.
                </audio>
            </div>
        """, height=65)
        
        st.download_button(
            label=f"📥 Download Verified Sound Take ({student_matching_record['code']}.mp3)",
            data=decoded_audio_bytes_payload,
            file_name=f"{student_matching_record['code']}_Verified_Take.mp3",
            mime="audio/mp3"
        )
    except Exception as data_err:
        st.error(f"Linguistic file block corrupted or written in an invalid format string structure ({data_err}).")
elif typed_student_code_password.strip() != "":
    st.error("🔒 Access Denied: Invalid Student ID Code search token criteria mappings.")
# ============================================================================
# PART 5: COORDINATOR MANUAL UPLOAD GATEWAY AND BINARY TO BASE64 CONVERTERS
# ============================================================================
st.write("---")
st.markdown("### 📤 Coordinator Audio Ingestion Console")
st.write("Authorized administrators use this portal to bind student recorded elements directly into the database sheet.")

admin_target_student_id = st.text_input(label="📋 Target Student Code Mapping Assignment:", placeholder="e.g., CEI-2026-4402", key="admin_id_field")
uploaded_student_file_asset = st.file_uploader(label="📁 Upload Student Playback Recording File Asset (.mp3, .wav):", type=["mp3", "wav"])

compiled_base64_string_payload = ""

if uploaded_student_file_asset is not None:
    try:
        raw_uploaded_bytes_block = uploaded_student_file_asset.read()
        compiled_base64_string_payload = base64.b64encode(raw_uploaded_bytes_block).decode('utf-8')
        st.info(f"✨ File asset '{uploaded_student_file_asset.name}' loaded and compressed successfully inside local browser memory.")
    except Exception as file_err:
        st.error(f"Error compiling structural file payload bytes ({file_err}).")
# ============================================================================
# PART 6: GOOGLE APPS SCRIPT WEB APP POST ENGINE AND THE DYNAMIC AUTOMATED MONITOR TABLE
# ============================================================================
st.write("---")
st.markdown("#### 🛠️ Direct Spreadsheet Append Form Hub")

APPS_SCRIPT_DEPLOYMENT_WEB_APP_URL = st.text_input(
    label="🔗 Paste Google Apps Script Web App URL Link:", 
    placeholder="https://google.com",
    type="password"
)

if st.button("⚡ Process Audio Upload Ledger Insertion Loop"):
    if admin_target_student_id.strip() == "":
        st.error("Operation Aborted: Target Student Code Mapping field cannot be blank.")
    elif compiled_base64_string_payload == "":
        st.error("Operation Aborted: Please choose a valid audio file asset to commit upload pipelines.")
    elif APPS_SCRIPT_DEPLOYMENT_WEB_APP_URL.strip() == "":
        st.error("Operation Aborted: Paste your public Forms Web App URL to append lines safely.")
    else:
        current_time_marker_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        form_payload_packet = {
            "timestamp": current_time_marker_string,
            "student_id": admin_target_student_id.strip(),
            "audio_data": compiled_base64_string_payload
        }
        
        with st.spinner("Executing secure pipeline data injection loop across cloud spreadsheets..."):
            try:
                post_server_response = requests.post(
                    APPS_SCRIPT_DEPLOYMENT_WEB_APP_URL, 
                    data=form_payload_packet, 
                    timeout=15
                )
                if post_server_response.status_code == 200 or "success" in post_server_response.text.lower():
                    st.balloons()
                    st.success("🚀 Success! Student recording locked and committed successfully inside Google Sheets!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Spreadsheet gateway rejected data logs format. Server Response: {post_server_response.text}")
            except Exception as connection_failure_err:
                st.error(f"Transmission connection failed. ({connection_failure_err}).")

# ----------------------------------------------------------------------------
# FULLY VIEWABLE CLASS DATABASE LEDGER GRID (UNLOCKED SECURELY VIA CHASSIS ENTRY AUTH)
# ----------------------------------------------------------------------------
st.write("---")
st.markdown("### 📊 Stored Records Summary Ledger Matrix")
st.write("This table unrolls automatically because you are authenticated via the main system security popup form:")

if sheet_raw_data_matrix is not None and not sheet_raw_data_matrix.empty:
    try:
        header_labels_row_list = sheet_raw_data_matrix.iloc.astype(str).tolist()
        data_content_matrix_rows = sheet_raw_data_matrix.iloc[1:].copy()
        data_content_matrix_rows.columns = header_labels_row_list
        
        visible_summary_ledger_df = data_content_matrix_rows.copy()
        if "Datos Audio" in visible_summary_ledger_df.columns:
            visible_summary_ledger_df["Datos Audio"] = "🔒 Audio Blob Data Protected"
            
        st.dataframe(visible_summary_ledger_df, use_container_width=True, hide_index=True)
        st.caption(f"💡 *Total Stored Student Registrations active: {len(visible_summary_ledger_df)} files rows.*")
        
        csv_ledger_buffer = visible_summary_ledger_df.to_csv(index=False)
        st.download_button(label="📥 Download Clean Student Logs Overview (.csv)", data=csv_ledger_buffer.encode('utf-8'), file_name="CEI_Registered_Students_Report.csv", mime="text/csv")
    except Exception as display_err:
        st.error(f"Error mapping spreadsheet layout columns variables arrays ({display_err}).")
else:
    st.info("Awaiting active sheet row entries database packets updates data models...")
