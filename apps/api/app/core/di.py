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
        from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
        from app.conversations.services.conversation_lock_service import (
            ConversationLockService,
        )
        from app.conversations.services.conversation_resolver import (
            ConversationResolver,
        )
        from app.conversations.services.message_buffer_service import (
            MessageBufferService,
        )
        from app.services.config_service import ConfigService
        from app.services.equine_event_service import EquineEventService
        from app.services.equine_service import EquineService
        from app.services.experience_service import ExperienceService
        from app.services.participant_form_link_service import ParticipantFormLinkService
        from app.services.policy_service import PolicyService
        from app.services.provider_service import ProviderService
        from app.services.saddle_service import SaddleService
        from app.services.schedule_service import ScheduleService
        from app.services.service_log_service import ServiceLogService
        from app.services.storage import get_storage_adapter
        from app.services.user_service import UserService
        self._services["config_service"] = ConfigService()
        self._services["conversation_lock_service"] = ConversationLockService()
        self._services["conversation_resolver"] = ConversationResolver()
        self._services["equine_service"] = EquineService()
        self._services["equine_event_service"] = EquineEventService()
        self._services["experience_service"] = ExperienceService()
        self._services["message_buffer_service"] = MessageBufferService()
        self._services["service_log_service"] = ServiceLogService()
        self._services["participant_form_link_service"] = ParticipantFormLinkService()
        self._services["policy_service"] = PolicyService()
        self._services["provider_service"] = ProviderService()
        self._services["saddle_service"] = SaddleService()

        from app.services.assignment_service import AssignmentService

        self._services["assignment_service"] = AssignmentService(
            equine_service=self._services["equine_service"],
            saddle_service=self._services["saddle_service"],
            config_service=self._services["config_service"],
        )
        self._services["schedule_service"] = ScheduleService()
        self._services["storage_adapter"] = get_storage_adapter()
        self._services["user_service"] = UserService()
        self._services["whatsapp_outbound_service"] = WhatsAppOutboundService()

        # ── Services with dependencies ──
        from app.services.auth_service import AuthService
        from app.services.notification_service import NotificationService
        from app.services.participant_service import ParticipantService

        config_svc = self._services["config_service"]
        form_svc = self._services["participant_form_link_service"]
        self._services["participant_service"] = ParticipantService(
            form_link_service=form_svc,
        )
        self._services["notification_service"] = NotificationService(
            outbound_service=self._services["whatsapp_outbound_service"],
        )
        self._services["auth_service"] = AuthService()

        # ── Services that depend on NotificationService ──
        from app.services.booking_service import BookingService
        from app.services.reservation_draft_service import ReservationDraftService
        from app.services.reservation_service import ReservationService

        notif_svc = self._services["notification_service"]
        self._services["reservation_service"] = ReservationService(
            notification_service=notif_svc,
            form_link_service=form_svc,
            config_service=config_svc,
        )
        self._services["booking_service"] = BookingService(
            reservation_service=self._services["reservation_service"],
        )
        self._services["reservation_draft_service"] = ReservationDraftService(
            reservation_service=self._services["reservation_service"],
            config_service=config_svc,
        )

        # ── Payment proof depends on storage + notification ──
        from app.services.payment_proof_service import PaymentProofService

        self._services["payment_proof_service"] = PaymentProofService()

        # ── WhatsApp / file ──
        from app.services.file_upload_service import FileUploadService
        from app.services.sync_service import SyncService

        self._services["file_upload_service"] = FileUploadService()

        # ── SyncService (depends on many services) ──
        self._services["sync_service"] = SyncService(
            config_service=config_svc,
            experience_service=self._services["experience_service"],
            schedule_service=self._services["schedule_service"],
            equine_service=self._services["equine_service"],
            reservation_service=self._services["reservation_service"],
            participant_service=self._services["participant_service"],
            payment_proof_service=self._services["payment_proof_service"],
            assignment_service=self._services["assignment_service"],
            service_log_service=self._services["service_log_service"],
            provider_service=self._services["provider_service"],
            policy_service=self._services["policy_service"],
            saddle_service=self._services["saddle_service"],
        )

        # ── WhatsApp ingestion (depends on resolver + buffer) ──
        from app.channels.whatsapp.ingestion_service import WhatsAppIngestionService

        self._services["whatsapp_ingestion_service"] = WhatsAppIngestionService(
            resolver=self._services["conversation_resolver"],
            buffer_service=self._services["message_buffer_service"],
        )

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
    def equine_event_service(self) -> Any:
        return self._services["equine_event_service"]

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

    @property
    def assignment_service(self) -> Any:
        return self._services["assignment_service"]

    @property
    def service_log_service(self) -> Any:
        return self._services["service_log_service"]

    @property
    def participant_form_link_service(self) -> Any:
        return self._services["participant_form_link_service"]

    @property
    def whatsapp_ingestion_service(self) -> Any:
        return self._services["whatsapp_ingestion_service"]

    @property
    def whatsapp_outbound_service(self) -> Any:
        return self._services["whatsapp_outbound_service"]

    @property
    def conversation_lock_service(self) -> Any:
        return self._services["conversation_lock_service"]

    @property
    def conversation_resolver(self) -> Any:
        return self._services["conversation_resolver"]

    @property
    def message_buffer_service(self) -> Any:
        return self._services["message_buffer_service"]

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
