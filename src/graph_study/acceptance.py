"""Arm-neutral acceptance runner for the calibration benchmark (issue #2).

Replays a case's steps against a running arm over HTTP and checks the expected
outcome. It is deliberately implementation-blind: it speaks only the
``contract.md`` surface, so the same cases produce comparable evidence for both
arms.

Values captured from one step's response are substituted into later steps, so a
case can issue a credential and then use its id. The final step's response is
checked against ``expect``.

Deterministic: a case passes or fails on HTTP status and JSON subset only.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from urllib.parse import urljoin

_TOKEN_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def _subst(value: object, context: dict) -> object:
    if isinstance(value, str):
        return _TOKEN_RE.sub(lambda m: str(context.get(m.group(1), m.group(0))), value)
    if isinstance(value, dict):
        return {k: _subst(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_subst(v, context) for v in value]
    return value


def _request(base_url: str, step: dict) -> tuple[int, str]:
    url = urljoin(base_url.rstrip("/") + "/", step["path"].lstrip("/"))
    data = None
    headers = {}
    if step.get("body") is not None:
        data = json.dumps(step["body"]).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=step["method"], headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def _subset(expected: object, actual: object) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and _subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list)
    return expected == actual


def _body_json(text: str) -> object:
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def run_case(base_url: str, case: dict) -> dict:
    """Replay one case; return ``{case_id, passed, steps, detail}``."""

    context: dict = {}
    step_results: list[dict] = []
    last_status = 0
    last_text = ""

    for index, step in enumerate(case["steps"]):
        resolved = {
            "method": step["method"],
            "path": _subst(step["path"], context),
            "body": _subst(step.get("body"), context),
        }
        status, text = _request(base_url, resolved)
        step_results.append(
            {"index": index, "method": resolved["method"], "path": resolved["path"], "status": status}
        )
        last_status, last_text = status, text

        body = _body_json(text)
        if isinstance(body, dict):
            for key, value in body.items():
                if isinstance(value, (str, int, float, bool)):
                    context[key] = value

    expect = case["expect"]
    detail: list[str] = []

    if last_status != expect["status"]:
        detail.append(f"status {last_status} != expected {expect['status']}")

    body = _body_json(last_text)
    subset = expect.get("json_subset")
    if isinstance(subset, dict) and subset and not _subset(subset, body):
        detail.append(f"json_subset {subset} not satisfied by {body!r}")

    audit = expect.get("audit_contains")
    if isinstance(audit, dict):
        events = body.get("events") if isinstance(body, dict) else None
        if not isinstance(events, list) or not any(
            _subset(audit, event) for event in events
        ):
            detail.append(f"no audit event matching {audit}")

    testids = expect.get("gui_testids")
    if isinstance(testids, list):
        missing = [t for t in testids if f'data-testid="{t}"' not in last_text]
        if missing:
            detail.append(f"missing GUI test ids: {missing}")

    return {
        "case_id": case["case_id"],
        "passed": not detail,
        "steps": step_results,
        "detail": detail,
    }


def run_all(base_url: str, cases: list[dict]) -> dict:
    """Replay every case; return a summary and per-case results."""

    results = [run_case(base_url, case) for case in cases]
    passed = sum(1 for r in results if r["passed"])
    return {"passed": passed, "total": len(results), "results": results}
