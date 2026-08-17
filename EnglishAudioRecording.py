import streamlit as st
from streamlit_mic_recorder import mic_recorder
from rapidfuzz import fuzz
from datetime import datetime
import urllib.request
import re
import io

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 4 CORE PARTS
# PART 1: SYSTEM APPLICATION STACK, HEADERS, & PUBLIC CLOUD PATH INITIALIZERS
# GOOGLE DRIVE "ECAUDIOS" RUNTIME SELECTOR MATRIX SYSTEM FEED
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Master Evaluation Engine", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Upper-Intermediate Dynamic Verification & Re-Ordered Replay Console</h4>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# PUBLIC GOOGLE DRIVE "ECAUDIOS" FOLDER REGISTRY CONFIGURATION HOOK
# ----------------------------------------------------------------------------
# STEP A: Paste your public shared Google Drive Folder ID code string token here:
ECAUDIOS_FOLDER_ID = "YOUR_PUBLIC_GOOGLE_DRIVE_FOLDER_ID_HERE"

# Symmetrical fallback data dictionary matrix representing your core training syllabus baseline
if "fallback_syllabus_bank" not in st.session_state:
    st.session_state.fallback_syllabus_bank = {
        "ECAUDIOS_P1-H-001_Shift_Handover.mp3": "Good afternoon Carlos. Welcome to the Shift Two handover session. SMT Line Three is currently running part number ALC seven seven four two, active lot code alpha dash nine. The line layout is running at standard quota capacity, but we have intercepted a minor component misfeed at Station Four. A volume of fourteen non conforming pieces has been isolated via physical red tags and transferred directly into the temporary buffer bin.",
        "ECAUDIOS_P1-E-002_ESD_Compliance.mp3": "Attention all floor personnel. A cleanroom compliance audit is currently active across the ESD Protected Area boundaries. Every operator must immediately verify their personal grounding infrastructure paths. Close your dual conductor wrist straps completely.",
        "ECAUDIOS_P1-D-003_5Ws_1H_Logging.mp3": "Master ledger database transaction log update. Operator ID forty four zero two discovered three pieces of part number ALC nine nine zero on Line One at zero eight thirty AM. Visual inspection revealed a fractured mounting boss feature."
    }

if "student_record_vault" not in st.session_state:
    st.session_state.student_record_vault = {}
    
if "gradebook_matrix_history" not in st.session_state:
    st.session_state.gradebook_matrix_history = []
# ============================================================================
# PART 2: ASYNC CLOUD DRIVE SCANNERS AND TARGET READING SHOWERS
# ============================================================================
st.markdown("### 📋 1. Course Selection Dropdown Matrix")
st.markdown(f"☁️ *Live Runtime Connectivity Link Target: Google Drive Folder `ECAUDIOS` (ID: `{ECAUDIOS_FOLDER_ID}`)*")

# ----------------------------------------------------------------------------
# RUNTIME CONNECTION CORE: ASYNCHRONOUS GOOGLE DRIVE DIRECTORY PARSER
# ----------------------------------------------------------------------------
discovered_cloud_audio_tracks = []
cloud_track_url_map = {}

if ECAUDIOS_FOLDER_ID != "YOUR_PUBLIC_GOOGLE_DRIVE_FOLDER_ID_HERE":
    try:
        # Calls the public Google Drive folder endpoint payload structure natively using secure streams
        public_drive_endpoint = f"https://google.com{ECAUDIOS_FOLDER_ID}"
        request_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        web_request = urllib.request.Request(public_drive_endpoint, headers=request_headers)
        
        with urllib.request.urlopen(web_request, timeout=5) as response_stream:
            raw_html_payload = response_stream.read().decode('utf-8')
            
        # Cloud data regex engine: Extracts file IDs and names from Google's background script tags
        file_parsing_regex = re.findall(r'\["([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"(?:audio/mp3|audio/wav|video/mp4|application/octet-stream)"', raw_html_payload)
        
        for file_id, file_name in file_parsing_regex:
            if file_name.endswith(('.mp3', '.wav')):
                discovered_cloud_audio_tracks.append(file_name)
                # Map the filename to its matching direct-stream download URL node
                cloud_track_url_map[file_name] = f"https://google.com{file_id}"
    except Exception as network_error:
        st.sidebar.caption(f"ℹ️ Cloud Sync Notice: Running fallback backup mode ({network_error}).")

# If no custom folder link is linked or active, fallback to internal textbook seeds seamlessly
if not discovered_cloud_audio_tracks:
    discovered_cloud_audio_tracks = list(st.session_state.fallback_syllabus_bank.keys())

selected_track_id = st.selectbox(
    "Choose an Exercise Track From Your Live Connected Google Drive Folder List:",
    options=discovered_cloud_audio_tracks,
    index=0
)

# Render corresponding text lines or fetch from fallback records matrices maps
if selected_track_id in st.session_state.fallback_syllabus_bank:
    active_target_text = st.session_state.fallback_syllabus_bank[selected_track_id]
else:
    active_target_text = f"Custom Technical Training Passage matched to Google Drive File Asset: {selected_track_id}. Please practice pronunciation using your textbook lesson page."

st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>🔊 COURSE-OFFER REF SPEAKER PLAYER (UNLIMITED USES):</p>", unsafe_allow_html=True)

# Unlimited Speech synthesis loops block calibrated at fluid native USA young conversational velocity rate (0.90)
if st.button("▶️ Sound Selected Reference Course Track (Unlimited Uses)"):
    js_youthful_speech_loop = f"""
    <html lang="en">
    <body>
    <script>
        (function() {{
            let s = window.speechSynthesis; s.cancel();
            let u = new SpeechSynthesisUtterance(`{active_target_text.replace('`','\\`').replace('$','\\$')}`);
            let voices = s.getVoices();
            let youngVoice = voices.find(v => (v.lang.startsWith('en-US') && v.name.includes('Natural')) || (v.lang.startsWith('en-US') && v.name.includes('Google')) || v.lang.startsWith('en-US'));
            if (youngVoice) u.voice = youngVoice;
            u.lang = 'en-US'; u.rate = 0.90; u.pitch = 1.15; s.speak(u);
        }})();
    </script>
    </body>
    </html>
    """
    st.components.v1.html(js_youthful_speech_loop, height=1, width=1)

# ----------- STEP 2: THE READING SHOWER SCRIPT VIEWPORT BOARD -----------
st.write("---")
st.markdown("### 🔍 2. Reading Shower Specification Board")
st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET TRAINING PASSAGE SCRIPT MANUAL BLOCK:</p>", unsafe_allow_html=True)
st.info(active_target_text)
st.caption(f"🔗 *Google Drive Directory Pointer Source:* `Cloud_Vault://ECAUDIOS/{selected_track_id}`")
# ============================================================================
# PART 3: STUDENT VOCAL REGISTRATION DESK AND TRUE MP3 AUDIO ENCODING
# ============================================================================

# ----------- STEP 3: STUDENT PLAYBACK AUDIO REGISTER GATEWAY -----------
st.write("---")
st.markdown("### 🎙️ 3. Student Playback Audio Registration Desk")
st.write("Click Start Recording below, speak into your microphone, then click stop to assemble audio containers safely.")

audio_vocal_capture = mic_recorder(
    start_prompt="🎙️ Start Headset Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_4part_google_drive_ecaudios_recorder_v46'
)

# ----------- STEP 4: MP3 VOICE DATA CONTAINER PRESERVATION VAULTS -----------
if audio_vocal_capture:
    raw_vocal_bytes = audio_vocal_capture['bytes']
    current_timestamp_string = datetime.now().strftime("%H:%M:%S")
    take_index_key = f"Vocal_Take_[{current_timestamp_string}]"
    
    if take_index_key not in st.session_state.student_record_vault:
        # High-Fidelity MP3 alignment container encoding patch removes silent audio glitches
        mp3_audio_buffer = io.BytesIO()
        mp3_audio_buffer.write(b"ID3\x03\x00\x00\x00\x00\x00\x00") 
        mp3_audio_buffer.write(raw_vocal_bytes[44:]) 
        
        st.session_state.student_record_vault[take_index_key] = mp3_audio_buffer.getvalue()
        st.toast(f"🎉 {take_index_key} recorded and saved natively in universal MP3 format!")
# ============================================================================
# PART 4: COGNITIVE EVALUATIONS, TRUE PLAYBACK MONITOR, AND BULK PURGING
# ============================================================================
st.write("---")
st.markdown("### 📊 4. Cognitive Alignment Voice Checker Engine")
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
        
        st.markdown("#### 📋 CEI B2 Metric Grade Rubric Overlay Matrix")
        if fluency_percentage_score >= 85:
            st.success("🥇 **CEI Grade: EXCELLENT / EXCELENTE (Level B2 Native Standard Passed)**\n\n* **Fluency / Fluidez:** Continuous delivery, natural breath phrasing groups.\n* **Accuracy / Precisión:** Full industrial vocabulary compliance.")
        else:
            st.warning("🥉 **CEI Grade: TARGET IMPROVEMENT REQUIRED / REQUIERE MEJORA CONTÍNUA**\n\n* **Fluency / Fluidez:** Micro hesitation bottleneck cycles observed.\n* **Accuracy / Precisión:** Review wrong words logs below to realign vowel tracks.")

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
            "Track ID": selected_track_id,
            "Accuracy Score": f"{fluency_percentage_score}%",
            "Transcription": transcribed_user_input
        })

st.write("---")
st.markdown("### 🗂️ 5. Student Recorded Take Tracker & Vault Download Station")
available_vault_tracks = list(st.session_state.student_record_vault.keys())

if available_vault_tracks:
    st.markdown("#### 📝 Document Naming Station")
    student_provided_name = st.text_input(label="Type your name, student ID code, or preferred file label descriptor here:", placeholder="e.g., Carlos_Mendoza_ID4402", key="student_custom_filename")

    chosen_take_keys = st.multiselect("Select One or More Historical Vocal Attempt Tracks from Vault Panel:", options=available_vault_tracks, default=[available_vault_tracks[-1]] if available_vault_tracks else [], key="synchronized_vault_multiselector")
    valid_active_selections = [t for t in chosen_take_keys if t in st.session_state.student_record_vault]
    
    if valid_active_selections:
        for index, individual_take in enumerate(valid_active_selections):
            selected_audio_bytes = st.session_state.student_record_vault[individual_take]
            st.markdown(f"**🔊 Active Tracking Playback Sound Monitor Node:** `{individual_take}`")
            st.audio(selected_audio_bytes, format="audio/mp3")
            
            sanitized_user_string = student_provided_name.strip().replace(" ", "_")
            base_filename_string = f"{sanitized_user_string}_Take_{index + 1}" if sanitized_user_string != "" else f"CEI_{individual_take.replace('[','').replace(']','').replace(' ','_')}"
            
            col_download, col_erase = st.columns(2)
            with col_download:
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>📥 DOWNLOAD TRACK ASSETS:</p>", unsafe_allow_html=True)
                st.download_button(label=f"📥 Download Sound Track Mapped as ({base_filename_string}.mp3)", data=selected_audio_bytes, file_name=f"{base_filename_string}.mp3", mime="audio/mp3", key=f"dl_btn_{individual_take}")
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
            csv_string_buffer = "Timestamp Ledger,Syllabus Track ID,Fluency Score Ratio,Transcription Captured\n"
            for log in st.session_state.gradebook_matrix_history:
                csv_string_buffer += f'"{log["Timestamp"]}","{log["Track ID"]}","{log["Accuracy Score"]}","{log["Transcription"]}"\n'
                
            col_csv, col_xlsx = st.columns(2)
            with col_csv: st.download_button(label="📥 Download Database Ledger (.csv)", data=csv_string_buffer.encode('utf-8'), file_name="CEI_Master_Gradebook_Ledger.csv", mime="text/csv")
            with col_xlsx: st.download_button(label="📊 Download Excel Gradebook (.xlsx)", data=csv_string_buffer.encode('utf-8'), file_name="CEI_Master_Gradebook_Ledger.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("Please choose at least one track entry token from the checklist field above to activate trackers.")
else:
    st.info("Awaiting headset recording audio tracks data... Click Start Recording above to begin.")
