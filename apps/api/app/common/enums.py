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


class ScheduleStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    FULL = "full"


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

    EXPERIENCE_READ = "experience.read"
    EXPERIENCE_CREATE = "experience.create"
    EXPERIENCE_UPDATE = "experience.update"
    EXPERIENCE_DELETE = "experience.delete"

    SCHEDULE_READ = "schedule.read"
    SCHEDULE_CREATE = "schedule.create"
    SCHEDULE_UPDATE = "schedule.update"
    SCHEDULE_DELETE = "schedule.delete"
    SCHEDULE_CONFIRM_EFFECT = "schedule.confirm.effect"

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

    KNOWLEDGE_READ = "knowledge.read"
    KNOWLEDGE_CREATE = "knowledge.create"
    KNOWLEDGE_DELETE = "knowledge.delete"


class NotificationEventType(StrEnum):
    RESERVATION_CREATED = "reservation_created"
    RESERVATION_CONFIRMED = "reservation_confirmed"
    PARTICIPANT_FORM_LINK_GENERATED = "participant_form_link_generated"
    PRE_SERVICE_REMINDER = "pre_service_reminder"
    POST_SERVICE_COMPLETED = "post_service_completed"
    PAYMENT_APPROVED_FORM_SENT = "payment_approved_form_sent"
    PAYMENT_REJECTED_SENT = "payment_rejected_sent"
    RESERVATION_CONFIRMED_LOGISTICS_SENT = "reservation_confirmed_logistics_sent"
    PARTICIPANT_FORM_RESENT = "participant_form_resent"
    RESERVATION_CANCELLED = "reservation_cancelled"


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
        Permission.SCHEDULE_READ,
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
    },
}
