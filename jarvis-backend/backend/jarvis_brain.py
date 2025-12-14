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

JARVIS_SYSTEM_PROMPT = """
You are Jarvis, a calm, intelligent, and professional AI assistant.

Your personality:
- Speak in a composed, confident, and respectful tone.
- Address the user as "sir" naturally and sparingly (once per response at most).
- Sound helpful and reassuring, never robotic or overly verbose.
- Maintain a refined, Iron Man-style assistant demeanor.

Your behavior:
- Always respond and clearly.
- When a task or tool has been completed, acknowledge it smoothly and naturally.
- Do not describe internal reasoning, tools, models, or system processes.
- Do not mention technical details, code, or implementation.
- Focus only on the result and the user's intent.

Your goal:
- Anticipate the user's needs.
- Communicate efficiently.
- Make interactions feel seamless, intelligent, and polished.

You are Jarvis.
"""

TOOL_DEFINITIONS = """
You can use the following tools:

1. open_app(app_name: str)
   - Opens an application on the system.

2. google_search(query: str)
   - Searches the web for information.

3. type_text(text: str)
   - Types text using the keyboard.

4. remember(text: str)
   - Saves information to long-term memory.

5. forget(text: str)
   - Deletes information from memory.

Rules:
- If multiple actions are requested, return them in order.
- If no tool is needed, return an empty list.
- Respond ONLY in valid JSON.
"""


# -------------------- SHORT-TERM MEMORY --------------------

SHORT_TERM_CONTEXT = []
MAX_CONTEXT_TURNS = 6

def add_to_short_term(role: str, text: str):
    SHORT_TERM_CONTEXT.append(f"{role}: {text}")
    if len(SHORT_TERM_CONTEXT) > MAX_CONTEXT_TURNS:
        SHORT_TERM_CONTEXT.pop(0)


def get_short_term_context():
    if not SHORT_TERM_CONTEXT:
        return "No recent conversation."
    return "\n".join(SHORT_TERM_CONTEXT)

def forget_memory(keyword: str):
    memories = get_all_memory()
    removed = []

    for mem in memories:
        mem_id, mem_type, content, key = mem
        if keyword.lower() in content.lower() or (key and keyword.lower() in key.lower()):
            from jarvis_memory import delete_memory_by_id
            delete_memory_by_id(mem_id)
            removed.append(content)

    return removed

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

def jarvis_reply(user_message: str, context: str = ""):
    memories = get_relevant_memory(user_message)
    short_term = get_short_term_context()

    memory_block = ""
    if memories:
        memory_block = "Relevant long-term memory:\n" + "\n".join(f"- {m}" for m in memories)

    prompt = f"""
{JARVIS_SYSTEM_PROMPT}

Recent conversation:
{short_term}

{memory_block}

Context:
{context}

User said:
{user_message}

Respond as Jarvis:
"""

    reply = call_ollama(prompt)

    # update short-term memory
    add_to_short_term("User", user_message)
    add_to_short_term("Jarvis", reply)

    return reply



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
    
    if t.startswith("forget "):
        return ("memory", "forget", text[7:].strip())

    if "forget what you remember about" in t:
        return ("memory", "forget", text.split("about", 1)[1].strip())


    # ----- DEFAULT -----
    return ("llm", None, None)


def get_relevant_memory(user_message: str, limit: int = 5):
    """
    Very simple relevance matching:
    - keyword overlap
    - special handling for name / preferences
    """

    memories = get_all_memory()
    if not memories:
        return []

    message_words = set(user_message.lower().split())
    scored = []

    for mem in memories:
        _, mem_type, content, key = mem
        content_words = set(content.lower().split())
        score = len(message_words & content_words)

        # Boost important memories
        if key == "name":
            score += 5
        if mem_type == "preference":
            score += 2

        if score > 0:
            scored.append((score, content))

    scored.sort(reverse=True)
    return [c for _, c in scored[:limit]]


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
            result = open_app(payload)

            reply = jarvis_reply(
                user_message=message,
                context=f"The system has successfully opened {payload}."
            )

            speak(reply)
            return {"reply": reply, "tool": "open_app", "result": result}

        if action == "google_search":
            result = google_search(payload)

            reply = jarvis_reply(
                user_message=message,
                context=f"A web search for '{payload}' has been initiated."
            )

            speak(reply)
            return {"reply": reply, "tool": "google_search", "result": result}

        if action == "type_text":
            result = type_text(payload)
            return {"reply": "Typing text.", "tool": "type_text", "result": result}

    # -------- MEMORY HANDLING --------
    if typ == "memory":
        if action == "remember":
            add_memory("fact", payload)

            reply = jarvis_reply(
                user_message=message,
                context="The information has been saved to long-term memory."
            )

            speak(reply)
            return {"reply": reply, "tool": "memory", "result": payload}

        if action == "note":
            reply = jarvis_reply(
                user_message=message,
                context="The note has been stored in long-term memory."
            )
            speak(reply)
            return {"reply": reply, "tool": "memory", "result": payload}

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
        if action == "forget":
            removed = forget_memory(payload)
            if removed:
                reply = jarvis_reply(
                    user_message=message,
                    context=f"The following memories were deleted: {', '.join(removed)}"
                )
            else:
                reply = jarvis_reply(
                    user_message=message,
                    context="No matching memory was found to delete."
                )

            speak(reply)
            return {"reply": reply, "tool": "memory", "result": removed}



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
    reply = jarvis_reply(
        user_message=message
    )

    speak(reply)
    return {"reply": reply, "tool": "none", "result": None}


