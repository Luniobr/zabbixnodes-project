# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

ZabbixNodes is a **multi-instance Zabbix management platform**: a central API + UI to
operate many Zabbix servers from one place. It is a monorepo with two deployable services
plus a documentation site:

- `back-zabbixnodes/` — FastAPI REST API (see `back-zabbixnodes/CLAUDE.md`)
- `front-zabbixnodes/` — Vue 3 SPA (see `front-zabbixnodes/CLAUDE.md`)
- `docs/` + `mkdocs.yml` — MkDocs (Material) documentation
- `docker-compose.yml` — full stack: `api` + `db` (PostgreSQL 16) + `frontend`

## Big picture

The browser loads the SPA from Nginx (port 80) and calls the API **directly** at
`<host>:8001/api/v1` (the URL is baked into the SPA via `VITE_API_BASE_URL`). The API
talks to PostgreSQL over asyncpg and to the managed Zabbix servers over HTTP. Auth is JWT.
Detailed diagrams live in `docs/architecture.md`.

## Docs

```bash
# requires mkdocs-material (see docs/requirements.txt)
mkdocs serve                 # preview at http://127.0.0.1:8000
mkdocs build --strict        # build; --strict fails on broken links/nav
```

## Deploy / images

Images are published to `registry.lunioit.com` with the **mutable** tag `:vue-dev`:

- `zabbixnodes-backend:vue-dev`, `zabbixnodes-frontend:vue-dev`, `zabbixnodes-docs:vue-dev`
- Build commands are in the top comment of each Dockerfile (`Dockerfile`, `Dockerfile.docs`).
- Because the tag is mutable, **force a pull** when redeploying:
  `docker compose pull <svc> && docker compose up -d <svc>`.

## Cross-cutting gotchas

- **`ENCRYPTION_KEY` must be 32 bytes** (AES-256), provided as hex (64 chars) or base64.
  `core/security.py` validates this and fails fast on a shorter/invalid key. Do **not**
  change it once instance credentials have been encrypted in the DB — they become
  unreadable.
- **PostgreSQL volume**: `POSTGRES_USER/PASSWORD/DB` are only applied on the *first*
  initialization of the data volume. Reusing a volume created with other credentials causes
  `password authentication failed`; recreate the volume (`docker compose down -v`) or create
  the role/db manually.
- The `db` host in `DATABASE_URL` must match the compose **service name**, and
  user/password/database must be identical on both the `api` and `db` services.
- No automated test suite or Python linter is configured. The frontend has lint/format
  (`npm run lint`, `npm run format`).
