# Agent operating notes

## Start

Read `PROJECT.md`, `PLAN.md`, and issue #1 before changing architecture.

## Non-negotiable boundaries

- Prefer deterministic code over inference whenever the output can be checked mechanically.
- The success edge belongs to deterministic validation, not to the coding model.
- Do not modify any pinned source checkout; they are read-only study/reference sources. Their location comes from `graph_study.sources.resolve_sources_dir`: `.sources/` outside the ACS dev root, the ACS deps cache inside it.
- Do not put API keys, tokens, or local absolute paths in committed files.
- Do not enable a paid coding worker by default.
- Repair loops must stay bounded.
- Keep generated/disposable work under `.workspaces/` and evidence under `.graph-evidence/`.
- Do not vendor ACS, OIO, ABA, PCM, CGM, or upstream OSS into this repository.

## Repository workflow

Use issue #1 for this initial study lab. Prefer branch + pull request delivery. Keep implementation claims separate from local verification claims: GitHub edits can establish repository structure, not that Docker, Node, browser, or local coding-agent execution succeeded.
