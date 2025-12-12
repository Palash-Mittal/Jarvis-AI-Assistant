import subprocess
from tools import open_app, google_search, type_text
from jarvis_memory import save_note
from config import LLM

def call_ollama(prompt: str, model: str):
    cmd = [LLM["ollama_executable"], "run", model]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(prompt)
        return out.strip()
    except Exception as e:
        return f"[ERROR] {e}"

def decide(message: str):
    text = message.lower()

    # OPEN APP
    if text.startswith("open "):
        app = message[5:]
        out = open_app(app)
        return {"reply": f"Opening {app}.", "tool": "open_app", "result": out}

    # SEARCH
    if text.startswith("search ") or text.startswith("google "):
        query = message.split(" ", 1)[1]
        out = google_search(query)
        return {"reply": f"Searching for {query}.", "tool": "google_search", "result": out}

    # TYPE
    if text.startswith("type "):
        to_type = message[5:]
        out = type_text(to_type)
        return {"reply": "Typing text...", "tool": "type_text", "result": out}

    # MEMORY
    if text.startswith("note ") or text.startswith("remember "):
        content = message.split(" ", 1)[1]
        save_note(content)
        return {"reply": "Noted.", "tool": "memory", "result": content}

    # DEFAULT → LLM
    reply = call_ollama(message, LLM["default_model"])
    return {"reply": reply, "tool": "none", "result": None}
