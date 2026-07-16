from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

from faster_whisper import WhisperModel

from app.core.config import settings
from app.core.logging import logger

_MODEL: WhisperModel | None = None


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    language_probability: float | None
    duration: float | None


def _get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:
        logger.info(
            "[whisper] Loading model '%s' on %s (compute=%s)...",
            settings.whisper_model_size,
            settings.whisper_device,
            settings.whisper_compute_type,
        )
        _MODEL = WhisperModel(
            model_size_or_path=settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
        logger.info("[whisper] Model loaded")
    return _MODEL


def unload_model() -> None:
    global _MODEL
    if _MODEL is not None:
        _MODEL = None
        logger.info("[whisper] Model unloaded")


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> TranscriptionResult:
    model = _get_model()
    ext = _ext_from_mime(mime_type)

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            language=settings.whisper_language,
            beam_size=settings.whisper_beam_size,
            condition_on_previous_text=False,
            vad_filter=True,
        )

        detected_lang = info.language
        detected_prob = info.language_probability

        logger.debug(
            "[whisper] Transcribed %.1fs | detected language=%s (p=%.2f)",
            info.duration or 0,
            detected_lang,
            detected_prob or 0,
        )

        text_parts: list[str] = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        text = " ".join(text_parts)
        return TranscriptionResult(
            text=text,
            language=detected_lang,
            language_probability=detected_prob,
            duration=info.duration,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _ext_from_mime(mime_type: str) -> str:
    mapping = {
        "audio/ogg": "ogg",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/mp4": "m4a",
        "audio/amr": "amr",
        "audio/wav": "wav",
        "audio/webm": "webm",
    }
    return mapping.get(mime_type, "ogg")
