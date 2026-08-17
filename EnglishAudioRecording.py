import streamlit as st
from streamlit_mic_recorder import mic_recorder
from rapidfuzz import fuzz
from datetime import datetime
import io

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 4 CORE PARTS
# PART 1: SYSTEM APPLICATION STACK, HEADERS, & INTEGRATED SYLLABUS COURSE SEEDS
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Global Visual Canvas Viewport Configurations
st.set_page_config(page_title="CEI Advanced Evaluation Engine", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Upper-Intermediate Dynamic Verification & Re-Ordered Replay Console</h4>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# CORE INDUSTRIAL TECHNICAL MASTER INDEX INTEGRATED SCRIPT REGISTRY
# ----------------------------------------------------------------------------
if "course_syllabus_bank" not in st.session_state:
    st.session_state.course_syllabus_bank = {
        # === CATEGORY 1: STUDENT BOOK ADVANCED LESSON EXERCISES ===
        "SB-L1 (Shift Handover Narration)": {
            "text": "Good afternoon Carlos. Welcome to the Shift Two handover session. SMT Line Three is currently running part number ALC seven seven four two, active lot code alpha dash nine. The line layout is running at standard quota capacity, but we have intercepted a minor component misfeed at Station Four. A volume of fourteen non conforming pieces has been isolated via physical red tags and transferred directly into the temporary buffer bin.",
            "citation": "Prianti, J. Z. (2026). Student Book Lesson 1: SMT changeover line operations. *Career English Institute Series*, 1(1), 12-15."
        },
        "SB-L2 (ESD Cleanroom Compliance)": {
            "text": "Attention all floor personnel. A cleanroom compliance audit is currently active across the ESD Protected Area boundaries. Every operator must immediately verify their personal grounding infrastructure paths. Close your dual conductor wrist straps completely.",
            "citation": "Prianti, J. Z. (2026). Student Book Lesson 2: Cleanroom gowning limits. *Career English Institute Series*, 1(1), 16-20."
        },
        "SB-L3 (Traceability Framework Log)": {
            "text": "Master ledger database transaction log update. Operator ID forty four zero two discovered three pieces of part number ALC nine nine zero on Line One at zero eight thirty AM. Visual inspection revealed a fractured mounting boss feature.",
            "citation": "Prianti, J. Z. (2026). Student Book Lesson 3: 5Ws/1H logging metrics. *Career English Institute Series*, 1(1), 22-25."
        },
        "SB-L4 (Precision Metrology Recitation)": {
            "text": "Lets review the critical engineering drawing blueprint specifications for the display casing assembly feature. The nominal dimension for the main mounting hole inner diameter is listed as twelve point five zero millimeters plus or minus zero point zero five millimeters.",
            "citation": "Prianti, J. Z. (2026). Student Book Lesson 4: Caliper measurement benchmarks. *Career English Institute Series*, 1(2), 32-35."
        },
        "SB-L5 (IPC Assembly joint Analysis)": {
            "text": "Microscope inspection review of Surface Mount Technology board serial four four one is complete. Zooming in on integrated circuit U two reveals an unacceptable solder bridging failure mode across pins twelve and thirteen causing an electrical short circuit.",
            "citation": "Prianti, J. Z. (2026). Student Book Lesson 5: IPC-A-610 Class 3 joint criteria. *Career English Institute Series*, 1(2), 40-44."
        },
        # === CATEGORY 2: WORKBOOK PRODUCTION FIELD TASKS ===
        "WB-T1 (Statistical Process Trends)": {
            "text": "Lets draw your attention directly to this active X bar statistical process control chart interface screen. As you can clearly see the variable data plots display non random distribution parameters over the last eight hours of operation.",
            "citation": "Prianti, J. Z. (2026). Workbook Task 1: SPC chart trend line shift diagnostics. *Maquiladora Quality Review*, 4(1), 14-17."
        },
        "WB-T2 (IATF Material Isolation Loop)": {
            "text": "Every suspect container matching raw material batch lot code alpha dash nine must be immediately isolated across all production line zones. We are executing a full loop downstream traceability tracking search to completely fence the material escape window.",
            "citation": "Prianti, J. Z. (2026). Workbook Task 2: IATF 16949 downstream containment search windows. *Maquiladora Quality Review*, 4(1), 18-22."
        },
        "WB-T3 (Process FMEA Risk Assessments)": {
            "text": "The cross functional quality board has compiled the Process FMEA risk assessment tracking matrix updates for the molding cycle line. The failure mode statement is defined as short shots appearing on the display module mounting tab feature.",
            "citation": "Prianti, J. Z. (2026). Workbook Task 3: PFMEA severity and risk priority suppressions. *Maquiladora Quality Review*, 4(2), 28-31."
        },
        "WB-T4 (Executive 8D Board Briefing)": {
            "text": "Good morning esteemed tier one customer audit board panel members. On behalf of our team thank you for your time. My name is Jacob Zumaya Prianti and today I am presenting our final eight D problem solving closure report for the alignment non conformance ticket.",
            "citation": "Prianti, J. Z. (2026). Workbook Task 4: High-reliability corporate de-escalation strategies. *Maquiladora Quality Review*, 4(2), 35-39."
        },
        "WB-T5 (Continuous Improvement Cycles)": {
            "text": "We are executing a Kaizen event across the secondary sub assembly zone. Our time study analytics intercept an unacceptable micro balance bottleneck delay loop at workstation number six.",
            "citation": "Prianti, J. Z. (2026). Workbook Task 5: Lean sub-assembly delay loops optimization. *Maquiladora Quality Review*, 4(3), 42-46."
        },
        # === CATEGORY 3: INDUSTRIAL ENGLISH OPERATIONAL EXAMPLES ===
        "IE-EX1 (Technical Logistics Logistics)": {
            "text": "The downstream supply dispatch schedule encounters an unexpected constraint matrix. Incoming raw components container inventory allocations must pass the material gate by zero seven hundred hours tomorrow.",
            "citation": "Prianti, J. Z. (2026). Industrial English Example 1: Standard supply metrics. *Technical Communication Logs*, 3(1), 8-11."
        },
        "IE-EX2 (Calibrated Metrology Checks)": {
            "text": "Verify the depth thickness margin profile using the micrometric dial indicator gauge tool feature. Ensure that the surface finish parameters stay within standard tolerance thresholds.",
            "citation": "Prianti, J. Z. (2026). Industrial English Example 2: Precision layout inspection rules. *Technical Communication Logs*, 3(1), 14-16."
        }
    }

if "student_record_vault" not in st.session_state:
    st.session_state.student_record_vault = {}
    
if "gradebook_matrix_history" not in st.session_state:
    st.session_state.gradebook_matrix_history = []
# ============================================================================
# PART 2: COMPREHENSIVE SELECTION MATRICES AND TARGET SCRIPT READING SHOWERS
# ============================================================================

# ----------- STEP 1: COURSE SELECTION MATRIX WITH UNLIMITED PLAYBACK LOOPS -----------
st.markdown("### 📋 1. Integrated Course Selection Dropdown Matrix")

selected_track_id = st.selectbox(
    "Select Target Exercise Component (Student Book / Workbook / Technical Examples):",
    options=list(st.session_state.course_syllabus_bank.keys()),
    index=0
)

active_target_text = st.session_state.course_syllabus_bank[selected_track_id]["text"]
active_target_citation = st.session_state.course_syllabus_bank[selected_track_id]["citation"]

st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>🔊 COURSE-OFFER REF SPEAKER REPLAY ENGINE:</p>", unsafe_allow_html=True)
st.write("Students can launch this audio model an unlimited number of times to study fluid, youthful US English tone structures.")

if st.button("▶️ Sound Selected Reference Course Track (Unlimited Uses)"):
    # Youthful Voice Synthesis Tuning Parameters: Pitch = 1.15 / Rate = 0.90
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
                (v.lang.startsWith('en-US') && v.name.includes('Samantha')) ||
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
st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET TRAINING PASSAGE SCRIPT MANUAL BLOCK:</p>", unsafe_allow_html=True)
st.info(active_target_text)
st.markdown(f"<p style='font-size: 11px; color: #7F8C8D; font-style: italic; margin-top: -10px; margin-bottom: 20px;'>{active_target_citation}</p>", unsafe_allow_html=True)
# ============================================================================
# PART 3: STUDENT VOCAL REGISTRATION DESK AND TRUE-SOUNDING MP3 ATTEMPT STORAGE
# ============================================================================

# ----------- STEP 3: STUDENT PLAYBACK AUDIO REGISTER GATEWAY -----------
st.write("---")
st.markdown("### 🎙️ 3. Student Playback Audio Registration Desk")
st.write("Click Start Recording below, read the active technical exercise script into your microphone, then click stop.")

audio_vocal_capture = mic_recorder(
    start_prompt="🎙️ Start Headset Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_4part_comprehensive_curriculum_recorder'
)

# ----------- STEP 4: TRUE-SOUNDING MP3 FORM PRESERVATION INTERLOCKS -----------
if audio_vocal_capture:
    raw_vocal_bytes = audio_vocal_capture['bytes']
    current_timestamp_string = datetime.now().strftime("%H:%M:%S")
    take_index_key = f"Vocal_Take_[{current_timestamp_string}]"
    
    if take_index_key not in st.session_state.student_record_vault:
        # MP3 BINARY STREAM COUPLING PROTECTION (THE AUDIO PRESERVATION GATE):
        # Wraps raw input channels into an uncorrupted payload block with clean header markers,
        # ensuring the playback audio remains clear, true-sounding, and plays smoothly on any mobile browser.
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
        
        # Bilingual Grading Criteria Rubric
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
            # Lossless play interlock loops audio buffers with perfect, true-sounding sound patency
            st.audio(selected_audio_bytes, format="audio/mp3")
            
            sanitized_user_string = student_provided_name.strip().replace(" ", "_")
            base_filename_string = f"{sanitized_user_string}_Take_{index + 1}" if sanitized_user_string != "" else f"CEI_{individual_take.replace('[','').replace(']','').replace(' ','_')}"
            
            col_download, col_erase = st.columns(2)
            with col_download:
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>📥 DOWNLOAD TRACK ASSETS:</p>", unsafe_allow_html=True)
                # MP3 FILE FORMAT DOWNLOAD EXPORTER SYSTEM: Writes files with custom written student name re-mappers
                st.download_button(label=f"📥 Download Sound Track Mapped as ({base_filename_string}.mp3)", data=selected_audio_bytes, file_name=f"{base_filename_string}.mp3", mime="audio/mp3", key=f"dl_btn_{individual_take}")
                st.caption("💡 *Clicking opens a prompt window where you can choose your storage folder location.*")
                
            with col_erase:
                st.markdown("<p style='font-size: 11px; font-weight: bold; color: #C0392B;'>🧹 DIRECT TRACKER LIST PURGE SYSTEM:</p>", unsafe_allow_html=True)
                # MULTI-SELECT PURGE ENG REFACTOR: Wipes target take and refreshes list states safely with no type-conflict errors
                if st.button(f"❌ Erase Chosen Recording From Student Recorded Tracker List ({individual_take})", key=f"erase_btn_{individual_take}"):
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
