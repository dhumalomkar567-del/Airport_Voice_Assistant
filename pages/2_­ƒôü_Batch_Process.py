"""
2_📁_Batch_Process.py
-----------------------
Batch-process page: upload multiple audio files at once (e.g. recorded
kiosk sessions from another location), transcribe + answer each one,
and export the combined results as CSV.
"""

import time
import tempfile
import pandas as pd
import streamlit as st

from services.ai_processor import transcribe_audio, get_response
from services.tts_engine import synthesize_speech
from database.db_manager import init_db, insert_interaction

st.set_page_config(page_title="Batch Process", page_icon="📁", layout="wide")
init_db()

st.title("📁 Batch Process")
st.caption("Upload one or more audio files to transcribe and answer in bulk.")

model_size = st.sidebar.selectbox(
    "Whisper model size", ["tiny", "base", "small", "medium"], index=1
)
generate_audio = st.sidebar.checkbox("Generate spoken replies (slower)", value=False)

uploaded_files = st.file_uploader(
    "Upload audio files (wav, mp3, m4a)",
    type=["wav", "mp3", "m4a"],
    accept_multiple_files=True,
)

if uploaded_files and st.button("🚀 Process Batch"):
    results = []
    progress = st.progress(0.0, text="Starting...")

    for i, uploaded_file in enumerate(uploaded_files):
        progress.progress(
            i / len(uploaded_files),
            text=f"Processing {uploaded_file.name} ({i + 1}/{len(uploaded_files)})",
        )

        suffix = "." + uploaded_file.name.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        start_time = time.time()
        try:
            query_text, language, _ = transcribe_audio(tmp_path, model_size)
            response_text, intent = get_response(query_text)
            status = "success"
            audio_path = synthesize_speech(response_text) if generate_audio else None
        except Exception as e:
            query_text, language, intent = "", "unknown", "error"
            response_text = f"Error: {e}"
            audio_path = None
            status = "error"

        elapsed = round(time.time() - start_time, 2)

        insert_interaction(
            source="Batch Process",
            file_name=uploaded_file.name,
            language=language,
            query_text=query_text,
            response_text=response_text,
            intent=intent,
            status=status,
            processing_time=elapsed,
        )

        results.append(
            {
                "File": uploaded_file.name,
                "Language": language,
                "Query": query_text,
                "Response": response_text,
                "Intent": intent,
                "Status": status,
                "Time (s)": elapsed,
                "Audio Path": audio_path,
            }
        )

    progress.progress(1.0, text="Done!")
    st.success(f"Processed {len(results)} file(s).")

    df = pd.DataFrame(results)
    st.dataframe(df.drop(columns=["Audio Path"]), use_container_width=True)

    csv = df.drop(columns=["Audio Path"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download results as CSV",
        data=csv,
        file_name="batch_results.csv",
        mime="text/csv",
    )

    for row in results:
        if row["Audio Path"]:
            st.audio(row["Audio Path"], format="audio/mp3")
