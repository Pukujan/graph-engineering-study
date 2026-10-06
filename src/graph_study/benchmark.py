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

from .cases import CALIBRATION_HOLDOUT_COUNT

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
    "task_materials.package_sha256": "sha256",
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


def directory_package_sha256(directory: Path) -> str:
    """Digest of the sha256sum manifest for every file under ``directory``.

    Used to pin both the shared task bundle and the sealed holdouts: the digest
    changes if any file is added, removed, or edited, without the contents ever
    entering an arm's context.
    """

    return seal_holdouts(directory)["package_sha256"]


def _check_holdout_manifest(path: Path, expected_digest: str) -> list[str]:
    path = Path(path)
    if not path.exists():
        return [f"holdout manifest not found: {path}"]

    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    problems: list[str] = []
    if len(lines) != CALIBRATION_HOLDOUT_COUNT:
        problems.append(
            f"holdout manifest has {len(lines)} entries, expected "
            f"{CALIBRATION_HOLDOUT_COUNT}"
        )
    for line in lines:
        digest, sep, rel = line.partition("  ")
        if sep != "  " or not _is_hex(digest, 64) or not rel:
            problems.append(f"malformed manifest line: {line!r}")

    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != expected_digest:
        problems.append(
            f"holdout manifest digest {actual} does not match "
            f"holdouts.manifest_sha256 {expected_digest}"
        )
    return problems


def check_task_materials(
    record: object,
    shared_dir: Path,
    holdout_manifest: Path,
) -> list[str]:
    """Return problems when the frozen task materials do not match the record.

    Re-seals ``shared_dir`` and compares it to ``task_materials.package_sha256``,
    then checks the holdout manifest is well-formed, has exactly
    ``CALIBRATION_HOLDOUT_COUNT`` entries, and matches
    ``holdouts.manifest_sha256``. Empty list means the materials are pinned.
    """

    problems: list[str] = []

    expected_shared = _lookup(record, "task_materials.package_sha256")
    if isinstance(expected_shared, str):
        actual = directory_package_sha256(shared_dir)
        if actual != expected_shared:
            problems.append(
                f"task_materials.package_sha256 {expected_shared} does not match "
                f"the shared bundle digest {actual}"
            )

    expected_holdouts = _lookup(record, "holdouts.manifest_sha256")
    if isinstance(expected_holdouts, str):
        problems.extend(_check_holdout_manifest(holdout_manifest, expected_holdouts))

    return problems


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
