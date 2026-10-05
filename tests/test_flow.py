from __future__ import annotations

from pathlib import Path

from graph_study.flow import GraphDeps, GraphState, factory_graph


def make_source(tmp_path: Path) -> Path:
    source = tmp_path / "aba"
    template = source / "templates" / "react-vite-shadcn"
    template.mkdir(parents=True)
    (template / "package.json").write_text("{}", encoding="utf-8")
    return source


def test_graph_passes_without_inference_when_validator_passes(tmp_path: Path) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# test", encoding="utf-8")
    workspace = tmp_path / "workspace"
    deps = GraphDeps(
        repo_root=tmp_path,
        app_builder_root=make_source(tmp_path),
        app_builder_commit="abc",
        validation_commands=['python -c "print(\'ok\')"'],
        evidence_root=tmp_path / "evidence",
        coding_worker_cmd=None,
    )
    state = GraphState(spec_path=spec, workspace=workspace)

    outcome = factory_graph.run_sync(state=state, deps=deps)

    assert outcome.status == "passed"
    assert state.attempts == 0
    assert Path(outcome.evidence_file).exists()


def test_graph_stops_for_reasoning_when_validation_fails_and_worker_is_off(
    tmp_path: Path,
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# test", encoding="utf-8")
    workspace = tmp_path / "workspace"
    deps = GraphDeps(
        repo_root=tmp_path,
        app_builder_root=make_source(tmp_path),
        app_builder_commit="abc",
        validation_commands=['python -c "import sys; sys.exit(2)"'],
        evidence_root=tmp_path / "evidence",
        coding_worker_cmd=None,
    )
    state = GraphState(spec_path=spec, workspace=workspace)

    outcome = factory_graph.run_sync(state=state, deps=deps)

    assert outcome.status == "needs_reasoning"
    assert state.attempts == 0
