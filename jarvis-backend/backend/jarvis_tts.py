# backend/jarvis_tts.py
import pyttsx3
import threading
from logger import logger


def speak(text: str):
    if not text:
        return

    def _run():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.setProperty("volume", 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            logger.exception("TTS failed")

    # Run each speech in its own daemon thread
    threading.Thread(target=_run, daemon=True).start()
