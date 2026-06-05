<template>
  <div>
    <div class="header">
      <TitlePage title="Conformidade de Templates" />
    </div>

    <!-- Instance group filter -->
    <div class="filter-card" style="margin-bottom: 16px">
      <div class="filter-row" style="flex-wrap: nowrap">
        <label class="filter-label" style="white-space: nowrap">Grupo de Instâncias:</label>
        <select class="form-control" style="width: 200px" v-model="selectedInstanceGroup" @change="onInstanceGroupChange">
          <option value="">Todos os grupos</option>
          <option v-for="g in instanceGroups" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
      </div>
    </div>

    <!-- Configuration -->
    <div class="config-card">
      <div class="config-grid">
        <div class="form-group" style="margin: 0">
          <label class="form-label">Instância de referência *</label>
          <select class="form-control" v-model="refInstance" @change="loadRefTemplates">
            <option value="">— Selecione —</option>
            <option v-for="inst in filteredInstances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
          </select>
        </div>
        <div class="form-group" style="margin: 0">
          <label class="form-label">Template de referência *</label>
          <select class="form-control" v-model="refTemplate" :disabled="!refInstance || loadingTemplates">
            <option value="">— Selecione —</option>
            <option v-for="t in refTemplates" :key="t.templateid" :value="t.name">{{ t.name }}</option>
          </select>
          <div v-if="loadingTemplates" class="text-muted text-sm" style="margin-top: 4px">Carregando templates...</div>
        </div>
      </div>

      <div class="form-group" style="margin-top: 16px; margin-bottom: 0">
        <label class="form-label">Instâncias alvo</label>
        <div class="targets-box">
          <label class="target-label">
            <input type="checkbox" v-model="selectAll" @change="toggleAll" />
            <span class="text-sm">Todas</span>
          </label>
          <label v-for="inst in targetInstances" :key="inst.id" class="target-label">
            <input
              type="checkbox"
              :checked="selectedTargets.includes(inst.id)"
              @change="toggleTarget(inst.id)"
            />
            <span class="text-sm">{{ inst.name }}</span>
          </label>
        </div>
      </div>

      <div class="config-actions">
        <button class="btn btn-primary" @click="analyze" :disabled="!canAnalyze || analyzing">
          <span v-if="analyzing" class="spinner"></span>
          <span v-else>🔍 Analisar</span>
        </button>
        <span v-if="analyzing" class="text-muted text-sm">Consultando instâncias em paralelo...</span>
      </div>
      <div v-if="analyzeError" class="alert alert-error" style="margin-top: 12px">{{ analyzeError }}</div>
    </div>

    <!-- Results -->
    <div v-if="results.length > 0">
      <div class="results-header">
        <div class="results-summary">
          <span class="badge badge-online">✅ Conforme: {{ countByStatus('ok') }}</span>
          <span class="badge badge-unknown">⚠️ Divergente: {{ countByStatus('divergent') }}</span>
          <span class="badge badge-offline">❌ Ausente: {{ countByStatus('absent') }}</span>
          <span v-if="countByStatus('error') > 0" class="badge badge-offline">🔴 Erro: {{ countByStatus('error') }}</span>
        </div>
        <button
          v-if="hasFixable && isSuperadmin"
          class="btn btn-primary btn-sm"
          @click="fixSelected"
          :disabled="fixing || fixTargets.length === 0"
        >
          <span v-if="fixing" class="spinner"></span>
          <span v-else>🔧 Corrigir selecionadas ({{ fixTargets.length }})</span>
        </button>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th v-if="hasFixable && isSuperadmin" style="width: 36px"></th>
              <th>Instância</th>
              <th>Status</th>
              <th>Itens (referência)</th>
              <th>Itens (atual)</th>
              <th>Divergência</th>
              <th style="width: 120px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in results" :key="r.instance_id">
              <td v-if="hasFixable && isSuperadmin">
                <input
                  v-if="r.status === 'absent' || r.status === 'divergent'"
                  type="checkbox"
                  :checked="fixTargets.includes(r.instance_id)"
                  @change="toggleFixTarget(r.instance_id)"
                />
              </td>
              <td><strong>{{ r.instance_name }}</strong></td>
              <td>
                <span class="badge" :class="{
                  'badge-online': r.status === 'ok',
                  'badge-unknown': r.status === 'divergent',
                  'badge-offline': r.status === 'absent' || r.status === 'error'
                }">{{ statusLabel(r.status) }}</span>
              </td>
              <td class="text-sm">{{ r.reference_items ?? '—' }}</td>
              <td class="text-sm">{{ r.actual_items ?? '—' }}</td>
              <td class="text-sm">
                <span v-if="r.status === 'divergent'" class="text-muted">
                  {{ r.actual_items - r.reference_items > 0 ? '+' : '' }}{{ r.actual_items - r.reference_items }} itens
                </span>
                <span v-else-if="r.status === 'error'" class="text-muted">{{ r.error || 'Erro de conexão' }}</span>
                <span v-else>—</span>
              </td>
              <td>
                <button
                  v-if="r.status === 'divergent' || r.status === 'absent'"
                  class="btn btn-sm"
                  style="font-size: 12px"
                  @click="openDiff(r)"
                  :disabled="loadingDiff"
                >🔎 Ver itens</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Fix results -->
      <div v-if="fixResult.length > 0" style="margin-top: 16px">
        <div class="form-label" style="margin-bottom: 8px">Resultado da correção:</div>
        <div v-for="r in fixResult" :key="r.instance_id" class="fix-result-row">
          <strong>{{ r.instance_name }}</strong>:
          <span :class="r.status === 'fixed' ? 'badge badge-online' : r.status === 'partial' ? 'badge badge-unknown' : 'badge badge-offline'">
            <span v-if="r.status === 'fixed'">✅ Corrigido ({{ r.created }} itens criados)</span>
            <span v-else-if="r.status === 'partial'">⚠️ Parcial ({{ r.created }} criados, {{ r.failed }} falhas)</span>
            <span v-else-if="r.status === 'ok'">✅ Já estava conforme</span>
            <span v-else>❌ {{ r.error }}</span>
          </span>
          <div v-if="r.details?.some(d => !d.created)" style="margin-top: 4px; padding-left: 12px">
            <div v-for="d in r.details.filter(d => !d.created)" :key="d.key_" class="text-sm text-muted">
              ⚠️ {{ d.name }}: {{ d.error }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Diff Modal -->
    <Transition name="fade">
      <div v-if="diffModal" class="fullscreen-overlay" @click.self="closeDiff">
        <div class="fullscreen-panel">

          <!-- Header -->
          <div class="panel-header">
            <div>
              <div class="panel-title">{{ diffData ? `Itens: ${diffData.template_name}` : 'Carregando...' }}</div>
              <div v-if="diffData" class="text-sm text-muted" style="margin-top: 4px">
                {{ diffData.reference_instance }} (referência: {{ diffData.ref_total }} itens)
                vs
                {{ diffData.target_instance }} (atual: {{ diffData.target_total }} itens)
                —
                <span v-if="(diffData.absent ?? 0) > 0" style="color: var(--danger)"><strong>{{ diffData.absent }}</strong> ausentes</span>
                <span v-if="(diffData.absent ?? 0) > 0 && (diffData.extra ?? 0) > 0"> · </span>
                <span v-if="(diffData.extra ?? 0) > 0" style="color: var(--warning)"><strong>{{ diffData.extra }}</strong> extras</span>
                <span v-if="(diffData.ok ?? 0) > 0"> · <strong>{{ diffData.ok }}</strong> conformes</span>
              </div>
            </div>
            <button class="btn btn-sm" @click="closeDiff" style="flex-shrink: 0; margin-left: 16px">✕ Fechar</button>
          </div>

          <!-- Loading -->
          <div v-if="loadingDiff" class="table-empty" style="padding: 40px">Carregando itens...</div>

          <!-- Filter bar -->
          <div v-if="!loadingDiff && diffData" class="diff-filter-bar">
            <span class="text-sm text-muted" style="font-weight: 500">Filtrar:</span>
            <label class="diff-filter-label">
              <input type="checkbox" v-model="diffFilter.absent" />
              <span class="text-sm" style="color: var(--danger)">❌ Ausentes ({{ diffData.absent ?? 0 }})</span>
            </label>
            <label class="diff-filter-label">
              <input type="checkbox" v-model="diffFilter.extra" />
              <span class="text-sm" style="color: var(--warning)">➕ Extras ({{ diffData.extra ?? 0 }})</span>
            </label>
            <label class="diff-filter-label">
              <input type="checkbox" v-model="diffFilter.ok" />
              <span class="text-sm" style="color: var(--success)">✅ Conformes ({{ diffData.ok ?? 0 }})</span>
            </label>
            <span class="text-muted text-sm" style="margin-left: auto">Clique em uma linha para ver detalhes</span>
          </div>

          <!-- Item table -->
          <div v-if="!loadingDiff && diffData" class="panel-body">
            <table>
              <thead>
                <tr class="sticky-header">
                  <th style="width: 90px">Status</th>
                  <th>Nome</th>
                  <th>Chave</th>
                  <th style="width: 110px">Tipo</th>
                  <th style="width: 80px">Intervalo</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="item in filteredDiffItems" :key="item.key_">
                  <tr class="item-row" :class="{ 'item-expanded': expandedKey === item.key_ }" @click="toggleItemExpand(item.key_)">
                    <td>
                      <span v-if="item.status === 'absent'" class="badge badge-offline" style="font-size: 11px">❌ Ausente</span>
                      <span v-else-if="item.status === 'extra'" class="badge badge-unknown" style="font-size: 11px">➕ Extra</span>
                      <span v-else class="badge badge-online" style="font-size: 11px">✅ Ok</span>
                    </td>
                    <td style="font-size: 13px">{{ item.name }}</td>
                    <td style="font-size: 11px; font-family: monospace; color: var(--text-muted)">{{ item.key_ }}</td>
                    <td style="font-size: 12px; color: var(--text-muted)">{{ itemTypeName(item.type) }}</td>
                    <td style="font-size: 12px; color: var(--text-muted)">{{ (item.ref_item || item.target_item)?.delay || '—' }}</td>
                  </tr>
                  <tr v-if="expandedKey === item.key_" class="expand-row">
                    <td colspan="5" style="padding: 0">
                      <div class="expand-body">
                        <!-- Side-by-side for ok items -->
                        <div v-if="item.status === 'ok'" class="side-by-side">
                          <div>
                            <div class="expand-section-title">Referência ({{ diffData.reference_instance }})</div>
                            <div v-html="renderItemDetails(item.ref_item)"></div>
                          </div>
                          <div>
                            <div class="expand-section-title">Atual ({{ diffData.target_instance }})</div>
                            <div v-html="renderItemDetails(item.target_item)"></div>
                          </div>
                        </div>
                        <!-- Single column for absent/extra -->
                        <div v-else>
                          <div class="expand-section-title">
                            <span v-if="item.status === 'absent'">Item na referência ({{ diffData.reference_instance }}) — ausente no alvo</span>
                            <span v-else>Item extra no alvo ({{ diffData.target_instance }}) — não existe na referência</span>
                          </div>
                          <div v-html="renderItemDetails(item.ref_item || item.target_item)"></div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <!-- Footer fix button -->
          <div v-if="!loadingDiff && diffData && (diffData.absent ?? 0) > 0 && isSuperadmin" class="panel-footer">
            <button class="btn btn-primary" @click="fixFromDiff" :disabled="fixing">
              <span v-if="fixing" class="spinner"></span>
              <span v-else>🔧 Sincronizar {{ diffData.absent }} itens ausentes</span>
            </button>
            <span class="text-sm text-muted">Cria os itens ausentes no alvo com as mesmas propriedades da referência.</span>
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

const isSuperadmin = computed(() => authStore.role === 'superadmin')

// State
const instanceGroups = ref([])
const instances = ref([])
const selectedInstanceGroup = ref('')

const refInstance = ref('')
const refTemplate = ref('')
const refTemplates = ref([])
const loadingTemplates = ref(false)
const selectedTargets = ref([])
const selectAll = ref(true)

const analyzing = ref(false)
const analyzeError = ref('')
const results = ref([])
const fixTargets = ref([])
const fixing = ref(false)
const fixResult = ref([])

// Diff modal
const diffModal = ref(false)
const loadingDiff = ref(false)
const diffData = ref(null)
const diffInstance = ref(null)
const diffFilter = reactive({ absent: true, extra: true, ok: false })
const expandedKey = ref(null)

const filteredInstances = computed(() => {
  if (!selectedInstanceGroup.value) return instances.value
  return instances.value.filter(i => String(i.group?.id) === String(selectedInstanceGroup.value))
})

const targetInstances = computed(() =>
  filteredInstances.value.filter(i => String(i.id) !== String(refInstance.value))
)

const canAnalyze = computed(() =>
  refInstance.value && refTemplate.value && selectedTargets.value.length > 0
)

const hasFixable = computed(() =>
  results.value.some(r => r.status === 'absent' || r.status === 'divergent')
)

const filteredDiffItems = computed(() => {
  if (!diffData.value) return []
  return diffData.value.items.filter(item => {
    if (item.status === 'absent') return diffFilter.absent
    if (item.status === 'extra') return diffFilter.extra
    if (item.status === 'ok') return diffFilter.ok
    return true
  })
})

async function init() {
  try {
    const [instancesRes, groupsRes] = await Promise.all([
      client.get('/instances'),
      client.get('/instance-groups'),
    ])
    instances.value = instancesRes.data
    instanceGroups.value = groupsRes.data
    selectedTargets.value = instancesRes.data.map(i => i.id)
  } catch (e) {
    console.error(e)
  }
}

function onInstanceGroupChange() {
  refInstance.value = ''
  refTemplates.value = []
  refTemplate.value = ''
  selectedTargets.value = []
  results.value = []
}

function toggleAll() {
  selectedTargets.value = selectAll.value ? targetInstances.value.map(i => i.id) : []
}

function toggleTarget(id) {
  const idx = selectedTargets.value.indexOf(id)
  if (idx === -1) selectedTargets.value.push(id)
  else selectedTargets.value.splice(idx, 1)
  selectAll.value = selectedTargets.value.length === targetInstances.value.length
}

async function loadRefTemplates() {
  if (!refInstance.value) { refTemplates.value = []; return }
  loadingTemplates.value = true
  refTemplate.value = ''
  selectedTargets.value = targetInstances.value.map(i => i.id)
  try {
    const { data } = await client.get(`/instances/${refInstance.value}/templates`)
    refTemplates.value = data
  } catch (_) {}
  finally { loadingTemplates.value = false }
}

async function analyze() {
  analyzing.value = true
  analyzeError.value = ''
  results.value = []
  fixTargets.value = []
  try {
    const { data } = await client.post('/compliance/analyze', {
      reference_instance_id: parseInt(refInstance.value),
      template_name: refTemplate.value,
      instance_ids: selectedTargets.value,
    })
    results.value = data.results
    fixTargets.value = data.results
      .filter(r => r.status === 'absent' || r.status === 'divergent')
      .map(r => r.instance_id)
  } catch (e) {
    analyzeError.value = e?.response?.data?.detail || e?.message || 'Erro ao analisar'
  } finally {
    analyzing.value = false
  }
}

function toggleFixTarget(id) {
  const idx = fixTargets.value.indexOf(id)
  if (idx === -1) fixTargets.value.push(id)
  else fixTargets.value.splice(idx, 1)
}

async function fixSelected() {
  fixing.value = true
  fixResult.value = []
  try {
    const { data } = await client.post('/compliance/fix', {
      reference_instance_id: parseInt(refInstance.value),
      template_name: refTemplate.value,
      instance_ids: fixTargets.value,
    })
    const savedFixResult = data.results
    await analyze()
    fixResult.value = savedFixResult
  } catch (e) {
    console.error(e)
  } finally {
    fixing.value = false
  }
}

async function openDiff(r) {
  diffInstance.value = r
  diffModal.value = true
  diffData.value = null
  loadingDiff.value = true
  expandedKey.value = null
  diffFilter.absent = true
  diffFilter.extra = true
  diffFilter.ok = false
  try {
    const { data } = await client.post('/compliance/diff', {
      reference_instance_id: parseInt(refInstance.value),
      template_name: refTemplate.value,
      target_instance_id: r.instance_id,
    })
    diffData.value = data
    if (!data.absent && !data.extra) diffFilter.ok = true
  } catch (e) {
    console.error(e)
    diffModal.value = false
  } finally {
    loadingDiff.value = false
  }
}

function closeDiff() {
  diffModal.value = false
  diffData.value = null
  diffInstance.value = null
  expandedKey.value = null
}

function toggleItemExpand(key_) {
  expandedKey.value = expandedKey.value === key_ ? null : key_
}

async function fixFromDiff() {
  if (!diffInstance.value) return
  fixing.value = true
  try {
    const { data } = await client.post('/compliance/fix', {
      reference_instance_id: parseInt(refInstance.value),
      template_name: refTemplate.value,
      instance_ids: [diffInstance.value.instance_id],
    })
    const savedFixResult = data.results
    closeDiff()
    await analyze()
    fixResult.value = savedFixResult
  } catch (e) {
    console.error(e)
  } finally {
    fixing.value = false
  }
}

function countByStatus(s) {
  return results.value.filter(r => r.status === s).length
}

function statusLabel(s) {
  return { ok: '✅ Conforme', divergent: '⚠️ Divergente', absent: '❌ Ausente', error: '🔴 Erro' }[s] || s
}

function itemTypeName(t) {
  const map = {
    '0': 'Agente Zabbix', '2': 'Trapper', '3': 'Verificação simples', '5': 'Interno Zabbix',
    '7': 'Agente Zabbix (ativo)', '10': 'Verificação externa', '11': 'Monitor de BD',
    '12': 'Agente IPMI', '13': 'Agente SSH', '14': 'Agente Telnet', '15': 'Calculado',
    '16': 'Agente JMX', '17': 'SNMP trap', '18': 'Item dependente', '19': 'Agente HTTP',
    '20': 'Agente SNMP', '21': 'Script',
  }
  return map[String(t)] || `Tipo ${t}`
}

function valueTypeName(v) {
  const map = {
    '0': 'Numérico (float)', '1': 'Caractere', '2': 'Log',
    '3': 'Numérico (inteiro)', '4': 'Texto',
  }
  return map[String(v)] || `Tipo ${v}`
}

function preprocessingTypeName(t) {
  const map = {
    '1': 'Multiplicador customizado', '2': 'Trim direita', '3': 'Trim esquerda', '4': 'Trim',
    '5': 'Regex', '6': 'Booleano para decimal', '7': 'Octal para decimal', '8': 'Hex para decimal',
    '9': 'Simple change', '10': 'Mudança por tempo', '11': 'In range', '12': 'Corresponde ao regex',
    '13': 'Não corresponde ao regex', '14': 'Erro em JSON', '15': 'Erro em XML',
    '16': 'Erro via regex', '17': 'Descarta valores iguais', '18': 'Descarta valores iguais (HB)',
    '19': 'JSONPath', '20': 'XML XPath', '21': 'Renomear', '22': 'Prometheus pattern',
    '23': 'Prometheus para JSON', '24': 'CSV para JSON', '25': 'Substituir',
    '26': 'Verifica valor não suportado', '27': 'JavaScript', '28': 'XML para JSON',
  }
  return map[String(t)] || `Tipo ${t}`
}

function _esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderItemDetails(item) {
  if (!item) return '<span class="text-muted text-sm">—</span>'

  const rows = []
  const field = (label, value) => {
    if (value === null || value === undefined || value === '') return
    rows.push(`<tr>
      <td style="padding:4px 12px 4px 0;font-size:12px;color:var(--text-muted);white-space:nowrap;vertical-align:top;width:160px">${label}</td>
      <td style="padding:4px 0;font-size:13px;word-break:break-word">${_esc(String(value))}</td>
    </tr>`)
  }

  field('Nome', item.name)
  field('Chave', item.key_)
  field('Tipo', itemTypeName(item.type))
  field('Tipo de informação', valueTypeName(item.value_type))
  field('Unidades', item.units)
  field('Intervalo', item.delay)
  field('Histórico', item.history)
  field('Tendências', item.trends)
  if (item.snmp_oid) field('OID SNMP', item.snmp_oid)
  if (item.params) field('Parâmetros / Fórmula', item.params)
  if (item.ipmi_sensor) field('Sensor IPMI', item.ipmi_sensor)
  if (item.jmx_endpoint) field('JMX Endpoint', item.jmx_endpoint)
  if (item.username) field('Usuário', item.username)
  if (item.url) field('URL', item.url)
  if (item.trapper_hosts) field('Hosts trapper', item.trapper_hosts)
  if (item.timeout && item.timeout !== '3s') field('Timeout', item.timeout)
  field('Status', item.status === '1' ? '🔴 Desabilitado' : '🟢 Habilitado')
  field('Descrição', item.description)

  let html = `<table style="border-collapse:collapse;width:100%">${rows.join('')}</table>`

  const tags = item.tags
  if (tags?.length > 0) {
    const tagHtml = tags.map(t =>
      `<span style="display:inline-block;padding:2px 8px;background:var(--bg);border:1px solid var(--border);border-radius:10px;font-size:11px;margin:2px">${_esc(t.tag)}${t.value ? ': ' + _esc(t.value) : ''}</span>`
    ).join('')
    html += `<div style="margin-top:10px"><div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);margin-bottom:6px">Tags (${tags.length})</div><div>${tagHtml}</div></div>`
  }

  const prep = item.preprocessing
  if (prep?.length > 0) {
    const prepRows = prep.map((p, i) => {
      const name = preprocessingTypeName(p.type)
      const params = p.params ? `<code style="font-size:11px;background:var(--bg);padding:1px 4px;border-radius:3px">${_esc(p.params)}</code>` : ''
      return `<div style="padding:3px 0;font-size:12px"><span style="color:var(--text-muted)">${i + 1}.</span> <strong>${name}</strong>${params ? ' → ' + params : ''}</div>`
    }).join('')
    html += `<div style="margin-top:10px"><div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);margin-bottom:6px">Preprocessing (${prep.length})</div>${prepRows}</div>`
  }

  return html
}

onMounted(init)
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.filter-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 20px;
}

.filter-row { display: flex; align-items: center; gap: 12px; }
.filter-label { font-size: 14px; white-space: nowrap; }

.config-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group { margin-bottom: 16px; }

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

.targets-box {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  min-height: 40px;
}

.target-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg);
}

.config-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-error { background: rgba(200,0,0,0.08); border: 1px solid var(--danger); color: var(--danger); }

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.results-summary {
  display: flex;
  gap: 16px;
  font-size: 14px;
  flex-wrap: wrap;
}

.fix-result-row {
  padding: 6px 0;
  font-size: 13px;
  border-bottom: 1px solid var(--border);
}

.table-wrapper {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 16px;
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

.badge { display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 3px; }
.badge-online  { color: var(--success); }
.badge-offline { color: var(--danger); }
.badge-unknown { background: var(--bg); border: 1px solid var(--border); }

/* Fullscreen diff modal */
.fullscreen-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 200;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 48px 16px 24px;
  overflow-y: auto;
}

.fullscreen-panel {
  background: var(--card-bg);
  border-radius: 8px;
  width: 100%;
  max-width: 1000px;
  max-height: calc(100vh - 72px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 16px;
}

.panel-title { font-weight: 600; font-size: 16px; }

.panel-body { overflow-y: auto; flex: 1; }

.panel-footer {
  padding: 14px 24px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

.diff-filter-bar {
  padding: 10px 24px;
  border-bottom: 1px solid var(--border);
  display: flex;
  gap: 16px;
  align-items: center;
  flex-shrink: 0;
  background: var(--bg);
  flex-wrap: wrap;
}

.diff-filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.sticky-header {
  position: sticky;
  top: 0;
  background: var(--card-bg);
  z-index: 1;
}

.item-row { border-bottom: 1px solid var(--border); cursor: pointer; }
.item-row:hover td { background: var(--bg-hover); }
.item-expanded td { background: var(--bg-hover); }

.expand-row { border-bottom: 2px solid var(--border); }

.expand-body {
  padding: 16px 24px;
  background: var(--bg);
}

.side-by-side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.expand-section-title {
  font-weight: 600;
  font-size: 12px;
  margin-bottom: 8px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

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

.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
