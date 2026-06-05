# docker build -t registry.lunioit.com/zabbixnodes-backend:vue-dev . && docker push registry.lunioit.com/zabbixnodes-backend:vue-dev

# Stage 1: Build dependencies
FROM python:3.13-slim AS dependencies

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Constrói wheels da ÁRVORE COMPLETA de dependências (sem --no-deps),
# incluindo extras como sqlalchemy[asyncio] -> greenlet, uvicorn[standard], etc.
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi8 \
    shared-mime-info \
    fonts-liberation \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=dependencies /build/wheels /wheels
COPY requirements.txt .

# Instala a partir do requirements.txt (honra os extras) usando SOMENTE os
# wheels locais (--no-index), garantindo build offline e reproduzível.
RUN pip install --upgrade pip && \
    pip install --no-cache --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

COPY . .

# Remove arquivos .env para forçar uso de variáveis de ambiente em produção
RUN rm -f .env .env.local .env.*.local

RUN chmod +x entrypoint.sh

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=info

ENTRYPOINT ["./entrypoint.sh"]