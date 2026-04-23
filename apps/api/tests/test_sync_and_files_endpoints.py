import os
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.deps import get_current_user
from app.main import app

client = TestClient(app)


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="660000000000000000000001",
        role="admin",
        is_active=True,
    )


def test_sync_bootstrap_contract(monkeypatch) -> None:
    async def fake_bootstrap(*_args, **_kwargs):
        return {
            "server_time": datetime.now(UTC).isoformat(),
            "user": {"id": "u1"},
            "reservation_rules": {"min_days_in_advance": 7},
            "emergency_contacts": {"items": []},
            "experiences": [],
            "schedules": [],
            "equines": [],
            "cursors": {"reservations": ""},
        }

    monkeypatch.setattr("app.api.endpoints.sync.service.build_bootstrap", fake_bootstrap)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.get("/api/v1/sync/bootstrap")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert "server_time" in body
    assert "user" in body
    assert "cursors" in body


def test_files_init_upload_contract(monkeypatch) -> None:
    async def fake_init_upload(*_args, **_kwargs):
        return {
            "upload_id": "up-1",
            "storage_key": "payment_proof/up-1-proof.pdf",
            "upload_url": "https://example.com/upload",
            "expires_at": datetime.now(UTC).isoformat(),
        }

    monkeypatch.setattr("app.api.endpoints.files.service.init_upload", fake_init_upload)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/files/init-upload",
        json={
            "context": "payment_proof",
            "filename": "proof.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1024,
            "sha256_hash": "abc",
        },
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["upload_id"] == "up-1"
    assert body["storage_key"].startswith("payment_proof/")
