import sounddevice as sd
import numpy as np
import whisper
import tempfile
import wave

model = whisper.load_model("small")

SAMPLE_RATE = 16000

def record_audio(seconds=4):
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    return np.squeeze(audio)

def save_temp_wav(audio_data, sample_rate=SAMPLE_RATE):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        pcm = (audio_data * 32767).astype(np.int16)
        wf.writeframes(pcm.tobytes())
    return temp.name

def transcribe_whisper():
    audio = record_audio()
    path = save_temp_wav(audio)
    result = model.transcribe(path, fp16=False)
    return result.get("text", "").strip()
