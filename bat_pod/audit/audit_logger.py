"""Audit logger module using SQLite for persistent, offline-first compliance."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from bat_pod.config import settings
from bat_pod.core.models import AuditRecord


class AuditLogger:
    """Manages SQLite storage for all safety interventions and authorized actions."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = Path(db_path) if db_path else settings.get_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create audit table schema if not already present."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    sensor_context TEXT NOT NULL,
                    requested_action TEXT NOT NULL,
                    authorization TEXT NOT NULL,
                    execution_result TEXT NOT NULL,
                    verification_result TEXT NOT NULL,
                    error TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC)"
            )
            conn.commit()

    def log(
        self,
        user: str,
        intent: str,
        requested_action: str,
        authorization: str,
        execution_result: str,
        verification_result: str,
        sensor_context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """Record an audit event and return its generated ID."""
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        ctx_json = json.dumps(sensor_context or {})

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (
                    timestamp, user, intent, sensor_context,
                    requested_action, authorization, execution_result,
                    verification_result, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    user,
                    intent,
                    ctx_json,
                    requested_action,
                    authorization,
                    execution_result,
                    verification_result,
                    error,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def log_record(self, record: AuditRecord) -> int:
        """Log a typed AuditRecord object."""
        return self.log(
            user=record.user,
            intent=record.intent,
            requested_action=record.requested_action,
            authorization=record.authorization,
            execution_result=record.execution_result,
            verification_result=record.verification_result,
            sensor_context=record.sensor_context,
            error=record.error,
            timestamp=record.timestamp,
        )

    def get_recent(self, limit: int = 10) -> List[AuditRecord]:
        """Fetch the most recent audit records in descending chronological order."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, user, intent, sensor_context,
                       requested_action, authorization, execution_result,
                       verification_result, error
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            records = []
            for r in rows:
                try:
                    ctx = json.loads(r["sensor_context"])
                except Exception:
                    ctx = {}
                records.append(
                    AuditRecord(
                        id=r["id"],
                        timestamp=r["timestamp"],
                        user=r["user"],
                        intent=r["intent"],
                        sensor_context=ctx,
                        requested_action=r["requested_action"],
                        authorization=r["authorization"],
                        execution_result=r["execution_result"],
                        verification_result=r["verification_result"],
                        error=r["error"],
                    )
                )
            return records

    def get_latest_record(self) -> Optional[AuditRecord]:
        """Retrieve the most recent audit record."""
        recent = self.get_recent(limit=1)
        return recent[0] if recent else None

    def get_latest_emergency_or_action(self) -> Optional[AuditRecord]:
        """Find the latest emergency intervention or physical action record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, user, intent, sensor_context,
                       requested_action, authorization, execution_result,
                       verification_result, error
                FROM audit_logs
                WHERE requested_action NOT IN ('none', '')
                ORDER BY id DESC
                LIMIT 1
                """
            )
            r = cursor.fetchone()
            if not r:
                return None
            try:
                ctx = json.loads(r["sensor_context"])
            except Exception:
                ctx = {}
            return AuditRecord(
                id=r["id"],
                timestamp=r["timestamp"],
                user=r["user"],
                intent=r["intent"],
                sensor_context=ctx,
                requested_action=r["requested_action"],
                authorization=r["authorization"],
                execution_result=r["execution_result"],
                verification_result=r["verification_result"],
                error=r["error"],
            )


# Default global audit logger instance
audit_logger = AuditLogger()
