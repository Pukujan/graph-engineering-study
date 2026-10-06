"""Acceptance-case schema and checker for the calibration benchmark (issue #2).

Acceptance cases and hidden holdouts are small, machine-readable scripts: an
ordered list of contract calls plus the expected outcome. Both arms are checked
against the same cases, and every case cites the contract section and (where it
applies) the named invariant it exercises, so a case cannot silently drift from
the spec it is meant to test.

Deterministic by construction: ``check_cases`` validates structure and
cross-references, never behaviour.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CASE_SCHEMA = "graph-study.benchmark.case.v1"
CALIBRATION_HOLDOUT_COUNT = 5

# Visible acceptance cases are named case-NN.json; hidden holdouts h-NN.json.
CASE_ID_RE = re.compile(r"^(case|h)-\d+$")
CONTRACT_ID_RE = re.compile(r"\bC-[A-Z]+-\d+\b")

_REQUIRED = ("schema", "case_id", "scenario", "contract_ref", "steps", "expect")


def load_cases(directory: Path) -> list[tuple[Path, dict]]:
    """Load every ``*.json`` case under ``directory`` as ``(path, record)``."""

    directory = Path(directory)
    loaded: list[tuple[Path, dict]] = []
    for path in sorted(directory.glob("*.json")):
        loaded.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return loaded


def contract_ids(contract_text: str) -> set[str]:
    """Every ``C-...`` section id named in a contract document."""

    return set(CONTRACT_ID_RE.findall(contract_text))


def invariant_ids(registry: object) -> set[str]:
    """The ``id`` of every invariant in a formal registry."""

    records = registry.get("invariants") if isinstance(registry, dict) else registry
    if not isinstance(records, list):
        return set()
    return {
        r["id"]
        for r in records
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }


def check_cases(
    cases: list[tuple[Path, dict]],
    contract: set[str],
    invariants: set[str],
) -> list[str]:
    """Return a problem string for every case that is malformed or mislinked.

    Empty list means every case is structurally valid and every reference it
    makes resolves. ``cases`` is the output of :func:`load_cases`.
    """

    problems: list[str] = []
    seen: set[str] = set()

    for path, record in cases:
        label = path.name
        if not isinstance(record, dict):
            problems.append(f"{label}: case is not an object")
            continue

        for field in _REQUIRED:
            if field not in record:
                problems.append(f"{label}: missing {field}")
        case_id = record.get("case_id")
        if not isinstance(case_id, str) or not CASE_ID_RE.match(case_id):
            problems.append(f"{label}: case_id must match case-NN or h-NN")
        else:
            if path.stem != case_id:
                problems.append(f"{label}: filename must match case_id {case_id!r}")
            if case_id in seen:
                problems.append(f"{label}: duplicate case_id {case_id!r}")
            seen.add(case_id)

        ref = record.get("contract_ref")
        if isinstance(ref, str) and ref not in contract:
            problems.append(f"{label}: contract_ref {ref!r} is not a contract section")

        inv = record.get("invariant_ref")
        if inv is not None:
            if not isinstance(inv, str) or inv not in invariants:
                problems.append(
                    f"{label}: invariant_ref {inv!r} is not a registered invariant"
                )

        steps = record.get("steps")
        if not isinstance(steps, list) or not steps:
            problems.append(f"{label}: steps must be a non-empty list")
        else:
            for index, step in enumerate(steps):
                if not isinstance(step, dict):
                    problems.append(f"{label}: step {index} is not an object")
                    continue
                if not isinstance(step.get("method"), str) or not step["method"]:
                    problems.append(f"{label}: step {index} needs a method")
                if not isinstance(step.get("path"), str) or not step["path"]:
                    problems.append(f"{label}: step {index} needs a path")

        expect = record.get("expect")
        if not isinstance(expect, dict):
            problems.append(f"{label}: expect must be an object")
        elif not isinstance(expect.get("status"), int) or isinstance(expect.get("status"), bool):
            problems.append(f"{label}: expect.status must be an integer HTTP status")

    return problems
