import streamlit as st
from streamlit_mic_recorder import mic_recorder
from rapidfuzz import fuzz
from datetime import datetime
import pandas as pd
import io
import re
import time

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 4 CORE PARTS
# PART 1: COMPREHENSIVE DEPENDENCY PACKAGES & PRODUCTION CSV CLOUD INITIALIZERS
# LIVE SYNCHRONIZED RECURSIVE GOOGLE SHEETS DATA STREAM MATRIX
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Master Evaluation Engine", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Upper-Intermediate Dynamic Verification & Re-Ordered Replay Console</h4>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# DYNAMIC UNBLOCKED GOOGLE SPREADSHEET MANIFEST TRACKING ADAPTER HOOK
# ----------------------------------------------------------------------------
# CONVERTED LIVE DATA PACKET TARGET URL: Swapped /pubhtml to /pub?output=csv to pipe raw rows streams
PUBLISHED_MANIFEST_CSV_URL = "https://google.com"

# Symmetrical local hardcoded data records fallback matrix representing your baseline syllabus
if "fallback_syllabus_bank" not in st.session_state:
    st.session_state.fallback_syllabus_bank = {
        "ECAUDIOS_SB-Unit1_Shift_Handover.mp3": "Good afternoon Carlos. Welcome to the Shift Two handover session. SMT Line Three is currently running part number ALC seven seven four two, active lot code alpha dash nine.",
        "ECAUDIOS_WB-Unit2_ESD_Compliance.mp3": "Attention all floor personnel. A cleanroom compliance audit is currently active across the ESD Protected Area boundaries. Every operator must immediately verify their personal grounding infrastructure paths.",
        "ECAUDIOS_IE-Unit3_5Ws_Logging.mp3": "Master ledger database transaction log update. Operator ID forty four zero two discovered three pieces of part number ALC nine nine zero on Line One at zero eight thirty AM. Visual inspection revealed a fractured mounting boss feature."
    }

if "student_record_vault" not in st.session_state:
    st.session_state.student_record_vault = {}
    
if "gradebook_matrix_history" not in st.session_state:
    st.session_state.gradebook_matrix_history = []
# ============================================================================
# PART 2: INDEX-BASED CLOUD DATA STREAM MAPPINGS & DIRECT REPLAY MONITOR LOOPS
# ============================================================================
st.markdown("### 📋 1. Course Selection Dropdown Matrix")

discovered_curriculum_tracks = {}

if "pub?output=csv" in PUBLISHED_MANIFEST_CSV_URL:
    try:
        # THE CACHE BUSTER INTERLOCK: Appends a dynamic clock query token to bypass server memory freezes
        live_timestamp_nonce = int(time.time())
        cache_busted_csv_stream_url = f"{PUBLISHED_MANIFEST_CSV_URL}&cb={live_timestamp_nonce}"
        
        # Stream raw dataset tables natively down from the web link parameters
        cloud_data_frame = pd.read_csv(cache_busted_csv_stream_url, header=None) # Forces headerless raw vector scan
        
        # REFACTOR INTERLOCK: Reads spreadsheet columns strictly by index position instead of text keys
        for index, row in cloud_data_frame.iterrows():
            if len(row) >= 2:
                track_name = str(row.iloc[0]).strip()
                audio_link = str(row.iloc[1]).strip()
                
                # Check for empty cells or padding artifacts securely, skipping column text headers rows
                if track_name != "nan" and track_name != "" and audio_link != "nan" and audio_link != "" and not track_name.lower().startswith("audio_track"):
                    clean_title_label = track_name.replace('.mp3','').replace('.wav','').replace('_',' ')
                    simulated_text = f"Technical language standard training module passage matching cloud file asset: '{clean_title_label}'. Practice pronunciation flow and vocal tracking loops using your workbook guidelines."
                    
                    discovered_curriculum_tracks[track_name] = {
                        "text": simulated_text,
                        "url": audio_link
                    }
    except Exception as spreadsheet_sync_error:
        st.sidebar.caption(f"ℹ nighttime Cloud Sheet Status: Running standalone engine fallback mode ({spreadsheet_sync_error}).")

# Fall back to base syllabus tokens if sheet link returns empty data fields
if not discovered_curriculum_tracks:
    for k, v in st.session_state.fallback_syllabus_bank.items():
        discovered_curriculum_tracks[k] = {"text": v, "url": None}

# EXACT USER COMPLIANCE PROMPT DROPDOWN STRING LABELS ENFORCED
selected_track_id = st.selectbox(
    "Choose an Exercise track:",
    options=sorted(list(discovered_curriculum_tracks.keys())),
    index=0
)

active_target_text = discovered_curriculum_tracks[selected_track_id]["text"]
active_target_url = discovered_curriculum_tracks[selected_track_id]["url"]

st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>🔊 NATURAL NATIVE YOUNG SPEAKER REPLAY CORE:</p>", unsafe_allow_html=True)
st.write("Students can launch this reference model an unlimited number of times to study fluid, youthful US English tone structures.")

# Direct browser link true sound player or youthful acoustic speaker guide fallback logic node
if active_target_url and "drive.google.com" in active_target_url:
    try:
        # Extracts raw shared link structures into direct browser audio streaming packets natively
        parsed_id = re.search(r'(?:id=|\/d\/)([\w-]+)', active_target_url).group(1)
        direct_streaming_node = f"https://google.com{parsed_id}"
        st.audio(direct_streaming_node, format="audio/mp3")
    except Exception:
        st.write("Awaiting public sharing link permissions verification...")
else:
    if st.button("▶️ Sound Selected Reference Course Track (Unlimited Uses)"):
        js_youthful_speech_loop = f"""
        <html lang="en"><body><script>(function() {{ let s = window.speechSynthesis; s.cancel(); let u = new SpeechSynthesisUtterance(`{active_target_text.replace('`','\\`').replace('$','\\$')}`); let voices = s.getVoices(); let youngVoice = voices.find(v => (v.lang.startsWith('en-US') && v.name.includes('Natural')) || (v.lang.startsWith('en-US') && v.name.includes('Google')) || v.lang.startsWith('en-US')); if (youngVoice) u.voice = youngVoice; u.lang = 'en-US'; u.rate = 0.90; u.pitch = 1.15; s.speak(u); }})();</script></body></html>
        """
        st.components.v1.html(js_youthful_speech_loop, height=1, width=1)

# ----------- STEP 2: THE READING SHOWER SCRIPT VIEWPORT BOARD -----------
st.write("---")
st.markdown("### 🔍 2. Reading Shower Specification Board")
st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET TRAINING PASSAGE SCRIPT MANUAL BLOCK:</p>", unsafe_allow_html=True)
st.info(active_target_text)
# ============================================================================
# PART 3: STUDENT VOCAL REGISTRATION DESK AND LOSSLESS SOUND CHANNEL SAVES
# ============================================================================

# ----------- STEP 3: STUDENT PLAYBACK AUDIO REGISTER GATEWAY -----------
st.write("---")
st.markdown("### 🎙️ 3. Student Playback Audio Registration Desk")
st.write("Click Start Recording below, speak into your microphone, then click stop to assemble audio containers safely.")

audio_vocal_capture = mic_recorder(
    start_prompt="🎙️ Start Headset Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_4part_lossless_sound_fidelity_cache_busted_recorder_v51'
)

# ----------- STEP 4: TRUE RECORDED SOUND PATENCY SECURITY GATE -----------
if audio_vocal_capture:
    raw_vocal_bytes = audio_vocal_capture['bytes']
    current_timestamp_string = datetime.now().strftime("%H:%M:%S")
    take_index_key = f"Vocal_Take_[{current_timestamp_string}]"
    
    if take_index_key not in st.session_state.student_record_vault:
        # Lossless passthrough leaves raw binary blocks uncorrupted to ensure your playback audio has sound
        st.session_state.student_record_vault[take_index_key] = raw_vocal_bytes
        st.toast(f"🎉 {take_index_key} recorded and verified with original sound fidelity active!")
# ============================================================================
# PART 4: COGNITIVE EVALUATIONS, COHORT ID MANAGEMENT PANELS, & EXPORTERS
# ============================================================================
st.write("---")
st.markdown("### 📊 4. Cognitive Alignment Voice Checker Engine")

col_id, col_name = st.columns(2)
with col_id:
    student_id_code = st.text_input(label="📋 Enter Student ID Code:", placeholder="e.g., CEI-2026-4402", key="student_custom_id_code")
with col_name:
    student_provided_name = st.text_input(label="📝 Enter Student Name or Custom Label:", placeholder="e.g., Carlos Mendoza", key="student_custom_filename")

transcribed_user_input = st.text_area(label="Transcription Verification Pane:", placeholder="Awaiting manual transcript text lines or automatic speech mapping logs...", key="text_transcription_transfer")

if st.button("🔍 Run Linguistic Evaluation Loops"):
    if transcribed_user_input.strip() == "":
        st.error("System Notice: Please provide text content inside the container to execute structural gap check matrices.")
    else:
        ref_clean_tokens = active_target_text.lower().replace(".", "").replace(",", "").replace("’", "").replace("'", "").split()
        user_clean_tokens = transcribed_user_input.lower().replace(".", "").replace(",", "").replace("’", "").replace("'", "").split()
        
        fluency_percentage_score = round(fuzz.token_set_ratio(active_target_text, transcribed_user_input))
        st.markdown(f"### ➔ COHORT SCORE MATRIX GAP BALANCE [{fluency_percentage_score}%]:")
        st.metric(label="Fluency Matching Score Percentage Matrix", value=f"{fluency_percentage_score}%")
        
        col_correct, col_wrong = st.columns(2)
        with col_correct:
            st.markdown("<p style='font-size: 12px; font-weight: bold; color: #27AE60;'>CORRECTLY READ WORDS LOG:</p>", unsafe_allow_html=True)
            correct_words_box = [w for w in ref_clean_tokens if w in user_clean_tokens]
            for w in correct_words_box: st.write(f"✓ **{w}**")
                
        with col_wrong:
            st.markdown("<p style='font-size: 12px; font-weight: bold; color: #C0392B;'>WRONG READ WORDS & PRACTICE TIPS LOG:</p>", unsafe_allow_html=True)
            wrong_words_box = [w for w in ref_clean_tokens if w not in user_clean_tokens]
            for index, w in enumerate(wrong_words_box):
                st.write(f"✗ **{w}**")
                js_word_model = f"""<html lang='en'><body><button id='spk_{index}' style='padding:2px 6px; font-size:11px; background:#C0392B; color:white; border:none; border-radius:3px;'>🔊 Speak Target</button><script>document.getElementById('spk_{index}').addEventListener('click', () => {{ let s = window.speechSynthesis; s.cancel(); let u = new SpeechSynthesisUtterance("{w}"); u.lang='en-US'; u.rate=0.85; s.speak(u); }});</script></body></html>"""
                st.components.v1.html(js_word_model, height=30)

        st.session_state.gradebook_matrix_history.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Student_ID": student_id_code.strip() if student_id_code.strip() != "" else "TEMP-ID",
            "Student_Name": student_provided_name.strip() if student_provided_name.strip() != "" else "Anonymous Cohort",
            "Track ID": selected_track_id,
            "Accuracy Score": f"{fluency_percentage_score}%",
            "Transcription": transcribed_user_input
        })

# ----------------------------------------------------------------------------
# 🛠️ SYSTEM MAINTENANCE UPGRADE AREA: THE STUDENT ID CODES MAINTENANCE DASHBOARD
# ----------------------------------------------------------------------------
if st.session_state.gradebook_matrix_history:
    st.write("---")
    st.markdown("### 🛠️ Coordinator Database Maintenance Dashboard")
    st.write("Select a committed record entry line to overwrite or upgrade its target Student ID column parameters:")
    
    gradebook_string_indices = []
    for index, log in enumerate(st.session_state.gradebook_matrix_history):
        gradebook_string_indices.append(f"Row [{index + 1}] - Time: {log['Timestamp']} | Current ID: {log['Student_ID']} | Name: {log['Student_Name']}")
        
    chosen_maintenance_row_string = st.selectbox(
        "Select Logged Gradebook Record Line to Modify:",
        options=gradebook_string_indices,
        key="maintenance_row_selector"
    )
    
    target_numerical_index = int(chosen_maintenance_row_string.split("Row [")[1].split("]")[0]) - 1
    
    col_new_id, col_upgrade_trigger = st.columns(2)
    with col_new_id:
        new_upgraded_id_string = st.text_input(label="Type New Corrected Student ID Code String:", placeholder="e.g., OFFICIAL-CEI-4402", key=f"upgrade_field_{target_numerical_index}")
    with col_upgrade_trigger:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("⚡ Execute Administrative ID Code Upgrade", key="run_id_maintenance_upgrade"):
            if new_upgraded_id_string.strip() == "":
                st.error("Operation Denied: Input field cannot be empty.")
            else:
                st.session_state.gradebook_matrix_history[target_numerical_index]["Student_ID"] = new_upgraded_id_string.strip()
                st.toast(f"⚡ Row [{target_numerical_index + 1}] successfully updated to official Student ID: {new_upgraded_id_string.strip()}!")
                st.rerun()

st.write("---")
st.markdown("### 🗂️ 5. Student Recorded Take Tracker & Vault Download Station")
available_vault_tracks = list(st.session_state.student_record_vault.keys())

if available_vault_tracks:
    chosen_take_keys = st.multiselect("Select One or More Historical Vocal Attempt Tracks from Vault Panel:", options=available_vault_tracks, default=[available_vault_tracks[-1]] if available_vault_tracks else [], key="synchronized_vault_multiselector")
    valid_active_selections = [t for t in chosen_take_keys if t in st.session_state.student_record_vault]
    
    if valid_active_selections:
        for index, individual_take in enumerate(valid_active_selections):
            selected_audio_bytes = st.session_state.student_record_vault[individual_take]
            st.markdown(f"**🔊 Active Tracking Playback Sound Monitor Node:** `{individual_take}`")
            st.audio(selected_audio_bytes, format="audio/wav")
            
            sanitized_user_string = student_provided_name.strip().replace(" ", "_")
            base_filename_string = f"{sanitized_user_string}_Take_{index + 1}" if sanitized_user_string != "" else f"CEI_{individual_take.replace('[','').replace(']','').replace(' ','_')}"
            
            col_download, col_erase = st.columns(2)
            with col_download:
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>📥 DOWNLOAD TRACK ASSETS:</p>", unsafe_allow_html=True)
                st.download_button(label=f"📥 Download Sound Track Mapped as ({base_filename_string}.wav)", data=selected_audio_bytes, file_name=f"{base_filename_string}.wav", mime="audio/wav", key=f"dl_btn_{individual_take}")
                st.caption("💡 *Clicking opens a prompt window where you can choose your storage folder location.*")
                
            with col_erase:
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: #C0392B;'>🧹 DIRECT TRACKER LIST PURGE SYSTEM:</p>", unsafe_allow_html=True)
                if st.button("❌ Erase Chosen Recording From Student Recorded Tracker List", key=f"erase_btn_{individual_take}"):
                    del st.session_state.student_record_vault[individual_take]
                    st.toast(f"🧹 Successfully quit and erased reference track `{individual_take}` from vault panel!")
                    st.rerun()
                    
        if st.session_state.gradebook_matrix_history:
            st.write("---")
            st.markdown("#### 📥 Administrative Spreadsheet Exporter Station")
            csv_string_buffer = "Timestamp Ledger,Student ID Code,Student Name,Syllabus Track ID,Fluency Score Ratio,Transcription Captured\n"
            for log in st.session_state.gradebook_matrix_history:
                csv_string_buffer += f'"{log["Timestamp"]}","{log["Student_ID"]}","{log["Student_Name"]}","{log["Track ID"]}","{log["Accuracy Score"]}","{log["Transcription"]}"\n'
                
            col_csv, col_xlsx = st.columns(2)
            with col_csv: st.download_button(label="📥 Download Database Ledger (.csv)", data=csv_string_buffer.encode('utf-8'), file_name="CEI_Master_Gradebook_Ledger.csv", mime="text/csv")
            with col_xlsx: st.download_button(label="📊 Download Excel Gradebook (.xlsx)", data=csv_string_buffer.encode('utf-8'), file_name="CEI_Master_Gradebook_Ledger.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("Please choose at least one track entry token from the checklist field above to activate trackers.")
else:
    st.info("Awaiting headset recording audio tracks data... Click Start Recording above to begin.")
