import asyncio
import os
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.deps import get_current_user
from app.common.enums import ExperienceCategory, ExperienceStatus, UserRole
from app.core.di import Container
from app.main import app
from app.schemas.experience import ExperienceCreateSchema
from app.schemas.sync import SyncPushOperationSchema
from app.services.sync_handlers._shared import strip_null_values
from app.services.sync_service import SyncOperationExecutor

client = TestClient(app)


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="660000000000000000000001",
        role=UserRole.ADMIN,
        is_active=True,
    )


def _guide_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="660000000000000000000002",
        role=UserRole.GUIDE,
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
            "equines": [],
            "cursors": {"reservations": ""},
        }

    monkeypatch.setattr(Container.get_instance().sync_service, "build_bootstrap", fake_bootstrap)
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

    monkeypatch.setattr(Container.get_instance().file_upload_service, "init_upload", fake_init_upload)
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


def test_sync_executor_rejects_catalog_write_for_guide() -> None:
    operation = SyncPushOperationSchema(
        operation_id="op-1",
        entity_type="experience",
        entity_local_id="local-experience-1",
        operation_type="create",
        idempotency_key="idem-op-1",
        payload={
            "name": "Ruta de prueba",
            "slug": "ruta-prueba",
            "description": "Descripcion",
            "level": "basic",
            "duration_hours": 2,
        },
    )
    from app.services.sync_handlers import (
        ConfigSyncHandler, ExperienceSyncHandler, ReservationSyncHandler, ResourceSyncHandler,
    )
    _c = Container.get_instance()
    executor = SyncOperationExecutor(
        experience_handler=ExperienceSyncHandler(
            experience_service=_c.experience_service,
        ),
        reservation_handler=ReservationSyncHandler(
            reservation_service=_c.reservation_service,
            participant_service=_c.participant_service,
            payment_proof_service=_c.payment_proof_service,
            assignment_service=_c.assignment_service,
            service_log_service=_c.service_log_service,
        ),
        resource_handler=ResourceSyncHandler(
            provider_service=_c.provider_service,
            policy_service=_c.policy_service,
        ),
        config_handler=ConfigSyncHandler(config_service=_c.config_service),
    )
    result = asyncio.run(
        executor.execute(
            current_user=_guide_user(),
            operation=operation,
        )
    )
    assert result.status == "rejected"
    assert result.error is not None
    assert result.error.code == "auth.forbidden"


def test_experience_create_payload_applies_defaults_when_optional_fields_are_null() -> None:
    payload = strip_null_values(
        {
            "name": "Ruta de prueba",
            "slug": "ruta-prueba",
            "description": "Descripcion",
            "level": "basic",
            "category": None,
            "status": None,
            "tags": None,
            "duration_hours": 2,
        }
    )
    schema = ExperienceCreateSchema(**payload)
    assert schema.category == ExperienceCategory.EXPERIENCE
    assert schema.status == ExperienceStatus.PUBLISHED
    assert schema.tags == []
