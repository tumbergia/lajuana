from datetime import datetime

from pydantic import BaseModel

from app.common.enums import ParticipantFormLinkStatus


class ParticipantFormLinkGenerateRequest(BaseModel):
    expected_participants_count: int


class ParticipantFormLinkGenerateResponse(BaseModel):
    id: str
    reservation_id: str
    token: str
    expires_at: datetime
    max_participants: int
    form_url: str


class ParticipantFormLinkStatusResponse(BaseModel):
    id: str
    reservation_id: str
    status: ParticipantFormLinkStatus
    expires_at: datetime
    max_participants: int
    used_count: int
    completed_participants: int
    created_at: datetime
    revoked_at: datetime | None = None


class ParticipantFormPublicStatusResponse(BaseModel):
    reservation_code: str
    experience_name: str
    requested_date: str | None = None
    completed_count: int
    expected_count: int
    is_complete: bool
    link_status: ParticipantFormLinkStatus


class ParticipantFormTokenValidationResponse(BaseModel):
    valid: bool
    reservation_code: str | None = None
    experience_name: str | None = None
    participant_first_name: str | None = None
    expires_at: datetime | None = None
    max_participants: int | None = None
    used_count: int | None = None
