import logging
from datetime import datetime, timezone
from typing import Any

from memory import get_connection

logger = logging.getLogger("call_analytics")

VALID_OUTCOMES = frozenset({"SUCCESS", "FAILURE"})


def initialize_call_analytics_table() -> None:
    """Create the call_analytics table if it does not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS call_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT NOT NULL UNIQUE,
                outcome TEXT NOT NULL CHECK(outcome IN ('SUCCESS', 'FAILURE')),
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def record_call_outcome(call_id: str, outcome: str) -> bool:
    """Record a call outcome idempotently. Returns True if a new row was inserted."""
    logger.info("[ANALYTICS] record_call_outcome called: call_id=%s outcome=%s", call_id, outcome)
    
    if not call_id:
        raise ValueError("call_id is required")

    if outcome not in VALID_OUTCOMES:
        raise ValueError("outcome must be SUCCESS or FAILURE")

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        # Check if this call_id already exists
        existing = connection.execute(
            "SELECT call_id FROM call_analytics WHERE call_id = ?",
            (call_id,)
        ).fetchone()
        
        if existing:
            logger.info("[ANALYTICS] Duplicate call_id detected, skipping insert: call_id=%s", call_id)
            return False
        
        cursor = connection.execute(
            """
            INSERT INTO call_analytics (call_id, outcome, created_at)
            VALUES (?, ?, ?)
            """,
            (call_id, outcome, timestamp),
        )
        connection.commit()
        inserted = cursor.rowcount > 0
        logger.info("[ANALYTICS] Database insert completed: call_id=%s inserted=%s rowcount=%s", call_id, inserted, cursor.rowcount)
        return inserted


def get_analytics_summary() -> dict[str, int]:
    """Return aggregate call analytics from the database."""
    with get_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS count FROM call_analytics"
        ).fetchone()["count"]
        successful = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM call_analytics
            WHERE outcome = 'SUCCESS'
            """
        ).fetchone()["count"]
        failed = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM call_analytics
            WHERE outcome = 'FAILURE'
            """
        ).fetchone()["count"]

    return {
        "total_calls": total,
        "successful_calls": successful,
        "failed_calls": failed,
    }


def list_call_analytics() -> list[dict[str, Any]]:
    """Return all call analytics rows for debugging or future use."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, call_id, outcome, created_at
            FROM call_analytics
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        {
            "id": row["id"],
            "call_id": row["call_id"],
            "outcome": row["outcome"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


initialize_call_analytics_table()
