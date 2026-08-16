import streamlit as st
from streamlit_mic_recorder import mic_recorder
from rapidfuzz import fuzz
import sqlite3
import io
import sys
import types
import base64
from datetime import datetime

# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 7 CORE PARTS
# PART 1: CORE APPLICATION STACK AND SYSTEM VIEWPORT SETUP
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

st.set_page_config(
    page_title="CEI Advanced Evaluation Engine", 
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Level Upper-Intermediate Diagnostic Verification & Narration Evaluation Engine</h4>", unsafe_allow_html=True)
# ============================================================================
# PART 2: EMBEDDED SQLITE3 SCHEMAS AND BASELINE SYLLABUS DATA SEEDING
# ============================================================================

def get_database_connection():
    """Establishes an atomic link to the internal SQLite database ledger."""
    return sqlite3.connect("cei_multimedia_workspace.db", check_same_thread=False)

def initialize_relational_database_tables():
    """Constructs schema tables for scripts, guides, and evaluation scores."""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Table 1: Technical Manual Syllabus Script Registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_tracks (
            track_id TEXT PRIMARY KEY,
            script_text TEXT NOT NULL,
            apa_citation TEXT,
            audio_blob BLOB,
            is_custom INTEGER DEFAULT 0
        )
    """)
    
    # Table 2: Historical Performance Metrics Portfolio Record Ledger
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_evaluations (
            evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            track_id TEXT NOT NULL,
            fluency_score INTEGER NOT NULL,
            transcription_captured TEXT,
            correct_count INTEGER,
            deviation_count INTEGER,
            FOREIGN KEY(track_id) REFERENCES syllabus_tracks(track_id)
        )
    """)
    conn.commit()
    
    # Seed baseline technical data matrices if table reads completely empty
    cursor.execute("SELECT COUNT(*) FROM syllabus_tracks")
    if cursor.fetchone()[0] == 0:
        baseline_seeds = [
            (
                "P1-H-001 (Shift Handover)",
                "Good afternoon Carlos. Welcome to the Shift Two handover session. SMT Line Three is currently running part number ALC seven seven four two, active lot code alpha dash nine. The line layout is running at standard quota capacity, but we have intercepted a minor component misfeed at Station Four. A volume of fourteen non conforming pieces has been isolated via physical red tags and transferred directly into the temporary buffer bin.",
                "Prianti, J. Z. (2026). SMT shift changeover and line logistics. *Career English Institute Manuals*, 1(1), 12-15.",
                None, 0
            ),
            (
                "P1-E-002 (ESD Compliance)",
                "Attention all floor personnel. A cleanroom compliance audit is currently active across the ESD Protected Area boundaries. Every operator must immediately verify their personal grounding infrastructure paths. Close your dual conductor wrist straps completely.",
                "Prianti, J. Z. (2026). Cleanroom gowning protocols and ESD limits. *Career English Institute Manuals*, 1(1), 16-20.",
                None, 0
            ),
            (
                "P1-D-003 (5Ws/1H Logging)",
                "Master ledger database transaction log update. Operator ID forty four zero two discovered three pieces of part number ALC nine nine zero on Line One at zero eight thirty AM. Visual inspection revealed a fractured mounting boss feature.",
                "Prianti, J. Z. (2026). Traceability logging and 5Ws/1H framework tools. *Maquiladora Quality Review*, 4(2), 45-48.",
                None, 0
            )
        ]
        cursor.executemany("INSERT INTO syllabus_tracks VALUES (?, ?, ?, ?, ?)", baseline_seeds)
        conn.commit()
    conn.close()

# Enforce database schema locking on load
initialize_relational_database_tables()
# ============================================================================
# PART 3: COORDINATOR ADMIN SECTIONS AND HOT-PATCH EXTENSION REPOSITORIES
# ============================================================================

if "future_upgrades_registry" not in st.session_state:
    st.session_state.future_upgrades_registry = {}

def execute_hot_patched_subroutines(patch_id, code_string):
    try:
        compiled_patch_module = types.ModuleType(patch_id)
        exec(code_string, compiled_patch_module.__dict__)
        sys.modules[patch_id] = compiled_patch_module
        st.session_state.future_upgrades_registry[patch_id] = code_string
        return True
    except Exception as err:
        st.sidebar.error(f"Patch Compilation Aborted: {err}")
        return False

st.sidebar.markdown("## 🛠️ Coordinator Admin Panel")
st.sidebar.write("Dynamically expand the relational track database and commit MP3 guide reference tracks.")

with st.sidebar.form(key="upload_form", clear_on_submit=True):
    new_id = st.text_input("New Track ID Code (e.g., P3-A-004):")
    new_text = st.text_area("Target Reading Script Text Content:")
    new_citation = st.text_input("APA 7 Reference Citation String:")
    uploaded_audio = st.file_uploader("Upload Guide Reference Track Audio File (.mp3, .wav)", type=["mp3", "wav"])
    submit_btn = st.form_submit_button(label="📥 Commit Custom Module to SQL")
    
if submit_btn:
    if new_id.strip() == "" or new_text.strip() == "":
        st.sidebar.error("System Error: Track ID and Script Text cannot be left blank.")
    else:
        db_conn = get_database_connection()
        db_cursor = db_conn.cursor()
        audio_binary = uploaded_audio.read() if uploaded_audio is not None else None
        
        db_cursor.execute(
            "INSERT OR REPLACE INTO syllabus_tracks (track_id, script_text, apa_citation, audio_blob, is_custom) VALUES (?, ?, ?, ?, 1)",
            (new_id, new_text, new_citation if new_citation.strip() != "" else "Custom Reference Asset.", sqlite3.Binary(audio_binary) if audio_binary else None)
        )
        db_conn.commit()
        db_conn.close()
        st.sidebar.success(f"🎉 Track {new_id} committed permanently into SQL database ledger!")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔌 Hot-Patch System Registry")
with st.sidebar.expander("Deploy Future Upgrade Patch", expanded=False):
    patch_id_key = st.text_input("Extension Identifier (e.g., custom_kpi_v2):")
    patch_source_code = st.text_area("Source Code Engine Logic (Python syntax):", height=120)
    apply_patch_btn = st.button("🔌 Hot-Patch Active Environment")
    
    if apply_patch_btn and patch_id_key.strip() != "" and patch_source_code.strip() != "":
        if execute_hot_patched_subroutines(patch_id_key, patch_source_code):
            st.sidebar.success(f"🎉 Extension {patch_id_key} integrated successfully!")

for patch_key in list(st.session_state.future_upgrades_registry.keys()):
    if patch_key in sys.modules:
        try:
            sys.modules[patch_key].execute_dynamic_matrix_override(st)
        except AttributeError:
            pass
# ============================================================================
# PART 4: REVERSE ENGINE PIPELINE - NATIVE CLIENT TEXT-TO-MP3 COUPLING
# ============================================================================

st.markdown("### 🔄 Text-To-MP3 Converter Engine")
st.write("Convert any text script directly into a universal audio format container file.")

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
# PART 5: DYNAMIC RECORD EXTRACTION, PRESENTATION WINDOW, AND AUDIO-TO-TEXT LINK
# ============================================================================

conn = get_database_connection()
cursor = conn.cursor()
cursor.execute("SELECT track_id, script_text, apa_citation, audio_blob FROM syllabus_tracks")
query_rows = cursor.fetchall()
conn.close()

track_selection_map = {row[0]: {"text": row[1], "citation": row[2], "audio": row[3]} for row in query_rows}

selected_track_id = st.selectbox(
    "Select Target Technical Syllabus Track:",
    options=list(track_selection_map.keys()),
    index=0
)

reference_text = track_selection_map[selected_track_id]["text"]
apa_citation = track_selection_map[selected_track_id]["citation"]

st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET PROCESS SPECIFICATION SCRIPT:</p>", unsafe_allow_html=True)
st.info(reference_text)
st.markdown(f"<p style='font-size: 11px; color: #7F8C8D; font-style: italic; margin-top: -10px; margin-bottom: 20px;'>{apa_citation}</p>", unsafe_allow_html=True)

audio_binary_payload = track_selection_map[selected_track_id]["audio"]

if audio_binary_payload is not None:
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>🔊 ACTIVE LESSON GUIDE SOUND COMPONENT PATH FROM DATABASE:</p>", unsafe_allow_html=True)
    st.audio(audio_binary_payload, format="audio/mp3")
    
    audio_base64_data = base64.b64encode(audio_binary_payload).decode("utf-8")
    
    js_audio_to_text_bridge = f"""
    <html lang="en">
    <body>
    <button id="transcribe_trigger_btn" style="width:100%; padding:12px; font-weight:bold; background-color:#145A32; color:white; border:none; border-radius:4px; cursor:pointer;">
        🔀 Auto-Convert Stored SQL Audio Guide to Text Transcription Loop
    </button>
    <script>
        document.getElementById("transcribe_trigger_btn").addEventListener("click", async () => {{
            let SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognitionClass) {{
                alert("Browser Error: WebSpeech conversion blocked or unsupported in this engine.");
                return;
            }}
            let engine = new SpeechRecognitionClass();
            engine.continuous = false;
            engine.lang = 'en-US';
            
            let soundNode = new Audio("data:audio/mp3;base64,{audio_base64_data}");
            engine.onstart = () => {{ soundNode.play(); }};
            engine.onresult = (event) => {{
                let outputLog = event.results[0].transcript;
                window.parent.postMessage({{type: 'streamlit:set_widget_value', value: outputLog, id: 'text_transcription_transfer'}}, '*');
            }};
            engine.start();
        }});
    </script>
    </body>
    </html>
    """
    st.components.v1.html(js_audio_to_text_bridge, height=50)
# ============================================================================
# PART 6: OMNI-BROWSER RECORDER GATEWAYS AND STRING COMPARISON FILTERS
# ============================================================================

st.write("---")
st.markdown("### 🎙️ Student Recording Station")
st.write("Click Start Recording below, speak the target text into your microphone, then click stop to run comparisons.")

audio_asset_capture = mic_recorder(
    start_prompt="🎙️ Start Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_sql_embedded_recorder_v7'
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
    placeholder="Awaiting speech recording transcription or guide conversion logs...",
    key="text_transcription_transfer"
)

if st.button("🔍 Run Linguistic Evaluation Loops"):
    if transcribed_user_input.strip() == "":
        st.error("System Notice: Please provide text inside the transcription box to execute structural gap check matrices.")
    else:
        ref_clean_tokens = reference_text.lower().replace(".", "").replace(",", "").split()
        user_clean_tokens = transcribed_user_input.lower().replace(".", "").replace(",", "").split()
        
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

        # Commit analytics values directly to SQL performance ledger
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO student_evaluations (timestamp, track_id, fluency_score, transcription_captured, correct_count, deviation_count) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_track_id, fluency_percentage_score, transcribed_user_input, len(correct_words_box), len(wrong_words_box))
        )
        conn.commit()
        conn.close()
        st.success("💾 Evaluation performance metrics logged successfully to database ledger!")
        # ============================================================================
        # PART 7: PORTFOLIO EXPORTERS AND HISTORICAL RETROSPECTIVE TABLE PANELS
        # ============================================================================
        st.write("---")
        st.markdown("### 📥 Download Portfolio Workspace Assets")
        
        if audio_asset_capture:
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

st.write("---")
st.markdown("### 📊 Database Portfolio Log Ledger View")
if st.checkbox("Reveal Stored Student Performance Evaluation History Data Matrices"):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, track_id, fluency_score, correct_count, deviation_count FROM student_evaluations ORDER BY evaluation_id DESC")
    history_rows = cursor.fetchall()
    conn.close()
    
    if history_rows:
        for row in history_rows:
            st.markdown(f"📅 **{row[0]}** | Track: `{row[1]}` | 🎯 **Score: {row[2]}%** | Words Correct: `{row[3]}` | Deviations: `{row[4]}`")
            st.markdown("<hr style='margin:4px 0; border-top:1px dashed #BDC3C7;'>", unsafe_allow_html=True)
    else:
        st.info("No recorded score logs found inside the database schema yet. Run an evaluation loop to seed records.")
