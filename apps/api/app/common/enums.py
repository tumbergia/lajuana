from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    STAFF = "staff"
    GUIDE = "guide"


class ReservationStatus(StrEnum):
    CONTACT = "contact"
    QUOTED = "quoted"
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_RECEIVED = "payment_received"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ScheduleStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    FULL = "full"


class ExperienceLevel(StrEnum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


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


class AssignmentPriority(StrEnum):
    STANDARD = "standard"
    CHILD_SAFETY = "child_safety"
    SENIOR_SAFETY = "senior_safety"
