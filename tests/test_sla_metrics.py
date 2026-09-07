from datetime import UTC, datetime

from app import store


def test_sla_metrics_classify_active_cases_against_their_deadlines(tmp_path, monkeypatch):
    """Changing deadline logic must fail this test, not merely alter a score."""
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cloudatlas.db")
    store.initialize()
    with store.connection() as conn:
        conn.execute("UPDATE cases SET status = 'resolved'")
        conn.execute(
            "UPDATE cases SET status = 'investigating', opened_at = ?, sla_minutes = 60 WHERE external_id = ?",
            ("2026-09-07T10:00:00+00:00", "CA-1001"),
        )
        conn.execute(
            "UPDATE cases SET status = 'investigating', opened_at = ?, sla_minutes = 60 WHERE external_id = ?",
            ("2026-09-07T11:10:00+00:00", "CA-1002"),
        )
        conn.execute(
            "UPDATE cases SET status = 'investigating', opened_at = ?, sla_minutes = 60 WHERE external_id = ?",
            ("2026-09-07T11:30:00+00:00", "CA-1003"),
        )

    result = store.metrics(reference_time=datetime(2026, 9, 7, 12, 0, tzinfo=UTC))

    assert result["sla"] == {
        "active": 3,
        "on_time": 1,
        "at_risk": 1,
        "breached": 1,
        "compliance_percent": 33.3,
    }
    assert result["sla_health"] == 33.3


def test_sla_metrics_exclude_resolved_cases_from_active_compliance(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cloudatlas.db")
    store.initialize()
    with store.connection() as conn:
        conn.execute("UPDATE cases SET status = 'resolved'")
        conn.execute(
            "UPDATE cases SET opened_at = ?, sla_minutes = 30 WHERE external_id = ?",
            ("2026-09-07T10:00:00+00:00", "CA-1001"),
        )

    result = store.metrics(reference_time=datetime(2026, 9, 7, 12, 0, tzinfo=UTC))

    assert result["sla"] == {
        "active": 0,
        "on_time": 0,
        "at_risk": 0,
        "breached": 0,
        "compliance_percent": 100.0,
    }
