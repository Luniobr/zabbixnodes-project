# Deploy via Portainer

O deploy em produção pode ser feito pelo **Portainer**, criando uma *Stack* a partir do
`docker-compose.yml` e informando as variáveis inline.

## Passo a passo

1. No Portainer, vá em **Stacks → Add stack**.
2. Dê um nome (ex.: `zabbixnodes`).
3. Em **Web editor**, cole o compose abaixo (ajuste imagens, credenciais e origins).
4. Clique em **Deploy the stack**.

!!! note "Registry privado"
    As imagens estão em `registry.lunioit.com`. Se o registry exigir autenticação, cadastre
    as credenciais em **Registries** no Portainer antes de fazer o deploy.

## Compose de referência

```yaml
services:
  api:
    image: registry.lunioit.com/zabbixnodes-backend:vue-dev
    container_name: zabbixnodes_api
    ports:
      - "8001:8000"
    environment:
      DATABASE_URL: 'postgresql+asyncpg://zabbixnodes:TROCAR_SENHA@db:5432/zabbixnodes'
      SECRET_KEY: 'TROCAR_por_chave_aleatoria_min_32_chars'
      ENCRYPTION_KEY: 'TROCAR_por_chave_de_32_bytes_hex_ou_base64'
      ADMIN_USER: admin
      ADMIN_PASSWORD: 'TROCAR_SENHA'
      JWT_EXPIRATION_HOURS: 8
      ZABBIX_TIMEOUT_SECONDS: 10
      API_RATE_LIMIT: 60
      ALLOWED_ORIGINS: 'http://SEU_HOST,http://localhost'
    depends_on:
      db:
        condition: service_healthy
    networks:
      - zabbixnodes_net
    restart: unless-stopped

  frontend:
    image: registry.lunioit.com/zabbixnodes-frontend:vue-dev
    container_name: zabbixnodes_frontend
    ports:
      - "80:80"
    depends_on:
      - api
    networks:
      - zabbixnodes_net
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    container_name: zabbixnodes_db
    environment:
      POSTGRES_DB: zabbixnodes
      POSTGRES_USER: zabbixnodes
      POSTGRES_PASSWORD: 'TROCAR_SENHA'
    volumes:
      - zabbixnodes_postgres_data:/var/lib/postgresql/data
    networks:
      - zabbixnodes_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U zabbixnodes -d zabbixnodes"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

volumes:
  zabbixnodes_postgres_data:

networks:
  zabbixnodes_net:
    driver: bridge
```

!!! warning "As 3 correspondências que NÃO podem divergir"
    O host no `DATABASE_URL` (`@db`) precisa ser o **nome do serviço** do banco (`db`), e
    **usuário/senha/database** precisam ser **idênticos** entre o `DATABASE_URL` do `api` e
    as variáveis `POSTGRES_*` do `db`.

!!! warning "Volume antigo ignora novas credenciais"
    O PostgreSQL só aplica `POSTGRES_USER/PASSWORD/DB` na **primeira** inicialização do
    volume. Se você reaproveitar um volume criado com outras credenciais, verá
    `password authentication failed`. Nesse caso, recrie o volume
    (`docker compose down -v`) ou crie o usuário/banco manualmente.

## Atualizando a stack

Como a tag `:vue-dev` é mutável, ao publicar novas imagens use **Pull and redeploy** (ou
*Update the stack* com *Re-pull image*) para o Portainer puxar a versão mais recente.

A lista completa de variáveis está em [Variáveis de ambiente](environment.md).
