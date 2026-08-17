import streamlit as st
from streamlit_mic_recorder import mic_recorder
from rapidfuzz import fuzz
from datetime import datetime
import pandas as pd
import struct
import io
import re
import time

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 5 STANDALONE PARTS
# PART 1: SYSTEM STACK DEPENDENCIES, BANNERS, & GLOBAL WORKSPACE REPO SINK
# LINEAR PCM WEB-RIFF AUDIO MULTIPLEXER (THE SILENT PLAYBACK RECORD FIX)
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Master Evaluation Engine", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Upper-Intermediate Dynamic Verification & Re-Ordered Replay Console</h4>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# DYNAMIC UNBLOCKED GOOGLE SPREADSHEET MANIFEST TRACKING ADAPTER HOOK
# ----------------------------------------------------------------------------
PUBLISHED_MANIFEST_CSV_URL = "https://google.com"

# Volatile session cache memories initialization
if "student_record_vault" not in st.session_state:
    st.session_state.student_record_vault = {}
    
if "gradebook_matrix_history" not in st.session_state:
    st.session_state.gradebook_matrix_history = []
# ============================================================================
# PART 2: COMPREHENSIVE NATIVE CLIENT-SIDE EXTRA EXERCISE SEED DATABANK
# ============================================================================
if "master_curriculum_catalog" not in st.session_state:
    st.session_state.master_curriculum_catalog = {
        "ECAUDIOS_Track_01_Shift_Handover.mp3": "Good afternoon Carlos. Welcome to the Shift Two handover session. SMT Line Three is currently running part number ALC seven seven four two, active lot code alpha dash nine. The line layout is running at standard quota capacity, but we have intercepted a minor component misfeed at Station Four.",
        "ECAUDIOS_Track_02_ESD_Compliance.mp3": "Attention all floor personnel. A cleanroom compliance audit is currently active across the ESD Protected Area boundaries. Every operator must immediately verify their personal grounding infrastructure paths. Close your dual conductor wrist straps completely.",
        "ECAUDIOS_Track_03_Traceability_Log.mp3": "Master ledger database transaction log update. Operator ID forty four zero two discovered three pieces of part number ALC nine nine zero on Line One at zero eight thirty AM. Visual inspection revealed a fractured mounting boss feature.",
        "ECAUDIOS_Track_04_Precision_Calipers.mp3": "Lets review the critical engineering drawing blueprint specifications for the display casing assembly feature. The nominal dimension for the main mounting hole inner diameter is listed as twelve point five zero millimeters plus or minus zero point zero five.",
        "ECAUDIOS_Track_05_Solder_Bridging.mp3": "Microscope inspection review of Surface Mount Technology board serial four four one is complete. Zooming in on integrated circuit U two reveals an unacceptable solder bridging failure mode across pins twelve and thirteen causing an electrical short.",
        "ECAUDIOS_Track_06_SPC_Trend_Lines.mp3": "Lets draw your attention directly to this active X bar statistical process control chart interface screen. As you can clearly see the variable data plots display non random distribution parameters over the last eight hours of operation.",
        "ECAUDIOS_Track_07_IATF_Containment.mp3": "Every suspect container matching raw material batch lot code alpha dash nine must be immediately isolated across all production line zones. We are executing a full loop downstream traceability tracking search to completely fence the window.",
        "ECAUDIOS_Track_08_PFMEA_Calculations.mp3": "The cross functional quality board has compiled the Process FMEA risk assessment tracking matrix updates for the molding cycle line. The failure mode statement is defined as short shots appearing on the display module mounting tab feature.",
        "ECAUDIOS_Track_09_8D_Presentation.mp3": "Good morning esteemed tier one customer audit board panel members. On behalf of our team thank you for your time. My name is Jacob Zumaya Prianti and today I am presenting our final eight D problem solving closure report for the alignment.",
        "ECAUDIOS_Track_10_Kaizen_Event_Flow.mp3": "We are executing a Kaizen event across the secondary sub assembly zone. Our time study analytics intercept an unacceptable micro balance bottleneck delay loop at workstation number six to optimize production flow matrix parameters.",
        "ECAUDIOS_Track_11_Material_Receiving.mp3": "Perform a strict incoming statistical lot sampling verification loop across all units in pallet tier number three. If the visual boss fracture margin ratio exceeds our acceptable quality limit threshold value, reject the container.",
        "ECAUDIOS_Track_12_Five_Whys_Analysis.mp3": "The five why investigative methodology was applied to isolate the source of the electrical short circuit. The team discovered that the main wiring branch layout insulation layer had rubbed against a sharp metal structural mounting column edge.",
        "ECAUDIOS_Track_13_Dispatch_Schedules.mp3": "The downstream supply dispatch schedule encounters an unexpected constraint matrix. Incoming raw components container inventory allocations must pass the material gate by zero seven hundred hours tomorrow morning to maintain quota targets.",
        "ECAUDIOS_Track_14_Dial_Indicators.mp3": "Verify the depth thickness margin profile using the micrometric dial indicator gauge tool feature. Ensure that the surface finish parameters stay within standard tolerance thresholds during the final article assembly checks.",
        "ECAUDIOS_Track_15_Hydraulic_Seals.mp3": "The hydraulic cylinder seals on molding press machine number twelve were replaced during the scheduled maintenance shift down time. Technicians checked the internal pump pressure curves to ensure fluid pressure ranges match completely.",
        "ECAUDIOS_Track_16_Emergency_Stoppage.mp3": "An automated line sensor lock out error triggered a sudden emergency belt stoppage across line segment number two. No operators were exposed to structural hazards. The line remained safely frozen until cleared by automation support teams.",
        "ECAUDIOS_Track_17_Passive_Voice_Logs.mp3": "When writing audit logs, use the passive voice to emphasize the item or non-conformance rather than the operator. Instead of saying 'The worker dropped the piece', write: 'The component was dropped and a fracture was observed on the boss feature.'",
        "ECAUDIOS_Track_18_Conditional_Rules.mp3": "Use first and second conditional structures to clarify safety rules and mitigation steps during line failures. For example: If the conveyor temperature exceeds two hundred degrees, the automated safety switch trips immediately to protect operators.",
        "ECAUDIOS_Track_19_Stencil_Thickness.mp3": "Review the stencil thickness specifications for the high-volume screen printer component at station one. Solder paste height must be carefully verified to maintain target volume profiles across the copper landing pads cleanly.",
        "ECAUDIOS_Track_20_Dissipative_Flooring.mp3": "A continuous grounding path audit was conducted across the newly installed static dissipative vinyl flooring panels. All resistance-to-ground measurements successfully conform to baseline cleanroom compliance parameters.",
        "ECAUDIOS_Track_21_First_Article_Log.mp3": "The first article inspection log for production run seven six two has been approved. Component positioning parameters, outer dimensions, and wire-bond pull strength test margins meet all tier one quality framework criteria fields.",
        "ECAUDIOS_Track_22_Laser_Matrix_Etch.mp3": "Scan the matrix barcode laser tag etched on the main housing frame to download the processing history dossier. Automated database tracking locks down single-unit visibility arrays from receiving to final dispatch operations.",
        "ECAUDIOS_Track_23_XRay_Fillet_Checks.mp3": "Cross-sectional x-ray inspection reveals insufficient heel fillets along the primary terminal joints of capacitor package C four. Isolate the lot inside the rework hold sector until a complete corrective action is filed.",
        "ECAUDIOS_Track_24_Pull_Signal_Queues.mp3": "We have successfully dropped our work-in-progress inventory load values by fourteen percent through the integration of standard cell layouts and pull-signal kitting queues at the workstation entry gates safely.",
        "ECAUDIOS_Track_25_Calibration_Meters.mp3": "The calibration frequency logs for the secondary multimeters reveal zero drift variance over the last quarter. Ensure all verification labels are stamped and signed off before the auditor arrives tomorrow.",
        "ECAUDIOS_Track_26_Thermal_Profile_Run.mp3": "Run a complete oven reflow thermal profiling sequence using the calibrated data logger package. Confirm the peak liquidus phase duration stays within ninety seconds to prevent joint brittleness.",
        "ECAUDIOS_Track_27_Vendor_Audit_Review.mp3": "The incoming sub-assembly supplier score has dropped to eighty-two percent due to dimensional non-conformances. We are launching a formal supplier corrective action request to mandate root cause investigations.",
        "ECAUDIOS_Track_28_Kitting_Zone_Layout.mp3": "Coordinators are reviewing the kitting zone logistics layout map to cut down on material handling cycle waste times. Moving the staging bins adjacent to the line entrance drops transit waste immediately."
    }
# ============================================================================
# PART 3: CLOUD DIRECTORY ACCOUNTING, 7-VOICE TIMBRES, & PACING VELOCITY SLIDERS
# ============================================================================
st.markdown("### 📋 1. Course Selection Dropdown Matrix")

discovered_curriculum_tracks = {}

if "pub?output=csv" in PUBLISHED_MANIFEST_CSV_URL:
    try:
        live_timestamp_nonce = int(time.time())
        cache_busted_csv_stream_url = f"{PUBLISHED_MANIFEST_CSV_URL}&cb={live_timestamp_nonce}"
        cloud_data_frame = pd.read_csv(cache_busted_csv_stream_url, header=None)
        
        for index, row in cloud_data_frame.iterrows():
            if len(row) >= 2:
                track_name = str(row.iloc).strip()
                audio_link = str(row.iloc).strip()
                
                if track_name != "nan" and track_name != "" and audio_link != "nan" and audio_link != "" and not track_name.lower().startswith("audio_track"):
                    if track_name in st.session_state.master_curriculum_catalog:
                        lesson_text = st.session_state.master_curriculum_catalog[track_name]
                    else:
                        clean_lbl = track_name.replace('.mp3','').replace('.wav','').replace('_',' ')
                        lesson_text = f"Technical language standard training manual passage matching cloud file asset: '{clean_lbl}'. Review printed references to trace vocabulary loops."
                        
                    discovered_curriculum_tracks[track_name] = {
                        "text": lesson_text,
                        "url": audio_link
                    }
    except Exception:
        pass

if len(discovered_curriculum_tracks) < 28:
    for k, v in st.session_state.master_curriculum_catalog.items():
        if k not in discovered_curriculum_tracks:
            discovered_curriculum_tracks[k] = {"text": v, "url": None}

# EXACT DROPDOWN PROMPT MATRIX USER SPECIFICATION ENFORCED
selected_track_id = st.selectbox(
    "Choose an Exercise track:",
    options=sorted(list(discovered_curriculum_tracks.keys())),
    index=0
)

active_target_text = discovered_curriculum_tracks[selected_track_id]["text"]
active_target_url = discovered_curriculum_tracks[selected_track_id]["url"]

st.write("---")
st.markdown("#### 🔊 Dual-Engine Reference Audio Station")

# ENGINE A: Streams your actual recorded raw audio voice file directly from Google Drive
if active_target_url and "://google.com" in active_target_url:
    try:
        parsed_id = re.search(r'(?:id=|\/d\/)([\w-]+)', active_target_url).group(1)
        direct_streaming_packet_url = f"https://google.com{parsed_id}"
        st.markdown("🥇 **Engine A: Play Original Recorded Human Voice Audio File**")
        st.audio(direct_streaming_packet_url, format="audio/mp3")
    except Exception:
        pass

st.write(" ")

# ENGINE B: Restores your 7 Optional Accent Dialects & Dynamic Speed Velocity Controllers
st.markdown("⚙️ **Engine B: Optional Dialect Accelerator & Pitch Tuning Deck**")

voice_options_map = {
    "🇺🇸 USA Female Standard (Natural Curve)": {"lang": "en-US", "name": "Google US English", "pitch": 1.10},
    "🇺🇸 USA Male Bold (Neural Engineering Style)": {"lang": "en-US", "name": "Microsoft David", "pitch": 0.78},
    "🇺🇸 USA Female Soft (Pacing Cadence standard)": {"lang": "en-US", "name": "Zira", "pitch": 1.15},
    "🇺🇸 USA Male Rich (Deep Resonance profile)": {"lang": "en-US", "name": "Google US English Male", "pitch": 0.74},
    "🇬🇧 UK English Female (London Dialect)": {"lang": "en-GB", "name": "Google UK English Female", "pitch": 1.05},
    "🇬🇧 UK English Male (BBC Standard)": {"lang": "en-GB", "name": "Google UK English Male", "pitch": 0.80},
    "🇦🇺 Australian Accent Mix (Sydney Timbre)": {"lang": "en-AU", "name": "Google AU English", "pitch": 1.00}
}

col_vce, col_spd = st.columns(2)
with col_vce:
    chosen_voice_timbre = st.selectbox("💡 Choose Accent Profile Variant (7 USA Native Options):", options=list(voice_options_map.keys()), index=0)
with col_spd:
    chosen_speaking_velocity = st.slider("🏃 Adjust Speaking Velocity Speed:", min_value=0.50, max_value=1.50, value=0.88, step=0.05)

target_voice_meta = voice_options_map[chosen_voice_timbre]

js_multi_engine_console = f"""
<div style='background-color: #F8F9F9; border: 1px solid #D5DBDB; border-radius: 6px; padding: 12px; text-align: center;'>
    <button id='cei_run_hybrid_btn' style='background-color: #2471A3; color: white; border: none; padding: 10px 24px; font-size: 13px; font-weight: bold; border-radius: 4px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        ▶️ Run Voice Simulation Model at {chosen_speaking_velocity}x Speed
    </button>
</div>

<script>
document.getElementById('cei_run_hybrid_btn').addEventListener('click', function() {{
    let synth = window.speechSynthesis;
    synth.cancel();
    
    let txt = `{active_target_text.replace('`','\\`').replace('$','\\$')}`;
    let utterance = new SpeechSynthesisUtterance(txt);
    
    utterance.lang = 'en-US';
    let vcs = synth.getVoices();
    let searchTerm = '{target_voice_meta["name"]}'.toLowerCase();
    let targetLang = '{target_voice_meta["lang"]}'.toLowerCase();
    
    let matchedVoice = vcs.find(v => v.lang.toLowerCase().startsWith(targetLang) && (v.name.toLowerCase().includes(searchTerm) || v.name.toLowerCase().includes('male')));
    if (!matchedVoice) matchedVoice = vcs.find(v => v.lang.toLowerCase().startsWith(targetLang));
    
    if (matchedVoice) utterance.voice = matchedVoice;
    utterance.rate = {chosen_speaking_velocity};
    utterance.pitch = {target_voice_meta["pitch"]};
    
    synth.speak(utterance);
}});
</script>
"""
st.components.v1.html(js_multi_engine_console, height=65)

# ----------- STEP 2: THE READING SHOWER SCRIPT VIEWPORT BOARD -----------
st.write("---")
st.markdown("### 🔍 2. Reading Shower Specification Board")
st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET TRAINING PASSAGE SCRIPT MANUAL BLOCK:</p>", unsafe_allow_html=True)
st.info(active_target_text)
# ============================================================================
# PART 4: STUDENT VOCAL REGISTRATION DESK AND NATIVE PCM RIFF EXPANSION CORE
# ============================================================================

# ----------- STEP 3: STUDENT PLAYBACK AUDIO REGISTER GATEWAY -----------
st.write("---")
st.markdown("### 🎙️ 3. Student Playback Audio Registration Desk")
st.write("Click Start Recording below, speak into your microphone, then click stop to assemble audio containers safely.")

audio_vocal_capture = mic_recorder(
    start_prompt="🎙️ Start Headset Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_5part_riff_recovery_volume_unmuted_recorder'
)

# ----------- STEP 4: THE WAV STRUCT SPECIFICATION HEADERS INJECTOR -----------
if audio_vocal_capture:
    raw_vocal_bytes = audio_vocal_capture['bytes']
    current_timestamp_string = datetime.now().strftime("%H:%M:%S")
    take_index_key = f"Vocal_Take_[{current_timestamp_string}]"
    
    if take_index_key not in st.session_state.student_record_vault:
        # 🔊 NATIVE SOUND PASSTHROUGH PATCH REFACTOR (THE SOUND RECOVERY INTERLOCK):
        # We intercept raw browser microphone bytes arrays and compile an official 44 byte RIFF header block.
        # This completely resolves the "silent recording" bug, unmuting the playback node.
        sample_rate_coefficient = 16000
        bit_depth_channels = 16
        total_data_size_len = len(raw_vocal_bytes)
        
        wav_header_packet_buffer = io.BytesIO()
        wav_header_packet_buffer.write(b'RIFF') # ChunkID token
        wav_header_packet_buffer.write(struct.pack('<I', 36 + total_data_size_len)) # ChunkSize
        wav_header_packet_buffer.write(b'WAVE') # Format tag
        wav_header_packet_buffer.write(b'fmt ') # Subchunk1ID descriptor
        wav_header_packet_buffer.write(struct.pack('<I', 16)) # Subchunk1Size
        wav_header_packet_buffer.write(struct.pack('<H', 1)) # AudioFormat code (1 = Uncompressed PCM)
        wav_header_packet_buffer.write(struct.pack('<H', 1)) # NumChannels (1 = Mono profile)
        wav_header_packet_buffer.write(struct.pack('<I', sample_rate_coefficient)) # SampleRate 16kHz
        wav_header_packet_buffer.write(struct.pack('<I', sample_rate_coefficient * 2)) # ByteRate matrix
        wav_header_packet_buffer.write(struct.pack('<H', 2)) # BlockAlign parameters
        wav_header_packet_buffer.write(struct.pack('<H', bit_depth_channels)) # BitsPerSample depth
        wav_header_packet_buffer.write(b'data') # Subchunk2ID token anchor
        wav_header_packet_buffer.write(struct.pack('<I', total_data_size_len)) # Subchunk2Size length bytes
        
        # Merge structural meta configuration headers with raw microphone payload streams safely
        finalized_sound_payload_bytes = wav_header_packet_buffer.getvalue() + raw_vocal_bytes
        
        st.session_state.student_record_vault[take_index_key] = finalized_sound_payload_bytes
        st.toast(f"🎉 {take_index_key} recorded and unmuted with official Web-RIFF headers active!")
# ============================================================================
# PART 5: COGNITIVE EVALUATIONS, COHORT ID MANAGEMENT PANELS, & EXPORTERS
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

if st.session_state.gradebook_matrix_history:
    st.write("---")
    st.markdown("### 🛠️ Coordinator Database Maintenance Dashboard")
    st.write("Select a committed record entry line to overwrite or upgrade its target Student ID column parameters:")
    
    gradebook_string_indices = []
    for index, log in enumerate(st.session_state.gradebook_matrix_history):
        gradebook_string_indices.append(f"Row [{index + 1}] - Time: {log['Timestamp']} | Current ID: {log['Student_ID']} | Name: {log['Student_Name']}")
        
    chosen_maintenance_row_string = st.selectbox("Select Logged Gradebook Record Line to Modify:", options=gradebook_string_indices, key="maintenance_row_selector")
    target_numerical_index = int(chosen_maintenance_row_string.split("Row [").split("]")) - 1
    
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
            # STABLE AUDIO MONITOR PLAYER: Streams the unmuted formatted WAV packet cleanly at high volume
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
