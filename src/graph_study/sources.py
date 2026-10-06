"""Resolve where the pinned source checkouts live.

The project's own contract keeps pinned checkouts in a git-ignored ``.sources``
directory beside the code. The ACS contract that governs the multi-agent
hotload is stricter: inside its dev root only one primary checkout per repo may
exist, and dependency clones belong under the per-user ACS cache instead.

This resolver satisfies both. It returns ``.sources`` when the repository sits
outside the dev root, and the ACS deps cache when it sits inside it, and it
honours an explicit override either way.

The dev-root and cache locations are read here rather than imported from the
ACS checkout's own ``dev_root_check`` because that checkout is one of the very
directories this function has to locate first.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_OVERRIDE = "GRAPH_STUDY_SOURCES_DIR"
DEFAULT_DIRNAME = ".sources"


def dev_root() -> Path:
    override = os.environ.get("ACS_DEV_ROOT")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        return Path("D:/development")
    return Path.home() / "development"


def cache_dir() -> Path:
    override = os.environ.get("ACS_CACHE_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "acs"
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "acs"


def _norm(path: Path) -> str:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        resolved = path.expanduser().absolute()
    return os.path.normcase(str(resolved))


def is_inside(path: Path, root: Path) -> bool:
    inner, outer = _norm(path), _norm(root)
    return inner == outer or inner.startswith(outer.rstrip("\\/") + os.sep)


def resolve_sources_dir(repo_root: Path) -> Path:
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        return Path(override).expanduser()
    repo_root = repo_root.expanduser()
    if is_inside(repo_root, dev_root()):
        return cache_dir() / "deps"
    return repo_root / DEFAULT_DIRNAME
