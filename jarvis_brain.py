#jarvis_brain.py
import subprocess
import json
from jarvis_tts import speak
from tools import open_app, google_search, type_text, open_web, system_control, find_file, clipboard, reminder, set_mode
from jarvis_memory import add_memory, get_all_memory, find_memory_by_key, delete_memory_by_id
import config
from logger import logger
import time
from tools.window_tools import(
    active_app,
    list_apps,
    focus_app,
    close_app,
    minimize_all
)

CONVERSATION_ACTIVE = False
LAST_CONVERSATION_TIME = 0
CONVERSATION_TIMEOUT = 20  # seconds

# LLM

OLLAMA = config.LLM.get("ollama_executable", "ollama")
DEFAULT_MODEL = config.LLM.get("default_model", "gemma2")
OLLAMA_TIMEOUT = config.LLM.get("ollama_timeout_s", 30)


def get_jarvis_system_prompt():
    mode = find_memory_by_key("mode") or "normal"

    if mode == "developer":
        return """
You are Jarvis operating in DEVELOPER mode.
Be technical, detailed, and precise.
You may explain code, logic, and architecture.
Use correct programming terminology.
"""

    if mode == "casual":
        return """
You are Jarvis operating in CASUAL mode.
Be friendly, relaxed, and slightly humorous.
Still be helpful and clear.
"""

    if mode == "silent":
        return """
You are Jarvis operating in SILENT mode.
Keep responses extremely short.
Only speak when necessary.
"""

    # For default jarvis
    return """
You are Jarvis, a calm, intelligent, and professional AI assistant.
Address the user as "sir" naturally (at most once per response).
Be concise, confident, and polished.
Do not mention tools, code, or technical details.
"""



TOOL_DEFINITIONS = """
Available tools (use EXACT names and arguments):

1. open_app(app_name: string)
   - Use ONLY to open installed desktop applications.

2. open_web(website: string, query?: string)
   - Use to open websites in a browser.
   - "website" should be a short platform or domain name
     (examples: "youtube", "spotify", "github", "google.com").
   - If "query" is provided, it represents what should be searched or played on that site.

3. google_search(query: string)
   - Use ONLY when the user is explicitly asking to search for information,
     not when they want to open a website or play media.

4. type_text(text: string)
   - Use to type text on the keyboard.

5. remember(text: string)
   - Use to save important information to memory.

6. forget(text: string)
   - Use to delete previously saved memory.

7. system_control(action: string)
   - Controls system volume and wifi.
   - Actions: mute, volume up, volume down, wifi on, wifi off

8. find_file(filename: string)
   - Searches for files on the system by name.

9. clipboard(action: string, text?: string)
   - Read, copy, or clear clipboard content.

10. reminder(seconds: number, message: string)
   - Sets a reminder after given seconds.

11. active_app()
   - Use to identify the currently focused application.

12. list_apps()
   - Use to list currently open applications.

13. focus_app(app_name: string)
   - Use to switch focus to an open application.

14. close_app(app_name?: string)
   - Close a specific app or the currently active window.

15. minimize_all()
   - Minimize all open windows.


GENERAL DECISION RULES (VERY IMPORTANT):

- If the request could mean either an app or a website, ALWAYS prefer open_web.
- If the request could mean either a website or a Google search, ALWAYS prefer open_web.
- Use open_app ONLY when the user clearly refers to a desktop application.
- If the user explicitly says "website", "site", "browser", or provides a URL, use open_web.
- If multiple actions are requested, return them in the correct order.
- If no tool is needed, return an empty list of actions.


MEDIA HANDLING RULES (CRITICAL):

- When the user says "play", "listen", or "watch", treat it as a media request.
- Try to extract:
  • the media name (song, playlist, video, movie, etc.)
  • the platform (Spotify, YouTube, etc.)

QUERY EXTRACTION RULES (VERY IMPORTANT):

- If the media name is CLEAR, include it using the argument "query".
- The "query" must contain ONLY the actual media name.
- Do NOT include filler words like "song", "video", or "playlist"
  unless they are part of the real name.

Examples:
- "play believer on spotify"
  → website: "spotify", query: "believer"

- "play interstellar soundtrack on youtube"
  → website: "youtube", query: "interstellar soundtrack"

- "play my workout playlist"
  → website: "spotify", query: "workout playlist"

- "play this playlist"
  → website: "spotify", query: OMITTED (ambiguous)

- "play something"
  → website: "spotify", query: OMITTED (ambiguous)


MEDIA DECISION LOGIC:

- If BOTH platform and query are clear:
  → use open_web with both "website" and "query".

- If query is clear but platform is NOT mentioned:
  → choose a default platform:
    • Music / audio → spotify
    • Video / movie → youtube

- If the request is ambiguous or missing the media name:
  → DO NOT guess the query.
  → Use open_web with ONLY the platform.
  → Allow Jarvis to ask a clarification question in its reply.

- NEVER use google_search for playing or watching media.
- Prefer open_web over open_app for media playback.
"""


TOOL_REGISTRY = {
    "open_app": open_app,
    "open_web": open_web,
    "google_search": google_search,
    "type_text": type_text,
    "system_control": system_control,
    "find_file": find_file,
    "clipboard": clipboard,
    "reminder": reminder,
    "set_mode": set_mode,
    "active_app": active_app,
    "list_apps": list_apps,
    "focus_app": focus_app,
    "close_app": close_app,
    "minimize_all": minimize_all
}

# Short term memory

SHORT_TERM_CONTEXT = []
MAX_CONTEXT = 6


def add_to_short_term(role, text):
    SHORT_TERM_CONTEXT.append(f"{role}: {text}")
    if len(SHORT_TERM_CONTEXT) > MAX_CONTEXT:
        SHORT_TERM_CONTEXT.pop(0)


def get_short_term_context():
    return "\n".join(SHORT_TERM_CONTEXT) if SHORT_TERM_CONTEXT else ""


# Long term memory

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


# ollama things

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


# planning

def llm_plan(message: str):
    prompt = f"""
You are a strict JSON command planner for Jarvis.

{TOOL_DEFINITIONS}

User request:
"{message}"

IMPORTANT OUTPUT RULES (MANDATORY):
- Return ONLY valid JSON.
- The top-level key MUST be "actions".
- "actions" MUST be a list.
- Each action MUST be an object with keys: "tool" and "args".
- NEVER return plain text, explanations, or comments.
- NEVER return strings inside "actions".
- If no tool is needed, return exactly: {{ "actions": [] }}.

ARGUMENT RULES:
- Include ONLY the arguments required for the selected tool.
- Omit optional arguments if they are unclear or ambiguous.
- Do NOT invent values.

EXAMPLES:

Example 1 (open app):
{{
  "actions": [
    {{
      "tool": "open_app",
      "args": {{ "app_name": "chrome" }}
    }}
  ]
}}

Example 2 (media with clear query):
{{
  "actions": [
    {{
      "tool": "open_web",
      "args": {{
        "website": "youtube",
        "query": "interstellar soundtrack"
      }}
    }}
  ]
}}

Example 3 (media but ambiguous query):
{{
  "actions": [
    {{
      "tool": "open_web",
      "args": {{
        "website": "spotify"
      }}
    }}
  ]
}}

Now return ONLY the JSON object:
"""


    raw = call_ollama(prompt)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == -1:
        logger.error("No JSON found in LLM output")
        return {"actions": []}

    try:
        parsed = json.loads(raw[start:end])
        actions = parsed.get("actions", [])
        if not isinstance(actions, list):
            logger.error("Actions is not a list")
            return {"actions": []}

        return {"actions": actions}
    except Exception:
        logger.error("Failed to parse planner JSON")
        return {"actions": []}



# tool execution

def execute_plan(actions):
    results = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        tool = action.get("tool")
        args = action.get("args", {})
        func = TOOL_REGISTRY.get(tool)
        if not func:
            logger.error(f"Unknown tool: {tool}")
            continue
        try:
            result = func(**args)
            results.append({**result, "tool": tool})
        except Exception as e:
            logger.exception(f"Tool failed: {tool}")
            results.append({
                "tool": tool,
                "status": "error",
                "message": str(e)
            })

    return results


# jarvis response

def jarvis_reply(message, context=""):
    memories = get_relevant_memory(message)
    short_term = get_short_term_context()

    prompt = f"""
{get_jarvis_system_prompt()}

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


# decide function

def decide(message: str, model=None):
    global CONVERSATION_ACTIVE, LAST_CONVERSATION_TIME

    now = time.time()

    # Auto-disable conversation if timeout
    if CONVERSATION_ACTIVE and now - LAST_CONVERSATION_TIME > CONVERSATION_TIMEOUT:
        CONVERSATION_ACTIVE = False

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
            errors.append(a)

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

    if not actions:
        clarification_prompt = (
          "Ask a short, polite clarification question if needed. "
          "Do not execute any action yet."
        )
        reply = jarvis_reply(message, clarification_prompt)
    else:
        reply = jarvis_reply(message, context)

    CONVERSATION_ACTIVE = True
    LAST_CONVERSATION_TIME = time.time()

    speak(reply)

    return {
        "reply": reply,
        "tool": [a["tool"] for a in actions],
        "result": results
    }

