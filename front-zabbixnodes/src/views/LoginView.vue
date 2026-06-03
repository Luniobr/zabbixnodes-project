<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <h1>ZabbixNodes</h1>
        <p>Gerenciamento Multi-Instância Zabbix</p>
      </div>

      <div class="alert alert-error" v-if="msgError">{{ msgError }}</div>
      <form @submit.prevent="submit">
        <BaseInput
          id="username"
          v-model="username"
          label="Usuário"
          placeholder="Username"
          autocomplete="username"
          required
        />

        <BaseInput
          id="password"
          type="password"
          v-model="password"
          label="Senha"
          placeholder="Senha"
          autocomplete="current-password"
          required
        />
        <BaseButton type="submit" :loading="loading" style="width: 100%; justify-content: center"
          >Entrar</BaseButton
        >
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
// Components
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'

const { client } = useApi()
const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const msgError = ref(null)

async function submit() {
  loading.value = true
  msgError.value = null

  try {
    const { data } = await client.post('/auth/login', {
      username: username.value,
      password: password.value,
    })
    authStore.setAuth({
      token: data.access_token,
      username: data.username || username.value,
      role: data.role || 'admin',
    })
    router.push('/dashboard')
  } catch (error) {
    const status = error?.response?.status
    if (status === 401) {
      msgError.value = 'Credenciais inválidas. Por favor, verifique seu username e password.'
    } else {
      msgError.value = 'Falha no login'
    }

    console.error('Login failed:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped></style>
