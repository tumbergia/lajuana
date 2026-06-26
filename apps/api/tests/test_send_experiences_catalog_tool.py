"""Tests for send_experiences_catalog tool (Fase B: envío de catálogo PDF).

Cubre: catálogo disponible, no encontrado en storage, y deshabilitado por config.
Usa el LocalStorageAdapter real sobre tmp_path (mismo patrón que test_storage.py).
"""

from __future__ import annotations

import asyncio

import pytest

from app.ai.mcp.tools.catalog import send_experiences_catalog


def _point_storage_to(monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
    monkeypatch.setattr(
        "app.services.storage.settings.storage_local_root", str(tmp_path)
    )
    # Asegura el adaptador local (sin credenciales S3).
    monkeypatch.setattr(
        "app.services.storage.settings.storage_s3_access_key_id", None
    )
    monkeypatch.setattr(
        "app.services.storage.settings.storage_s3_secret_access_key", None
    )


def test_returns_attachment_when_catalog_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """PDF presente en storage → catalog_available=True con la referencia al adjunto."""
    _point_storage_to(monkeypatch, tmp_path)
    storage_key = "catalogs/experiencias-muleras.pdf"
    monkeypatch.setattr(
        "app.core.config.settings.whatsapp_experiences_catalog_enabled", True
    )
    monkeypatch.setattr(
        "app.core.config.settings.whatsapp_experiences_catalog_storage_key", storage_key
    )

    pdf_path = tmp_path / "catalogs"
    pdf_path.mkdir(parents=True)
    (pdf_path / "experiencias-muleras.pdf").write_bytes(b"%PDF-1.4 fake")

    result = asyncio.run(send_experiences_catalog(trace_id="t-1"))

    assert result["catalog_available"] is True
    assert result["attachment"] is not None
    assert result["attachment"]["storage_key"] == storage_key
    assert result["attachment"]["mime_type"] == "application/pdf"
    assert not result["blocking_reasons"]


def test_returns_unavailable_when_pdf_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """PDF ausente → catalog_available=False y blocking_reason catalog_not_found."""
    _point_storage_to(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.core.config.settings.whatsapp_experiences_catalog_enabled", True
    )
    monkeypatch.setattr(
        "app.core.config.settings.whatsapp_experiences_catalog_storage_key",
        "catalogs/missing.pdf",
    )

    result = asyncio.run(send_experiences_catalog(trace_id="t-2"))

    assert result["catalog_available"] is False
    assert result["attachment"] is None
    assert result["blocking_reasons"][0]["code"] == "catalog_not_found"


def test_returns_unavailable_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Catálogo deshabilitado por config → catalog_available=False sin tocar storage."""
    _point_storage_to(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.core.config.settings.whatsapp_experiences_catalog_enabled", False
    )

    result = asyncio.run(send_experiences_catalog(trace_id="t-3"))

    assert result["catalog_available"] is False
    assert result["blocking_reasons"][0]["code"] == "catalog_disabled"


def test_orchestrator_extracts_outbound_document_from_attachment() -> None:
    """El output con attachment se convierte en OutboundDocumentRef."""
    from app.ai.assistant.orchestrator import AssistantOrchestrator

    tool_output = {
        "catalog_available": True,
        "attachment": {
            "storage_key": "catalogs/x.pdf",
            "filename": "Catalogo.pdf",
            "mime_type": "application/pdf",
            "caption": "Catálogo",
        },
    }
    ref = AssistantOrchestrator._extract_outbound_document(tool_output)
    assert ref is not None
    assert ref.storage_key == "catalogs/x.pdf"
    assert ref.filename == "Catalogo.pdf"


def test_orchestrator_extracts_none_without_attachment() -> None:
    """Sin attachment (o catálogo no disponible) no se adjunta documento."""
    from app.ai.assistant.orchestrator import AssistantOrchestrator

    assert AssistantOrchestrator._extract_outbound_document({"catalog_available": False}) is None
    assert AssistantOrchestrator._extract_outbound_document({}) is None


def test_policy_allows_catalog_tool_on_whatsapp() -> None:
    """send_experiences_catalog debe estar permitida para clientes (WhatsApp)."""
    from app.ai.assistant.policy import ToolPolicyEngine
    from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel

    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="send_experiences_catalog",
        arguments={},
        risk_level=RiskLevel.LOW,
        user_goal="Pedir el catálogo en PDF.",
        audit_summary="El usuario pidió el catálogo en PDF.",
    )

    decision = ToolPolicyEngine().validate(plan, channel="whatsapp")

    assert decision.allowed is True
