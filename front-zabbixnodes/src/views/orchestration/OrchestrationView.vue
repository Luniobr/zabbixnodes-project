<template>
  <div>
    <div class="header">
      <TitlePage title="Orquestração em Massa" />
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab-btn" :class="{ active: tab === 'run' }" @click="tab = 'run'">▶ Nova Operação</button>
      <button class="tab-btn" :class="{ active: tab === 'history' }" @click="switchHistory">📋 Histórico</button>
    </div>

    <!-- ===== TAB: Nova Operação ===== -->
    <div v-show="tab === 'run'">
      <div class="run-card">
        <div v-if="runError" class="alert alert-error">{{ runError }}</div>

        <!-- Operation selector -->
        <div class="form-group">
          <label class="form-label">Operação</label>
          <select class="form-control" v-model="opType" @change="resetRun">
            <option value="">— Selecione uma operação —</option>
            <option value="create_host_group">Criar Grupo de Hosts em múltiplas instâncias</option>
            <option value="enable_hosts">Habilitar Hosts por padrão</option>
            <option value="disable_hosts">Desabilitar Hosts por padrão</option>
          </select>
        </div>

        <!-- CREATE HOST GROUP params -->
        <div v-if="opType === 'create_host_group'" class="form-group">
          <label class="form-label">Nome do Grupo *</label>
          <input type="text" class="form-control" v-model="params.group_name" placeholder="Ex: Linux Servers" />
        </div>

        <!-- TOGGLE HOSTS params -->
        <div v-if="opType === 'enable_hosts' || opType === 'disable_hosts'" class="form-group">
          <label class="form-label">Padrão de Hostname *</label>
          <input type="text" class="form-control" v-model="params.pattern" placeholder="Ex: web-, db-prod, .cliente.com" />
          <div class="form-hint">Hosts cujo nome ou hostname <em>contenha</em> esse texto serão afetados</div>
        </div>

        <!-- Instance selector -->
        <div v-if="opType" class="form-group">
          <label class="form-label">Instâncias *</label>
          <div class="instance-filter">
            <label class="filter-label" style="white-space: nowrap; font-size: 12px">Filtrar por grupo:</label>
            <select class="form-control" style="width: 200px; font-size: 13px" v-model="selectedInstanceGroup" @change="selectedIds = []">
              <option value="">Todos os grupos</option>
              <option v-for="g in instanceGroups" :key="g.id" :value="g.id">{{ g.name }}</option>
            </select>
          </div>
          <div v-if="loadingInstances" class="text-muted text-sm">Carregando instâncias...</div>
          <div class="instance-list">
            <label v-for="inst in filteredInstances" :key="inst.id" class="instance-item">
              <input type="checkbox" :value="inst.id" v-model="selectedIds" />
              <span>{{ inst.name }}</span>
              <span class="badge" :class="inst.status === 'online' ? 'badge-online' : 'badge-offline'">{{ inst.status }}</span>
            </label>
            <div v-if="filteredInstances.length === 0 && !loadingInstances" class="text-muted text-sm">
              Nenhuma instância encontrada
            </div>
          </div>
          <div class="instance-actions">
            <button class="btn btn-secondary btn-sm" @click="selectAll">Selecionar tudo</button>
            <button class="btn btn-secondary btn-sm" @click="selectedIds = []">Limpar</button>
            <span class="text-muted text-sm" style="margin-left: auto">{{ selectedIds.length }} selecionada(s)</span>
          </div>
        </div>

        <!-- Execute -->
        <div v-if="opType" style="margin-top: 8px">
          <button class="btn btn-primary" @click="executeOp" :disabled="running || selectedIds.length === 0">
            <span v-if="running" class="spinner"></span>
            {{ running ? 'Executando...' : '▶ Executar' }}
          </button>
        </div>
      </div>

      <!-- Results -->
      <div v-if="runResults" style="margin-top: 24px">
        <div class="results-title">
          Resultado da Execução
          <span class="badge badge-unknown text-sm">Run #{{ lastRunId }}</span>
        </div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Instância</th>
                <th style="width: 120px">Status</th>
                <th>Detalhes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in runResults" :key="r.instance_name">
                <td><strong>{{ r.instance_name }}</strong></td>
                <td><span class="badge" :class="resultBadgeClass(r.status)">{{ resultLabel(r.status) }}</span></td>
                <td class="text-sm text-muted">{{ resultDetail(r) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ===== TAB: Histórico ===== -->
    <div v-show="tab === 'history'">
      <div v-if="historyLoading" class="text-muted text-sm" style="padding: 16px">Carregando...</div>
      <div v-if="historyError" class="alert alert-error">{{ historyError }}</div>
      <div v-if="!historyLoading && history.length === 0 && !historyError" class="text-muted text-sm" style="padding: 16px">
        Nenhuma execução registrada
      </div>

      <div v-if="history.length > 0" class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th style="width: 60px">#</th>
              <th>Operação</th>
              <th>Parâmetros</th>
              <th style="width: 140px">Início</th>
              <th style="width: 90px">Status</th>
              <th style="width: 60px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in history" :key="run.id">
              <td class="text-muted text-sm">{{ run.id }}</td>
              <td class="text-sm">{{ opTypeLabel(run.type) }}</td>
              <td class="text-sm text-muted">{{ runParamSummary(run) }}</td>
              <td class="text-sm text-muted">{{ fmtDate(run.started_at) }}</td>
              <td><span class="badge badge-online">Concluído</span></td>
              <td>
                <button class="btn btn-secondary btn-sm" @click="viewRun(run.id)">Ver</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Run detail modal -->
      <Transition name="fade">
        <div v-if="detailRun" class="modal-overlay" @click.self="detailRun = null">
          <div class="modal modal-lg">
            <div class="modal-title">
              {{ opTypeLabel(detailRun.type) }}
              <span class="badge badge-unknown text-sm">#{{ detailRun.id }}</span>
            </div>
            <div class="text-muted text-sm" style="margin-bottom: 12px">{{ runParamSummary(detailRun) }}</div>
            <div class="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Instância</th>
                    <th style="width: 120px">Status</th>
                    <th>Detalhes</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in (detailRun.results ?? [])" :key="r.instance_name">
                    <td>{{ r.instance_name }}</td>
                    <td><span class="badge" :class="resultBadgeClass(r.status)">{{ resultLabel(r.status) }}</span></td>
                    <td class="text-sm text-muted">{{ resultDetail(r) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="detailRun = null">Fechar</button>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import TitlePage from '@/components/ui/TitlePage.vue'

const { client } = useApi()

// Tab
const tab = ref('run')

// State
const instances = ref([])
const instanceGroups = ref([])
const selectedInstanceGroup = ref('')
const selectedIds = ref([])
const loadingInstances = ref(false)

// Operation
const opType = ref('')
const params = ref({ group_name: '', pattern: '' })
const running = ref(false)
const runError = ref('')
const runResults = ref(null)
const lastRunId = ref(null)

// History
const history = ref([])
const historyLoading = ref(false)
const historyError = ref('')
const detailRun = ref(null)
const historyLoaded = ref(false)

const filteredInstances = computed(() => {
  if (!selectedInstanceGroup.value) return instances.value
  return instances.value.filter(i => String(i.group?.id) === String(selectedInstanceGroup.value))
})

async function init() {
  loadingInstances.value = true
  try {
    const [instancesRes, groupsRes] = await Promise.all([
      client.get('/instances'),
      client.get('/instance-groups'),
    ])
    instances.value = instancesRes.data.filter(i => i.is_active)
    instanceGroups.value = groupsRes.data
  } catch (e) {
    runError.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar dados'
  } finally {
    loadingInstances.value = false
  }
}

function resetRun() {
  params.value = { group_name: '', pattern: '' }
  selectedIds.value = []
  selectedInstanceGroup.value = ''
  runResults.value = null
  runError.value = ''
}

function selectAll() {
  selectedIds.value = filteredInstances.value.map(i => i.id)
}

async function switchHistory() {
  tab.value = 'history'
  if (!historyLoaded.value) await loadHistory()
}

async function executeOp() {
  runError.value = ''
  runResults.value = null

  if (!opType.value) return
  if (selectedIds.value.length === 0) { runError.value = 'Selecione ao menos uma instância.'; return }

  let endpoint, body

  if (opType.value === 'create_host_group') {
    if (!params.value.group_name.trim()) { runError.value = 'Informe o nome do grupo.'; return }
    endpoint = '/orchestration/create-host-group'
    body = { name: params.value.group_name.trim(), instance_ids: selectedIds.value }

  } else if (opType.value === 'enable_hosts' || opType.value === 'disable_hosts') {
    if (!params.value.pattern.trim()) { runError.value = 'Informe o padrão de hostname.'; return }
    endpoint = '/orchestration/toggle-hosts'
    body = {
      pattern: params.value.pattern.trim(),
      enable: opType.value === 'enable_hosts',
      instance_ids: selectedIds.value,
    }
  }

  running.value = true
  try {
    const { data } = await client.post(endpoint, body)
    runResults.value = data.results
    lastRunId.value = data.run_id
    historyLoaded.value = false // força reload do histórico na próxima visita
  } catch (e) {
    runError.value = e?.response?.data?.detail || e?.message || 'Erro ao executar operação'
  } finally {
    running.value = false
  }
}

async function loadHistory() {
  historyLoading.value = true
  historyError.value = ''
  try {
    const { data } = await client.get('/orchestration')
    history.value = data
    historyLoaded.value = true
  } catch (e) {
    historyError.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar histórico'
  } finally {
    historyLoading.value = false
  }
}

async function viewRun(id) {
  try {
    const { data } = await client.get(`/orchestration/${id}`)
    detailRun.value = data
  } catch (e) {
    console.error(e)
  }
}

function resultBadgeClass(status) {
  const map = {
    success: 'badge-online', fixed: 'badge-online', ok: 'badge-online',
    already_exists: 'badge-unknown', no_match: 'badge-unknown',
    error: 'badge-offline', partial: 'badge-warning',
  }
  return map[status] || 'badge-unknown'
}

function resultLabel(status) {
  const map = {
    success: 'Sucesso', fixed: 'Corrigido', ok: 'OK',
    already_exists: 'Já existe', no_match: 'Sem resultado',
    error: 'Erro', partial: 'Parcial',
  }
  return map[status] || status
}

function resultDetail(r) {
  if (r.error) return r.error
  if (r.details?.matched !== undefined) return `${r.details.matched} host(s) afetado(s)`
  if (r.details?.hosts?.length) return r.details.hosts.slice(0, 5).join(', ') + (r.details.hosts.length > 5 ? '...' : '')
  if (r.details?.group_id) return `ID: ${r.details.group_id}`
  if (r.matched !== undefined) return `${r.matched} host(s) afetado(s)`
  return '—'
}

function opTypeLabel(type) {
  const map = {
    CREATE_HOST_GROUP: 'Criar Grupo de Hosts',
    MASS_ENABLE_HOSTS: 'Habilitar Hosts',
    MASS_DISABLE_HOSTS: 'Desabilitar Hosts',
    TEMPLATE_COMPLIANCE_AUDIT: 'Auditoria de Conformidade',
    TEMPLATE_COMPLIANCE_FIX: 'Correção de Conformidade',
  }
  return map[type] || type
}

function runParamSummary(run) {
  const p = run.parameters || {}
  if (p.group_name) return `Grupo: ${p.group_name}`
  if (p.pattern) return `Padrão: ${p.pattern}${p.enable !== undefined ? (p.enable ? ' → habilitar' : ' → desabilitar') : ''}`
  if (p.template_name) return `Template: ${p.template_name}`
  return JSON.stringify(p)
}

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR')
}

onMounted(init)
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 2px solid var(--border);
}

.tab-btn {
  padding: 8px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: -2px;
  transition: color 0.15s;
}

.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--primary, #d40000); border-bottom-color: var(--primary, #d40000); }

/* Run card */
.run-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  max-width: 760px;
}

.form-group { margin-bottom: 16px; }

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
}

.form-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
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

.instance-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.filter-label { font-size: 14px; }

.instance-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
}

.instance-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
}

.instance-actions {
  margin-top: 6px;
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Results */
.results-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Alerts */
.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-error { background: rgba(200,0,0,0.08); border: 1px solid var(--danger); color: var(--danger); }

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

.text-sm { font-size: 12px; }
.text-muted { color: var(--text-muted); }

/* Badges */
.badge { display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 3px; }
.badge-online  { color: var(--success); }
.badge-offline { color: var(--danger); }
.badge-warning { color: var(--warning); }
.badge-unknown { background: var(--bg); border: 1px solid var(--border); }

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
  transition: all 0.2s;
  white-space: nowrap;
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:hover:not(:disabled) { background: var(--bg-hover); }

.btn-primary { background: var(--primary, #d40000); color: #fff; border-color: var(--primary, #d40000); }
.btn-primary:hover:not(:disabled) { opacity: 0.85; background: var(--primary, #d40000); }
.btn-secondary { background: var(--card-bg); }
.btn-sm { padding: 4px 10px; font-size: 13px; }

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
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-lg { max-width: 700px; width: 95%; }

.modal-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
