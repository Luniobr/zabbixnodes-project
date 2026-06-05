#!/bin/bash
set -e

# Script de entrypoint para o backend FastAPI com banco de dados PostgreSQL

echo "================================"
echo "ZabbixNodes Backend - Startup"
echo "================================"
echo ""

# Variáveis de ambiente com valores padrão
LOG_LEVEL=${LOG_LEVEL:-info}
WORKERS=${WORKERS:-4}
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

# 1. Validar DATABASE_URL
echo "[1/4] Verificando configuração..."
if [ -z "$DATABASE_URL" ]; then
  echo "❌ ERRO: DATABASE_URL não definida!"
  echo "Defina a variável antes de iniciar o container"
  exit 1
fi

# 2. Aguardar banco de dados
# Conexão REAL via asyncpg (valida porta + credenciais + database).
# O parsing do host/porta/credenciais fica a cargo do asyncpg, evitando
# extração frágil via sed e o problema do nc inexistente na imagem slim.
echo "[2/4] Aguardando disponibilidade do banco de dados..."
if ! python wait_for_db.py; then
  echo "❌ ERRO: Não foi possível conectar ao banco de dados. Abortando."
  exit 1
fi

echo ""

# 3. Executar migrations
echo "[3/4] Executando migrations do Alembic..."
if alembic upgrade head 2>&1; then
  echo "   ✓ Migrations executadas com sucesso"
else
  echo "   ⚠ Aviso: Erro ao executar migrations"
  echo "   Continuando mesmo assim..."
fi

echo ""

# 4. Iniciar aplicação
echo "[4/4] Iniciando aplicação FastAPI"
echo "   HOST: $HOST"
echo "   PORT: $PORT"
echo "   WORKERS: $WORKERS"
echo "   LOG_LEVEL: $LOG_LEVEL"
echo ""
echo "================================"
echo "Aplicação iniciada com sucesso!"
echo "Docs disponível em: http://localhost:$PORT/docs"
echo "================================"
echo ""

exec uvicorn main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WORKERS" \
  --log-level "$LOG_LEVEL" \
  --access-log
