# Calibration SDD — system design

## Components

| Component | Responsibility |
| --- | --- |
| API / control plane | Serves the contract endpoints; owns request validation. |
| Policy engine | Decides allow/deny for a (principal, resource, action); deny precedence; scope intersection. |
| Credential broker | Issues short-lived, resource-and-action-scoped credentials; never widens scope. |
| Database connector | Returns a scoped credential for `db:reports`. Sandbox only. |
| Kubernetes connector | Returns a scoped credential for `k8s:ns/team-a`. Sandbox only. |
| Audit service | Append-only record of authorization-sensitive actions. |
| Minimal GUI | Serves `GET /` showing principals, resources, active leases, audit, and a revocation control. |

The internal structure, language, and storage are the implementing arm's choice.
Only the external surface in `contract.md` is fixed.

## Trust boundaries

- **Operator ↔ API** — a trusted local context; no operator authentication is
  modeled in the calibration.
- **Principal ↔ broker** — the untrusted boundary. A principal may request only
  what its grants allow, and a connector may not mint a broader downstream
  credential than the broker granted.
- **Broker ↔ connector** — the connector is treated as potentially returning a
  broader scope than requested; the broker must clamp or refuse it.
- **System ↔ audit store** — audit records are append-only from the
  application's point of view.

## Lease state machine

```text
requested -> issued -> active -> { revoked | expired }
```

- A credential moves to `revoked` when the operator revokes it, and to `expired`
  when its lifetime passes.
- Neither terminal state authorizes a new protected operation after the
  transition point.
- A revoked or expired credential is not silently renewed; renewal requires a
  fresh decision.

## Failure semantics

- A request outside the granted scope is **denied**, never partially granted.
- A connector failure during issuance issues **no** credential (fail closed).
- A malformed or ambiguous resource scope is rejected, not guessed.
- A duplicate request with the same request id does not create additional
  privilege.
- An authorization decision that cannot be made is a deny, not an allow.

## Data ownership

- Principals, grants, and leases are owned by the control plane.
- Audit events are owned by the audit service and are append-only.
- Connectors own no durable state beyond the credential they mint for one
  request.

## Formal targets

- One TLA+ model of the lease state machine, covering lease/revocation ordering
  and the revocation-monotonicity invariant.
- One SMT (Z3) property over the policy engine, covering deny precedence and
  scope intersection.

Both must be registered with their property, model boundary, assumptions,
counterexample behavior, and implementation links, per the invariant registry.
