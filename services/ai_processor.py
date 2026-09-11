"""
ai_processor.py
----------------
Wraps OpenAI's Whisper (via faster-whisper) for speech-to-text, and
implements a lightweight rule-based intent engine that answers common
airport passenger queries (flight status, gate, baggage, security,
lounge, wifi, boarding, restroom, etc.)

Swap `get_response()` with a call to a real flight-info API / LLM
whenever one is available -- the interface is intentionally simple.
"""

import time
import streamlit as st

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


# ---------------------------------------------------------------------
# Whisper model loading (cached so it only loads once per session)
# ---------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading speech recognition model...")
def load_whisper_model(model_size: str = "base"):
    if not WHISPER_AVAILABLE:
        return None
    # device="cpu" so this works out-of-the-box on any machine;
    # switch to "cuda" if a GPU is available.
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(audio_path: str, model_size: str = "base"):
    """
    Transcribe an audio file to text.

    Returns: (text, detected_language, duration_seconds)
    """
    start = time.time()
    model = load_whisper_model(model_size)

    if model is None:
        # Fallback so the UI never crashes if faster-whisper isn't installed.
        return "[faster-whisper not installed]", "unknown", 0.0

    segments, info = model.transcribe(audio_path, beam_size=5)
    text = " ".join(segment.text.strip() for segment in segments)
    duration = round(time.time() - start, 2)
    return text.strip(), info.language, duration


# ---------------------------------------------------------------------
# Rule-based intent + FAQ response engine
# ---------------------------------------------------------------------
FAQ_RULES = [
    (["flight status", "delay", "on time", "landed", "departed"],
     "flight_status",
     "Please share your flight number at the information desk or check the "
     "nearest departure board for real-time flight status."),
    (["gate", "boarding gate", "which gate"],
     "gate_info",
     "Gate numbers are shown on your boarding pass and on the terminal "
     "display screens. Gates may change up to 30 minutes before departure."),
    (["baggage", "luggage", "suitcase", "lost bag"],
     "baggage",
     "Baggage claim carousels are located on the arrivals level. For lost "
     "or delayed baggage, please visit the Baggage Services counter."),
    (["security", "checkpoint", "scanner"],
     "security",
     "Security checkpoints are located before each terminal gate area. "
     "Please keep your boarding pass and ID ready."),
    (["lounge", "business lounge", "vip"],
     "lounge",
     "Airline lounges are located near the boarding gates in each "
     "terminal. Access depends on your ticket class or lounge membership."),
    (["wifi", "internet", "wi-fi"],
     "wifi",
     "Free airport Wi-Fi is available; connect to the 'Airport-Free-WiFi' "
     "network and follow the on-screen instructions."),
    (["restroom", "toilet", "washroom", "bathroom"],
     "restroom",
     "Restrooms are available on every floor, near the elevators and "
     "food court areas."),
    (["boarding time", "when do we board", "boarding pass"],
     "boarding",
     "Boarding usually begins 45 minutes before departure. Please be at "
     "your gate at least 30 minutes prior."),
    (["taxi", "cab", "transport", "how do i get to"],
     "transport",
     "Taxis, ride-shares, and airport shuttles are available at the "
     "ground transportation area outside arrivals."),
]

DEFAULT_RESPONSE = (
    "I'm sorry, I didn't quite catch that. Could you please repeat your "
    "question, or ask an airport staff member for assistance?"
)


def get_response(query_text: str):
    """
    Very lightweight intent matcher: scans the transcribed text for
    keywords and returns the matching canned answer + intent label.

    Returns: (response_text, intent_label)
    """
    if not query_text:
        return DEFAULT_RESPONSE, "unknown"

    text_lower = query_text.lower()
    for keywords, intent, response in FAQ_RULES:
        if any(keyword in text_lower for keyword in keywords):
            return response, intent

    return DEFAULT_RESPONSE, "unrecognized"
