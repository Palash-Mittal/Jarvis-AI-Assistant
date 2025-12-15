# backend/jarvis_tts.py
import pyttsx3
import threading
from logger import logger

VOICE_INDEX = 1   # 🔁 change after testing voices
RATE = 165        # slower = more Jarvis-like
VOLUME = 1.0


def speak(text: str):
    if not text:
        return

    def _run():
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")

            if VOICE_INDEX < len(voices):
                engine.setProperty("voice", voices[VOICE_INDEX].id)

            engine.setProperty("rate", RATE)
            engine.setProperty("volume", VOLUME)

            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            logger.exception("TTS failed")

    threading.Thread(target=_run, daemon=True).start()
