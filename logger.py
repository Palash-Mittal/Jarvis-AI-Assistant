#logger.py
import logging
from logging.handlers import RotatingFileHandler
import config
import os

LOG_PATH = "jarvis.log"

log_dir = os.path.dirname(LOG_PATH)

if log_dir:
    os.makedirs(log_dir, exist_ok=True)


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
