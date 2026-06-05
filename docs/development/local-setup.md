# Ambiente local

Como rodar o backend e o frontend na sua máquina para desenvolvimento.

## Pré-requisitos

- **Python 3.13** (o backend declara `.python-version` = 3.13)
- **Node.js 20.19+ ou 22.12+** (definido em `front-zabbixnodes/package.json` → `engines`)
- **PostgreSQL 16** acessível (local ou em container)

!!! tip "Banco via Docker"
    Para subir só o PostgreSQL rapidamente:
    ```bash
    docker run -d --name zabbixnodes-db \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=dev \
      -e POSTGRES_DB=zabbixnodes \
      -p 5432:5432 postgres:16-alpine
    ```

## Backend

```bash
cd back-zabbixnodes

# 1. Ambiente virtual
python3.13 -m venv .venv
source .venv/bin/activate

# 2. Dependências
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do backend (`back-zabbixnodes/.env`):

```bash
DATABASE_URL=postgresql+asyncpg://postgres:dev@localhost:5432/zabbixnodes
SECRET_KEY=troque-por-uma-chave-aleatoria-de-no-minimo-32-caracteres
ENCRYPTION_KEY=
ADMIN_PASSWORD=admin123
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

!!! warning "Gere a `ENCRYPTION_KEY` corretamente"
    A `ENCRYPTION_KEY` precisa ter **32 bytes** (AES-256). Gere com:
    ```bash
    python3 -c "import os; print(os.urandom(32).hex())"
    ```
    Uma chave menor (ex.: 16 bytes) é **rejeitada** na inicialização do recurso de
    criptografia. Veja [Variáveis de ambiente](../deploy/environment.md).

Aplique as migrations e suba a aplicação:

```bash
# 3. Migrations
alembic upgrade head

# 4. Servidor de desenvolvimento (hot reload)
fastapi dev main.py
```

- API: `http://localhost:8000`
- Documentação interativa (Swagger): `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

!!! note "Usuário admin inicial"
    No primeiro boot, o `lifespan` cria um superadmin usando `ADMIN_USER` (padrão `admin`)
    e `ADMIN_PASSWORD`. Se já existir, a criação é ignorada.

## Frontend

```bash
cd front-zabbixnodes

# 1. Dependências
npm install

# 2. Apontar para a API local — crie .env.local
echo "VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1" > .env.local

# 3. Servidor de desenvolvimento (Vite)
npm run dev
```

Por padrão o Vite serve em `http://localhost:5173`.

!!! tip "CORS"
    A origem do frontend (ex.: `http://localhost:5173`) precisa estar listada na variável
    `ALLOWED_ORIGINS` do backend, senão as chamadas serão bloqueadas pelo navegador.

## Resumo de portas (dev)

| Serviço | URL |
|---------|-----|
| Frontend (Vite) | `http://localhost:5173` |
| Backend (FastAPI) | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |
| PostgreSQL | `localhost:5432` |
