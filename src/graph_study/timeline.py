"""Deterministic timeline evidence for the IAM A/B benchmark (issue #2).

The benchmark measures each arm "from the first command, not from the first
model token", and the result format requires a ``timeline.jsonl`` per arm. This
module records that timeline deterministically: UTC ISO-8601 timestamps, a fixed
milestone vocabulary, and elapsed-time arithmetic that the operator does not
compute by hand.

Like the freeze gate, this is deliberately inference-free. Nothing here decides
whether an arm passed; it only records and checks when each milestone happened.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# Ordered: the natural progression of one arm. ``start`` is the first command.
KNOWN_MILESTONES: tuple[str, ...] = (
    "start",
    "bootstrapped",
    "first_build",
    "first_e2e",
    "first_security_gate",
    "acceptance_pass",
    "holdout_complete",
    "cutoff",
    "post_cutoff_repair",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def append_event(
    path: Path,
    event: str,
    *,
    at: str | None = None,
    note: str | None = None,
) -> dict:
    """Append one milestone to the timeline, returning the written event.

    ``event`` must be a known milestone; ``at`` defaults to now in UTC. The line
    is JSON with ``event``, ``at``, and an optional ``note``.
    """

    if event not in KNOWN_MILESTONES:
        raise ValueError(
            f"unknown milestone {event!r}; expected one of {', '.join(KNOWN_MILESTONES)}"
        )
    record = {"event": event, "at": at or _utc_now()}
    if note is not None:
        record["note"] = note

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return record


def load_events(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def summarize(events: list[dict]) -> dict:
    """Elapsed seconds per milestone, relative to the first recorded event.

    Raises ``ValueError`` if timestamps go backwards, because a non-monotonic
    timeline means the evidence is not trustworthy.
    """

    if not events:
        return {
            "events": 0,
            "milestones_present": [],
            "milestones_missing": list(KNOWN_MILESTONES),
            "elapsed_seconds": {},
            "monotonic": True,
        }

    origin = _parse(events[0]["at"])
    elapsed: dict[str, float] = {}
    present: list[str] = []
    previous = origin
    for record in events:
        stamp = _parse(record["at"])
        if stamp < previous:
            raise ValueError(
                f"timeline is not monotonic: {record['event']} at {record['at']} "
                f"precedes the previous event"
            )
        previous = stamp
        name = record["event"]
        if name not in present:
            present.append(name)
        elapsed[name] = (stamp - origin).total_seconds()

    return {
        "events": len(events),
        "milestones_present": present,
        "milestones_missing": [m for m in KNOWN_MILESTONES if m not in present],
        "elapsed_seconds": elapsed,
        "monotonic": True,
    }
