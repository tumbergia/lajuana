from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId

from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.common.enums import (
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
    UserRole,
)
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents import (
    ReservationDocument,
    UserDocument,
)
from app.documents.audit_metadata_models import NotificationMetadata
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.documents.notification_template_document import NotificationTemplateDocument
from app.documents.reservation_audit_log_document import ReservationAuditLogDocument
from app.notifications.email_provider import EmailProvider
from app.notifications.in_app_provider import InAppNotificationProvider
from app.notifications.provider import NotificationProvider
from app.notifications.renderer import render_subject, render_template
from app.notifications.whatsapp_provider import WhatsAppNotificationProvider
from app.services.config_service import ConfigService


class NotificationService:
    def __init__(
        self,
        outbound_service: WhatsAppOutboundService | None = None,
        config_service: ConfigService | None = None,
    ) -> None:
        outbound = outbound_service or WhatsAppOutboundService()
        self._providers: dict[NotificationChannel, NotificationProvider] = {
            NotificationChannel.EMAIL: EmailProvider(),
            NotificationChannel.IN_APP: InAppNotificationProvider(),
            NotificationChannel.WHATSAPP: WhatsAppNotificationProvider(outbound_service=outbound),
        }
        self._config_service = config_service or ConfigService()

    async def business_location_vars(self) -> dict[str, str]:
        location = await self._config_service.get_business_location()
        return {
            "location_name": location.name,
            "location_address": location.address,
            "location_municipality": location.municipality,
            "location_directions": location.directions,
            "location_url": location.google_maps_url,
        }

    def get_provider(self, channel: NotificationChannel) -> NotificationProvider:
        return self._providers[channel]

    async def enqueue(
        self,
        event_type: NotificationEventType,
        reservation_id: str | None,
        channel: NotificationChannel,
        recipient_type: str,
        recipient_identifier: str,
        variables: dict[str, str] | None = None,
        scheduled_for: datetime | None = None,
        dedup_suffix: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        skip_template: bool = False,
        contact_phone: str | None = None,
        language: str = "es",
    ) -> NotificationOutboxDocument:
        reservation_key = reservation_id or "none"
        # La dedup_key incluye el idioma y recipient_identifier para evitar colisiones entre múltiples idiomas o destinatarios.
        dedup_key = f"{event_type.value}:{reservation_key}:{recipient_type}:{recipient_identifier}:{channel.value}:{language}"
        if dedup_suffix:
            dedup_key += f":{dedup_suffix}"

        existing = await NotificationOutboxDocument.find_one(
            {"deduplication_key": dedup_key, "status": {"$ne": NotificationStatus.CANCELLED}}
        )
        if existing is not None:
            return existing

        rendered_body = body
        rendered_subject = subject
        template_key = None

        if not skip_template:
            template = await NotificationTemplateDocument.find_one(
                {
                    "template_key": f"{event_type.value}.{recipient_type}",
                    "channel": channel.value,
                    "language": language,
                    "is_active": True,
                }
            )
            # Fallback a español si no hay versión en el idioma del cliente.
            if template is None and language != "es":
                template = await NotificationTemplateDocument.find_one(
                    {
                        "template_key": f"{event_type.value}.{recipient_type}",
                        "channel": channel.value,
                        "language": "es",
                        "is_active": True,
                    }
                )

            if template is not None and variables:
                rendered_body = render_template(template.body, variables)
                rendered_subject = render_subject(template.subject, variables)
                template_key = template.template_key
            elif template is None and body is None:
                logger.warning(
                    "[notif] Template not found | event=%s | recipient=%s | channel=%s",
                    event_type.value,
                    recipient_type,
                    channel.value,
                )

        doc = NotificationOutboxDocument(
            reservation_id=PydanticObjectId(reservation_id) if reservation_id else None,
            event_type=event_type.value,
            recipient_type=recipient_type,
            recipient_identifier=recipient_identifier,
            channel=channel,
            template_key=template_key,
            subject=rendered_subject,
            rendered_body=rendered_body,
            contact_phone=contact_phone,
            status=(NotificationStatus.SCHEDULED if scheduled_for else NotificationStatus.PENDING),
            scheduled_for=(
                scheduled_for.replace(tzinfo=UTC)
                if scheduled_for and scheduled_for.tzinfo is None
                else scheduled_for
            ),
            deduplication_key=dedup_key,
        )
        await doc.insert()
        return doc

    async def enqueue_admin_in_app(
        self,
        event_type: NotificationEventType,
        title: str,
        body: str,
        reservation_id: str | None = None,
        actor_user_id: str | None = None,
        dedup_suffix: str | None = None,
        contact_phone: str | None = None,
    ) -> list[NotificationOutboxDocument]:
        """Fan-out an in-app notification to active admins, excluding actor and respecting prefs."""
        admins = await UserDocument.find(
            {"is_active": True, "role": UserRole.ADMIN},
        ).to_list()

        tasks = []
        for user in admins:
            if actor_user_id and str(user.id) == actor_user_id:
                continue
            if not user.prefers_notification(event_type.value):
                continue
            tasks.append(
                self.enqueue(
                    event_type=event_type,
                    reservation_id=reservation_id,
                    channel=NotificationChannel.IN_APP,
                    recipient_type="internal",
                    recipient_identifier=str(user.id),
                    subject=title,
                    body=body,
                    skip_template=True,
                    dedup_suffix=f"{str(user.id)}:{dedup_suffix}" if dedup_suffix else str(user.id),
                    contact_phone=contact_phone,
                )
            )

        if not tasks:
            return []
        entries = list(await asyncio.gather(*tasks))
        # Deliver in-app immediately so the inbox updates without waiting for the outbox poll.
        for entry in entries:
            if getattr(entry, "status", None) == NotificationStatus.PENDING:
                try:
                    await self.send_from_outbox(entry)
                except Exception:
                    logger.exception(
                        "[notif] Immediate in-app delivery failed | outbox=%s",
                        getattr(entry, "id", None),
                    )
        return entries

    async def enqueue_reservation_created(
        self, reservation: ReservationDocument, actor_user_id: str | None = None
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

        holder = reservation.holder_name or "Cliente"
        code = reservation.code or str(reservation.id)
        admin_entries = await self.enqueue_admin_in_app(
            event_type=NotificationEventType.RESERVATION_CREATED,
            title="Nueva reserva",
            body=f"{holder} — {code} ({reservation.participant_count} participantes)",
            reservation_id=str(reservation.id),
            actor_user_id=actor_user_id,
            dedup_suffix="created",
            contact_phone=reservation.holder_phone,
        )
        entries.extend(admin_entries)
        return entries

    async def enqueue_payment_received(
        self, reservation: ReservationDocument
    ) -> list[NotificationOutboxDocument]:
        internal_users = await UserDocument.find(
            {"is_active": True, "role": UserRole.ADMIN},
        ).to_list()

        vars = self._build_customer_vars(reservation)
        tasks = []
        for user in internal_users:
            if user.email:
                tasks.append(
                    self.enqueue(
                        event_type=NotificationEventType.RESERVATION_CONFIRMED,
                        reservation_id=str(reservation.id),
                        channel=NotificationChannel.EMAIL,
                        recipient_type="internal",
                        recipient_identifier=user.email,
                        variables=vars,
                    )
                )
            tasks.append(
                self.enqueue(
                    event_type=NotificationEventType.RESERVATION_CONFIRMED,
                    reservation_id=str(reservation.id),
                    channel=NotificationChannel.IN_APP,
                    recipient_type="internal",
                    recipient_identifier=str(user.id),
                    variables=vars,
                )
            )

        return list(await asyncio.gather(*tasks))

    async def enqueue_reservation_confirmed(
        self, reservation: ReservationDocument
    ) -> list[NotificationOutboxDocument]:
        vars = self._build_customer_vars(reservation)
        tasks: list[NotificationOutboxDocument] = []
        # El email al customer SIEMPRE va en español (cliente-facing formal).
        # Los templates bilingües se aplican a WhatsApp (donde el cliente ya
        # interactuó en otro idioma).
        customer_lang = "es"

        if reservation.holder_email:
            tasks.append(
                self.enqueue(
                    event_type=NotificationEventType.RESERVATION_CONFIRMED,
                    reservation_id=str(reservation.id),
                    channel=NotificationChannel.EMAIL,
                    recipient_type="customer",
                    recipient_identifier=reservation.holder_email,
                    variables=vars,
                    language=customer_lang,
                )
            )

        internal_users = await UserDocument.find(
            {"is_active": True, "role": UserRole.ADMIN},
        ).to_list()
        for user in internal_users:
            if user.email:
                tasks.append(
                    self.enqueue(
                        event_type=NotificationEventType.RESERVATION_CONFIRMED,
                        reservation_id=str(reservation.id),
                        channel=NotificationChannel.EMAIL,
                        recipient_type="internal",
                        recipient_identifier=user.email,
                        variables=vars,
                    )
                )
            tasks.append(
                self.enqueue(
                    event_type=NotificationEventType.RESERVATION_CONFIRMED,
                    reservation_id=str(reservation.id),
                    channel=NotificationChannel.IN_APP,
                    recipient_type="internal",
                    recipient_identifier=str(user.id),
                    variables=vars,
                )
            )

        return list(await asyncio.gather(*tasks))

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

    async def send_from_outbox(self, entry: NotificationOutboxDocument) -> None:
        provider = self._providers.get(entry.channel)
        if provider is None:
            entry.status = NotificationStatus.FAILED
            entry.last_error = f"No provider for channel {entry.channel}"
            await entry.save()
            return

        entry.status = NotificationStatus.SENDING
        await entry.save()

        try:
            result = await provider.send(entry)
        except Exception as exc:
            logger.exception(
                "[notif] Provider send crashed | outbox=%s | channel=%s",
                getattr(entry, "id", None),
                entry.channel.value,
            )
            await self._record_send_failure(entry, str(exc) or exc.__class__.__name__)
            return

        if result.success:
            entry.status = NotificationStatus.SENT
            entry.sent_at = datetime.now(UTC)
            entry.provider_message_id = result.provider_message_id
            await entry.save()
            await self._update_reservation_audit_fields(entry)
            return

        await self._record_send_failure(entry, result.error_detail)

    async def _record_send_failure(
        self,
        entry: NotificationOutboxDocument,
        error_detail: str | None,
    ) -> None:
        entry.attempt_count += 1
        entry.last_error = error_detail
        if entry.attempt_count >= entry.max_attempts:
            entry.status = NotificationStatus.FAILED
            await entry.save()
            if entry.channel == NotificationChannel.WHATSAPP:
                await self._notify_whatsapp_delivery_failed(entry)
            return

        entry.status = NotificationStatus.PENDING
        await entry.save()

    async def _notify_whatsapp_delivery_failed(self, entry: NotificationOutboxDocument) -> None:
        preview = (entry.subject or entry.event_type or "mensaje").strip()
        phone = entry.recipient_identifier or "desconocido"
        await self.enqueue_admin_in_app(
            event_type=NotificationEventType.WHATSAPP_DELIVERY_FAILED,
            title="Fallo envío WhatsApp",
            body=f"No se pudo enviar a {phone}: {preview}. {entry.last_error or ''}".strip(),
            reservation_id=str(entry.reservation_id) if entry.reservation_id else None,
            dedup_suffix=str(entry.id),
            contact_phone=phone if phone != "desconocido" else None,
        )

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

    async def enqueue_reservation_confirmed_logistics(
        self,
        reservation: ReservationDocument,
        experience_name: str,
        scheduled_date: str,
        start_time: str | None = None,
        language: str | None = None,
    ) -> NotificationOutboxDocument | None:
        if not reservation.holder_phone:
            return None
        lang = language or reservation.holder_language or "es"
        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "experience_name": experience_name,
            "scheduled_date": scheduled_date,
            **await self.business_location_vars(),
        }
        return await self.enqueue(
            event_type=NotificationEventType.RESERVATION_CONFIRMED_LOGISTICS_SENT,
            reservation_id=str(reservation.id),
            channel=NotificationChannel.WHATSAPP,
            recipient_type="customer",
            recipient_identifier=reservation.holder_phone,
            variables=vars,
            language=lang,
        )

    async def enqueue_payment_approved_form(
        self,
        reservation: ReservationDocument,
        experience_name: str,
        language: str | None = None,
    ) -> NotificationOutboxDocument | None:
        if not reservation.holder_phone:
            return None
        lang = language or reservation.holder_language or "es"
        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            "experience_name": experience_name,
            "form_url": reservation.form_url or "",
        }
        return await self.enqueue(
            event_type=NotificationEventType.PAYMENT_APPROVED_FORM_SENT,
            reservation_id=str(reservation.id),
            channel=NotificationChannel.WHATSAPP,
            recipient_type="customer",
            recipient_identifier=reservation.holder_phone,
            variables=vars,
            language=lang,
        )

    async def enqueue_payment_approved_location(
        self,
        reservation: ReservationDocument,
        language: str | None = None,
    ) -> NotificationOutboxDocument | None:
        if not reservation.holder_phone:
            return None
        lang = language or reservation.holder_language or "es"
        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            **await self.business_location_vars(),
        }
        return await self.enqueue(
            event_type=NotificationEventType.PAYMENT_APPROVED_LOCATION_SENT,
            reservation_id=str(reservation.id),
            channel=NotificationChannel.WHATSAPP,
            recipient_type="customer",
            recipient_identifier=reservation.holder_phone,
            variables=vars,
            language=lang,
        )

    async def enqueue_payment_rejected(
        self,
        reservation: ReservationDocument,
        experience_name: str,
        rejection_reason: str,
        language: str | None = None,
    ) -> NotificationOutboxDocument | None:
        if not reservation.holder_phone:
            return None
        lang = language or reservation.holder_language or "es"
        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            "experience_name": experience_name,
            "rejection_reason": rejection_reason,
        }
        return await self.enqueue(
            event_type=NotificationEventType.PAYMENT_REJECTED_SENT,
            reservation_id=str(reservation.id),
            channel=NotificationChannel.WHATSAPP,
            recipient_type="customer",
            recipient_identifier=reservation.holder_phone,
            variables=vars,
            language=lang,
        )

    async def enqueue_participant_form_resent(
        self,
        reservation: ReservationDocument,
        experience_name: str,
        language: str | None = None,
    ) -> NotificationOutboxDocument | None:
        if not reservation.holder_phone:
            return None
        lang = language or reservation.holder_language or "es"
        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            "experience_name": experience_name,
            "form_url": reservation.form_url or "",
        }
        return await self.enqueue(
            event_type=NotificationEventType.PARTICIPANT_FORM_RESENT,
            reservation_id=str(reservation.id),
            channel=NotificationChannel.WHATSAPP,
            recipient_type="customer",
            recipient_identifier=reservation.holder_phone,
            variables=vars,
            language=lang,
        )

    async def enqueue_reservation_cancelled(
        self,
        reservation: ReservationDocument,
        experience_name: str,
        language: str | None = None,
    ) -> NotificationOutboxDocument | None:
        if not reservation.holder_phone:
            return None
        lang = language or reservation.holder_language or "es"
        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "experience_name": experience_name,
        }
        return await self.enqueue(
            event_type=NotificationEventType.RESERVATION_CANCELLED,
            reservation_id=str(reservation.id),
            channel=NotificationChannel.WHATSAPP,
            recipient_type="customer",
            recipient_identifier=reservation.holder_phone,
            variables=vars,
            language=lang,
        )

    def _build_customer_vars(self, reservation: ReservationDocument) -> dict[str, str]:
        return {
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "participants_count": str(reservation.participant_count),
        }

    async def _update_reservation_audit_fields(self, entry: NotificationOutboxDocument) -> None:
        """Update reservation audit fields after a WhatsApp notification is sent."""
        event_map = {
            NotificationEventType.RESERVATION_CONFIRMED_LOGISTICS_SENT.value: {
                "fields": {
                    "confirmation_message_sent_at": datetime.now(UTC),
                },
                "audit_action": "notification.reservation_confirmed_logistics_sent",
            },
            NotificationEventType.PAYMENT_APPROVED_FORM_SENT.value: {
                "fields": {
                    "participant_form_sent_at": datetime.now(UTC),
                    "participant_form_send_count": None,  # +1 logic below
                },
                "audit_action": "notification.payment_approved_form_sent",
            },
            NotificationEventType.PAYMENT_APPROVED_LOCATION_SENT.value: {
                "fields": {},
                "audit_action": "notification.payment_approved_location_sent",
            },
            NotificationEventType.PARTICIPANT_FORM_RESENT.value: {
                "fields": {
                    "participant_form_sent_at": datetime.now(UTC),
                    "participant_form_send_count": None,
                },
                "audit_action": "notification.participant_form_resent",
            },
        }

        cfg = event_map.get(entry.event_type)
        if cfg is None or entry.reservation_id is None:
            return

        collection = ReservationDocument.get_motor_collection()
        set_fields: dict[str, object] = dict(cfg["fields"])
        if entry.provider_message_id:
            set_fields["participant_form_last_message_id"] = entry.provider_message_id

        # Increment send count: $inc for those events, $set for timestamp
        inc_fields: dict[str, int] = {}
        if cfg["fields"].get("participant_form_send_count") is None:
            inc_fields["participant_form_send_count"] = 1
            del set_fields["participant_form_send_count"]

        updates: dict[str, object] = {"$set": set_fields}
        if inc_fields:
            updates["$inc"] = inc_fields

        try:
            if set_fields or inc_fields:
                await collection.update_one(
                    {"_id": entry.reservation_id},
                    updates,
                )
        except Exception as exc:
            logger.warning(
                "[outbox=%s] Failed to update reservation audit fields | error=%s",
                entry.id,
                exc,
            )

        try:
            current_reservation = await ReservationDocument.get(entry.reservation_id)
            if current_reservation is not None:
                current_status = (
                    str(current_reservation.status.value)
                    if hasattr(current_reservation.status, "value")
                    else str(current_reservation.status)
                )
            else:
                current_status = "unknown"
            log = ReservationAuditLogDocument(
                reservation_id=entry.reservation_id,
                payment_proof_id=None,
                actor_user_id=None,
                actor_role=None,
                action=cfg["audit_action"],
                previous_status=current_status,
                new_status=current_status,
                source="backend_event",
                metadata=NotificationMetadata(
                    recipient_phone=entry.recipient_identifier,
                    template_key=entry.template_key,
                    provider_message_id=entry.provider_message_id,
                    status="sent",
                ),
            )
            await log.insert()
        except Exception as exc:
            logger.warning(
                "[outbox=%s] Audit log failed | action=%s | error=%s",
                entry.id,
                cfg["audit_action"],
                exc,
            )

    async def process_pending_batch(self, batch_size: int = 10) -> int:
        now = datetime.now(UTC)
        entries = (
            await NotificationOutboxDocument.find(
                {
                    "$or": [
                        {"status": NotificationStatus.PENDING.value},
                        {
                            "status": NotificationStatus.SCHEDULED.value,
                            "scheduled_for": {"$lte": now},
                        },
                    ]
                }
            )
            .sort("created_at")
            .limit(batch_size)
            .to_list()
        )

        count = 0
        for entry in entries:
            await self.send_from_outbox(entry)
            count += 1
        return count
