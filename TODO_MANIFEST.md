# WayFare TODO Manifest

Last updated: 2026-03-19

This file is the execution manifest for Codex.

Primary product goal:

> Keep WayFare stable enough for real user testing, with the knowledge workflow and schedule workflow both usable out of the box.

---

## Current Status

### Already completed baseline

The following chain is now implemented in the active dev path:

1. knowledge base creation is backend-first
2. document upload uses the backend contract
3. parse status returns to the workspace UI
4. reader can open uploaded files
5. AI chat is wired through the current knowledge base and document set
6. fallback behavior exists when DB or model services are unavailable

This means the old split between localStorage knowledge base metadata and backend document state is no longer the main execution path.

---

## Current Top Priorities

### P0 - Finish operational stability for testing

1. Add environment / smoke scripts
2. Clean stale release and startup docs
3. Verify packaged startup path against the new portable API contract

### P1 - Make the schedule board feel like part of the same product

4. Bind schedule items to real knowledge bases
5. Allow creating a schedule from inside a workspace
6. Show real knowledge base tags on the schedule timeline

### P2 - Hardening and shipping

7. Deployment hardening
8. Feedback logging / lightweight analytics
9. Additional UI polish

---

## Task Details

### P0-5. Dev Workflow / Environment Stability

Goal:

> A developer should be able to tell whether WayFare is healthy in under 2 minutes.

Required scripts:

- `check_env.ps1` or similar
- verify:
  - Astro frontend reachable
  - Go backend reachable
  - Python sidecar reachable
  - `/healthz` works
  - knowledge base CRUD works
  - upload works
  - chat endpoint works

Acceptance criteria:

- there is one documented dev start path
- there is one documented environment check path

---

### P1-1. Schedule Board Real Association

Problem:

The schedule UI is visually in place, but the knowledge base tag is still placeholder-level.

Goal:

> Bind schedules to a real knowledge base or real scope label.

Required behavior:

- schedule item stores `knowledgeBaseId` or an equivalent scope field
- schedule UI renders the real tag text
- optional: create a schedule from inside a workspace

Acceptance criteria:

- a tester can tell which knowledge base a proactive task belongs to

---

### P1-2. Smoke Test Scripts

Goal:

Replace manual regression with fast smoke checks.

Desired checks:

- create knowledge base
- upload sample document
- list documents
- hit `/healthz`
- call `/chat`
- create schedule
- complete / reschedule schedule

---

### P1-3. Documentation Cleanup

Goal:

Remove stale instructions that refer to the deleted embedded portable UI or outdated startup assumptions.

Likely files:

- `README_QUICKSTART.txt`
- `MVP_TEST_CHECKLIST.md`
- release/startup docs that still mention the removed old UI

---

## Codex Execution Prompt Template

Use this template for future runs:

> Reference `ARCHITECTURE.md` and `TODO_MANIFEST.md` first.
> Treat the current Portable Mode API contract as the canonical dev/test path.
> Do not patch a single file in isolation.
> Make changes flow-first and run verification after edits.
> Final output must include changed files, remaining blockers, and the next best task.

---

## Execution Rule for Future Runs

Codex should optimize for:

1. fewer human handoffs
2. fewer contract mismatches
3. faster validation
4. more stable tester-facing flows

In short:

> Keep the MVP runnable, then keep it shippable.
