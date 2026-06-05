# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Backend API for ZabbixNodes. See the repo-root `CLAUDE.md` for the big picture.

## Stack

Python 3.13 · FastAPI · SQLAlchemy 2 (async) + asyncpg · Alembic · pydantic-settings ·
python-jose (JWT) · passlib/bcrypt · cryptography (AES-256-GCM) · slowapi · zabbix-utils.

## Commands

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

fastapi dev main.py                               # dev server on :8000 (docs at /docs)

alembic upgrade head                              # apply migrations
alembic revision --autogenerate -m "descrição"    # create migration after model changes
```

There is **no test suite and no Python linter** configured.

## Architecture

- **API-only.** The legacy Jinja2/HTML routes were removed; the UI is the separate Vue SPA.
  `main.py` exposes only the API plus a JSON `GET /health` used by the container healthcheck.
- **Routing.** Everything is under `/api/v1`. `api/v1/router.py` aggregates one `APIRouter`
  per domain; each module sets its own `prefix`/`tags`. Resources scoped to a Zabbix
  instance are nested: `/instances/{instance_id}/hosts|host-groups|proxies|templates|triggers`
  and `/instances/{instance_id}/hosts/{host_id}/items`.
- **Auth/authz** (`api/deps.py`): `get_current_user` decodes the JWT and requires
  `is_active`; `require_superadmin` restricts to superadmins; `check_instance_access(..., require_write=...)`
  enforces per-instance permissions (`UserInstancePermission`). Tokens are JWT HS256, issued
  in `api/v1/auth.py` via `core/security.py`.
- **Config** (`core/config.py`, pydantic-settings): the `.env` is loaded **only if present**,
  so container env vars take precedence (and the Dockerfile removes `.env` from the image).
  `ALLOWED_ORIGINS` accepts a comma-separated string **or** a JSON list. Full variable table:
  `docs/deploy/environment.md`.
- **Zabbix credential encryption** (`core/security.py`): `encrypt_token`/`decrypt_token` use
  AES-256-GCM with the key from `ENCRYPTION_KEY` (see root gotchas).
- **Layers:** `api/v1/` (routes) → `services/` (business logic, Zabbix integration) ·
  `schemas/` (Pydantic) · `models/` (SQLAlchemy) · `core/` (config, database, security).

## Adding an endpoint

1. Create/extend a module in `api/v1/` with an `APIRouter(prefix=..., tags=...)`.
2. Register it in `api/v1/router.py` (`router.include_router(...)`).
3. If models changed: `alembic revision --autogenerate -m "..."` then `alembic upgrade head`.

## Container runtime

`entrypoint.sh` (1) waits for the DB via `wait_for_db.py` — a real asyncpg connection that
validates port + credentials + database (do **not** reintroduce an `nc` check; netcat isn't
in the slim image), (2) runs `alembic upgrade head`, (3) starts uvicorn with `WORKERS`.

The multi-stage `Dockerfile` builds the **full** dependency tree (no `--no-deps`) and installs
from `requirements.txt`, so the `sqlalchemy[asyncio]` extra pulls in `greenlet` (required by
SQLAlchemy async).
