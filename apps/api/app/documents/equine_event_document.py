from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from beanie import PydanticObjectId
from pymongo import IndexModel

from app.common.collections import Collections
from app.common.enums import EquineOperationalStatus
from app.documents.base import AuditDocument


class EquineEventType(StrEnum):
    HEALTH_CHECK = "health_check"
    INJURY = "injury"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    VACCINATION = "vaccination"
    FARRIER = "farrier"
    HOOF_CARE = "hoof_care"
    DENTISTRY = "dentistry"
    WEIGHT = "weight"
    HEIGHT = "height"
    TRAINING = "training"
    NUTRITION = "nutrition"
    LAB_TEST = "lab_test"
    REST = "rest"
    AVAILABILITY_CHANGE = "availability_change"
    ROUTE_ACTIVITY = "route_activity"
    NOTE = "note"


EquineEventSeverity = Literal["low", "medium", "high", "critical"]
EquineEventSource = Literal["mobile_app", "admin_app", "system", "ai_tool"]


class EquineEventDocument(AuditDocument):
    equine_id: PydanticObjectId
    event_type: EquineEventType
    happened_at: datetime
    title: str
    description: str | None = None
    severity: EquineEventSeverity | None = None

    reservation_id: PydanticObjectId | None = None
    assignment_id: PydanticObjectId | None = None
    participant_id: PydanticObjectId | None = None

    measured_weight_kg: Decimal | None = None
    measured_height_m: Decimal | None = None

    next_due_at: datetime | None = None
    performed_by: str | None = None
    medication_name: str | None = None
    dosage: str | None = None
    lab_result_summary: str | None = None

    affects_availability: bool = False
    resulting_operational_status: EquineOperationalStatus | None = None
    rest_until: datetime | None = None

    source: EquineEventSource = "mobile_app"

    class Settings:
        name = Collections.EQUINE_EVENTS
        indexes = [
            "equine_id",
            "event_type",
            "reservation_id",
            IndexModel([("equine_id", 1), ("happened_at", -1)]),
        ]
