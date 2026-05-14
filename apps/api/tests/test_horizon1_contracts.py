from datetime import date

import pytest
from pydantic import ValidationError

from app.ai.mcp.tool_contracts import (
    CheckExperienceAvailabilityInput,
    ListAvailableSchedulesInput,
    ListExperiencesInput,
    QuoteExperienceInput,
    RequestHumanReviewInput,
)


class TestQuoteExperienceInput:
    def test_rejects_participants_count(self):
        with pytest.raises(ValidationError):
            QuoteExperienceInput.model_validate({
                "experience_query": "medio día",
                "participants_count": 4,
            })

    def test_accepts_participant_count(self):
        payload = QuoteExperienceInput.model_validate({
            "experience_query": "medio día",
            "participant_count": 4,
            "requested_date": "2026-06-20",
        })
        assert payload.participant_count == 4
        assert payload.requested_date == date(2026, 6, 20)

    def test_rejects_legacy_schedule_id(self):
        with pytest.raises(ValidationError):
            QuoteExperienceInput.model_validate({
                "experience_query": "medio día",
                "participant_count": 4,
                "schedule_id": "legacy-schedule-id",
            })

    def test_rejects_special_conditions(self):
        with pytest.raises(ValidationError):
            QuoteExperienceInput.model_validate({
                "experience_query": "medio día",
                "participant_count": 4,
                "special_conditions": {"foo": "bar"},
            })

    def test_requires_experience_id_or_query(self):
        with pytest.raises(ValidationError):
            QuoteExperienceInput.model_validate({
                "participant_count": 4,
            })

    def test_accepts_optional_notes(self):
        payload = QuoteExperienceInput.model_validate({
            "experience_query": "medio día",
            "participant_count": 4,
            "notes": "Preferencia de horario en la mañana",
        })
        assert payload.notes == "Preferencia de horario en la mañana"

    def test_accepts_requested_date_as_none(self):
        payload = QuoteExperienceInput.model_validate({
            "experience_query": "medio día",
            "participant_count": 4,
        })
        assert payload.requested_date is None


class TestListExperiencesInput:
    def test_defaults(self):
        payload = ListExperiencesInput()
        assert payload.is_active is True
        assert payload.limit == 20

    def test_rejects_limit_above_50(self):
        with pytest.raises(ValidationError):
            ListExperiencesInput(limit=100)

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            ListExperiencesInput.model_validate({
                "is_active": True,
                "invalid_field": "value",
            })


class TestCheckExperienceAvailabilityInput:
    def test_requires_experience(self):
        with pytest.raises(ValidationError) as exc:
            CheckExperienceAvailabilityInput.model_validate({
                "requested_date": "2026-06-20",
                "participant_count": 4,
            })
        assert "experience_id_or_experience_query_required" in str(exc.value)

    def test_accepts_valid_input(self):
        payload = CheckExperienceAvailabilityInput.model_validate({
            "experience_query": "medio día",
            "requested_date": "2026-06-20",
            "participant_count": 4,
        })
        assert payload.participant_count == 4

    def test_rejects_participant_count_above_30(self):
        with pytest.raises(ValidationError):
            CheckExperienceAvailabilityInput.model_validate({
                "experience_query": "medio día",
                "requested_date": "2026-06-20",
                "participant_count": 31,
            })


class TestListAvailableSchedulesInput:
    def test_all_optional_defaults(self):
        payload = ListAvailableSchedulesInput()
        assert payload.limit == 10
        assert payload.participant_count is None
        assert payload.date_from is None
        assert payload.date_to is None

    def test_rejects_limit_above_30(self):
        with pytest.raises(ValidationError):
            ListAvailableSchedulesInput(limit=50)

    def test_rejects_participant_count_above_30(self):
        with pytest.raises(ValidationError):
            ListAvailableSchedulesInput(participant_count=50)


class TestRequestHumanReviewInput:
    def test_accepts_valid_input(self):
        payload = RequestHumanReviewInput.model_validate({
            "conversation_id": "conv-001",
            "reason_code": "customer_requests_human",
            "summary": "El cliente solicita hablar con un asesor humano.",
        })
        assert payload.conversation_id == "conv-001"
        assert payload.priority == "normal"

    def test_rejects_short_summary(self):
        with pytest.raises(ValidationError):
            RequestHumanReviewInput.model_validate({
                "conversation_id": "conv-001",
                "reason_code": "customer_requests_human",
                "summary": "Corto",
            })

    def test_rejects_invalid_reason_code(self):
        with pytest.raises(ValidationError):
            RequestHumanReviewInput.model_validate({
                "conversation_id": "conv-001",
                "reason_code": "invalid_code",
                "summary": "El cliente solicita hablar con un asesor humano.",
            })
