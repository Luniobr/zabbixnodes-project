<template>
  <div>
    <!-- Breadcrumb -->
    <div class="breadcrumb">
      <router-link to="/instances" class="breadcrumb-link">Instâncias</router-link>
      <span class="breadcrumb-sep">&nbsp;/&nbsp;</span>
      <span>{{ isEdit ? 'Editar Instância' : 'Nova Instância' }}</span>
    </div>

    <div class="form-card">
      <!-- Alerts -->
      <div v-if="loadError" class="alert alert-error">{{ loadError }}</div>
      <div v-if="saveError" class="alert alert-error">{{ saveError }}</div>
      <div
        v-if="testResult"
        class="alert"
        :class="testResult.success ? 'alert-success' : 'alert-error'"
      >
        {{
          testResult.success
            ? `Conexão OK — Zabbix v${testResult.version} (${testResult.latency_ms}ms)`
            : `Falha: ${testResult.error}`
        }}
      </div>

      <form @submit.prevent="save">
        <!-- Nome -->
        <div class="form-group">
          <label class="form-label">Nome *</label>
          <input
            type="text"
            class="form-control"
            v-model="form.name"
            placeholder="Cliente ABC"
            required
          />
          <div class="form-hint">Nome único para identificar a instância</div>
        </div>

        <!-- URL -->
        <div class="form-group">
          <label class="form-label">URL da API *</label>
          <input
            type="url"
            class="form-control"
            v-model="form.url"
            placeholder="https://zabbix.cliente.com"
            required
          />
          <div class="form-hint">URL base do Zabbix (sem /api_jsonrpc.php)</div>
        </div>

        <!-- Auth mode -->
        <div class="form-group">
          <label class="form-label">Modo de Autenticação</label>
          <div class="auth-mode-selector">
            <label class="radio-label">
              <input type="radio" v-model="form.auth_mode" value="token" />
              API Token
            </label>
            <label class="radio-label">
              <input type="radio" v-model="form.auth_mode" value="credentials" />
              Usuário + Senha
            </label>
          </div>
        </div>

        <!-- Token -->
        <div class="form-group" v-if="form.auth_mode === 'token'">
          <label class="form-label">
            {{ isEdit ? 'Novo API Token (deixe vazio para manter)' : 'API Token *' }}
          </label>
          <input
            type="password"
            class="form-control"
            v-model="form.api_token"
            placeholder="••••••••••••••••"
            :required="form.auth_mode === 'token' && !isEdit"
          />
          <div class="form-hint">
            Token permanente gerado em Administração → Usuários → Token de API
          </div>
        </div>

        <!-- Credentials -->
        <template v-if="form.auth_mode === 'credentials'">
          <div class="form-group">
            <label class="form-label">
              {{ isEdit ? 'Usuário Zabbix (deixe vazio para manter)' : 'Usuário Zabbix *' }}
            </label>
            <input
              type="text"
              class="form-control"
              v-model="form.api_user"
              placeholder="Admin"
              :required="form.auth_mode === 'credentials' && !isEdit"
            />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ isEdit ? 'Senha Zabbix (deixe vazio para manter)' : 'Senha Zabbix *' }}
            </label>
            <input
              type="password"
              class="form-control"
              v-model="form.api_password"
              placeholder="••••••••••••••••"
              :required="form.auth_mode === 'credentials' && !isEdit"
            />
            <div class="form-hint">
              Atenção: sessões por usuário+senha expiram; prefira tokens permanentes quando possível
            </div>
          </div>
        </template>

        <!-- Descrição -->
        <div class="form-group">
          <label class="form-label">Descrição</label>
          <textarea
            class="form-control"
            v-model="form.description"
            rows="2"
            placeholder="Ambiente de produção do cliente..."
          ></textarea>
        </div>

        <!-- Grupo -->
        <div class="form-group">
          <label class="form-label">Grupo</label>
          <select class="form-control" v-model="form.group_id">
            <option value="">— Sem grupo —</option>
            <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </div>

        <!-- Actions -->
        <div class="form-actions">
          <button
            type="button"
            class="btn btn-secondary"
            @click="testConn"
            :disabled="testing || !canTest"
          >
            <span v-if="testing" class="spinner"></span>
            ⚡ Testar Conexão
          </button>
          <div class="spacer"></div>
          <router-link to="/instances" class="btn btn-secondary">Cancelar</router-link>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            {{ saving ? 'Salvando...' : 'Salvar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const { client } = useApi()

const instanceId = route.params.id || null
const isEdit = computed(() => !!instanceId)

const form = ref({
  name: '',
  url: '',
  auth_mode: 'token',
  api_token: '',
  api_user: '',
  api_password: '',
  description: '',
  group_id: '',
  tags: [],
})

const groups = ref([])
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const loadError = ref('')
const saveError = ref('')

const canTest = computed(() => {
  if (!form.value.url) return false
  if (form.value.auth_mode === 'token') {
    return !!(form.value.api_token || instanceId)
  }
  return !!(form.value.api_user && form.value.api_password) || !!instanceId
})

function authData() {
  if (form.value.auth_mode === 'token') {
    return { api_token: form.value.api_token }
  }
  return { api_user: form.value.api_user, api_password: form.value.api_password }
}

async function init() {
  try {
    const { data } = await client.get('/instance-groups')
    groups.value = data
  } catch (_) {}

  if (instanceId) {
    try {
      const { data } = await client.get(`/instances/${instanceId}`)
      form.value = {
        name: data.name,
        url: data.url,
        auth_mode: 'token',
        api_token: '',
        api_user: '',
        api_password: '',
        description: data.description || '',
        group_id: data.group_id || '',
        tags: data.tags || [],
      }
    } catch (e) {
      loadError.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar instância'
    }
  }
}

async function testConn() {
  if (!form.value.url) return
  testing.value = true
  testResult.value = null
  try {
    const hasNewToken = form.value.auth_mode === 'token' && form.value.api_token
    const hasNewCreds =
      form.value.auth_mode === 'credentials' && form.value.api_user && form.value.api_password

    if (hasNewToken || hasNewCreds) {
      const { data } = await client.post('/instances/test-credentials', {
        url: form.value.url,
        ...authData(),
      })
      testResult.value = data
    } else if (instanceId) {
      const { data } = await client.post(`/instances/${instanceId}/test`)
      testResult.value = data
    }
  } catch (e) {
    testResult.value = {
      success: false,
      error: e?.response?.data?.detail || e?.message || 'Erro ao testar conexão',
    }
  } finally {
    testing.value = false
  }
}

async function save() {
  saving.value = true
  saveError.value = ''
  try {
    const payload = {
      name: form.value.name,
      url: form.value.url,
      description: form.value.description,
      group_id: form.value.group_id || null,
      tags: form.value.tags,
    }

    if (form.value.auth_mode === 'token') {
      if (form.value.api_token) payload.api_token = form.value.api_token
    } else {
      if (form.value.api_user) payload.api_user = form.value.api_user
      if (form.value.api_password) payload.api_password = form.value.api_password
    }

    if (instanceId) {
      await client.put(`/instances/${instanceId}`, payload)
    } else {
      await client.post('/instances', payload)
    }

    router.push('/instances')
  } catch (e) {
    saveError.value = e?.response?.data?.detail || e?.message || 'Erro ao salvar instância'
  } finally {
    saving.value = false
  }
}

onMounted(init)
</script>

<style scoped>
.breadcrumb {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 24px;
}

.breadcrumb-link {
  color: var(--text-muted);
  font-weight: 400;
  text-decoration: none;
}

.breadcrumb-link:hover {
  color: var(--text);
}

.breadcrumb-sep {
  color: var(--text-muted);
}

.form-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 24px;
  max-width: 640px;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary, #d40000);
}

.form-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.auth-mode-selector {
  display: flex;
  gap: 16px;
  margin-top: 4px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 24px;
}

.spacer {
  flex: 1;
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-error {
  background: rgba(var(--danger-rgb, 200, 0, 0), 0.08);
  border: 1px solid var(--danger);
  color: var(--danger);
}

.alert-success {
  background: rgba(var(--success-rgb, 0, 160, 0), 0.08);
  border: 1px solid var(--success);
  color: var(--success);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:hover:not(:disabled) {
  background: var(--bg-hover);
}

.btn-secondary {
  background: var(--card-bg);
}

.btn-primary {
  background: var(--primary, #d40000);
  color: #fff;
  border-color: var(--primary, #d40000);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.85;
  background: var(--primary, #d40000);
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
