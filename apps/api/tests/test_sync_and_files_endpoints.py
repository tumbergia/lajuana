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

    monkeypatch.setattr(
        Container.get_instance().file_upload_service, "init_upload", fake_init_upload
    )
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
        ConfigSyncHandler,
        ExperienceSyncHandler,
        NotificationSyncHandler,
        ReservationSyncHandler,
        ResourceSyncHandler,
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
        notification_handler=NotificationSyncHandler(),
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


def test_sync_executor_rejects_saddle_write_for_guide() -> None:
    """Un guía no puede crear sillas vía sync (solo admin)."""
    operation = SyncPushOperationSchema(
        operation_id="op-s",
        entity_type="saddle",
        entity_local_id="local-saddle-1",
        operation_type="create",
        idempotency_key="idem-saddle-1",
        payload={"code": "M-99"},
    )
    from app.services.sync_handlers import (
        ConfigSyncHandler,
        ExperienceSyncHandler,
        NotificationSyncHandler,
        ReservationSyncHandler,
        ResourceSyncHandler,
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
            saddle_service=_c.saddle_service,
        ),
        config_handler=ConfigSyncHandler(config_service=_c.config_service),
        notification_handler=NotificationSyncHandler(),
    )
    result = asyncio.run(executor.execute(current_user=_guide_user(), operation=operation))
    assert result.status == "rejected"
    assert result.error is not None
    assert result.error.code == "auth.forbidden"


def test_resource_handler_routes_saddle_operations() -> None:
    """ResourceSyncHandler enruta create/delete/restore de saddle al servicio."""
    from app.services.sync_handlers import ResourceSyncHandler

    created = SimpleNamespace(id="s1")
    calls: dict = {}

    async def _create(schema):
        calls["create"] = schema
        return created

    async def _soft_delete(saddle_id):
        calls["delete"] = saddle_id
        return SimpleNamespace(id=saddle_id)

    async def _restore(saddle_id):
        calls["restore"] = saddle_id
        return SimpleNamespace(id=saddle_id)

    fake_saddle = SimpleNamespace(
        create=_create,
        soft_delete=_soft_delete,
        restore=_restore,
    )
    handler = ResourceSyncHandler(
        provider_service=None,
        policy_service=None,
        saddle_service=fake_saddle,
    )

    create_op = SyncPushOperationSchema(
        operation_id="op-c",
        entity_type="saddle",
        entity_local_id="l1",
        operation_type="create",
        idempotency_key="i-c",
        payload={"code": "M-1"},
    )
    doc = asyncio.run(
        handler.handle(
            entity="saddle", op_type="create", operation=create_op, current_user=_admin_user()
        )
    )
    assert doc is created
    assert calls["create"].code == "M-1"

    delete_op = SyncPushOperationSchema(
        operation_id="op-d",
        entity_type="saddle",
        entity_local_id="l1",
        entity_remote_id="s1",
        operation_type="delete",
        idempotency_key="i-d",
        payload={},
    )
    asyncio.run(
        handler.handle(
            entity="saddle", op_type="delete", operation=delete_op, current_user=_admin_user()
        )
    )
    assert calls["delete"] == "s1"

    restore_op = SyncPushOperationSchema(
        operation_id="op-r",
        entity_type="saddle",
        entity_local_id="l1",
        entity_remote_id="s1",
        operation_type="restore",
        idempotency_key="i-r",
        payload={},
    )
    asyncio.run(
        handler.handle(
            entity="saddle", op_type="restore", operation=restore_op, current_user=_admin_user()
        )
    )
    assert calls["restore"] == "s1"


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


def test_reservation_handler_routes_assignment_delete() -> None:
    """ReservationSyncHandler enruta delete de assignment a remove()."""
    from app.services.sync_handlers import ReservationSyncHandler

    removed = SimpleNamespace(id="a1")
    calls: dict = {}

    async def _remove(assignment_id, actor_id=None):
        calls["remove"] = (assignment_id, actor_id)
        return removed

    fake_assignment = SimpleNamespace(remove=_remove)
    handler = ReservationSyncHandler(
        reservation_service=None,
        participant_service=None,
        payment_proof_service=None,
        assignment_service=fake_assignment,
        service_log_service=None,
    )

    delete_op = SyncPushOperationSchema(
        operation_id="op-ad",
        entity_type="assignment",
        entity_local_id="l1",
        entity_remote_id="a1",
        operation_type="delete",
        idempotency_key="i-ad",
        payload={},
    )
    doc = asyncio.run(
        handler.handle(
            entity="assignment", op_type="delete", operation=delete_op, current_user=_admin_user()
        )
    )
    assert doc is removed
    assert calls["remove"][0] == "a1"


def test_sync_push_accepts_notification_mutation_operation_types() -> None:
    """Schema must accept mark_read / mark_all_read / clear_inbox from mobile outbox."""
    for op_type in ("mark_read", "mark_all_read", "delete", "clear_inbox"):
        op = SyncPushOperationSchema(
            operation_id=f"op-{op_type}",
            entity_type="notification_mutation",
            entity_local_id="notif-1" if op_type not in ("mark_all_read", "clear_inbox") else "__all__",
            operation_type=op_type,
            idempotency_key=f"idem-{op_type}",
            payload={"read_only": True} if op_type == "clear_inbox" else {},
        )
        assert op.operation_type == op_type


def test_notification_handler_mark_read_and_clear(monkeypatch) -> None:
    from datetime import UTC, datetime

    from app.services.sync_handlers.notification_handler import NotificationSyncHandler

    now = datetime.now(UTC)
    user = _admin_user()
    user.id = user.id  # already string-like SimpleNamespace

    class _FakeDoc:
        def __init__(self) -> None:
            self.id = "notif-1"
            self.user_id = user.id
            self.read = False
            self.read_at = None
            self.deleted_at = None
            self.version = 1
            self.updated_at = now
            self.title = "t"
            self.body = "b"
            self.event_type = "reservation_created"
            self.reservation_id = None
            self.contact_phone = None
            self.created_at = now

        async def save(self) -> None:
            return None

        def model_dump(self, mode: str = "json") -> dict:
            return {"id": self.id, "read": self.read, "deleted_at": self.deleted_at}

    doc = _FakeDoc()

    async def _get(_id: str):
        return doc if _id == "notif-1" else None

    class _FindResult:
        async def update_many(self, update: dict) -> SimpleNamespace:
            return SimpleNamespace(modified_count=2)

    def _find(_query: dict) -> _FindResult:
        return _FindResult()

    monkeypatch.setattr(
        "app.services.sync_handlers.notification_handler.InAppNotificationDocument.get",
        staticmethod(_get),
    )
    monkeypatch.setattr(
        "app.services.sync_handlers.notification_handler.InAppNotificationDocument.find",
        staticmethod(_find),
    )

    handler = NotificationSyncHandler()

    mark_op = SyncPushOperationSchema(
        operation_id="op-mr",
        entity_type="notification_mutation",
        entity_local_id="notif-1",
        operation_type="mark_read",
        idempotency_key="idem-mr",
        payload={},
    )
    marked = asyncio.run(
        handler.handle(
            entity="notification_mutation",
            op_type="mark_read",
            operation=mark_op,
            current_user=user,
        )
    )
    assert marked.read is True
    assert marked.read_at is not None

    clear_op = SyncPushOperationSchema(
        operation_id="op-cl",
        entity_type="notification_mutation",
        entity_local_id="__all__",
        operation_type="clear_inbox",
        idempotency_key="idem-cl",
        payload={"read_only": False},
    )
    cleared = asyncio.run(
        handler.handle(
            entity="notification_mutation",
            op_type="clear_inbox",
            operation=clear_op,
            current_user=user,
        )
    )
    assert cleared.model_dump()["cleared_count"] == 2
