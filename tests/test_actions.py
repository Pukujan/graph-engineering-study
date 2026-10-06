from __future__ import annotations

import json
from pathlib import Path

import pytest

from graph_study.actions import (
    _resolve_executable,
    scaffold_from_app_builder,
    validate_workspace,
)


def test_validate_workspace_stops_on_first_failure(tmp_path: Path) -> None:
    result = validate_workspace(
        tmp_path,
        [
            'python -c "print(1)"',
            'python -c "import sys; sys.exit(3)"',
            'python -c "raise RuntimeError(\'should not run\')"',
        ],
    )
    assert result.ok is False
    assert [item.returncode for item in result.commands] == [0, 3]


def test_scaffold_refuses_unowned_nonempty_target(tmp_path: Path) -> None:
    source = tmp_path / "aba"
    template = source / "templates" / "react-vite-shadcn"
    template.mkdir(parents=True)
    (template / "package.json").write_text("{}", encoding="utf-8")

    target = tmp_path / "target"
    target.mkdir()
    (target / "foreign.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(RuntimeError):
        scaffold_from_app_builder(source, target, source_commit="abc")


def test_resolve_executable_resolves_shim_and_preserves_unknown() -> None:
    import sys

    resolved = _resolve_executable(["python", "-c", "pass"])
    assert Path(resolved[0]).name.lower().startswith("python")
    assert Path(resolved[0]).is_file() or sys.platform != "win32"

    missing = ["definitely-not-a-real-executable-xyz", "--flag"]
    assert _resolve_executable(missing) == missing


def test_scaffold_records_source_revision(tmp_path: Path) -> None:
    source = tmp_path / "aba"
    template = source / "templates" / "react-vite-shadcn"
    template.mkdir(parents=True)
    (template / "package.json").write_text("{}", encoding="utf-8")

    target = tmp_path / "target"
    scaffold_from_app_builder(source, target, source_commit="deadbeef")

    marker = json.loads((target / ".graph-study.json").read_text(encoding="utf-8"))
    assert marker["source_commit"] == "deadbeef"
    assert (target / "package.json").exists()
