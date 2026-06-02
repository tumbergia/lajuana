#!/usr/bin/env python3
"""Unified CLI for La Juana API.

Usage:
    python -m app.cli seed --type <name>
    python -m app.cli seed         → list available seeds
    python -m app.cli seed --help
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import app.cli.seed as seed_module

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(name)s  %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="La Juana API — CLI tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Run a seed or list available seeds")
    seed_module.add_arguments(seed_parser)

    args = parser.parse_args()

    if args.command == "seed":
        if args.type is None:
            print("Available seeds:")
            for name, desc in seed_module.list_seeds():
                print(f"  {name:20s}  {desc}")
            sys.exit(0)

        asyncio.run(seed_module.run_seed(args))


if __name__ == "__main__":
    main()
