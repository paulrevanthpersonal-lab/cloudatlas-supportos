from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterator

from .models import CaseCreate, CaseUpdate

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "cloudatlas.db"

SEED_CASES = [
    ("CA-1001", "Conditional Access lockout", "Entra ID", "Identity", "Priya S.", "critical", "escalated", "Remote administrators cannot refresh privileged sessions", 30),
    ("CA-1002", "Checkout API latency regression", "Commerce API", "Application", "Marcus L.", "high", "investigating", "Checkout requests exceed the 1.5-second response target", 60),
    ("CA-1003", "Private DNS resolution drift", "Core Network", "Network", "Paul R.", "high", "investigating", "Two application subnets resolve stale private endpoints", 60),
    ("CA-1004", "Nightly export schema failure", "Reporting", "Data", "Elena M.", "medium", "investigating", "Finance exports fail downstream validation", 240),
    ("CA-1005", "Linux monitoring agent mismatch", "Observability", "Linux", "Noah K.", "low", "resolved", "Three hosts report delayed metrics after patching", 480),
    ("CA-1006", "Scoped Azure access request", "Cloud Platform", "Identity", "Paul R.", "medium", "new", "New operations analyst requires least-privilege access", 240),
    ("CA-1007", "VPN authentication loop", "Remote Access", "Network", "Mina K.", "high", "investigating", "Remote engineers cannot establish the corporate tunnel", 60),
    ("CA-1008", "Storage account firewall denial", "Azure Storage", "Cloud", "Paul R.", "high", "escalated", "Integration workers cannot write settlement files", 60),
    ("CA-1009", "Container image pull failure", "AKS Platform", "Delivery", "Avery J.", "high", "investigating", "New pods remain in ImagePullBackOff", 60),
    ("CA-1010", "Certificate expiry warning", "API Gateway", "Security", "Priya S.", "critical", "resolved", "Public gateway certificate expires within 24 hours", 30),
    ("CA-1011", "Route table blackhole", "Azure Network", "Network", "Paul R.", "critical", "escalated", "Application tier cannot reach the managed database", 30),
    ("CA-1012", "Redis memory saturation", "Session Cache", "Application", "Marcus L.", "high", "investigating", "Session eviction rate causes intermittent sign-outs", 60),
    ("CA-1013", "MFA registration gap", "Entra ID", "Identity", "Priya S.", "medium", "new", "Seven contractor accounts are outside registration policy", 240),
    ("CA-1014", "Log Analytics ingestion delay", "Observability", "Cloud", "Noah K.", "medium", "investigating", "Security events arrive more than fifteen minutes late", 240),
    ("CA-1015", "Ubuntu kernel reboot required", "Linux Fleet", "Linux", "Paul R.", "low", "new", "Twelve hosts require coordinated maintenance reboot", 480),
    ("CA-1016", "Webhook signature mismatch", "Partner Integration", "Application", "Elena M.", "high", "resolved", "Partner callbacks fail signature validation", 60),
    ("CA-1017", "Key Vault secret version drift", "Secrets Platform", "Security", "Priya S.", "high", "investigating", "Two applications reference a disabled secret version", 60),
    ("CA-1018", "CI runner disk pressure", "Build Platform", "Delivery", "Avery J.", "medium", "resolved", "Build agents fail while unpacking container layers", 240),
    ("CA-1019", "MySQL replication lag", "Customer Database", "Data", "Elena M.", "critical", "escalated", "Read replica trails primary by eleven minutes", 30),
    ("CA-1020", "RBAC inheritance conflict", "Cloud Platform", "Identity", "Paul R.", "medium", "investigating", "Support group receives broader access than intended", 240),
    ("CA-1021", "Outbound SNAT exhaustion", "Azure Network", "Network", "Mina K.", "critical", "resolved", "API nodes intermittently lose outbound connectivity", 30),
    ("CA-1022", "Queue poison-message backlog", "Order Worker", "Application", "Marcus L.", "high", "investigating", "Failed messages block normal order processing", 60),
    ("CA-1023", "Defender sensor unhealthy", "Security Monitoring", "Security", "Priya S.", "high", "new", "Four endpoints stopped reporting security telemetry", 60),
    ("CA-1024", "Terraform state lock orphaned", "Infrastructure Delivery", "Delivery", "Avery J.", "medium", "resolved", "Approved infrastructure change cannot acquire state", 240),
    ("CA-1025", "SFTP host-key rotation", "File Exchange", "Security", "Paul R.", "medium", "investigating", "Automated transfers reject the rotated host key", 240),
    ("CA-1026", "NTP clock skew", "Linux Fleet", "Linux", "Noah K.", "high", "resolved", "Authentication tokens fail validation on five hosts", 60),
    ("CA-1027", "Power BI refresh timeout", "Analytics", "Data", "Elena M.", "medium", "new", "Executive dashboard misses the morning refresh", 240),
    ("CA-1028", "WAF false-positive block", "Edge Security", "Security", "Priya S.", "high", "investigating", "Legitimate multipart uploads receive HTTP 403", 60),
    ("CA-1029", "Docker registry quota alert", "Container Registry", "Delivery", "Avery J.", "low", "new", "Artifact retention approaches the storage quota", 480),
    ("CA-1030", "User acceptance test data mismatch", "Release Validation", "Data", "Paul R.", "medium", "resolved", "UAT totals differ from the approved baseline", 240),
]

RUNBOOKS = [
    ("SOP-001", "Restore Azure VM administrative access", "Azure, Linux, SSH", 8),
    ("SOP-002", "Resolve private DNS drift", "DNS, Network, Private Link", 7),
    ("SOP-003", "Investigate Conditional Access blocks", "Entra ID, IAM, MFA", 9),
    ("SOP-004", "Triage REST API integration failure", "API, Logs, Contracts", 10),
    ("SOP-005", "Validate and roll back a deployment", "CI/CD, Docker, Release", 8),
    ("SOP-006", "Restore missing telemetry", "Azure Monitor, Linux, Logs", 7),
    ("SOP-007", "Diagnose VPN authentication loops", "VPN, RADIUS, Identity", 8),
    ("SOP-008", "Recover from SNAT port exhaustion", "NAT Gateway, Network", 9),
    ("SOP-009", "Rotate application secrets safely", "Key Vault, IAM", 10),
    ("SOP-010", "Clear orphaned Terraform state locks", "Terraform, IaC", 6),
    ("SOP-011", "Repair MySQL replication lag", "MySQL, Data", 9),
    ("SOP-012", "Respond to certificate expiry", "TLS, Key Vault", 8),
    ("SOP-013", "Reconcile RBAC inheritance", "Azure RBAC, IAM", 7),
    ("SOP-014", "Drain a poison-message queue", "Queues, Application", 8),
    ("SOP-015", "Recover container image pulls", "AKS, Registry, Docker", 7),
    ("SOP-016", "Validate SFTP host-key rotation", "SFTP, Security", 6),
    ("SOP-017", "Correct Linux NTP clock skew", "Linux, NTP", 6),
    ("SOP-018", "Investigate WAF false positives", "WAF, HTTP, Security", 9),
]

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
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
          id INTEGER PRIMARY KEY AUTOINCREMENT, external_id TEXT UNIQUE, title TEXT NOT NULL,
          service TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'Application', owner TEXT NOT NULL,
          priority TEXT NOT NULL, status TEXT NOT NULL, impact TEXT NOT NULL, opened_at TEXT NOT NULL,
          updated_at TEXT NOT NULL, sla_minutes INTEGER NOT NULL, resolution_note TEXT
        );
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, stage TEXT NOT NULL DEFAULT 'triage',
          event_type TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL,
          FOREIGN KEY(case_id) REFERENCES cases(id)
        );
        CREATE TABLE IF NOT EXISTS runbooks (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, tags TEXT NOT NULL, steps INTEGER NOT NULL
        );
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(cases)")}
        if "external_id" not in columns: conn.execute("ALTER TABLE cases ADD COLUMN external_id TEXT")
        if "category" not in columns: conn.execute("ALTER TABLE cases ADD COLUMN category TEXT NOT NULL DEFAULT 'Application'")
        event_columns = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
        if "stage" not in event_columns: conn.execute("ALTER TABLE events ADD COLUMN stage TEXT NOT NULL DEFAULT 'triage'")
        timestamp = now()
        for index, row in enumerate(SEED_CASES):
            opened = (datetime.now(UTC) - timedelta(hours=index * 3 + 1)).replace(microsecond=0).isoformat()
            conn.execute("""INSERT OR IGNORE INTO cases
              (external_id,title,service,category,owner,priority,status,impact,opened_at,updated_at,sla_minutes)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (*row[:8], opened, timestamp, row[8]))
        conn.executemany("INSERT OR IGNORE INTO runbooks (id,title,tags,steps) VALUES (?,?,?,?)", RUNBOOKS)
        for case in conn.execute("SELECT id,status FROM cases WHERE id NOT IN (SELECT DISTINCT case_id FROM events)").fetchall():
            stages = [
                ("reproduce", "evidence", "Impact reproduced and affected scope recorded"),
                ("analyze", "evidence", "Logs, changes, dependencies, and timestamps correlated"),
                ("isolate", "diagnosis", "Most likely failure domain isolated with reversible tests"),
            ]
            if case["status"] in {"escalated", "resolved"}: stages.append(("escalate", "handoff", "Evidence package and decision request sent to service owner"))
            if case["status"] == "resolved": stages += [("validate", "recovery", "User path and telemetry verified after remediation"), ("document", "closure", "Root cause and prevention notes added to knowledge base")]
            conn.executemany("INSERT INTO events (case_id,stage,event_type,detail,created_at) VALUES (?,?,?,?,?)", [(case["id"], *stage, timestamp) for stage in stages])

def list_cases(query: str = "", status: str = "", priority: str = "") -> list[dict]:
    clauses, values = [], []
    if query: clauses.append("(title LIKE ? OR service LIKE ? OR owner LIKE ? OR external_id LIKE ?)"); values += [f"%{query}%"] * 4
    if status: clauses.append("status = ?"); values.append(status)
    if priority: clauses.append("priority = ?"); values.append(priority)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connection() as conn:
        rows = conn.execute(f"SELECT * FROM cases {where} ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, id", values).fetchall()
        return [dict(row) for row in rows]

def get_case(case_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row: return None
        result = dict(row)
        result["events"] = [dict(item) for item in conn.execute("SELECT * FROM events WHERE case_id = ? ORDER BY id", (case_id,)).fetchall()]
        return result

def create_case(payload: CaseCreate) -> dict:
    timestamp = now(); sla = {"critical":30,"high":60,"medium":240,"low":480}[payload.priority.value]
    with connection() as conn:
        number = conn.execute("SELECT COALESCE(MAX(id),0)+1001 FROM cases").fetchone()[0]
        cursor = conn.execute("""INSERT INTO cases
          (external_id,title,service,category,owner,priority,status,impact,opened_at,updated_at,sla_minutes)
          VALUES (?,?,?,?,?,?,'new',?,?,?,?)""", (f"CA-{number}",payload.title,payload.service,payload.category,payload.owner,payload.priority.value,payload.impact,timestamp,timestamp,sla))
        case_id = cursor.lastrowid
        conn.execute("INSERT INTO events (case_id,stage,event_type,detail,created_at) VALUES (?,'intake','created',?,?)", (case_id,f"{payload.priority.value.title()} incident created",timestamp))
        return dict(conn.execute("SELECT * FROM cases WHERE id = ?",(case_id,)).fetchone())

def update_case(case_id: int, payload: CaseUpdate) -> dict | None:
    timestamp = now()
    with connection() as conn:
        result = conn.execute("UPDATE cases SET status=?,resolution_note=?,updated_at=? WHERE id=?",(payload.status.value,payload.resolution_note,timestamp,case_id))
        if result.rowcount == 0: return None
        stage = "validate" if payload.status.value == "resolved" else "escalate" if payload.status.value == "escalated" else "analyze"
        conn.execute("INSERT INTO events (case_id,stage,event_type,detail,created_at) VALUES (?,?,'status',?,?)",(case_id,stage,f"Status changed to {payload.status.value}: {payload.resolution_note}",timestamp))
        return dict(conn.execute("SELECT * FROM cases WHERE id=?",(case_id,)).fetchone())

def add_event(case_id: int, stage: str, detail: str) -> dict | None:
    with connection() as conn:
        if not conn.execute("SELECT 1 FROM cases WHERE id=?",(case_id,)).fetchone(): return None
        timestamp = now(); cursor = conn.execute("INSERT INTO events (case_id,stage,event_type,detail,created_at) VALUES (?,?,'note',?,?)",(case_id,stage,detail,timestamp))
        return dict(conn.execute("SELECT * FROM events WHERE id=?",(cursor.lastrowid,)).fetchone())

def list_runbooks(query: str = "") -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM runbooks WHERE title LIKE ? OR tags LIKE ? ORDER BY id",(f"%{query}%",f"%{query}%")).fetchall()
        return [dict(row) for row in rows]

def metrics() -> dict:
    with connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]; active = conn.execute("SELECT COUNT(*) FROM cases WHERE status!='resolved'").fetchone()[0]
        by_status = {row[0]:row[1] for row in conn.execute("SELECT status,COUNT(*) FROM cases GROUP BY status")}
        by_category = {row[0]:row[1] for row in conn.execute("SELECT category,COUNT(*) FROM cases GROUP BY category ORDER BY COUNT(*) DESC")}
        critical = conn.execute("SELECT COUNT(*) FROM cases WHERE priority='critical' AND status!='resolved'").fetchone()[0]
        return {"total":total,"active":active,"critical":critical,"resolved":by_status.get("resolved",0),"sla_health":round(100-(critical/max(active,1)*10),1),"by_status":by_status,"by_category":by_category,"runbooks":conn.execute("SELECT COUNT(*) FROM runbooks").fetchone()[0]}

def recent_events() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT events.*,cases.title,cases.external_id FROM events JOIN cases ON cases.id=events.case_id ORDER BY events.id DESC LIMIT 20").fetchall()
        return [dict(row) for row in rows]
