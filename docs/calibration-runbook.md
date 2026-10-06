# Calibration runbook

The ordered operator steps for the calibration benchmark. Every check here is
deterministic; none of them runs an arm or makes an inference call. The arms are
started by the operator, not by this tooling.

## Before anything

Decide, and write into the freeze record, the choices only the operator can make:

- which harness and model each arm uses (Arm A and Arm B may share a model);
- wall-clock, monetary, and token budgets, and the hardware class;
- the sandbox credentials (synthetic only) and infrastructure (disposable).

Until these are set, `check_freeze` fails closed — an incomplete freeze is not a
started experiment.

## Steps

### 1. Prepare the holdouts

Copy the starter holdouts out of the git-ignored staging directory to a private
location outside the repository (see `benchmark/calibration/HOLDOUTS.md`). The
contents must stay out of both arms' context.

### 2. Seal the holdouts

```bash
python scripts/seal_holdouts.py <private-holdout-dir> \
  --out benchmark/calibration/holdouts.manifest.sha256
```

Record the printed `package_sha256` as `holdouts.manifest_sha256`.

### 3. Pin the shared task bundle

```bash
python -c "import sys; sys.path.insert(0,'src'); from pathlib import Path; \
from graph_study.benchmark import directory_package_sha256 as d; \
print(d(Path('benchmark/calibration/shared')))"
```

Record the digest as `task_materials.package_sha256`.

### 4. Fill the freeze record

```bash
cp benchmark/freeze.template.json benchmark/freeze.json
# set every field, including task_materials.package_sha256 and holdouts.manifest_sha256
```

### 5. Check every gate

```bash
python scripts/check_freeze.py benchmark/freeze.json
python scripts/check_task_materials.py benchmark/freeze.json
python scripts/check_invariants.py formal/invariants.json
python scripts/check_cases.py benchmark/calibration/acceptance \
  --contract benchmark/calibration/shared/contract.md \
  --invariants formal/invariants.json
```

All four must report COMPLETE / PINNED. Then commit the freeze record; its
commit is the point after which the freeze may not change.

### 6. Run the arms

Start each arm from the same `starting_repo_commit`, giving each exactly the
`benchmark/calibration/shared/` bundle. Record milestones as they happen:

```bash
python scripts/benchmark_timeline.py record .workspaces/benchmark/arm-a/timeline.jsonl start
python scripts/benchmark_timeline.py record .workspaces/benchmark/arm-a/timeline.jsonl first_build
# ...
```

### 7. Score the visible acceptance cases

```bash
python scripts/run_acceptance.py --base-url <arm-a-url> \
  --cases benchmark/calibration/acceptance --out .workspaces/benchmark/arm-a/evidence/acceptance.json
```

### 8. Replay the holdouts after the cutoff

Verify the sealed package, then replay it with the same runner:

```bash
sha256sum -c benchmark/calibration/holdouts.manifest.sha256
python scripts/run_acceptance.py --base-url <arm-url> \
  --cases <private-holdout-dir> --out .workspaces/benchmark/<arm>/evidence/holdouts.json
```

### 9. Build the comparison

Assemble `.workspaces/benchmark/comparison/` from both arms' timelines, acceptance
and holdout evidence, and the operator's scores. Keep usability and robustness
separate, and keep observed evidence distinct from evaluator judgment.

## What this tooling does not do

- It does not choose the harness, model, budgets, hardware, or sandbox.
- It does not start, stop, or extend either arm.
- It does not author the proofs or models; it checks that each is fully
  specified in the invariant registry.
- It does not verify holdout *contents* in CI — only the sealed manifest's
  structure. Contents are verified at run time with `sha256sum -c`.
