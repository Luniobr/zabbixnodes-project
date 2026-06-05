# Variáveis de ambiente

Referência completa das variáveis usadas pelo backend e pelo frontend.

## Backend

### Aplicação (`core/config.py`)

| Variável | Obrigatória | Padrão | Descrição |
|----------|:----------:|--------|-----------|
| `DATABASE_URL` | ✅ | — | DSN async do PostgreSQL: `postgresql+asyncpg://user:senha@host:5432/db` |
| `SECRET_KEY` | ✅ | — | Chave de assinatura dos JWT (mín. 32 caracteres) |
| `ENCRYPTION_KEY` | ✅ | — | Chave AES-256 — **32 bytes** em hex (64 chars) ou base64 |
| `ADMIN_PASSWORD` | ✅ | — | Senha do superadmin criado no 1º boot |
| `ADMIN_USER` | | `admin` | Usuário do superadmin inicial |
| `ALLOWED_ORIGINS` | | `http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000` | Origins de CORS — separadas por vírgula **ou** lista JSON |
| `JWT_EXPIRATION_HOURS` | | `8` | Validade do token JWT (horas) |
| `API_RATE_LIMIT` | | `60` | Limite de requisições por minuto (slowapi) |
| `ZABBIX_TIMEOUT_SECONDS` | | `10` | Timeout das chamadas à API do Zabbix |

### Runtime do container (`entrypoint.sh`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `WORKERS` | `4` | Número de workers do uvicorn |
| `HOST` | `0.0.0.0` | Host de bind |
| `PORT` | `8000` | Porta interna da aplicação |
| `LOG_LEVEL` | `info` | Nível de log do uvicorn |

### Espera do banco (`wait_for_db.py`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DB_WAIT_MAX_ATTEMPTS` | `60` | Máximo de tentativas de conexão no boot |
| `DB_WAIT_INTERVAL` | `2` | Intervalo (s) entre tentativas |
| `DB_WAIT_CONNECT_TIMEOUT` | `5` | Timeout (s) por tentativa de conexão |

!!! tip "Gerar chaves seguras"
    ```bash
    # SECRET_KEY
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"

    # ENCRYPTION_KEY (32 bytes / AES-256) em hex
    python3 -c "import os; print(os.urandom(32).hex())"
    ```

!!! warning "Não troque a ENCRYPTION_KEY com dados em produção"
    As credenciais das instâncias Zabbix são cifradas com essa chave. Trocá-la depois de
    existirem dados gravados torna esses dados **ilegíveis**.

!!! note "Precedência: ambiente sobre .env"
    O `.env` é carregado **apenas se existir**. Em container as variáveis de ambiente têm
    precedência (e o `.env` não é incluído na imagem).

## Frontend

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` (fallback no código) | URL base da API consumida pela SPA |

!!! warning "Resolvida em tempo de build"
    Por ser uma variável `VITE_`, é embutida no bundle durante o `npm run build`. Na imagem
    de produção, o valor padrão é definido por `ENV VITE_API_BASE_URL=...` no Dockerfile do
    frontend.
