from enum import StrEnum


class EquineSpecies(StrEnum):
    MULE = "mule"
    DONKEY = "donkey"
    HORSE = "horse"
    UNKNOWN = "unknown"


class EquineSex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


class EquineLocationStatus(StrEnum):
    LA_JUANA = "la_juana"
    OTHER = "other"
    UNKNOWN = "unknown"


class UserRole(StrEnum):
    ADMIN = "admin"
    GUIDE = "guide"
    UNASSIGNED = "unassigned"


class RoleRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReservationStatus(StrEnum):
    CONTACT = "contact"
    QUOTED = "quoted"
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_RECEIVED = "payment_received"
    CONFIRMED = "confirmed"
    PRE_RESERVED = "pre_reserved"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"


class ExperienceLevel(StrEnum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExperienceDifficulty(StrEnum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExperienceCategory(StrEnum):
    ROUTE = "route"
    EXPERIENCE = "experience"
    PRIVATE = "private"


class ExperienceStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Channel(StrEnum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    RECEIVED = "received"
    VERIFIED = "verified"
    REJECTED = "rejected"


class AssignmentStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    FINAL = "final"
    REPLACED = "replaced"
    CANCELLED = "cancelled"


class AssignmentSource(StrEnum):
    MANUAL_ADMIN = "manual_admin"
    MANUAL_GUIDE = "manual_guide"
    SYSTEM_SUGGESTED = "system_suggested"


class EquineOperationalStatus(StrEnum):
    AVAILABLE = "available"
    RESTING = "resting"
    IN_SERVICE = "in_service"
    INJURED = "injured"
    RETIRED = "retired"
    UNAVAILABLE = "unavailable"
    RESTRICTED = "restricted"


class EquineExperienceFit(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL = "all"
    STAFF_ONLY = "staff_only"
    NOT_ASSIGNABLE = "not_assignable"


class ParticipantFormLinkStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPLETED = "completed"


class ParticipantFormStatus(StrEnum):
    NOT_SENT = "not_sent"
    SENT = "sent"
    PARTIAL = "partial"
    COMPLETE = "complete"
    REVOKED = "revoked"


class Permission(StrEnum):
    AUTH_SELF_READ = "auth.self.read"
    AUTH_SELF_UPDATE_PASSWORD = "auth.self.update_password"

    USER_READ = "user.read"
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"

    ROLE_REQUEST_CREATE_SELF = "role_request.create_self"
    ROLE_REQUEST_READ = "role_request.read"
    ROLE_REQUEST_MANAGE = "role_request.manage"

    EXPERIENCE_READ = "experience.read"
    EXPERIENCE_CREATE = "experience.create"
    EXPERIENCE_UPDATE = "experience.update"
    EXPERIENCE_DELETE = "experience.delete"

    RESERVATION_READ = "reservation.read"
    RESERVATION_CREATE = "reservation.create"
    RESERVATION_UPDATE = "reservation.update"
    RESERVATION_CONFIRM = "reservation.confirm"
    RESERVATION_CANCEL = "reservation.cancel"

    PARTICIPANT_READ = "participant.read"
    PARTICIPANT_CREATE = "participant.create"
    PARTICIPANT_UPDATE = "participant.update"

    PAYMENT_PROOF_READ = "payment_proof.read"
    PAYMENT_PROOF_CREATE = "payment_proof.create"
    PAYMENT_VERIFY = "payment.verify"

    EQUINE_READ = "equine.read"
    EQUINE_CREATE = "equine.create"
    EQUINE_UPDATE = "equine.update"
    EQUINE_DELETE = "equine.delete"

    RESERVATION_DELETE = "reservation.delete"

    SADDLE_READ = "saddle.read"
    SADDLE_CREATE = "saddle.create"
    SADDLE_UPDATE = "saddle.update"
    SADDLE_DELETE = "saddle.delete"

    ASSIGNMENT_READ = "assignment.read"
    ASSIGNMENT_CREATE = "assignment.create"
    ASSIGNMENT_UPDATE = "assignment.update"

    LOG_READ = "log.read"
    LOG_CREATE = "log.create"
    LOG_UPDATE = "log.update"
    LOG_DELETE = "log.delete"

    PROVIDER_READ = "provider.read"
    PROVIDER_CREATE = "provider.create"
    PROVIDER_UPDATE = "provider.update"
    PROVIDER_DELETE = "provider.delete"

    POLICY_READ = "policy.read"
    POLICY_CREATE = "policy.create"
    POLICY_UPDATE = "policy.update"

    CONFIG_READ = "config.read"
    CONFIG_UPDATE = "config.update"

    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_UPDATE = "notification.update"
    NOTIFICATION_TEMPLATE_READ = "notification_template.read"
    NOTIFICATION_TEMPLATE_CREATE = "notification_template.create"
    NOTIFICATION_TEMPLATE_UPDATE = "notification_template.update"
    PARTICIPANT_FORM_LINK_CREATE = "participant_form_link.create"
    PARTICIPANT_FORM_LINK_READ = "participant_form_link.read"
    PARTICIPANT_FORM_LINK_REVOKE = "participant_form_link.revoke"


class NotificationEventType(StrEnum):
    RESERVATION_CREATED = "reservation_created"
    RESERVATION_CONFIRMED = "reservation_confirmed"
    PARTICIPANT_FORM_LINK_GENERATED = "participant_form_link_generated"
    PRE_SERVICE_REMINDER = "pre_service_reminder"
    POST_SERVICE_COMPLETED = "post_service_completed"
    PAYMENT_APPROVED_FORM_SENT = "payment_approved_form_sent"
    PAYMENT_APPROVED_LOCATION_SENT = "payment_approved_location_sent"
    PAYMENT_REJECTED_SENT = "payment_rejected_sent"
    RESERVATION_CONFIRMED_LOGISTICS_SENT = "reservation_confirmed_logistics_sent"
    PARTICIPANT_FORM_RESENT = "participant_form_resent"
    RESERVATION_CANCELLED = "reservation_cancelled"
    PAYMENT_PROOF_REGISTERED = "payment_proof_registered"
    PARTICIPANT_FORM_COMPLETED = "participant_form_completed"
    HUMAN_REVIEW_REQUESTED = "human_review_requested"
    WHATSAPP_MESSAGE_UNATTENDED = "whatsapp_message_unattended"
    RESERVATION_STATUS_CHANGED = "reservation_status_changed"
    RESERVATION_UPDATED = "reservation_updated"
    CONFIGURATION_CHANGED = "configuration_changed"
    ASSIGNMENT_CHANGED = "assignment_changed"
    TOMORROW_SERVICES_SUMMARY = "tomorrow_services_summary"
    WHATSAPP_DELIVERY_FAILED = "whatsapp_delivery_failed"
    ROLE_REQUEST_CREATED = "role_request_created"
    ROLE_REQUEST_DECIDED = "role_request_decided"


# Preference keys for in-app notification toggles (grouped for UI).
NOTIFICATION_PREFERENCE_KEYS: tuple[str, ...] = (
    NotificationEventType.RESERVATION_CREATED.value,
    NotificationEventType.RESERVATION_CONFIRMED.value,
    NotificationEventType.RESERVATION_STATUS_CHANGED.value,
    NotificationEventType.RESERVATION_UPDATED.value,
    NotificationEventType.RESERVATION_CANCELLED.value,
    NotificationEventType.PAYMENT_PROOF_REGISTERED.value,
    NotificationEventType.PARTICIPANT_FORM_COMPLETED.value,
    NotificationEventType.HUMAN_REVIEW_REQUESTED.value,
    NotificationEventType.WHATSAPP_MESSAGE_UNATTENDED.value,
    NotificationEventType.CONFIGURATION_CHANGED.value,
    NotificationEventType.ASSIGNMENT_CHANGED.value,
    NotificationEventType.TOMORROW_SERVICES_SUMMARY.value,
    NotificationEventType.WHATSAPP_DELIVERY_FAILED.value,
    NotificationEventType.ROLE_REQUEST_CREATED.value,
)


class NotificationChannel(StrEnum):
    EMAIL = "email"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: set(Permission),
    UserRole.GUIDE: {
        Permission.AUTH_SELF_READ,
        Permission.AUTH_SELF_UPDATE_PASSWORD,
        Permission.EXPERIENCE_READ,
        Permission.RESERVATION_READ,
        Permission.PARTICIPANT_READ,
        Permission.EQUINE_READ,
        Permission.SADDLE_READ,
        Permission.ASSIGNMENT_READ,
        Permission.LOG_READ,
        Permission.LOG_CREATE,
        Permission.LOG_UPDATE,
        Permission.POLICY_READ,
        Permission.NOTIFICATION_READ,
        Permission.PARTICIPANT_FORM_LINK_READ,
    },
    UserRole.UNASSIGNED: {
        Permission.AUTH_SELF_READ,
        Permission.AUTH_SELF_UPDATE_PASSWORD,
        Permission.ROLE_REQUEST_CREATE_SELF,
        Permission.NOTIFICATION_READ,
    },
}
