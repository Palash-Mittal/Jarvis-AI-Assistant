# backend/tools.py
import os
import subprocess
import webbrowser
import time
from logger import logger

# pyautogui is optional; catch ImportError during import
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
          "vscode": "visual studio code",
          "vs code": "visual studio code",
          "file explorer": "explorer",
          "cmd": "command prompt",
          "ms edge": "egde",
          "microsoft edge": "edge",
          "microsoft word": "word",
          "microsoft excel": "excel",
          "microsoft powerpoint": "powerpoint"
        }

        if name in aliases:
            name=aliases[name]

        mapping = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "paint": "mspaint.exe",
            "command prompt": "cmd.exe",
            "visual studio code": "Code.exe",
            "edge": "msedge.exe",
            "whatsapp": "WhatsApp.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "epic games": r"C:\Program Files (x86)\Epic Games\Launcher\Engine\Binaries\Win64\EpicGamesLauncher.exe",
            "steam": r"C:\Program Files (x86)\Steam\steam.exe",

        }
        if name in mapping:
            path = mapping[name]
            logger.info(f"open_app -> launching mapped path: {path}")
            os.startfile(path)
            return {"status": "ok", "message": f"Opened {name}"}
        # fallback: try start command
        os.startfile(name)
        return {"status": "ok", "message": f"Tried opening {name}"}
    except Exception as e:
        logger.exception("open_app failed")
        return {"status": "error", "message": str(e)}

def open_web(name: str):
    try:
        name=name.lower().strip()
        aliases = {
            "yt": "youtube",
            "gpt": "chatgpt",
            "insta": "instagram",
            "ig": "instagram"
        }

        if name in aliases:
            name = aliases[name]

        mapping={
            "youtube": "https://www.youtube.com/",
            "chatgpt": "https://chatgpt.com/",
            "github": "https://github.com/",
            "instagram": "https://www.instagram.com/",
            "reddit": "https://www.reddit.com/",
        }
        if name in mapping:
            path=mapping[name]
            logger.info(f"open_web -> launching mapped path: {path}")
            os.startfile(path)
            return {"status": "ok", "message": f"Opened {name}"}
        #fallback
        url = f"https://www.google.com/search?q={name}"
        os.startfile(url)
        return {"status": "ok", "message": f"Tried opening {name}"}
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
