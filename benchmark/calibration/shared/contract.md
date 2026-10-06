# Calibration contract (normative)

This is the externally visible surface both arms must implement. Section ids
(`C-API-01`, `C-ERR-01`, …) are stable: acceptance cases and hidden holdouts
reference them, so a check means the same thing for both arms.

All request and response bodies are JSON. Timestamps are ISO-8601 UTC ending in
`Z`. Field names are case-sensitive.

## C-API-01 — Create principal

```text
POST /principals
{ "kind": "human" | "service" | "agent", "name": "<string>" }
-> 201 { "principal_id": "<string>", "kind": "<kind>", "name": "<string>", "state": "active" }
```

`principal_id` is stable for the principal's lifetime.

## C-API-02 — Request a scoped credential

```text
POST /principals/{principal_id}/credentials
{ "resource": "<resource>", "action": "<action>", "request_id": "<string>" }
-> 200 { "credential_id": "<string>", "principal_id": "<string>",
         "resource": "<resource>", "action": "<action>", "expires_at": "<iso8601>" }
```

- The issued credential is scoped to exactly the requested `resource` and
  `action`; the broker never widens it.
- `request_id` is idempotent: the same `request_id` repeated returns the same
  credential and creates no additional privilege.
- A request outside the principal's granted scope is refused per `C-ERR-01`.
- A resource outside the fixed set (`db:reports`, `k8s:ns/team-a`) is refused
  per `C-ERR-03`.

## C-API-03 — Authorization decision

```text
POST /decisions
{ "principal_id": "<string>", "resource": "<resource>", "action": "<action>" }
-> 200 { "allowed": <bool>, "reason": "<string>", "matched_rules": ["<string>", ...] }
```

- Deny beats allow when both match: if any applicable deny matches, `allowed`
  is `false`.
- The decision is explainable: `reason` names why, and `matched_rules` lists the
  rules that applied.

## C-API-04 — Revoke a credential

```text
POST /revocations
{ "credential_id": "<string>" }
-> 200 { "credential_id": "<string>", "revoked_at": "<iso8601>" }
```

After `revoked_at`, the credential authorizes no new protected operation. A
later attempt to use it is refused per `C-ERR-02`.

## C-API-05 — Audit log

```text
GET /audit
-> 200 { "events": [ <audit-event>, ... ] }
```

Audit events are append-only from the application's point of view. Each event
follows `C-AUDIT-01`.

## C-API-06 — GUI

```text
GET /  -> 200 text/html
```

The served HTML contains the elements required by `C-GUI-01`.

## C-API-07 — Perform a protected operation

```text
POST /operations
{ "credential_id": "<string>", "resource": "<resource>", "action": "<action>" }
-> 200 { "ok": true, "credential_id": "<string>" }
```

- The credential must still be active: revoked or expired credentials are
  refused per `C-ERR-02`.
- A credential used outside the resource/action it was issued for is refused
  per `C-ERR-01`.

## C-ERR-01 — Denial

A refused authorization or credential request returns HTTP `403`:

```text
{ "error": "denied", "reason": "<string>", "principal_id": "<string>",
  "resource": "<resource>", "action": "<action>" }
```

## C-ERR-02 — Revoked or expired credential

Use of a revoked or expired credential returns HTTP `403`:

```text
{ "error": "expired" | "revoked", "credential_id": "<string>", "reason": "<string>" }
```

## C-ERR-03 — Malformed or unknown scope

An unknown resource, unknown action, or malformed scope returns HTTP `400`:

```text
{ "error": "invalid_scope", "reason": "<string>", "resource": "<string>", "action": "<string>" }
```

## C-AUDIT-01 — Audit event format

Every authorization-sensitive action appends one event:

```text
{ "at": "<iso8601>", "actor": "<principal_id>", "action": "<string>",
  "resource": "<resource>", "decision": "allow" | "deny", "credential_id": "<string>" | null }
```

## C-GUI-01 — Required GUI elements

The page served at `GET /` contains elements with these `data-testid` values:

| test id | shows |
| --- | --- |
| `principals-table` | known principals |
| `resources-table` | the two fixed resources |
| `leases-table` | active credentials/leases |
| `audit-table` | recent audit events |
| `revocation-form` | the control to revoke a credential |

## Fixed vocabulary

- Resources: `db:reports`, `k8s:ns/team-a`.
- Actions: `db:reports` → `read`, `write`; `k8s:ns/team-a` → `get`, `apply`.
- Decision values: `allow`, `deny`.
