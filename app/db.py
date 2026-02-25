import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("database") / "app.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email VARCHAR UNIQUE,
            password_hash VARCHAR,
            credits INT DEFAULT 10,
            created_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audio_tasks (
            id UUID PRIMARY KEY,
            user_id UUID,
            task_id UUID,
            status VARCHAR,
            log VARCHAR,
            original_file_path VARCHAR,
            vocal_path VARCHAR,
            music_path VARCHAR,
            duration FLOAT
        );
        """
    )

    exists = conn.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)).fetchone()
    if not exists:
        password_hash = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"
        conn.execute(
            "INSERT INTO users (id, email, password_hash, credits, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "test@example.com", password_hash, 10, datetime.now(timezone.utc).isoformat()),
        )

    conn.commit()
    conn.close()
