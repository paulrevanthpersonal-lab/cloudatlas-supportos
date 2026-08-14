import os
from pathlib import Path

os.environ.setdefault("CLOUDATLAS_TESTING", "1")

from fastapi.testclient import TestClient

from app.main import app
from app.store import DB_PATH


def setup_module():
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()


def test_health_and_seeded_cases():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        cases = client.get("/api/cases")
        assert cases.status_code == 200
        assert len(cases.json()) >= 5


def test_create_and_resolve_case():
    with TestClient(app) as client:
        created = client.post(
            "/api/cases",
            json={"title": "VPN login loop", "service": "Remote Access", "owner": "Paul R.", "priority": "high", "impact": "Remote engineers cannot reach internal tools"},
        )
        assert created.status_code == 201
        case_id = created.json()["id"]
        updated = client.patch(
            f"/api/cases/{case_id}",
            json={"status": "resolved", "resolution_note": "Token cache cleared and sign-in verified"},
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == "resolved"


def test_validation_rejects_incomplete_case():
    with TestClient(app) as client:
        response = client.post("/api/cases", json={"title": "x"})
        assert response.status_code == 422

