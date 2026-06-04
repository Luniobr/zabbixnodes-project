<template>
  <div>
    <!-- Header -->
    <div class="header">
      <TitlePage title="Proxies" />
      <button
        class="btn btn-primary btn-sm"
        @click="showCreateModal = true"
        :disabled="!selectedInstance || !canWrite"
      >
        + Novo Proxy
      </button>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <label class="filter-label">Grupo de Instâncias:</label>
      <select class="form-control filter-select" v-model="selectedInstanceGroup" @change="onInstanceGroupChange">
        <option value="">— Selecione —</option>
        <option v-for="g in instanceGroups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>

      <template v-if="selectedInstanceGroup">
        <label class="filter-label">Instância:</label>
        <select class="form-control filter-select" v-model="selectedInstance" @change="loadProxies">
          <option value="">— Selecione —</option>
          <option v-for="inst in filteredInstances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
        </select>
      </template>

      <input
        v-if="selectedInstance"
        type="text"
        class="form-control filter-search"
        v-model="searchProxy"
        placeholder="Pesquisar proxy..."
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
            <th>Modo</th>
            <th>Último Acesso</th>
            <th>Descrição</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!selectedInstanceGroup">
            <td colspan="5" class="table-empty">Selecione um grupo de instâncias para começar</td>
          </tr>
          <tr v-else-if="!selectedInstance">
            <td colspan="5" class="table-empty">Selecione uma instância</td>
          </tr>
          <tr v-else-if="loading">
            <td colspan="5" class="table-empty">Carregando...</td>
          </tr>
          <tr v-else-if="filteredProxies.length === 0">
            <td colspan="5" class="table-empty">Nenhum proxy encontrado</td>
          </tr>
          <tr v-for="p in filteredProxies" :key="p.proxyid">
            <td><strong>{{ p.name }}</strong></td>
            <td>
              <span class="badge" :class="p.operating_mode == '0' ? 'badge-online' : 'badge-unknown'">
                {{ p.operating_mode == '0' ? 'Ativo' : 'Passivo' }}
              </span>
            </td>
            <td class="text-sm">{{ formatLastAccess(p.lastaccess) }}</td>
            <td class="text-muted text-sm">{{ p.description || '—' }}</td>
            <td>
              <button
                v-if="canWrite"
                class="btn btn-danger btn-sm btn-icon"
                title="Deletar"
                @click="confirmDelete(p)"
              >🗑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <Transition name="fade">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false; createError = ''">
        <div class="modal">
          <div class="modal-title">Novo Proxy</div>
          <div v-if="createError" class="alert alert-error">{{ createError }}</div>

          <div class="form-group">
            <label class="form-label">Nome *</label>
            <input type="text" class="form-control" v-model="newProxy.name" placeholder="proxy-01" />
          </div>
          <div class="form-group">
            <label class="form-label">Modo de Operação</label>
            <select class="form-control" v-model="newProxy.operating_mode">
              <option value="0">Ativo</option>
              <option value="1">Passivo</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Descrição</label>
            <input type="text" class="form-control" v-model="newProxy.description" placeholder="Proxy de produção..." />
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showCreateModal = false; createError = ''">Cancelar</button>
            <button class="btn btn-primary" @click="createProxy" :disabled="creating">
              <span v-if="creating" class="spinner"></span>
              Criar Proxy
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete Modal -->
    <Transition name="fade">
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="modal">
          <div class="modal-title">Confirmar exclusão</div>
          <p>Excluir o proxy <strong>{{ deleteTarget.name }}</strong>?</p>
          <p class="text-muted text-sm" style="margin-top: 8px">
            Esta ação remove o proxy da instância Zabbix.
          </p>
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
import { useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'
import TitlePage from '@/components/ui/TitlePage.vue'

const route = useRoute()
const { client } = useApi()

// State
const instanceGroups = ref([])
const instances = ref([])
const filteredInstances = ref([])
const selectedInstanceGroup = ref('')
const selectedInstance = ref('')
const proxies = ref([])
const searchProxy = ref('')
const canWrite = ref(false)
const loading = ref(false)
const error = ref('')

// Create modal
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const newProxy = ref({ name: '', operating_mode: '0', description: '' })

// Delete modal
const deleteTarget = ref(null)
const deleting = ref(false)

// Toast
const toast = reactive({ visible: false, message: '', type: 'success' })
let toastTimer = null

function showToast(message, type = 'success') {
  clearTimeout(toastTimer)
  toast.message = message
  toast.type = type
  toast.visible = true
  toastTimer = setTimeout(() => { toast.visible = false }, 3500)
}

const filteredProxies = computed(() => {
  if (!searchProxy.value) return proxies.value
  const q = searchProxy.value.toLowerCase()
  return proxies.value.filter(p => p.name.toLowerCase().includes(q))
})

async function init() {
  try {
    const [groupsRes, instancesRes] = await Promise.all([
      client.get('/instance-groups'),
      client.get('/instances'),
    ])
    instanceGroups.value = groupsRes.data
    instances.value = instancesRes.data

    const instanceIdFromUrl = route.query.instance_id
    if (instanceIdFromUrl) {
      const inst = instances.value.find(i => String(i.id) === String(instanceIdFromUrl))
      if (inst?.group) {
        selectedInstanceGroup.value = inst.group.id
        filteredInstances.value = instances.value.filter(
          i => i.group && String(i.group.id) === String(inst.group.id)
        )
      }
      selectedInstance.value = instanceIdFromUrl
      await loadProxies()
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar dados'
  }
}

function onInstanceGroupChange() {
  selectedInstance.value = ''
  proxies.value = []
  searchProxy.value = ''
  filteredInstances.value = instances.value.filter(
    i => i.group && String(i.group.id) === String(selectedInstanceGroup.value)
  )
}

async function loadProxies() {
  if (!selectedInstance.value) { proxies.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const { data } = await client.get(`/instances/${selectedInstance.value}/proxies`)
    proxies.value = data
    const inst = instances.value.find(i => String(i.id) === String(selectedInstance.value))
    canWrite.value = inst?.can_write ?? false
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar proxies'
  } finally {
    loading.value = false
  }
}

async function createProxy() {
  if (!newProxy.value.name) return
  creating.value = true
  createError.value = ''
  try {
    await client.post(`/instances/${selectedInstance.value}/proxies`, {
      name: newProxy.value.name,
      operating_mode: parseInt(newProxy.value.operating_mode),
      description: newProxy.value.description,
    })
    showCreateModal.value = false
    newProxy.value = { name: '', operating_mode: '0', description: '' }
    showToast('Proxy criado com sucesso', 'success')
    await loadProxies()
  } catch (e) {
    createError.value = e?.response?.data?.detail || e?.message || 'Erro ao criar proxy'
  } finally {
    creating.value = false
  }
}

function confirmDelete(p) {
  deleteTarget.value = p
}

async function doDelete() {
  deleting.value = true
  try {
    await client.delete(`/instances/${selectedInstance.value}/proxies/${deleteTarget.value.proxyid}`)
    proxies.value = proxies.value.filter(p => p.proxyid !== deleteTarget.value.proxyid)
    showToast('Proxy excluído', 'success')
    deleteTarget.value = null
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message || 'Erro ao excluir proxy', 'error')
  } finally {
    deleting.value = false
  }
}

function formatLastAccess(ts) {
  if (!ts || ts === '0') return '—'
  return new Date(parseInt(ts) * 1000).toLocaleString('pt-BR')
}

onMounted(init)
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
  flex-wrap: wrap;
}

.filter-label { font-size: 14px; white-space: nowrap; }
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

table { width: 100%; border-collapse: collapse; font-size: 14px; }
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

.badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
}

.badge-online  { color: var(--success); }
.badge-unknown { background: var(--bg); border: 1px solid var(--border); color: var(--text-muted); }

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
  margin-bottom: 16px;
}

.form-group { margin-bottom: 16px; }

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
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
