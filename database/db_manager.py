"""
db_manager.py
--------------
Handles all SQLite database operations for the Airport Voice Assistant.
Stores every voice interaction (query + AI response) for later analytics
in the Admin Dashboard.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "airport_assistant.db"


@contextmanager
def get_connection():
    """Context manager that yields a SQLite connection and closes it safely."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the interactions table if it does not already exist."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,          -- 'Live Kiosk' or 'Batch Process'
                file_name TEXT,
                language TEXT,
                query_text TEXT,
                response_text TEXT,
                intent TEXT,
                status TEXT DEFAULT 'success', -- 'success' or 'error'
                processing_time REAL
            )
            """
        )


def insert_interaction(source, file_name, language, query_text,
                        response_text, intent, status="success",
                        processing_time=0.0):
    """Insert a single voice-interaction record."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO interactions
            (timestamp, source, file_name, language, query_text,
             response_text, intent, status, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                source,
                file_name,
                language,
                query_text,
                response_text,
                intent,
                status,
                processing_time,
            ),
        )


def fetch_all_interactions():
    """Return every interaction as a list of dict-like Row objects."""
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM interactions ORDER BY id DESC")
        return cur.fetchall()


def fetch_recent(limit=10):
    """Return the most recent N interactions."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM interactions ORDER BY id DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()


def get_summary_stats():
    """Aggregate stats used on the Admin Dashboard."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM interactions").fetchone()["c"]
        success = conn.execute(
            "SELECT COUNT(*) AS c FROM interactions WHERE status='success'"
        ).fetchone()["c"]
        errors = total - success
        avg_time = conn.execute(
            "SELECT AVG(processing_time) AS a FROM interactions"
        ).fetchone()["a"] or 0.0
        by_lang = conn.execute(
            """
            SELECT COALESCE(language,'unknown') AS language, COUNT(*) AS c
            FROM interactions GROUP BY language ORDER BY c DESC
            """
        ).fetchall()
        by_intent = conn.execute(
            """
            SELECT COALESCE(intent,'unknown') AS intent, COUNT(*) AS c
            FROM interactions GROUP BY intent ORDER BY c DESC
            """
        ).fetchall()
        by_day = conn.execute(
            """
            SELECT substr(timestamp,1,10) AS day, COUNT(*) AS c
            FROM interactions GROUP BY day ORDER BY day
            """
        ).fetchall()
    return {
        "total": total,
        "success": success,
        "errors": errors,
        "avg_time": round(avg_time, 2),
        "by_language": by_lang,
        "by_intent": by_intent,
        "by_day": by_day,
    }


def clear_all_data():
    """Wipe the interactions table (used by the admin 'reset' button)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM interactions")
