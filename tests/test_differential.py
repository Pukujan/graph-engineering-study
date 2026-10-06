from __future__ import annotations

from graph_study.differential import (
    check_classifications,
    compare,
    differences,
    normalize,
)


def _arm(name: str, observations: list[dict]) -> dict:
    return {"arm": name, "observations": observations}


def test_normalize_drops_volatile_fields() -> None:
    decision = {
        "allowed": True,
        "resource": "db:reports",
        "credential_id": "c-1",
        "expires_at": "2026-10-06T01:00:00Z",
        "reason": "matched allow rule",
        "matched_rules": ["r1"],
    }

    assert normalize(decision) == {"allowed": True, "resource": "db:reports"}


def test_compare_matches_and_differences() -> None:
    a = _arm("a", [
        {"request_id": "r1", "decision": {"allowed": True, "resource": "db:reports"}},
        {"request_id": "r2", "decision": {"allowed": False}},
    ])
    b = _arm("b", [
        {"request_id": "r1", "decision": {"allowed": True, "resource": "db:reports", "credential_id": "c-9"}},
        {"request_id": "r2", "decision": {"allowed": True}},
    ])

    result = compare(a, b)

    assert [e["match"] for e in result] == [True, False]
    assert [e["request_id"] for e in differences(result)] == ["r2"]


def test_request_missing_from_one_arm_is_a_difference() -> None:
    a = _arm("a", [{"request_id": "r1", "decision": {"allowed": True}}])
    b = _arm("b", [])

    result = compare(a, b)

    assert result[0]["match"] is False
    assert result[0]["b"] is None


def test_unclassified_difference_is_reported() -> None:
    a = _arm("a", [{"request_id": "r1", "decision": {"allowed": True}}])
    b = _arm("b", [{"request_id": "r1", "decision": {"allowed": False}}])
    comparison = compare(a, b)

    problems = check_classifications(comparison, {})

    assert any("unclassified" in p for p in problems)


def test_invalid_classification_is_reported() -> None:
    a = _arm("a", [{"request_id": "r1", "decision": {"allowed": True}}])
    b = _arm("b", [{"request_id": "r1", "decision": {"allowed": False}}])
    comparison = compare(a, b)

    problems = check_classifications(comparison, {"r1": "looks-fine"})

    assert any("not one of" in p for p in problems)


def test_classified_difference_passes() -> None:
    a = _arm("a", [{"request_id": "r1", "decision": {"allowed": True}}])
    b = _arm("b", [{"request_id": "r1", "decision": {"allowed": False}}])
    comparison = compare(a, b)

    assert check_classifications(comparison, {"r1": "arm-b-bug"}) == []
