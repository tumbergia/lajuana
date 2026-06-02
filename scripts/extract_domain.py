#!/usr/bin/env python3
"""Extract domain models + repository interfaces into ``mobile_domain``.

Steps
-----
1. Copy model files from ``features/*/domain/`` to ``packages/mobile_domain/``
2. Update imports inside copied files
3. Replace originals with re-exports
4. Update ALL imports in ``apps/mobile/`` to point to ``package:mobile_domain/``
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOBILE_LIB = os.path.join(REPO_ROOT, "apps", "mobile", "lib")
DOMAIN_PKG = os.path.join(REPO_ROOT, "packages", "mobile_domain")

# Mapping: feature -> (model_files, repo_interface)
# Each entry lists source paths relative to lib/features/<feature>/
FEATURES: dict[str, dict[str, list[str]]] = {
    "reservations": {
        "models": [
            "domain/models/reservation_detail.dart",
            "domain/models/reservation_list_item.dart",
            "domain/models/reservation_participant_detail.dart",
            "domain/models/reservation_payment_proof_detail.dart",
            "domain/models/reservation_payment_summary.dart",
            "domain/models/reservation_timeline_event.dart",
            "domain/models/reservation_operational_alert.dart",
        ],
        "repos": [
            "domain/repositories/reservations_repository.dart",
        ],
    },
    "saddles": {
        "models": [
            "domain/models/saddle_list_item.dart",
        ],
        "repos": [
            "domain/repositories/saddles_repository.dart",
        ],
    },
    "equines": {
        "models": [
            "domain/models/equine.dart",
            "domain/models/equine_experience_fit.dart",
            "domain/models/equine_operational_status.dart",
            "domain/models/equine_timeline_entry.dart",
        ],
        "repos": [
            "domain/repositories/equine_repository.dart",
        ],
    },
    "assignments": {
        "models": [
            "domain/models/assignment.dart",
            "domain/models/assignment_board.dart",
        ],
        "repos": [
            "domain/repositories/assignments_repository.dart",
        ],
    },
}


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _find_dart_files(root: str) -> list[str]:
    files = []
    if not os.path.isdir(root):
        return files
    for dirpath, _, names in os.walk(root):
        for n in names:
            if n.endswith(".dart"):
                files.append(os.path.join(dirpath, n))
    return sorted(files)


def _resolve_src_path(feature: str, rel_path: str) -> str:
    """Convert e.g. ``domain/models/foo.dart`` to ``src/<feature>/foo.dart``."""
    basename = os.path.basename(rel_path)
    return f"src/{feature}/{basename}"


def _old_pkg_prefix(feature: str) -> str:
    return f"package:mobile/features/{feature}/"


def _new_pkg_prefix(feature: str) -> str:
    return f"package:mobile_domain/src/{feature}/"


def _is_domain_path(rel_path: str) -> bool:
    """True if the file is being extracted (in ``FEATURES``)."""
    for info in FEATURES.values():
        if rel_path in info["models"] or rel_path in info["repos"]:
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract domain into mobile_domain")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # ── Build replacement maps ───────────────────────────────────
    # For files BEING MOVED: old pkg:mobile/features/X/ -> new pkg:mobile_domain/src/X/
    move_replacements: list[tuple[str, str]] = []
    for feature in FEATURES:
        old = _old_pkg_prefix(feature)
        new = _new_pkg_prefix(feature)
        move_replacements.append((old, new))

    # For files STAYING in apps/mobile: pkg:mobile/features/X/domain/ -> pkg:mobile_domain/src/X/
    stay_replacements: list[tuple[str, str]] = []
    for feature in FEATURES:
        for rel_path in FEATURES[feature]["models"] + FEATURES[feature]["repos"]:
            domain_part = os.path.splitext(rel_path)[0]  # e.g. "domain/models/foo"
            old = f"package:mobile/features/{feature}/{domain_part}"
            new_src = _resolve_src_path(feature, rel_path)
            new_path = os.path.splitext(new_src)[0]
            stay_replacements.append((old, new_path))

    # ── 1. Copy files to mobile_domain ──────────────────────────
    total_copied = 0
    for feature, info in FEATURES.items():
        for group in ("models", "repos"):
            for rel_path in info[group]:
                src = os.path.join(MOBILE_LIB, "features", feature, rel_path)
                if not os.path.isfile(src):
                    print(f"  SKIP (missing): {src}")
                    continue
                dst_rel = _resolve_src_path(feature, rel_path)
                dst = os.path.join(DOMAIN_PKG, "lib", dst_rel)
                if args.dry_run:
                    print(f"  COPY {rel_path} -> {dst_rel}")
                else:
                    content = _read_file(src)
                    # Update imports within the moved file
                    for old, new in move_replacements:
                        content = content.replace(old, new)
                    # Fix sibling imports to files at src/ level (reservation_status, assignment_status)
                    content = content.replace(
                        "import 'reservation_status.dart';",
                        "import '../reservation_status.dart';",
                    )
                    content = content.replace(
                        "import 'assignment_status.dart';",
                        "import '../assignment_status.dart';",
                    )
                    _write_file(dst, content)
                    total_copied += 1

    print(f"\n{'DRY-RUN: ' if args.dry_run else ''}Copied {total_copied} files to mobile_domain")

    # ── 2. Replace originals with re-exports ─────────────────────
    total_reexport = 0
    for feature, info in FEATURES.items():
        for group in ("models", "repos"):
            for rel_path in info[group]:
                src = os.path.join(MOBILE_LIB, "features", feature, rel_path)
                if not os.path.isfile(src):
                    continue
                dst_rel = _resolve_src_path(feature, rel_path)
                pkg_path = os.path.splitext(dst_rel.replace(os.sep, "/"))[0]
                export_line = f"export 'package:mobile_domain/{pkg_path}';\n"
                if args.dry_run:
                    print(f"  RE-EXPORT {rel_path} -> {export_line.strip()}")
                else:
                    _write_file(src, export_line)
                    total_reexport += 1

    print(f"{'DRY-RUN: ' if args.dry_run else ''}Re-exported {total_reexport} originals")

    # ── 3. Update all imports in apps/mobile/lib + test ──────────
    total_updates = 0
    scan_roots = [
        os.path.join(MOBILE_LIB, "features"),
        os.path.join(MOBILE_LIB, "app"),
        os.path.join(MOBILE_LIB, "..", "test"),
    ]
    for root in scan_roots:
        for filepath in _find_dart_files(root):
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            new_content = content
            for old, new in stay_replacements:
                new_content = new_content.replace(old, new)
            if new_content != content:
                count = sum(1 for a, b in zip(content.splitlines(), new_content.splitlines()) if a != b)
                total_updates += count
                if not args.dry_run:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                if args.dry_run or True:
                    rel = os.path.relpath(filepath, MOBILE_LIB)
                    if count > 0:
                        pass  # too verbose for full output

    print(f"{'DRY-RUN: ' if args.dry_run else ''}Updated {total_updates} imports across apps/mobile")

    # ── 4. Update barrel export ──────────────────────────────────
    barrel = os.path.join(DOMAIN_PKG, "lib", "mobile_domain.dart")
    if not args.dry_run:
        exports = []
        for feature, info in FEATURES.items():
            for group in ("models", "repos"):
                for rel_path in info[group]:
                    dst_rel = _resolve_src_path(feature, rel_path)
                    pkg_path = os.path.splitext(dst_rel.replace(os.sep, "/"))[0]
                    exports.append(f"export '{pkg_path}';")
        new_barrel = "\n".join(sorted(exports))
        existing = _read_file(barrel) if os.path.isfile(barrel) else ""
        if new_barrel not in existing:
            with open(barrel, "a", encoding="utf-8") as f:
                f.write("\n\n// -- Extracted from apps/mobile (domain layer) --\n")
                f.write(new_barrel)
                f.write("\n")
            print(f"\nUpdated barrel: {barrel}")

    print("\nDone.")


if __name__ == "__main__":
    main()
