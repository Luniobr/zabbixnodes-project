<template>
  <div>
    <!-- Header -->
    <div class="header">
      <TitlePage title="Health Score" />
      <button class="btn btn-secondary btn-sm" @click="init" :disabled="loading">
        <span v-if="loading" class="spinner spinner-dark"></span>
        Atualizar
      </button>
    </div>

    <!-- Summary chips -->
    <div v-if="loaded" class="chips-row">
      <span class="hs-chip chip-excellent">{{ counts.excellent }} Excelente</span>
      <span class="hs-chip chip-healthy">{{ counts.healthy }} Saudável</span>
      <span class="hs-chip chip-warning">{{ counts.warning }} Atenção</span>
      <span class="hs-chip chip-critical">{{ counts.critical }} Crítico</span>
      <span class="hs-chip chip-offline">{{ counts.offline }} Offline</span>
    </div>

    <!-- Loading -->
    <div v-if="loading && !loaded" class="loading-state">
      <span class="spinner spinner-dark" style="width: 18px; height: 18px; border-width: 2px"></span>
      Calculando health scores...
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- Table -->
    <div v-if="loaded" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Instância</th>
            <th style="width: 90px">Conexão</th>
            <th style="width: 110px">Status</th>
            <th style="width: 90px; text-align: center">Score</th>
            <th style="width: 130px">Conectividade</th>
            <th style="width: 130px">Problemas</th>
            <th style="width: 110px">Proxies</th>
            <th style="width: 110px">Hosts</th>
            <th style="width: 90px">Versão</th>
            <th style="width: 60px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="10" class="table-empty">Atualizando...</td>
          </tr>
          <tr v-else-if="instances.length === 0">
            <td colspan="10" class="table-empty">Nenhuma instância ativa</td>
          </tr>
          <tr v-for="inst in instances" :key="inst.instance_id">
            <!-- Nome + grupo -->
            <td>
              <div style="font-weight: 500; font-size: 13px">{{ inst.name }}</div>
              <div class="text-muted" style="font-size: 11px">{{ inst.group_name || '—' }}</div>
            </td>

            <!-- Conexão -->
            <td>
              <span class="badge" :class="{
                'badge-online': inst.connection_status === 'online',
                'badge-slow':   inst.connection_status === 'slow',
                'badge-inactive': inst.connection_status === 'offline' || !inst.connection_status
              }">{{ connectionLabel(inst.connection_status) }}</span>
            </td>

            <!-- Status badge -->
            <td>
              <span class="hs-badge" :class="badgeClass(inst.color)">
                {{ inst.label || 'Offline' }}
              </span>
            </td>

            <!-- Score circle -->
            <td style="text-align: center">
              <div class="hs-circle" :class="inst.color || 'health-offline'">
                {{ inst.score !== null && inst.score !== undefined ? inst.score : '—' }}
              </div>
            </td>

            <!-- Conectividade -->
            <td>
              <div v-if="inst.dimensions?.connectivity">
                <div class="hs-mini-bar">
                  <div class="hs-mini-fill" :class="barColor(inst.dimensions.connectivity.score, inst.dimensions.connectivity.max)"
                    :style="`width: ${pct(inst.dimensions.connectivity)}%`"></div>
                </div>
                <div class="text-muted" style="font-size: 11px; margin-top: 2px">
                  {{ inst.latency_ms ? inst.latency_ms + 'ms' : inst.dimensions.connectivity.status }}
                </div>
              </div>
              <span v-else class="text-muted">—</span>
            </td>

            <!-- Problemas -->
            <td>
              <div v-if="inst.dimensions?.problems">
                <div class="hs-mini-bar">
                  <div class="hs-mini-fill" :class="barColor(inst.dimensions.problems.score, inst.dimensions.problems.max)"
                    :style="`width: ${pct(inst.dimensions.problems)}%`"></div>
                </div>
                <div class="text-muted truncate" style="font-size: 11px; margin-top: 2px; max-width: 120px">
                  {{ inst.dimensions.problems.status }}
                </div>
              </div>
              <span v-else class="text-muted">—</span>
            </td>

            <!-- Proxies -->
            <td>
              <div v-if="inst.dimensions?.proxies">
                <div class="hs-mini-bar">
                  <div class="hs-mini-fill" :class="barColor(inst.dimensions.proxies.score, inst.dimensions.proxies.max)"
                    :style="`width: ${pct(inst.dimensions.proxies)}%`"></div>
                </div>
                <div class="text-muted" style="font-size: 11px; margin-top: 2px">{{ inst.dimensions.proxies.status }}</div>
              </div>
              <span v-else class="text-muted">—</span>
            </td>

            <!-- Hosts -->
            <td>
              <div v-if="inst.dimensions?.hosts">
                <div class="hs-mini-bar">
                  <div class="hs-mini-fill" :class="barColor(inst.dimensions.hosts.score, inst.dimensions.hosts.max)"
                    :style="`width: ${pct(inst.dimensions.hosts)}%`"></div>
                </div>
                <div class="text-muted" style="font-size: 11px; margin-top: 2px">{{ inst.dimensions.hosts.status }}</div>
              </div>
              <span v-else class="text-muted">—</span>
            </td>

            <!-- Versão -->
            <td class="text-sm text-muted">{{ inst.zabbix_version ? 'v' + inst.zabbix_version : '—' }}</td>

            <!-- Detalhe -->
            <td>
              <button class="btn btn-secondary btn-sm btn-icon" title="Ver detalhes" @click="detail = inst">🔍</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail modal -->
    <Transition name="fade">
      <div v-if="detail" class="modal-overlay" @click.self="detail = null">
        <div class="modal">
          <div class="modal-title">
            <span>{{ detail.name }}</span>
            <div class="hs-circle" :class="detail.color || 'health-offline'" style="width: 40px; height: 40px; font-size: 14px">
              {{ detail.score ?? '—' }}
            </div>
          </div>
          <div class="text-muted text-sm" style="margin-bottom: 16px">
            {{ detail.group_name || 'Sem grupo' }}
            <span v-if="detail.latency_ms"> · {{ detail.latency_ms }}ms</span>
            <span v-if="detail.zabbix_version"> · v{{ detail.zabbix_version }}</span>
          </div>

          <div v-if="detail.error && !detail.score" class="alert alert-error">{{ detail.error }}</div>

          <div v-if="detail.dimensions && Object.keys(detail.dimensions).length > 0" class="dimensions">
            <div v-for="(dim, key) in detail.dimensions" :key="key" class="dimension-row">
              <div class="dimension-header">
                <span style="font-size: 13px; font-weight: 500">{{ dimLabel(key) }}</span>
                <span style="font-size: 13px; font-weight: 600">{{ dim.score }} / {{ dim.max }}</span>
              </div>
              <div class="hs-mini-bar" style="height: 8px; border-radius: 4px">
                <div class="hs-mini-fill" :class="barColor(dim.score, dim.max)"
                  :style="`width: ${pct(dim)}%; border-radius: 4px`"></div>
              </div>
              <div class="text-muted" style="font-size: 12px; margin-top: 3px">{{ dim.status }}</div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="detail = null">Fechar</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import TitlePage from '@/components/ui/TitlePage.vue'

const { client } = useApi()

const instances = ref([])
const loading = ref(false)
const loaded = ref(false)
const error = ref('')
const detail = ref(null)

const counts = computed(() => ({
  excellent: instances.value.filter(i => i.color === 'health-excellent').length,
  healthy:   instances.value.filter(i => i.color === 'health-healthy').length,
  warning:   instances.value.filter(i => i.color === 'health-warning').length,
  critical:  instances.value.filter(i => i.color === 'health-critical').length,
  offline:   instances.value.filter(i => i.score === null || i.score === undefined).length,
}))

async function init() {
  loading.value = true
  error.value = ''
  loaded.value = false
  try {
    const { data } = await client.get('/health')
    const order = { 'health-critical': 0, 'health-warning': 1, 'health-healthy': 2, 'health-excellent': 3 }
    instances.value = data.sort((a, b) => (order[a.color] ?? 4) - (order[b.color] ?? 4))
    loaded.value = true
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar health scores'
  } finally {
    loading.value = false
  }
}

function connectionLabel(status) {
  return { online: 'Online', slow: 'Lento', offline: 'Offline' }[status] || 'Offline'
}

function pct(dim) {
  return Math.round((dim.score / dim.max) * 100)
}

function badgeClass(color) {
  const map = {
    'health-excellent': 'badge-excellent',
    'health-healthy':   'badge-healthy',
    'health-warning':   'badge-warning',
    'health-critical':  'badge-critical',
  }
  return map[color] || 'badge-offline'
}

function barColor(score, max) {
  const p = score / max
  if (p >= 0.9) return 'bar-excellent'
  if (p >= 0.6) return 'bar-healthy'
  if (p >= 0.3) return 'bar-warning'
  return 'bar-critical'
}

function dimLabel(key) {
  const map = {
    connectivity: 'Conectividade',
    problems:     'Problemas ativos',
    proxies:      'Proxies',
    hosts:        'Hosts monitorados',
    version:      'Versão Zabbix',
  }
  return map[key] || key
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

.chips-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.hs-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.chip-excellent { background: rgba(34, 197, 94, .12);  color: #22c55e; }
.chip-healthy   { background: rgba(59, 130, 246, .12); color: #3b82f6; }
.chip-warning   { background: rgba(245, 158, 11, .12); color: #f59e0b; }
.chip-critical  { background: rgba(239, 68, 68, .12);  color: #ef4444; }
.chip-offline   { background: rgba(107, 114, 128, .12);color: #6b7280; }

.loading-state {
  padding: 32px 0;
  text-align: center;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-error { background: rgba(200,0,0,0.08); border: 1px solid var(--danger); color: var(--danger); }

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

.table-empty { text-align: center; padding: 20px !important; color: var(--text-muted); }
.text-sm { font-size: 12px; }
.text-muted { color: var(--text-muted); }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Connection badge */
.badge { display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 3px; }
.badge-online   { color: var(--success); }
.badge-slow     { background: rgba(245,158,11,.15); color: #f59e0b; }
.badge-inactive { color: var(--text-muted); }
.badge-offline  { color: var(--text-muted); }

/* Health status badge */
.hs-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
}

.badge-excellent { background: rgba(34, 197, 94, .15);  color: #22c55e; }
.badge-healthy   { background: rgba(59, 130, 246, .15); color: #3b82f6; }
.badge-warning   { background: rgba(245, 158, 11, .15); color: #f59e0b; }
.badge-critical  { background: rgba(239, 68, 68, .15);  color: #ef4444; }
.badge-offline-hs { background: rgba(107, 114, 128, .15); color: #6b7280; }

/* Score circle */
.hs-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
}

.health-excellent { background: rgba(34, 197, 94, .15);  color: #22c55e; border: 2px solid #22c55e; }
.health-healthy   { background: rgba(59, 130, 246, .15); color: #3b82f6; border: 2px solid #3b82f6; }
.health-warning   { background: rgba(245, 158, 11, .15); color: #f59e0b; border: 2px solid #f59e0b; }
.health-critical  { background: rgba(239, 68, 68, .15);  color: #ef4444; border: 2px solid #ef4444; }
.health-offline   { background: rgba(107, 114, 128, .15);color: #6b7280; border: 2px solid #6b7280; }

/* Mini bars */
.hs-mini-bar { height: 5px; border-radius: 3px; background: var(--border); overflow: hidden; }
.hs-mini-fill { height: 100%; transition: width 0.3s; }
.bar-excellent { background: #22c55e; }
.bar-healthy   { background: #3b82f6; }
.bar-warning   { background: #f59e0b; }
.bar-critical  { background: #ef4444; }

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
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:hover:not(:disabled) { background: var(--bg-hover); }
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

.spinner-dark {
  border-color: rgba(0,0,0,0.15);
  border-top-color: var(--text-muted);
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
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.dimensions { display: flex; flex-direction: column; gap: 14px; }

.dimension-row { /* each dimension */ }

.dimension-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
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
