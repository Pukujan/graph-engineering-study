"""Deterministic helpers for the IAM A/B benchmark program (issue #2).

The benchmark compares a plain coding harness against this repository's
graph-engineered factory. Two things must be true before either arm runs, and
both are mechanically checkable, so neither is left to inference:

* the experiment is *frozen* -- the task spec, starting commit, resources,
  models, sandbox, specs, formal methods, and holdout hash are all recorded;
* the hidden holdouts are *sealed* -- their contents never enter either arm's
  context, only a manifest hash does.

This module is the deterministic gate for both. See
``docs/benchmark-protocol.md``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

FREEZE_SCHEMA = "graph-study.benchmark.freeze.v1"
HOLDOUT_SCHEMA = "graph-study.benchmark.holdouts.v1"
MANIFEST_NAME = "manifest.sha256"

_MISSING = object()

# Each required freeze field maps to the kind of value that satisfies it. A
# freeze is complete only when every field is present and satisfies its kind.
REQUIRED_FREEZE_FIELDS: dict[str, str] = {
    "task_spec_commit": "commit",
    "starting_repo_commit": "commit",
    "arms.a.harness": "str",
    "arms.a.model": "str",
    "arms.b.harness": "str",
    "arms.b.model": "str",
    "resources.wall_clock_hours": "num",
    "resources.monetary_budget_usd": "num",
    "resources.token_budget": "num",
    "resources.hardware_class": "str",
    "sandbox.credentials": "str",
    "sandbox.infrastructure": "str",
    "specs.pdd_commit": "commit",
    "specs.sdd_commit": "commit",
    "formal.methods": "list",
    "holdouts.manifest_sha256": "sha256",
    "holdouts.created_before_start": "true",
    "scoring.usability_separate_from_robustness": "true",
    "frozen_at": "str",
    "frozen_by": "str",
}


def _lookup(record: object, path: str) -> object:
    node = record
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return _MISSING
        node = node[part]
    return node


def _is_hex(value: object, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(c in "0123456789abcdef" for c in value)
    )


def _satisfies(value: object, kind: str) -> bool:
    if kind == "str":
        return isinstance(value, str) and value.strip() != ""
    if kind == "num":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > 0
        )
    if kind == "true":
        return value is True
    if kind == "list":
        return isinstance(value, list) and len(value) > 0
    if kind == "commit":
        return _is_hex(value, 40)
    if kind == "sha256":
        return _is_hex(value, 64)
    raise ValueError(f"unknown field kind: {kind}")


def check_freeze(record: object) -> list[str]:
    """Return the required freeze fields that are missing or invalid.

    An empty list means the freeze record is complete and the experiment may
    start. Field kinds are checked exactly: a commit must be 40 lowercase hex
    characters, a budget must be a positive number, an attestation must be
    literally ``true``.
    """

    missing: list[str] = []
    for path, kind in REQUIRED_FREEZE_FIELDS.items():
        value = _lookup(record, path)
        if value is _MISSING or not _satisfies(value, kind):
            missing.append(path)
    return missing


def seal_holdouts(directory: Path) -> dict:
    """Hash every file under ``directory`` into a sha256sum-style manifest.

    The returned ``manifest`` text is portable: ``sha256sum -c`` verifies it on
    any POSIX host. ``package_sha256`` is the digest of that text, which is what
    a freeze record records so the sealed package can be pinned without its
    contents ever entering an arm's context. A manifest file inside the
    directory is ignored so re-sealing is stable.
    """

    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    files = sorted(
        (
            p
            for p in directory.rglob("*")
            if p.is_file() and p.name != MANIFEST_NAME
        ),
        key=lambda p: p.relative_to(directory).as_posix(),
    )

    lines = [
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(directory).as_posix()}"
        for p in files
    ]
    manifest = "\n".join(lines) + ("\n" if lines else "")
    package = hashlib.sha256(manifest.encode("utf-8")).hexdigest()
    return {
        "schema": HOLDOUT_SCHEMA,
        "files": len(files),
        "package_sha256": package,
        "manifest": manifest,
    }
