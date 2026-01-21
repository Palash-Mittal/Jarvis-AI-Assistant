# backend/tools.py
import os
import subprocess
import webbrowser
import time
from logger import logger
import ctypes
import pyperclip
import threading

try:
    import pyautogui
    _HAS_PYAUTOGUI = True
except Exception:
    _HAS_PYAUTOGUI = False
    logger.warning("pyautogui not available — type_text tool will be disabled")

def open_app(name: str):
    try:
        name = name.lower().strip()

        aliases = {
            "vs code": "visual studio code",
            "vscode": "visual studio code",
            "file explorer": "explorer",
            "cmd": "command prompt",
            "ms edge": "edge",
            "microsoft edge": "edge",
        }

        if name in aliases:
            name = aliases[name]

        app_paths = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "paint": "mspaint.exe",
            "command prompt": "cmd.exe",

            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",

            "visual studio code": r"C:\Users\Palash\AppData\Local\Programs\Microsoft VS Code\Code.exe",

            "steam": r"C:\Program Files (x86)\Steam\steam.exe",
            "epic games": r"C:\Program Files (x86)\Epic Games\Launcher\Engine\Binaries\Win64\EpicGamesLauncher.exe",
        }

        path = app_paths.get(name)

        if path:
            path = os.path.expandvars(path)
            logger.info(f"Launching app: {name} -> {path}")
            subprocess.Popen(path)
            return {"status": "ok", "message": f"Opened {name}"}

        subprocess.Popen(f'start "" "{name}"', shell=True)
        return {"status": "ok", "message": f"Tried opening {name}"}

    except Exception as e:
        logger.exception("open_app failed")
        return {"status": "error", "message": str(e)}


def open_web(website: str, query: str | None = None):
    try:
        website = website.lower().strip()

        base_urls = {
            "youtube": "https://www.youtube.com",
            "spotify": "https://open.spotify.com",
            "google": "https://www.google.com",
            "github": "https://github.com",
            "instagram": "https://www.instagram.com",
        }

        base = base_urls.get(website)

        if not base:
            webbrowser.open(f"https://www.google.com/search?q={website}")
            return {"status": "ok", "message": f"Searched {website}"}

        if query:
            if website == "youtube":
                url = f"{base}/results?search_query={query}"
            elif website == "spotify":
                url = f"{base}/search/{query}"
            else:
                url = f"{base}/search?q={query}"
        else:
            url = base

        webbrowser.open(url)
        return {"status": "ok", "message": f"Opened {website}"}

    except Exception as e:
        logger.exception("open_web failed")
        return {"status": "error", "message": str(e)}


def google_search(query: str):
    try:
        url = f"https://www.google.com/search?q={query}"
        logger.info(f"google_search -> {url}")
        webbrowser.open(url)
        return {"status": "ok", "message": f"Searched: {query}"}
    except Exception as e:
        logger.exception("google_search failed")
        return {"status": "error", "message": str(e)}

def type_text(text: str):
    if not _HAS_PYAUTOGUI:
        logger.error("type_text requested but pyautogui not installed")
        return {"status": "error", "message": "pyautogui not installed"}
    try:
        time.sleep(0.4)
        pyautogui.write(text, interval=0.03)
        return {"status": "ok", "message": "Typed text"}
    except Exception as e:
        logger.exception("type_text failed")
        return {"status": "error", "message": str(e)}

def system_control(action: str):
    try:
        action = action.lower()

        if action == "mute":
            ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)

        elif action == "volume up":
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)

        elif action == "volume down":
            ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)

        elif action == "wifi off":
            subprocess.run("netsh interface set interface Wi-Fi disable", shell=True)

        elif action == "wifi on":
            subprocess.run("netsh interface set interface Wi-Fi enable", shell=True)

        else:
            return {"status": "error", "message": "Unknown system action"}

        return {"status": "ok", "message": f"System action executed: {action}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def find_file(filename: str, search_path="C:\\"):
    matches = []
    try:
        for root, _, files in os.walk(search_path):
            for f in files:
                if filename.lower() in f.lower():
                    matches.append(os.path.join(root, f))
                    if len(matches) >= 5:
                        return {"status": "ok", "results": matches}
        return {"status": "ok", "results": matches}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def clipboard(action: str, text: str | None = None):
    try:
        action = action.lower()

        if action == "read":
            return {"status": "ok", "content": pyperclip.paste()}

        if action == "copy" and text:
            pyperclip.copy(text)
            return {"status": "ok", "message": "Copied to clipboard"}

        if action == "clear":
            pyperclip.copy("")
            return {"status": "ok", "message": "Clipboard cleared"}

        return {"status": "error", "message": "Invalid clipboard action"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def reminder(seconds: int, message: str):
    def _remind():
        time.sleep(seconds)
        from jarvis_tts import speak
        speak(f"Reminder: {message}")

    threading.Thread(target=_remind, daemon=True).start()
    return {"status": "ok", "message": "Reminder set"}

def set_mode(mode: str):
    from jarvis_memory import add_memory
    add_memory("config", mode, key="mode")
    return {"status": "ok", "message": f"Mode set to {mode}"}
