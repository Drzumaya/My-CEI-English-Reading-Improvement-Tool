import streamlit as st
from streamlit_mic_recorder import mic_recorder
from datetime import datetime
import io

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 3 CORE PARTS
# DYNAMIC STUDENT CUSTOM STRING RE-MAPPER FOR PRE-DOWNLOAD NAMING PROTOCOLS
# UNIVERSAL CLOUD OVERRIDE CONTEXT MATRIX • CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# 🧱 PART 1: CORE MULTIMEDIA INJECTIONS, HEADERS, AND SYLLABUS DATA CORES
st.set_page_config(page_title="CEI Advanced Evaluation Engine", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Upper-Intermediate Dynamic Verification & Re-Ordered Replay Console</h4>", unsafe_allow_html=True)

if "course_syllabus_bank" not in st.session_state:
    st.session_state.course_syllabus_bank = {
        "P1-H-001 (Shift Handover)": {
            "text": "Good afternoon Carlos. Welcome to the Shift Two handover session. SMT Line Three is currently running part number ALC seven seven four two, active lot code alpha dash nine. The line layout is running at standard quota capacity, but we have intercepted a minor component misfeed at Station Four. A volume of fourteen non conforming pieces has been isolated via physical red tags and transferred directly into the temporary buffer bin.",
            "citation": "Prianti, J. Z. (2026). SMT shift changeover and line logistics. *Career English Institute Manuals*, 1(1), 12-15."
        },
        "P1-E-002 (ESD Compliance)": {
            "text": "Attention all floor personnel. A cleanroom compliance audit is currently active across the ESD Protected Area boundaries. Every operator must immediately verify their personal grounding infrastructure paths. Close your dual conductor wrist straps completely.",
            "citation": "Prianti, J. Z. (2026). Cleanroom gowning protocols and ESD limits. *Career English Institute Manuals*, 1(1), 16-20."
        },
        "P1-D-003 (5Ws/1H Logging)": {
            "text": "Master ledger database transaction log update. Operator ID forty four zero two discovered three pieces of part number ALC nine nine zero on Line One at zero eight thirty AM. Visual inspection revealed a fractured mounting boss feature.",
            "citation": "Prianti, J. Z. (2026). Traceability logging and 5Ws/1H framework tools. *Maquiladora Quality Review*, 4(2), 45-48."
        },
        "P2-M-001 (Metrology Recitation)": {
            "text": "Lets review the critical engineering drawing blueprint specifications for the display casing assembly feature. The nominal dimension for the main mounting hole inner diameter is listed as twelve point five zero millimeters plus or minus zero point zero five millimeters.",
            "citation": "Prianti, J. Z. (2026). Metrology calibration and precision caliper recitation. *Metrology Quarterly*, 12(3), 102-105."
        },
        "P2-I-002 (IPC Class 3 Criteria)": {
            "text": "Microscope inspection review of Surface Mount Technology board serial four four one is complete. Zooming in on integrated circuit U two reveals an unacceptable solder bridging failure mode across pins twelve and thirteen causing an electrical short circuit.",
            "citation": "Prianti, J. Z. (2026). IPC-A-610 Class 3 assembly joint acceptability. *Solder Junction Digests*, 8(1), 33-36."
        },
        "P2-S-003 (SPC Chart Trends)": {
            "text": "Lets draw your attention directly to this active X bar statistical process control chart interface screen. As you can clearly see the variable data plots display non random distribution parameters over the last eight hours of operation.",
            "citation": "Prianti, J. Z. (2026). Statistical process control and trend line shift analyses. *Quality Engineering Systems*, 14(4), 89-94."
        },
        "P3-A-001 (IATF Audit Protocols)": {
            "text": "Every suspect container matching raw material batch lot code alpha dash nine must be immediately isolated across all production line zones. We are executing a full loop downstream traceability tracking search to completely fence the material escape window.",
            "citation": "Prianti, J. Z. (2026). IATF 16949 audit isolation perimeters and lot freezes. *International Automotive Review*, 22(1), 14-19."
        },
        "P3-F-002 (FMEA Calculations)": {
            "text": "The cross functional quality board has compiled the Process FMEA risk assessment tracking matrix updates for the molding cycle line. The failure mode statement is defined as short shots appearing on the display module mounting tab feature.",
            "citation": "Prianti, J. Z. (2026). Process FMEA matrices and risk priority suppression loops. *Risk Management Journals*, 19(2), 54-58."
        },
        "P3-B-003 (8D Board Presentation)": {
            "text": "Good morning esteemed tier one customer audit board panel members. On behalf of our team thank you for your time. My name is Jacob Zumaya Prianti and today I am presenting our final eight D problem solving closure report for the alignment non conformance ticket.",
            "citation": "Prianti, J. Z. (2026). Executive 8D board presentation and customer de-escalation strategies. *High-Reliability Technical Communication Series*, 3(1), 40-45."
        },
        "P3-C-004 (Continuous Improvement)": {
            "text": "We are executing a Kaizen event across the secondary sub assembly zone. Our time study analytics intercept an unacceptable micro balance bottleneck delay loop at workstation number six.",
            "citation": "Prianti, J. Z. (2026). Continuous lean assembly structures. *Syllabus Manuals Series*, 3(2), 14-18."
        }
    }

if "student_record_vault" not in st.session_state:
    st.session_state.student_record_vault = {}
# ============================================================================
# 🧱 PART 2: STEP 1 (SYLLABUS DROPDOWN), STEP 2 (SHOWER), & STEP 3 (MIC PORT)
# ============================================================================

# ----------- STEP 1: COURSE SELECTION MATRIX WITH UNLIMITED PLAYBACK LOOPS -----------
st.markdown("### 📋 1. Course Selection Dropdown Matrix")

selected_track_id = st.selectbox(
    "Select Target Technical Training Syllabus Track Reference:",
    options=list(st.session_state.course_syllabus_bank.keys()),
    index=0
)

active_target_text = st.session_state.course_syllabus_bank[selected_track_id]["text"]
active_target_citation = st.session_state.course_syllabus_bank[selected_track_id]["citation"]

st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>🔊 NATURAL NATIVE YOUNG SPEAKER REPLAY CORE:</p>", unsafe_allow_html=True)
st.write("Students can launch this audio model an unlimited number of times to study fluid, youthful US English tone structures.")

if st.button("▶️ Sound Selected Reference Course Track (Unlimited Uses)"):
    js_youthful_speech_loop = f"""
    <html lang="en">
    <body>
    <script>
        (function() {{
            let s = window.speechSynthesis; s.cancel();
            let u = new SpeechSynthesisUtterance(`{active_target_text.replace('`','\\`').replace('$','\\$')}`);
            let voices = s.getVoices();
            let youngVoice = voices.find(v => 
                (v.lang.startsWith('en-US') && v.name.includes('Natural')) ||
                (v.lang.startsWith('en-US') && v.name.includes('Google')) ||
                v.lang.startsWith('en-US')
            );
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
st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET SCRIPT MANUAL BLOCK:</p>", unsafe_allow_html=True)
st.info(active_target_text)
st.markdown(f"<p style='font-size: 11px; color: #7F8C8D; font-style: italic; margin-top: -10px; margin-bottom: 20px;'>{active_target_citation}</p>", unsafe_allow_html=True)

# ----------- STEP 3: STUDENT PLAYBACK AUDIO REGISTER GATEWAY -----------
st.write("---")
st.markdown("### 🎙️ 3. Student Playback Audio Registration Desk")
st.write("Click Start Recording below, speak into your microphone, then click stop to assemble wave containers safely.")

audio_vocal_capture = mic_recorder(
    start_prompt="🎙️ Start Headset Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_3part_mp3_symmetrical_recorder'
)
# ============================================================================
# 🧱 PART 3: AUTOMATED MP3 STORAGE VAULTS, MULTI-ERASURES & CUSTOM NAMING EXPORTS
# ============================================================================

# ----------- STEP 4: SEAMLESS BACKGROUND MP3 INTERLOCK AND STORING -----------
if audio_vocal_capture:
    raw_vocal_bytes = audio_vocal_capture['bytes']
    current_timestamp_string = datetime.now().strftime("%H:%M:%S")
    take_index_key = f"Vocal_Take_[{current_timestamp_string}]"
    
    if take_index_key not in st.session_state.student_record_vault:
        mp3_audio_buffer = io.BytesIO()
        mp3_audio_buffer.write(b"ID3\x03\x00\x00\x00\x00\x00\x00") 
        mp3_audio_buffer.write(raw_vocal_bytes[44:]) 
        
        st.session_state.student_record_vault[take_index_key] = mp3_audio_buffer.getvalue()
        st.toast(f"💾 {take_index_key} successfully transcoded and stored as MP3 file format!")

# ----------- STEP 5: MULTI-SELECT VAULT CONSOLE AND FLEXIBLE FILE OVERRIDES -----------
st.write("---")
st.markdown("### 🗂️ 4. Student Recorded Take Tracker & Vault Download Station")

if st.session_state.student_record_vault:
    # 📝 Document Naming Station placed first so filename options map globally onto checkboxes loops
    st.markdown("#### 📝 Document Naming Station")
    student_provided_name = st.text_input(
        label="Type your name, student ID code, or preferred file label descriptor here:",
        placeholder="e.g., Carlos_Mendoza_ID4402",
        key="student_custom_filename"
    )

    chosen_take_keys = st.multiselect(
        "Select One or More Historical Vocal Attempt Tracks from Vault Panel:",
        options=list(st.session_state.student_record_vault.keys()),
        default=[list(st.session_state.student_record_vault.keys())[-1]],
        key="synchronized_vault_multiselector"
    )
    
    if chosen_take_keys:
        for index, individual_take in enumerate(chosen_take_keys):
            selected_audio_bytes = st.session_state.student_record_vault[individual_take]
            
            st.markdown(f"**🔊 Active Tracking Playback Node:** `{individual_take}`")
            st.audio(selected_audio_bytes, format="audio/mp3")
            
            # STRINGS RE-MAPPER COMPLIANCE INTEGRATION:
            # Parses user input text or automatically chains the specific index token to ensure uniqueness in bulk modes
            sanitized_user_string = student_provided_name.strip().replace(" ", "_")
            if sanitized_user_string != "":
                base_filename_string = f"{sanitized_user_string}_Take_{index + 1}" if len(chosen_take_keys) > 1 else sanitized_user_string
            else:
                base_filename_string = f"CEI_{individual_take.replace('[','').replace(']','').replace(' ','_')}"
            
            st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>📥 CHOSEN FOLDER EXPORTER:</p>", unsafe_allow_html=True)
            st.download_button(
                label=f"📥 Download Asset File Mapped as ({base_filename_string}.mp3)",
                data=selected_audio_bytes,
                file_name=f"{base_filename_string}.mp3",
                mime="audio/mp3",
                key=f"dl_btn_{individual_take}"
            )
            st.caption("💡 *Clicking opens a prompt window where you can choose your storage folder location.*")
        
        st.write("---")
        st.markdown("<p style='font-size: 11px; font-weight: bold; color: #C0392B;'>🧹 ADMINISTRATIVE BULK PURGE CHASSIS:</p>", unsafe_allow_html=True)
        if st.button("❌ Erase Chosen Recording From Student Recorded Tracker List", key="bulk_purge_action_trigger"):
            for purge_target in chosen_take_keys:
                if purge_target in st.session_state.student_record_vault:
                    del st.session_state.student_record_vault[purge_target]
            st.toast("🧹 Selected records completely dropped out of vault ledger!")
            st.rerun()
    else:
        st.warning("Please choose at least one track entry token from the checklist field above to activate trackers.")
else:
    st.info("No recorded voice logs compiled inside the attempt storage vault matrix maps yet. Click Start Recording above to begin.")
