#!/usr/bin/env python3
"""Record or summarize a benchmark arm's timeline.jsonl (issue #2).

Two modes:

    benchmark_timeline.py record  <timeline.jsonl> <milestone> [--at ISO8601] [--note TEXT]
    benchmark_timeline.py summary <timeline.jsonl>

``record`` appends one UTC-stamped milestone. ``summary`` prints elapsed seconds
per milestone from the first event, the milestones still missing, and exits
non-zero if the timeline is not monotonic. Deterministic: no inference decides
what the timeline says.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.timeline import (  # noqa: E402
    KNOWN_MILESTONES,
    append_event,
    load_events,
    summarize,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", help="append a UTC-stamped milestone")
    record.add_argument("timeline")
    record.add_argument("milestone", choices=KNOWN_MILESTONES)
    record.add_argument("--at", default=None, help="ISO-8601 UTC; defaults to now")
    record.add_argument("--note", default=None)

    summary = sub.add_parser("summary", help="print elapsed seconds per milestone")
    summary.add_argument("timeline")

    args = parser.parse_args()
    path = Path(args.timeline)

    if args.command == "record":
        event = append_event(path, args.milestone, at=args.at, note=args.note)
        print(json.dumps(event))
        return 0

    try:
        result = summarize(load_events(path))
    except ValueError as exc:
        print(f"INVALID timeline: {exc}")
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
