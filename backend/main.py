# backend/main.py
import sys
import json
import time
import traceback
from jarvis_brain import decide
from jarvis_voice import transcribe_whisper
from logger import logger

def send(data):
    try:
        line = json.dumps(data, ensure_ascii=False)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        logger.debug("Sent to stdout: " + line)
    except Exception:
        logger.exception("Failed to send response")

def safe_json_load(s):
    try:
        return json.loads(s)
    except Exception:
        return None

def main_loop():
    send({"status": "jarvis-ready"})
    logger.info("Engine started, waiting for input on stdin...")
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue

        logger.info("Received raw input: " + raw)
        # try JSON first
        req = safe_json_load(raw)
        if req is None:
            # If not json and raw-text allowed, treat as raw command
            logger.debug("Input is not JSON, treating as raw command")
            command_text = raw
            try:
                out = decide(command_text)
                send(out)
                # handle shutdown signal
                if out.get("tool") == "meta" and isinstance(out.get("result"), dict) and out["result"].get("shutdown"):
                    logger.info("Shutdown requested -> exiting")
                    break
            except Exception:
                logger.exception("Error handling raw command")
                send({"reply": "[ERROR] internal error", "tool": "none", "result": None})
            continue

        # if json, expect {"command": "..."} optionally {"model": "..."}
        command = req.get("command") or req.get("message") or ""
        model = req.get("model")
        # special voice input
        if command == "voice_input":
            try:
                text = transcribe_whisper()
                send({"text": text})
            except Exception:
                logger.exception("Voice transcription failed")
                send({"text": ""})
            continue

        if command == "health":
            send({"reply": "OK", "tool": "meta", "result": {"status": "ok"}})
            continue

        try:
            result = decide(command, model=model)
            send(result)
            # handle shutdown
            if result.get("tool") == "meta" and isinstance(result.get("result"), dict) and result["result"].get("shutdown"):
                logger.info("Shutdown requested -> exiting")
                break
        except Exception:
            logger.exception("Error processing request")
            send({"reply": "[ERROR] internal error", "tool": "none", "result": None})

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down")
    except Exception:
        logger.exception("Fatal error in main loop")
    finally:
        logger.info("Engine exiting")
