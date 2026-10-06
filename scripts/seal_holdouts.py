#!/usr/bin/env python3
"""Seal a holdout directory into a sha256 manifest before either arm runs.

Writes a ``sha256sum``-format manifest and prints the package digest to record
in the freeze record's ``holdouts.manifest_sha256``. The holdout *contents* stay
outside both arms' context; only the digest is shared. Verify later with
``sha256sum -c <manifest>`` on any POSIX host.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.benchmark import seal_holdouts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="directory holding the hidden holdout cases")
    parser.add_argument(
        "--out",
        default=None,
        help="manifest path (default: <directory>.manifest.sha256, a sibling file)",
    )
    args = parser.parse_args()

    directory = Path(args.directory)
    result = seal_holdouts(directory)
    out = Path(args.out) if args.out else directory.with_suffix(".manifest.sha256")
    out.write_text(result["manifest"], encoding="utf-8")

    print(f"sealed {result['files']} file(s)")
    print(f"package_sha256 {result['package_sha256']}")
    print(f"manifest {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
