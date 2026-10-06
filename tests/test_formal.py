from __future__ import annotations

from graph_study.formal import check_invariants


def _complete() -> dict:
    return {
        "id": "deny-beats-allow",
        "method": "SMT",
        "property": "for every request, if an allow and a deny both match, the decision is deny",
        "model_boundary": "single policy version, finite rule set",
        "assumptions": ["rules are evaluated without error", "request attributes are well-typed"],
        "counterexample_behavior": "an allow returned where a deny also matched",
        "implementation_links": ["tests/test_policy.py::test_deny_precedence"],
    }


def test_complete_registry_has_no_problems() -> None:
    assert check_invariants([_complete()]) == []


def test_missing_field_is_reported() -> None:
    record = _complete()
    del record["model_boundary"]

    problems = check_invariants([record])

    assert any("deny-beats-allow" in p and "model_boundary" in p for p in problems)


def test_empty_assumptions_and_links_are_reported() -> None:
    record = _complete()
    record["assumptions"] = []
    record["implementation_links"] = []

    problems = check_invariants([record])

    assert any("assumptions" in p for p in problems)
    assert any("implementation_links" in p for p in problems)


def test_unknown_method_is_reported() -> None:
    record = _complete()
    record["method"] = "vibes"

    problems = check_invariants([record])

    assert any("unknown method" in p for p in problems)


def test_empty_registry_and_non_list_are_reported() -> None:
    assert check_invariants([]) != []
    assert check_invariants({"not": "a list"}) != []
