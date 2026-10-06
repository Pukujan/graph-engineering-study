#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.sources import resolve_sources_dir  # noqa: E402

LOCK = ROOT / "config" / "sources.lock.json"
LEGACY_DEST = ROOT / ".sources"


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


def _rmtree_readonly(path: Path) -> None:
    """Remove a tree that may hold read-only git object files.

    Git marks packed objects read-only, and on Windows a plain ``rmtree`` (or
    the delete half of a cross-drive ``shutil.move``) fails on them.
    """

    def retry(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    try:
        shutil.rmtree(path, onexc=retry)
    except TypeError:  # Python < 3.12 spells the hook onerror
        shutil.rmtree(path, onerror=retry)


def migrate_legacy(legacy: Path, dest: Path) -> None:
    """Relocate an in-repo cache to the configured destination.

    Checkouts are copied then removed rather than re-fetched, so the pinned
    revisions survive the relocation the ACS dev-root contract requires. A
    checkout already at the destination is kept; an in-repo duplicate of it is
    dropped, and anything else is left in place rather than overwritten.
    """
    if legacy == dest or not legacy.is_dir():
        return
    dest.mkdir(parents=True, exist_ok=True)
    for child in sorted(legacy.iterdir()):
        target = dest / child.name
        if target.exists():
            existing, incoming = head(target), head(child)
            if incoming and incoming == existing:
                _rmtree_readonly(child)
                print(f"DEDUP {child.name} (already at {target})")
            else:
                print(f"KEPT {child.name} (destination differs: {target})")
            continue
        shutil.copytree(child, target, symlinks=True)
        _rmtree_readonly(child)
        print(f"MOVED {child.name} -> {target}")
    try:
        legacy.rmdir()
    except OSError:
        pass


def fetch(entry: dict, dest: Path, *, reset: bool = False) -> None:
    target = dest / entry["id"]
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
        "--dest",
        help=(
            "source cache directory; defaults to .sources outside the ACS dev "
            "root and the ACS deps cache inside it"
        ),
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="discard modifications inside the source cache before re-pinning",
    )
    args = parser.parse_args()

    data = json.loads(LOCK.read_text(encoding="utf-8"))
    groups = data["groups"]
    selected = groups.keys() if args.group == "all" else [args.group]

    dest = Path(args.dest).expanduser() if args.dest else resolve_sources_dir(ROOT)
    dest.mkdir(parents=True, exist_ok=True)
    migrate_legacy(LEGACY_DEST, dest)
    print(f"sources: {dest}")

    for group in selected:
        for entry in groups[group]:
            fetch(entry, dest, reset=args.reset)


if __name__ == "__main__":
    main()
