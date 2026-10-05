from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

OUTPUT_LIMIT = 20_000


@dataclass
class CommandEvidence:
    command: str
    returncode: int
    stdout: str
    stderr: str
    started_at: str
    finished_at: str


@dataclass
class ValidationEvidence:
    ok: bool
    commands: list[CommandEvidence]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bounded(text: str) -> str:
    return text if len(text) <= OUTPUT_LIMIT else text[-OUTPUT_LIMIT:]


def _timeout_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def run_command(command: str, cwd: Path, *, timeout: int = 900) -> CommandEvidence:
    started = _now()
    try:
        proc = subprocess.run(
            shlex.split(command),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        return CommandEvidence(
            command=command,
            returncode=proc.returncode,
            stdout=_bounded(proc.stdout or ""),
            stderr=_bounded(proc.stderr or ""),
            started_at=started,
            finished_at=_now(),
        )
    except subprocess.TimeoutExpired as exc:
        return CommandEvidence(
            command=command,
            returncode=124,
            stdout=_bounded(_timeout_text(exc.stdout)),
            stderr=_bounded(_timeout_text(exc.stderr) + "\nTIMEOUT"),
            started_at=started,
            finished_at=_now(),
        )
    except OSError as exc:
        return CommandEvidence(
            command=command,
            returncode=127,
            stdout="",
            stderr=str(exc),
            started_at=started,
            finished_at=_now(),
        )


def validate_workspace(workspace: Path, commands: Iterable[str]) -> ValidationEvidence:
    evidence: list[CommandEvidence] = []
    for command in commands:
        result = run_command(command, workspace)
        evidence.append(result)
        if result.returncode != 0:
            return ValidationEvidence(ok=False, commands=evidence)
    return ValidationEvidence(ok=True, commands=evidence)


def scaffold_from_app_builder(
    app_builder_root: Path,
    workspace: Path,
    *,
    source_commit: str,
    spec_path: Path | None = None,
) -> None:
    template = app_builder_root / "templates" / "react-vite-shadcn"
    if not template.is_dir():
        raise FileNotFoundError(f"app-builder template not found: {template}")

    if workspace.exists():
        marker = workspace / ".graph-study.json"
        if marker.is_file():
            return
        if any(workspace.iterdir()):
            raise RuntimeError(f"refusing non-empty unowned workspace: {workspace}")
        workspace.rmdir()

    workspace.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, workspace)

    metadata = {
        "schema_version": "graph-engineering-study.workspace.v1",
        "source": "Pukujan/app-builder-automation",
        "source_commit": source_commit,
        "template": "templates/react-vite-shadcn",
        "created_at": _now(),
    }
    (workspace / ".graph-study.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    if spec_path is not None:
        (workspace / "GRAPH_SPEC.md").write_text(
            spec_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def write_evidence(root: Path, run_id: str, payload: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{run_id}.json"
    path.write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def evidence_to_dict(evidence: ValidationEvidence) -> dict:
    return {
        "ok": evidence.ok,
        "commands": [asdict(item) for item in evidence.commands],
    }


def run_coding_worker(
    command_template: str,
    *,
    workspace: Path,
    task_file: Path,
    attempt: int,
    timeout: int = 1800,
) -> CommandEvidence:
    rendered = command_template.format(
        workspace=str(workspace),
        task_file=str(task_file),
        attempt=attempt,
    )
    env = os.environ.copy()
    env.update(
        {
            "GRAPH_STUDY_WORKSPACE": str(workspace),
            "GRAPH_STUDY_TASK_FILE": str(task_file),
            "GRAPH_STUDY_ATTEMPT": str(attempt),
        }
    )
    started = _now()
    try:
        proc = subprocess.run(
            shlex.split(rendered),
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        return CommandEvidence(
            command=rendered,
            returncode=proc.returncode,
            stdout=_bounded(proc.stdout or ""),
            stderr=_bounded(proc.stderr or ""),
            started_at=started,
            finished_at=_now(),
        )
    except subprocess.TimeoutExpired as exc:
        return CommandEvidence(
            command=rendered,
            returncode=124,
            stdout=_bounded(_timeout_text(exc.stdout)),
            stderr=_bounded(_timeout_text(exc.stderr) + "\nTIMEOUT"),
            started_at=started,
            finished_at=_now(),
        )
    except OSError as exc:
        return CommandEvidence(
            command=rendered,
            returncode=127,
            stdout="",
            stderr=str(exc),
            started_at=started,
            finished_at=_now(),
        )
