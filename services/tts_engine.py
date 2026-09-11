"""
tts_engine.py
--------------
Converts text responses into speech audio (MP3) using gTTS
(Google Text-to-Speech). The generated file is saved to a temp folder
and its path returned so Streamlit can play it with st.audio().
"""

import uuid
from pathlib import Path

from gtts import gTTS

AUDIO_OUT_DIR = Path(__file__).parent.parent / "audio_output"
AUDIO_OUT_DIR.mkdir(exist_ok=True)


def synthesize_speech(text: str, lang: str = "en") -> str:
    """
    Convert text to speech and save as an MP3 file.
    Returns the path to the generated audio file, or None on failure.
    """
    if not text:
        return None

    # gTTS only understands a small set of language codes; fall back to
    # English if Whisper detected something gTTS doesn't support.
    supported_langs = {"en", "hi", "es", "fr", "de", "ar", "zh-CN", "ja"}
    lang_code = lang if lang in supported_langs else "en"

    try:
        tts = gTTS(text=text, lang=lang_code)
        file_path = AUDIO_OUT_DIR / f"response_{uuid.uuid4().hex[:8]}.mp3"
        tts.save(str(file_path))
        return str(file_path)
    except Exception as e:
        print(f"[tts_engine] TTS generation failed: {e}")
        return None


def cleanup_old_audio(keep_last: int = 20):
    """Optional housekeeping: delete old generated audio files."""
    files = sorted(AUDIO_OUT_DIR.glob("response_*.mp3"), key=lambda f: f.stat().st_mtime)
    for f in files[:-keep_last]:
        try:
            f.unlink()
        except OSError:
            pass
