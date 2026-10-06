from __future__ import annotations

from pathlib import Path

import pytest

from graph_study.timeline import (
    KNOWN_MILESTONES,
    append_event,
    load_events,
    summarize,
)


def test_append_defaults_to_utc_and_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "timeline.jsonl"

    written = append_event(path, "start")
    events = load_events(path)

    assert written["event"] == "start"
    assert written["at"].endswith("Z")
    assert events == [written]


def test_unknown_milestone_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        append_event(tmp_path / "timeline.jsonl", "whenever")


def test_summary_computes_elapsed_from_first_event(tmp_path: Path) -> None:
    path = tmp_path / "timeline.jsonl"
    append_event(path, "start", at="2026-10-06T00:00:00Z")
    append_event(path, "first_build", at="2026-10-06T00:12:30Z")
    append_event(path, "acceptance_pass", at="2026-10-06T01:00:00Z")

    result = summarize(load_events(path))

    assert result["elapsed_seconds"]["start"] == 0
    assert result["elapsed_seconds"]["first_build"] == 750
    assert result["elapsed_seconds"]["acceptance_pass"] == 3600
    assert "holdout_complete" in result["milestones_missing"]


def test_summary_rejects_non_monotonic_timeline(tmp_path: Path) -> None:
    path = tmp_path / "timeline.jsonl"
    append_event(path, "start", at="2026-10-06T00:00:00Z")
    append_event(path, "first_build", at="2026-10-05T23:00:00Z")

    with pytest.raises(ValueError):
        summarize(load_events(path))


def test_empty_timeline_reports_everything_missing(tmp_path: Path) -> None:
    result = summarize(load_events(tmp_path / "absent.jsonl"))

    assert result["events"] == 0
    assert result["milestones_missing"] == list(KNOWN_MILESTONES)
