memory_store = {
    "notes": []
}

def save_note(text: str):
    memory_store["notes"].append(text)
    return True

def get_notes():
    return memory_store["notes"]
