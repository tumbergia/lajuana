from __future__ import annotations

from typing import Any

import pytest

from app.ai.providers import stt_provider
from app.ai.providers.stt_provider import TranscriptionResult, transcribe_audio


class _FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeInfo:
    def __init__(self, language: str, probability: float, duration: float) -> None:
        self.language = language
        self.language_probability = probability
        self.duration = duration


class _FakeWhisperModel:
    """Replica mínima de faster_whisper.WhisperModel.

    Captura los kwargs con los que se llamó a `transcribe` para que el test
    pueda verificar que el proveedor propaga `language=None` cuando
    `whisper_language` está desactivado.
    """

    last_kwargs: dict[str, Any] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def transcribe(
        self,
        audio_path: str,
        *,
        language: str | None = None,
        beam_size: int = 5,
        condition_on_previous_text: bool = True,
        vad_filter: bool = False,
        **_: Any,
    ) -> tuple[Any, _FakeInfo]:
        _FakeWhisperModel.last_kwargs = {
            "language": language,
            "beam_size": beam_size,
            "condition_on_previous_text": condition_on_previous_text,
            "vad_filter": vad_filter,
        }
        segments = [
            _FakeSegment("Quiero hacer una reserva"),
            _FakeSegment("para mañana"),
        ]
        info = _FakeInfo(language="es", probability=0.99, duration=4.5)
        return segments, info

    @classmethod
    def reset(cls) -> None:
        cls.last_kwargs = {}


def _patch_model(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeWhisperModel.reset()
    monkeypatch.setattr(stt_provider, "_MODEL", None)
    monkeypatch.setattr(stt_provider, "WhisperModel", _FakeWhisperModel)


def test_transcribe_audio_auto_detects_language(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Cuando `whisper_language` es None, el proveedor NO fuerza idioma."""
    _patch_model(monkeypatch)
    monkeypatch.setattr(stt_provider.settings, "whisper_language", None)
    monkeypatch.setattr(stt_provider.settings, "whisper_beam_size", 5)

    audio_bytes = b"fake-ogg-bytes"
    result = transcribe_audio(audio_bytes, mime_type="audio/ogg")

    assert isinstance(result, TranscriptionResult)
    assert result.text == "Quiero hacer una reserva para mañana"
    assert result.language == "es"
    assert result.language_probability == pytest.approx(0.99)
    assert result.duration == pytest.approx(4.5)

    # Verifica que NO se forzó idioma.
    assert _FakeWhisperModel.last_kwargs["language"] is None
    # Decodificación robusta: no encadenar contexto entre segmentos.
    assert _FakeWhisperModel.last_kwargs["condition_on_previous_text"] is False
    # VAD activo para cortar silencios y reducir alucinaciones.
    assert _FakeWhisperModel.last_kwargs["vad_filter"] is True


def test_transcribe_audio_forced_language(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Cuando `whisper_language` está fijo, el proveedor lo propaga."""
    _patch_model(monkeypatch)
    monkeypatch.setattr(stt_provider.settings, "whisper_language", "en")
    monkeypatch.setattr(stt_provider.settings, "whisper_beam_size", 3)

    result = transcribe_audio(b"fake-bytes", mime_type="audio/mp3")
    assert result.text == "Quiero hacer una reserva para mañana"
    assert _FakeWhisperModel.last_kwargs["language"] == "en"
    assert _FakeWhisperModel.last_kwargs["beam_size"] == 3


def test_transcribe_audio_empty_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Texto vacío no debe crashear; `transcribe_audio` lo retorna tal cual."""
    _patch_model(monkeypatch)

    class _EmptyWhisperModel(_FakeWhisperModel):
        def transcribe(self, audio_path: str, **_: Any) -> tuple[Any, _FakeInfo]:
            _FakeWhisperModel.last_kwargs = {"language": None}
            return [], _FakeInfo(language="es", probability=0.0, duration=0.0)

    monkeypatch.setattr(stt_provider, "WhisperModel", _EmptyWhisperModel)
    monkeypatch.setattr(stt_provider, "_MODEL", None)

    result = transcribe_audio(b"silence", mime_type="audio/ogg")
    assert result.text == ""
    assert result.language == "es"
    assert result.duration == 0.0
