FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code at /app
COPY backend/ .

# Frontend at /frontend (BASE_DIR.parent / "frontend" = /app/../frontend = /frontend)
COPY frontend/ /frontend

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
