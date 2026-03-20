# WayFare Dev Quick Start

Last updated: 2026-03-19

## Recommended dev path

### Option A: one-click startup

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_dev.ps1
```

This opens:

- Go backend on `http://127.0.0.1:8080`
- Astro frontend on `http://127.0.0.1:4321`

### Option B: manual startup

Backend:

```powershell
cd .\wayfare_backend
$env:WAYFARE_OPEN_BROWSER='0'
go run .
```

Frontend:

```powershell
cd .
npm run dev
```

---

## Environment check

Toolchain only:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_env.ps1
```

Toolchain + runtime endpoints:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_env.ps1 -CheckRuntime
```

---

## Current expected URLs

- Backend health: `http://127.0.0.1:8080/healthz`
- Dashboard: `http://127.0.0.1:4321/dashboard`
- Schedule board: `http://127.0.0.1:4321/workspace/schedule`

---

## Expected MVP flow

1. Create a knowledge base
2. Upload a PDF
3. Wait for parsing status to become `completed`
4. Open the document in the workspace
5. Ask AI a question
6. Confirm the answer is returned in Chinese by default
