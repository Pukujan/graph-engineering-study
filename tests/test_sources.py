from __future__ import annotations

from pathlib import Path

from graph_study.sources import is_inside, resolve_sources_dir


def test_resolve_uses_in_repo_dir_outside_dev_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ACS_DEV_ROOT", str(tmp_path / "dev"))
    repo = tmp_path / "elsewhere" / "repo"
    repo.mkdir(parents=True)

    assert resolve_sources_dir(repo) == repo / ".sources"


def test_resolve_uses_acs_deps_cache_inside_dev_root(tmp_path: Path, monkeypatch) -> None:
    dev = tmp_path / "dev"
    repo = dev / "repo"
    repo.mkdir(parents=True)
    monkeypatch.setenv("ACS_DEV_ROOT", str(dev))
    monkeypatch.setenv("ACS_CACHE_DIR", str(tmp_path / "cache"))

    assert resolve_sources_dir(repo) == tmp_path / "cache" / "deps"


def test_resolve_honours_explicit_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ACS_DEV_ROOT", str(tmp_path / "dev"))
    monkeypatch.setenv("GRAPH_STUDY_SOURCES_DIR", str(tmp_path / "pinned"))

    assert resolve_sources_dir(tmp_path) == tmp_path / "pinned"


def test_is_inside_matches_root_and_descendants_only(tmp_path: Path) -> None:
    root = tmp_path / "dev"

    assert is_inside(root, root)
    assert is_inside(root / "a" / "b", root)
    assert not is_inside(tmp_path / "dev-other", root)
    assert not is_inside(tmp_path / "outside", root)
