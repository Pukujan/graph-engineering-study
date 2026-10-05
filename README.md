# Graph Engineering Study

A study lab for the architecture we have been discussing: **deterministic software factory outside, coding inference only where reasoning is actually needed**.

The repository deliberately does not vendor the upstream systems. It records exact revisions and fetches them into an ignored local source cache.

## What is here

```text
spec
  |
  v
scaffold from known substrate     deterministic
  |
  v
validate                           deterministic
  | pass
  +-----------------------------> finish + evidence
  |
  | fail
  v
coding worker                      optional inference
  |
  v
validate again                     deterministic
```

The initial GUI substrate comes from `Pukujan/app-builder-automation`. The real multi-agent install path comes from `Pukujan/agent-custom-setup`, with OIO/PCM/CGM at the certified release-train revisions.

## Read first

- [PLAN.md](PLAN.md) — full implementation and study plan.
- [docs/architecture.md](docs/architecture.md) — node boundaries and why inference is small.
- [docs/study-path.md](docs/study-path.md) — what to reverse-study in every source repo.
- [Issue #1](https://github.com/Pukujan/graph-engineering-study/issues/1) — implementation record.
- [Issue #2](https://github.com/Pukujan/graph-engineering-study/issues/2) — long-running IAM A/B benchmark design.

## Bootstrap

Requires Git and Python 3.10+.

```bash
python scripts/bootstrap.py
```

That fetches the locked sources under `.sources/`, creates `.venv/`, installs the pinned Pydantic Graph checkout, installs this package, and installs the OIO validator dependency.

It does **not** call a coding model.

To also run the real ACS hotloader against this repo:

```bash
.venv/bin/python scripts/install_hotload.py
```

On Windows use `.venv\Scripts\python.exe`.

## Inspect the graph

```bash
graph-study diagram
```

The executable state machine lives in `src/graph_study/flow.py`.

## Scaffold the GUI substrate

```bash
python scripts/scaffold_ui.py \
  --out .workspaces/control-room \
  --spec examples/control-room.md
```

Add `--install` to run the substrate's pinned `pnpm install --frozen-lockfile`.

This copies the already-built React/Vite/shadcn substrate. It does not ask a model to invent routing, TypeScript configuration, Tailwind setup, or UI primitives.

## Run without inference

After dependencies exist in the workspace:

```bash
graph-study run \
  --spec examples/control-room.md \
  --workspace .workspaces/control-room \
  --validate "pnpm run typecheck"
```

If the validator passes, the graph finishes without a model call.

If it fails and no coding worker is configured, the graph ends in `needs_reasoning`. That is deliberate: it exposes the point where deterministic machinery ran out.

## Add a coding worker

Set a command template through `CODING_WORKER_CMD` or `--coding-worker`.

The template may use:

- `{workspace}`
- `{task_file}`
- `{attempt}`

Example shape:

```bash
export CODING_WORKER_CMD='your-coding-agent --workspace {workspace} --task {task_file}'
```

The graph supplies the exact failed validation evidence. The worker may patch the workspace, but **cannot mark the run successful**. The same deterministic validator runs again. Repair attempts default to two.

This is where Codex/OpenHands/etc. plug in later.

## Why this is not another generic coding harness

The baseline intentionally removes work from the coding model:

- project setup comes from a known substrate;
- workflow state is explicit;
- retry budget is code;
- validators are code;
- evidence capture is code;
- success is an exit-status decision;
- inference is only a repair edge.

Phase 2 adds Dagger and Nx around those same semantics. Phase 3 studies Hatchet as the durable runtime. See [PLAN.md](PLAN.md).

## Local evidence boundary

This repository was assembled through GitHub. The pull-request CI can validate Python syntax, the current Pydantic Graph API, tests, and graph rendering.

It does **not** prove the full local hotload, Node/pnpm app build, Docker, browser, Dagger, or coding-worker path works on your machine. That is the next Codex/operator verification step, and failures from it should be fixed as evidence rather than hidden.
