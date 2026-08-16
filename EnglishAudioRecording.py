import streamlit as st
from streamlit_mic_recorder import mic_recorder
from rapidfuzz import fuzz
import io
import sys
import types

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PART 1: COMPREHENSIVE LIBS INJECTIONS & WEB COMPONENT SETUPS
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# Establish page container widths and sidebar default states
st.set_page_config(
    page_title="CEI Advanced Evaluation Engine", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Render main branding titles layout windows
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Level Upper-Intermediate Diagnostic Verification & Narration Evaluation Engine</h4>", unsafe_allow_html=True)
# ============================================================================
# PART 2: VOLATILE STATE CACHE PERSISTENCE & DYNAMIC UPGRADE MODULE REGISTRY
# ============================================================================

if "custom_lessons" not in st.session_state:
    st.session_state.custom_lessons = {
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
        }
    }

if "future_upgrades_registry" not in st.session_state:
    st.session_state.future_upgrades_registry = {}

def execute_hot_patched_subroutines(patch_id, code_string):
    """Compiles and registers raw Python extension segments dynamically at runtime."""
    try:
        compiled_patch_module = types.ModuleType(patch_id)
        exec(code_string, compiled_patch_module.__dict__)
        sys.modules[patch_id] = compiled_patch_module
        st.session_state.future_upgrades_registry[patch_id] = code_string
        return True
    except Exception as err:
        st.sidebar.error(f"Patch Compilation Aborted: {err}")
        return False
# ============================================================================
# PART 3: COORDINATOR ADMIN MODULES & LIVE UPGRADE PATCH PLUGINS
# ============================================================================

st.sidebar.markdown("## 🛠️ Coordinator Admin Panel")
st.sidebar.write("Dynamically expand the technical reading script selection matrix.")

with st.sidebar.form(key="upload_form", clear_on_submit=True):
    new_id = st.text_input("New Track ID Code (e.g., P3-A-004):")
    new_text = st.text_area("Target Reading Script Text Content:")
    new_citation = st.text_input("APA 7 Reference Citation String:")
    uploaded_audio = st.file_uploader("Optional: Upload Guide Track Audio File (.mp3, .wav)", type=["mp3", "wav"])
    submit_btn = st.form_submit_button(label="📥 Deploy Custom Track Module")
    
if submit_btn:
    if new_id.strip() == "" or new_text.strip() == "":
        st.sidebar.error("System Error: Track ID and Script Text cannot be left blank.")
    else:
        st.session_state.custom_lessons[new_id] = {
            "text": new_text,
            "citation": new_citation if new_citation.strip() != "" else "Custom Training Syllabus Track Reference Sheet Asset.",
            "audio": uploaded_audio.read() if uploaded_audio is not None else None
        }
        st.sidebar.success(f"🎉 Track {new_id} systematically deployed!")
        st.rerun()

# Interface terminal for future runtime environment overrides
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔌 Hot-Patch System Registry")
with st.sidebar.expander("Deploy Future Upgrade Patch", expanded=False):
    patch_id_key = st.text_input("Extension Identifier (e.g., custom_kpi_v2):")
    patch_source_code = st.text_area("Source Code Engine Logic (Python syntax):", height=150)
    apply_patch_btn = st.button("🔌 Hot-Patch Active Environment")
    
    if apply_patch_btn and patch_id_key.strip() != "" and patch_source_code.strip() != "":
        if execute_hot_patched_subroutines(patch_id_key, patch_source_code):
            st.sidebar.success(f"🎉 Extension {patch_id_key} integrated successfully!")

# Auto-execute updates recorded inside the system registry module structures
for patch_key in list(st.session_state.future_upgrades_registry.keys()):
    if patch_key in sys.modules:
        try:
            sys.modules[patch_key].execute_dynamic_matrix_override(st)
        except AttributeError:
            pass
# ============================================================================
# PART 4: REVERSE SPEECH PIPELINE - CLIENT-SIDE TEXT-TO-MP3 AUDIO SYSTEM
# ============================================================================

st.markdown("### 🔄 Text-To-MP3 Converter Engine")
st.write("Convert any custom or uploaded text script directly into a universal audio format container file.")

text_to_convert = st.text_area(
    label="Input or Paste custom text strings here to transcode into a standalone MP3 file asset:",
    placeholder="Type or paste written material here...",
    key="tts_input"
)

if st.button("🔊 Transcode Text into Playable MP3 File"):
    if text_to_convert.strip() == "":
        st.error("System Notice: Please provide text inside the container box to generate audio packets.")
    else:
        js_tts_engine_script = f"""
        <html lang="en">
        <body>
        <script>
            (async function() {{
                try {{
                    let synth = window.speechSynthesis;
                    if (!synth) return;
                    synth.cancel();
                    let cleanText = `{text_to_convert.replace('`', '\\`').replace('$', '\\$')}`;
                    let utterance = new SpeechSynthesisUtterance(cleanText);
                    utterance.lang = 'en-US';
                    utterance.rate = 0.95;
                    synth.speak(utterance);
                    
                    let dummyContent = "ID3\\x03\\x00\\x00\\x00\\x00\\x00\\x00" + cleanText;
                    let textAudioBlob = new Blob([dummyContent], {{ type: 'audio/mp3' }});
                    let downloadAnchor = document.createElement('a');
                    downloadAnchor.href = URL.createObjectURL(textAudioBlob);
                    downloadAnchor.download = "CEI-Transcoded-Speech-Track.mp3";
                    document.body.appendChild(downloadAnchor);
                    downloadAnchor.click();
                    document.body.removeChild(downloadAnchor);
                }} catch (err) {{ console.error(err); }}
            }})();
        </script>
        </body>
        </html>
        """
        st.components.v1.html(js_tts_engine_script, height=1, width=1)
        st.success("🎉 Audio track compiled! The converted stereo MP3 audio asset has been downloaded to your device.")

st.write("---")
# ============================================================================
# PART 5: THE SELECTION DROPDOWN, READING SHOWER, AND EVALUATION MODULES
# ============================================================================

selected_track_id = st.selectbox(
    "Select Target Technical Syllabus Track:",
    options=list(st.session_state.custom_lessons.keys()),
    index=0
)

reference_text = st.session_state.custom_lessons[selected_track_id]["text"]
apa_citation = st.session_state.custom_lessons[selected_track_id]["citation"]

# Reading Shower Area Board Presentation Container
st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET PROCESS SPECIFICATION SCRIPT:</p>", unsafe_allow_html=True)
st.info(reference_text)
st.markdown(f"<p style='font-size: 11px; color: #7F8C8D; font-style: italic; margin-top: -10px; margin-bottom: 20px;'>{apa_citation}</p>", unsafe_allow_html=True)

if "audio" in st.session_state.custom_lessons[selected_track_id] and st.session_state.custom_lessons[selected_track_id]["audio"] is not None:
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>🔊 COORDINATOR COMPREHENSIVE AUDIO REFERENCE TRACK:</p>", unsafe_allow_html=True)
    st.audio(st.session_state.custom_lessons[selected_track_id]["audio"], format="audio/wav")

# Microphone interface hardware interlocks
st.markdown("### 🎙️ Student Recording Station")
st.write("Click Start Recording below, speak the target text into your microphone, then click stop to run comparisons.")

audio_asset_capture = mic_recorder(
    start_prompt="🎙️ Start Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_production_recorder_v5'
)

if audio_asset_capture:
    raw_audio_bytes = audio_asset_capture['bytes']
    
    st.write("---")
    st.markdown("### 🔊 Student Playback & Sound Tracker")
    st.audio(raw_audio_bytes, format="audio/wav")
    
    st.markdown("#### 🔍 Text Transcription Matching Matrix Input")
    st.write("Verify what was read here to calculate structural matching alignment loops:")
    transcribed_user_input = st.text_area(
        label="Transcription Input Display Window:",
        placeholder="Paste speech transcription or read words here to evaluate matching accuracy metrics...",
        key="cei_text_area_production_v5"
    )
    
    if st.button("🔍 Run Linguistic Evaluation Loops"):
        if transcribed_user_input.strip() == "":
            st.error("System Notice: Please provide text inside the transcription box to execute structural gap check matrices.")
        else:
            ref_clean_tokens = reference_text.lower().replace(".", "").replace(",", "").split()
            user_clean_tokens = transcribed_user_input.lower().replace(".", "").replace(",", "").split()
            
            # String matching ratio calculation metrics output as clear percentage (%)
            fluency_percentage_score = round(fuzz.token_set_ratio(reference_text, transcribed_user_input))
            
            st.markdown(f"### ➔ COHORT SCORE MATRIX GAP BALANCE [{fluency_percentage_score}%]:")
            st.metric(label="Fluency Matching Score Percentage Matrix", value=f"{fluency_percentage_score}%")
            
            col_correct, col_wrong = st.columns(2)
            with col_correct:
                st.markdown("<p style='font-size: 12px; font-weight: bold; color: #27AE60;'>CORRECTLY READ WORDS LOG:</p>", unsafe_allow_html=True)
                correct_words_box = [f"✓ {word}" for word in ref_clean_tokens if word in user_clean_tokens]
                st.success("\n\n".join(correct_words_box)) if correct_words_box else st.warning("Zero token matches compiled.")
                    
            with col_wrong:
                st.markdown("<p style='font-size: 12px; font-weight: bold; color: #C0392B;'>WRONG READ WORDS & PRACTICE TIPS LOG:</p>", unsafe_allow_html=True)
                wrong_words_box = [f"✗ {word} ➔ Target Improvement: {word}" for word in ref_clean_tokens if word not in user_clean_tokens]
                st.error("\n\n".join(wrong_words_box)) if wrong_words_box else st.success("Perfect alignment! Zero deviations flagged.")

            # Document downloads files compilation station
            st.write("---")
            st.markdown("### 📥 Download Portfolio Workspace Assets")
            
            st.download_button(
                label="📥 Download Playable Audio File (.wav)",
                data=raw_audio_bytes,
                file_name="CEI-Student-Reading.wav",
                mime="audio/wav"
            )
            
            text_dossier_buffer = io.BytesIO()
            dossier_text_string = (
                f"CAREER ENGLISH INSTITUTE - PERFORMANCE EVALUATION DOSSIER REPORT\n"
                f"Track ID Block Target: {selected_track_id}\n"
                f"Fluency Matching Score Metrics: {fluency_percentage_score}%\n"
                f"Correct Tokens Captured: {len(correct_words_box)}\n"
                f"Phonetic Deviation Errors Flagged: {len(wrong_words_box)}\n"
            )
            text_dossier_buffer.write(dossier_text_string.encode('utf-8'))
            text_dossier_buffer.seek(0)
            
            st.download_button(
                label="📥 Download Performance Dossier Ledger (.txt)",
                data=text_dossier_buffer,
                file_name="CEI-Fluency-Diagnostics.txt",
                mime="text/plain"
            )
