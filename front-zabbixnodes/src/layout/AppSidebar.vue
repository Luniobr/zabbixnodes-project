<template>
  <nav class="sidebar">
    <template v-for="item in menu" :key="item.label || item.type">
      <!-- Divisor -->
      <div v-if="item.type === 'divider'" class="sidebar-divider" />

      <!-- Título de seção -->
      <div v-else-if="item.type === 'section'" class="sidebar-section">
        {{ item.label }}
      </div>

      <!-- Link simples -->
      <RouterLink
        v-else-if="item.type === 'link'"
        :to="{ name: item.route }"
        :title="item.label"
        class="sidebar-link"
        active-class="active"
      >
        <span v-html="item.icon" />
        <span class="sidebar-label">{{ item.label }}</span>
      </RouterLink>

      <!-- Grupo colapsável -->
      <template v-else-if="item.type === 'group'">
        <button
          class="sidebar-group"
          :class="{ 'sidebar-group-active': open[item.key] }"
          :title="item.label"
          @click="toggle(item.key)"
        >
          <span v-html="item.icon" />
          <span class="sidebar-label">{{ item.label }}</span>
          <svg
            class="sidebar-chevron"
            :class="{ rotated: open[item.key] }"
            width="12"
            height="12"
            fill="currentColor"
            viewBox="0 0 16 16"
          >
            <path
              d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"
            />
          </svg>
        </button>

        <div v-show="open[item.key]">
          <RouterLink
            v-for="link in item.links"
            :key="link.route"
            :to="{ name: link.route }"
            :title="link.label"
            class="sidebar-link sidebar-sublink"
            active-class="active"
          >
            <span v-html="link.icon" />
            <span class="sidebar-label">{{ link.label }}</span>
          </RouterLink>
        </div>
      </template>
    </template>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const route = useRouter()

const open = ref({ instance: true, manage: false })

function toggle(section) {
  open.value[section] = !open.value[section]
}

const menu = [
  {
    type: 'link',
    label: 'Dashboard',
    route: 'dashboard',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 1a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 1z"/></svg>',
  },
  { type: 'divider' },
  { type: 'section', label: 'Gestão' },
  {
    type: 'group',
    key: 'instances',
    label: 'Instâncias',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm15 3a1 1 0 0 1 1 1v6a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1h14z"/></svg>',
    links: [
      {
        label: 'Grupos de Instâncias',
        route: 'instance-groups',
        icon: '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M1 2a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2zm5 0a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V2zm5 0a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-2a1 1 0 0 1-1-1V2zM1 7a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V7zm5 0a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V7zm5 0a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-2a1 1 0 0 1-1-1V7z"/></svg>',
      },
      {
        label: 'Minhas Instâncias',
        route: 'instances',
        icon: '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm15 3a1 1 0 0 1 1 1v6a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1h14z"/></svg>',
      },
    ],
  },
  {
    type: 'group',
    key: 'manage',
    label: 'Gerenciar instâncias',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/></svg>',
    links: [
      {
        label: 'Hosts',
        route: 'hosts',
        icon: '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2zm0 1h12a1 1 0 0 1 1 1v1H1V2a1 1 0 0 1 1-1zm0 4h12v8a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V5z"/></svg>',
      },
      {
        label: 'Grupos de Hosts',
        route: 'host-groups',
        icon: '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M1 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path fill-rule="evenodd" d="M13.5 5a.5.5 0 0 1 .5.5V7h1.5a.5.5 0 0 1 0 1H14v1.5a.5.5 0 0 1-1 0V8h-1.5a.5.5 0 0 1 0-1H13V5.5a.5.5 0 0 1 .5-.5z"/></svg>',
      },
      {
        label: 'Proxies',
        route: 'proxies',
        icon: '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M11 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h6zM5 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H5z"/><path d="M8 14a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/></svg>',
      },
      {
        label: 'Templates',
        route: 'templates',
        icon: '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm0 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3zm2 3h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1 0-1zm0 2.5h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1 0-1zm0 2.5h4a.5.5 0 0 1 0 1H5a.5.5 0 0 1 0-1z"/></svg>',
      },
      {
        label: 'Triggers Ativas',
        route: 'triggers',
        icon: '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/></svg>',
      },
    ],
  },
  { type: 'divider' },
  { type: 'section', label: 'Orquestração' },
  {
    type: 'link',
    label: 'Conformidade',
    route: 'compliance',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5 10.5a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5zm0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/><path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm0 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3z"/></svg>',
  },
  {
    type: 'link',
    label: 'Orquestração',
    route: 'orchestration',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M6 9a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3A.5.5 0 0 1 6 9zM3.854 4.146a.5.5 0 1 0-.708.708L4.793 6.5 3.146 8.146a.5.5 0 1 0 .708.708l2-2a.5.5 0 0 0 0-.708l-2-2z"/><path d="M2 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2H2zm12 1a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1h12z"/></svg>',
  },
  { type: 'divider' },
  { type: 'section', label: 'Monitoramento' },
  {
    type: 'link',
    label: 'Health Score',
    route: 'health',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8z"/><path d="M8 3.5a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5H5a.5.5 0 0 1 0-1h2.5V4a.5.5 0 0 1 .5-.5z"/></svg>',
  },
  {
    type: 'link',
    label: 'Relatórios',
    route: 'reports',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/><path d="M4.5 12.5A.5.5 0 0 1 5 12h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5zm0-2A.5.5 0 0 1 5 10h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5zm0-2A.5.5 0 0 1 5 8h4a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5z"/></svg>',
  },
  { type: 'divider' },
  { type: 'section', label: 'Config' },
  {
    type: 'link',
    label: 'Usuários',
    route: 'users',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M7 14s-1 0-1-1 1-4 5-4 5 3 5 4-1 1-1 1H7zm4-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path fill-rule="evenodd" d="M5.216 14A2.238 2.238 0 0 1 5 13c0-1.355.68-2.75 1.936-3.72A6.325 6.325 0 0 0 5 9c-4 0-5 3-5 4s1 1 1 1h4.216z"/><path d="M4.5 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z"/></svg>',
  },
  {
    type: 'link',
    label: 'Auditoria',
    route: 'audit',
    icon: '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/><path d="M10.97 4.97a.75.75 0 0 1 1.071 1.05l-3.992 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.235.235 0 0 1 .02-.022z"/></svg>',
  },
]
</script>

<style></style>
