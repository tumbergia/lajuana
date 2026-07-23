"""Tests for RoleRequestService."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.common.enums import RoleRequestStatus, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.schemas.role_request import RoleRequestCreateSchema, RoleRequestDecisionSchema
from app.services.role_request_service import RoleRequestService


def _fake_user(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000001",
        email="user@example.com",
        full_name="Sin Rol",
        role=UserRole.UNASSIGNED,
        is_active=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _fake_request(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="670000000000000000000001",
        user_id="660000000000000000000001",
        requested_role=UserRole.GUIDE,
        status=RoleRequestStatus.PENDING,
        decided_role=None,
        decided_by=None,
        decided_at=None,
        note=None,
        version=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )
    base.update(overrides)

    async def _save() -> None:
        return None

    ns = SimpleNamespace(**base)
    ns.save = _save
    return ns


class TestCreateSelfRequest:
    def test_create_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        inserted: list[object] = []

        class FakeRoleRequestDocument:
            def __init__(self, **kwargs: object) -> None:
                for k, v in kwargs.items():
                    setattr(self, k, v)
                self.id = "670000000000000000000001"
                self.version = 1
                self.created_at = datetime.now(UTC)
                self.updated_at = datetime.now(UTC)
                self.deleted_at = None
                self.decided_role = None
                self.decided_by = None
                self.decided_at = None
                self.note = None

            async def insert(self) -> None:
                inserted.append(self)

            @staticmethod
            async def find_one(query: dict) -> None:
                return None

        notified: list[dict] = []

        class FakeNotificationService:
            async def enqueue_admin_in_app(self, **kwargs: object) -> list:
                notified.append(kwargs)
                return []

        monkeypatch.setattr(
            "app.services.role_request_service.RoleRequestDocument",
            FakeRoleRequestDocument,
        )

        service = RoleRequestService(notification_service=FakeNotificationService())
        actor = _fake_user()

        async def run() -> None:
            result = await service.create_self_request(
                actor,
                RoleRequestCreateSchema(requested_role=UserRole.GUIDE),
            )
            assert result.requested_role == UserRole.GUIDE
            assert len(inserted) == 1
            assert len(notified) == 1

        asyncio.run(run())

    def test_create_rejects_non_unassigned(self) -> None:
        service = RoleRequestService()
        actor = _fake_user(role=UserRole.GUIDE)

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.create_self_request(
                    actor,
                    RoleRequestCreateSchema(requested_role=UserRole.GUIDE),
                )
            assert exc.value.code == ErrorCode.ROLE_REQUEST_NOT_ALLOWED

        asyncio.run(run())

    def test_create_rejects_unassigned_role(self) -> None:
        service = RoleRequestService()
        actor = _fake_user()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.create_self_request(
                    actor,
                    RoleRequestCreateSchema(requested_role=UserRole.UNASSIGNED),
                )
            assert exc.value.code == ErrorCode.ROLE_REQUEST_INVALID_ROLE

        asyncio.run(run())

    def test_create_rejects_duplicate_pending(self, monkeypatch: pytest.MonkeyPatch) -> None:
        existing = _fake_request()

        async def _find_one(query: dict) -> SimpleNamespace:
            return existing

        monkeypatch.setattr(
            "app.services.role_request_service.RoleRequestDocument.find_one",
            _find_one,
        )
        service = RoleRequestService()
        actor = _fake_user()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.create_self_request(
                    actor,
                    RoleRequestCreateSchema(requested_role=UserRole.ADMIN),
                )
            assert exc.value.code == ErrorCode.ROLE_REQUEST_ALREADY_PENDING

        asyncio.run(run())


class TestDecide:
    def test_approve_with_requested_role(self, monkeypatch: pytest.MonkeyPatch) -> None:
        doc = _fake_request()
        requester = _fake_user()
        admin = _fake_user(
            id="660000000000000000000099",
            role=UserRole.ADMIN,
            email="admin@example.com",
            full_name="Admin",
        )
        updated: list[tuple] = []
        notified: list[dict] = []

        class FakeUserService:
            async def update_user(self, user_id: str, payload: object) -> SimpleNamespace:
                updated.append((user_id, payload))
                return requester

        class FakeNotificationService:
            async def enqueue(self, **kwargs: object) -> SimpleNamespace:
                notified.append(kwargs)
                return SimpleNamespace(status="pending", id="outbox1")

            async def send_from_outbox(self, entry: object) -> None:
                return None

        async def _get(request_id: str) -> SimpleNamespace:
            return doc

        async def _get_user(user_id: object) -> SimpleNamespace:
            return requester

        monkeypatch.setattr(
            "app.services.role_request_service.RoleRequestDocument.get",
            _get,
        )
        monkeypatch.setattr(
            "app.services.role_request_service.UserDocument.get",
            _get_user,
        )

        service = RoleRequestService(
            user_service=FakeUserService(),
            notification_service=FakeNotificationService(),
        )

        async def run() -> None:
            result = await service.decide(
                str(doc.id),
                admin,
                RoleRequestDecisionSchema(action="approve"),
            )
            assert result.status == RoleRequestStatus.APPROVED
            assert result.decided_role == UserRole.GUIDE
            assert len(updated) == 1
            assert updated[0][1].role == UserRole.GUIDE
            assert len(notified) == 1

        asyncio.run(run())

    def test_approve_with_different_role(self, monkeypatch: pytest.MonkeyPatch) -> None:
        doc = _fake_request(requested_role=UserRole.GUIDE)
        requester = _fake_user()
        admin = _fake_user(id="660000000000000000000099", role=UserRole.ADMIN)
        updated: list[object] = []

        class FakeUserService:
            async def update_user(self, user_id: str, payload: object) -> SimpleNamespace:
                updated.append(payload)
                return requester

        class FakeNotificationService:
            async def enqueue(self, **kwargs: object) -> SimpleNamespace:
                return SimpleNamespace(status="sent", id="outbox1")

            async def send_from_outbox(self, entry: object) -> None:
                return None

        async def _get(request_id: str) -> SimpleNamespace:
            return doc

        async def _get_user(user_id: object) -> SimpleNamespace:
            return requester

        monkeypatch.setattr(
            "app.services.role_request_service.RoleRequestDocument.get",
            _get,
        )
        monkeypatch.setattr(
            "app.services.role_request_service.UserDocument.get",
            _get_user,
        )

        service = RoleRequestService(
            user_service=FakeUserService(),
            notification_service=FakeNotificationService(),
        )

        async def run() -> None:
            result = await service.decide(
                str(doc.id),
                admin,
                RoleRequestDecisionSchema(action="approve", assigned_role=UserRole.ADMIN),
            )
            assert result.status == RoleRequestStatus.APPROVED
            assert result.decided_role == UserRole.ADMIN
            assert updated[0].role == UserRole.ADMIN

        asyncio.run(run())

    def test_reject(self, monkeypatch: pytest.MonkeyPatch) -> None:
        doc = _fake_request()
        requester = _fake_user()
        admin = _fake_user(id="660000000000000000000099", role=UserRole.ADMIN)

        class FakeUserService:
            async def update_user(self, user_id: str, payload: object) -> SimpleNamespace:
                raise AssertionError("reject should not update user role")

        class FakeNotificationService:
            async def enqueue(self, **kwargs: object) -> SimpleNamespace:
                return SimpleNamespace(status="sent", id="outbox1")

            async def send_from_outbox(self, entry: object) -> None:
                return None

        async def _get(request_id: str) -> SimpleNamespace:
            return doc

        async def _get_user(user_id: object) -> SimpleNamespace:
            return requester

        monkeypatch.setattr(
            "app.services.role_request_service.RoleRequestDocument.get",
            _get,
        )
        monkeypatch.setattr(
            "app.services.role_request_service.UserDocument.get",
            _get_user,
        )

        service = RoleRequestService(
            user_service=FakeUserService(),
            notification_service=FakeNotificationService(),
        )

        async def run() -> None:
            result = await service.decide(
                str(doc.id),
                admin,
                RoleRequestDecisionSchema(action="reject", note="No aplica"),
            )
            assert result.status == RoleRequestStatus.REJECTED
            assert result.decided_role is None
            assert result.note == "No aplica"

        asyncio.run(run())

    def test_decide_not_pending(self, monkeypatch: pytest.MonkeyPatch) -> None:
        doc = _fake_request(status=RoleRequestStatus.APPROVED)
        admin = _fake_user(id="660000000000000000000099", role=UserRole.ADMIN)

        async def _get(request_id: str) -> SimpleNamespace:
            return doc

        monkeypatch.setattr(
            "app.services.role_request_service.RoleRequestDocument.get",
            _get,
        )

        service = RoleRequestService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.decide(
                    str(doc.id),
                    admin,
                    RoleRequestDecisionSchema(action="approve"),
                )
            assert exc.value.code == ErrorCode.ROLE_REQUEST_NOT_PENDING

        asyncio.run(run())
