from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from graph_study.acceptance import run_all, run_case


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # silence test output
        pass

    def _json(self, code: int, obj: object) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/principals":
            self._json(201, {"principal_id": "p-1", "kind": payload.get("kind"),
                             "name": payload.get("name"), "state": "active"})
        elif self.path.endswith("/credentials"):
            resource = payload.get("resource")
            if resource not in ("db:reports", "k8s:ns/team-a"):
                self._json(400, {"error": "invalid_scope", "resource": resource})
            elif resource == "k8s:ns/team-a":
                self._json(403, {"error": "denied", "resource": resource,
                                 "action": payload.get("action")})
            else:
                self._json(200, {"credential_id": "c-1", "principal_id": "p-1",
                                 "resource": resource, "action": payload.get("action"),
                                 "expires_at": "2026-10-06T01:00:00Z"})
        elif self.path == "/operations":
            self._json(200, {"ok": True, "credential_id": payload.get("credential_id")})
        else:
            self._json(404, {"error": "not_found"})

    def do_GET(self) -> None:
        if self.path == "/audit":
            self._json(200, {"events": [{"actor": "p-1", "action": "read", "decision": "allow"}]})
        elif self.path == "/":
            self._html(
                '<div data-testid="principals-table"></div>'
                '<div data-testid="resources-table"></div>'
                '<div data-testid="leases-table"></div>'
                '<div data-testid="audit-table"></div>'
                '<div data-testid="revocation-form"></div>'
            )
        else:
            self._json(404, {"error": "not_found"})


@pytest.fixture()
def base_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()


def _case(case_id: str, steps: list[dict], expect: dict, ref: str = "C-API-01") -> dict:
    return {
        "schema": "graph-study.benchmark.case.v1",
        "case_id": case_id,
        "scenario": "test",
        "contract_ref": ref,
        "invariant_ref": None,
        "steps": steps,
        "expect": expect,
    }


def test_single_step_pass(base_url: str) -> None:
    case = _case(
        "case-01",
        [{"method": "POST", "path": "/principals", "body": {"kind": "agent", "name": "a"}}],
        {"status": 201, "json_subset": {"kind": "agent", "state": "active"}},
    )

    result = run_case(base_url, case)

    assert result["passed"] is True
    assert result["detail"] == []


def test_substitution_between_steps(base_url: str) -> None:
    case = _case(
        "case-02",
        [
            {"method": "POST", "path": "/principals", "body": {"kind": "service", "name": "s"}},
            {"method": "POST", "path": "/principals/{principal_id}/credentials",
             "body": {"resource": "db:reports", "action": "read"}},
        ],
        {"status": 200, "json_subset": {"resource": "db:reports"}},
    )

    result = run_case(base_url, case)

    assert result["passed"] is True
    assert result["steps"][1]["path"] == "/principals/p-1/credentials"


def test_status_mismatch_fails(base_url: str) -> None:
    case = _case(
        "case-03",
        [{"method": "POST", "path": "/principals", "body": {"kind": "agent", "name": "a"}}],
        {"status": 200},
    )

    result = run_case(base_url, case)

    assert result["passed"] is False
    assert any("status 201" in d for d in result["detail"])


def test_json_subset_mismatch_fails(base_url: str) -> None:
    case = _case(
        "case-04",
        [{"method": "POST", "path": "/principals", "body": {"kind": "agent", "name": "a"}}],
        {"status": 201, "json_subset": {"state": "disabled"}},
    )

    result = run_case(base_url, case)

    assert result["passed"] is False


def test_gui_testids_and_audit(base_url: str) -> None:
    gui = _case(
        "case-05",
        [{"method": "GET", "path": "/", "body": None}],
        {"status": 200, "gui_testids": ["principals-table", "revocation-form"]},
        ref="C-GUI-01",
    )
    audit = _case(
        "case-06",
        [{"method": "GET", "path": "/audit", "body": None}],
        {"status": 200, "audit_contains": {"actor": "p-1", "decision": "allow"}},
        ref="C-AUDIT-01",
    )

    assert run_case(base_url, gui)["passed"] is True
    assert run_case(base_url, audit)["passed"] is True


def test_run_all_summary(base_url: str) -> None:
    ok = _case(
        "case-07",
        [{"method": "GET", "path": "/audit", "body": None}],
        {"status": 200},
    )
    bad = _case(
        "case-08",
        [{"method": "GET", "path": "/audit", "body": None}],
        {"status": 500},
    )

    summary = run_all(base_url, [ok, bad])

    assert summary["total"] == 2
    assert summary["passed"] == 1
