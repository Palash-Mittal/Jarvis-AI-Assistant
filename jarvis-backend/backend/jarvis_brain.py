# backend/jarvis_brain.py

import subprocess
import re
from jarvis_tts import speak
from tools import open_app, google_search, type_text
from jarvis_memory import (
    add_memory,
    get_all_memory,
    find_memory_by_key
)
import config
from logger import logger


# -------------------- LLM CONFIG --------------------

OLLAMA = config.LLM.get("ollama_executable", "ollama")
DEFAULT_MODEL = config.LLM.get("default_model", "gemma2")
OLLAMA_TIMEOUT = config.LLM.get("ollama_timeout_s", 30)


# -------------------- LLM CALL --------------------

def call_ollama(prompt: str, model: str | None = None, timeout: int | None = None):
    model = model or DEFAULT_MODEL
    timeout = timeout or OLLAMA_TIMEOUT
    cmd = [OLLAMA, "run", model]

    logger.debug(f"Running Ollama: {cmd}")

    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            timeout=timeout,
            text=True,
            encoding="utf-8",     # force UTF-8
            errors="replace"      # never crash on bad chars
        )

        if proc.returncode != 0:
            logger.error(f"Ollama stderr: {proc.stderr}")
            return "[ERROR] Ollama failed"

        return proc.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.exception("Ollama call timed out")
        return "[ERROR] Ollama timed out"

    except Exception as e:
        logger.exception("Ollama call crashed")
        return f"[ERROR] {e}"


# -------------------- COMMAND CLASSIFIER --------------------

def classify_command(text: str):
    t = text.strip().lower()

    # ----- TOOLS -----
    if t.startswith("open "):
        return ("tool", "open_app", text[5:].strip())

    if t.startswith("search ") or t.startswith("google "):
        return ("tool", "google_search", text.split(" ", 1)[1])

    if t.startswith("type "):
        return ("tool", "type_text", text.split(" ", 1)[1])

    # ----- MEMORY -----
    if t.startswith("remember that "):
        return ("memory", "remember", text[14:].strip())

    if t.startswith("note "):
        return ("memory", "note", text[5:].strip())

    if "what do you remember" in t or "list memory" in t:
        return ("memory", "list", None)

    if "my name is" in t:
        return ("memory", "set_name", text.split("my name is", 1)[1].strip())

    if "what is my name" in t:
        return ("memory", "get_name", None)

    # ----- META -----
    if t in ("health", "status", "ping"):
        return ("meta", "health", None)

    if t in ("shutdown", "exit", "quit"):
        return ("meta", "shutdown", None)

    # ----- DEFAULT -----
    return ("llm", None, None)


# -------------------- DECISION ENGINE --------------------

def decide(message: str, model: str | None = None):
    if not message or not message.strip():
        return {"reply": "Empty command.", "tool": "none", "result": None}

    message = message.strip()
    logger.info(f"Received command: {message}")

    typ, action, payload = classify_command(message)

    # -------- TOOL HANDLING --------
    if typ == "tool":
        if action == "open_app":
            reply = f"Opening {payload}."
            speak(reply)
            result = open_app(payload)
            return {"reply": reply, "tool": "open_app", "result": result}


        if action == "google_search":
            reply = f"Searching for {payload}."
            speak(reply)
            result = google_search(payload)
            return {"reply": reply, "tool": "google_search", "result": result}


        if action == "type_text":
            result = type_text(payload)
            return {"reply": "Typing text.", "tool": "type_text", "result": result}

    # -------- MEMORY HANDLING --------
    if typ == "memory":
        if action == "remember":
            reply = "I will remember that."
            speak(reply)
            add_memory("fact", payload)
            return {"reply": reply, "tool": "memory", "result": payload}


        if action == "note":
            add_memory("note", payload)
            return {"reply": "Noted.", "tool": "memory", "result": payload}

        if action == "list":
            rows = get_all_memory()
            if not rows:
                return {
                    "reply": "I don't remember anything yet.",
                    "tool": "memory",
                    "result": []
                }

            text = "\n".join(f"- {r[2]}" for r in rows[:10])
            return {
                "reply": "Here is what I remember:\n" + text,
                "tool": "memory",
                "result": rows
            }

        if action == "set_name":
            reply = f"Got it. Your name is {payload} sir."
            speak(reply)
            add_memory("preference", payload, key="name")
            return {"reply": reply, "tool": "memory", "result": payload}


        if action == "get_name":
            name = find_memory_by_key("name")
            if name:
                reply = f"Your name is {name} sir."
            else:
                reply = "I don't know your name yet sir."

            speak(reply)
            return {"reply": reply, "tool": "memory", "result": name}


    # -------- META HANDLING --------
    if typ == "meta":
        if action == "health":
            return {"reply": "OK", "tool": "meta", "result": {"status": "ok"}}

        if action == "shutdown":
            return {
                "reply": "Shutting down.",
                "tool": "meta",
                "result": {"shutdown": True}
            }

    # -------- LLM FALLBACK --------
    model_override = None
    mo = re.match(r"^model=([^\s]+)\s+(.*)$", message, re.I)
    prompt = message

    if mo:
        model_override = mo.group(1)
        prompt = mo.group(2)
        logger.info(f"Model override: {model_override}")

    model_to_use = model_override or model or DEFAULT_MODEL
    reply = call_ollama(prompt, model_to_use)
    speak(reply)
    return {"reply": reply, "tool": "none", "result": None}
