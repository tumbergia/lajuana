from __future__ import annotations

from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId

from app.common.enums import (
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
    UserRole,
)
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents import ReservationDocument, UserDocument
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.documents.notification_template_document import NotificationTemplateDocument
from app.notifications.email_provider import EmailProvider
from app.notifications.in_app_provider import InAppNotificationProvider
from app.notifications.provider import NotificationProvider
from app.notifications.renderer import render_subject, render_template
from app.notifications.whatsapp_provider import WhatsAppNotificationProvider


class NotificationService:
    def __init__(self) -> None:
        self._providers: dict[NotificationChannel, NotificationProvider] = {
            NotificationChannel.EMAIL: EmailProvider(),
            NotificationChannel.IN_APP: InAppNotificationProvider(),
            NotificationChannel.WHATSAPP: WhatsAppNotificationProvider(),
        }

    def get_provider(self, channel: NotificationChannel) -> NotificationProvider:
        return self._providers[channel]

    async def enqueue(
        self,
        event_type: NotificationEventType,
        reservation_id: str,
        channel: NotificationChannel,
        recipient_type: str,
        recipient_identifier: str,
        variables: dict[str, str] | None = None,
        scheduled_for: datetime | None = None,
        dedup_suffix: str | None = None,
    ) -> NotificationOutboxDocument:
        dedup_key = f"{event_type.value}:{reservation_id}:{recipient_type}:{channel.value}"
        if dedup_suffix:
            dedup_key += f":{dedup_suffix}"

        existing = await NotificationOutboxDocument.find_one(
            {"deduplication_key": dedup_key, "status": {"$ne": NotificationStatus.CANCELLED}}
        )
        if existing is not None:
            return existing

        template = await NotificationTemplateDocument.find_one(
            {
                "template_key": f"{event_type.value}.{recipient_type}",
                "channel": channel.value,
                "is_active": True,
            }
        )

        rendered_body = None
        subject = None
        template_key = None
        if template is not None and variables:
            rendered_body = render_template(template.body, variables)
            subject = render_subject(template.subject, variables)
            template_key = template.template_key
        elif template is None:
            logger.warning(
                "[notif] Template not found | event=%s | recipient=%s | channel=%s",
                event_type.value,
                recipient_type,
                channel.value,
            )

        doc = NotificationOutboxDocument(
            reservation_id=PydanticObjectId(reservation_id),
            event_type=event_type.value,
            recipient_type=recipient_type,
            recipient_identifier=recipient_identifier,
            channel=channel,
            template_key=template_key,
            subject=subject,
            rendered_body=rendered_body,
            status=(
                NotificationStatus.SCHEDULED if scheduled_for else NotificationStatus.PENDING
            ),
            scheduled_for=(
                scheduled_for.replace(tzinfo=UTC)
                if scheduled_for and scheduled_for.tzinfo is None
                else scheduled_for
            ),
            deduplication_key=dedup_key,
        )
        await doc.insert()
        return doc

    async def enqueue_reservation_created(
        self, reservation: ReservationDocument
    ) -> list[NotificationOutboxDocument]:
        entries: list[NotificationOutboxDocument] = []

        if reservation.holder_email:
            vars = self._build_customer_vars(reservation)
            entry = await self.enqueue(
                event_type=NotificationEventType.RESERVATION_CREATED,
                reservation_id=str(reservation.id),
                channel=NotificationChannel.EMAIL,
                recipient_type="customer",
                recipient_identifier=reservation.holder_email,
                variables=vars,
            )
            entries.append(entry)

        return entries

    async def enqueue_payment_received(
        self, reservation: ReservationDocument
    ) -> list[NotificationOutboxDocument]:
        entries: list[NotificationOutboxDocument] = []

        internal_users = await UserDocument.find(
            UserDocument.is_active,
            UserDocument.role == UserRole.ADMIN,
        ).to_list()
        for user in internal_users:
            if user.email:
                entry = await self.enqueue(
                    event_type=NotificationEventType.RESERVATION_CONFIRMED,
                    reservation_id=str(reservation.id),
                    channel=NotificationChannel.EMAIL,
                    recipient_type="internal",
                    recipient_identifier=user.email,
                    variables=self._build_customer_vars(reservation),
                )
                entries.append(entry)

            in_app = await self.enqueue(
                event_type=NotificationEventType.RESERVATION_CONFIRMED,
                reservation_id=str(reservation.id),
                channel=NotificationChannel.IN_APP,
                recipient_type="internal",
                recipient_identifier=str(user.id),
                variables=self._build_customer_vars(reservation),
            )
            entries.append(in_app)

        return entries

    async def enqueue_reservation_confirmed(
        self, reservation: ReservationDocument
    ) -> list[NotificationOutboxDocument]:
        entries: list[NotificationOutboxDocument] = []

        if reservation.holder_email:
            vars = self._build_customer_vars(reservation)
            entry = await self.enqueue(
                event_type=NotificationEventType.RESERVATION_CONFIRMED,
                reservation_id=str(reservation.id),
                channel=NotificationChannel.EMAIL,
                recipient_type="customer",
                recipient_identifier=reservation.holder_email,
                variables=vars,
            )
            entries.append(entry)

        internal_users = await UserDocument.find(
            UserDocument.is_active,
            UserDocument.role == UserRole.ADMIN,
        ).to_list()
        for user in internal_users:
            if user.email:
                entry = await self.enqueue(
                    event_type=NotificationEventType.RESERVATION_CONFIRMED,
                    reservation_id=str(reservation.id),
                    channel=NotificationChannel.EMAIL,
                    recipient_type="internal",
                    recipient_identifier=user.email,
                    variables=vars,
                )
                entries.append(entry)

            in_app = await self.enqueue(
                event_type=NotificationEventType.RESERVATION_CONFIRMED,
                reservation_id=str(reservation.id),
                channel=NotificationChannel.IN_APP,
                recipient_type="internal",
                recipient_identifier=str(user.id),
                variables=vars,
            )
            entries.append(in_app)

        return entries

    async def enqueue_post_service(
        self, reservation: ReservationDocument
    ) -> list[NotificationOutboxDocument]:
        entries: list[NotificationOutboxDocument] = []

        if reservation.holder_email and reservation.completed_at:
            vars = self._build_customer_vars(reservation)
            scheduled = reservation.completed_at + timedelta(hours=2)
            entry = await self.enqueue(
                event_type=NotificationEventType.POST_SERVICE_COMPLETED,
                reservation_id=str(reservation.id),
                channel=NotificationChannel.EMAIL,
                recipient_type="customer",
                recipient_identifier=reservation.holder_email,
                variables=vars,
                scheduled_for=scheduled,
            )
            entries.append(entry)

        return entries

    async def enqueue_form_link(
        self, reservation: ReservationDocument, form_url: str
    ) -> list[NotificationOutboxDocument]:
        entries: list[NotificationOutboxDocument] = []

        if reservation.holder_email:
            vars = self._build_customer_vars(reservation)
            vars["form_url"] = form_url
            if reservation.participant_form_expires_at:
                vars["form_expires_at"] = reservation.participant_form_expires_at.isoformat()

            entry = await self.enqueue(
                event_type=NotificationEventType.PARTICIPANT_FORM_LINK_GENERATED,
                reservation_id=str(reservation.id),
                channel=NotificationChannel.EMAIL,
                recipient_type="customer",
                recipient_identifier=reservation.holder_email,
                variables=vars,
                dedup_suffix=reservation.participant_form_token_hash,
            )
            entries.append(entry)

        return entries

    async def send_from_outbox(self, entry: NotificationOutboxDocument) -> None:
        provider = self._providers.get(entry.channel)
        if provider is None:
            entry.status = NotificationStatus.FAILED
            entry.last_error = f"No provider for channel {entry.channel}"
            await entry.save()
            return

        entry.status = NotificationStatus.SENDING
        await entry.save()

        result = await provider.send(entry)

        if result.success:
            entry.status = NotificationStatus.SENT
            entry.sent_at = datetime.now(UTC)
            entry.provider_message_id = result.provider_message_id
        else:
            entry.attempt_count += 1
            if entry.attempt_count >= entry.max_attempts:
                entry.status = NotificationStatus.FAILED
            else:
                entry.status = NotificationStatus.PENDING
            entry.last_error = result.error_detail

        await entry.save()

    async def retry(self, outbox_id: str) -> NotificationOutboxDocument:
        doc = await NotificationOutboxDocument.get(outbox_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.NOTIFICATION_NOT_FOUND,
                message="Notificación no encontrada.",
            )
        if doc.status not in (NotificationStatus.FAILED, NotificationStatus.CANCELLED):
            raise ApiError(
                status_code=409,
                code=ErrorCode.NOTIFICATION_SEND_FAILED,
                message="Solo se pueden reintentar notificaciones fallidas o canceladas.",
                details={"status": doc.status.value},
            )
        doc.status = NotificationStatus.PENDING
        doc.attempt_count = 0
        doc.last_error = None
        await doc.save()
        return doc

    async def cancel(self, outbox_id: str) -> NotificationOutboxDocument:
        doc = await NotificationOutboxDocument.get(outbox_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.NOTIFICATION_NOT_FOUND,
                message="Notificación no encontrada.",
            )
        if doc.status in (NotificationStatus.SENT, NotificationStatus.CANCELLED):
            raise ApiError(
                status_code=409,
                code=ErrorCode.NOTIFICATION_SEND_FAILED,
                message="No se puede cancelar una notificación ya enviada o cancelada.",
                details={"status": doc.status.value},
            )
        doc.status = NotificationStatus.CANCELLED
        await doc.save()
        return doc

    def _build_customer_vars(self, reservation: ReservationDocument) -> dict[str, str]:
        return {
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "participants_count": str(reservation.participant_count),
        }

    async def process_pending_batch(self, batch_size: int = 10) -> int:
        now = datetime.now(UTC)
        entries = await NotificationOutboxDocument.find(
            {
                "$or": [
                    {"status": NotificationStatus.PENDING.value},
                    {
                        "status": NotificationStatus.SCHEDULED.value,
                        "scheduled_for": {"$lte": now},
                    },
                ]
            }
        ).sort("created_at").limit(batch_size).to_list()

        count = 0
        for entry in entries:
            await self.send_from_outbox(entry)
            count += 1
        return count
