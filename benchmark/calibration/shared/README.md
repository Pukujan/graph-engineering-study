# Calibration task — shared bundle

Both benchmark arms (A: a plain coding harness; B: this repository's graph path)
receive **exactly this directory** and nothing else about the task. Nothing in
here may be tailored to either arm.

The calibration is a small identity-and-access system, not the full IAM platform
from issue #2. Its purpose is to prove the experiment harness — timing, evidence
capture, isolation, and the sealed holdouts — before the full benchmark starts.

## Contents

| File | Role |
| --- | --- |
| `pdd.md` | Problem, users, behavior, and explicit non-goals. |
| `sdd.md` | Components, trust boundaries, state machines, failure semantics. |
| `contract.md` | **Normative.** The externally visible HTTP surface both arms must implement. |

## Rules

- Both arms start from the same empty starting repository at the frozen
  `starting_repo_commit`.
- The contract is the only place the external interface is fixed. Internal
  language, framework, and structure are the arm's choice.
- Acceptance checks and hidden holdouts are written against `contract.md`
  section ids, so a passing check means the same thing for both arms.
- No arm sees the hidden holdouts before the build cutoff, and no arm sees the
  other arm's implementation.
- The resources, actions, and GUI test ids are fixed (see `contract.md`) so the
  two systems are comparable; everything else is open.
