<template>
  <div>
    <!-- Header -->
    <div class="header">
      <TitlePage title="Templates" />
      <button
        class="btn btn-primary btn-sm"
        @click="openCreate"
        :disabled="!selectedInstance || !canWrite"
      >
        + Novo Template
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
        <select class="form-control filter-select" v-model="selectedInstance" @change="loadTemplates">
          <option value="">— Selecione —</option>
          <option v-for="inst in filteredInstances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
        </select>
      </template>

      <input
        v-if="selectedInstance"
        type="text"
        class="form-control filter-search"
        v-model="search"
        placeholder="Pesquisar template..."
      />
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <Transition name="fade">
      <div v-if="toast.visible" class="alert" :class="`alert-${toast.type}`">{{ toast.message }}</div>
    </Transition>

    <!-- Table -->
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th style="width: 110px; text-align: center">Hosts</th>
            <th style="width: 110px; text-align: center">Itens</th>
            <th style="width: 200px">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!selectedInstanceGroup">
            <td colspan="4" class="table-empty">Selecione um grupo de instâncias para começar</td>
          </tr>
          <tr v-else-if="!selectedInstance">
            <td colspan="4" class="table-empty">Selecione uma instância</td>
          </tr>
          <tr v-else-if="loading">
            <td colspan="4" class="table-empty">Carregando...</td>
          </tr>
          <tr v-else-if="filteredTemplates.length === 0">
            <td colspan="4" class="table-empty">Nenhum template encontrado</td>
          </tr>
          <tr v-for="t in filteredTemplates" :key="t.templateid">
            <td>
              <strong>{{ t.name }}</strong>
              <div v-if="t.description" class="text-sm text-muted" style="margin-top: 2px">{{ t.description }}</div>
            </td>
            <td style="text-align: center">
              <span class="badge badge-unknown">{{ t.hosts_count }}</span>
            </td>
            <td style="text-align: center">
              <span class="text-sm text-muted">{{ t.items_count }}</span>
            </td>
            <td>
              <div class="actions">
                <button v-if="canWrite" class="btn btn-secondary btn-sm btn-icon" title="Editar" @click="openEdit(t)">✏️</button>
                <button class="btn btn-secondary btn-sm" title="Ver itens" @click="openItems(t)">📋 Itens</button>
                <button class="btn btn-secondary btn-sm" title="Hosts vinculados" @click="openDetail(t)">🔗 Hosts</button>
                <button v-if="canWrite" class="btn btn-danger btn-sm btn-icon" title="Deletar" @click="confirmDelete(t)">🗑</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <Transition name="fade">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false; createError = ''">
        <div class="modal modal-md">
          <div class="modal-title">Novo Template</div>
          <div v-if="createError" class="alert alert-error">{{ createError }}</div>

          <div class="form-group">
            <label class="form-label">Nome técnico (host) *</label>
            <input type="text" class="form-control" v-model="newTemplate.host" placeholder="Template Linux by Zabbix agent" />
            <div class="form-hint">Identificador interno do template no Zabbix</div>
          </div>
          <div class="form-group">
            <label class="form-label">Nome visível</label>
            <input type="text" class="form-control" v-model="newTemplate.name" placeholder="Igual ao nome técnico se vazio" />
          </div>
          <div class="form-group">
            <label class="form-label">Descrição</label>
            <textarea class="form-control" rows="3" v-model="newTemplate.description" placeholder="Descrição opcional"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Grupos de Templates *</label>
            <div v-if="loadingGroups" class="text-muted text-sm">Carregando grupos...</div>
            <div v-else class="checklist">
              <label v-for="g in templateGroups" :key="g.groupid" class="checklist-item">
                <input
                  type="checkbox"
                  :checked="newTemplate.group_ids.includes(g.groupid)"
                  @change="toggleGroup(newTemplate.group_ids, g.groupid)"
                />
                <span class="text-sm">{{ g.name }}</span>
              </label>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showCreateModal = false; createError = ''">Cancelar</button>
            <button class="btn btn-primary" @click="doCreate" :disabled="creating">
              <span v-if="creating" class="spinner"></span>
              Criar Template
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit Modal -->
    <Transition name="fade">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false; editError = ''">
        <div class="modal modal-md">
          <div class="modal-title">Editar Template — {{ editTemplate?.host }}</div>
          <div v-if="editError" class="alert alert-error">{{ editError }}</div>

          <div class="form-group">
            <label class="form-label">Nome visível</label>
            <input type="text" class="form-control" v-model="editForm.name" />
          </div>
          <div class="form-group">
            <label class="form-label">Descrição</label>
            <textarea class="form-control" rows="3" v-model="editForm.description"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Grupos de Templates</label>
            <div v-if="loadingGroups" class="text-muted text-sm">Carregando grupos...</div>
            <div v-else class="checklist">
              <label v-for="g in templateGroups" :key="g.groupid" class="checklist-item">
                <input
                  type="checkbox"
                  :checked="editForm.group_ids.includes(g.groupid)"
                  @change="toggleGroup(editForm.group_ids, g.groupid)"
                />
                <span class="text-sm">{{ g.name }}</span>
              </label>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false; editError = ''">Cancelar</button>
            <button class="btn btn-primary" @click="doEdit" :disabled="saving">
              <span v-if="saving" class="spinner"></span>
              Salvar
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Items Modal -->
    <Transition name="fade">
      <div v-if="itemsModal" class="fullscreen-overlay" @click.self="closeItems">
        <div class="fullscreen-panel">
          <div class="panel-header">
            <div>
              <div class="panel-title">{{ itemsTemplate?.name }}</div>
              <div class="text-sm text-muted" style="margin-top: 4px">{{ templateItems.length }} item(s)</div>
            </div>
            <div class="panel-header-actions">
              <input
                type="text"
                class="form-control"
                style="width: 220px; padding: 4px 10px; font-size: 13px"
                placeholder="Filtrar itens..."
                v-model="itemsSearch"
              />
              <button class="btn btn-sm" @click="closeItems">✕ Fechar</button>
            </div>
          </div>

          <div v-if="loadingItems" class="table-empty" style="padding: 40px">
            <span class="spinner spinner-dark"></span> Carregando itens...
          </div>

          <div v-else class="panel-body">
            <table>
              <thead>
                <tr class="sticky-header">
                  <th>Nome</th>
                  <th style="width: 200px">Descrição</th>
                  <th style="width: 150px">Tipo</th>
                  <th>Chave e informações adicionais</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredItems.length === 0">
                  <td colspan="4" class="table-empty">Nenhum item encontrado</td>
                </tr>
                <tr
                  v-for="item in filteredItems"
                  :key="item.itemid"
                  class="item-row"
                  :class="{ 'item-expanded': expandedItem === item.itemid }"
                  @click="expandedItem = expandedItem === item.itemid ? null : item.itemid"
                >
                  <td style="font-size: 13px; font-weight: 500">{{ item.name }}</td>
                  <td class="text-sm text-muted cell-clamp">{{ item.description || '—' }}</td>
                  <td class="text-sm text-muted">{{ itemTypeName(item.type) }}</td>
                  <td>
                    <code class="key-code">{{ item.key_ }}</code>
                    <div v-if="item.preprocessing?.length > 0" style="margin-top: 4px">
                      <div
                        v-for="(p, i) in item.preprocessing.slice(0, expandedItem === item.itemid ? 999 : 2)"
                        :key="i"
                        class="text-sm text-muted preprocessing-row"
                      >
                        <span style="opacity: 0.6">{{ i + 1 }}.</span>
                        {{ preprocessingTypeName(p.type) }}
                        <code v-if="p.params" class="preproc-code">
                          {{ p.params.length > 40 ? p.params.slice(0, 40) + '…' : p.params }}
                        </code>
                      </div>
                      <div
                        v-if="expandedItem !== item.itemid && item.preprocessing.length > 2"
                        class="text-sm text-muted"
                        style="opacity: 0.7"
                      >+ {{ item.preprocessing.length - 2 }} mais...</div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Detail Modal (hosts vinculados) -->
    <Transition name="fade">
      <div v-if="detailModal" class="fullscreen-overlay" @click.self="closeDetail">
        <div class="fullscreen-panel" style="max-width: 700px">
          <div class="panel-header">
            <div>
              <div class="panel-title">{{ detailTemplate?.name }}</div>
              <div class="text-sm text-muted" style="margin-top: 4px">{{ detailHosts.length }} host(s) vinculado(s)</div>
            </div>
            <button class="btn btn-sm" @click="closeDetail">✕ Fechar</button>
          </div>

          <div v-if="loadingDetail" class="table-empty" style="padding: 40px">
            Carregando...
          </div>

          <div v-else>
            <div v-if="canWrite" class="link-bar">
              <select class="form-control" style="max-width: 300px" v-model="linkHostId">
                <option value="">— Vincular a um host —</option>
                <option v-for="h in availableHosts" :key="h.hostid" :value="h.hostid">{{ h.host }}</option>
              </select>
              <button class="btn btn-primary btn-sm" @click="linkHost" :disabled="!linkHostId || linking">
                <span v-if="linking" class="spinner"></span>
                <span v-else>+ Vincular</span>
              </button>
            </div>

            <div v-if="detailHosts.length === 0" class="table-empty">
              Nenhum host vinculado a este template
            </div>

            <table v-else>
              <thead>
                <tr>
                  <th>Host</th>
                  <th>Status</th>
                  <th v-if="canWrite" style="width: 80px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="h in detailHosts" :key="h.hostid">
                  <td style="font-size: 13px">{{ h.host }}</td>
                  <td>
                    <span class="badge" :class="h.status == '0' ? 'badge-online' : 'badge-offline'">
                      {{ h.status == '0' ? 'Habilitado' : 'Desabilitado' }}
                    </span>
                  </td>
                  <td v-if="canWrite" style="text-align: center">
                    <button
                      class="btn btn-danger btn-sm btn-icon"
                      title="Desvincular"
                      @click="unlinkHost(h)"
                      :disabled="unlinking === h.hostid"
                    >
                      <span v-if="unlinking === h.hostid" class="spinner"></span>
                      <span v-else>✕</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete Modal -->
    <Transition name="fade">
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="modal">
          <div class="modal-title">Confirmar exclusão</div>
          <p>Excluir o template <strong>{{ deleteTarget.name }}</strong>?</p>
          <p class="text-muted text-sm" style="margin-top: 8px">
            Esta ação remove o template e todos os seus itens da instância Zabbix. Hosts vinculados perderão o vínculo.
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
const templates = ref([])
const search = ref('')
const loading = ref(false)
const error = ref('')
const canWrite = ref(false)

// Template groups (lazy)
const templateGroups = ref([])
const loadingGroups = ref(false)

// Create modal
const showCreateModal = ref(false)
const newTemplate = ref({ host: '', name: '', description: '', group_ids: [] })
const creating = ref(false)
const createError = ref('')

// Edit modal
const showEditModal = ref(false)
const editTemplate = ref(null)
const editForm = ref({ name: '', description: '', group_ids: [] })
const saving = ref(false)
const editError = ref('')

// Items modal
const itemsModal = ref(false)
const itemsTemplate = ref(null)
const templateItems = ref([])
const loadingItems = ref(false)
const itemsSearch = ref('')
const expandedItem = ref(null)

// Detail modal (hosts)
const detailModal = ref(false)
const detailTemplate = ref(null)
const detailHosts = ref([])
const loadingDetail = ref(false)
const allHosts = ref([])
const linkHostId = ref('')
const linking = ref(false)
const unlinking = ref(null)

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

const filteredTemplates = computed(() => {
  if (!search.value) return templates.value
  const q = search.value.toLowerCase()
  return templates.value.filter(t => t.name.toLowerCase().includes(q))
})

const filteredItems = computed(() => {
  if (!itemsSearch.value) return templateItems.value
  const q = itemsSearch.value.toLowerCase()
  return templateItems.value.filter(i =>
    i.name.toLowerCase().includes(q) || i.key_.toLowerCase().includes(q)
  )
})

const availableHosts = computed(() => {
  const linked = new Set(detailHosts.value.map(h => h.hostid))
  return allHosts.value.filter(h => !linked.has(h.hostid))
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
      await loadTemplates()
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar dados'
  }
}

function onInstanceGroupChange() {
  selectedInstance.value = ''
  templates.value = []
  search.value = ''
  filteredInstances.value = instances.value.filter(
    i => i.group && String(i.group.id) === String(selectedInstanceGroup.value)
  )
}

async function loadTemplates() {
  if (!selectedInstance.value) { templates.value = []; return }
  loading.value = true
  error.value = ''
  search.value = ''
  try {
    const { data } = await client.get(`/instances/${selectedInstance.value}/templates`)
    templates.value = data
    const inst = instances.value.find(i => String(i.id) === String(selectedInstance.value))
    canWrite.value = inst?.can_write ?? false
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar templates'
  } finally {
    loading.value = false
  }
}

function toggleGroup(list, groupid) {
  const idx = list.indexOf(groupid)
  if (idx === -1) list.push(groupid)
  else list.splice(idx, 1)
}

async function _loadGroups() {
  if (templateGroups.value.length > 0) return
  loadingGroups.value = true
  try {
    const { data } = await client.get(`/instances/${selectedInstance.value}/templates/groups`)
    templateGroups.value = data
  } catch (_) {}
  finally { loadingGroups.value = false }
}

async function openCreate() {
  newTemplate.value = { host: '', name: '', description: '', group_ids: [] }
  createError.value = ''
  showCreateModal.value = true
  await _loadGroups()
}

async function doCreate() {
  if (!newTemplate.value.host || newTemplate.value.group_ids.length === 0) {
    createError.value = 'Nome técnico e pelo menos um grupo são obrigatórios.'
    return
  }
  creating.value = true
  createError.value = ''
  try {
    await client.post(`/instances/${selectedInstance.value}/templates`, newTemplate.value)
    showToast('Template criado', 'success')
    showCreateModal.value = false
    await loadTemplates()
  } catch (e) {
    createError.value = e?.response?.data?.detail || e?.message || 'Erro ao criar template'
  } finally {
    creating.value = false
  }
}

async function openEdit(t) {
  editTemplate.value = t
  editForm.value = { name: t.name, description: t.description || '', group_ids: [] }
  editError.value = ''
  showEditModal.value = true
  await _loadGroups()
  try {
    const { data } = await client.get(`/instances/${selectedInstance.value}/templates/${t.templateid}`)
    editForm.value.group_ids = (data.groups || []).map(g => g.groupid)
  } catch (_) {}
}

async function doEdit() {
  saving.value = true
  editError.value = ''
  try {
    await client.put(
      `/instances/${selectedInstance.value}/templates/${editTemplate.value.templateid}`,
      editForm.value
    )
    const t = templates.value.find(t => t.templateid === editTemplate.value.templateid)
    if (t) {
      t.name = editForm.value.name || t.name
      t.description = editForm.value.description
    }
    showToast('Template atualizado', 'success')
    showEditModal.value = false
  } catch (e) {
    editError.value = e?.response?.data?.detail || e?.message || 'Erro ao atualizar template'
  } finally {
    saving.value = false
  }
}

async function openItems(t) {
  itemsTemplate.value = t
  itemsModal.value = true
  loadingItems.value = true
  templateItems.value = []
  itemsSearch.value = ''
  expandedItem.value = null
  try {
    const { data } = await client.get(
      `/instances/${selectedInstance.value}/templates/${t.templateid}/items`
    )
    templateItems.value = data
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message, 'error')
    itemsModal.value = false
  } finally {
    loadingItems.value = false
  }
}

function closeItems() {
  itemsModal.value = false
  itemsTemplate.value = null
  templateItems.value = []
}

async function openDetail(t) {
  detailTemplate.value = t
  detailModal.value = true
  loadingDetail.value = true
  linkHostId.value = ''
  detailHosts.value = []
  try {
    const [detailRes, hostsRes] = await Promise.all([
      client.get(`/instances/${selectedInstance.value}/templates/${t.templateid}`),
      client.get(`/instances/${selectedInstance.value}/hosts`),
    ])
    detailHosts.value = detailRes.data.hosts || []
    allHosts.value = hostsRes.data
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message, 'error')
    detailModal.value = false
  } finally {
    loadingDetail.value = false
  }
}

function closeDetail() {
  detailModal.value = false
  detailTemplate.value = null
  detailHosts.value = []
}

async function linkHost() {
  if (!linkHostId.value) return
  linking.value = true
  try {
    await client.post(
      `/instances/${selectedInstance.value}/templates/${detailTemplate.value.templateid}/link`,
      { host_ids: [linkHostId.value] }
    )
    const host = allHosts.value.find(h => h.hostid === linkHostId.value)
    if (host) detailHosts.value.push(host)
    linkHostId.value = ''
    const t = templates.value.find(t => t.templateid === detailTemplate.value.templateid)
    if (t) t.hosts_count++
    showToast('Host vinculado', 'success')
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message, 'error')
  } finally {
    linking.value = false
  }
}

async function unlinkHost(host) {
  unlinking.value = host.hostid
  try {
    await client.delete(
      `/instances/${selectedInstance.value}/templates/${detailTemplate.value.templateid}/hosts/${host.hostid}`
    )
    detailHosts.value = detailHosts.value.filter(h => h.hostid !== host.hostid)
    const t = templates.value.find(t => t.templateid === detailTemplate.value.templateid)
    if (t) t.hosts_count = Math.max(0, t.hosts_count - 1)
    showToast('Host desvinculado', 'success')
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message, 'error')
  } finally {
    unlinking.value = null
  }
}

function confirmDelete(t) {
  deleteTarget.value = t
}

async function doDelete() {
  deleting.value = true
  try {
    await client.delete(
      `/instances/${selectedInstance.value}/templates/${deleteTarget.value.templateid}`
    )
    templates.value = templates.value.filter(t => t.templateid !== deleteTarget.value.templateid)
    showToast('Template excluído', 'success')
    deleteTarget.value = null
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message, 'error')
  } finally {
    deleting.value = false
  }
}

function itemTypeName(t) {
  const map = {
    '0': 'Agente Zabbix', '2': 'Trapper', '3': 'Simples', '5': 'Interno Zabbix',
    '7': 'Agente Zabbix (ativo)', '10': 'Externo', '11': 'BD', '12': 'IPMI',
    '13': 'SSH', '14': 'Telnet', '15': 'Calculado', '16': 'JMX', '17': 'SNMP trap',
    '18': 'Dependente', '19': 'HTTP', '20': 'SNMP', '21': 'Script',
  }
  return map[String(t)] || `Tipo ${t}`
}

function preprocessingTypeName(t) {
  const map = {
    '1': 'Multiplicador', '2': 'Trim dir.', '3': 'Trim esq.', '4': 'Trim',
    '5': 'Regex', '6': 'Bool→Dec', '7': 'Oct→Dec', '8': 'Hex→Dec',
    '9': 'Simple change', '10': 'Change/s', '11': 'In range', '12': 'Match regex',
    '13': 'Not match regex', '14': 'Erro JSON', '15': 'Erro XML',
    '16': 'Erro regex', '17': 'Descarta iguais', '18': 'Descarta iguais (HB)',
    '19': 'JSONPath', '20': 'XPath', '21': 'Renomear', '22': 'Prometheus',
    '23': 'Prometheus→JSON', '24': 'CSV→JSON', '25': 'Substituir',
    '26': 'Valor não suportado', '27': 'JavaScript', '28': 'XML→JSON',
  }
  return map[String(t)] || `Tipo ${t}`
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
  width: 100%;
  box-sizing: border-box;
}

.form-control:focus { outline: none; border-color: var(--primary, #d40000); }

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-error { background: rgba(200,0,0,0.08); border: 1px solid var(--danger); color: var(--danger); }
.alert-success { background: rgba(0,160,0,0.08); border: 1px solid var(--success); color: var(--success); }

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
.actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }

.badge { display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 3px; }
.badge-unknown { background: var(--bg); border: 1px solid var(--border); }
.badge-online  { color: var(--success); }
.badge-offline { color: var(--danger); }

.checklist {
  max-height: 160px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  cursor: pointer;
}

.form-hint { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* Standard modals */
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
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-md { max-width: 560px; }
.modal-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
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

/* Fullscreen panels (items + detail) */
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
  max-width: 1100px;
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

.panel-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.panel-title { font-weight: 600; font-size: 16px; }

.panel-body {
  overflow-y: auto;
  flex: 1;
}

.sticky-header {
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 1;
}

.item-row { border-bottom: 1px solid var(--border); cursor: pointer; }
.item-row:hover td { background: var(--bg-hover); }
.item-expanded td { background: var(--bg-hover); }

.cell-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  max-width: 200px;
}

.key-code {
  font-size: 11px;
  background: var(--bg);
  padding: 2px 6px;
  border-radius: 3px;
  color: var(--text-muted);
}

.preprocessing-row { padding: 1px 0; }

.preproc-code {
  font-size: 10px;
  background: var(--bg);
  padding: 1px 4px;
  border-radius: 2px;
  margin-left: 4px;
}

/* Detail modal link bar */
.link-bar {
  padding: 12px 24px;
  border-bottom: 1px solid var(--border);
  display: flex;
  gap: 8px;
  align-items: center;
  background: var(--bg);
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
  text-decoration: none;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn:hover:not(:disabled) { background: var(--bg-hover); }

.btn-primary { background: var(--primary, #d40000); color: #fff; border-color: var(--primary, #d40000); }
.btn-primary:hover:not(:disabled) { opacity: 0.85; background: var(--primary, #d40000); }
.btn-secondary { background: var(--card-bg); }
.btn-danger { background: var(--danger); color: #fff; border-color: var(--danger); }
.btn-danger:hover:not(:disabled) { opacity: 0.85; }
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

.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
