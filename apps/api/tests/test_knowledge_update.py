"""Tests de la lógica de actualización de metadata del RAG (PATCH /knowledge/{id}).

Cubre _compute_metadata_changes (pura): qué se actualiza en el documento y qué
se propaga a los chunks según cambien title/scope.
"""

from __future__ import annotations

from app.services.knowledge_service import KnowledgeService

_compute = KnowledgeService._compute_metadata_changes


def test_scope_change_propagates_to_chunks() -> None:
    doc_changes, chunk_changes = _compute(
        current_title="Guía", current_scope="public", title=None, scope="ops"
    )
    assert doc_changes == {"scope": "ops"}
    assert chunk_changes == {"scope": "ops"}


def test_title_change_propagates_to_chunks() -> None:
    doc_changes, chunk_changes = _compute(
        current_title="Viejo", current_scope="public", title="Nuevo", scope=None
    )
    assert doc_changes == {"title": "Nuevo"}
    assert chunk_changes == {"title": "Nuevo"}


def test_title_is_stripped() -> None:
    doc_changes, _ = _compute(
        current_title="Viejo", current_scope="public", title="  Nuevo  ", scope=None
    )
    assert doc_changes == {"title": "Nuevo"}


def test_unchanged_values_produce_no_changes() -> None:
    doc_changes, chunk_changes = _compute(
        current_title="Guía", current_scope="public", title="Guía", scope="public"
    )
    assert doc_changes == {}
    assert chunk_changes == {}


def test_none_values_are_noop() -> None:
    doc_changes, chunk_changes = _compute(
        current_title="Guía", current_scope="public", title=None, scope=None
    )
    assert doc_changes == {}
    assert chunk_changes == {}


def test_blank_title_is_ignored() -> None:
    doc_changes, chunk_changes = _compute(
        current_title="Guía", current_scope="public", title="   ", scope=None
    )
    assert doc_changes == {}
    assert chunk_changes == {}


def test_both_title_and_scope_change() -> None:
    doc_changes, chunk_changes = _compute(
        current_title="A", current_scope="public", title="B", scope="ops"
    )
    assert doc_changes == {"title": "B", "scope": "ops"}
    assert chunk_changes == {"title": "B", "scope": "ops"}
