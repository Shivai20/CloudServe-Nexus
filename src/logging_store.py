"""Decision Audit Logging Module (A8).

Maintains a strict 1:1 persistent audit trail of every automated decision,
conforming to the required Governance Framework schema across both SQLite
and JSONL file logs.
"""

from typing import Any, Dict, List, Optional
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from src.models import DecisionLogEntry

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "storage", "decisions.db"
)
DEFAULT_JSONL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "storage", "decisions.jsonl"
)


class DecisionLoggingStore:
    """Manages persistent logging of all routing and generation decisions."""

    def __init__(
        self, db_path: str = DEFAULT_DB_PATH, jsonl_path: str = DEFAULT_JSONL_PATH
    ):
        self.db_path = db_path
        self.jsonl_path = jsonl_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.jsonl_path), exist_ok=True)
        self._init_sqlite()

    def _init_sqlite(self):
        """Initializes the SQLite decisions table matching the governance schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    ticket_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    input_summary TEXT,
                    model_info TEXT,
                    prediction TEXT,
                    alternatives TEXT,
                    sources_used TEXT,
                    threshold_applied REAL,
                    action_taken TEXT NOT NULL,
                    reason TEXT,
                    guardrail_results TEXT,
                    prompt_version TEXT,
                    requirement_ids TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_id ON decisions(ticket_id)")
            conn.commit()

    def log_decision(self, entry: DecisionLogEntry) -> None:
        """Persists a decision entry to SQLite and appends to the JSONL audit log."""
        # 1. Write to SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO decisions (
                        decision_id, timestamp, ticket_id, stage, input_summary,
                        model_info, prediction, alternatives, sources_used,
                        threshold_applied, action_taken, reason,
                        guardrail_results, prompt_version, requirement_ids
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.decision_id,
                        entry.timestamp,
                        entry.ticket_id,
                        entry.stage,
                        entry.input_summary,
                        json.dumps(entry.model),
                        json.dumps(entry.prediction),
                        json.dumps(entry.alternatives),
                        json.dumps(entry.sources_used),
                        entry.threshold_applied,
                        entry.action_taken,
                        entry.reason,
                        json.dumps(entry.guardrail_results),
                        entry.prompt_version,
                        json.dumps(entry.requirement_ids),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to write decision to SQLite: {e}")

        # 2. Append to JSONL log file
        try:
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to append decision to JSONL: {e}")

    def count_decisions_for_ticket(self, ticket_id: str) -> int:
        """Counts logged decisions for a specific ticket."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM decisions WHERE ticket_id = ?", (ticket_id,))
            return cursor.fetchone()[0]

    def get_all_decisions(self) -> List[Dict[str, Any]]:
        """Retrieves all logged decisions from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def clear(self):
        """Clears existing logs (used before new batch test runs)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM decisions")
            conn.commit()
        if os.path.exists(self.jsonl_path):
            os.remove(self.jsonl_path)


_logger_store_instance: Optional[DecisionLoggingStore] = None


def get_logging_store(
    db_path: str = DEFAULT_DB_PATH, jsonl_path: str = DEFAULT_JSONL_PATH
) -> DecisionLoggingStore:
    global _logger_store_instance
    if _logger_store_instance is None:
        _logger_store_instance = DecisionLoggingStore(
            db_path=db_path, jsonl_path=jsonl_path
        )
    return _logger_store_instance
