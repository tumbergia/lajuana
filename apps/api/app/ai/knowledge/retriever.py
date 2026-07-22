"""Retriever top-k sobre el índice de conocimiento La Juana (por idioma)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.ai.knowledge.chunking import normalize_kb_language
from app.ai.knowledge.embeddings import cosine_similarity, embed_texts
from app.ai.knowledge.indexer import ensure_index
from app.core.logging import logger

DEFAULT_TOP_K = 3
DEFAULT_MIN_SCORE = 0.25

_CTA_BY_LANG: dict[str, str] = {
    "es": "¿Te interesa saber más de las experiencias que ofrecemos o de nosotros?",
    "en": "Would you like to know more about the experiences we offer, or about us?",
    "fr": "Tu aimerais en savoir plus sur les expériences que nous proposons, ou sur nous ?",
    "de": "Möchtest du mehr über unsere Erlebnisse oder über uns erfahren?",
    "it": "Ti interessa saperne di più sulle esperienze che offriamo o su di noi?",
    "ru": "Хочешь узнать больше о наших впечатлениях или о нас?",
    "zh": "想进一步了解我们提供的体验，还是了解我们自己？",
    "ja": "私たちが提供する体験についてもっと知りたいですか？それとも私たち自身について？",
}

_EMPTY_BY_LANG: dict[str, str] = {
    "es": (
        "Ese detalle aún no lo tenemos publicado. "
        "Puedo ayudarte con nuestras experiencias, disponibilidad o una reserva."
    ),
    "en": (
        "We don't have that detail published yet. "
        "I can help with our experiences, availability, or a reservation."
    ),
    "fr": (
        "Ce détail n’est pas encore publié chez nous. "
        "Je peux t’aider avec nos expériences, la disponibilité ou une réservation."
    ),
    "de": (
        "Dieses Detail haben wir noch nicht veröffentlicht. "
        "Ich kann bei unseren Erlebnissen, Verfügbarkeit oder einer Reservierung helfen."
    ),
    "it": (
        "Quel dettaglio non è ancora pubblicato. "
        "Posso aiutarti con le nostre esperienze, disponibilità o una prenotazione."
    ),
    "ru": (
        "Эту деталь мы ещё не опубликовали. "
        "Могу помочь с нашими впечатлениями, доступностью или бронированием."
    ),
    "zh": "我们还没有公布该细节。我可以帮你了解我们的体验、档期或预订。",
    "ja": (
        "その詳細はまだ公開していません。"
        "体験・空き状況・予約のお手伝いができます。"
    ),
}

_ASSISTANT_NOTE_LINE = re.compile(
    r"(?i)(do not invent|no inventes|no las inventes|config(?:uración)? live|"
    r"config live|get_public_business_rules|assistant limits|"
    r"l[ií]mites para el asistente|exact address.*come from|"
    r"direcci[oó]n exacta.*sistema|deben tomarse de)"
)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    title: str
    text: str
    score: float


def _lexical_score(query: str, text: str) -> float:
    q_lower = query.lower()
    hay = text.lower()
    q_tokens = {t for t in q_lower.split() if len(t) > 2}
    if not q_tokens:
        return 0.0
    hits = sum(1 for t in q_tokens if t in hay)
    score = hits / len(q_tokens)
    # Términos clave: aunque el resto del query sea ruido, no devolver vacío.
    for term in (
        "juana",
        "horario",
        "horarios",
        "fundador",
        "fundadores",
        "jairo",
        "pamela",
        "unesco",
        "neira",
        "somos",
        "agencia",
        "opening",
        "hours",
    ):
        if term in q_lower and term in hay:
            score = max(score, 0.4)
    return score


def retrieve(
    query: str,
    *,
    language: str | None = "es",
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[RetrievedChunk]:
    """Devuelve los chunks más relevantes para `query` en el idioma de sesión."""
    q = (query or "").strip()
    if not q:
        return []

    lang = normalize_kb_language(language)
    chunks = ensure_index(lang)
    if not chunks:
        return []

    def _lexical_hits(min_s: float) -> list[RetrievedChunk]:
        scored_lex: list[RetrievedChunk] = []
        for ch in chunks:
            score = _lexical_score(q, f"{ch.get('title') or ''} {ch.get('text') or ''}")
            if score >= min_s:
                scored_lex.append(
                    RetrievedChunk(
                        chunk_id=str(ch.get("chunk_id") or ""),
                        title=str(ch.get("title") or ""),
                        text=str(ch.get("text") or ""),
                        score=float(score),
                    )
                )
        scored_lex.sort(key=lambda c: c.score, reverse=True)
        return scored_lex[: max(1, top_k)]

    scored: list[RetrievedChunk] = []
    try:
        query_vec = embed_texts([q])[0]
        for ch in chunks:
            emb = ch.get("embedding")
            if not emb or len(emb) != len(query_vec):
                score = _lexical_score(q, f"{ch.get('title') or ''} {ch.get('text') or ''}")
            else:
                score = cosine_similarity(query_vec, emb)
            if score >= min_score:
                scored.append(
                    RetrievedChunk(
                        chunk_id=str(ch.get("chunk_id") or ""),
                        title=str(ch.get("title") or ""),
                        text=str(ch.get("text") or ""),
                        score=float(score),
                    )
                )
    except Exception as exc:
        logger.warning("[knowledge] Vector retrieve failed (%s); lexical fallback", exc)
        return _lexical_hits(min_s=0.05)

    scored.sort(key=lambda c: c.score, reverse=True)
    hits = scored[: max(1, top_k)]
    if hits:
        return hits
    # Embeddings incompatibles / umbral alto → no dejar al usuario sin respuesta.
    logger.info("[knowledge] No vector hits for lang=%s; lexical fallback", lang)
    return _lexical_hits(min_s=0.05)


def _sanitize_user_facing_text(text: str) -> str:
    """Quita headings y notas internas del MD antes de enviar al usuario."""
    lines = text.splitlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        if (
            stripped.startswith("(")
            and stripped.endswith(")")
            and _ASSISTANT_NOTE_LINE.search(stripped)
        ):
            continue
        if _ASSISTANT_NOTE_LINE.search(stripped):
            continue
        cleaned.append(line)
    body = "\n".join(cleaned).strip()
    return re.sub(r"\n{3,}", "\n\n", body)


def format_knowledge_response(
    chunks: list[RetrievedChunk],
    *,
    language: str = "es",
) -> str:
    """Arma una respuesta user-facing (primera persona) + CTA en el idioma."""
    lang = normalize_kb_language(language)
    if not chunks:
        return _EMPTY_BY_LANG.get(lang, _EMPTY_BY_LANG["en"])

    parts: list[str] = []
    seen: set[str] = set()
    for ch in chunks:
        body = _sanitize_user_facing_text(ch.text.strip())
        if not body:
            continue
        key = body[:120]
        if key in seen:
            continue
        seen.add(key)
        parts.append(body)
        if len(parts) >= 2:
            break

    if not parts:
        return _EMPTY_BY_LANG.get(lang, _EMPTY_BY_LANG["en"])

    joined = "\n\n".join(parts)
    if len(joined) > 1000:
        joined = joined[:997].rstrip() + "…"

    cta = _CTA_BY_LANG.get(lang, _CTA_BY_LANG["en"])
    if cta not in joined:
        joined = f"{joined}\n\n{cta}"
    return joined
