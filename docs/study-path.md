# Study path

Use this order. The point is to compare responsibilities, not to read every repository front to back.

## 1. This repo

Read:

1. `PLAN.md`
2. `src/graph_study/flow.py`
3. `src/graph_study/actions.py`
4. `scripts/scaffold_ui.py`
5. `scripts/install_hotload.py`

Question to answer: which decisions remain after deterministic software has done everything it can?

## 2. app-builder-automation

Inspect:

- `templates/react-vite-shadcn/` — why a complete substrate shrinks design search space;
- `server/src/loop.mjs` — model/tool loop and repair gate;
- `server/src/tools.mjs` — tool surface;
- `eval/run-acceptance.mjs` and `eval/verify-app.mjs` — executable acceptance;
- `docs/research/2026-10-04-dyad-design-study.md` — design specialization notes.

Compare its generation loop to this repo's smaller graph. ABA is optimized for app creation; this repo is optimized for making the control boundary obvious.

## 3. agent-custom-setup

Inspect:

- `modules/coordination/multi-agent-hotload/v0.1.0/SPEC.md`
- `HOTLOAD.md`
- `scripts/acs_install.py`
- `scripts/hotload_check.py`
- `formal/install.tla`

Question: which safety properties are better expressed as deterministic install gates than as agent instructions?

## 4. observational-issue-ops

Inspect:

- `PROJECT.md`
- `.github/ISSUE_TEMPLATE/observational-issue.yml`
- `.github/scripts/oio_installer.py`
- `.github/scripts/oio_triage.py`

Question: why should intake/provenance be separate from execution coordination?

## 5. Pydantic Graph

Inspect the pinned checkout:

- `pydantic_graph/`
- `docs/graph.md`
- graph builder examples.

Question: what do typed edges/state buy us over a while-loop?

## 6. Dagger

Inspect how functions, containers, caching, and modules encode repeatable execution.

Question: which validation steps become more reliable when the agent sees one high-level `validate` result instead of orchestrating shell commands itself?

## 7. Nx

Inspect project graph and generator APIs.

Question: which forms of "coding" are actually repeatable transformations that should become generators?

## 8. OpenHands SDK

Inspect agent, conversation, terminal, file-editor, workspace, and Agent Server boundaries.

Question: what belongs inside the reasoning worker versus the outer graph?

## 9. Hatchet

Inspect workflow/task definitions, retries, durability, and self-hosting.

Question: after the graph works locally, which failure modes require durable execution rather than more model intelligence?

## Suggested experiment

Break one import in a disposable ABA-derived workspace.

1. Let deterministic validation capture the exact type error.
2. Run with no coding worker: expect `needs_reasoning`.
3. Enable a coding worker with one attempt.
4. Compare changed files and validation evidence.
5. Repeat with an intentionally harder behavioral bug.
6. Record where the cost is coming from: environment setup, search, reasoning, or verification.
