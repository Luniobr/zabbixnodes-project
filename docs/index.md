# ZabbixNodes

**ZabbixNodes** é uma plataforma de **gerenciamento multi-instância Zabbix** — um hub
centralizado para administrar vários servidores Zabbix a partir de uma única interface.

> Título e descrição definidos em `back-zabbixnodes/main.py`:
> *"ZabbixNodes — Plataforma de Gerenciamento Multi-Instância Zabbix"*.

## O que ela faz

A partir de uma instância cadastrada (URL + credenciais do Zabbix), a plataforma permite
operar os recursos daquele Zabbix de forma centralizada. Os domínios cobertos pela API são:

- **Instâncias** e **grupos de instâncias** — cadastro dos servidores Zabbix gerenciados
- **Hosts** e **grupos de hosts**
- **Proxies**
- **Templates**
- **Triggers** e **items**
- **Dashboard** — visão consolidada
- **Compliance** e **orchestration** — conformidade e automação
- **Reports** — relatórios (geração de PDF via WeasyPrint)
- **Usuários**, **permissões por instância** e **auditoria**

!!! note "Modelo de acesso"
    Há dois níveis de papel: `superadmin` (acesso total) e usuários comuns, cujo acesso
    é controlado por instância (`UserInstancePermission`, com flag de escrita). Veja
    [Arquitetura › Fluxo de autenticação](architecture.md#fluxo-de-autenticacao).

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.13 · FastAPI · SQLAlchemy 2 (async) · Alembic |
| Banco de dados | PostgreSQL 16 |
| Autenticação | JWT (HS256) · bcrypt |
| Integração Zabbix | `zabbix-utils` · `aiohttp` / `httpx` |
| Frontend | Vue 3 · Vite · Vue Router · Pinia · Axios |
| Servidor web (frontend) | Nginx (Alpine) |
| Empacotamento | Docker (multi-stage) · Docker Compose |
| Registry | `registry.lunioit.com` |

## Estrutura do repositório

```text
zabbixnodes-project/
├── back-zabbixnodes/     # API FastAPI (backend)
├── front-zabbixnodes/    # SPA Vue 3 (frontend)
├── docs/                 # esta documentação (MkDocs)
├── docker-compose.yml    # stack completo (api + db + frontend)
└── mkdocs.yml
```

## Por onde começar

- Rodar localmente → [Desenvolvimento › Ambiente local](development/local-setup.md)
- Entender a arquitetura → [Arquitetura](architecture.md)
- Publicar em produção → [Deploy › Docker](deploy/docker.md) e [Deploy › Portainer](deploy/portainer.md)
- Referência da API → [API › Visão geral](api/overview.md)
