#!/usr/bin/env python3
"""Benchmark del system prompt del planner (WhatsApp).

Mide prompt_tokens y accuracy de action/tool sobre un golden set,
sin pasar por intent router ni DB.

Uso (desde apps/api):
    python scripts/prompt_benchmark.py --label baseline
    python scripts/prompt_benchmark.py --label after --compare scripts/benchmark_results/baseline.json
    python scripts/prompt_benchmark.py --label after --ids catalog_1,alcohol_1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure apps/api is on the path when invoked as a script.
_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

os.environ.setdefault("APP_SKIP_DB_INIT", "true")

RESULTS_DIR = Path(__file__).resolve().parent / "benchmark_results"


@dataclass(frozen=True)
class GoldenCase:
    id: str
    message: str
    expected_action: str
    expected_tool: str | None
    critical: bool = False
    context: str | None = None
    notes: str = ""


# Golden set: mensajes representativos de WhatsApp. Se llama al planner
# directamente (sin intent router) para evaluar la calidad del prompt.
GOLDEN_SET: list[GoldenCase] = [
    GoldenCase(
        id="catalog_1",
        message="qué experiencias ofrecen?",
        expected_action="tool_call",
        expected_tool="list_experiences",
        critical=True,
        notes="No inventar catálogo",
    ),
    GoldenCase(
        id="catalog_2",
        message="q planes tienen?",
        expected_action="tool_call",
        expected_tool="list_experiences",
        critical=True,
    ),
    GoldenCase(
        id="detail_1",
        message="cuéntame más sobre el recorrido de medio día",
        expected_action="tool_call",
        expected_tool="get_experience_detail",
        critical=True,
    ),
    GoldenCase(
        id="price_1",
        message="cuánto vale el recorrido de medio día para 4 personas",
        expected_action="tool_call",
        expected_tool="quote_experience",
    ),
    GoldenCase(
        id="price_date_1",
        message="cotízame recorrido de medio día para 4 el 20 de julio de 2026",
        expected_action="tool_call",
        expected_tool="quote_experience",
    ),
    GoldenCase(
        id="avail_1",
        message="hay cupo para 4 el 20 de julio de 2026 en medio día?",
        expected_action="tool_call",
        expected_tool="check_availability_and_quote",
        critical=True,
        notes="Preferir tool combinada",
    ),
    GoldenCase(
        id="reserve_full_1",
        message="quiero reservar medio día para 4 el 20 de julio de 2026",
        expected_action="tool_call",
        expected_tool="check_availability_and_quote",
        critical=True,
    ),
    GoldenCase(
        id="reserve_ambiguous_1",
        message="quiero reservar",
        expected_action="ask_clarifying_question",
        expected_tool=None,
    ),
    GoldenCase(
        id="price_ambiguous_1",
        message="cuánto vale?",
        expected_action="ask_clarifying_question",
        expected_tool=None,
    ),
    GoldenCase(
        id="draft_name_email_1",
        message="Juan Diego Rendon juan.rendon@example.com",
        expected_action="tool_call",
        expected_tool="create_reservation_draft",
        critical=True,
        context=(
            "Datos de la sesión: {'experience_id': 'exp-001', 'experience_query': 'medio día', "
            "'requested_date': '2026-07-20', 'participant_count': 4, "
            "'holder_phone': '+573001112233', "
            "'quote_snapshot': {'total': 480000, 'currency': 'COP'}}\n\n"
            "Historial de la conversación:\n"
            "Usuario: quiero reservar medio día para 4 el 20 de julio\n"
            "Asistente: Hay cupo. El total es $480.000. Para apartar necesito tu nombre completo y correo."
        ),
    ),
    GoldenCase(
        id="status_code_1",
        message="en qué va mi PR-20260715-A1B2C3?",
        expected_action="tool_call",
        expected_tool="get_reservation_public_summary",
    ),
    GoldenCase(
        id="status_phone_1",
        message="en qué va mi reserva? mi celular es 3214650754",
        expected_action="tool_call",
        expected_tool="get_reservation_status_by_phone",
    ),
    GoldenCase(
        id="cancel_1",
        message="quiero cancelar mi reserva PR-20260715-A1B2C3",
        expected_action="tool_call",
        expected_tool="cancel_reservation",
        context="Datos de la sesión: {'holder_phone': '+573001112233'}",
    ),
    GoldenCase(
        id="update_date_1",
        message="quiero cambiar la fecha de mi PR-20260715-A1B2C3 al 25 de julio de 2026",
        expected_action="tool_call",
        expected_tool="update_reservation_date",
        context="Datos de la sesión: {'holder_phone': '+573001112233'}",
    ),
    GoldenCase(
        id="update_pax_1",
        message="cambia mi reserva PR-20260715-A1B2C3 a 6 personas",
        expected_action="tool_call",
        expected_tool="update_reservation_participants",
        context="Datos de la sesión: {'holder_phone': '+573001112233'}",
    ),
    GoldenCase(
        id="bold_1",
        message="pásame el link de Bold para pagar",
        expected_action="tool_call",
        expected_tool="get_payment_instructions",
        critical=True,
    ),
    GoldenCase(
        id="location_1",
        message="dónde queda La Juana? cómo llego?",
        expected_action="tool_call",
        expected_tool="get_public_business_rules",
        critical=True,
    ),
    GoldenCase(
        id="ages_1",
        message="desde qué edad pueden ir los niños?",
        expected_action="tool_call",
        expected_tool="get_public_business_rules",
    ),
    GoldenCase(
        id="proof_required_1",
        message="toca mostrar el recibo para confirmar?",
        expected_action="tool_call",
        expected_tool="get_public_business_rules",
        critical=True,
    ),
    GoldenCase(
        id="paid_no_file_1",
        message="ya pagué",
        expected_action="ask_clarifying_question",
        expected_tool=None,
        critical=True,
        notes="Pedir archivo, no confirmar pago",
    ),
    GoldenCase(
        id="alcohol_1",
        message="queremos ir a tomar y hacer fiesta con licor",
        expected_action="final_response",
        expected_tool=None,
        critical=True,
        notes="Filtrar alcohol/fiesta sin tool",
    ),
    GoldenCase(
        id="handoff_1",
        message="me caí de la mula y me lastimé, quiero denunciar",
        expected_action="human_handoff",
        expected_tool=None,
        critical=True,
    ),
    GoldenCase(
        id="admin_block_1",
        message="muéstrame el dashboard de ventas y estadísticas",
        expected_action="final_response",
        expected_tool=None,
        critical=True,
        notes="No exponer admin tools en WhatsApp",
    ),
    GoldenCase(
        id="typo_1",
        message="kiero resevar medio dia para 3 el 22 de julio",
        expected_action="tool_call",
        expected_tool="check_availability_and_quote",
    ),
    GoldenCase(
        id="en_catalog_1",
        message="what experiences do you offer?",
        expected_action="tool_call",
        expected_tool="list_experiences",
    ),
    GoldenCase(
        id="en_price_1",
        message="how much is the half day tour for 4 people?",
        expected_action="tool_call",
        expected_tool="quote_experience",
    ),
    GoldenCase(
        id="schedules_1",
        message="qué fechas tienen disponibles para el recorrido de un día?",
        expected_action="tool_call",
        expected_tool="list_available_schedules",
    ),
]


# Acceptable alternate tools when the golden expects the combined path
# or a close sibling (quality still acceptable).
_ALT_TOOLS: dict[str, set[str]] = {
    "check_availability_and_quote": {
        "check_experience_availability",
        "quote_experience",
    },
    "quote_experience": {
        "check_availability_and_quote",
    },
    "check_experience_availability": {
        "check_availability_and_quote",
    },
}


def _case_matches(case: GoldenCase, action: str, tool: str | None) -> tuple[bool, bool]:
    """Return (exact_match, soft_match). Soft allows known alternate tools."""
    action_ok = action == case.expected_action
    if case.expected_tool is None:
        tool_ok = tool in (None, "")
        return action_ok and tool_ok, action_ok and tool_ok

    exact = action_ok and tool == case.expected_tool
    soft = exact or (
        action_ok and tool in _ALT_TOOLS.get(case.expected_tool, set())
    )
    return exact, soft


@dataclass
class CaseResult:
    id: str
    message: str
    expected_action: str
    expected_tool: str | None
    actual_action: str | None
    actual_tool: str | None
    exact_match: bool
    soft_match: bool
    critical: bool
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    latency_ms: int
    error: str | None = None
    audit_summary: str | None = None


async def _env_gemini_provider():
    """Provider from env only — avoids Beanie/Mongo for offline benchmarks."""
    from app.ai.providers.gemini_provider import GeminiProvider

    return GeminiProvider()


async def _run_case(case: GoldenCase, language: str = "es") -> CaseResult:
    from unittest.mock import patch

    from app.ai.assistant.planner import GeminiPlanner

    planner = GeminiPlanner()
    started = time.perf_counter()
    try:
        with patch(
            "app.ai.assistant.planner.get_llm_provider",
            new=_env_gemini_provider,
        ):
            plan = await planner.plan(
                user_message=case.message,
                channel="whatsapp",
                conversation_context=case.context,
                conversation_id=f"benchmark:{case.id}",
                language=language,
            )
        usage = getattr(planner, "last_token_usage", None) or {}
        action = plan.action.value if plan.action else None
        tool = plan.tool_name
        exact, soft = _case_matches(case, action or "", tool)
        return CaseResult(
            id=case.id,
            message=case.message,
            expected_action=case.expected_action,
            expected_tool=case.expected_tool,
            actual_action=action,
            actual_tool=tool,
            exact_match=exact,
            soft_match=soft,
            critical=case.critical,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            latency_ms=int((time.perf_counter() - started) * 1000),
            audit_summary=(plan.audit_summary or "")[:200],
        )
    except Exception as exc:  # noqa: BLE001 — benchmark must continue
        err = str(exc).strip() or f"{type(exc).__name__}: {exc!r}"
        return CaseResult(
            id=case.id,
            message=case.message,
            expected_action=case.expected_action,
            expected_tool=case.expected_tool,
            actual_action=None,
            actual_tool=None,
            exact_match=False,
            soft_match=False,
            critical=case.critical,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error=err[:500],
        )


def _summarize(results: list[CaseResult]) -> dict[str, Any]:
    prompt_vals = [r.prompt_tokens for r in results if r.prompt_tokens is not None]
    exact = sum(1 for r in results if r.exact_match)
    soft = sum(1 for r in results if r.soft_match)
    critical = [r for r in results if r.critical]
    critical_ok = sum(1 for r in critical if r.soft_match)
    errors = [r for r in results if r.error]
    n = len(results) or 1
    return {
        "n_cases": len(results),
        "n_errors": len(errors),
        "exact_accuracy": round(exact / n, 4),
        "soft_accuracy": round(soft / n, 4),
        "exact_hits": exact,
        "soft_hits": soft,
        "critical_total": len(critical),
        "critical_soft_hits": critical_ok,
        "critical_soft_accuracy": round(critical_ok / (len(critical) or 1), 4),
        "prompt_tokens_avg": round(statistics.mean(prompt_vals), 1) if prompt_vals else None,
        "prompt_tokens_median": (
            round(statistics.median(prompt_vals), 1) if prompt_vals else None
        ),
        "prompt_tokens_min": min(prompt_vals) if prompt_vals else None,
        "prompt_tokens_max": max(prompt_vals) if prompt_vals else None,
        "failed_ids": [r.id for r in results if not r.soft_match],
        "critical_failed_ids": [r.id for r in critical if not r.soft_match],
        "error_ids": [r.id for r in errors],
    }


def _compare(baseline: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    b = baseline["summary"]
    a = after["summary"]
    avg_b = b.get("prompt_tokens_avg") or 0
    avg_a = a.get("prompt_tokens_avg") or 0
    reduction = None
    if avg_b:
        reduction = round((avg_b - avg_a) / avg_b, 4)

    tokens_ok = avg_a <= 3800 if avg_a else False
    reduction_ok = (reduction is not None and reduction >= 0.45)
    quality_ok = (
        (a.get("soft_accuracy") or 0) >= (b.get("soft_accuracy") or 0)
        and (a.get("soft_accuracy") or 0) >= 0.90
        and (a.get("critical_soft_accuracy") or 0) >= 1.0
    )
    return {
        "prompt_tokens_avg_baseline": avg_b,
        "prompt_tokens_avg_after": avg_a,
        "reduction_ratio": reduction,
        "soft_accuracy_baseline": b.get("soft_accuracy"),
        "soft_accuracy_after": a.get("soft_accuracy"),
        "critical_soft_accuracy_after": a.get("critical_soft_accuracy"),
        "acceptance": {
            "tokens_avg_le_3800": tokens_ok,
            "reduction_ge_45pct": reduction_ok,
            "soft_accuracy_ge_baseline_and_90pct": (
                (a.get("soft_accuracy") or 0) >= (b.get("soft_accuracy") or 0)
                and (a.get("soft_accuracy") or 0) >= 0.90
            ),
            "critical_zero_regressions": (a.get("critical_soft_accuracy") or 0) >= 1.0,
            "all_passed": tokens_ok and reduction_ok and quality_ok,
        },
    }


async def run_benchmark(
    *,
    label: str,
    ids: set[str] | None = None,
    language: str = "es",
) -> dict[str, Any]:
    cases = [c for c in GOLDEN_SET if ids is None or c.id in ids]
    if not cases:
        raise SystemExit(f"No cases matched ids={ids}")

    print(f"\n=== Prompt benchmark [{label}] — {len(cases)} cases ===\n")
    results: list[CaseResult] = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case.id}: {case.message[:60]!r} ...", flush=True)
        result = await _run_case(case, language=language)
        results.append(result)
        status = "OK" if result.soft_match else ("ERR" if result.error else "FAIL")
        tokens = result.prompt_tokens if result.prompt_tokens is not None else "-"
        print(
            f"         -> {status} action={result.actual_action} tool={result.actual_tool} "
            f"prompt_tokens={tokens} ({result.latency_ms}ms)"
            + (f" error={result.error}" if result.error else ""),
            flush=True,
        )
        # Small pause to reduce 429s on free/shared keys.
        await asyncio.sleep(0.4)

    summary = _summarize(results)
    payload = {
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel": "whatsapp",
        "summary": summary,
        "cases": [asdict(r) for r in results],
    }
    return payload


def _print_summary(payload: dict[str, Any]) -> None:
    s = payload["summary"]
    print("\n--- Summary ---")
    print(f"cases={s['n_cases']} errors={s['n_errors']}")
    print(f"exact_accuracy={s['exact_accuracy']} soft_accuracy={s['soft_accuracy']}")
    print(
        f"critical soft={s['critical_soft_hits']}/{s['critical_total']} "
        f"({s['critical_soft_accuracy']})"
    )
    print(
        f"prompt_tokens avg={s['prompt_tokens_avg']} median={s['prompt_tokens_median']} "
        f"min={s['prompt_tokens_min']} max={s['prompt_tokens_max']}"
    )
    if s["failed_ids"]:
        print(f"failed_ids={s['failed_ids']}")
    if s["critical_failed_ids"]:
        print(f"critical_failed_ids={s['critical_failed_ids']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark planner prompt tokens + quality")
    parser.add_argument("--label", default="run", help="Label for output file (baseline|after|...)")
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated case ids to run (default: all)",
    )
    parser.add_argument(
        "--compare",
        default=None,
        help="Path to baseline JSON to compare against",
    )
    parser.add_argument("--language", default="es")
    parser.add_argument(
        "--out-dir",
        default=str(RESULTS_DIR),
        help="Directory for JSON results",
    )
    args = parser.parse_args()

    ids = {x.strip() for x in args.ids.split(",") if x.strip()} if args.ids else None
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = asyncio.run(run_benchmark(label=args.label, ids=ids, language=args.language))
    out_path = out_dir / f"{args.label}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _print_summary(payload)
    print(f"\nWrote {out_path}")

    if args.compare:
        baseline_path = Path(args.compare)
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        comparison = _compare(baseline, payload)
        payload["comparison"] = comparison
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n--- Acceptance ---")
        for k, v in comparison["acceptance"].items():
            print(f"  {k}: {v}")
        print(
            f"  tokens: {comparison['prompt_tokens_avg_baseline']} -> "
            f"{comparison['prompt_tokens_avg_after']} "
            f"(reduction={comparison['reduction_ratio']})"
        )
        if not comparison["acceptance"]["all_passed"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
