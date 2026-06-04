<template>
  <div>
    <!-- Header -->
    <div class="header">
      <TitlePage title="Instâncias" />
      <router-link to="/instances/new" class="btn btn-primary btn-sm">
        + Nova Instância
      </router-link>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <label class="filter-label">Grupo de Instâncias:</label>
      <select class="form-control filter-select" v-model="selectedGroup">
        <option value="">Todos os grupos</option>
        <option v-for="g in instanceGroups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
      <input
        type="text"
        class="form-control filter-search"
        v-model="search"
        placeholder="Pesquisar instância..."
      />
    </div>

    <!-- Error -->
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- Toast -->
    <Transition name="fade">
      <div v-if="toast.visible" class="alert" :class="`alert-${toast.type}`">
        {{ toast.message }}
      </div>
    </Transition>

    <!-- Table -->
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>URL</th>
            <th>Versão</th>
            <th>Status</th>
            <th>Última Verificação</th>
            <th>Grupo</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && instances.length === 0">
            <td colspan="7" class="table-empty">Carregando...</td>
          </tr>
          <tr v-else-if="filteredInstances.length === 0">
            <td colspan="7" class="table-empty">
              Nenhuma instância encontrada.
              <router-link
                v-if="isSuperadmin && !selectedGroup && !search"
                to="/instances/new"
              >Adicionar primeira instância</router-link>
            </td>
          </tr>
          <tr v-for="inst in filteredInstances" :key="inst.id">
            <td>
              <strong>{{ inst.name }}</strong>
              <div v-if="!inst.is_active" class="text-sm text-muted">desativada</div>
            </td>
            <td class="url-cell">
              <a
                :href="inst.url"
                target="_blank"
                rel="noopener noreferrer"
                class="url-link"
                :title="inst.url"
                @click.stop
              >
                <span class="truncate">{{ inst.url }}</span>
                <svg width="11" height="11" fill="currentColor" viewBox="0 0 16 16" class="external-icon">
                  <path d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                  <path d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                </svg>
              </a>
            </td>
            <td>{{ inst.zabbix_version || '—' }}</td>
            <td v-html="statusBadge(inst.is_active ? inst.status : 'inactive')"></td>
            <td>{{ formatDate(inst.last_check) }}</td>
            <td>{{ inst.group?.name || '—' }}</td>
            <td>
              <div class="actions">
                <button
                  class="btn btn-secondary btn-sm btn-icon"
                  title="Testar Conexão"
                  @click="testConn(inst)"
                  :disabled="testing === inst.id"
                >
                  <span v-if="testing === inst.id" class="spinner"></span>
                  <span v-else>⚡</span>
                </button>
                <template v-if="isSuperadmin">
                  <router-link
                    :to="`/instances/${inst.id}/edit`"
                    class="btn btn-secondary btn-sm btn-icon"
                    title="Editar"
                  >✏️</router-link>
                  <button
                    class="btn btn-secondary btn-sm btn-icon"
                    :title="inst.is_active ? 'Desativar' : 'Ativar'"
                    @click="toggle(inst)"
                  >{{ inst.is_active ? '⏸' : '▶' }}</button>
                  <button
                    class="btn btn-danger btn-sm btn-icon"
                    title="Deletar"
                    @click="confirmDelete(inst)"
                  >🗑</button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Delete modal -->
    <Transition name="fade">
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="modal">
          <div class="modal-title">Confirmar exclusão</div>
          <p>Tem certeza que deseja excluir a instância <strong>{{ deleteTarget.name }}</strong>?</p>
          <p class="text-muted text-sm" style="margin-top: 8px">Esta ação não pode ser desfeita.</p>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="deleteTarget = null">Cancelar</button>
            <button class="btn btn-danger" @click="doDelete" :disabled="deleting">
              <span v-if="deleting" class="spinner"></span>
              Excluir
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import TitlePage from '@/components/ui/TitlePage.vue'

const { client } = useApi()
const authStore = useAuthStore()

const instances = ref([])
const instanceGroups = ref([])
const selectedGroup = ref('')
const search = ref('')
const loading = ref(false)
const error = ref('')
const testing = ref(null)
const deleteTarget = ref(null)
const deleting = ref(false)

// Role já está no store após login — sem necessidade de chamar /auth/me
const isSuperadmin = computed(() => authStore.role === 'superadmin')

// Toast local simples
const toast = reactive({ visible: false, message: '', type: 'success' })
let toastTimer = null

function showToast(message, type = 'success') {
  clearTimeout(toastTimer)
  toast.message = message
  toast.type = type
  toast.visible = true
  toastTimer = setTimeout(() => { toast.visible = false }, 3500)
}

const filteredInstances = computed(() =>
  instances.value.filter((i) => {
    const matchGroup = !selectedGroup.value || String(i.group?.id) === String(selectedGroup.value)
    const matchSearch = !search.value || i.name.toLowerCase().includes(search.value.toLowerCase())
    return matchGroup && matchSearch
  })
)

function statusBadge(status) {
  const map = {
    online:   '<span class="badge badge-online">● Online</span>',
    degraded: '<span class="badge badge-slow">● Degradada</span>',
    offline:  '<span class="badge badge-offline">● Offline</span>',
    inactive: '<span class="badge badge-inactive">● Inativa</span>',
  }
  return map[status] || '<span class="badge">—</span>'
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [instRes, groupsRes] = await Promise.all([
      client.get('/instances'),
      client.get('/instance-groups'),
    ])
    instances.value = instRes.data
    instanceGroups.value = groupsRes.data
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar instâncias'
  } finally {
    loading.value = false
  }
}

async function testConn(inst) {
  testing.value = inst.id
  try {
    const { data } = await client.post(`/instances/${inst.id}/test`)
    if (data.success) {
      showToast(`✅ ${inst.name}: v${data.version} — ${data.latency_ms}ms`, 'success')
      inst.status = 'online'
      inst.zabbix_version = data.version
    } else {
      showToast(`❌ ${inst.name}: ${data.error}`, 'error')
      inst.status = 'offline'
    }
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message || 'Erro ao testar conexão', 'error')
  } finally {
    testing.value = null
  }
}

async function toggle(inst) {
  try {
    const { data } = await client.patch(`/instances/${inst.id}/toggle`)
    inst.is_active = data.is_active
    showToast(`${inst.name} ${inst.is_active ? 'ativada' : 'desativada'}`, 'success')
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message || 'Erro ao alterar status', 'error')
  }
}

function confirmDelete(inst) {
  deleteTarget.value = inst
}

async function doDelete() {
  deleting.value = true
  try {
    await client.delete(`/instances/${deleteTarget.value.id}`)
    instances.value = instances.value.filter((i) => i.id !== deleteTarget.value.id)
    showToast('Instância excluída com sucesso', 'success')
    deleteTarget.value = null
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message || 'Erro ao excluir instância', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 20px;
  margin-bottom: 16px;
}

.filter-label {
  font-size: 14px;
  white-space: nowrap;
}

.filter-select { width: 200px; }
.filter-search { width: 200px; margin-left: auto; }

.form-control {
  padding: 7px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary, #d40000);
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-error {
  background: rgba(200, 0, 0, 0.08);
  border: 1px solid var(--danger);
  color: var(--danger);
}

.alert-success {
  background: rgba(0, 160, 0, 0.08);
  border: 1px solid var(--success);
  color: var(--success);
}

.table-wrapper {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

thead { background: var(--bg); }

th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--bg-hover); }

.table-empty {
  text-align: center;
  padding: 24px !important;
  color: var(--text-muted);
}

.text-sm { font-size: 12px; }
.text-muted { color: var(--text-muted); }

.url-cell { max-width: 220px; }

.url-link {
  display: flex;
  align-items: center;
  gap: 5px;
  max-width: 200px;
  font-size: 12px;
  color: var(--text-muted);
  text-decoration: none;
}

.url-link:hover { color: var(--text); }

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.external-icon { flex-shrink: 0; opacity: 0.5; }

.actions { display: flex; gap: 8px; align-items: center; }

.badge { display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 3px; }
.badge-online   { color: var(--success); }
.badge-slow     { color: var(--warning); }
.badge-offline  { color: var(--danger); }
.badge-inactive { color: var(--text-muted); }

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

.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:hover:not(:disabled) { background: var(--bg-hover); }

.btn-primary {
  background: var(--primary, #d40000);
  color: #fff;
  border-color: var(--primary, #d40000);
}
.btn-primary:hover:not(:disabled) { opacity: 0.85; background: var(--primary, #d40000); }

.btn-secondary { background: var(--card-bg); }

.btn-danger {
  background: var(--danger);
  color: #fff;
  border-color: var(--danger);
}
.btn-danger:hover:not(:disabled) { opacity: 0.85; }

.btn-sm { padding: 4px 10px; font-size: 13px; }
.btn-icon { padding: 4px 8px; }

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 24px;
  width: 100%;
  max-width: 400px;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
