import subprocess
import json
from jarvis_tts import speak
from tools import open_app, google_search, type_text, open_web
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
Available tools (use EXACT names and arguments):

1. open_app(app_name: string)
   - Use ONLY to open installed desktop applications.

2. open_web(website: string)
   - Use to open websites in a browser.
   - The argument should be a short site name or domain (example: "youtube", "github", "google.com").

3. google_search(query: string)
   - Use ONLY when the user is explicitly asking to search for information,
     not when they want to open a website.

4. type_text(text: string)
   - Use to type text on the keyboard.

5. remember(text: string)
   - Use to save important information to memory.

6. forget(text: string)
   - Use to delete previously saved memory.

Decision rules (VERY IMPORTANT):
- If the request could mean either an app or a website, ALWAYS prefer open_web.
- If the request could mean either a website or a Google search, ALWAYS prefer open_web.
- Use open_app ONLY when the user clearly refers to a desktop application.
- If the user explicitly says "website", "site", "browser", or provides a URL, use open_web.
- If multiple actions are requested, return them in the correct order.
- If no tool is needed, return an empty list of actions.

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
        name = args.get("app_name")

        if tool == "open_app" and "." in args.get("app_name"):
            tool = "open_web"
            args = {"website": name}

        if tool == "open_app" and args.get("app_name"):
            results.append(open_app(args.get("app_name")))

        elif tool == "google_search" and args.get("query"):
            results.append(google_search(args.get("query")))

        elif tool == "type_text":
            results.append(type_text(args.get("text")))

        elif tool == "remember":
            add_memory("fact", args.get("text"))
            results.append("memory saved")

        elif tool == "forget":
            results.append(forget_memory(args.get("text")))

        elif tool == "open_web" and args.get("website"):
            results.append(open_web(args.get("website")))

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
    for a in ["shutdown","exit"]:
        if (message.lower()).find(a)!=-1:
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

    errors=[]
    for a in results:
        if a.get("status") == "error":
            errors = errors.append(a)

    if len(errors)==0:
        context = (
        f"Actions executed: {', '.join(a['tool'] for a in actions)}"
        )
    
    elif len(errors)>0 and len(errors)<len(actions):
        context = "Some requested actions were completed, but others could not be."

    elif len(errors)==len(actions):
        context = "I was unable to complete the requested actions."

    if actions and not results:
        context = "No actions could be executed"

    reply = jarvis_reply(message, context)
    speak(reply)

    return {
        "reply": reply,
        "tool": [a["tool"] for a in actions],
        "result": results
    }
