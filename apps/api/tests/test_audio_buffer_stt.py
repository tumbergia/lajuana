"""Tests for deferred audio STT + buffer combine (same debounce as text)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.ai.providers.stt_provider import TranscriptionResult
from app.conversations.services import conversation_turn_worker as worker_mod
from app.conversations.services.conversation_turn_worker import (
    audio_events_unsupported_language,
    combine_messages,
    ensure_audio_transcriptions,
)


class _FakeAudioEvent:
    def __init__(
        self,
        *,
        wa_message_id: str,
        media_id: str | None = "media-1",
        message_type: str = "audio",
        body: str | None = "[audio]",
        transcription: str | None = None,
        transcription_language: str | None = None,
    ) -> None:
        self.wa_message_id = wa_message_id
        self.media_id = media_id
        self.message_type = message_type
        self.body = body
        self.transcription = transcription
        self.transcription_language = transcription_language
        self.saved = False

    async def save(self) -> None:
        self.saved = True


@pytest.mark.asyncio
async def test_ensure_audio_transcriptions_runs_stt_and_sets_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_stt(media_id: str) -> TranscriptionResult:
        return TranscriptionResult(
            text=f"texto de {media_id}",
            language="zh",
            language_probability=0.9,
            duration=1.0,
        )

    monkeypatch.setattr(worker_mod, "download_and_transcribe", fake_stt)
    events = [
        _FakeAudioEvent(wa_message_id="1", media_id="m1"),
        _FakeAudioEvent(wa_message_id="2", media_id="m2"),
    ]
    lang = await ensure_audio_transcriptions(events)  # type: ignore[arg-type]
    assert lang == "zh"
    assert events[0].transcription == "texto de m1"
    assert events[1].transcription == "texto de m2"
    assert events[0].body == "texto de m1"
    assert events[0].saved is True


@pytest.mark.asyncio
async def test_combine_two_audio_transcriptions() -> None:
    events = [
        _FakeAudioEvent(
            wa_message_id="1",
            body="Primera parte sobre la fábrica",
            transcription="Primera parte sobre la fábrica",
        ),
        _FakeAudioEvent(
            wa_message_id="2",
            body="Segunda parte: quiero fechas",
            transcription="Segunda parte: quiero fechas",
        ),
    ]
    combined = combine_messages(events)  # type: ignore[arg-type]
    assert combined == (
        "Primera parte sobre la fábrica\nSegunda parte: quiero fechas"
    )


def test_unsupported_only_audios_rejected() -> None:
    events = [
        _FakeAudioEvent(
            wa_message_id="1",
            transcription="안녕",
            transcription_language="ko",
            body="안녕",
        ),
        _FakeAudioEvent(
            wa_message_id="2",
            transcription="하세요",
            transcription_language="ko",
            body="하세요",
        ),
    ]
    reject, lang, text = audio_events_unsupported_language(events)  # type: ignore[arg-type]
    assert reject is True
    assert lang == "ko"
    assert "안녕" in text


def test_mixed_supported_and_unsupported_keeps_supported() -> None:
    events = [
        _FakeAudioEvent(
            wa_message_id="1",
            transcription="Quiero reservar",
            transcription_language="es",
            body="Quiero reservar",
        ),
        _FakeAudioEvent(
            wa_message_id="2",
            transcription="안녕",
            transcription_language="ko",
            body="안녕",
        ),
    ]
    reject, lang, _text = audio_events_unsupported_language(events)  # type: ignore[arg-type]
    assert reject is False
    assert lang is None
    assert events[1].body == ""
    combined = combine_messages(events)  # type: ignore[arg-type]
    assert combined == "Quiero reservar"
