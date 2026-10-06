"""Formal-method invariant registry for the IAM A/B benchmark (issue #2).

Issue #2 requires that each proof or model state five things -- the property,
the model boundary, the assumptions, the counterexample/failure behavior, and
the connection to the executable implementation or tests -- and that formal
methods be "tied to named invariants" rather than decorative.

This module makes that checkable. A registry is a list of invariant records;
``check_invariants`` returns a problem string for every record that is missing a
required field, names an unknown method, or leaves the assumptions empty. The
benchmark's freeze record points at the registry, so a proof that is not fully
specified fails the gate instead of being counted.
"""

from __future__ import annotations

FORMAL_SCHEMA = "graph-study.benchmark.formal.v1"

# Only methods the issue names as in scope. A record may not claim a method
# outside this set.
KNOWN_METHODS: tuple[str, ...] = ("TLA+", "Lean 4", "SMT")

# Every record must state all five items the issue requires, plus a stable id.
REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "method",
    "property",
    "model_boundary",
    "assumptions",
    "counterexample_behavior",
    "implementation_links",
)


def _nonempty_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _nonempty_list(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0


def check_invariants(records: object) -> list[str]:
    """Return a problem string for every incomplete invariant record.

    An empty list means every record is fully specified. ``records`` must be a
    list; a non-list is itself a single problem.
    """

    if not isinstance(records, list):
        return ["registry must be a list of invariant records"]
    if not records:
        return ["registry is empty; at least one named invariant is required"]

    problems: list[str] = []
    for index, record in enumerate(records):
        label = (
            record.get("id")
            if isinstance(record, dict) and _nonempty_str(record.get("id"))
            else f"#{index}"
        )
        if not isinstance(record, dict):
            problems.append(f"{label}: record is not an object")
            continue

        for field in REQUIRED_FIELDS:
            if field not in record:
                problems.append(f"{label}: missing {field}")
                continue
            value = record[field]
            if field == "assumptions":
                if not _nonempty_list(value):
                    problems.append(f"{label}: assumptions must be a non-empty list")
            elif field == "implementation_links":
                if not _nonempty_list(value):
                    problems.append(
                        f"{label}: implementation_links must be a non-empty list"
                    )
            elif not _nonempty_str(value):
                problems.append(f"{label}: {field} must be a non-empty string")

        method = record.get("method")
        if _nonempty_str(method) and method not in KNOWN_METHODS:
            problems.append(
                f"{label}: unknown method {method!r}; expected one of "
                f"{', '.join(KNOWN_METHODS)}"
            )
    return problems
