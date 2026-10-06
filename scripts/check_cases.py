#!/usr/bin/env python3
"""Check calibration acceptance cases against the contract and invariant registry.

Every case must be well-formed, cite a real contract section, and (if it names
one) a registered invariant. Exit code 1 lists the problems; exit code 0 means
every case is valid and every reference resolves. Deterministic: no inference
decides whether a case is well-formed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.cases import (  # noqa: E402
    check_cases,
    contract_ids,
    invariant_ids,
    load_cases,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases_dir", help="directory of case-NN.json / h-NN.json files")
    parser.add_argument("--contract", required=True, help="path to contract.md")
    parser.add_argument("--invariants", required=True, help="path to invariant registry JSON")
    args = parser.parse_args()

    contract = contract_ids(Path(args.contract).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.invariants).read_text(encoding="utf-8"))
    cases = load_cases(Path(args.cases_dir))

    problems = check_cases(cases, contract, invariant_ids(registry))
    if problems:
        print(f"INCOMPLETE cases: {len(problems)} problem(s) in {len(cases)} case(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"COMPLETE cases: {len(cases)} case(s) valid against {len(contract)} contract sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
