# Calibration PDD — product/problem definition

## Problem

Agents and services need access to a small set of protected resources without
being handed long-lived, broad credentials. A human operator needs to see who
holds what, revoke access, and read an audit trail of authorization decisions.

The calibration scopes this to two resources so the system is small enough to
build inside a benchmark budget while still exercising the hard parts:
scoping, deny precedence, revocation, expiry, and auditing.

## Users

- **Operator** — creates principals, grants scopes, revokes credentials, reads
  the audit log through a minimal GUI.
- **Agent / service** — requests a scoped credential for one resource and one
  action, uses it, and receives a machine-readable decision when refused.

## Behavior

1. The operator registers a principal (human, service, or agent) with a stable
   id.
2. A principal requests a credential for one resource and one action.
3. The policy engine decides whether the request is within the principal's
   granted scope. **Deny beats allow** when both match.
4. If allowed, the broker issues a short-lived credential for exactly the
   requested resource and action; it never widens the scope.
5. A revoked or expired credential authorizes nothing new.
6. Authorization-sensitive actions append an audit event.

## Resources and actions (fixed)

| Resource | Actions |
| --- | --- |
| `db:reports` | `read`, `write` |
| `k8s:ns/team-a` | `get`, `apply` |

## Non-goals (explicit)

- more than two resources, or more than one connector per resource kind;
- credential rotation, long-lived secrets, or a secret store;
- multi-provider database support, real database or cluster access;
- load, soak, or scale testing;
- a full MCP server (a single credential-request surface is enough);
- horizontal scaling, high availability, or durable queueing;
- authentication of the operator beyond a trusted local context.

These are deliberately out of scope. The full IAM benchmark (issue #2) covers
them; the calibration exists to validate the harness, not the product.
