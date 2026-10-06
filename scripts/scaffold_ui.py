#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.actions import scaffold_from_app_builder  # noqa: E402
from graph_study.sources import resolve_sources_dir  # noqa: E402


def app_builder_commit() -> str:
    data = json.loads(
        (ROOT / "config" / "sources.lock.json").read_text(encoding="utf-8")
    )
    for entry in data["groups"]["reference"]:
        if entry["id"] == "app-builder-automation":
            return entry["commit"]
    raise RuntimeError("app-builder-automation missing from source lock")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold the ABA GUI substrate")
    parser.add_argument("--out", required=True)
    parser.add_argument("--spec")
    parser.add_argument(
        "--install",
        action="store_true",
        help="run pnpm install --frozen-lockfile after the deterministic copy",
    )
    args = parser.parse_args()

    workspace = Path(args.out).resolve()
    source = resolve_sources_dir(ROOT) / "app-builder-automation"
    if not source.is_dir():
        raise SystemExit("app-builder source missing; run scripts/fetch_sources.py first")

    scaffold_from_app_builder(
        source,
        workspace,
        source_commit=app_builder_commit(),
        spec_path=Path(args.spec).resolve() if args.spec else None,
    )

    if args.install:
        subprocess.run(
            ["pnpm", "install", "--frozen-lockfile"],
            cwd=workspace,
            check=True,
        )

    print(workspace)


if __name__ == "__main__":
    main()
