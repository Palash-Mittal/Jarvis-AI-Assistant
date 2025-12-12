import sys
import json
from jarvis_brain import decide
from jarvis_voice import transcribe_whisper

def send(data):
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()

def listen():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        req = json.loads(line)

        if req.get("command") == "voice_input":
            text = transcribe_whisper()
            send({"text": text})
        else:
            out = decide(req.get("command"))
            send(out)

if __name__ == "__main__":
    send({"status": "jarvis-ready"})
    listen()
