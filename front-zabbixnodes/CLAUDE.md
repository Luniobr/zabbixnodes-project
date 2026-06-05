# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Frontend SPA for ZabbixNodes. See the repo-root `CLAUDE.md` for the big picture.

## Stack

Vue 3 (Composition API) · Vite · Vue Router · Pinia · Axios.

## Commands

```bash
npm install
npm run dev        # Vite dev server on :5173
npm run build      # production build -> dist/
npm run lint       # oxlint + eslint (both with --fix)
npm run format     # prettier on src/
```

No test runner is configured.

## Architecture

- **HTTP client** — `src/composables/useApi.js` exposes a preconfigured Axios `client`.
  `baseURL` comes from `import.meta.env.VITE_API_BASE_URL`. A request interceptor injects
  `Authorization: Bearer <token>` from the auth store; a response interceptor logs out and
  redirects to `login` on `401`. Use `const { client } = useApi()` rather than importing axios
  directly.
- **Auth state** — `src/stores/auth.js` (Pinia) holds `token`/`user`/`role`, persisted in
  `localStorage` under the key `useAuth`. Use `setAuth(...)` after login and `logout()`.
- **Routing** — `src/router/index.js` (`createWebHistory`). `/login` is marked
  `meta: { public: true }`; other views are nested under `layout/AppLayout.vue`.
- **Imports** — the alias `@` maps to `src/` (`vite.config.js`); use `@/components`,
  `@/stores`, `@/composables`, etc.

## VITE_API_BASE_URL is build-time

Anything prefixed `VITE_` is inlined into the bundle at build time. For local dev set it in
`.env.local`; the production image sets a default via `ENV VITE_API_BASE_URL=...` in the
`Dockerfile`. Changing the API URL generally requires rebuilding the frontend image. The
built `dist/` is served by Nginx (`nginx.conf`) in production.
