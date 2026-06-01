"""Simple DI container — one registry, no magic.

Usage::

    # On startup (lifespan.py):
    container = Container.init()

    # In endpoints:
    @router.get(...)
    async def handler(svc: ReservationService = Depends(get_reservation_service)):
        ...
"""

from __future__ import annotations

from typing import Any


class Container:
    """Holds one instance of each service. Lazy-init by default."""

    _instance: Container | None = None

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._init_services()

    def _init_services(self) -> None:
        """Register all services with their dependencies."""
        # ── Leaf services (no deps on other app services) ──
        from app.services.config_service import ConfigService
        from app.services.equine_service import EquineService
        from app.services.experience_service import ExperienceService
        from app.services.ops_service import OpsService
        from app.services.participant_form_link_service import ParticipantFormLinkService
        from app.services.participant_service import ParticipantService
        from app.services.policy_service import PolicyService
        from app.services.provider_service import ProviderService
        from app.services.saddle_service import SaddleService
        from app.services.schedule_service import ScheduleService
        from app.services.service_log_service import ServiceLogService
        from app.services.storage import LocalStorageAdapter, get_storage_adapter
        from app.services.sync_service import SyncService
        from app.services.user_service import UserService

        self._services["config_service"] = ConfigService()
        self._services["equine_service"] = EquineService()
        self._services["experience_service"] = ExperienceService()
        self._services["ops_service"] = OpsService()
        self._services["participant_form_link_service"] = ParticipantFormLinkService()
        self._services["participant_service"] = ParticipantService()
        self._services["policy_service"] = PolicyService()
        self._services["provider_service"] = ProviderService()
        self._services["saddle_service"] = SaddleService()
        self._services["schedule_service"] = ScheduleService()
        self._services["service_log_service"] = ServiceLogService()
        self._services["sync_service"] = SyncService()
        self._services["user_service"] = UserService()
        self._services["storage_adapter"] = get_storage_adapter()

        # ── Services with dependencies ──
        from app.services.notification_service import NotificationService
        from app.services.auth_service import AuthService

        config_svc = self._services["config_service"]
        self._services["notification_service"] = NotificationService()
        self._services["auth_service"] = AuthService()

        # ── Services that depend on NotificationService ──
        from app.services.reservation_service import ReservationService
        from app.services.booking_service import BookingService
        from app.services.reservation_draft_service import ReservationDraftService

        notif_svc = self._services["notification_service"]
        form_svc = self._services["participant_form_link_service"]
        self._services["reservation_service"] = ReservationService(
            notification_service=notif_svc,
            form_link_service=form_svc,
            config_service=config_svc,
        )
        self._services["booking_service"] = BookingService()
        self._services["reservation_draft_service"] = ReservationDraftService()

        # ── Payment proof depends on storage + notification ──
        from app.services.payment_proof_service import PaymentProofService

        self._services["payment_proof_service"] = PaymentProofService()

        # ── WhatsApp / file ──
        from app.services.file_upload_service import FileUploadService

        self._services["file_upload_service"] = FileUploadService()

    # ------------------------------------------------------------------
    # Public accessors — one per service for type safety + IDE support
    # ------------------------------------------------------------------

    @property
    def reservation_service(self) -> Any:
        return self._services["reservation_service"]

    @property
    def notification_service(self) -> Any:
        return self._services["notification_service"]

    @property
    def booking_service(self) -> Any:
        return self._services["booking_service"]

    @property
    def payment_proof_service(self) -> Any:
        return self._services["payment_proof_service"]

    @property
    def config_service(self) -> Any:
        return self._services["config_service"]

    @property
    def auth_service(self) -> Any:
        return self._services["auth_service"]

    @property
    def user_service(self) -> Any:
        return self._services["user_service"]

    @property
    def experience_service(self) -> Any:
        return self._services["experience_service"]

    @property
    def equine_service(self) -> Any:
        return self._services["equine_service"]

    @property
    def saddle_service(self) -> Any:
        return self._services["saddle_service"]

    @property
    def schedule_service(self) -> Any:
        return self._services["schedule_service"]

    @property
    def participant_service(self) -> Any:
        return self._services["participant_service"]

    @property
    def file_upload_service(self) -> Any:
        return self._services["file_upload_service"]

    @property
    def sync_service(self) -> Any:
        return self._services["sync_service"]

    @property
    def policy_service(self) -> Any:
        return self._services["policy_service"]

    @property
    def provider_service(self) -> Any:
        return self._services["provider_service"]

    @property
    def reservation_draft_service(self) -> Any:
        return self._services["reservation_draft_service"]

    # ------------------------------------------------------------------
    # Class-level lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def init(cls) -> Container:
        cls._instance = cls()
        return cls._instance

    @classmethod
    def get_instance(cls) -> Container:
        if cls._instance is None:
            raise RuntimeError("DI container not initialized. Call Container.init() first.")
        return cls._instance
