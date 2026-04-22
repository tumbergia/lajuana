from app.documents import (
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    ReservationDocument,
    ScheduleDocument,
    UserDocument,
)
from app.schemas.auth import UserResponseSchema
from app.schemas.experience import ExperienceResponseSchema
from app.schemas.participant import ParticipantResponseSchema
from app.schemas.payment_proof import PaymentProofResponseSchema
from app.schemas.reservation import ReservationListItemSchema, ReservationResponseSchema
from app.schemas.schedule import ScheduleResponseSchema


def user_to_response(user: UserDocument) -> UserResponseSchema:
    return UserResponseSchema(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


def experience_to_response(doc: ExperienceDocument) -> ExperienceResponseSchema:
    return ExperienceResponseSchema(
        id=str(doc.id),
        name=doc.name,
        slug=doc.slug,
        description=doc.description,
        level=doc.level,
        duration_hours=doc.duration_hours,
        duration_days=doc.duration_days,
        base_capacity=doc.base_capacity,
        is_active=doc.is_active,
    )


def schedule_to_response(doc: ScheduleDocument) -> ScheduleResponseSchema:
    return ScheduleResponseSchema(
        id=str(doc.id),
        experience_id=str(doc.experience_id),
        date=doc.date,
        start_time=doc.start_time,
        capacity_total=doc.capacity_total,
        reserved_slots=doc.reserved_slots,
        internal_slots=doc.internal_slots,
        blocked_slots=doc.blocked_slots,
        available_slots=doc.available_slots,
        status=doc.status,
        custom_request_only=doc.custom_request_only,
        notes=doc.notes,
    )


def reservation_to_response(doc: ReservationDocument) -> ReservationResponseSchema:
    return ReservationResponseSchema(
        id=str(doc.id),
        code=doc.code,
        experience_id=str(doc.experience_id),
        schedule_id=str(doc.schedule_id) if doc.schedule_id else None,
        channel=doc.channel,
        status=doc.status,
        participant_count=doc.participant_count,
        payment_status=doc.payment_status,
        holder_name=doc.holder_name,
        holder_email=doc.holder_email,
        holder_phone=doc.holder_phone,
        requested_date=doc.requested_date,
        quoted_total_amount=doc.quoted_total_amount,
        currency=doc.currency,
        confirmed_at=doc.confirmed_at,
        cancelled_at=doc.cancelled_at,
        completed_at=doc.completed_at,
        created_at=doc.created_at,
    )


def reservation_to_list_item(doc: ReservationDocument) -> ReservationListItemSchema:
    return ReservationListItemSchema(
        id=str(doc.id),
        code=doc.code,
        status=doc.status,
        participant_count=doc.participant_count,
        payment_status=doc.payment_status,
        created_at=doc.created_at,
    )


def participant_to_response(doc: ParticipantDocument) -> ParticipantResponseSchema:
    return ParticipantResponseSchema(
        id=str(doc.id),
        reservation_id=str(doc.reservation_id),
        first_name=doc.first_name,
        last_name=doc.last_name,
        birth_date=doc.birth_date,
        document_type=doc.document_type,
        document_number=doc.document_number,
        phone=doc.phone,
        country=doc.country,
        city=doc.city,
        height_cm=doc.height_cm,
        weight_kg=doc.weight_kg,
        experience_level=doc.experience_level,
        emergency_contact=doc.emergency_contact,
        accepted_data_processing=doc.accepted_data_processing,
        accepted_media_usage=doc.accepted_media_usage,
        is_completed=doc.is_completed,
        created_at=doc.created_at,
    )


def payment_proof_to_response(doc: PaymentProofDocument) -> PaymentProofResponseSchema:
    return PaymentProofResponseSchema(
        id=str(doc.id),
        reservation_id=str(doc.reservation_id),
        storage_key=doc.storage_key,
        filename=doc.filename,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        sha256=doc.sha256,
        status=doc.status,
        uploaded_at=doc.uploaded_at,
    )
