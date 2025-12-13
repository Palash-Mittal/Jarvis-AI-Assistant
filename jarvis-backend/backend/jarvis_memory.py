# backend/jarvis_memory.py
from db import get_conn, init_db

init_db()

def add_memory(mem_type: str, value: str, key: str | None = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO memory (type, key, value) VALUES (?, ?, ?)",
            (mem_type, key, value)
        )
        conn.commit()

def get_all_memory():
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT type, key, value, created_at FROM memory ORDER BY created_at DESC"
        )
        return cur.fetchall()

def find_memory_by_key(key: str):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT value FROM memory WHERE key = ? ORDER BY created_at DESC LIMIT 1",
            (key,)
        )
        row = cur.fetchone()
        return row[0] if row else None

def clear_memory():
    with get_conn() as conn:
        conn.execute("DELETE FROM memory")
        conn.commit()
