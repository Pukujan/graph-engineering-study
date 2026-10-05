# Graph Engineering Control Room

Build the smallest useful GUI for studying a software-engineering graph.

## Required surfaces

- current graph node and run status;
- ordered run timeline;
- deterministic validation results with command, exit code, and bounded logs;
- repair attempt count and maximum;
- coding-worker enabled/disabled indicator;
- source revision of the app-builder substrate;
- evidence-file link/location;
- clear distinction between "usable" and "verified".

## Design constraints

Use the existing React/Vite/shadcn substrate. Do not replace project setup, routing, or UI primitives unless the spec explicitly requires it.

The first version may use fixture JSON. It does not need a hosted backend.

## Acceptance hooks

The UI should expose stable test IDs:

- graph-status
- run-timeline
- validation-results
- repair-budget
- worker-status
- evidence-location
