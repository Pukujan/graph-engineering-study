from __future__ import annotations

import hashlib
from pathlib import Path

from graph_study.benchmark import (
    MANIFEST_NAME,
    check_freeze,
    seal_holdouts,
)

GOOD_COMMIT = "a" * 40
GOOD_SHA = "b" * 64


def _complete_record() -> dict:
    return {
        "task_spec_commit": GOOD_COMMIT,
        "starting_repo_commit": GOOD_COMMIT,
        "arms": {"a": {"harness": "codex", "model": "m1"}, "b": {"harness": "graph", "model": "m1"}},
        "resources": {
            "wall_clock_hours": 8,
            "monetary_budget_usd": 50,
            "token_budget": 1_000_000,
            "hardware_class": "8 vCPU / 32 GB",
        },
        "sandbox": {"credentials": "synthetic only", "infrastructure": "disposable local"},
        "specs": {"pdd_commit": GOOD_COMMIT, "sdd_commit": GOOD_COMMIT},
        "formal": {"methods": ["TLA+", "Z3"]},
        "holdouts": {"manifest_sha256": GOOD_SHA, "created_before_start": True},
        "scoring": {"usability_separate_from_robustness": True},
        "frozen_at": "2026-10-06T00:00:00Z",
        "frozen_by": "operator",
    }


def test_complete_record_has_no_missing_fields() -> None:
    assert check_freeze(_complete_record()) == []


def test_missing_field_is_reported() -> None:
    record = _complete_record()
    del record["arms"]["b"]["model"]

    assert "arms.b.model" in check_freeze(record)


def test_placeholder_values_are_rejected() -> None:
    record = _complete_record()
    record["starting_repo_commit"] = None
    record["sandbox"]["credentials"] = "   "
    record["resources"]["wall_clock_hours"] = 0
    record["holdouts"]["created_before_start"] = False

    missing = check_freeze(record)

    assert "starting_repo_commit" in missing
    assert "sandbox.credentials" in missing
    assert "resources.wall_clock_hours" in missing
    assert "holdouts.created_before_start" in missing


def test_malformed_commit_and_hash_are_rejected() -> None:
    record = _complete_record()
    record["task_spec_commit"] = "a" * 41  # one character too long
    record["holdouts"]["manifest_sha256"] = "B" * 64  # uppercase is not canonical

    missing = check_freeze(record)

    assert "task_spec_commit" in missing
    assert "holdouts.manifest_sha256" in missing


def test_seal_holdouts_is_deterministic_and_verifiable(tmp_path: Path) -> None:
    (tmp_path / "case-01.json").write_text('{"scenario": "revoked-session-race"}\n', encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "case-02.txt").write_text("duplicate mcp request\n", encoding="utf-8")

    first = seal_holdouts(tmp_path)
    second = seal_holdouts(tmp_path)

    assert first["files"] == 2
    assert first["package_sha256"] == second["package_sha256"]

    # The manifest is standard sha256sum output: two spaces, hash then path.
    line = first["manifest"].splitlines()[0]
    digest, _, rel = line.partition("  ")
    assert rel == "case-01.json"
    assert digest == hashlib.sha256((tmp_path / "case-01.json").read_bytes()).hexdigest()


def test_seal_holdouts_ignores_its_own_manifest(tmp_path: Path) -> None:
    (tmp_path / "case.json").write_text("x\n", encoding="utf-8")
    before = seal_holdouts(tmp_path)
    (tmp_path / MANIFEST_NAME).write_text(before["manifest"], encoding="utf-8")

    after = seal_holdouts(tmp_path)

    assert after["files"] == 1
    assert after["package_sha256"] == before["package_sha256"]
