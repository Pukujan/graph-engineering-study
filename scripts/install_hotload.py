#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / ".sources"

ACS = SOURCES / "agent-custom-setup"
PCM = SOURCES / "project-continuity-modules"
CGM = SOURCES / "content-generation-modules"
OIO = SOURCES / "observational-issue-ops"
INSTALLER = (
    ACS
    / "modules"
    / "coordination"
    / "multi-agent-hotload"
    / "v0.1.0"
    / "scripts"
    / "acs_install.py"
)


def require(path: Path, description: str) -> None:
    if not path.exists():
        raise SystemExit(
            f"missing {description}: {path}. Run scripts/bootstrap.py first."
        )


def main() -> None:
    require(ROOT / ".content-system", "CGM adopter adapter")
    require(INSTALLER, "ACS hotload installer")
    require(PCM, "PCM checkout")
    require(CGM, "CGM checkout")
    require(OIO, "OIO checkout")

    argv = [
        sys.executable,
        str(INSTALLER),
        "--adopter-root",
        str(ROOT),
        "--pcm-root",
        str(PCM),
        "--cgm-root",
        str(CGM),
        "--oio-root",
        str(OIO),
    ]
    print("+", " ".join(argv))
    raise SystemExit(
        subprocess.run(argv, cwd=ROOT, check=False).returncode
    )


if __name__ == "__main__":
    main()
