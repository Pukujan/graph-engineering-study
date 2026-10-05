# Architecture

## Why this is a graph instead of one long coding-agent prompt

The graph makes state transitions explicit and makes the success condition independent of the model.

```text
spec
  |
  v
scaffold -------- deterministic
  |
  v
validate -------- deterministic evidence
  | pass
  +----------------------> finish
  |
  | fail
  v
repair ---------- optional inference
  |
  v
validate -------- same deterministic evidence
```

## Node contracts

### Scaffold

Inputs: spec, target workspace, pinned app-builder source.

Responsibilities:

- copy the known React/Vite/shadcn substrate;
- never ask a model to invent package setup;
- record the source revision used;
- refuse an unexpectedly non-empty target.

### Validate

Inputs: workspace and explicit validation commands.

Responsibilities:

- run commands without model interpretation;
- capture exit codes/stdout/stderr;
- emit structured evidence;
- choose pass/fail from exit status.

Validation may later move behind Dagger. That changes execution isolation, not the edge semantics.

### Repair

Inputs: spec, latest failed validation, workspace, bounded attempt count.

Responsibilities:

- create a small repair request;
- invoke the configured coding worker;
- capture the worker exit status;
- return control to Validate.

The repair worker never owns the terminal success state.

## Where inference belongs

Inference is appropriate when the graph has evidence but no practical deterministic transformation from the evidence to a patch. Examples include root-cause diagnosis across several files, understanding user intent, and implementing novel business logic.

Inference is inappropriate for setup, type checking, formatting, linting, test execution, retries, file existence, or deciding whether a command exited successfully.

## Why the GUI is separated

The GUI is a client of run state. ABA's substrate is reused to avoid re-solving frontend setup. The graph can run headless. A GUI failure therefore cannot redefine workflow truth.

## Future replacement map

| Baseline piece | Later OSS piece | What must stay invariant |
| --- | --- | --- |
| host validation commands | Dagger | pass/fail comes from executable evidence |
| template copy | Nx generator | known scaffolding stays deterministic |
| command coding worker | OpenHands/Codex | worker cannot declare success |
| in-process graph | Hatchet | state/edge semantics stay explicit |
