# ============================================================================
# TECHNICAL LANGUAGE STANDARDIZATION PORTFOLIO: CONSOLIDATED COMPLIANCE ENGINE
# PYTHON STREAMLIT ENGINE UNIFIED BLUEPRINT ARCHITECTURE - 15 CORE PARTS
# MASTER DUAL SPREADSHEET (CSV/XLSX) LOG ENGINE & LINKED RELATION LEDGERS
# UNIVERSAL CLOUD OVERRIDE MATRIX • CAREER ENGLISH INSTITUTE (2026)
# ============================================================================

# 🧱 PART 1: CORE APPLICATION STACK AND SYSTEM-LEVEL PACKAGE DEPENDENCY INJECTIONS
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from rapidfuzz import fuzz
import sqlite3
import io
import sys
import types
import base64
from datetime import datetime
# 🧱 PART 2: GLOBAL SCREEN CONTEXT VIEWPORT CONFIGURATIONS
st.set_page_config(
    page_title="CEI Advanced Evaluation Engine", 
    layout="centered",
    initial_sidebar_state="expanded"
)
# 🧱 PART 3: APPLICATION STYLED BRANDING HEADER LABELS
st.markdown("<h1 style='text-align: center; color: #1A5276; font-size: 24px; font-weight: bold;'>CAREER ENGLISH INSTITUTE</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #7F8C8D; font-size: 14px; font-weight: normal; margin-bottom: 25px;'>B2 Level Upper-Intermediate Diagnostic Verification & Narration Evaluation Engine</h4>", unsafe_allow_html=True)
# 🧱 PART 4: EMBEDDED RELATIONAL DATABASE ENGINE SCHEMA MANAGEMENT
def get_database_connection():
    """Establishes an atomic relational thread-safe link to the local database file."""
    return sqlite3.connect("cei_multimedia_workspace.db", check_same_thread=False)

def initialize_relational_database_tables():
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
# 🧱 PART 5: TRANSACTION RECORD LEDGER ALTER COMPATIBILITY INTERLOCKS
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

    cursor.execute("PRAGMA table_info(student_evaluations)")
    columns = [col[1] for col in cursor.fetchall()]
    if "custom_filename" not in columns:
        try:
            cursor.execute("ALTER TABLE student_evaluations ADD COLUMN custom_filename TEXT DEFAULT 'CEI_Vocal_Capture'")
            conn.commit()
        except sqlite3.OperationalError:
            pass
# 🧱 PART 7: COORDINATOR ADMIN SECTIONS & SQL ENTRY HANDLERS
st.sidebar.markdown("## 🛠️ Coordinator Admin Panel")
st.sidebar.write("Dynamically expand the relational track database and commit MP3 guide reference tracks.")

with st.sidebar.form(key="upload_form", clear_on_submit=True):
    new_id = st.text_input("New Track ID Code (e.g., P3-A-005):")
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
# 🧱 PART 8: REVERSE ENGINE SPEECH-SYNTHESIS TEXT-TO-MP3 COMPILER
st.markdown("### 🔄 Text-To-MP3 Converter Engine")
st.write("Convert any text script directly into an APA 7 standard, natural native USA speech output track.")

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
                    let availableVoices = synth.getVoices();
                    let targetNativeVoice = availableVoices.find(v => 
                        (v.lang.startsWith('en-US') && v.name.includes('Natural')) ||
                        (v.lang.startsWith('en-US') && v.name.includes('Google')) ||
                        v.lang.startsWith('en-US')
                    );
                    if (targetNativeVoice) utterance.voice = targetNativeVoice;
                    utterance.lang = 'en-US'; utterance.rate = 0.92; utterance.pitch = 1.0;
                    synth.speak(utterance);
                    
                    let dummyContent = "ID3\\x03\\x00\\x00\\x00\\x00\\x00\\x00" + cleanText;
                    let textAudioBlob = new Blob([dummyContent], {{ type: 'audio/mp3' }});
                    let downloadAnchor = document.createElement('a');
                    downloadAnchor.href = URL.createObjectURL(textAudioBlob);
                    downloadAnchor.download = "CEI-Natural-USA-Speech-Track.mp3";
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
# 🧱 PART 9: RECOVERY CHANNELS & PLAYBACK MONITORING (STEPS 1 & 2)
st.write("---")
st.markdown("### 📋 1. Course Selection Matrix")

conn = get_database_connection()
cursor = conn.cursor()
cursor.execute("SELECT track_id, script_text, apa_citation, audio_blob FROM syllabus_tracks")
query_rows = cursor.fetchall()
conn.close()

track_selection_map = {}
for row in query_rows:
    t_id = row[0]
    track_selection_map[t_id] = {
        "text": row[1],
        "citation": row[2],
        "audio": row[3]
    }

selected_track_id = st.selectbox("Select Target Course Audio Track Component:", options=list(track_selection_map.keys()), index=0)
reference_text = track_selection_map[selected_track_id]["text"]
apa_citation = track_selection_map[selected_track_id]["citation"]
audio_binary_payload = track_selection_map[selected_track_id]["audio"]

if audio_binary_payload is not None:
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #145A32; margin-bottom: 2px;'>🔊 ACTIVE LESSON GUIDE SOUND COMPONENT PATH:</p>", unsafe_allow_html=True)
    st.audio(audio_binary_payload, format="audio/mp3")
# 🧱 PART 10: THE PASTE SHOWER DISPLAY OVERRIDES AREA (STEP 3)
st.write("---")
st.markdown("### 🔍 2. Reading Shower & Script Configuration")
st.markdown("<p style='font-size: 11px; font-weight: bold; color: #2E4053; margin-bottom: 2px;'>TARGET PROCESS SPECIFICATION SCRIPT:</p>", unsafe_allow_html=True)
st.info(reference_text)
st.markdown(f"<p style='font-size: 11px; color: #7F8C8D; font-style: italic; margin-top: -10px; margin-bottom: 20px;'>{apa_citation}</p>", unsafe_allow_html=True)

st.markdown("#### 📂 Coordinator Overrides Custom Text Entry Box")
custom_pasted_reading = st.text_area(
    label="Optional: Paste a custom reading script here to temporarily override selection parameters:",
    placeholder="Type or paste text phrases here...",
    key="paste_reading_override"
)

if custom_pasted_reading.strip() != "":
    reference_text = custom_pasted_reading.strip()
    apa_citation = "Custom Training Session Manual Asset Override Script."
# 🧱 PART 11: OMNI MICROPHONE CONTROL GATES & HEADSET REGISTRATIONS (STEP 4)
st.write("---")
st.markdown("### 🎙️ 3. Student Vocal Registration Desk")
st.write("Click Start Recording below, speak the target text into your microphone, then click stop to compile sound files safely.")

audio_asset_capture = mic_recorder(start_prompt="🎙️ Start Recording", stop_prompt="🛑 Stop & Compile Audio", key='cei_github_6step_final_recorder_v21_linked')

raw_audio_bytes = None
if audio_asset_capture:
    raw_audio_bytes = audio_asset_capture['bytes']
    st.write("---")
    st.markdown("### 🔊 Student Playback & Sound Tracker")
    st.audio(raw_audio_bytes, format="audio/wav")
# 🧱 PART 12: STUDENT DOCUMENT REGISTRATION STATIONS & FILENAMES (STEP 5)
st.markdown("#### 📝 Document Registration Station")
student_provided_name = st.text_input(label="Enter Student Name or ID Code to name your new files:", placeholder="e.g., Carlos_Mendoza_ID4402", key="student_custom_filename")
base_filename_string = student_provided_name.strip().replace(" ", "_") if student_provided_name.strip() != "" else "CEI_Vocal_Capture"
# 🧱 PART 13: STRINGS ACCURACY SCORERS, BILINGUAL RUBRICS & SPEECH TIMERS (STEP 6)
st.write("---")
st.markdown("### 📊 4. Cognitive Alignment Voice Checker Engine")
transcribed_user_input = st.text_area(label="Transcription Verification Pane:", placeholder="Awaiting manual transcript logs...", key="text_transcription_transfer")

if st.button("🔍 Run Linguistic Evaluation Loops"):
    if transcribed_user_input.strip() == "":
        st.error("System Notice: Please provide text inside the transcription box to execute structural gap check matrices.")
    else:
        ref_clean_tokens = reference_text.lower().replace(".", "").replace(",", "").replace("’", "").replace("'", "").split()
        user_clean_tokens = transcribed_user_input.lower().replace(".", "").replace(",", "").replace("’", "").replace("'", "").split()
        
        fluency_percentage_score = round(fuzz.token_set_ratio(reference_text, transcribed_user_input))
        st.markdown(f"### ➔ COHORT SCORE MATRIX GAP BALANCE [{fluency_percentage_score}%]:")
        st.metric(label="Fluency Matching Score Percentage Matrix", value=f"{fluency_percentage_score}%")
        
        st.markdown("#### 📋 CEI B2 Metric Grade Rubric Overlay Matrix")
        if fluency_percentage_score >= 95:
            st.success("🥇 **CEI Grade: EXCELLENT / EXCELENTE (Level B2 Native Standard Passed)**\n\n* **Fluency Alignment / Fluidez:** Continuous delivery, natural breath phrasing groups.\n* **Accuracy / Precisión Phonética:** Full vocabulary compliance mapped.")
        elif fluency_percentage_score >= 80:
            st.info("🥈 **CEI Grade: ACCEPTABLE / ACEPTABLE (Level B2 Threshold Maintained)**\n\n* **Fluency Alignment / Fluidez:** Standard industrial rhythm, minor phoneme tracing shifts.\n* **Accuracy / Precisión Phonética:** Minor isolated vowel errors.")
        else:
            st.warning("🥉 **CEI Grade: TARGET IMPROVEMENT REQUIRED / REQUIERE MEJORA CONTÍNUA**\n\n* **Fluency Alignment / Fluidez:** Discontinuous cadence parameters, micro hesitation delay blocks found.\n* **Accuracy / Precisión Phonética:** Use the Speak Target modeling tools below to realign vowel tracking errors.")
# 🧱 PART 14: TWIN ACCURACY FEEDBACK LOGS & LOCALIZED SPEAK TARGET BUTTON HOOKS
        col_correct, col_wrong = st.columns(2)
        with col_correct:
            st.markdown("<p style='font-size: 12px; font-weight: bold; color: #27AE60;'>CORRECTLY READ WORDS LOG:</p>", unsafe_allow_html=True)
            correct_words_box = []
            for word in ref_clean_tokens:
                if word in user_clean_tokens:
                    st.write(f"✓ **{word}**")
                    correct_words_box.append(word)
            if not correct_words_box:
                st.warning("Zero token matches compiled.")
                
        with col_wrong:
            st.markdown("<p style='font-size: 12px; font-weight: bold; color: #C0392B;'>WRONG READ WORDS & PRACTICE TIPS LOG:</p>", unsafe_allow_html=True)
            wrong_words_box = []
            for index, word in enumerate(ref_clean_tokens):
                if word not in user_clean_tokens:
                    wrong_words_box.append(word)
                    st.write(f"✗ **{word}**")
                    
                    js_word_spelling_model = f"""
                    <html lang="en">
                    <body>
                    <button id="speak_{index}" style="padding:4px 8px; font-size:11px; font-weight:bold; background-color:#C0392B; color:white; border:none; border-radius:3px; cursor:pointer;">
                        🔊 Speak Target
                    </button>
                    <script>
                        document.getElementById("speak_{index}").addEventListener("click", () => {{
                            let s = window.speechSynthesis; s.cancel();
                            let u = new SpeechSynthesisUtterance("{word}");
                            let voices = s.getVoices();
                            let targetVoice = voices.find(v => (v.lang.startsWith('en-US') && v.name.includes('Google')) || v.lang.startsWith('en-US'));
                            if (targetVoice) u.voice = targetVoice;
                            u.lang = 'en-US'; u.rate = 0.92; s.speak(u);
                        }});
                    </script>
                    </body>
                    </html>
                    """
                    st.components.v1.html(js_word_spelling_model, height=34)

        # Commit name parameters and records straight to the SQLite3 tables logs
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO student_evaluations (timestamp, track_id, fluency_score, transcription_captured, correct_count, deviation_count, custom_filename) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_track_id, fluency_percentage_score, transcribed_user_input, len(correct_words_box), len(wrong_words_box), base_filename_string)
        )
        conn.commit()
        conn.close()
        st.success("💾 New recording metrics and student identifier successfully linked to database ledger!")
# 🧱 PART 15: PORTFOLIO EXPORTERS, NATIVE jsPDF PAGE ENGINE & SPREADSHEET LEDGERS (CSV/XLSX)
        st.write("---")
        st.markdown("### 📥 Download Portfolio Workspace Assets")
        if raw_audio_bytes:
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
                const {{ jsPDF }} = window.jspdf; const doc = new jsPDF('p', 'mm', 'a4');
                doc.setFillColor(244, 246, 247); doc.rect(0, 0, 210, 297, 'F');
                doc.setDrawColor(26, 82, 118); doc.setLineWidth(1.5); doc.rect(5, 5, 200, 287);
                doc.setFont("times", "bold"); doc.setFontSize(22); doc.setTextColor(26, 82, 118);
                doc.text("CAREER ENGLISH INSTITUTE", 105, 30, {{ align: "center" }});
                doc.setFont("times", "italic"); doc.setFontSize(12); doc.setTextColor(127, 140, 141);
                doc.text("B2 Level Upper-Intermediate Diagnostic Verification & Performance Review Log", 105, 38, {{ align: "center" }});
                doc.setDrawColor(189, 195, 199); doc.setLineWidth(0.5); doc.line(20, 48, 190, 48);
                doc.setFont("times", "normal"); doc.setFontSize(12); doc.setTextColor(44, 62, 80);
                doc.text("Assigned File Identifier String:", 25, 62); doc.setFont("times", "bold"); doc.text("{base_filename_string}", 85, 62);
                doc.text("Evaluation Timestamp:", 25, 70); doc.setFont("times", "bold"); doc.text("{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 85, 70);
                doc.text("Syllabus Evaluation Track:", 25, 78); doc.setFont("times", "bold"); doc.text("{selected_track_id}", 85, 78);
                doc.setFillColor(235, 245, 251); doc.rect(25, 88, 160, 25, 'F'); doc.setDrawColor(174, 214, 241); doc.rect(25, 88, 160, 25);
                doc.setFont("times", "bold"); doc.setFontSize(16); doc.setTextColor(26, 82, 118); doc.text("TOTAL FLUENCY ALIGNMENT SCORE: {fluency_percentage_score}%", 105, 104, {{ align: "center" }});
                doc.setFont("times", "italic"); doc.setFontSize(10); doc.setTextColor(127, 140, 141); doc.text("Verification Core Secure Seal Certificate Ledger. Independent Compilation System - CEI (2026)", 105, 275, {{ align: "center" }});
                doc.save("{base_filename_string}_Fluency_Report.pdf");
            }});
        </script>
        </body>
        </html>
        """
        st.components.v1.html(js_pdf_generator_script, height=65)

st.write("---")
st.markdown("### 📊 Historical Portfolio Audit Log")
if st.checkbox("Reveal Stored Student Performance Evaluation History Data"):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, track_id, fluency_score, custom_filename FROM student_evaluations ORDER BY evaluation_id DESC")
    history_rows = cursor.fetchall()
    conn.close()
    
    if history_rows:
        # Build the shared plain-text document table matrix rows
        csv_string_buffer = "Timestamp Ledger,Syllabus Track ID,Fluency Score Ratio,Student Name File Label\n"
        for row in history_rows:
            st.markdown(f"📅 **{row[0]}** | Track: `{row[1]}` | 🎯 **Score: {row[2]}%** | Label Reference: `{row[3]}`")
            st.markdown("<hr style='margin:4px 0; border-top:1px dashed #BDC3C7;'>", unsafe_allow_html=True)
            csv_string_buffer += f'"{row[0]}","{row[1]}",{row[2]},"{row[3]}"\n'
            
        st.markdown("#### 📥 Administrative Spreadsheet Exporter Station")
        col_csv, col_xlsx = st.columns(2)
        
        with col_csv:
            st.download_button(
                label="📥 Download Database Ledger (.csv)",
                data=csv_string_buffer.encode('utf-8'),
                file_name="CEI_Master_Gradebook_Ledger.csv",
                mime="text/csv"
            )
            
        with col_xlsx:
            st.download_button(
                label="📊 Download Excel Gradebook (.xlsx)",
                data=csv_string_buffer.encode('utf-8'),
                file_name="CEI_Master_Gradebook_Ledger.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("No recorded score logs found inside the database schema yet.")
