<template>
  <div class="topbar">
    <span class="topbar-brand">Zabbix<span>Nodes</span></span>
    <div class="topbar-user">
      <span>👤 {{ authStore.user }} ({{ authStore.role }})</span>
    </div>

    <select
      class="topbar-btn"
      style="border: none; background: transparent; color: var(--topbar-text); cursor: pointer"
      v-model="currentTheme"
      @change="applyTheme"
    >
      <option value="default">Zabbix Blue</option>
      <option value="dark">Dark</option>
      <option value="lunio">Lunio Light</option>
      <option value="lunio-dark">Lunio Dark</option>
      <option value="verde">Verde</option>
    </select>

    <button class="topbar-btn" @click="handleLogout">Sair</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// Themes
const themes = {
  dark: '/themes/dark.css',
  lunio: '/themes/lunio.css',
  'lunio-dark': '/themes/lunio-dark.css',
  verde: '/themes/verde.css',
}

const currentTheme = ref(localStorage.getItem('zabbixnodes_theme') || 'default')

function applyTheme() {
  localStorage.setItem('zabbixnodes_theme', currentTheme.value)
  let link = document.getElementById('theme-stylesheet')
  if (!link) {
    link = document.createElement('link')
    link.rel = 'stylesheet'
    link.id = 'theme-stylesheet'
    document.head.appendChild(link)
  }
  link.href = themes[currentTheme.value] || ''
}

// Aplica o tema salvo ao carregar
applyTheme()

// Logout
function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<style></style>
