#!/usr/bin/env python3
"""Compare the two arms' decision evidence and require every difference classified.

Feeds identical requests to both arms, normalizes the decisions, flags semantic
differences, and refuses to pass while any difference is unclassified. Exit code
1 lists unclassified or invalid differences. Deterministic: structural
comparison only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.differential import (  # noqa: E402
    check_classifications,
    compare,
    differences,
    load_arm,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm_a", help="arm A evidence JSON")
    parser.add_argument("arm_b", help="arm B evidence JSON")
    parser.add_argument(
        "--classifications",
        default=None,
        help="JSON mapping request_id -> classification for every difference",
    )
    parser.add_argument("--out", default=None, help="write the comparison JSON here")
    args = parser.parse_args()

    comparison = compare(load_arm(args.arm_a), load_arm(args.arm_b))
    diffs = differences(comparison)

    if args.out:
        Path(args.out).write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")

    print(f"{len(comparison) - len(diffs)}/{len(comparison)} requests agree; {len(diffs)} differ")

    classifications = {}
    if args.classifications:
        classifications = json.loads(Path(args.classifications).read_text(encoding="utf-8"))

    problems = check_classifications(comparison, classifications)
    if problems:
        print(f"UNCLASSIFIED: {len(problems)} difference(s) need a classification")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    for entry in diffs:
        print(f"  {entry['request_id']}: {classifications[entry['request_id']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
