# Calibration holdouts

Five hidden cases are prepared before either benchmark arm starts, sealed into a
manifest, and kept out of both arms' context. Only the digest is shared.

## Where the cases live

The case **contents** are not committed. They live outside the repository in a
directory the operator owns and keeps private:

```text
<private-holdout-dir>/
  h-01.json  h-02.json  h-03.json  h-04.json  h-05.json
```

The starter set in this repository is staged at
`.workspaces/benchmark/calibration-holdouts/`, which is git-ignored. The operator
owns these cases: relocate them somewhere durable and private before sealing a
real run, and regenerate the manifest if the set changes. A disposable
`.workspaces/` tree may be cleaned at any time, so do not rely on it as the
permanent store.

Each case uses the same schema as the visible acceptance cases
(`graph-study.benchmark.case.v1`), so the same runner replays both.

## Sealing

```bash
python scripts/seal_holdouts.py <private-holdout-dir> \
  --out benchmark/calibration/holdouts.manifest.sha256
```

That writes a `sha256sum`-format manifest and prints a `package_sha256`. Record
that digest in the freeze record as `holdouts.manifest_sha256`, and record the
digest of the shared task bundle as `task_materials.package_sha256`. Then check:

```bash
python scripts/check_task_materials.py benchmark/freeze.json
```

It re-seals the shared bundle and validates the holdout manifest — well-formed,
exactly five entries, and matching the freeze digests. CI validates manifest
**structure** only; the contents are verified at run time with
`sha256sum -c benchmark/calibration/holdouts.manifest.sha256`.

## What the five cover

| Case | Scenario | Invariant |
| --- | --- | --- |
| h-01 | credential revoked concurrently with an in-flight operation | `revocation-monotonicity` |
| h-02 | an allow and a deny both match; deny must win | `deny-beats-allow` |
| h-03 | connector returns a broader credential than requested | `connector-no-broader-mint` |
| h-04 | duplicated credential request with the same request id | `replay-no-extra-privilege` |
| h-05 | credential used past expiry under clock skew | `expired-lease-requires-fresh-decision` |

## Boundary

Neither arm sees these before the build cutoff. The holdout runner produces
machine-readable evidence only after the cutoff. Do not commit the case
contents, and do not let them enter either arm's working context.
