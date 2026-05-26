"""Deterministic WhatsApp notification service for reservation business events.

Sends transactional WhatsApp messages directly via WhatsAppOutboundService
without passing through Gemini, MCP, or the chatbot. Each method is
idempotent by checking reservation audit fields before sending.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from beanie import PydanticObjectId

from app.channels.whatsapp.normalizer import build_conversation_id
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.common.enums import UserRole
from app.core.config import settings
from app.core.logging import logger
from app.documents import (
    ExperienceDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
    ScheduleDocument,
)
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.documents.notification_template_document import NotificationTemplateDocument
from app.notifications.renderer import render_template
from app.services.participant_form_link_service import ParticipantFormLinkService


class ReservationWhatsAppNotificationService:
    """Deterministic WhatsApp notifier for reservation business events.

    Each method:
      1. Resolves the message template from MongoDB.
      2. Renders the template with reservation/experience data.
      3. Sends via WhatsAppOutboundService (Graph API).
      4. Updates reservation audit fields.
      5. Creates a ReservationAuditLogDocument entry.
    """

    def __init__(self) -> None:
        self._outbound = WhatsAppOutboundService()
        self._form_link_service = ParticipantFormLinkService()

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    async def send_payment_approved_participant_form(
        self,
        reservation: ReservationDocument,
        actor_id: PydanticObjectId | None,
    ) -> bool:
        """Send WhatsApp with participant form link after payment approval.

        Idempotent: if ``participant_form_sent_at`` is already set, skips
        sending and returns True.
        """
        if not reservation.holder_phone:
            logger.warning(
                "[reservation=%s] No holder_phone, skipping form WhatsApp",
                reservation.id,
            )
            return False

        # Idempotency: already sent
        if reservation.participant_form_sent_at is not None:
            logger.info(
                "[reservation=%s] Form already sent at %s, skipping",
                reservation.id,
                reservation.participant_form_sent_at,
            )
            return True

        # Ensure form URL exists
        if not reservation.form_url:
            form_url = await self._ensure_form_url(reservation, actor_id)
        else:
            form_url = reservation.form_url

        experience = await ExperienceDocument.get(reservation.experience_id)
        experience_name = experience.name if experience else ""

        template = await self._load_template("payment_approved_form_sent.customer")
        if template is None:
            logger.error(
                "[reservation=%s] Template payment_approved_form_sent.customer not found",
                reservation.id,
            )
            return False

        body = render_template(template.body, {
            "customer_name": reservation.holder_name or "Cliente",
            "experience_name": experience_name,
            "form_url": form_url,
        })

        return await self._send_and_audit(
            reservation=reservation,
            template_key=template.template_key,
            body=body,
            actor_id=actor_id,
            audit_action="notification.payment_approved_form_sent",
            update_fields={
                "participant_form_sent_at": datetime.now(UTC),
                "participant_form_sent_by": actor_id,
                "participant_form_send_count": reservation.participant_form_send_count + 1,
            },
        )

    async def send_payment_rejected(
        self,
        reservation: ReservationDocument,
        reason: str,
        actor_id: PydanticObjectId | None,
    ) -> bool:
        """Send WhatsApp with rejection reason after payment rejection."""
        if not reservation.holder_phone:
            logger.warning(
                "[reservation=%s] No holder_phone, skipping rejection WhatsApp",
                reservation.id,
            )
            return False

        experience = await ExperienceDocument.get(reservation.experience_id)
        experience_name = experience.name if experience else ""

        template = await self._load_template("payment_rejected_sent.customer")
        if template is None:
            logger.error(
                "[reservation=%s] Template payment_rejected_sent.customer not found",
                reservation.id,
            )
            return False

        body = render_template(template.body, {
            "customer_name": reservation.holder_name or "Cliente",
            "experience_name": experience_name,
            "rejection_reason": reason,
        })

        return await self._send_and_audit(
            reservation=reservation,
            template_key=template.template_key,
            body=body,
            actor_id=actor_id,
            audit_action="notification.payment_rejected_sent",
            update_fields=None,
        )

    async def send_reservation_confirmed_logistics(
        self,
        reservation: ReservationDocument,
        actor_id: PydanticObjectId | None,
    ) -> bool:
        """Send WhatsApp with logistics/recommendations after confirmation.

        Does NOT include the form link (form was already sent on payment
        approval). Idempotent: skips if confirmation_message_sent_at is set.
        """
        if not reservation.holder_phone:
            logger.warning(
                "[reservation=%s] No holder_phone, skipping logistics WhatsApp",
                reservation.id,
            )
            return False

        if reservation.confirmation_message_sent_at is not None:
            logger.info(
                "[reservation=%s] Logistics already sent at %s, skipping",
                reservation.id,
                reservation.confirmation_message_sent_at,
            )
            return True

        experience = await ExperienceDocument.get(reservation.experience_id)
        experience_name = experience.name if experience else ""

        schedule: ScheduleDocument | None = None
        start_time = ""
        meeting_point = "La Juana (ver coordenadas)"

        if reservation.schedule_id:
            schedule = await ScheduleDocument.get(reservation.schedule_id)

        if schedule is not None:
            start_time = (
                schedule.start_time.isoformat()
                if hasattr(schedule.start_time, "isoformat")
                else str(schedule.start_time)
            )

        scheduled_date = (
            reservation.requested_date.isoformat()
            if reservation.requested_date
            else ""
        )
        if schedule is not None and not scheduled_date:
            scheduled_date = schedule.date.isoformat()

        template = await self._load_template(
            "reservation_confirmed_logistics_sent.customer"
        )
        if template is None:
            logger.error(
                "[reservation=%s] Template reservation_confirmed_logistics_sent.customer not found",
                reservation.id,
            )
            return False

        body = render_template(template.body, {
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "experience_name": experience_name,
            "scheduled_date": scheduled_date,
            "start_time": start_time,
            "meeting_point": meeting_point,
        })

        return await self._send_and_audit(
            reservation=reservation,
            template_key=template.template_key,
            body=body,
            actor_id=actor_id,
            audit_action="notification.reservation_confirmed_logistics_sent",
            update_fields={
                "confirmation_message_sent_at": datetime.now(UTC),
                "confirmation_message_sent_by": actor_id,
            },
        )

    async def resend_participant_form(
        self,
        reservation: ReservationDocument,
        actor_id: PydanticObjectId | None,
    ) -> bool:
        """Re-send the participant form WhatsApp on manual admin request.

        Always sends, regardless of previous sends (no idempotency).
        """
        if not reservation.holder_phone:
            logger.warning(
                "[reservation=%s] No holder_phone, skipping resend WhatsApp",
                reservation.id,
            )
            return False

        if not reservation.form_url:
            await self._ensure_form_url(reservation, actor_id)

        experience = await ExperienceDocument.get(reservation.experience_id)
        experience_name = experience.name if experience else ""

        template = await self._load_template("participant_form_resent.customer")
        if template is None:
            logger.error(
                "[reservation=%s] Template participant_form_resent.customer not found",
                reservation.id,
            )
            return False

        body = render_template(template.body, {
            "customer_name": reservation.holder_name or "Cliente",
            "experience_name": experience_name,
            "form_url": reservation.form_url or "",
        })

        success = await self._send_and_audit(
            reservation=reservation,
            template_key=template.template_key,
            body=body,
            actor_id=actor_id,
            audit_action="notification.participant_form_resent",
            update_fields={
                "participant_form_sent_at": datetime.now(UTC),
                "participant_form_sent_by": actor_id,
                "participant_form_send_count": reservation.participant_form_send_count + 1,
            },
        )
        return success

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    async def _ensure_form_url(
        self,
        reservation: ReservationDocument,
        actor_id: PydanticObjectId | None,
    ) -> str:
        """Generate a participant form link if one does not already exist."""
        expected = reservation.expected_participants_count or reservation.participant_count
        _, raw_token = await self._form_link_service.generate(
            reservation_id=str(reservation.id),
            expected_participants_count=expected,
            created_by=actor_id,
        )
        form_url = f"{settings.app_base_url}/formulario-participantes?t={raw_token}"
        reservation.form_url = form_url
        reservation.expected_participants_count = expected
        await reservation.save()
        return form_url

    async def _load_template(self, template_key: str) -> NotificationTemplateDocument | None:
        return await NotificationTemplateDocument.find_one(
            {
                "template_key": template_key,
                "channel": "whatsapp",
                "is_active": True,
            }
        )

    async def _send_and_audit(
        self,
        *,
        reservation: ReservationDocument,
        template_key: str,
        body: str,
        actor_id: PydanticObjectId | None,
        audit_action: str,
        update_fields: dict | None,
    ) -> bool:
        """Send the message via WhatsApp and persist audit trail.

        Best-effort: a sending failure does NOT raise — it is logged and
        audited as ``status: "failed"``.
        """
        holder_phone = reservation.holder_phone or ""
        conversation_id = build_conversation_id("whatsapp", holder_phone)
        turn = ConversationTurnDocument(
            trace_id=str(uuid4()),
            channel="whatsapp",
            from_phone=holder_phone,
            user_message="(transactional send)",
            conversation_id=conversation_id,
        )
        await turn.insert()

        try:
            result = await self._outbound.send(
                turn=turn,
                to_phone=reservation.holder_phone or "",
                text=body,
            )

            provider_message_id = result.provider_message_id
            status = result.status
        except Exception as exc:
            logger.error(
                "[reservation=%s] WhatsApp send failed | action=%s | error=%s",
                reservation.id,
                audit_action,
                exc,
            )
            provider_message_id = None
            status = "failed"

        # Persist audit fields on reservation (direct $set to skip Beanie change tracking)
        if update_fields:
            set_fields: dict[str, object] = dict(update_fields)
            if provider_message_id:
                set_fields["participant_form_last_message_id"] = provider_message_id
            # Use motor collection to avoid Beanie state issues after previous saves
            collection = ReservationDocument.get_motor_collection()
            await collection.update_one(
                {"_id": reservation.id},
                {"$set": set_fields},
            )
            # Also update the in-memory object so callers see latest values
            for field, value in set_fields.items():
                setattr(reservation, field, value)

        # Audit log (best-effort, non-critical)
        try:
            log = ReservationAuditLogDocument(
                reservation_id=reservation.id,
                payment_proof_id=None,
                actor_user_id=actor_id,
                actor_role=UserRole.ADMIN,
                action=audit_action,
                source="backend_event",
                metadata={
                    "recipient_phone": reservation.holder_phone,
                    "template_key": template_key,
                    "provider_message_id": provider_message_id,
                    "status": status,
                },
            )
            await log.insert()
        except Exception as exc:
            logger.warning(
                "[reservation=%s] Audit log failed | action=%s | error=%s",
                reservation.id,
                audit_action,
                exc,
            )

        return status == "sent"
