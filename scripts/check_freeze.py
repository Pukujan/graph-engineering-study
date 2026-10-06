#!/usr/bin/env python3
"""Check a benchmark freeze record is complete before either arm runs.

Exit code 0 means the record satisfies every required field and the experiment
may start; exit code 1 lists the fields still missing or invalid. Deterministic
by construction: no inference decides whether the freeze is complete.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.benchmark import check_freeze  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", help="path to a benchmark freeze record JSON file")
    args = parser.parse_args()

    record = json.loads(Path(args.record).read_text(encoding="utf-8"))
    missing = check_freeze(record)
    if missing:
        print(f"INCOMPLETE freeze record: {len(missing)} field(s) unset or invalid")
        for path in missing:
            print(f"  - {path}")
        return 1

    print("COMPLETE freeze record: the experiment may start")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
