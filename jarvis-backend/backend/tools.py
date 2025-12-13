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
        mapping = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe"
        }
        if name in mapping:
            path = mapping[name]
            logger.info(f"open_app -> launching mapped path: {path}")
            os.startfile(path)
            return {"status": "ok", "message": f"Opened {name}"}
        # fallback: try start command
        subprocess.Popen(['start', name], shell=True)
        return {"status": "ok", "message": f"Tried opening {name}"}
    except Exception as e:
        logger.exception("open_app failed")
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
