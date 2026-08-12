import re
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Any

from memory import get_connection

MAX_SUMMARY_LENGTH = 500
MAX_FIELD_LENGTH = 300

_SENSITIVE_PATTERNS = [
    re.compile(r"\b(?:password|passwd|pwd)\s*[:=]?\s*\S+", re.I),
    re.compile(r"\b(?:otp|pin)\s*[:=]?\s*\d{4,8}", re.I),
    re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    re.compile(r"\b(?:account|acct)\s*(?:number|no\.?|#)\s*[:=]?\s*\d+", re.I),
    re.compile(r"\b(?:api[_-]?key|secret|token)\s*[:=]?\s*\S+", re.I),
]


def _sanitize_text(text: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    """Remove sensitive patterns and truncate text before storage."""
    cleaned = text.strip()
    for pattern in _SENSITIVE_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    if len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 3] + "..."
    return cleaned


def _generate_reference_id() -> str:
    """Generate a human-friendly reference ID like ASH-20260812-A3F7."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = secrets.token_hex(2).upper()
    return f"ASH-{date_part}-{suffix}"


def initialize_escalations_table() -> None:
    """Create the escalations table if it does not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_id TEXT NOT NULL UNIQUE,
                caller_identifier TEXT,
                caller_name TEXT,
                reason TEXT NOT NULL,
                summary TEXT NOT NULL,
                agent_checks TEXT,
                urgency TEXT NOT NULL DEFAULT 'medium',
                language TEXT,
                preferred_followup TEXT,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def get_active_escalation_for_caller(
    caller_identifier: str,
) -> dict[str, Any] | None:
    """Return the caller's most recent Open or In Progress escalation, if any."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM escalations
            WHERE caller_identifier = ?
              AND status IN ('Open', 'In Progress')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (caller_identifier,),
        ).fetchone()

    return _row_to_dict(row) if row else None


def create_escalation(
    *,
    caller_identifier: str | None = None,
    caller_name: str | None = None,
    reason: str,
    summary: str,
    agent_checks: str | None = None,
    urgency: str = "medium",
    language: str | None = None,
    preferred_followup: str | None = None,
) -> dict[str, Any]:
    """Create a new human-help escalation request with sanitized fields."""
    if not reason or not summary:
        raise ValueError("reason and summary are required")

    reference_id = _generate_reference_id()
    timestamp = datetime.now(timezone.utc).isoformat()

    sanitized = {
        "caller_identifier": (
            _sanitize_text(caller_identifier, MAX_FIELD_LENGTH)
            if caller_identifier
            else None
        ),
        "caller_name": (
            _sanitize_text(caller_name, MAX_FIELD_LENGTH) if caller_name else None
        ),
        "reason": _sanitize_text(reason, MAX_FIELD_LENGTH),
        "summary": _sanitize_text(summary, MAX_SUMMARY_LENGTH),
        "agent_checks": (
            _sanitize_text(agent_checks, MAX_FIELD_LENGTH) if agent_checks else None
        ),
        "urgency": _sanitize_text(urgency, 50).lower(),
        "language": (
            _sanitize_text(language, MAX_FIELD_LENGTH) if language else None
        ),
        "preferred_followup": (
            _sanitize_text(preferred_followup, MAX_FIELD_LENGTH)
            if preferred_followup
            else None
        ),
    }

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO escalations (
                reference_id,
                caller_identifier,
                caller_name,
                reason,
                summary,
                agent_checks,
                urgency,
                language,
                preferred_followup,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
            """,
            (
                reference_id,
                sanitized["caller_identifier"],
                sanitized["caller_name"],
                sanitized["reason"],
                sanitized["summary"],
                sanitized["agent_checks"],
                sanitized["urgency"],
                sanitized["language"],
                sanitized["preferred_followup"],
                timestamp,
            ),
        )
        connection.commit()
        row_id = cursor.lastrowid

    return get_escalation_by_id(row_id) or {
        "reference_id": reference_id,
        "status": "Open",
        "created_at": timestamp,
    }


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "reference_id": row["reference_id"],
        "caller_identifier": row["caller_identifier"],
        "caller_name": row["caller_name"],
        "reason": row["reason"],
        "summary": row["summary"],
        "agent_checks": row["agent_checks"],
        "urgency": row["urgency"],
        "language": row["language"],
        "preferred_followup": row["preferred_followup"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def get_escalation_by_id(escalation_id: int) -> dict[str, Any] | None:
    """Look up a single escalation by its numeric ID."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM escalations WHERE id = ?",
            (escalation_id,),
        ).fetchone()

    return _row_to_dict(row) if row else None


def list_escalations(status: str | None = None) -> list[dict[str, Any]]:
    """Return all escalations, optionally filtered by status."""
    with get_connection() as connection:
        if status:
            rows = connection.execute(
                """
                SELECT * FROM escalations
                WHERE status = ?
                ORDER BY created_at DESC
                """,
                (status,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM escalations
                ORDER BY created_at DESC
                """
            ).fetchall()

    return [_row_to_dict(row) for row in rows]


def update_escalation_status(
    escalation_id: int, status: str
) -> dict[str, Any] | None:
    """Update the status of an escalation request."""
    allowed = {"Open", "In Progress", "Resolved"}
    if status not in allowed:
        raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")

    with get_connection() as connection:
        connection.execute(
            "UPDATE escalations SET status = ? WHERE id = ?",
            (status, escalation_id),
        )
        connection.commit()

    return get_escalation_by_id(escalation_id)


initialize_escalations_table()
