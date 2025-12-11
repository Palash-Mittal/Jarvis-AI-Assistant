import subprocess
from .tools import open_app, google_search, type_text
from .jarvis_memory import save_note
from . import config


def call_ollama(prompt: str, model: str):
    ollama = config.LLM["ollama_executable"]
    cmd = [ollama, "run", model]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate(prompt)
        return out.strip()

    except Exception as e:
        return f"[ERROR calling ollama] {e}"


def decide(message: str, model=None):
    text = message.lower()

    # OPEN APP
    if text.startswith("open "):
        app = message[5:]
        out = open_app(app)
        return {"reply": f"Opening {app}.", "tool_used": "open_app", "tool_output": out}

    # SEARCH
    if text.startswith("search ") or text.startswith("google "):
        query = message.split(" ", 1)[1]
        out = google_search(query)
        return {"reply": f"Searching for {query}.", "tool_used": "google_search", "tool_output": out}

    # TYPE
    if text.startswith("type "):
        to_type = message[5:]
        out = type_text(to_type)
        return {"reply": "Typing text...", "tool_used": "type_text", "tool_output": out}

    # MEMORY
    if text.startswith("note ") or text.startswith("remember "):
        content = message.split(" ", 1)[1]
        save_note(content)
        return {"reply": "Noted.", "tool_used": "memory", "tool_output": content}

    # DEFAULT → LLM
    model = model or config.LLM["default_model"]
    reply = call_ollama(message, model)

    return {"reply": reply, "tool_used": "none", "tool_output": None}
