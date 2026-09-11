"""
main.py
--------
Entry point for the Airport Voice Assistant Streamlit app.
Sets global page config and shows a welcome / navigation landing page.
Use the sidebar to move between the Live Kiosk, Batch Process, and
Admin Dashboard pages.
"""

import streamlit as st
from database.db_manager import init_db, get_summary_stats

st.set_page_config(
    page_title="Airport Voice Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure the database & table exist before anything else runs.
init_db()

st.title("✈️ Airport Voice Assistant")
st.markdown(
    """
    Welcome to the **Airport Voice Assistant** — an AI-powered kiosk system
    that listens to passenger questions, transcribes them with **Whisper**,
    matches an intent, and replies with **synthesized speech**.
    """
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎙️ Live Kiosk")
    st.write(
        "Real-time voice interaction: record a question, get an instant "
        "spoken + text answer."
    )

with col2:
    st.subheader("📁 Batch Process")
    st.write(
        "Upload multiple recorded audio files at once and process them "
        "together — useful for reviewing recorded kiosk sessions."
    )

with col3:
    st.subheader("📊 Admin Dashboard")
    st.write(
        "View usage analytics: total queries, common intents, languages, "
        "and success rate."
    )

st.divider()

stats = get_summary_stats()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Queries", stats["total"])
m2.metric("Successful", stats["success"])
m3.metric("Errors", stats["errors"])
m4.metric("Avg. Processing Time (s)", stats["avg_time"])

st.info("👈 Use the sidebar to navigate to a page.")
