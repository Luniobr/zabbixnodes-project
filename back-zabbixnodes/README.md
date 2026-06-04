# ZabbixNodes Backend

## Instalação

### 1. Criar ambiente virtual
```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```
DATABASE_URL=postgresql+asyncpg://postgres:dev@localhost:5432/zabbixnodes
SECRET_KEY=sua-chave-secreta-aqui-min-32-caracteres
ADMIN_PASSWORD=admin123
ENCRYPTION_KEY=dc793222263d62730c11634a476f0079
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000
```

#### Gerar chaves seguras

Para gerar a `ENCRYPTION_KEY`:
```bash
python3 -c "import os; print(os.urandom(16).hex())"
```

Para gerar a `SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Migrations (Alembic)

### Executar migrations (criar tabelas)
```bash
alembic upgrade head
```

### Ver histórico de migrations
```bash
alembic history
```

### Ver status atual
```bash
alembic current
```

### Reverter última migration
```bash
alembic downgrade -1
```

### Criar nova migration após alterar modelos
```bash
alembic revision --autogenerate -m "Descrição da mudança"
```

## Iniciar a aplicação

```bash
fastapi dev main.py
```

A API estará disponível em `http://localhost:8000`
Documentação interativa em `http://localhost:8000/docs`