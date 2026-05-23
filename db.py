import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).parent / "data.db"))


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with closing(get_db()) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '新对话',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
        """)
        conn.commit()


def create_conversation():
    conv_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    now = datetime.now().isoformat()
    with closing(get_db()) as conn:
        conn.execute(
            "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
            (conv_id, "新对话", now),
        )
        conn.commit()
    return {"id": conv_id, "title": "新对话", "created_at": now}


def get_conversations():
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_conversation(conv_id):
    with closing(get_db()) as conn:
        row = conn.execute(
            "SELECT id, title, created_at FROM conversations WHERE id = ?", (conv_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_conversation(conv_id):
    with closing(get_db()) as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()


def add_message(conv_id, role, content):
    now = datetime.now().isoformat()
    with closing(get_db()) as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conv_id, role, content, now),
        )
        conn.commit()
    return {"role": role, "content": content, "created_at": now}


def get_messages(conv_id):
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_conversation_title(conv_id, title):
    with closing(get_db()) as conn:
        conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id)
        )
        conn.commit()
