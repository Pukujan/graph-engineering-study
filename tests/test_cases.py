from __future__ import annotations

from pathlib import Path

from graph_study.cases import (
    CASE_SCHEMA,
    check_cases,
    contract_ids,
    invariant_ids,
    load_cases,
)

CONTRACT = {"C-API-01", "C-API-02"}
INVARIANTS = {"privilege-intersection"}


def _case(case_id: str = "case-01", **overrides) -> dict:
    record = {
        "schema": CASE_SCHEMA,
        "case_id": case_id,
        "scenario": "request a credential inside scope",
        "contract_ref": "C-API-02",
        "invariant_ref": "privilege-intersection",
        "steps": [{"method": "POST", "path": "/principals", "body": {}}],
        "expect": {"status": 200},
    }
    record.update(overrides)
    return record


def _loaded(record: dict) -> list[tuple[Path, dict]]:
    return [(Path(f"{record['case_id']}.json"), record)]


def test_valid_case_has_no_problems() -> None:
    assert check_cases(_loaded(_case()), CONTRACT, INVARIANTS) == []


def test_unknown_contract_ref_is_reported() -> None:
    problems = check_cases(_loaded(_case(contract_ref="C-API-99")), CONTRACT, INVARIANTS)

    assert any("contract_ref" in p for p in problems)


def test_unknown_invariant_ref_is_reported() -> None:
    problems = check_cases(_loaded(_case(invariant_ref="made-up")), CONTRACT, INVARIANTS)

    assert any("invariant_ref" in p for p in problems)


def test_null_invariant_ref_is_allowed() -> None:
    assert check_cases(_loaded(_case(invariant_ref=None)), CONTRACT, INVARIANTS) == []


def test_missing_field_is_reported() -> None:
    record = _case()
    del record["scenario"]

    problems = check_cases(_loaded(record), CONTRACT, INVARIANTS)

    assert any("missing scenario" in p for p in problems)


def test_filename_must_match_case_id() -> None:
    problems = check_cases([(Path("case-99.json"), _case("case-01"))], CONTRACT, INVARIANTS)

    assert any("filename" in p for p in problems)


def test_bad_case_id_and_duplicate_are_reported() -> None:
    bad = check_cases([(Path("weird.json"), _case("weird"))], CONTRACT, INVARIANTS)
    assert any("case-NN" in p for p in bad)

    dup = check_cases(_loaded(_case()) + _loaded(_case()), CONTRACT, INVARIANTS)
    assert any("duplicate" in p for p in dup)


def test_empty_steps_and_bad_status_are_reported() -> None:
    record = _case()
    record["steps"] = []
    record["expect"] = {"status": "200"}

    problems = check_cases(_loaded(record), CONTRACT, INVARIANTS)

    assert any("steps" in p for p in problems)
    assert any("expect.status" in p for p in problems)


def test_contract_and_invariant_id_extraction() -> None:
    text = "## C-API-01 — create\nsee C-API-02 and C-ERR-03, not C-lower-1"

    assert contract_ids(text) == {"C-API-01", "C-API-02", "C-ERR-03"}
    assert invariant_ids({"invariants": [{"id": "a"}, {"id": "b"}]}) == {"a", "b"}
    assert invariant_ids([{"id": "x"}]) == {"x"}
    assert invariant_ids("nonsense") == set()


def test_load_cases_reads_json_files(tmp_path: Path) -> None:
    (tmp_path / "case-01.json").write_text(
        '{"schema": "graph-study.benchmark.case.v1", "case_id": "case-01"}\n',
        encoding="utf-8",
    )

    loaded = load_cases(tmp_path)

    assert len(loaded) == 1
    assert loaded[0][0].name == "case-01.json"
