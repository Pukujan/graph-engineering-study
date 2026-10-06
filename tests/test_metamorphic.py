from __future__ import annotations

from graph_study.metamorphic import check_relations


def _obs(relation: str, before: dict, after: dict) -> dict:
    return {"relation": relation, "before": before, "after": after}


def test_satisfied_relations_have_no_problems() -> None:
    observations = [
        _obs("reorder-independent", {"allowed": True}, {"allowed": True}),
        _obs("scope-reduction-never-increases",
             {"scope": ["read", "write"]}, {"scope": ["read"]}),
        _obs("removed-allow-never-increases", {"allowed": True}, {"allowed": False}),
        _obs("added-deny-never-increases", {"allowed": True}, {"allowed": False}),
    ]

    assert check_relations(observations) == []


def test_reorder_change_is_a_violation() -> None:
    problems = check_relations([_obs("reorder-independent", {"allowed": True}, {"allowed": False})])

    assert any("decision changed" in p for p in problems)


def test_scope_widening_is_a_violation() -> None:
    problems = check_relations([
        _obs("scope-reduction-never-increases", {"scope": ["read"]}, {"scope": ["read", "write"]})
    ])

    assert any("scope widened" in p for p in problems)


def test_privilege_increase_is_a_violation() -> None:
    problems = check_relations([
        _obs("removed-allow-never-increases", {"allowed": False}, {"allowed": True}),
        _obs("added-deny-never-increases", {"allowed": False}, {"allowed": True}),
    ])

    assert len(problems) == 2


def test_unknown_relation_is_reported() -> None:
    problems = check_relations([_obs("vibes", {}, {})])

    assert any("unknown relation" in p for p in problems)
