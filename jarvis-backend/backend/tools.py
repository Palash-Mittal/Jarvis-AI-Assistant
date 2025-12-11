import os
import subprocess
import webbrowser
import pyautogui
import time

def open_app(name: str):
    try:
        name = name.lower()

        mapping = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe"
        }

        if name in mapping:
            os.startfile(mapping[name])
            return {"status": "ok", "message": f"Opened {name}"}

        subprocess.Popen(['start', name], shell=True)
        return {"status": "ok", "message": f"Tried opening {name}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def google_search(query: str):
    try:
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return {"status": "ok", "message": f"Searched: {query}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def type_text(text: str):
    try:
        time.sleep(0.4)
        pyautogui.write(text, interval=0.03)
        return {"status": "ok", "message": "Typed text"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
