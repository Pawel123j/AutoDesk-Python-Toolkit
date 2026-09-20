from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "toolkit.db"


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                action_type TEXT NOT NULL,
                file_name TEXT NOT NULL,
                details TEXT
            )
            """
        )
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    init_db()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def add_history(action_type: str, file_name: str, details: dict[str, Any] | None = None) -> None:
    payload = json.dumps(details or {}, ensure_ascii=True)
    created_at = datetime.now(UTC).isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO history (created_at, action_type, file_name, details)
            VALUES (?, ?, ?, ?)
            """,
            (created_at, action_type, file_name, payload),
        )
        connection.commit()


def fetch_history(limit: int = 100) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 250))
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, action_type, file_name, details
            FROM history
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    history: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["details"] = json.loads(item.get("details") or "{}")
        except json.JSONDecodeError:
            item["details"] = {}
        history.append(item)
    return history


def clear_history() -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM history")
        connection.commit()
