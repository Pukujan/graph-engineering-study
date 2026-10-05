from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic_graph import BaseNode, End, GraphBuilder, GraphRunContext, StepContext

from .actions import (
    evidence_to_dict,
    run_coding_worker,
    scaffold_from_app_builder,
    validate_workspace,
    write_evidence,
)


@dataclass
class RunOutcome:
    status: str
    attempts: int
    evidence_file: str
    message: str


@dataclass
class GraphState:
    spec_path: Path
    workspace: Path
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    attempts: int = 0
    max_attempts: int = 2
    validations: list[dict] = field(default_factory=list)
    worker_runs: list[dict] = field(default_factory=list)


@dataclass
class GraphDeps:
    repo_root: Path
    app_builder_root: Path
    app_builder_commit: str
    validation_commands: list[str]
    evidence_root: Path
    coding_worker_cmd: str | None = None


def _payload(state: GraphState, status: str) -> dict:
    return {
        "schema_version": "graph-engineering-study.run.v1",
        "run_id": state.run_id,
        "status": status,
        "spec_path": str(state.spec_path),
        "workspace": str(state.workspace),
        "attempts": state.attempts,
        "max_attempts": state.max_attempts,
        "validations": state.validations,
        "worker_runs": state.worker_runs,
    }


def _finish(
    ctx: GraphRunContext[GraphState, GraphDeps],
    status: str,
    message: str,
) -> End[RunOutcome]:
    evidence = write_evidence(
        ctx.deps.evidence_root,
        ctx.state.run_id,
        _payload(ctx.state, status),
    )
    return End(
        RunOutcome(
            status=status,
            attempts=ctx.state.attempts,
            evidence_file=str(evidence),
            message=message,
        )
    )


@dataclass
class Scaffold(BaseNode[GraphState, GraphDeps, RunOutcome]):
    async def run(
        self,
        ctx: GraphRunContext[GraphState, GraphDeps],
    ) -> Validate | End[RunOutcome]:
        try:
            scaffold_from_app_builder(
                ctx.deps.app_builder_root,
                ctx.state.workspace,
                source_commit=ctx.deps.app_builder_commit,
                spec_path=ctx.state.spec_path,
            )
        except Exception as exc:
            return _finish(ctx, "scaffold_failed", f"deterministic scaffold failed: {exc}")
        return Validate()


@dataclass
class Validate(BaseNode[GraphState, GraphDeps, RunOutcome]):
    async def run(
        self,
        ctx: GraphRunContext[GraphState, GraphDeps],
    ) -> Repair | End[RunOutcome]:
        result = validate_workspace(
            ctx.state.workspace,
            ctx.deps.validation_commands,
        )
        ctx.state.validations.append(evidence_to_dict(result))

        if result.ok:
            return _finish(ctx, "passed", "deterministic validation passed")

        if not ctx.deps.coding_worker_cmd:
            return _finish(
                ctx,
                "needs_reasoning",
                "validation failed and no coding worker is enabled",
            )

        if ctx.state.attempts >= ctx.state.max_attempts:
            return _finish(
                ctx,
                "failed",
                "validation still fails after the bounded repair budget",
            )

        return Repair()


@dataclass
class Repair(BaseNode[GraphState, GraphDeps, RunOutcome]):
    async def run(
        self,
        ctx: GraphRunContext[GraphState, GraphDeps],
    ) -> Validate | End[RunOutcome]:
        ctx.state.attempts += 1
        latest = ctx.state.validations[-1]

        request_dir = ctx.state.workspace / ".graph-study"
        request_dir.mkdir(parents=True, exist_ok=True)
        task_file = request_dir / f"repair-{ctx.state.attempts}.md"
        task_file.write_text(
            "# Repair request\n\n"
            f"Attempt: {ctx.state.attempts}/{ctx.state.max_attempts}\n\n"
            "## Original spec\n\n"
            + ctx.state.spec_path.read_text(encoding="utf-8")
            + "\n\n## Deterministic validation evidence\n\n```json\n"
            + json.dumps(latest, indent=2)
            + "\n```\n\n"
            "Make the smallest repository change that addresses the evidence. "
            "Do not claim success and do not weaken or remove the validation gate. "
            "The outer graph will rerun validation.\n",
            encoding="utf-8",
        )

        worker = run_coding_worker(
            ctx.deps.coding_worker_cmd or "",
            workspace=ctx.state.workspace,
            task_file=task_file,
            attempt=ctx.state.attempts,
        )
        ctx.state.worker_runs.append(asdict(worker))

        if worker.returncode != 0 and ctx.state.attempts >= ctx.state.max_attempts:
            return _finish(
                ctx,
                "worker_failed",
                "coding worker failed and the repair budget is exhausted",
            )

        return Validate()


builder = GraphBuilder(
    state_type=GraphState,
    deps_type=GraphDeps,
    output_type=RunOutcome,
)


@builder.step
async def start(ctx: StepContext[GraphState, GraphDeps, None]) -> Scaffold:
    return Scaffold()


builder.add(
    builder.node(Scaffold),
    builder.node(Validate),
    builder.node(Repair),
    builder.edge_from(builder.start_node).to(start),
)

factory_graph = builder.build()
