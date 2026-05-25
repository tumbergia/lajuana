from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ParticipantDocument,
    ParticipantFormLinkDocument,
    PaymentProofDocument,
    PolicyDocument,
    ProviderDocument,
    ReservationDocument,
    SaddleDocument,
    ScheduleDocument,
    ServiceLogDocument,
    UserDocument,
)
from app.schemas.assignment import AssignmentResponseSchema
from app.schemas.auth import UserResponseSchema
from app.schemas.equine import EquineResponseSchema
from app.schemas.experience import ExperienceResponseSchema
from app.schemas.participant import ParticipantResponseSchema
from app.schemas.participant_form_link import ParticipantFormLinkStatusResponse
from app.schemas.payment_proof import PaymentProofResponseSchema
from app.schemas.policy import PolicyResponseSchema
from app.schemas.provider import ProviderResponseSchema
from app.schemas.reservation import ReservationListItemSchema, ReservationResponseSchema
from app.schemas.saddle import SaddleResponseSchema
from app.schemas.schedule import ScheduleResponseSchema
from app.schemas.service_log import ServiceLogResponseSchema


def user_to_response(user: UserDocument) -> UserResponseSchema:
    return UserResponseSchema(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        version=user.version,
        created_at=user.created_at,
        updated_at=user.updated_at,
        deleted_at=user.deleted_at,
    )


def experience_to_response(doc: ExperienceDocument) -> ExperienceResponseSchema:
    return ExperienceResponseSchema(
        id=str(doc.id),
        name=doc.name,
        slug=doc.slug,
        subtitle=doc.subtitle,
        description=doc.description,
        image_url=doc.image_url,
        level=doc.level,
        difficulty=doc.difficulty,
        category=doc.category,
        status=doc.status,
        duration_hours=doc.duration_hours,
        duration_days=doc.duration_days,
        base_capacity=doc.base_capacity,
        duration=doc.duration,
        route_details=doc.route_details,
        pricing=doc.pricing,
        inclusions=doc.inclusions,
        standard_max_participants=doc.standard_max_participants,
        min_participants=doc.min_participants,
        tags=doc.tags,
        is_active=doc.is_active,
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
    )


def schedule_to_response(doc: ScheduleDocument) -> ScheduleResponseSchema:
    return ScheduleResponseSchema(
        id=str(doc.id),
        experience_id=str(doc.experience_id),
        date=doc.date,
        start_time=doc.start_time,
        is_active=doc.is_active,
        capacity_total=doc.capacity_total,
        reserved_slots=doc.reserved_slots,
        internal_slots=doc.internal_slots,
        blocked_slots=doc.blocked_slots,
        available_slots=doc.available_slots,
        status=doc.status,
        custom_request_only=doc.custom_request_only,
        notes=doc.notes,
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
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
        expected_participants_count=doc.expected_participants_count,
        participants_completed_count=doc.participants_completed_count,
        participant_form_status=doc.participant_form_status,
        form_url=doc.form_url,
        confirmed_at=doc.confirmed_at,
        cancelled_at=doc.cancelled_at,
        completed_at=doc.completed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
        version=doc.version,
    )


def reservation_to_list_item(doc: ReservationDocument) -> ReservationListItemSchema:
    return ReservationListItemSchema(
        id=str(doc.id),
        code=doc.code,
        status=doc.status,
        participant_count=doc.participant_count,
        payment_status=doc.payment_status,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
        version=doc.version,
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
        dietary_restrictions=doc.dietary_restrictions,
        blood_type=doc.blood_type,
        eps_or_travel_insurance=doc.eps_or_travel_insurance,
        health_conditions=doc.health_conditions,
        sensory_disabilities=doc.sensory_disabilities,
        emergency_contact=doc.emergency_contact,
        accepted_data_processing=doc.accepted_data_processing,
        accepted_media_usage=doc.accepted_media_usage,
        accepted_risk_release=doc.accepted_risk_release,
        risk_release_text_version=doc.risk_release_text_version,
        is_completed=doc.is_completed,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
        version=doc.version,
    )


def form_link_to_status_response(
    doc: ParticipantFormLinkDocument,
) -> ParticipantFormLinkStatusResponse:
    return ParticipantFormLinkStatusResponse(
        id=str(doc.id),
        reservation_id=str(doc.reservation_id),
        status=doc.status,
        expires_at=doc.expires_at,
        max_participants=doc.max_participants,
        used_count=doc.used_count,
        completed_participants=doc.used_count,
        created_at=doc.created_at,
        revoked_at=doc.revoked_at,
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
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
        version=doc.version,
    )


def equine_to_response(doc: EquineDocument) -> EquineResponseSchema:
    return EquineResponseSchema(
        id=str(doc.id),
        name=doc.name,
        approximate_birth_date=doc.approximate_birth_date,
        approximate_age_years=doc.approximate_age_years,
        weight_kg=doc.weight_kg,
        sex=doc.sex,
        breed=doc.breed,
        gait=doc.gait,
        is_available=doc.is_available,
        availability_notes=doc.availability_notes,
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
    )


def saddle_to_response(doc: SaddleDocument) -> SaddleResponseSchema:
    return SaddleResponseSchema(
        id=str(doc.id),
        code=doc.code,
        name=doc.name,
        is_available=doc.is_available,
        notes=doc.notes,
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
    )


def assignment_to_response(doc: AssignmentDocument) -> AssignmentResponseSchema:
    return AssignmentResponseSchema(
        id=str(doc.id),
        reservation_id=str(doc.reservation_id),
        participant_id=str(doc.participant_id),
        equine_id=str(doc.equine_id),
        saddle_id=str(doc.saddle_id) if doc.saddle_id else None,
        priority=doc.priority,
        assigned_manually=doc.assigned_manually,
        notes=doc.notes,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
        version=doc.version,
    )


def service_log_to_response(doc: ServiceLogDocument) -> ServiceLogResponseSchema:
    return ServiceLogResponseSchema(
        id=str(doc.id),
        reservation_id=str(doc.reservation_id),
        event_type=doc.event_type,
        happened_at=doc.happened_at,
        checkpoint_name=doc.checkpoint_name,
        notes=doc.notes,
        related_participant_id=(
            str(doc.related_participant_id) if doc.related_participant_id else None
        ),
        related_equine_id=str(doc.related_equine_id) if doc.related_equine_id else None,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
        version=doc.version,
    )


def provider_to_response(doc: ProviderDocument) -> ProviderResponseSchema:
    return ProviderResponseSchema(
        id=str(doc.id),
        name=doc.name,
        provider_type=doc.provider_type,
        contact_name=doc.contact_name,
        phone=doc.phone,
        email=doc.email,
        location=doc.location,
        capacity_notes=doc.capacity_notes,
        rate_notes=doc.rate_notes,
        is_active=doc.is_active,
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
    )


def policy_to_response(doc: PolicyDocument) -> PolicyResponseSchema:
    return PolicyResponseSchema(
        id=str(doc.id),
        reservation_id=str(doc.reservation_id),
        provider_id=str(doc.provider_id) if doc.provider_id else None,
        policy_number=doc.policy_number,
        issued_at=doc.issued_at,
        expires_at=doc.expires_at,
        notes=doc.notes,
        version=doc.version,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        deleted_at=doc.deleted_at,
    )
