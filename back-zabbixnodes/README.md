# ZabbixNodes Backend

API (FastAPI) da plataforma de gerenciamento multi-instância Zabbix.
Backend API-only — a interface é servida separadamente pelo frontend Vue (`front-zabbixnodes`).

A documentação interativa fica em `/docs` e o healthcheck em `/health`.

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|:---:|---|---|
| `DATABASE_URL` | ✅ | — | `postgresql+asyncpg://user:senha@host:5432/db` |
| `SECRET_KEY` | ✅ | — | Chave de assinatura dos JWT (mín. 32 chars) |
| `ENCRYPTION_KEY` | ✅ | — | Chave AES-256 (32 bytes) em **hex** ou **base64** |
| `ADMIN_PASSWORD` | ✅ | — | Senha do usuário admin criado no 1º boot |
| `ADMIN_USER` | | `admin` | Usuário admin |
| `ALLOWED_ORIGINS` | | `localhost...` | Origins CORS — vírgula ou lista JSON |
| `JWT_EXPIRATION_HOURS` | | `8` | Validade do token |
| `API_RATE_LIMIT` | | `60` | Limite de requisições por minuto |
| `ZABBIX_TIMEOUT_SECONDS` | | `10` | Timeout das chamadas ao Zabbix |
| `WORKERS` / `LOG_LEVEL` | | `4` / `info` | Usados pelo `entrypoint.sh` (Docker) |

### Gerar chaves seguras

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY (32 bytes / AES-256) — hex
python3 -c "import os; print(os.urandom(32).hex())"
```

> ⚠️ Não troque a `ENCRYPTION_KEY` depois que houver credenciais salvas no banco —
> os dados criptografados ficariam ilegíveis.

## Rodar com Docker (produção)

A imagem é multi-stage e roda como API-only atrás de um Postgres. As variáveis
são injetadas via ambiente (o `.env` é ignorado dentro do container).

```bash
docker build -t registry.lunioit.com/zabbixnodes-backend:vue-dev .
docker push registry.lunioit.com/zabbixnodes-backend:vue-dev
```

No boot, o `entrypoint.sh` aguarda o banco (conexão real via asyncpg),
roda as migrations do Alembic e sobe o uvicorn. Orquestração de
`api` + `db` + `frontend` fica no `docker-compose.yml` da raiz do projeto.

## Rodar localmente (desenvolvimento)

```bash
# 1. Ambiente virtual
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Criar .env na raiz do backend (veja a tabela acima)

# 3. Migrations + app
alembic upgrade head
fastapi dev main.py
```

API em `http://localhost:8000` · docs em `http://localhost:8000/docs`.

## Migrations (Alembic)

```bash
alembic upgrade head                              # aplicar
alembic current                                   # status atual
alembic history                                   # histórico
alembic downgrade -1                              # reverter última
alembic revision --autogenerate -m "descrição"    # criar nova após mudar modelos
```
