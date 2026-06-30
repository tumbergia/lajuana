"""Seed plugin registry for unified CLI.

Usage via CLI:
    python -m app.cli seed --type <name>

Available types:
    python -m app.cli seed --list

Legacy scripts (python -m scripts.seed_*) continue to work independently.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import logging

logger = logging.getLogger(__name__)

# ── Seed registry ────────────────────────────────────────────────────────────
# Maps seed type → (module_path, description)
# Each module must expose ``async def run_seed()``.
_seed_registry: dict[str, tuple[str, str]] = {}


def register_seed(name: str, module_path: str, description: str) -> None:
    """Register a seed module for CLI discovery."""
    _seed_registry[name] = (module_path, description)


def list_seeds() -> list[tuple[str, str]]:
    """Return (name, description) for all registered seeds."""
    return [(name, desc) for name, (_, desc) in _seed_registry.items()]


# ── Bootstrap all seeds ─────────────────────────────────────────────────────

def _bootstrap():
    """Register all known seed types."""
    register_seed(
        "reproducible",
        "scripts.seed_reproducible",
        "Full demo dataset (users, reservations, equines, …)",
    )
    register_seed(
        "equines",
        "scripts.seed_equines_rf14",
        "Upsert real equines from CVs.xlsx",
    )
    register_seed(
        "experiences",
        "scripts.seed_experiences_and_schedules_qa",
        "Upsert QA experiences",
    )
    register_seed(
        "form-test",
        "scripts.seed_form_test",
        "Test participant form data",
    )
    register_seed(
        "proof-file",
        "scripts.seed_proof_file_data",
        "Upload test payment proof files",
    )


_bootstrap()


# ── CLI helper ───────────────────────────────────────────────────────────────

def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach seed subcommand arguments to *parser*."""
    parser.add_argument(
        "--type",
        "-t",
        choices=list(_seed_registry.keys()),
        help="Seed type to run (omit to list available seeds)",
    )
    parser.add_argument(
        "--drop-first",
        action="store_true",
        help="Drop known collections before seeding (use with caution)",
    )


async def run_seed(args: argparse.Namespace) -> None:
    """Import and run the requested seed module."""
    entry = _seed_registry.get(args.type)
    if entry is None:
        available = ", ".join(_seed_registry.keys())
        logger.error("Unknown seed type '%s'. Available: %s", args.type, available)
        raise SystemExit(1)

    module_path, _ = entry
    try:
        mod = importlib.import_module(module_path)
    except ImportError as exc:
        logger.error("Failed to import seed module '%s': %s", module_path, exc)
        raise SystemExit(1) from exc

    logger.info("Running seed '%s' from %s …", args.type, module_path)
    await mod.run_seed()
    logger.info("Seed '%s' completed.", args.type)
