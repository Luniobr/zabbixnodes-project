<template>
  <div>
    <!-- Breadcrumb -->
    <div class="breadcrumb">
      <router-link to="/hosts" class="breadcrumb-link">Hosts</router-link>
      <span class="breadcrumb-sep">&nbsp;/&nbsp;</span>
      <span>{{ hostName || 'Itens' }}</span>
    </div>

    <!-- Filters -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-field">
          <label class="form-label">Instância</label>
          <select class="form-control" v-model="instanceId" @change="onInstanceChange">
            <option value="">— Selecione —</option>
            <option v-for="inst in instances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
          </select>
        </div>
        <div class="filter-field">
          <label class="form-label">Host</label>
          <select class="form-control" v-model="hostId" :disabled="!instanceId" @change="onHostChange">
            <option value="">— Selecione —</option>
            <option v-for="h in hosts" :key="h.hostid" :value="h.hostid">{{ h.name }}</option>
          </select>
        </div>
        <div class="filter-field filter-field-flex">
          <label class="form-label">Filtrar por nome</label>
          <input
            type="text"
            class="form-control"
            v-model="search"
            placeholder="cpu, memory, ping..."
            @keydown.enter="load"
          />
        </div>
        <button class="btn btn-primary" @click="load" :disabled="!instanceId || !hostId || loading">
          <span v-if="loading" class="spinner"></span>
          Buscar
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <p v-if="!loaded && !loading && !error" class="text-muted text-sm hint">
      Selecione instância e host para ver os itens.
    </p>

    <!-- Items table -->
    <div v-if="loaded" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Chave</th>
            <th style="width: 100px">Tipo Valor</th>
            <th style="width: 80px">Intervalo</th>
            <th style="width: 80px">Unidade</th>
            <th style="width: 130px">Último Valor</th>
            <th style="width: 130px">Última Leitura</th>
            <th style="width: 80px">Status</th>
            <th style="width: 60px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="9" class="table-empty">Carregando...</td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="9" class="table-empty">Nenhum item encontrado</td>
          </tr>
          <tr v-for="item in filtered" :key="item.itemid" :class="{ 'item-error': item.state == '1' }">
            <td>
              <span style="font-size: 13px">{{ item.name }}</span>
              <div v-if="item.error" class="item-error-msg">{{ item.error }}</div>
            </td>
            <td class="text-muted text-sm truncate" style="max-width: 180px">{{ item.key_ }}</td>
            <td class="text-sm text-muted">{{ valueTypeName(item.value_type) }}</td>
            <td class="text-sm text-muted">{{ item.delay || '—' }}</td>
            <td class="text-sm text-muted">{{ item.units || '—' }}</td>
            <td class="text-sm">
              <span v-if="item.lastvalue !== ''">{{ formatValue(item.lastvalue, item.value_type, item.units) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-sm text-muted">{{ fmtClock(item.lastclock) }}</td>
            <td>
              <span class="badge" :class="item.status == '0' ? 'badge-online' : 'badge-inactive'">
                {{ item.status == '0' ? 'Ativo' : 'Inativo' }}
              </span>
            </td>
            <td>
              <button
                v-if="item.status == '0' && item.lastclock"
                class="btn btn-secondary btn-sm btn-icon"
                title="Ver Histórico"
                @click="openHistory(item)"
              >📈</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- History Modal -->
    <Transition name="fade">
      <div v-if="historyItem" class="modal-overlay" @click.self="historyItem = null; history = []">
        <div class="modal modal-xl">
          <div class="modal-title">{{ historyItem.name }}</div>
          <div class="text-muted text-sm" style="margin-bottom: 12px">
            {{ historyItem.key_ }}
            <span v-if="historyItem.units"> · <strong>{{ historyItem.units }}</strong></span>
          </div>

          <div v-if="historyLoading" class="table-empty">Carregando histórico...</div>
          <div v-if="historyError" class="alert alert-error">{{ historyError }}</div>

          <div v-if="!historyLoading" class="history-controls">
            <label class="form-label" style="margin: 0">Registros:</label>
            <select class="form-control" style="width: 100px" v-model="historyLimit" @change="loadHistory">
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
              <option value="500">500</option>
            </select>
            <span class="text-muted text-sm">{{ history.length }} registro(s)</span>
          </div>

          <div v-if="!historyLoading && history.length > 0" class="table-wrapper history-table">
            <table>
              <thead>
                <tr>
                  <th style="width: 160px">Data/Hora</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="h in history" :key="h.clock + h.ns">
                  <td class="text-sm text-muted">{{ fmtClock(h.clock) }}</td>
                  <td class="text-sm">
                    <strong>{{ formatValue(h.value, historyItem.value_type, historyItem.units) }}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div
            v-if="!historyLoading && history.length === 0 && !historyError"
            class="text-muted text-sm"
            style="padding: 12px 0"
          >Nenhum histórico disponível</div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="historyItem = null; history = []">Fechar</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'

const route = useRoute()
const { client } = useApi()

// State
const instances = ref([])
const hosts = ref([])
const items = ref([])
const instanceId = ref('')
const hostId = ref('')
const hostName = ref('')
const search = ref('')
const loading = ref(false)
const loaded = ref(false)
const error = ref('')

// History modal
const historyItem = ref(null)
const history = ref([])
const historyLoading = ref(false)
const historyError = ref('')
const historyLimit = ref('100')

const filtered = computed(() => {
  if (!search.value) return items.value
  const s = search.value.toLowerCase()
  return items.value.filter(i =>
    i.name.toLowerCase().includes(s) || i.key_.toLowerCase().includes(s)
  )
})

async function init() {
  try {
    const { data } = await client.get('/instances')
    instances.value = data.filter(i => i.is_active)

    const instId = route.query.instance_id
    const hId = route.query.host_id
    const hName = route.query.host_name

    if (instId) {
      instanceId.value = instId
      await loadHosts()
      if (hId) {
        hostId.value = hId
        hostName.value = hName || hId
        await load()
      }
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar dados'
  }
}

async function loadHosts() {
  if (!instanceId.value) return
  try {
    const { data } = await client.get(`/instances/${instanceId.value}/hosts`)
    hosts.value = data.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
  } catch (_) {
    hosts.value = []
  }
}

function onInstanceChange() {
  hostId.value = ''
  hostName.value = ''
  items.value = []
  loaded.value = false
  loadHosts()
}

function onHostChange() {
  const h = hosts.value.find(h => h.hostid == hostId.value)
  hostName.value = h ? (h.name || h.host) : ''
  items.value = []
  loaded.value = false
}

async function load() {
  if (!instanceId.value || !hostId.value) return
  loading.value = true
  error.value = ''
  loaded.value = false
  try {
    const params = {}
    if (search.value) params.search = search.value
    const { data } = await client.get(
      `/instances/${instanceId.value}/hosts/${hostId.value}/items`,
      { params }
    )
    items.value = data
    loaded.value = true
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar itens'
  } finally {
    loading.value = false
  }
}

async function openHistory(item) {
  historyItem.value = item
  history.value = []
  historyError.value = ''
  await loadHistory()
}

async function loadHistory() {
  if (!historyItem.value) return
  historyLoading.value = true
  historyError.value = ''
  try {
    const { data } = await client.get(
      `/instances/${instanceId.value}/hosts/${hostId.value}/items/${historyItem.value.itemid}/history`,
      { params: { value_type: historyItem.value.value_type, limit: historyLimit.value } }
    )
    history.value = data
  } catch (e) {
    historyError.value = e?.response?.data?.detail || e?.message
  } finally {
    historyLoading.value = false
  }
}

function valueTypeName(vt) {
  return ['Float', 'String', 'Log', 'Integer', 'Text'][parseInt(vt)] || vt
}

function formatValue(val, vt, units) {
  if (val === '' || val === null || val === undefined) return '—'
  const vti = parseInt(vt)
  if (vti === 0 || vti === 3) {
    const n = parseFloat(val)
    if (isNaN(n)) return val
    if (units === 'B' || units === 'Bps') {
      const abs = Math.abs(n)
      if (abs >= 1073741824) return (n / 1073741824).toFixed(2) + ' G' + units
      if (abs >= 1048576)    return (n / 1048576).toFixed(2) + ' M' + units
      if (abs >= 1024)       return (n / 1024).toFixed(2) + ' K' + units
      return n.toFixed(2) + ' ' + units
    }
    const formatted = Number.isInteger(n) ? n.toString() : n.toFixed(4).replace(/\.?0+$/, '')
    return units ? `${formatted} ${units}` : formatted
  }
  const s = String(val)
  return s.length > 80 ? s.substring(0, 80) + '…' : s
}

function fmtClock(ts) {
  if (!ts || ts === '0') return '—'
  return new Date(parseInt(ts) * 1000).toLocaleString('pt-BR')
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

.breadcrumb-link:hover { color: var(--text); }
.breadcrumb-sep { color: var(--text-muted); }

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

.filter-field { min-width: 180px; }
.filter-field-flex { flex: 1; }

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

.form-control:focus {
  outline: none;
  border-color: var(--primary, #d40000);
}

.form-control:disabled { opacity: 0.5; cursor: not-allowed; }

.hint {
  padding: 16px 0;
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

.table-wrapper {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow-x: auto;
}

.history-table {
  max-height: 360px;
  overflow-y: auto;
  margin-top: 12px;
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

tr.item-error td { background: rgba(239, 68, 68, 0.04); }

.table-empty {
  text-align: center;
  padding: 24px !important;
  color: var(--text-muted);
}

.item-error-msg {
  font-size: 11px;
  color: var(--danger);
  margin-top: 2px;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-sm { font-size: 12px; }
.text-muted { color: var(--text-muted); }

.badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 3px;
}

.badge-online  { color: var(--success); }
.badge-inactive { color: var(--text-muted); }

.history-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
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
  white-space: nowrap;
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
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-xl {
  max-width: 800px;
  width: 95%;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
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
