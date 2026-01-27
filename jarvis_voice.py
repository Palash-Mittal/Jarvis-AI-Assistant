#jarvis_voice.py
import sounddevice as sd
import numpy as np
import whisper
import tempfile
import wave
import time

model = whisper.load_model("small")
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 1.2
PREBUFFER_DURATION = 0.3

def wait_for_wake_word_audio(timeout=5):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        audio = record_audio_silence()
        if audio is not None and len(audio) > SAMPLE_RATE * 0.3:
            return audio
    return None


def contains_wake_word(text):
    text = text.lower()

    wake_words = [
        "jarvis",
        "hey jarvis",
        "ok jarvis",
        "jervis",
        "jar vis",
        "service",
        "drivers"
    ]

    return any(w in text for w in wake_words)

def record_audio_silence():
    input_audio_chunks=[]
    prebuffer_chunks = []
    silence_time = 0.0
    input_silence_start_time = None
    max_prebuffer_chunks = int(PREBUFFER_DURATION / CHUNK_DURATION)
    speech_detected = False
    recording_active = True

    def callback(indata, frames, time_info, status):
        nonlocal silence_time, speech_detected, input_silence_start_time, recording_active

        chunk=indata.copy()

        volume = np.max(np.abs(indata))

        prebuffer_chunks.append(chunk)

        if len(prebuffer_chunks) > max_prebuffer_chunks:
            prebuffer_chunks.pop(0)

        if not speech_detected:
            if volume > SILENCE_THRESHOLD:
                speech_detected = True
                input_audio_chunks.extend(prebuffer_chunks)
        else:

            input_audio_chunks.append(chunk)

            if volume < SILENCE_THRESHOLD:
                if input_silence_start_time is None:
                    input_silence_start_time = time.monotonic()
                elif time.monotonic() - input_silence_start_time >= 0.6:

                    recording_active = False
                    raise sd.CallbackStop()
            else:
                input_silence_start_time = None

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=int(CHUNK_DURATION * SAMPLE_RATE),
        callback=callback
    ):
        while recording_active:
            sd.sleep(50)
        
    audio = np.concatenate(input_audio_chunks, axis=0)
    return np.squeeze(audio)


def save_temp_wav(audio_data, sr=SAMPLE_RATE):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        pcm = (audio_data * 32767).astype(np.int16)
        wf.writeframes(pcm.tobytes())
    return temp.name

def strip_wake_word(text):
    text = text.lower()
    for w in ["hey jarvis", "ok jarvis", "jarvis", "jar vis", "jervis", "service", "drivers"]:
        if w in text:
            return text.replace(w, "", 1).strip()
    return ""



def transcribe_whisper():
    audio = wait_for_wake_word_audio()

    if audio is None:
        return ""

    path = save_temp_wav(audio)
    result = model.transcribe(path, fp16=False)
    text = result.get("text", "").strip()

    if not text:
        return ""

    if not contains_wake_word(text):
        return ""

    return strip_wake_word(text)



