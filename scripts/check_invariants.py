#!/usr/bin/env python3
"""Check a formal-invariant registry is fully specified before scoring.

Every record must name its method, property, model boundary, assumptions,
counterexample behavior, and implementation links. Exit code 1 lists the
problems; exit code 0 means every named invariant is tied down. Deterministic:
no inference decides whether a proof is fully specified.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.formal import check_invariants  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", help="path to a formal-invariant registry JSON file")
    args = parser.parse_args()

    data = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    records = data.get("invariants") if isinstance(data, dict) else data

    problems = check_invariants(records)
    if problems:
        print(f"INCOMPLETE invariant registry: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"COMPLETE invariant registry: {len(records)} invariant(s) specified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
