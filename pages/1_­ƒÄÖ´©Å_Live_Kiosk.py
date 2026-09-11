"""
1_🎙️_Live_Kiosk.py
--------------------
Live voice-interaction kiosk page. Passengers (or a demo user) record a
question with their microphone, the app transcribes it with Whisper,
matches an intent, generates a spoken reply, and logs the interaction.
"""

import time
import streamlit as st

from services.ai_processor import transcribe_audio, get_response
from services.tts_engine import synthesize_speech
from database.db_manager import init_db, insert_interaction, fetch_recent

st.set_page_config(page_title="Live Kiosk", page_icon="🎙️", layout="wide")
init_db()

st.title("🎙️ Live Kiosk")
st.caption("Tap the microphone, ask your question, and get an instant answer.")

model_size = st.sidebar.selectbox(
    "Whisper model size", ["tiny", "base", "small", "medium"], index=1
)
st.sidebar.caption("Larger models are more accurate but slower.")

audio_value = st.audio_input("🎤 Record your question")

if audio_value is not None:
    with st.spinner("Transcribing your question..."):
        # Save the recorded bytes to a temp wav file for Whisper.
        temp_path = "temp_live_input.wav"
        with open(temp_path, "wb") as f:
            f.write(audio_value.getvalue())

        start_time = time.time()
        try:
            query_text, language, _ = transcribe_audio(temp_path, model_size)
            response_text, intent = get_response(query_text)
            audio_path = synthesize_speech(response_text, lang="en")
            status = "success"
        except Exception as e:
            query_text, language, intent = "", "unknown", "error"
            response_text = f"Sorry, something went wrong: {e}"
            audio_path = None
            status = "error"

        elapsed = round(time.time() - start_time, 2)

    st.subheader("📝 You asked:")
    st.write(query_text if query_text else "_(no speech detected)_")

    st.subheader("🤖 Assistant response:")
    st.write(response_text)

    if audio_path:
        st.audio(audio_path, format="audio/mp3")

    insert_interaction(
        source="Live Kiosk",
        file_name=None,
        language=language,
        query_text=query_text,
        response_text=response_text,
        intent=intent,
        status=status,
        processing_time=elapsed,
    )

    st.success(f"Processed in {elapsed}s")

st.divider()
st.subheader("🕓 Recent interactions")
recent = fetch_recent(5)
if recent:
    for row in recent:
        with st.expander(f"{row['timestamp']} — {row['intent']}"):
            st.write(f"**Query:** {row['query_text']}")
            st.write(f"**Response:** {row['response_text']}")
else:
    st.caption("No interactions logged yet.")
