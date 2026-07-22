"""CLI: construye el índice vectorial del MD corporativo (todos los idiomas).

Uso (desde apps/api):
  python -m scripts.index_company_knowledge
  python -m scripts.index_company_knowledge --force
  python -m scripts.index_company_knowledge --lang en --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Index La Juana company knowledge MD")
    parser.add_argument("--force", action="store_true", help="Rebuild even if up to date")
    parser.add_argument(
        "--lang",
        default=None,
        help="Solo un idioma (es/en/fr/de/it/ru/zh/ja). Por defecto: todos.",
    )
    args = parser.parse_args()

    from app.ai.knowledge.indexer import build_all_indexes, build_index, index_path

    if args.lang:
        path = build_index(language=args.lang, force=args.force)
        print(f"Index written: {path or index_path(args.lang)}")
    else:
        paths = build_all_indexes(force=args.force)
        for path in paths:
            print(f"Index written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
