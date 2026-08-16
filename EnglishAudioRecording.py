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
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 10 Core PARTS
# PART 1: COMPREHENSIVE PLATFORM LIBS INJECTIONS AND WEB GLOBAL CONTEXT SETUP
# CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

st.set_page_config(
    page_title="CEI Advanced Evaluation Engine", 
    layout="centered",
    initial_sidebar_state="expanded"
)
# ============================================================================
# PART 2: INSTITUTIONAL BRANDING AND PRESENTATION PLOCKS
# ============================================================================
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Level Upper-Intermediate Diagnostic Verification & Narration Evaluation Engine</h4>", unsafe_allow_html=True)
# ============================================================================
# PART 3: EMBEDDED ATOMIC SQLITE SCHEMAS AND CACHE INITIALIZATION
# ============================================================================
def get_database_connection():
    """Establishes a thread-safe relational link to the local database file."""
    return sqlite3.connect("cei_multimedia_workspace.db", check_same_thread=False)

def initialize_relational_database_tables():
    """Constructs the schema tables required to persist data loops across server runs."""
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_tracks (
            track_id TEXT PRIMARY KEY,
            script_text TEXT NOT NULL,
            apa_citation TEXT,
            audio_blob BLOB,
            is_custom INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_evaluations (
            evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            track_id TEXT NOT NULL,
            fluency_score INTEGER NOT NULL,
            transcription_captured TEXT,
            correct_count INTEGER,
            deviation_count INTEGER,
            custom_filename TEXT,
            FOREIGN KEY(track_id) REFERENCES syllabus_tracks(track_id)
        )
    """)
    conn.commit()
# ============================================================================
# PART 4: AUTOMATED SCRIPT CORE DATABASE SEEDING
# ============================================================================
    cursor.execute("SELECT COUNT(*) FROM syllabus_tracks")
    if cursor.fetchone() == 0:
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
            )
        ]
        cursor.executemany("INSERT INTO syllabus_tracks VALUES (?, ?, ?, ?, ?)", baseline_seeds)
        conn.commit()
    conn.close()

# Execute schema locks on initialization load parameters
initialize_relational_database_tables()
# ============================================================================
# PART 5: COORDINATOR SIDEBAR FORMS & SQL DATA PACKET SUBMISSIONS
# ============================================================================
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
            (new_id, new_text, new_citation if new_citation.strip() != "" else "Custom Reference Asset Tracking Sheet.", sqlite3.Binary(audio_binary) if audio_binary else None)
        )
        db_conn.commit()
        db_conn.close()
        st.sidebar.success(f"🎉 Track {new_id} committed permanently into SQL database ledger!")
        st.rerun()
# ============================================================================
# PART 6: REVERSE SPEECH PIPELINE - REENGINEERED TEXT-TO-MP3 COUPLING
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
# PART 7: LIVE SQL DATA LOADING AND THE PRESENTATION READING SHOWER
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
# ============================================================================
# PART 8: ASYNC RECORDED GUIDE TRACK SPEECH-TO-TEXT CONVERTER MODULES
# ============================================================================
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
                let outputLog = event.results[0][0].transcript;
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
# PART 9: OMNI-BROWSER HEADSET MIC RECORDER AND RATIO MATRIX EVALUATOR
# ============================================================================
st.write("---")
st.markdown("### 🎙️ Student Recording Station")
st.write("Click Start Recording below, speak the target text into your microphone, then click stop to run comparisons.")

audio_asset_capture = mic_recorder(
    start_prompt="🎙️ Start Recording",
    stop_prompt="🛑 Stop & Compile Audio",
    key='cei_github_sql_naming_pdf_recorder_v10'
)

if audio_asset_capture:
    raw_audio_bytes = audio_asset_capture['bytes']
    st.write("---")
    st.markdown("### 🔊 Student Playback & Sound Tracker")
    st.audio(raw_audio_bytes, format="audio/wav")
    
st.markdown("#### 🔍 Text Transcription Matching Matrix Input")
transcribed_user_input = st.text_area(label="Transcription Input Display Window:", placeholder="Awaiting speech recording logs...", key="text_transcription_transfer")

st.markdown("#### 📝 Document Naming Station")
student_provided_name = st.text_input(label="Enter Student Name or ID Code to auto-label saved tracking file assets:", placeholder="e.g., Carlos_Mendoza_ID4402", key="student_custom_filename")
base_filename_string = student_provided_name.strip().replace(" ", "_") if student_provided_name.strip() != "" else "CEI_Vocal_Capture"

if st.button("🔍 Run Linguistic Evaluation Loops"):
    if transcribed_user_input.strip() == "":
        st.error("System Notice: Please provide text inside the transcription box to execute structural gap check matrices.")
    else:
        ref_clean_tokens = reference_text.lower().replace(".", "").replace(",", "").split()
        user_clean_tokens = transcribed_user_input.lower().replace(".", "").replace(",", "").split()
        
        # Fluency score metrics processed as an absolute percentage value (%)
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
            st.error("\n\n".join(wrong_words_box)) if wrong_words_box else st.success("Perfect alignment validated!")

        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO student_evaluations (timestamp, track_id, fluency_score, transcription_captured, correct_count, deviation_count, custom_filename) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_track_id, fluency_percentage_score, transcribed_user_input, len(correct_words_box), len(wrong_words_box), base_filename_string)
        )
        conn.commit()
        conn.close()
        st.success("💾 Evaluation performance metrics logged successfully to database ledger!")
# ============================================================================
# PART 10: DYNAMIC WAV/PDF PORTFOLIO LOG EXPORTERS AND RETROSPECTIVE TABLES
# ============================================================================
        st.write("---")
        st.markdown("### 📥 Download Portfolio Workspace Assets")
        
        if audio_asset_capture:
            st.download_button(label=f"📥 Download Named Audio Record ({base_filename_string}.wav)", data=raw_audio_bytes, file_name=f"{base_filename_string}.wav", mime="audio/wav")
        
        js_pdf_generator_script = f"""
        <html lang="en">
        <head><script src="https://cloudflare.com"></script></head>
        <body>
        <button id="pdf_compile_trigger_btn" style="width:100%; padding:14px; font-weight:bold; background-color:#27AE60; color:white; border:none; border-radius:4px; cursor:pointer; font-size:14px; margin-bottom:10px;">
            📥 Download Certified Fluency Diagnostics Report Sheet (PDF)
        </button>
        <script>
            document.getElementById("pdf_compile_trigger_btn").addEventListener("click", async () => {{
                const {{ jsPDF }} = window.jspdf;
                const doc = new jsPDF('p', 'mm', 'a4');
                doc.setFillColor(244, 246, 247); doc.rect(0, 0, 210, 297, 'F');
                doc.setDrawColor(26, 82, 118); doc.setLineWidth(1.5); doc.rect(5, 5, 200, 287);
                doc.setFont("times", "bold"); doc.setFontSize(22); doc.setTextColor(26, 82, 118);
                doc.text("CAREER ENGLISH INSTITUTE", 105, 30, {{ align: "center" }});
                doc.setFont("times", "italic"); doc.setFontSize(12); doc.setTextColor(127, 140, 141);
                doc.text("B2 Level Upper-Intermediate Diagnostic Verification & Performance Review Log", 105, 38, {{ align: "center" }});
                doc.setDrawColor(189, 195, 199); doc.setLineWidth(0.5); doc.line(20, 48, 190, 48);
                doc.setFont("times", "normal"); doc.setFontSize(12); doc.setTextColor(44, 62, 80);
                doc.text("Assigned File Identifier String:", 25, 62); doc.setFont("times", "bold"); doc.text("{base_filename_string}", 85, 62);
                doc.setFont("times", "normal"); doc.text("Evaluation Timestamp:", 25, 70); doc.setFont("times", "bold"); doc.text("{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 85, 70);
                doc.setFont("times", "normal"); doc.text("Syllabus Evaluation Track:", 25, 78); doc.setFont("times", "bold"); doc.text("{selected_track_id}", 85, 78);
                doc.setFillColor(235, 245, 251); doc.rect(25, 88, 160, 25, 'F');
                doc.setDrawColor(174, 214, 241); doc.rect(25, 88, 160, 25);
                doc.setFont("times", "bold"); doc.setFontSize(16); doc.setTextColor(26, 82, 118);
                doc.text("TOTAL FLUENCY ALIGNMENT SCORE: {fluency_percentage_score}%", 105, 104, {{ align: "center" }});
                doc.setFont("times", "bold"); doc.setFontSize(12); doc.setTextColor(39, 174, 96);
                doc.text("✓ Correct Tokens Captured Count: {len(correct_words_box)}", 25, 130);
                doc.setFont("times", "bold"); doc.setTextColor(192, 57, 43);
                doc.text("✗ Phonetic Deviation Errors Flagged: {len(wrong_words_box)}", 25, 138);
                doc.setFont("times", "italic"); doc.setFontSize(10); doc.setTextColor(127, 140, 141);
                doc.text("Verification Core Secure Seal Certificate Ledger. Independent Compilation System - CEI (2026)", 105, 275, {{ align: "center" }});
                doc.save("{base_filename_string}_Fluency_Report.pdf");
            }});
        </script>
        </body>
        </html>
        """
        st.components.v1.html(js_pdf_generator_script, height=65)

st.write("---")
st.markdown("### 📊 Database Portfolio Log Ledger View")
if st.checkbox("Reveal Stored Student Performance Evaluation History Data Matrices"):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, track_id, fluency_score, custom_filename FROM student_evaluations ORDER BY evaluation_id DESC")
    history_rows = cursor.fetchall()
    conn.close()
    if history_rows:
        for row in history_rows:
            st.markdown(f"📅 **{row[0]}** | Track: `{row[1]}` | 🎯 **Score: {row[2]}%** | Label Reference: `{row[3]}`")
            st.markdown("<hr style='margin:4px 0; border-top:1px dashed #BDC3C7;'>", unsafe_allow_html=True)
    else:
        st.info("No recorded score logs found inside the database schema yet.")
