from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from .models import CaseCreate, CaseUpdate


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "cloudatlas.db"


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def initialize() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                service TEXT NOT NULL,
                owner TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                impact TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sla_minutes INTEGER NOT NULL,
                resolution_note TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        if count == 0:
            seed = [
                ("Conditional Access lockout", "Entra ID", "Priya S.", "critical", "escalated", "Remote administrators cannot refresh sessions", 30),
                ("Intermittent API latency", "Client API", "Marcus L.", "high", "investigating", "Checkout requests exceed 1.5 seconds", 60),
                ("DNS resolution drift", "Core Network", "Paul R.", "high", "investigating", "Two application subnets resolve stale records", 60),
                ("Data export validation errors", "Reporting", "Elena M.", "medium", "investigating", "Nightly exports fail schema validation", 240),
                ("Linux agent version mismatch", "Observability", "Noah K.", "low", "resolved", "Three hosts report delayed metrics", 480),
                ("Azure portal access request", "Cloud Platform", "Paul R.", "medium", "new", "New operations analyst requires scoped access", 240),
            ]
            timestamp = now()
            conn.executemany(
                """INSERT INTO cases
                (title, service, owner, priority, status, impact, opened_at, updated_at, sla_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(*row[:6], timestamp, timestamp, row[6]) for row in seed],
            )
            conn.executemany(
                "INSERT INTO events (case_id, event_type, detail, created_at) VALUES (?, ?, ?, ?)",
                [
                    (1, "evidence", "Authentication logs attached to incident timeline", timestamp),
                    (2, "change", "Deployment correlation identified in release window", timestamp),
                    (3, "mitigation", "Resolver cache flushed and TTL policy corrected", timestamp),
                    (4, "triage", "Invalid payload isolated to upstream mapping", timestamp),
                ],
            )


def list_cases() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, id").fetchall()
        return [dict(row) for row in rows]


def create_case(payload: CaseCreate) -> dict:
    timestamp = now()
    sla = {"critical": 30, "high": 60, "medium": 240, "low": 480}[payload.priority.value]
    with connection() as conn:
        cursor = conn.execute(
            """INSERT INTO cases
            (title, service, owner, priority, status, impact, opened_at, updated_at, sla_minutes)
            VALUES (?, ?, ?, ?, 'new', ?, ?, ?, ?)""",
            (payload.title, payload.service, payload.owner, payload.priority.value, payload.impact, timestamp, timestamp, sla),
        )
        case_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO events (case_id, event_type, detail, created_at) VALUES (?, 'created', ?, ?)",
            (case_id, f"Case created with {payload.priority.value} priority", timestamp),
        )
        return dict(conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone())


def update_case(case_id: int, payload: CaseUpdate) -> dict | None:
    timestamp = now()
    with connection() as conn:
        result = conn.execute(
            "UPDATE cases SET status = ?, resolution_note = ?, updated_at = ? WHERE id = ?",
            (payload.status.value, payload.resolution_note, timestamp, case_id),
        )
        if result.rowcount == 0:
            return None
        conn.execute(
            "INSERT INTO events (case_id, event_type, detail, created_at) VALUES (?, 'status', ?, ?)",
            (case_id, f"Status changed to {payload.status.value}: {payload.resolution_note}", timestamp),
        )
        return dict(conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone())


def metrics() -> dict:
    with connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM cases WHERE status != 'resolved'").fetchone()[0]
        critical = conn.execute("SELECT COUNT(*) FROM cases WHERE priority = 'critical' AND status != 'resolved'").fetchone()[0]
        resolved = conn.execute("SELECT COUNT(*) FROM cases WHERE status = 'resolved'").fetchone()[0]
        return {
            "total": total,
            "active": active,
            "critical": critical,
            "resolved": resolved,
            "sla_health": round(100 - (critical / max(active, 1) * 12), 1),
        }


def recent_events() -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            """SELECT events.*, cases.title FROM events
            JOIN cases ON cases.id = events.case_id
            ORDER BY events.id DESC LIMIT 8"""
        ).fetchall()
        return [dict(row) for row in rows]
