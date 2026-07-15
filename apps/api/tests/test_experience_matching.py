"""Tests for the fuzzy matching used by get_experience_detail.

Validates:
- Exact match
- Substring match (query is substring of name)
- Substring match (name is substring of query)
- Word-level match (all query words match some name word)
- Singular/plural variants (cemento <-> cementos)
- Partial word matches
- Stopword handling
- Score threshold (returns None for bad matches)
- find_best_experience returns the best match
"""

from __future__ import annotations

from app.ai.mcp.tools import (
    _find_best_experience,
    _is_singular_plural_variant,
    _match_score,
    _normalize_text,
    _word_matches,
)

# ── _normalize_text ──────────────────────────────────────────────────────


def test_normalize_strips_accents() -> None:
    assert _normalize_text("Fábrica") == "fabrica"
    assert _normalize_text("Montaña") == "montana"
    assert _normalize_text("Niños") == "ninos"


def test_normalize_lowercases() -> None:
    assert _normalize_text("CABALGATA") == "cabalgata"


def test_normalize_strips_trailing_punctuation() -> None:
    assert _normalize_text("Fábrica de Cementos!!!") == "fabrica de cementos"
    assert _normalize_text("  espacios  ") == "espacios"


# ── _is_singular_plural_variant ──────────────────────────────────────────


def test_singular_plural_basic() -> None:
    assert _is_singular_plural_variant("cemento", "cementos") is True
    assert _is_singular_plural_variant("cementos", "cemento") is True


def test_singular_plural_with_es_suffix() -> None:
    assert _is_singular_plural_variant("cristal", "cristales") is True
    assert _is_singular_plural_variant("montana", "montanas") is True
    assert _is_singular_plural_variant("fabrica", "fabricas") is True
    assert _is_singular_plural_variant("mula", "mulas") is True
    assert _is_singular_plural_variant("experiencia", "experiencias") is True


def test_singular_plural_too_short() -> None:
    assert _is_singular_plural_variant("dia", "dias") is False
    assert _is_singular_plural_variant("a", "as") is False


def test_singular_plural_not_a_pair() -> None:
    assert _is_singular_plural_variant("cemento", "chorros") is False
    assert _is_singular_plural_variant("casa", "perro") is False


# ── _word_matches ───────────────────────────────────────────────────────


def test_word_matches_exact() -> None:
    assert _word_matches("cemento", "cemento") is True


def test_word_matches_substring() -> None:
    assert _word_matches("cement", "cemento") is True
    assert _word_matches("cemento", "cement") is True


def test_word_matches_singular_plural() -> None:
    assert _word_matches("cemento", "cementos") is True
    assert _word_matches("cristal", "cristales") is True


def test_word_matches_no_match() -> None:
    assert _word_matches("xyz", "cemento") is False
    assert _word_matches("cemento", "xyz") is False


def test_word_matches_empty() -> None:
    assert _word_matches("", "cemento") is False
    assert _word_matches("cemento", "") is False


# ── _match_score ────────────────────────────────────────────────────────


def test_score_exact_match() -> None:
    score = _match_score("Fabrica de Cementos", "Fabrica de Cementos")
    assert score == 1.0


def test_score_query_is_substring() -> None:
    score = _match_score("La Montana de Cristal", "Montana de Cristal")
    assert score >= 0.9


def test_score_name_is_substring() -> None:
    score = _match_score("Chorros", "Los Chorros")
    assert score >= 0.8


def test_score_word_match_with_stopwords() -> None:
    score = _match_score("Fabrica de Cemento", "de Fabrica de Cemento")
    assert score >= 0.7


def test_score_singular_plural() -> None:
    score = _match_score("Fabrica de Cemento", "Fabrica de Cementos")
    assert score >= 0.5


def test_score_no_match() -> None:
    score = _match_score("Fabrica de Cemento", "xyz123 abc456")
    assert score == 0.0


def test_score_empty_inputs() -> None:
    assert _match_score("", "query") == 0.0
    assert _match_score("name", "") == 0.0
    assert _match_score("", "") == 0.0


# ── _find_best_experience ──────────────────────────────────────────────


class _FakeExp:
    def __init__(self, name: str, aliases: list[str] | None = None) -> None:
        self.name = name
        self.aliases = aliases or []


_EXPS = [
    _FakeExp("Cabalgata Basica"),
    _FakeExp("Los Chorros"),
    _FakeExp("La Montana de Cristal"),
    _FakeExp("Fabrica de Cemento", aliases=["Fabrica de Cementos", "Cementos"]),
]


def test_find_best_singular_vs_plural() -> None:
    """The bug from the user report: 'Fábrica de Cementos' must find 'Fábrica de Cemento'."""
    result, score = _find_best_experience(_EXPS, "Fabrica de Cementos", lambda e: e.name)
    assert result is not None
    assert result.name == "Fabrica de Cemento"
    assert score >= 0.5


def test_find_best_partial_word() -> None:
    result, score = _find_best_experience(_EXPS, "chorros", lambda e: e.name)
    assert result is not None
    assert result.name == "Los Chorros"
    assert score >= 0.5


def test_find_best_with_accents() -> None:
    result, score = _find_best_experience(_EXPS, "Fábrica de cemento", lambda e: e.name)
    assert result is not None
    assert result.name == "Fabrica de Cemento"
    assert score >= 0.5


def test_find_best_no_match_returns_none() -> None:
    result, score = _find_best_experience(_EXPS, "xyz123", lambda e: e.name)
    assert result is None
    assert score < 0.5


def test_find_best_empty_query() -> None:
    result, score = _find_best_experience(_EXPS, "", lambda e: e.name)
    assert result is None


def test_find_best_empty_candidates() -> None:
    result, score = _find_best_experience([], "anything", lambda e: e.name)
    assert result is None


def test_find_best_picks_highest_score() -> None:
    """When multiple candidates match, the best one wins."""
    exps = [
        _FakeExp("Fabrica"),
        _FakeExp("Fabrica de Cemento"),
    ]
    result, score = _find_best_experience(exps, "Fabrica de Cemento", lambda e: e.name)
    assert result is not None
    assert result.name == "Fabrica de Cemento"
    assert score == 1.0
