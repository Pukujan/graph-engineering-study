"""Metamorphic relations for the calibration policy surface (issue #2).

Metamorphic testing checks that a change which should not alter a decision does
not alter it, and that a change which should only reduce privilege never
increases it. Issue #2 names the relations; this module checks observed
before/after decision pairs against them.

An observation is ``{relation, before, after}`` where ``before`` and ``after``
are ``{"allowed": bool, "scope": [str, ...]}``. Deterministic: each relation is
a fixed structural check, never inferred.
"""

from __future__ import annotations

RELATIONS = (
    "reorder-independent",
    "unrelated-resource-unchanged",
    "scope-reduction-never-increases",
    "removed-allow-never-increases",
    "added-deny-never-increases",
    "idempotent-replay-no-wider",
)


def _allowed(decision: object) -> bool | None:
    return decision.get("allowed") if isinstance(decision, dict) else None


def _scope(decision: object) -> set:
    if not isinstance(decision, dict):
        return set()
    scope = decision.get("scope")
    return set(scope) if isinstance(scope, list) else set()


def _check(relation: str, before: dict, after: dict) -> str | None:
    """Return a failure message, or None when the relation holds."""

    if relation in ("reorder-independent", "unrelated-resource-unchanged"):
        if before != after:
            return f"decision changed ({before} -> {after})"
        return None

    if relation in ("scope-reduction-never-increases", "idempotent-replay-no-wider"):
        extra = _scope(after) - _scope(before)
        if extra:
            return f"scope widened by {sorted(extra)}"
        return None

    if relation in ("removed-allow-never-increases", "added-deny-never-increases"):
        if _allowed(before) is False and _allowed(after) is True:
            return "privilege increased (deny/absence of allow became allow)"
        return None

    return f"unknown relation {relation!r}"


def check_relations(observations: list[dict]) -> list[str]:
    """Return a problem string for every observation that violates its relation.

    Empty list means every observed before/after pair satisfies its relation.
    """

    if not isinstance(observations, list):
        return ["observations must be a list"]

    problems: list[str] = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            problems.append(f"#{index}: observation is not an object")
            continue
        relation = observation.get("relation")
        if relation not in RELATIONS:
            problems.append(
                f"#{index}: unknown relation {relation!r}; expected one of "
                f"{', '.join(RELATIONS)}"
            )
            continue
        failure = _check(relation, observation.get("before"), observation.get("after"))
        if failure is not None:
            problems.append(f"#{index} ({relation}): {failure}")
    return problems
