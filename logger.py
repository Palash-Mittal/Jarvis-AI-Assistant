# backend/logger.py
import logging
from logging.handlers import RotatingFileHandler
import config
import os

LOG_PATH = config.ENGINE.get("log_path", "jarvis.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger("jarvis")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    logger.addHandler(handler)


console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)
