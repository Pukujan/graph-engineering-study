#!/usr/bin/env python3
"""Check observed before/after decisions against the metamorphic relations.

Reads a JSON file of ``{relation, before, after}`` observations and reports any
that violate their relation. Exit code 1 lists the violations. Deterministic:
each relation is a fixed structural check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.metamorphic import check_relations  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", help="JSON file of metamorphic observations")
    args = parser.parse_args()

    data = json.loads(Path(args.observations).read_text(encoding="utf-8"))
    observations = data.get("observations") if isinstance(data, dict) else data

    problems = check_relations(observations)
    if problems:
        print(f"VIOLATIONS: {len(problems)}")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"OK: {len(observations)} observation(s) satisfy their relations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
