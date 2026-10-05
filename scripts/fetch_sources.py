#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "config" / "sources.lock.json"
DEST = ROOT / ".sources"


def run(argv: list[str], *, cwd: Path | None = None, capture: bool = False) -> str:
    proc = subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=capture,
    )
    if proc.returncode != 0:
        detail = ""
        if capture:
            detail = (proc.stdout or "") + (proc.stderr or "")
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(argv)}\n{detail}"
        )
    return (proc.stdout or "").strip() if capture else ""


def head(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    try:
        return run(["git", "rev-parse", "HEAD"], cwd=path, capture=True)
    except RuntimeError:
        return None


def dirty(path: Path) -> bool:
    return bool(run(["git", "status", "--porcelain"], cwd=path, capture=True).strip())


def fetch(entry: dict, *, reset: bool = False) -> None:
    target = DEST / entry["id"]
    expected = entry["commit"]

    if target.exists() and not (target / ".git").exists():
        raise RuntimeError(f"refusing non-git source directory: {target}")

    if not target.exists():
        target.mkdir(parents=True)
        run(["git", "init"], cwd=target)
        run(["git", "remote", "add", "origin", entry["url"]], cwd=target)

    current = head(target)
    if current == expected:
        print(f"OK {entry['id']} {expected[:12]}")
        return

    if dirty(target) and not reset:
        raise RuntimeError(
            f"{target} has local changes; source checkouts are read-only. "
            "Remove the changes or rerun with --reset."
        )

    run(["git", "fetch", "--depth", "1", "origin", expected], cwd=target)
    run(["git", "checkout", "--detach", "--force", "FETCH_HEAD"], cwd=target)

    actual = head(target)
    if actual != expected:
        raise RuntimeError(f"{entry['id']}: expected {expected}, got {actual}")

    print(f"FETCHED {entry['id']} {expected[:12]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch exact study/reference source revisions"
    )
    parser.add_argument(
        "--group",
        choices=["stack", "reference", "oss", "all"],
        default="all",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="discard modifications inside .sources before re-pinning",
    )
    args = parser.parse_args()

    data = json.loads(LOCK.read_text(encoding="utf-8"))
    groups = data["groups"]
    selected = groups.keys() if args.group == "all" else [args.group]

    DEST.mkdir(exist_ok=True)
    for group in selected:
        for entry in groups[group]:
            fetch(entry, reset=args.reset)


if __name__ == "__main__":
    main()
