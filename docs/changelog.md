# Changelog

Registro das mudanças relevantes do projeto.

!!! note "Versões"
    A aplicação backend declara `version="1.0.0"` em `back-zabbixnodes/main.py`. O frontend
    está em `0.0.0` (`front-zabbixnodes/package.json`).

## Versão inicial

Primeira versão funcional do ZabbixNodes, com a plataforma multi-instância e o
empacotamento Docker.

### Backend (FastAPI)

- API versionada sob `/api/v1` com routers para: `auth`, `instances` e `instance-groups`,
  `dashboard`, `hosts`, `host-groups`, `proxies`, `templates`, `triggers`, `items`,
  `users`, `compliance`, `audit`, `orchestration`, `health` e `reports`.
- Autenticação **JWT (HS256)** com hash de senha **bcrypt**.
- Autorização por papel (`superadmin`) e **permissão por instância** (`check_instance_access`).
- Criptografia das credenciais de instâncias Zabbix com **AES-256-GCM**; a `ENCRYPTION_KEY`
  aceita **hex ou base64** e exige 32 bytes (com validação que falha cedo em chave inválida).
- Configuração via `pydantic-settings`, lendo `.env` apenas quando presente (variáveis de
  ambiente têm precedência).
- `ALLOWED_ORIGINS` aceita lista separada por vírgula **ou** lista JSON.
- **Rate limiting** (slowapi) e **headers de segurança** via middleware.
- Endpoint **`/health`** em JSON para o healthcheck do container.
- Backend **API-only**: removidas as rotas HTML/Jinja2 legadas (a UI passou a ser servida
  pelo frontend Vue).

### Frontend (Vue 3)

- SPA com **Vue 3 + Vite**, **Vue Router**, **Pinia** e **Axios**.
- Cliente HTTP central (`useApi`) com interceptors de token e tratamento de `401`.
- Store de autenticação (`Pinia`) com persistência em `localStorage`.

### Infraestrutura / Deploy

- **Dockerfile multi-stage** para backend e frontend, publicados em `registry.lunioit.com`.
- `entrypoint.sh` do backend: espera o banco via **asyncpg** (`wait_for_db.py`), roda
  **migrations Alembic** e sobe o uvicorn.
- Frontend servido por **Nginx** a partir do build estático.
- `docker-compose.yml` com `api` + `db` (PostgreSQL 16) + `frontend`.
- `.gitignore` com padrões Python padrão (bytecode `__pycache__/*.pyc` fora do versionamento).

!!! info "TODO"
    Adotar versionamento semântico com tags de release e datas a partir da próxima versão.
