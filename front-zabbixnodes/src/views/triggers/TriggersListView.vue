<template>
  <div>
    <div class="header">
      <TitlePage title="Triggers Ativas" />
    </div>

    <!-- Filters -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-field">
          <label class="form-label">Instância</label>
          <select class="form-control" v-model="filters.instanceId" @change="onInstanceChange">
            <option value="">— Selecione —</option>
            <option v-for="inst in instances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
          </select>
        </div>
        <div class="filter-field">
          <label class="form-label">Severidade mínima</label>
          <select class="form-control" v-model="filters.minSeverity">
            <option value="0">Todas</option>
            <option value="2">Warning +</option>
            <option value="3">Average +</option>
            <option value="4">High +</option>
            <option value="5">Disaster</option>
          </select>
        </div>
        <div class="filter-field">
          <label class="form-label">Grupo de Hosts</label>
          <select class="form-control" v-model="filters.groupId" :disabled="!filters.instanceId">
            <option value="">Todos os grupos</option>
            <option v-for="g in hostGroups" :key="g.groupid" :value="g.groupid">{{ g.name }}</option>
          </select>
        </div>
        <div class="filter-field filter-field-flex">
          <label class="form-label">Filtrar por host/trigger</label>
          <input type="text" class="form-control" v-model="filters.search" placeholder="buscar..." />
        </div>
        <button class="btn btn-primary" @click="load" :disabled="!filters.instanceId || loading">
          <span v-if="loading" class="spinner"></span>
          Buscar
        </button>
      </div>
    </div>

    <!-- Summary bar -->
    <div v-if="loaded" class="health-bar">
      <div class="health-indicator">
        <strong>{{ filtered.length }} trigger(s) em problema</strong>
      </div>
      <div class="health-stats">
        <div class="health-stat">
          <span class="badge sev-disaster">Disaster</span>
          <strong>{{ countBySev(5) }}</strong>
        </div>
        <div class="health-stat">
          <span class="badge sev-high">High</span>
          <strong>{{ countBySev(4) }}</strong>
        </div>
        <div class="health-stat">
          <span class="badge sev-average">Average</span>
          <strong>{{ countBySev(3) }}</strong>
        </div>
        <div class="health-stat">
          <span class="badge sev-warning">Warning</span>
          <strong>{{ countBySev(2) }}</strong>
        </div>
        <div class="health-stat">
          <span class="badge sev-info">Info</span>
          <strong>{{ countBySev(1) }}</strong>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <Transition name="fade">
      <div v-if="toast.visible" class="alert" :class="`alert-${toast.type}`">{{ toast.message }}</div>
    </Transition>

    <p v-if="!loaded && !loading && !error" class="text-muted text-sm hint">
      Selecione uma instância e clique em Buscar.
    </p>

    <!-- Triggers table -->
    <div v-if="loaded" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th style="width: 100px">Severidade</th>
            <th>Trigger</th>
            <th>Host</th>
            <th style="width: 140px">Último evento</th>
            <th style="width: 80px; text-align: center">Ack</th>
            <th style="width: 60px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="table-empty">Carregando...</td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="6" class="table-empty">Nenhuma trigger em problema</td>
          </tr>
          <tr v-for="t in filtered" :key="t.triggerid">
            <td>
              <span class="badge" :class="sevClass(t.priority)">{{ sevLabel(t.priority) }}</span>
            </td>
            <td>
              <div style="font-weight: 500; font-size: 13px">{{ t.description }}</div>
              <div v-if="t.comments" class="text-muted" style="font-size: 11px; margin-top: 2px">{{ t.comments }}</div>
            </td>
            <td class="text-sm">
              <div v-for="h in t.hosts" :key="h.hostid">{{ h.name || h.host }}</div>
            </td>
            <td class="text-sm text-muted">{{ fmtTime(t.lastchange) }}</td>
            <td style="text-align: center">
              <span v-if="t.lastEvent?.acknowledged == '1'" style="color: var(--success)" title="Reconhecido">✓</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <button
                v-if="t.lastEvent?.eventid && t.lastEvent?.acknowledged != '1'"
                class="btn btn-secondary btn-sm btn-icon"
                title="Reconhecer"
                @click="openAck(t)"
              >✓</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Ack modal -->
    <Transition name="fade">
      <div v-if="ackTarget" class="modal-overlay" @click.self="ackTarget = null; ackMessage = ''">
        <div class="modal">
          <div class="modal-title">Reconhecer Trigger</div>
          <p class="text-sm" style="margin-bottom: 12px">{{ ackTarget.description }}</p>
          <div class="form-group">
            <label class="form-label">Mensagem (opcional)</label>
            <input type="text" class="form-control" v-model="ackMessage" placeholder="Investigando..." />
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="ackTarget = null; ackMessage = ''">Cancelar</button>
            <button class="btn btn-primary" @click="doAck" :disabled="acking">
              <span v-if="acking" class="spinner"></span>
              Reconhecer
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

const instances = ref([])
const hostGroups = ref([])
const triggers = ref([])
const filters = reactive({ instanceId: '', minSeverity: '0', groupId: '', search: '' })
const loading = ref(false)
const loaded = ref(false)
const error = ref('')

const ackTarget = ref(null)
const ackMessage = ref('')
const acking = ref(false)

const toast = reactive({ visible: false, message: '', type: 'success' })
let toastTimer = null

function showToast(message, type = 'success') {
  clearTimeout(toastTimer)
  toast.message = message
  toast.type = type
  toast.visible = true
  toastTimer = setTimeout(() => { toast.visible = false }, 3500)
}

const filtered = computed(() => {
  if (!filters.search) return triggers.value
  const s = filters.search.toLowerCase()
  return triggers.value.filter(t =>
    t.description.toLowerCase().includes(s) ||
    t.hosts.some(h => (h.name || h.host).toLowerCase().includes(s))
  )
})

function countBySev(sev) {
  return filtered.value.filter(t => parseInt(t.priority) === sev).length
}

function sevLabel(p) {
  return ['Not classified', 'Info', 'Warning', 'Average', 'High', 'Disaster'][parseInt(p)] || p
}

function sevClass(p) {
  return ['sev-unknown', 'sev-info', 'sev-warning', 'sev-average', 'sev-high', 'sev-disaster'][parseInt(p)] || 'sev-unknown'
}

function fmtTime(ts) {
  if (!ts) return '—'
  return new Date(parseInt(ts) * 1000).toLocaleString('pt-BR')
}

async function init() {
  try {
    const { data } = await client.get('/instances')
    instances.value = data.filter(i => i.is_active)

    const instId = route.query.instance_id
    if (instId) {
      filters.instanceId = instId
      await loadGroups()
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar instâncias'
  }
}

async function onInstanceChange() {
  triggers.value = []
  loaded.value = false
  filters.groupId = ''
  await loadGroups()
}

async function loadGroups() {
  if (!filters.instanceId) return
  try {
    const { data } = await client.get(`/instances/${filters.instanceId}/host-groups`)
    hostGroups.value = data
  } catch (_) {
    hostGroups.value = []
  }
}

async function load() {
  if (!filters.instanceId) return
  loading.value = true
  error.value = ''
  loaded.value = false
  try {
    const params = { only_problems: true }
    if (parseInt(filters.minSeverity) > 0) params.min_severity = filters.minSeverity
    if (filters.groupId) params.group_id = filters.groupId
    const { data } = await client.get(`/instances/${filters.instanceId}/triggers`, { params })
    triggers.value = data
    loaded.value = true
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar triggers'
  } finally {
    loading.value = false
  }
}

function openAck(t) {
  ackTarget.value = t
  ackMessage.value = ''
}

async function doAck() {
  acking.value = true
  try {
    await client.post(
      `/instances/${filters.instanceId}/triggers/${ackTarget.value.triggerid}/ack`,
      { event_id: ackTarget.value.lastEvent.eventid, message: ackMessage.value }
    )
    ackTarget.value.lastEvent.acknowledged = '1'
    showToast('Trigger reconhecida', 'success')
    ackTarget.value = null
    ackMessage.value = ''
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message, 'error')
  } finally {
    acking.value = false
  }
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

.filter-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 20px;
  margin-bottom: 16px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-field { min-width: 160px; }
.filter-field-flex { flex: 1; min-width: 180px; }

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
}

.form-control {
  width: 100%;
  padding: 7px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  box-sizing: border-box;
}

.form-control:focus { outline: none; border-color: var(--primary, #d40000); }
.form-control:disabled { opacity: 0.5; cursor: not-allowed; }

/* Health bar (summary) */
.health-bar {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.health-indicator { font-size: 15px; }

.health-stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.health-stat {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hint { padding: 24px 0; }

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-error { background: rgba(200,0,0,0.08); border: 1px solid var(--danger); color: var(--danger); }
.alert-success { background: rgba(0,160,0,0.08); border: 1px solid var(--success); color: var(--success); }

/* Severity badges */
.badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
  font-weight: 500;
}

.sev-disaster { background: #7b0000; color: #fff; }
.sev-high     { background: #d40000; color: #fff; }
.sev-average  { background: #ef6600; color: #fff; }
.sev-warning  { background: #f59e0b; color: #1a1a1a; }
.sev-info     { background: #3b82f6; color: #fff; }
.sev-unknown  { background: #9ca3af; color: #fff; }

/* Table */
.table-wrapper {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow-x: auto;
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
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--bg-hover); }

.table-empty { text-align: center; padding: 24px !important; color: var(--text-muted); }
.text-sm { font-size: 12px; }
.text-muted { color: var(--text-muted); }

/* Buttons */
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
  white-space: nowrap;
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:hover:not(:disabled) { background: var(--bg-hover); }

.btn-primary { background: var(--primary, #d40000); color: #fff; border-color: var(--primary, #d40000); }
.btn-primary:hover:not(:disabled) { opacity: 0.85; background: var(--primary, #d40000); }
.btn-secondary { background: var(--card-bg); }
.btn-sm { padding: 4px 10px; font-size: 13px; }
.btn-icon { padding: 4px 8px; }

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
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
  max-width: 440px;
}

.modal-title { font-size: 18px; font-weight: 600; margin-bottom: 12px; }
.form-group { margin-bottom: 16px; }

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
