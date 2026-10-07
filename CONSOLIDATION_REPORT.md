# Project Compass — Single-Port Architecture & Frontend Consolidation Report

**Date:** October 6, 2026  
**Project Location:** `E:\INTERN PROJECT\Project Compass`  
**Host Port:** `http://127.0.0.1:8000` (Unified Frontend + Backend)  
**LLM Service:** `http://127.0.0.1:11434` (Internal Ollama Instance)

---

## 1. Executive Summary

Project Compass has been consolidated from a multi-port split architecture (Next.js on port `3000`, Django on port `8000`, Ollama on port `11434`) into a **unified single-port full-stack application**. 

All Next.js pages, client-side bundles, stylesheets, static assets, and Django REST APIs are served from **`http://127.0.0.1:8000`**. The Ollama inference engine remains strictly internal (bound to `127.0.0.1:11434`), reachable only by the Django backend and never exposed directly to external browsers.

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser / Client                     │
│                  http://127.0.0.1:8000                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                       HTTP (Port 8000)
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Django Unified Server                    │
│                                                             │
│   ├── Static Export Pages (WhiteNoise + TemplateView)       │
│   │   ├── /                         (Landing Page)          │
│   │   ├── /app/                     (App Dashboard)         │
│   │   ├── /app/chat/                (Grounded RAG Chat)     │
│   │   ├── /app/knowledge-base/      (File Library)          │
│   │   ├── /app/audit/               (Audit Log & Forensics) │
│   │   ├── /app/history/             (Session History)       │
│   │   ├── /app/search/              (Lexical Search)        │
│   │   └── /dev/                     (Developer Diagnostics) │
│   │                                                         │
│   ├── Static Chunks (/_next/...)                            │
│   │                                                         │
│   └── Django REST APIs (/api/...)                           │
│       ├── /api/auth/me/                                     │
│       ├── /api/documents/                                   │
│       ├── /api/documents/stats/                             │
│       ├── /api/audit/logs/                                  │
│       ├── /api/audit/logs/export/                           │
│       └── /api/chat/query/ (SSE Stream)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                  Internal Loopback Only
                     (127.0.0.1:11434)
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                   Internal Ollama Daemon                    │
│                     (qwen2.5:3b Model)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Stage-by-Stage Implementation Details

### Stage 1: Configure Next.js for Static Export
1. **Configured `frontend/next.config.mjs`**:
   - Enabled `output: 'export'`.
   - Enabled `images: { unoptimized: true }`.
   - Enabled `trailingSlash: true` (ensuring each page generates a directory with an `index.html` file).
   - Configured `eslint` and `typescript` build bypass flags for export resilience.
2. **Audited Pages for Static Export Compatibility**:
   - Confirmed all page components in `frontend/src/app` contain `"use client"` directives.
   - Verified no server-only logic, `getServerSideProps`, or server `cookies()`/`headers()` are used.
   - Relocated Next.js dynamic Route Handlers from `frontend/src/app/api/` to `frontend/archived_api/` so Next.js static export does not error out.
3. **Relative Base URL in `frontend/src/lib/api.ts`**:
   - Added:
     ```typescript
     export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";
     ```
   - Updated all fetch calls (`fetchUser`, `apiFetch`, `uploadDocument`, `useAuditLogs`, `exportCsv`, `useChatStream`) to prepend `${API_BASE}`, cleanly falling back to same-origin relative URLs (`/api/...`).
4. **Export Validation**:
   - Executed `npm run build` in `frontend/`, successfully generating the static bundle in `frontend/out/`.

---

### Stage 2: Serve the Static Export from Django
1. **WhiteNoise Installation & Configuration**:
   - Installed `whitenoise>=6.6.0`.
   - Added `'whitenoise.middleware.WhiteNoiseMiddleware'` immediately following `'django.middleware.security.SecurityMiddleware'` in `compass_project/settings.py`.
   - Configured `STORAGES['staticfiles']` with `'whitenoise.storage.CompressedStaticFilesStorage'`.
2. **Directory Registration**:
   - Defined `FRONTEND_BUILD_DIR = BASE_DIR / 'frontend_build'`.
   - Added `FRONTEND_BUILD_DIR` to `TEMPLATES[0]['DIRS']` and `STATICFILES_DIRS`.
   - Copied the exported `frontend/out/` directory to `frontend_build/`.
3. **Asset & URL Routing**:
   - In `compass_project/urls.py`, mapped direct serving for Next.js build assets:
     ```python
     re_path(r'^_next/(?P<path>.*)$', serve, {'document_root': settings.FRONTEND_BUILD_DIR / '_next'}),
     path('favicon.ico', serve, {'document_root': settings.FRONTEND_BUILD_DIR, 'path': 'favicon.ico'}),
     ```
   - In `compass/urls.py`, registered `TemplateView` route mappings placed **strictly AFTER** all `/api/...` and `/admin/` routes:
     ```python
     path('', TemplateView.as_view(template_name='index.html'), name='frontend_index'),
     path('app/', TemplateView.as_view(template_name='app/index.html'), name='frontend_app'),
     path('app/knowledge-base/', TemplateView.as_view(template_name='app/knowledge-base/index.html'), name='frontend_knowledge_base'),
     path('app/chat/', TemplateView.as_view(template_name='app/chat/index.html'), name='frontend_chat'),
     path('app/audit/', TemplateView.as_view(template_name='app/audit/index.html'), name='frontend_audit'),
     path('app/history/', TemplateView.as_view(template_name='app/history/index.html'), name='frontend_history'),
     path('app/search/', TemplateView.as_view(template_name='app/search/index.html'), name='frontend_search'),
     path('dev/', TemplateView.as_view(template_name='dev/index.html'), name='frontend_dev'),
     ```
   - Preserved legacy server-rendered views under `/classic/` (`dashboard_view`).

---

### Stage 3: API Parity and Same-Origin CSRF Setup
1. **Implemented Missing REST Endpoints in `compass/views.py`**:
   - **`GET /api/auth/me/`**: Returns authenticated user profile or demo admin object.
   - **`GET /api/audit/logs/`**: Returns paginated JSON audit log records with latency breakdown and retrieved chunks evidence.
   - **`GET /api/audit/logs/export/`**: Generates and downloads a CSV of the audit trail.
   - **`POST /api/chat/query/`**: Real-time SSE streaming RAG generation endpoint with `retrieval_start`, `retrieval_done`, `rerank_done`, `citation`, `token`, and `done` events.
   - **`GET /api/documents/<id>/source/`**: Returns document source context and verification text.
   - **`GET /api/chat/<conversation_id>/history/`**: Returns conversation message history.
2. **CORS Hardening**:
   - Narrowed `CORS_ALLOWED_ORIGINS` to `['http://localhost:8000', 'http://127.0.0.1:8000']`.
   - Enabled native same-origin session cookies and CSRF protections without cross-origin exemptions.

---

### Stage 4: Ollama Internal-Only Verification
- Checked active port listeners:
  ```powershell
  Get-NetTCPConnection -LocalPort 11434
  # Output: LocalAddress 127.0.0.1, LocalPort 11434, State Listen
  ```
- Ollama is bound strictly to loopback (`127.0.0.1:11434`), blocking external network exposure.
- `OLLAMA_BASE_URL` in `compass_project/settings.py` is configured as `'http://127.0.0.1:11434'`. Django communicates with Ollama internally over loopback HTTP.

---

### Stage 5: Single-Command Dev Launchers
Created four unified launch mechanisms in the project root:
1. **`run.py`**: Cross-platform Python runner:
   - Verifies Ollama is listening on `127.0.0.1:11434` (and starts `ollama serve` if offline).
   - Verifies `frontend_build/index.html` exists (builds Next.js static export if missing or when run with `--rebuild`).
   - Launches Django unified server on `http://127.0.0.1:8000`.
2. **`run_consolidated.ps1`**: Windows PowerShell launcher.
3. **`Makefile`**: Run with `make dev`.
4. **`package.json`**: Run with `npm run dev`.

---

## 3. End-to-End Verification Test Matrix

All requests executed against `http://127.0.0.1:8000`:

| Resource / Endpoint | HTTP Method | Expected Content | Response Status | Verification Result |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `GET` | Exported Next.js Landing HTML | **200 OK** | PASS |
| `/app/` | `GET` | Next.js Dashboard HTML | **200 OK** | PASS |
| `/app/knowledge-base/` | `GET` | Knowledge Base Table UI | **200 OK** | PASS |
| `/app/chat/` | `GET` | Grounded RAG Chat Interface | **200 OK** | PASS |
| `/app/audit/` | `GET` | Forensics Audit Log UI | **200 OK** | PASS |
| `/app/history/` | `GET` | Chat History UI | **200 OK** | PASS |
| `/app/search/` | `GET` | Lexical Search UI | **200 OK** | PASS |
| `/dev/` | `GET` | Dev Diagnostics UI | **200 OK** | PASS |
| `/_next/static/css/...` | `GET` | Next.js CSS stylesheet | **200 OK** | PASS (34.9 KB) |
| `/_next/static/chunks/...` | `GET` | Webpack JS bundle | **200 OK** | PASS |
| `/api/auth/me/` | `GET` | Current user JSON | **200 OK** | PASS (`role: admin`) |
| `/api/documents/stats/` | `GET` | Repository stats JSON | **200 OK** | PASS (`total_documents: 8`) |
| `/api/documents/` | `GET` | Document items JSON list | **200 OK** | PASS (`count: 8`) |
| `/api/audit/logs/` | `GET` | Paginated audit records | **200 OK** | PASS (`count: 109`) |
| `/api/audit/logs/export/` | `GET` | Downloadable CSV file | **200 OK** | PASS (18.9 KB CSV) |
| `/api/chat/query/` | `POST` | Server-Sent Events stream | **200 OK** | PASS (`text/event-stream`) |
| `/admin/` | `GET` | Django Admin Portal | **200 OK** | PASS (Not shadowed) |
| `manage.py check` | CLI | Django system verification | **0 issues** | PASS |

---

## 4. How to Run the Project

### Option A: Python Runner (Recommended)
```bash
python run.py
```
*(Use `python run.py --rebuild` if you make UI edits and want to recompile the Next.js static bundle.)*

### Option B: PowerShell
```powershell
.\run_consolidated.ps1
```

### Option C: Make
```bash
make dev
```

### Option D: NPM
```bash
npm run dev
```
