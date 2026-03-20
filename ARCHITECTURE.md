# WayFare Architecture Anchor

Last updated: 2026-03-19

## 1. Purpose

This document is the context anchor for Codex work on WayFare.

Current product goal:

> Keep the MVP stable enough for real user testing, with end-to-end reliability taking priority over extra polish.

The key question is:

> Can a tester create a knowledge base, upload material, wait for parsing, open a document, and talk to AI without manual repair work?

---

## 2. Product Scope

WayFare currently has two user-facing pillars:

1. Knowledge Workspace
   - create a knowledge base
   - upload documents
   - observe parsing status
   - preview documents in the reader
   - ask AI about current material

2. Proactive Schedule Board
   - create recurring / one-off tasks
   - receive browser notifications
   - complete / snooze / reschedule tasks

---

## 3. Current Stack

### Frontend

- Framework: Astro
- Mode: SSR
- Adapter: @astrojs/node
- Styling: Tailwind
- Main pages:
  - `src/pages/dashboard.astro`
  - `src/pages/create-knowledge-base.astro`
  - `src/pages/workspace/[kbId].astro`
  - `src/pages/workspace/schedule.astro`
  - `src/pages/schedule-board.astro`

### Go Backend

- Directory: `wayfare_backend/`
- Default dev entry: `go run .`
- Default dev port:
  - `8080` for `go run .`
  - `37880` for packaged executable

### Current canonical dev/test contract

The default and official dev contract is now **Portable Mode**.

Portable Mode currently exposes:

- `/knowledge-bases`
- `/upload`
- `/documents`
- `/documents/:id/file`
- `/chat`
- `/schedules`

It uses JSON-backed stores for knowledge bases, documents, and schedules, and starts the Python sidecar for parse / retrieval / AI response generation.

### Full Mode

Full Mode still exists, but it is no longer the primary target for day-to-day MVP iteration.

Use it only when intentionally testing PostgreSQL-backed behavior.

### Python Sidecar

- Directory: `wayfare_ai_backend/`
- Responsibilities:
  - parse uploaded documents
  - create embeddings
  - retrieve chunks for grounded responses
  - answer annotate / query requests
  - send parse-completed notifications back to Go
- Fallback behavior:
  - if PostgreSQL is unavailable, it falls back to a local JSON retrieval store
  - if the model call fails, it falls back to a deterministic local response instead of blocking the UI

---

## 4. Current Source of Truth

The active knowledge flow is now backend-first.

### Current source of truth for the shipped MVP flow

- knowledge base metadata: Go JSON store (`data/knowledge_bases.json`)
- document metadata / parse status: Go JSON store (`data/knowledge_bases.json` document section)
- schedules: Go JSON store (`data/schedules.json`)
- parsed chunks for retrieval:
  - PostgreSQL if available
  - otherwise Python local JSON fallback store

### Important note

`src/store/learningStore.ts` is now legacy / transitional and should not be treated as the canonical data source for dashboard or workspace behavior.

---

## 5. Canonical User Flows

### Flow A - Knowledge Base Entry

1. User creates a knowledge base
2. Dashboard immediately reflects it
3. Refreshing the page keeps it
4. Entering `/workspace/[kbId]` uses the same backend-backed record

### Flow B - Upload to Reader

1. User uploads a PDF
2. Backend stores the document record
3. Status becomes `processing`
4. Python sidecar finishes parsing
5. Status updates to `completed` or `failed`
6. Reader can preview the file

### Flow C - Reader to AI

1. User opens a document
2. User selects text or asks a freeform question
3. Frontend sends the active `knowledgeBaseId`
4. Backend gathers the current document hashes
5. Python sidecar returns an answer
6. If the model is unavailable, the user still gets a local fallback answer instead of a hard stop

### Flow D - Schedule Board

1. User creates a task
2. Task persists
3. Browser reminder works
4. Complete / snooze / reschedule changes persist
5. Next step is to bind schedule items to real knowledge bases

---

## 6. Files That Matter Most

### Frontend

- `src/lib/api/client.ts`
- `src/pages/dashboard.astro`
- `src/pages/create-knowledge-base.astro`
- `src/components/workspace/WorkspaceShell.astro`
- `src/components/ai/AIAssistant.astro`
- `src/components/schedule/ScheduleBoardView.astro`
- `src/lib/schedule-board.ts`

### Backend

- `wayfare_backend/main.go`
- `wayfare_backend/api_portable_knowledge_base.go`
- `wayfare_backend/api_portable_bridge.go`
- `wayfare_backend/api_chat_portable.go`
- `wayfare_backend/ipc.go`
- `wayfare_backend/knowledge_base_store_json.go`
- `wayfare_backend/api_schedules.go`

### Python

- `wayfare_ai_backend/services.py`
- `wayfare_ai_backend/database.py`
- `wayfare_ai_backend/context_builder.py`

---

## 7. Remaining Engineering Priorities

The core P0 chain is now in place.

The next priorities are:

1. environment / smoke scripts
2. schedule-to-knowledge-base association
3. stale doc cleanup
4. deployment hardening

---

## 8. Working Rules for Codex

When asked to continue WayFare development, Codex should:

1. read this file first
2. read `TODO_MANIFEST.md`
3. optimize for flow completion, not isolated component edits
4. change all necessary files in one pass
5. run build or smoke verification after edits
6. avoid stopping after only a visual change if the data path is still incomplete

Preferred mindset:

> Fix the pipe first. Then polish the surface.
