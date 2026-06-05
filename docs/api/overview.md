# Visão geral da API

A API é versionada sob o prefixo **`/api/v1`**, montado em `back-zabbixnodes/api/v1/router.py`.
Cada domínio é um `APIRouter` próprio, com seu `prefix` e `tags`.

!!! tip "Documentação interativa"
    A referência detalhada (parâmetros, schemas, respostas) está sempre disponível no
    **Swagger UI** em `/docs` e no **OpenAPI** em `/openapi.json` da aplicação em execução.

## Routers registrados

| Router | Prefixo (sob `/api/v1`) | Tag | Propósito |
|--------|-------------------------|-----|-----------|
| `auth` | `/auth` | auth | Login e dados do usuário autenticado |
| `instances` | `/instances` | instances | Cadastro/gestão das instâncias Zabbix |
| `instances.groups_router` | `/instance-groups` | instance-groups | Grupos de instâncias |
| `dashboard` | `/dashboard` | dashboard | Visão consolidada |
| `hosts` | `/instances/{instance_id}/hosts` | hosts | Hosts de uma instância |
| `host_groups` | `/instances/{instance_id}/host-groups` | host-groups | Grupos de hosts de uma instância |
| `proxies` | `/instances/{instance_id}/proxies` | proxies | Proxies de uma instância |
| `templates` | `/instances/{instance_id}/templates` | templates | Templates de uma instância |
| `triggers` | `/instances/{instance_id}/triggers` | triggers | Triggers de uma instância |
| `items` | `/instances/{instance_id}/hosts/{host_id}/items` | items | Items de um host |
| `users` | `/users` | users | Gestão de usuários |
| `compliance` | `/compliance` | compliance | Conformidade |
| `audit` | `/audit` | audit | Logs de auditoria |
| `orchestration` | `/orchestration` | orchestration | Automação/orquestração |
| `health` | _(sem prefixo próprio)_ | health | Health da API |
| `reports` | `/reports` | reports | Relatórios (geração de PDF) |

!!! note "Recursos aninhados por instância"
    Hosts, grupos de hosts, proxies, templates, triggers e items são **relativos a uma
    instância** — daí o prefixo `/instances/{instance_id}/...` (e `/{host_id}/items` para
    items). Sempre informe o `instance_id` correspondente.

## Autenticação

Todas as rotas protegidas exigem o header:

```http
Authorization: Bearer <token>
```

O token é obtido no login:

```bash
curl -X POST http://<host>:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"<senha>"}'
# -> { "access_token": "..." }
```

Exemplos de rotas conhecidas (verificadas no código):

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/auth/login` | Autentica e retorna o `access_token` |
| `GET` | `/api/v1/auth/me` | Dados do usuário autenticado |
| `POST` | `/api/v1/instances/test-credentials` | Testa a comunicação com um Zabbix |

!!! info "Endpoints completos"
    Esta página lista os **routers e prefixos** reais. Para a relação completa de endpoints
    de cada router, consulte o Swagger em `/docs`.

## Endpoints fora de `/api/v1`

| Rota | Descrição |
|------|-----------|
| `GET /health` | Healthcheck JSON usado pelo container (`back-zabbixnodes/main.py`) |
| `GET /docs` | Swagger UI |
| `GET /openapi.json` | Especificação OpenAPI |
