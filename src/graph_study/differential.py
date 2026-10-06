"""Differential comparison of the two benchmark arms (issue #2).

Where both arms implement the same contract, the benchmark feeds identical
requests to each and compares the normalized decisions. Issue #2 requires that
"a difference is not automatically a bug, but every semantic difference must be
classified", so this module pairs observations, flags differences, and refuses
to accept a difference that carries no valid classification.

Normalization is fixed by the benchmark, not by either arm: volatile fields
(ids, timestamps, free-text reasons, matched-rule order) are dropped so a
difference means a semantic disagreement, not an incidental one. Deterministic:
comparison is structural, never inferred.
"""

from __future__ import annotations

import json
from pathlib import Path

DIFFERENTIAL_SCHEMA = "graph-study.benchmark.differential.v1"

# Fields that differ run-to-run without meaning a behavioral difference.
VOLATILE_KEYS = frozenset(
    {
        "credential_id",
        "expires_at",
        "revoked_at",
        "at",
        "principal_id",
        "matched_rules",
        "reason",
    }
)

# Every difference must be classified as exactly one of these.
CLASSIFICATIONS = frozenset(
    {
        "equivalent",
        "arm-a-bug",
        "arm-b-bug",
        "spec-ambiguity",
        "expected-difference",
    }
)


def normalize(decision: object) -> dict:
    """Strip volatile fields so only the semantic decision remains."""

    if not isinstance(decision, dict):
        return {}
    return {k: decision[k] for k in sorted(decision) if k not in VOLATILE_KEYS}


def load_arm(path: Path) -> dict:
    """Load one arm's evidence: ``{arm, observations:[{request_id, decision}]}``."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "observations" not in data:
        raise ValueError(f"{path}: evidence must have an 'observations' list")
    return data


def compare(arm_a: dict, arm_b: dict) -> list[dict]:
    """Pair observations by request id and flag semantic differences.

    Returns one entry per shared request id: ``{request_id, match, a, b}``. A
    request present in only one arm is reported as ``match: False`` with the
    missing side as ``None``, because an arm that never answered is itself a
    difference worth classifying.
    """

    a_by_id = {
        o["request_id"]: normalize(o.get("decision"))
        for o in arm_a["observations"]
    }
    b_by_id = {
        o["request_id"]: normalize(o.get("decision"))
        for o in arm_b["observations"]
    }

    results: list[dict] = []
    for request_id in sorted(set(a_by_id) | set(b_by_id)):
        a = a_by_id.get(request_id)
        b = b_by_id.get(request_id)
        results.append(
            {"request_id": request_id, "match": a == b and request_id in a_by_id and request_id in b_by_id,
             "a": a, "b": b}
        )
    return results


def differences(comparison: list[dict]) -> list[dict]:
    return [entry for entry in comparison if not entry["match"]]


def check_classifications(
    comparison: list[dict], classifications: dict
) -> list[str]:
    """Return a problem for every difference without a valid classification.

    ``classifications`` maps ``request_id`` to a value in
    :data:`CLASSIFICATIONS`. Empty list means every difference is classified and
    every classification is one of the allowed values.
    """

    problems: list[str] = []
    for entry in differences(comparison):
        request_id = entry["request_id"]
        label = classifications.get(request_id)
        if label is None:
            problems.append(f"{request_id}: difference is unclassified")
        elif label not in CLASSIFICATIONS:
            problems.append(
                f"{request_id}: classification {label!r} is not one of "
                f"{', '.join(sorted(CLASSIFICATIONS))}"
            )
    return problems
