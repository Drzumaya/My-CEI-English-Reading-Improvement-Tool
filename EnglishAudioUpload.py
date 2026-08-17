import streamlit as st
import pandas as pd
import base64
import requests
import io
import time

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 6 STANDALONE PARTS
# PART 1: EXTENSION PACKAGE MANAGERS, WEB GEOMETRIES, & MASTER SESSION CACHES
# STRICT SECOND-COLUMN POSITIONAL LOCK • CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Secure Upload Gateway", layout="centered")
st.markdown("<h1 style='text-align: center; color: #117A65; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>Secure Playback Database Upload & Student Verification Desk</h4>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# CRITICAL HARDCODED SYSTEM SECURITY PROTECTIONS INTERLOCK
# ----------------------------------------------------------------------------
# Replace this token with your exact long Google Spreadsheet alphanumeric ID string.
TARGET_GOOGLE_SHEET_ID = "1-2BcRqA0typAluQO2F8snEfwyCWaHgOEhp0x0YiiTo9xnsKbreEibH0hSUE6EigvFg"

# Public streaming ledger export channel
PUBLIC_CSV_EXPORT_URL = f"https://google.com{TARGET_GOOGLE_SHEET_ID}/pub?output=csv"
# ============================================================================
# PART 2: DYNAMIC SPREADSHEET LEDGER ROW CONVERTERS AND MEMORY MATRICES
# ============================================================================

@st.cache_data(ttl=3) # Short cache validation window checks for incoming row updates quickly
def fetch_cloud_upload_ledger(target_url):
    try:
        live_timestamp_nonce = int(time.time())
        cache_busted_url = f"{target_url}&cb={live_timestamp_nonce}"
        # Read the sheet raw layout without assuming default numeric header assignments
        df = pd.read_csv(cache_busted_url, header=None)
        return df
    except Exception as err:
        st.error(f"Spreadsheet connection timed out. Verify your Sheet ID sharing configurations ({err}).")
        return None

# Load the dynamic dataset from your active sheet infrastructure
sheet_raw_data_matrix = fetch_cloud_upload_ledger(PUBLIC_CSV_EXPORT_URL)
# ============================================================================
# PART 3: STUDENT PASSWORD VERIFICATION CORE & UNBLOCKED HTML5 STREAM LAYOUTS
# ============================================================================
st.write("---")
st.markdown("### 🔐 Student Playback Security Portal")
st.write("Please type your official Student ID Code below to act as your verification password:")

# EXACT TARGET PASSING PROMPT SPECIFICATION ENFORCED
typed_student_code_password = st.text_input(
    label="🔑 Enter Student Code to Unlock Recording Access:",
    placeholder="e.g., CEI-2026-4402",
    type="password"  # Obfuscates input strings for data privacy security compliance rules
)

student_matching_record = None

if typed_student_code_password.strip() != "" and sheet_raw_data_matrix is not None:
    search_token = typed_student_code_password.strip().lower()
    
    # ----------------------------------------------------------------------------
    # STRICT SECOND-COLUMN POSITIONAL INTERLOCK (CÓDIGO ESTUDIANTE TARGETS):
    # Force-binds the password checker loop directly into the 2nd column (index 1)
    # ----------------------------------------------------------------------------
    timestamp_column_index = 0   # Column 1 (Index 0) -> Fecha Registro
    student_code_column_index = 1 # Column 2 (Index 1) -> STRICT: Código Estudiante
    audio_stream_column_index = 2 # Column 3 (Index 2) -> Datos Audio

    # Loop through the spreadsheet rows starting past the header cell titles row index
    for index, row in sheet_raw_data_matrix.iterrows():
        if index == 0: 
            continue # Skip row index 0 labels row cleanly
        if len(row) > max(student_code_column_index, audio_stream_column_index):
            spreadsheet_student_id = str(row.iloc[student_code_column_index]).strip().lower()
            
            # Match current row token directly with typed password criteria vectors
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
            raw_base64_string = raw_base64_string.split(",")[1]
            
        decoded_audio_bytes_payload = base64.b64decode(raw_base64_string)
        st.markdown("<p style='font-size: 11px; font-weight: bold; color: #117A65; margin-bottom: 2px;'>🔊 UNBLOCKED PLAYBACK TRACK CONSOLE:</p>", unsafe_allow_html=True)
        
        # HTML5 web container player bypasses dynamic platform cross-origin mutes cleanly
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
    st.error("🔒 Access Denied: Invalid Student ID Code password. Recording asset not found inside database rows.")
# ============================================================================
# PART 4: COORDINATOR MANUAL UPLOAD GATEWAY AND BINARY TO BASE64 CONVERTERS
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
# PART 5: GOOGLE APPS SCRIPT FORM-POSTER WEB APP ENGINE CONNECTOR
# ============================================================================
st.markdown("#### 🛠️ Direct Spreadsheet Append Form Hub")
st.write("Provide your public Google Apps Script deployment URL link to send rows data down to the master sheet:")

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
                    st.success(f"🚀 Success! Student recording locked and committed under ID Code '{admin_target_student_id}' successfully inside Google Sheets!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Spreadsheet gateway rejected data row entry logic logs format. Server Response: {post_server_response.text}")
            except Exception as connection_failure_err:
                st.error(f"Transmission connection failed. Confirm Web App permissions parameters are deployed to 'Anyone' ({connection_failure_err}).")
# ============================================================================
# PART 6: COMPREHENSIVE GOOGLE APPS SCRIPT MACRO BLUEPRINT SPECIFICATION CODE
# ============================================================================
st.write("---")
st.markdown("### 📝 6. Required Google Apps Script Backend Setup Manual")
st.write("To handle row writing requests matching your exact column layouts, deploy this custom code block:")

apps_script_instructions_manual_text = """
1. Open your target Google Spreadsheet layout window.
2. Confirm row 1 header structures match column assignments: 
   * Cell **A1** -> `Fecha Registro`
   * Cell **B1** -> Exactly **`Código Estudiante`** (Your specified matching password anchor column)
   * Cell **C1** -> `Datos Audio`
3. Click **Extensions** inside top dashboard menu bar rows -> Open **Apps Script** window.
4. Delete all existing code text content inside the editor panel completely and paste this exact macro block script:

```javascript
function doPost(e) {
  var targetSpreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var masterSheetLedger = targetSpreadsheet.getSheets()[0]; // Targets first worksheet tab index row channels
  
  var timestampValue = e.parameter.timestamp;
  var studentIdCode   = e.parameter.student_id;
  var audioBase64Data = e.parameter.audio_data;
  
  // Appends fields straight into columns under your exact matching tracking header cells rows labels!
  masterSheetLedger.appendRow([timestampValue, studentIdCode, audioBase64Data]);
  
  return ContentService.createTextOutput(JSON.stringify({"result": "success"}))
                       .setMimeType(ContentService.MimeType.JSON);
}
```
5. Click **Deploy** -> **New Deployment**.
6. Select type: **Web App**.
7. Set **Execute as**: *Me (Your account)*.
8. Set **Who has access**: Change to **Anyone**. (Crucial for Streamlit cloud scripts communication).
9. Click **Deploy**, authorize permissions, copy the generated **Web App URL**, and paste it into the panel input window above.
"""
st.markdown(apps_script_instructions_manual_text)
