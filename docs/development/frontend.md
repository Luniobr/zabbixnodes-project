# Frontend

SPA construída com **Vue 3** + **Vite**, usando **Vue Router**, **Pinia** e **Axios**.

## Stack

Principais dependências (`front-zabbixnodes/package.json`):

| Pacote | Uso |
|--------|-----|
| `vue` | Framework (Vue 3, Composition API) |
| `vite` | Bundler / dev server |
| `vue-router` | Roteamento SPA |
| `pinia` | Gerenciamento de estado |
| `axios` | Cliente HTTP |
| `eslint`, `oxlint`, `prettier` | Lint e formatação |

## Scripts

Definidos em `package.json`:

```bash
npm run dev       # servidor de desenvolvimento (Vite)
npm run build     # build de produção -> dist/
npm run preview   # pré-visualiza o build
npm run lint      # oxlint + eslint
npm run format    # prettier em src/
```

## Padrões adotados

### `useApi` (cliente HTTP)

`src/composables/useApi.js` centraliza um cliente Axios já configurado:

- **baseURL** a partir de `import.meta.env.VITE_API_BASE_URL` (fallback
  `http://localhost:8000/api/v1`).
- **Interceptor de request** injeta `Authorization: Bearer <token>` a partir do store de auth.
- **Interceptor de response** faz logout e redireciona para `login` em caso de `401`.

```js
import { useApi } from '@/composables/useApi'

const { client } = useApi()
const { data } = await client.get('/instances')
```

### Pinia store (`auth`)

`src/stores/auth.js` mantém `token`, `user` e `role`, persistindo em `localStorage`
(chave `useAuth`):

```js
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
auth.setAuth({ token, username, role })   // após login
auth.logout()                             // limpa estado + storage
```

### Roteamento

`src/router/index.js` usa `createWebHistory`. A rota `/login` é marcada como
`meta: { public: true }`; as demais ficam aninhadas sob o layout `AppLayout.vue`
(ex.: `dashboard`, `instances`, `triggers`, etc.).

!!! note "Alias de import"
    O alias `@` aponta para `src/` (configurado em `vite.config.js`), então use
    `@/components/...`, `@/stores/...`, `@/composables/...`.

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `VITE_API_BASE_URL` | URL base da API consumida pela SPA | `http://127.0.0.1:8000/api/v1` |

!!! warning "Variáveis Vite são embutidas no build"
    Tudo que começa com `VITE_` é resolvido em **tempo de build** e embutido no bundle.
    Para desenvolvimento, defina em `.env.local`; para a imagem de produção, o valor padrão
    vem do `Dockerfile` (`ENV VITE_API_BASE_URL=...`). Veja
    [Deploy › Docker](../deploy/docker.md).

## Build de produção

```bash
npm run build      # gera dist/
```

O conteúdo de `dist/` é servido pelo Nginx na imagem de produção (ver
[Deploy › Docker](../deploy/docker.md)).
