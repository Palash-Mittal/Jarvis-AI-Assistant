# backend/config.py
LLM = {
    "default_model": "gemma2",
    "ollama_executable": "ollama",
    "ollama_timeout_s": 30  # timeout for calls to ollama.run
}

ENGINE = {
    "stdin_read_timeout_s": 0.1,   # not actively used but kept for future use
    "log_path": "backend/jarvis.log",
    "allow_raw_text": True  # if True, treat plain text input as {"command": "<text>"}
}
