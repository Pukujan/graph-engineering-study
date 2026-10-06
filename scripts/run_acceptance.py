#!/usr/bin/env python3
"""Replay calibration acceptance cases against a running arm.

Speaks only the contract.md surface, so the same cases produce comparable
evidence for both arms. Writes JSON evidence and exits non-zero if any case
fails. Deterministic: a case passes on HTTP status and JSON subset alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.acceptance import run_all  # noqa: E402
from graph_study.cases import load_cases  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="root URL of the running arm")
    parser.add_argument("--cases", required=True, help="directory of case JSON files")
    parser.add_argument("--out", default=None, help="write JSON evidence to this path")
    args = parser.parse_args()

    cases = [record for _, record in load_cases(Path(args.cases))]
    summary = run_all(args.base_url, cases)

    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"{summary['passed']}/{summary['total']} passed")
    for result in summary["results"]:
        if not result["passed"]:
            print(f"  FAIL {result['case_id']}: {'; '.join(result['detail'])}")

    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
