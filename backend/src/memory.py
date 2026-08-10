import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Store the database outside the source-code files.
# backend/data/swasthya_sathi.db
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "swasthya_sathi.db"


def get_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """Create the caller memory table if it does not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS caller_memory (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT,
                facts TEXT NOT NULL DEFAULT '{}',
                last_interaction TEXT
            )
            """
        )

        connection.commit()


def lookup_caller(user_id: str) -> dict[str, Any] | None:
    """Look up a caller's saved memory using their persistent user ID."""

    if not user_id:
        return None

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                user_id,
                name,
                language_preference,
                facts,
                last_interaction
            FROM caller_memory
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    try:
        facts = json.loads(row["facts"] or "{}")
    except (TypeError, json.JSONDecodeError):
        facts = {}

    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": facts,
        "last_interaction": row["last_interaction"],
    }


def save_caller(
    user_id: str,
    name: str | None = None,
    language_preference: str | None = None,
    facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Save or update a caller's approved memory.

    Only structured facts should be stored here.
    Do not pass raw conversation transcripts or medical notes.
    """

    if not user_id:
        raise ValueError("user_id is required")

    existing = lookup_caller(user_id)

    existing_facts = existing.get("facts", {}) if existing else {}

    if facts:
        existing_facts.update(facts)

    final_name = name if name is not None else (
        existing.get("name") if existing else None
    )

    final_language = (
        language_preference
        if language_preference is not None
        else (existing.get("language_preference") if existing else None)
    )

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO caller_memory (
                user_id,
                name,
                language_preference,
                facts,
                last_interaction
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction
            """,
            (
                user_id,
                final_name,
                final_language,
                json.dumps(existing_facts, ensure_ascii=False),
                timestamp,
            ),
        )

        connection.commit()

    return lookup_caller(user_id) or {
        "user_id": user_id,
        "name": final_name,
        "language_preference": final_language,
        "facts": existing_facts,
        "last_interaction": timestamp,
    }


# Initialize the database when this module is imported.
initialize_database()