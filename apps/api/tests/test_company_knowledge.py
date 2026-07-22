"""Tests: intent router + retrieval del KB corporativo (i18n)."""

from __future__ import annotations

import os

os.environ.setdefault("KNOWLEDGE_EMBEDDING_MODE", "hash")

from app.ai.assistant.intent_router import detect_and_build_plan
from app.ai.knowledge.chunking import load_source_chunks, split_markdown_sections
from app.ai.knowledge.indexer import build_index, ensure_index
from app.ai.knowledge.retriever import format_knowledge_response, retrieve
from app.schemas.assistant_plan import AssistantAction


def test_md_chunks_into_sections() -> None:
    chunks = load_source_chunks("es")
    assert len(chunks) >= 5
    assert all(c.language == "es" for c in chunks)
    assert any("somos" in c.text.lower() for c in chunks)
    assert not any("límites para el asistente" in c.title.lower() for c in chunks)


def test_split_markdown_ignores_tiny_headings() -> None:
    md = "# A\n\n## Tiny\n\nx\n\n## Real section with enough body text here\n\nMore text.\n"
    chunks = split_markdown_sections(md)
    assert any("Real section" in c.title for c in chunks)


def test_retrieve_founders_returns_relevant_chunk() -> None:
    build_index(language="es", force=True)
    assert ensure_index("es")
    hits = retrieve(
        "quiénes son Jairo y Pamela fundadores",
        language="es",
        top_k=3,
        min_score=0.0,
    )
    assert hits, "expected at least one chunk"
    blob = " ".join(h.text.lower() for h in hits)
    assert "jairo" in blob or "pamela" in blob or "fundador" in blob
    assert "somos" in blob or "nuestros" in blob or "nacimos" in blob


def test_format_knowledge_response_adds_cta_first_person() -> None:
    build_index(language="es", force=True)
    hits = retrieve("descripcion general de la juana", language="es", top_k=2, min_score=0.0)
    msg = format_knowledge_response(hits, language="es")
    assert "somos" in msg.lower() or "nuestra" in msg.lower()
    assert "experiencias" in msg.lower()
    assert "?" in msg


def test_format_knowledge_response_empty() -> None:
    msg = format_knowledge_response([], language="es")
    assert "publicado" in msg.lower() or "experiencias" in msg.lower()


def test_english_kb_retrieve_and_cta() -> None:
    build_index(language="en", force=True)
    hits = retrieve("who founded La Juana Jairo Pamela", language="en", top_k=3, min_score=0.0)
    assert hits
    msg = format_knowledge_response(hits, language="en")
    assert "we " in msg.lower() or "our " in msg.lower()
    assert "experiences" in msg.lower() or "about us" in msg.lower()


def test_intent_founders_routes_to_company_knowledge() -> None:
    for msg in [
        "quiénes son Jairo y Pamela",
        "quiénes fundaron La Juana?",
        "qué es La Juana",
        "qué es el Paisaje Cultural Cafetero aquí",
        "cuéntame de la UNESCO",
        "historia de la arriería en La Juana",
        "mientras me revisan esto me gustaria preguntarte acerca de una descripcion general de la juana",
        "descripcion general de la juana",
    ]:
        plan = detect_and_build_plan(user_message=msg)
        assert plan is not None, msg
        assert plan.action == AssistantAction.TOOL_CALL, msg
        assert plan.tool_name == "search_company_knowledge", msg
        assert plan.arguments.query


def test_intent_what_is_experience_lists_catalog() -> None:
    plan = detect_and_build_plan(user_message="que es una experiencia")
    assert plan is not None
    assert plan.tool_name == "list_experiences"


def test_intent_vague_consiste_lists_catalog() -> None:
    plan = detect_and_build_plan(user_message="o en que consiste\nno entiendo")
    assert plan is not None
    assert plan.tool_name == "list_experiences"


def test_intent_location_still_public_rules() -> None:
    plan = detect_and_build_plan(user_message="dónde quedan?")
    assert plan is not None
    assert plan.tool_name == "get_public_business_rules"


def test_intent_booking_skips_rag() -> None:
    plan = detect_and_build_plan(
        user_message="quiero reservar la montaña de cristal para el 5 de agosto 3 personas"
    )
    assert plan is not None
    assert plan.tool_name == "check_availability_and_quote"
    assert plan.tool_name != "search_company_knowledge"
