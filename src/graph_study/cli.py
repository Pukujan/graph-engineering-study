from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from .actions import scaffold_from_app_builder
from .flow import GraphDeps, GraphState, factory_graph

ROOT = Path(__file__).resolve().parents[2]


def _source_commit(source_id: str) -> str:
    data = json.loads(
        (ROOT / "config" / "sources.lock.json").read_text(encoding="utf-8")
    )
    for entries in data["groups"].values():
        for entry in entries:
            if entry["id"] == source_id:
                return entry["commit"]
    raise KeyError(source_id)


def _app_builder_root() -> Path:
    return ROOT / ".sources" / "app-builder-automation"


async def _run(args: argparse.Namespace) -> int:
    worker = args.coding_worker or os.environ.get("CODING_WORKER_CMD")
    state = GraphState(
        spec_path=Path(args.spec).resolve(),
        workspace=Path(args.workspace).resolve(),
        max_attempts=args.max_repairs,
    )
    deps = GraphDeps(
        repo_root=ROOT,
        app_builder_root=_app_builder_root(),
        app_builder_commit=_source_commit("app-builder-automation"),
        validation_commands=args.validate,
        evidence_root=ROOT / ".graph-evidence",
        coding_worker_cmd=worker,
    )
    outcome = await factory_graph.run(state=state, deps=deps)
    print(json.dumps(outcome.__dict__, indent=2))
    return 0 if outcome.status == "passed" else 1


def _scaffold(args: argparse.Namespace) -> int:
    scaffold_from_app_builder(
        _app_builder_root(),
        Path(args.workspace).resolve(),
        source_commit=_source_commit("app-builder-automation"),
        spec_path=Path(args.spec).resolve() if args.spec else None,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Graph engineering study CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run scaffold -> validate -> optional repair graph")
    run.add_argument("--spec", required=True)
    run.add_argument("--workspace", required=True)
    run.add_argument(
        "--validate",
        action="append",
        default=[],
        help="deterministic validation command; repeat for multiple commands",
    )
    run.add_argument("--coding-worker", default=None)
    run.add_argument("--max-repairs", type=int, default=2)

    scaffold = sub.add_parser("scaffold", help="copy ABA starter into a workspace")
    scaffold.add_argument("--workspace", required=True)
    scaffold.add_argument("--spec")

    sub.add_parser("diagram", help="print the graph Mermaid diagram")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "diagram":
        print(factory_graph.render(title="Graph engineering study"))
        raise SystemExit(0)

    if args.command == "scaffold":
        raise SystemExit(_scaffold(args))

    if args.command == "run":
        if not args.validate:
            args.validate = ["pnpm run typecheck"]
        raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
