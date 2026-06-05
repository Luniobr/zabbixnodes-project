# Backend

API REST construída com **FastAPI** sobre **SQLAlchemy 2 (async)** e **PostgreSQL**.

## Stack

Principais dependências (`back-zabbixnodes/requirements.txt`):

| Pacote | Uso |
|--------|-----|
| `fastapi` / `uvicorn[standard]` | Framework web e servidor ASGI |
| `sqlalchemy[asyncio]` / `asyncpg` | ORM assíncrono e driver PostgreSQL |
| `alembic` | Migrations de banco |
| `pydantic` / `pydantic-settings` | Validação e configuração via env |
| `python-jose[cryptography]` | JWT (HS256) |
| `passlib[bcrypt]` / `bcrypt` | Hash de senha |
| `cryptography` | AES-256-GCM (cifra das credenciais Zabbix) |
| `slowapi` | Rate limiting |
| `zabbix-utils` / `aiohttp` / `httpx` | Integração com a API do Zabbix |
| `weasyprint` | Geração de PDF (reports) |

## Configuração

As configurações vêm de variáveis de ambiente via `core/config.py` (pydantic-settings).
O arquivo `.env` é lido **apenas se existir**; em container, as variáveis de ambiente têm
precedência. Veja a lista completa em [Variáveis de ambiente](../deploy/environment.md).

## Migrations (Alembic)

A configuração fica em `alembic.ini` (`script_location = alembic`). A URL do banco é
fornecida em tempo de execução (a `sqlalchemy.url` do `.ini` é um placeholder).

```bash
alembic upgrade head                              # aplicar todas as migrations
alembic current                                   # revisão atual
alembic history                                   # histórico
alembic downgrade -1                              # reverter a última
alembic revision --autogenerate -m "descrição"    # criar nova após mudar modelos
```

!!! note "Em produção as migrations são automáticas"
    O `entrypoint.sh` roda `alembic upgrade head` no boot do container, antes de subir o
    uvicorn. Veja [Deploy › Docker](../deploy/docker.md).

## Estrutura da API

Todos os endpoints ficam sob o prefixo **`/api/v1`**. O agregador é
`api/v1/router.py`, que inclui um router por domínio:

```python
# api/v1/router.py
router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(instances.router)
router.include_router(instances.groups_router)
# ... hosts, host_groups, proxies, templates, triggers, items,
#     users, compliance, audit, orchestration, dashboard, health, reports
```

Cada módulo define seu próprio `APIRouter(prefix=..., tags=...)`. A lista completa de
prefixos está em [API › Visão geral](../api/overview.md).

### Camadas

- **`api/v1/*.py`** — rotas (entrada HTTP, validação via schemas)
- **`api/deps.py`** — dependências de autenticação/autorização (`get_current_user`,
  `require_superadmin`, `check_instance_access`)
- **`schemas/`** — modelos Pydantic de entrada/saída
- **`models/`** — modelos SQLAlchemy (tabelas)
- **`services/`** — regras de negócio e integração (ex.: `services/zabbix.py`)
- **`core/`** — `config.py`, `database.py`, `security.py`

## Como adicionar um novo endpoint

1. Crie (ou edite) um módulo em `api/v1/`, definindo um router:

    ```python
    from fastapi import APIRouter, Depends
    from api.deps import get_current_user
    from models.user import HubUser

    router = APIRouter(prefix="/exemplo", tags=["exemplo"])

    @router.get("")
    async def listar(current_user: HubUser = Depends(get_current_user)):
        return {"ok": True}
    ```

2. Registre o router em `api/v1/router.py`:

    ```python
    from api.v1 import exemplo
    router.include_router(exemplo.router)
    ```

3. Se houver mudança de modelo, gere e aplique a migration:

    ```bash
    alembic revision --autogenerate -m "add tabela exemplo"
    alembic upgrade head
    ```

!!! tip "Proteção e autorização"
    Use `Depends(get_current_user)` para exigir autenticação, `Depends(require_superadmin)`
    para restringir a superadmins, e `check_instance_access(...)` quando a operação for
    relativa a uma instância específica.

## Segurança aplicada no `main.py`

- **CORS** restrito a `ALLOWED_ORIGINS`.
- **Rate limiting** via `slowapi` (`API_RATE_LIMIT` por minuto).
- **Headers de segurança** (`X-Content-Type-Options`, `X-Frame-Options`,
  `X-XSS-Protection`) adicionados por middleware.
- **`/health`** — endpoint JSON usado pelo healthcheck do container.
