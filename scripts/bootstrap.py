#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_study.sources import resolve_sources_dir  # noqa: E402

VENV = ROOT / ".venv"


def run(argv: list[str]) -> None:
    print("+", " ".join(str(x) for x in argv))
    subprocess.run(argv, cwd=ROOT, check=True)


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap the zero-inference study lab"
    )
    parser.add_argument(
        "--hotload",
        action="store_true",
        help="also invoke the real ACS hotloader",
    )
    parser.add_argument(
        "--stack-only",
        action="store_true",
        help="fetch only stack sources; skip OSS/reference study sources",
    )
    args = parser.parse_args()

    group = "stack" if args.stack_only else "all"
    run([sys.executable, "scripts/fetch_sources.py", "--group", group])

    if not VENV.exists():
        venv.EnvBuilder(with_pip=True).create(VENV)

    py = str(venv_python())
    sources = resolve_sources_dir(ROOT)

    if not args.stack_only:
        run([py, "-m", "pip", "install", "-e", str(sources / "pydantic-ai" / "pydantic_graph")])
        run([py, "-m", "pip", "install", "-e", "."])
        run([py, "-m", "pip", "install", "pytest"])

    oio_requirements = sources / "observational-issue-ops" / "requirements.txt"
    if oio_requirements.is_file():
        run([py, "-m", "pip", "install", "-r", str(oio_requirements)])

    if args.hotload:
        run([py, "scripts/install_hotload.py"])

    print("\nBootstrap complete. No coding model was called.")
    if not args.stack_only:
        print(f"Python: {py}")
        print("Next: run graph-study diagram")


if __name__ == "__main__":
    main()
