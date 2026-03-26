"""SQLite metrics storage for dashboard"""
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from finance_data.dashboard.models import CallRecord, ConsistencyResult, FieldDiff, ToolStats

_DEFAULT_DB = Path.home() / ".finance_data" / "dashboard_metrics.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS call_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool TEXT NOT NULL,
    provider TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL,
    response_time_ms REAL NOT NULL DEFAULT 0.0,
    error TEXT,
    source TEXT NOT NULL DEFAULT 'probe'
);
CREATE INDEX IF NOT EXISTS idx_tool_provider ON call_records(tool, provider);
CREATE INDEX IF NOT EXISTS idx_timestamp ON call_records(timestamp);

CREATE TABLE IF NOT EXISTS consistency_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL,
    providers_compared TEXT NOT NULL,
    record_counts TEXT NOT NULL DEFAULT '{}',
    diffs TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_consistency_tool ON consistency_results(tool);
CREATE INDEX IF NOT EXISTS idx_consistency_timestamp ON consistency_results(timestamp);
"""


class MetricsStore:
    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or _DEFAULT_DB
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self._db_path), check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_schema(self) -> None:
        conn = self._get_conn()
        conn.executescript(_SCHEMA)
        conn.commit()

    def record(
        self,
        tool: str,
        provider: str,
        status: str,
        response_time_ms: float,
        error: Optional[str] = None,
        source: str = "probe",
    ) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO call_records (tool, provider, timestamp, status, response_time_ms, error, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tool, provider, datetime.utcnow().isoformat(), status, response_time_ms, error, source),
        )
        conn.commit()

    def get_latest(
        self,
        tool: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> List[CallRecord]:
        conn = self._get_conn()
        query = """
            SELECT t.tool, t.provider, t.timestamp, t.status, t.response_time_ms, t.error, t.source
            FROM call_records t
            INNER JOIN (
                SELECT tool, provider, MAX(id) as max_id
                FROM call_records
                {where}
                GROUP BY tool, provider
            ) latest ON t.id = latest.max_id
            ORDER BY t.timestamp DESC
        """
        conditions = []
        params = []
        if tool:
            conditions.append("tool = ?")
            params.append(tool)
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(query.format(where=where), params).fetchall()
        return [
            CallRecord(
                tool=r["tool"],
                provider=r["provider"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                status=r["status"],
                response_time_ms=r["response_time_ms"],
                error=r["error"],
                source=r["source"],
            )
            for r in rows
        ]

    def get_stats(
        self,
        tool: Optional[str] = None,
        provider: Optional[str] = None,
        hours: int = 24,
    ) -> List[ToolStats]:
        conn = self._get_conn()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conditions = ["timestamp >= ?"]
        params: list = [cutoff]
        if tool:
            conditions.append("tool = ?")
            params.append(tool)
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        where = "WHERE " + " AND ".join(conditions)
        query = f"""
            SELECT tool, provider,
                   COUNT(*) as total_calls,
                   SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as success_count,
                   AVG(response_time_ms) as avg_response_ms
            FROM call_records
            {where}
            GROUP BY tool, provider
            ORDER BY tool, provider
        """
        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            total = r["total_calls"]
            success = r["success_count"]
            rate = (success / total * 100) if total > 0 else 0.0
            # Get last record for this pair
            last = conn.execute(
                "SELECT status, timestamp, error FROM call_records "
                "WHERE tool = ? AND provider = ? ORDER BY id DESC LIMIT 1",
                (r["tool"], r["provider"]),
            ).fetchone()
            results.append(ToolStats(
                tool=r["tool"],
                provider=r["provider"],
                total_calls=total,
                success_count=success,
                success_rate=round(rate, 1),
                avg_response_ms=round(r["avg_response_ms"], 1),
                last_status=last["status"] if last else None,
                last_check_time=datetime.fromisoformat(last["timestamp"]) if last else None,
                last_error=last["error"] if last else None,
            ))
        return results

    def record_consistency(self, result: ConsistencyResult) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO consistency_results (tool, timestamp, status, providers_compared, record_counts, diffs) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                result.tool,
                datetime.utcnow().isoformat(),
                result.status,
                json.dumps(result.providers_compared),
                json.dumps(result.record_counts),
                json.dumps([d.model_dump() for d in result.diffs]),
            ),
        )
        conn.commit()

    def get_latest_consistency(self) -> List[ConsistencyResult]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT c.tool, c.status, c.providers_compared, c.record_counts, c.diffs "
            "FROM consistency_results c "
            "INNER JOIN ("
            "  SELECT tool, MAX(id) as max_id FROM consistency_results GROUP BY tool"
            ") latest ON c.id = latest.max_id "
            "ORDER BY c.tool",
        ).fetchall()
        results = []
        for r in rows:
            results.append(ConsistencyResult(
                tool=r["tool"],
                status=r["status"],
                providers_compared=json.loads(r["providers_compared"]),
                record_counts=json.loads(r["record_counts"]),
                diffs=[FieldDiff(**d) for d in json.loads(r["diffs"])],
            ))
        return results

    def get_history(
        self,
        tool: str,
        provider: str,
        limit: int = 50,
    ) -> List[CallRecord]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT tool, provider, timestamp, status, response_time_ms, error, source "
            "FROM call_records WHERE tool = ? AND provider = ? "
            "ORDER BY id DESC LIMIT ?",
            (tool, provider, limit),
        ).fetchall()
        return [
            CallRecord(
                tool=r["tool"],
                provider=r["provider"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                status=r["status"],
                response_time_ms=r["response_time_ms"],
                error=r["error"],
                source=r["source"],
            )
            for r in rows
        ]
