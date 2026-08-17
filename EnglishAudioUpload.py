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
# FIXED PUBLISHED WEB-TOKEN INFRASTRUCTURE ENGINE • MYCEIUPLOADEDFILES.PY
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Secure Storage Portal", layout="centered")
st.markdown("<h1 style='text-align: center; color: #117A65; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>Secure Playback Database Upload & Student Verification Desk</h4>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# CRITICAL HARDCODED SYSTEM SECURITY PROTECTIONS INTERLOCK
# ----------------------------------------------------------------------------
# FIXED: Assigned your exact long Google Web Publication Key Token String cleanly
TARGET_GOOGLE_SHEET_TOKEN = "2PACX-1vR14gLuF0ogpRIDP_OGmAff4akh2JdUKLVawIgBVd4AJhK796f1-uonX-2aLVaIW2nFtzyGsWe0yCLP"

# FIXED NETWORK ENVERT: Corrected path destination route mapping to unblock database rows streaming channels
PUBLIC_CSV_EXPORT_URL = f"https://google.com{TARGET_GOOGLE_SHEET_TOKEN}/pub?output=csv"
# ============================================================================
# PART 3: STUDENT PASSWORD VERIFICATION CORE & UNBLOCKED HTML5 STREAM LAYOUTS
# ============================================================================
st.write("---")
st.markdown("### 🔐 Student Playback Security Portal")
st.write("Please type your official Student ID Code below to act as your verification password:")

typed_student_code_password = st.text_input(
    label="🔑 Enter Student Code to Unlock Recording Access:",
    placeholder="e.g., CEI-2026-4402",
    type="password"
)

student_matching_record = None

if typed_student_code_password.strip() != "" and sheet_raw_data_matrix is not None:
    search_token = typed_student_code_password.strip().lower()
    
    timestamp_column_index = 0   # Column 1 (Index 0) -> Fecha Registro
    student_code_column_index = 1 # Column 2 (Index 1) -> STRICT: Código Estudiante
    audio_stream_column_index = 2 # Column 3 (Index 2) -> Datos Audio

    # Loop through the spreadsheet rows starting past the header cell titles row index
    for index, row in sheet_raw_data_matrix.iterrows():
        if index == 0: 
            continue # Skip row index 0 cleanly
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
            raw_base64_string = raw_base64_string.split(",")
            
        decoded_audio_bytes_payload = base64.b64decode(raw_base64_string)
        st.markdown("<p style='font-size: 11px; font-weight: bold; color: #117A65; margin-bottom: 2px;'>🔊 UNBLOCKED PLAYBACK TRACK CONSOLE:</p>", unsafe_allow_html=True)
        
        # HTML5 web container player bypasses dynamic platform cross-origin mutes cleanly using native MP3 formatting
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
# PART 6: LIVE SPREADSHEET MONITOR GRID TABLE AND ACCESS KEYS INTERLOCK
# ============================================================================
st.write("---")
st.markdown("### 📊 Coordinator Administrative Results Monitor Ledger")
st.write("Unlock this panel view option to verify compiled rows currently stored inside your cloud database spreadsheet:")

admin_panel_access_password_token = st.text_input(
    label="🔒 Enter Administrator Access Password to Display Ledger Results Table:",
    placeholder="Enter admin dashboard token keys...",
    type="password"
)

if admin_panel_access_password_token.strip() == "CEI-Admin-2026":
    st.success("🔓 Administrative Access Cleared! Compiling stored sheet entries rows...")
    
    if sheet_raw_data_matrix is not None and not sheet_raw_data_matrix.empty:
        try:
            # Reconstruct columns structures using row index 0 names mappings labels
            header_labels_row_list = sheet_raw_data_matrix.iloc[0].astype(str).tolist()
            
            # Slice row arrays past indices boundary fields 
            data_content_matrix_rows = sheet_raw_data_matrix.iloc[1:].copy()
            data_content_matrix_rows.columns = header_labels_row_list
            
            # Formats clean output grids by stripping raw base64 column string blocks text out-of-screen
            visible_summary_ledger_df = data_content_matrix_rows.copy()
            if "Datos Audio" in visible_summary_ledger_df.columns:
                visible_summary_ledger_df["Datos Audio"] = "🔒 Audio Blob Data Protected"
                
            st.markdown("**📂 LIVE AUTOMATED DATABASE COHORT REGISTER MATRIX (STORES AUTOMATICALLY):**")
            st.dataframe(visible_summary_ledger_df, use_container_width=True, hide_index=True)
            
            st.caption(f"💡 *Total Stored Student Registrations active: {len(visible_summary_ledger_df)} files rows.*")
            
            # Provide direct download ledger backup channel option
            csv_ledger_buffer = visible_summary_ledger_df.to_csv(index=False)
            st.download_button(label="📥 Download Clean Student Logs Overview (.csv)", data=csv_ledger_buffer.encode('utf-8'), file_name="CEI_Registered_Students_Report.csv", mime="text/csv")
            
        except Exception as display_err:
            st.error(f"Error mapping spreadsheet layout columns variables arrays ({display_err}).")
    else:
        st.info("Awaiting active sheet row entries database packets updates data models...")
elif admin_panel_access_password_token.strip() != "":
    st.error("🔒 Security Lock: Invalid administrative verification token password access keys.")
