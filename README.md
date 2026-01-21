🤖 Jarvis Desktop AI Assistant

A Jarvis-style desktop AI assistant for Windows, inspired by Iron Man, powered by a local LLM (Ollama), voice control, tool execution, and persistent memory.

This project is designed to feel like a real personal assistant, not just a chatbot.

✨ Features

🎙️ Voice Interaction

Offline voice recognition using Whisper

Wake word detection ("Jarvis")

Silence-based recording (hands-free)

Text-to-speech responses (Jarvis-style voice)

🧠 Intelligence

Local LLM execution via Ollama

JSON-based action planner

Tool decision engine (no hallucinated actions)

Context-aware replies

Follow-up questions for ambiguous commands

🛠️ System Tools

Jarvis can:

Open desktop applications (Chrome, VS Code, Notepad, etc.)

Open websites & search media (YouTube, Spotify, Google)

Type text automatically

Control system behavior (extensible)

Switch personality modes (Developer / Casual / Silent)

💾 Memory System

SQLite-based persistent memory

Remembers preferences & configuration

Mode stored across sessions

Safe add / forget memory operations

🧱 Architecture Highlights

Tool registry (scalable, clean)

Safe JSON parsing from LLM

Strict tool validation

Modular backend design

Rotating logs for debugging

📂 Project Structure
