# IAM A/B benchmark protocol

This is the frozen contract for the benchmark described in issue #2. It exists
so the comparison between a plain coding harness (Arm A) and this repository's
graph-engineered factory (Arm B) is decided by evidence the operator can
inspect, not by which arm looked more finished.

The benchmark is an **experiment**. It uses disposable infrastructure and
synthetic credentials only. No arm touches real production credentials,
database roles, or cluster-admin access.

## Arms

| Arm | What it is | What it receives |
| --- | --- | --- |
| A | one strong coding harness, chosen by the operator | the same spec, starting repo, reference docs, model family, budgets, and test infrastructure as Arm B |
| B | this repository's graph path: OIO-style intake, deterministic generators, ABA GUI substrate, typed workflow state, deterministic gates, a subordinate coding worker, bounded repair, durable evidence | the same inputs as Arm A |

The coding worker in Arm B may be the same model or harness as Arm A. The
difference under test is **who owns the process**: in Arm A the agent decides
its own sequence; in Arm B the graph owns state, routing, and the success edge,
and the worker is a bounded repair edge.

Neither arm may see the other's implementation, and neither may weaken or
remove acceptance checks to improve its score.

## Freeze before either arm starts

Both arms must begin from equivalent conditions, so the experiment is frozen
first. Copy `benchmark/freeze.template.json` to `benchmark/freeze.json`, fill
every field, and run:

```bash
python scripts/check_freeze.py benchmark/freeze.json
```

The record is complete only when that command prints `COMPLETE`. Commit the
completed record before starting either arm; its commit is the point after
which the freeze may not change.

The record pins, at minimum:

- the task-spec commit and the starting-repository commit;
- each arm's harness and model;
- wall-clock, monetary, token, and hardware budgets;
- the sandbox's credentials and infrastructure;
- the PDD and SDD commits supplied to both arms;
- the formal methods in scope;
- the holdout manifest hash, created before the start;
- confirmation that usability and robustness are scored separately.

## Hidden holdouts

Prepare the holdout cases before either implementation starts and keep their
contents outside both arms' context. Only the digest is shared. Seal them with:

```bash
python scripts/seal_holdouts.py <holdout-dir>
```

That writes a `sha256sum`-format manifest and prints a `package_sha256`, which
is the value recorded in `holdouts.manifest_sha256`. Verify the sealed package
later with `sha256sum -c <manifest>` on any POSIX host. The holdout runner
produces machine-readable evidence only after the build cutoff.

Suggested holdouts (from issue #2): stale/revoked session race, deny/allow
policy conflict, connector minting broader credentials than requested, provider
transient failure during issuance, cluster unreachable after authorization,
duplicate/replayed MCP request, principal deletion during an active lease,
clock skew around expiry, partial audit-store outage, malformed resource scope,
policy migration N to N+1, concurrent agents requesting overlapping scopes.

## Measurement

Track from the first command, not the first model token. Record each arm's
milestones to its `timeline.jsonl` with the deterministic recorder:

```bash
python scripts/benchmark_timeline.py record <arm>/timeline.jsonl start
python scripts/benchmark_timeline.py record <arm>/timeline.jsonl first_build
python scripts/benchmark_timeline.py summary <arm>/timeline.jsonl
```

`record` stamps UTC ISO-8601 and rejects unknown milestones; `summary` prints
elapsed seconds per milestone and exits non-zero if the timeline is not
monotonic. The four axes are:

- **Speed** — time to bootstrap, first compiling build, first usable end-to-end
  flow, first security gate passing, all visible acceptance tests, holdout
  completion, and post-cutoff repair.
- **Human effort** — operator interventions, architecture clarifications, manual
  environment repairs, manual bug fixes, and model claims of success that the
  gates did not confirm.
- **Inference/cost** — model calls, tokens, coding-worker calls, monetary cost,
  and the share of nodes completed with zero inference.
- **Quality and robustness** — compile/lint/type failures, visible and holdout
  test failures, regressions, security-invariant violations, unresolved races,
  architecture drift from the SDD, severity-weighted bug count, and clean-machine
  reproducibility.

Robustness is evaluated separately from usability. A system can be pleasant and
fragile, or ugly and correct.

## Scoring

Score both arms on usability, UI coherence, feature completeness, correctness,
security behavior, failure clarity, operational robustness, maintainability, and
inspectability/auditability. Keep **usable** and **robust** as separate scores.
The final report distinguishes observed evidence from evaluator judgment.

## Stop conditions

Each arm stops at the first of: full acceptance target reached; wall-clock
budget exhausted; monetary/token budget exhausted; unrecoverable environment
failure; or operator termination. Do not extend one arm because it is close to
finishing unless the same extension is given to the other arm.

## Run layout

Durable contract files are committed; run outputs are disposable and live under
`.workspaces/benchmark/` (git-ignored). Each arm's run directory follows the
result format from issue #2:

```text
.workspaces/benchmark/
  arm-a/        manifest.json  timeline.jsonl  evidence/  screenshots/  final-report.md
  arm-b/        manifest.json  timeline.jsonl  evidence/  screenshots/  final-report.md
  holdouts/     manifest.sha256
  comparison/   metrics.json  bugs.json  result.md
```

Record the exact final commit of each arm. Fixes applied after the cutoff are
recorded as post-benchmark repair time, never folded into the timed build.

## Scale

Before the full IAM benchmark, run the smaller calibration task from issue #2
(identity registry, two-resource policy engine, one database connector, one
Kubernetes sandbox connector, minimal GUI, revocation, audit log, one TLA+ state
machine, one SMT policy property, five hidden holdouts). Only once timing,
evidence capture, and isolation are proven should the full benchmark start.

## Formal methods

Formal methods are used only where they match the property being checked, and
every proof or model states: the property, the model boundary, the assumptions,
the counterexample/failure behavior, and the connection to the executable
implementation. A proof is never treated as proof of the whole implementation
outside its modeled assumptions.

Record each named invariant in a registry and check it before scoring:

```bash
python scripts/check_invariants.py formal/invariants.json
```

`formal/invariants.template.json` lists the invariants named in issue #2 with
their fields left empty, so the registry fails closed until a human ties each
one down. The checker rejects a record that omits any of the five items, names a
method outside TLA+, Lean 4, or SMT, or leaves the assumptions or implementation
links empty.

## Boundaries

- No real production credentials, database roles, or cluster-admin access.
- No arm may weaken or remove acceptance checks to improve its score.
- No coding model gets access to hidden holdout cases before the cutoff.
- The freeze record is not a formality: an incomplete record means the
  experiment has not started.
