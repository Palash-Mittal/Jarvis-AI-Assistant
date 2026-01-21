# 🤖 Jarvis Desktop AI Assistant

A Jarvis-style desktop AI assistant for Windows, inspired by Iron Man, powered by a local LLM (Ollama), voice control, tool execution, and persistent memory.

This project is designed to feel like a real personal assistant, not just a chatbot.

---

## Features

🎙️ Voice Interaction

Offline voice recognition using Whisper

Wake word detection ("Jarvis")

Silence-based recording (hands-free)

Text-to-speech responses (Jarvis-style voice)

---

## Intelligence

Local LLM execution via Ollama

JSON-based action planner

Tool decision engine (no hallucinated actions)

Context-aware replies

Follow-up questions for ambiguous commands

---

## System Tools

Jarvis can:

Open desktop applications (Chrome, VS Code, Notepad, etc.)

Open websites & search media (YouTube, Spotify, Google)

Type text automatically

Control system behavior (extensible)

Switch personality modes (Developer / Casual / Silent)

---

## Memory System

SQLite-based persistent memory

Remembers preferences & configuration

Mode stored across sessions

Safe add / forget memory operations

---

## Architecture Highlights

Tool registry (scalable, clean)

Safe JSON parsing from LLM

Strict tool validation

Modular backend design

Rotating logs for debugging

---

## Project Structure
```bash
├── main.py              # Entry point, stdin/stdout bridge
├── jarvis_brain.py      # Decision engine, planner, executor
├── jarvis_voice.py      # Voice recording + Whisper STT
├── jarvis_tts.py        # Text-to-speech output
├── jarvis_memory.py     # Long-term memory manager
├── db.py                # SQLite database setup
├── tools.py             # System & browser tools
├── logger.py            # Logging system
├── config.py            # Configuration (LLM, engine)
└── memory.db            # Persistent memory database
```
---

## 🧪 Example Commands

Jarvis open chrome

Jarvis open vs code
Jarvis play interstellar soundtrack on youtube

Jarvis search for python decorators

Jarvis enter developer mode

Jarvis type hello world

Jarvis shutdown

---

## Tool System

Tools are executed using a registry-based dispatcher:

open_app(app_name)

open_web(website, query?)

google_search(query)

type_text(text)

set_mode(mode)

(Easily extensible)

LLM outputs strict JSON, which is validated before execution.

---

## Safety & Reliability

No raw LLM execution

All actions must match allowed tools

Invalid or malformed plans are ignored safely

Tool failures are logged and handled gracefully

---

## Requirements

Python

Python 3.10+

Python Libraries
```bash
pip install pyttsx3 sounddevice numpy whisper pyautogui pyperclip
```
External

Ollama installed and running

Supported LLM (e.g. gemma2, llama3)

Windows OS

---

## Running the Project
```bash
python main.py
```
Jarvis communicates via stdin/stdout, making it easy to:

Connect to a GUI

Use with Electron / Tauri

Control remotely

---

