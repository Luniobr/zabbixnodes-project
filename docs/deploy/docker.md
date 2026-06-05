# Deploy com Docker

Ambos os serviços usam **Dockerfile multi-stage** e são publicados no registry
`registry.lunioit.com`.

## Build e push das imagens

### Backend

```bash
cd back-zabbixnodes
docker build -t registry.lunioit.com/zabbixnodes-backend:vue-dev .
docker push registry.lunioit.com/zabbixnodes-backend:vue-dev
```

O Dockerfile do backend:

1. **Stage de build** — compila os *wheels* da árvore completa de dependências
   (incluindo o extra `sqlalchemy[asyncio]` → `greenlet`).
2. **Stage de runtime** — `python:3.13-slim`, instala os wheels offline, copia o código,
   cria um usuário não-root e define um `HEALTHCHECK` (`curl -f .../health`).

No boot, o `entrypoint.sh`:

```text
[1/4] valida configuração (DATABASE_URL)
[2/4] aguarda o banco via asyncpg (wait_for_db.py)
[3/4] roda 'alembic upgrade head'
[4/4] sobe o uvicorn (WORKERS workers)
```

### Frontend

```bash
cd front-zabbixnodes
docker build -t registry.lunioit.com/zabbixnodes-frontend:vue-dev .
docker push registry.lunioit.com/zabbixnodes-frontend:vue-dev
```

O Dockerfile do frontend faz `npm ci` + `npm run build` (stage Node) e serve o `dist/`
com **Nginx** (`nginx.conf`). O valor padrão de `VITE_API_BASE_URL` é definido via `ENV`
no próprio Dockerfile.

!!! warning "Variáveis VITE são embutidas no build"
    Como o Vite resolve `VITE_API_BASE_URL` em tempo de build, alterar a URL da API
    normalmente exige **rebuild** da imagem do frontend (ou ajustar antes do `npm run build`).

## Subir o stack completo

O repositório traz um `docker-compose.yml` na raiz com `api` + `db` + `frontend` na rede
`zabbixnodes_net`. Para subir tudo:

```bash
docker compose up -d
docker compose ps          # status (api e db devem ficar healthy)
docker compose logs -f api # acompanhar o boot do backend
```

!!! tip "A tag :vue-dev é mutável"
    Ao atualizar uma imagem, **force o pull** no ambiente de destino, senão o Docker reusa
    a imagem em cache:
    ```bash
    docker compose pull api && docker compose up -d api
    ```

## Healthchecks

| Serviço | Verificação |
|---------|-------------|
| `db` | `pg_isready -U <user> -d <db>` |
| `api` | `curl -f http://localhost:8000/health` |
| `frontend` | requisição HTTP ao Nginx |

```bash
docker inspect --format='{{.State.Health.Status}}' zabbixnodes_api
```

## Verificação rápida pós-deploy

```bash
curl -i http://<host>:8001/health     # backend -> {"status":"ok"}
curl -I http://<host>:80/             # frontend (Nginx) -> 200
# Swagger da API:
#   http://<host>:8001/docs
```

Veja a referência completa de variáveis em
[Variáveis de ambiente](environment.md) e o deploy via UI em
[Portainer](portainer.md).
