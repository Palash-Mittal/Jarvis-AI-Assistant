from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .jarvis_brain import decide
from .jarvis_voice import transcribe_whisper
from . import config

app = FastAPI(title="Jarvis Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class Chat(BaseModel):
    message: str
    model: str | None = None


@app.post("/api/chat")
def chat(req: Chat):
    return decide(req.message, req.model)


@app.get("/api/listen")
def listen_api():
    text = transcribe_whisper()
    return {"text": text}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app",
                host=config.BACKEND["host"],
                port=config.BACKEND["port"],
                reload=True)
