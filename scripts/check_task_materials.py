#!/usr/bin/env python3
"""Check a freeze record's task-material pins match the materials on disk.

Re-seals the shared bundle and validates the sealed holdout manifest against the
digests in the record. Exit code 1 on any mismatch, or on unset pins unless
``--allow-incomplete`` is given (used by CI against the template). Deterministic:
no inference decides whether the materials are pinned.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.benchmark import check_task_materials  # noqa: E402

DEFAULT_SHARED = ROOT / "benchmark" / "calibration" / "shared"
DEFAULT_HOLDOUTS = ROOT / "benchmark" / "calibration" / "holdouts.manifest.sha256"


def _unset(record: object, path: str) -> bool:
    node = record
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return True
        node = node[part]
    return node is None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", help="path to a benchmark freeze record JSON file")
    parser.add_argument("--shared", default=str(DEFAULT_SHARED))
    parser.add_argument("--holdouts", default=str(DEFAULT_HOLDOUTS))
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="treat unset pins as non-fatal (for the template in CI)",
    )
    args = parser.parse_args()

    record = json.loads(Path(args.record).read_text(encoding="utf-8"))

    unset = [
        field
        for field in ("task_materials.package_sha256", "holdouts.manifest_sha256")
        if _unset(record, field)
    ]
    if unset and not args.allow_incomplete:
        print(f"UNPINNED: {', '.join(unset)} not set in the freeze record")
        return 1

    problems = check_task_materials(record, Path(args.shared), Path(args.holdouts))
    if problems:
        print(f"MISMATCH: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if unset:
        print(f"OK (incomplete): {', '.join(unset)} not set; nothing to verify")
        return 0

    print("PINNED: task materials match the freeze record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
