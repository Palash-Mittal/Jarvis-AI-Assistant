#config.py
LLM = {
    "default_model": "gemma2",
    "ollama_executable": "ollama",
    "ollama_timeout_s": 30 
}

ENGINE = {
    "stdin_read_timeout_s": 0.1,  
    "log_path": "jarvis.log",
    "allow_raw_text": True  # if True, treat plain text input as {"command": "<text>"}
}
