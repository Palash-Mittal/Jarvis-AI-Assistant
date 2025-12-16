import subprocess
import json
from jarvis_tts import speak
from tools import open_app, google_search, type_text
from jarvis_memory import add_memory, get_all_memory, find_memory_by_key, delete_memory_by_id
import config
from logger import logger
import time

# -------------------- LLM CONFIG --------------------

OLLAMA = config.LLM.get("ollama_executable", "ollama")
DEFAULT_MODEL = config.LLM.get("default_model", "gemma2")
OLLAMA_TIMEOUT = config.LLM.get("ollama_timeout_s", 30)


JARVIS_SYSTEM_PROMPT = """
You are Jarvis, a calm, intelligent, and professional AI assistant.
Address the user as "sir" naturally (at most once per response).
Be concise, confident, and polished.
Do not mention tools, code, or technical details.
"""


TOOL_DEFINITIONS = """
Available tools:
- open_app(app_name)
- google_search(query)
- type_text(text)
- remember(text)
- forget(text)

Rules:
- Extract all requested actions in order.
- If no action is required, return an empty list.
- Respond ONLY with valid JSON.
"""


# -------------------- SHORT-TERM MEMORY --------------------

SHORT_TERM_CONTEXT = []
MAX_CONTEXT = 6


def add_to_short_term(role, text):
    SHORT_TERM_CONTEXT.append(f"{role}: {text}")
    if len(SHORT_TERM_CONTEXT) > MAX_CONTEXT:
        SHORT_TERM_CONTEXT.pop(0)


def get_short_term_context():
    return "\n".join(SHORT_TERM_CONTEXT) if SHORT_TERM_CONTEXT else ""


# -------------------- LONG-TERM MEMORY --------------------

def get_relevant_memory(message):
    memories = get_all_memory()
    if not memories:
        return []

    words = set(message.lower().split())
    scored = []

    for mem_id, mem_type, content, key in memories:
        score = len(words & set(content.lower().split()))
        if key == "name":
            score += 5
        if score > 0:
            scored.append((score, content))

    scored.sort(reverse=True)
    return [c for _, c in scored[:5]]


def forget_memory(keyword):
    removed = []
    for mem_id, _, content, key in get_all_memory():
        if keyword.lower() in content.lower():
            delete_memory_by_id(mem_id)
            removed.append(content)
    return removed


# -------------------- OLLAMA --------------------

def call_ollama(prompt, model=None):
    cmd = [OLLAMA, "run", model or DEFAULT_MODEL]
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=OLLAMA_TIMEOUT
        )
        return proc.stdout.strip()
    except Exception as e:
        logger.exception("Ollama failed")
        return f"[ERROR] {e}"


# -------------------- LLM PLANNER --------------------

def llm_plan(message: str):
    prompt = f"""
You are a strict JSON command planner for Jarvis.

{TOOL_DEFINITIONS}

User request:
"{message}"

IMPORTANT RULES:
- Return ONLY valid JSON
- "actions" MUST be a list
- Each action MUST be an object with keys: "tool" and "args"
- NEVER return strings inside "actions"
- If no tool is needed, return: {{ "actions": [] }}

EXAMPLE:
{{
  "actions": [
    {{
      "tool": "open_app",
      "args": {{ "app_name": "chrome" }}
    }}
  ]
}}

Now return JSON:
"""

    raw = call_ollama(prompt)

    # 🔒 SAFE JSON EXTRACTION
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == -1:
        logger.error("No JSON found in LLM output")
        return {"actions": []}

    try:
        parsed = json.loads(raw[start:end])

        # 🔒 FORCE CORRECT SHAPE
        actions = parsed.get("actions", [])
        if not isinstance(actions, list):
            logger.error("Actions is not a list")
            return {"actions": []}

        return {"actions": actions}

    except Exception:
        logger.error("Failed to parse planner JSON")
        return {"actions": []}



# -------------------- TOOL EXECUTION --------------------

def execute_plan(actions):
    results = []

    if not isinstance(actions, list):
        logger.error("Actions is not a list")
        return results

    for a in actions:
        # 🔒 HARD VALIDATION
        if not isinstance(a, dict):
            logger.error(f"Invalid action format (skipped): {a}")
            continue

        tool = a.get("tool")
        args = a.get("args", {})

        if tool == "open_app":
            results.append(open_app(args.get("app_name")))

        elif tool == "google_search":
            results.append(google_search(args.get("query")))

        elif tool == "type_text":
            results.append(type_text(args.get("text")))

        elif tool == "remember":
            add_memory("fact", args.get("text"))
            results.append("memory saved")

        elif tool == "forget":
            results.append(forget_memory(args.get("text")))

        else:
            logger.error(f"Unknown tool: {tool}")

    return results



# -------------------- JARVIS RESPONSE --------------------

def jarvis_reply(message, context=""):
    memories = get_relevant_memory(message)
    short_term = get_short_term_context()

    prompt = f"""
{JARVIS_SYSTEM_PROMPT}

Recent context:
{short_term}

Relevant memory:
{chr(10).join(memories)}

Context:
{context}

User said:
{message}

Respond as Jarvis:
"""

    reply = call_ollama(prompt)

    add_to_short_term("User", message)
    add_to_short_term("Jarvis", reply)

    return reply


# -------------------- DECISION ENGINE --------------------

def decide(message: str, model=None):
    logger.info(f"User: {message}")
    if (message.lower()).find("shutdown")!=-1:
        reply=jarvis_reply(message)
        speak(reply)
        time.sleep(6)
        return {
        "reply": reply,
        "tool": "meta",
        "result": {"shutdown":True}
        }
    
    plan = llm_plan(message)
    actions = plan.get("actions", [])

    results = execute_plan(actions)

    context = (
        f"Actions executed: {', '.join(a['tool'] for a in actions)}"
        if actions else
        "No system actions were required."
    )

    reply = jarvis_reply(message, context)
    speak(reply)

    return {
        "reply": reply,
        "tool": [a["tool"] for a in actions],
        "result": results
    }
