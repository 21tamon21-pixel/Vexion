# VEXION Beta

VEXION is a coding-first AI workspace with anonymous, server-side usage tracking,
projects, attachments, streaming chat, markdown/code rendering and five VEXION
model identities.

## Feature map

| Area | Where |
|---|---|
| Chat + streaming (guest and signed-in lanes) | `backend/routers/chat.py`, `frontend/src/lib/stream.ts` |
| VEXION model catalog | `backend/lib/models_catalog.py` |
| Projects (shared instructions) | `backend/routers/projects.py`, `frontend/src/pages/Projects.tsx` |
| Attachments (image / PDF / text) | `backend/routers/attachments.py` |
| Image generation | `backend/routers/images.py` |
| Usage dashboard | `backend/routers/usage.py` |
| Rendering pipeline | `frontend/src/components/render/` |
| Voice (browser STT/TTS, streaming speech) | `frontend/src/hooks/useVoice.ts` |

The product name is configurable: set `APP_NAME` in `backend/.env`.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Vite + React 19 + TypeScript (strict) + Tailwind v4 + shadcn/ui | fast, typed, no framework lock-in, plain static build |
| Data fetching | TanStack Query | cache + invalidation, no fetch-in-effect |
| Rendering | react-markdown, remark-gfm, remark-math, rehype-katex, rehype-highlight, mermaid | one composable pipeline, each plugin swappable |
| Backend | FastAPI (async) + Pydantic v2 | typed request/response contracts, native SSE |
| Database | MongoDB via motor | document shape matches conversations/messages |
| Identity | validated anonymous client ID | persisted locally and enforced server-side |
| Streaming | Server-Sent Events | simplest reliable one-way token stream |

## Run locally

```bash
# Install frontend dependencies once, then build and serve the beta from FastAPI.
cd frontend && npm install && npm run build
cd ../backend && pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000

# Open http://localhost:8000. The Vite dev server remains available internally:
# cd frontend && npm run dev  (it proxies /api to the backend on port 8001).
```

The beta uses the existing local JSON persistence under `backend/.vexion-data/`.
That ignored directory should be replaced with managed storage before deploying
multiple backend instances.

## Build & deploy

```bash
cd frontend && npm run build    # static bundle in frontend/dist
cd backend  && uvicorn server:app --host 0.0.0.0 --port 8000
```

The beta production path is one port: FastAPI serves `frontend/dist` and owns
every `/api/*` route. Provider secrets remain in the server environment.

## Environment variables

Every variable is documented in [`.env.example`](./.env.example).
Copy it to `backend/.env`. No secret is ever sent to the browser; the only
config the frontend sees is the non-secret payload of `GET /api/config`.

## Quality gates

```bash
cd frontend && yarn typecheck   # tsc -b, strict
cd frontend && yarn lint        # oxlint
cd backend  && pytest           # backend specs
```

## Export to GitHub

The repository is ordinary source: `backend/` (Python + requirements.txt),
`frontend/` (package.json + Vite), docs and `.env.example`.

