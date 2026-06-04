<template>
  <div>
    <div class="header">
      <TitlePage title="Hosts" />
      <button v-if="canWrite" class="btn btn-primary btn-sm" @click="openCreateModal" :disabled="!selectedInstance">
        + Novo Host
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
        <select class="form-control filter-select" v-model="selectedInstance" @change="loadHosts">
          <option value="">— Selecione —</option>
          <option v-for="inst in filteredInstances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
        </select>
      </template>

      <select v-if="selectedInstance" class="form-control filter-select" v-model="selectedGroup" @change="loadHosts">
        <option value="">Todos os grupos</option>
        <option v-for="g in hostGroups" :key="g.groupid" :value="g.groupid">{{ g.name }}</option>
      </select>

      <input
        v-if="selectedInstance"
        type="text"
        class="form-control filter-search"
        v-model="searchHost"
        placeholder="Pesquisar host..."
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
            <th>Hostname</th>
            <th>Nome Visível</th>
            <th>Grupos</th>
            <th>Templates</th>
            <th>Interface</th>
            <th>Proxy</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!selectedInstanceGroup">
            <td colspan="8" class="table-empty">Selecione um grupo de instâncias para começar</td>
          </tr>
          <tr v-else-if="!selectedInstance">
            <td colspan="8" class="table-empty">Selecione uma instância</td>
          </tr>
          <tr v-else-if="loading">
            <td colspan="8" class="table-empty">Carregando...</td>
          </tr>
          <tr v-else-if="filteredHosts.length === 0">
            <td colspan="8" class="table-empty">Nenhum host encontrado</td>
          </tr>
          <tr v-for="h in filteredHosts" :key="h.hostid">
            <td><strong>{{ h.host }}</strong></td>
            <td>{{ h.name !== h.host ? h.name : '—' }}</td>
            <td>
              <span
                v-for="g in h.groups.slice(0, 3)"
                :key="g.groupid"
                class="badge badge-unknown"
                style="margin-right: 2px"
              >{{ g.name }}</span>
              <span v-if="h.groups.length > 3" class="text-muted text-sm">+{{ h.groups.length - 3 }}</span>
            </td>
            <td>
              <span v-for="t in h.parentTemplates.slice(0, 2)" :key="t.templateid" class="text-sm" style="display: block">
                {{ t.name }}
              </span>
              <span v-if="h.parentTemplates.length > 2" class="text-muted text-sm">+{{ h.parentTemplates.length - 2 }} mais</span>
              <span v-if="h.parentTemplates.length === 0" class="text-muted">—</span>
            </td>
            <td>
              <span
                v-for="iface in h.interfaces.filter(i => i.main == 1)"
                :key="iface.interfaceid"
                class="text-sm"
              >{{ iface.useip == 1 ? iface.ip : iface.dns }}</span>
            </td>
            <td>
              <span v-if="h.monitoringProxy?.name" class="badge badge-unknown text-sm">{{ h.monitoringProxy.name }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <span class="badge" :class="h.status == '0' ? 'badge-online' : 'badge-offline'">
                {{ h.status == '0' ? 'Habilitado' : 'Desabilitado' }}
              </span>
            </td>
            <td>
              <div class="actions">
                <button v-if="canWrite" class="btn btn-secondary btn-sm btn-icon" title="Editar" @click="openEditModal(h)">✏️</button>
                <button class="btn btn-secondary btn-sm btn-icon" title="Gerenciar Templates" @click="openTemplatesModal(h)">📋</button>
                <router-link
                  class="btn btn-secondary btn-sm btn-icon"
                  title="Ver Itens"
                  :to="`/items?instance_id=${selectedInstance}&host_id=${h.hostid}&host_name=${encodeURIComponent(h.name)}`"
                >📊</router-link>
                <button
                  v-if="canWrite"
                  class="btn btn-secondary btn-sm btn-icon"
                  :title="h.status == '0' ? 'Desabilitar' : 'Habilitar'"
                  @click="toggleHost(h)"
                >{{ h.status == '0' ? '⏸' : '▶' }}</button>
                <button v-if="canWrite" class="btn btn-danger btn-sm btn-icon" title="Deletar" @click="confirmDeleteHost(h)">🗑</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Host Modal -->
    <Transition name="fade">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false; createError = ''">
        <div class="modal">
          <div class="modal-title">Novo Host</div>
          <div v-if="createError" class="alert alert-error">{{ createError }}</div>

          <div class="form-group">
            <label class="form-label">Hostname (técnico) *</label>
            <input type="text" class="form-control" v-model="newHost.host" placeholder="server-prod-01" />
          </div>
          <div class="form-group">
            <label class="form-label">Nome visível</label>
            <input type="text" class="form-control" v-model="newHost.name" placeholder="Servidor Produção 01" />
          </div>
          <div class="form-group">
            <label class="form-label">IP da Interface</label>
            <input type="text" class="form-control" v-model="newHost.ip" placeholder="192.168.1.100" />
          </div>
          <div class="form-group">
            <label class="form-label">Porta</label>
            <input type="text" class="form-control" v-model="newHost.port" placeholder="10050" />
          </div>
          <div class="form-group">
            <label class="form-label">Grupo de Hosts *</label>
            <select class="form-control" v-model="newHost.group_id">
              <option value="">— Selecione —</option>
              <option v-for="g in hostGroups" :key="g.groupid" :value="g.groupid">{{ g.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Templates</label>
            <div class="checklist">
              <div v-if="loadingCreateTemplates" class="text-muted text-sm" style="padding: 4px">Carregando...</div>
              <label v-for="t in allCreateTemplates" :key="t.templateid" class="checklist-item">
                <input
                  type="checkbox"
                  :checked="newHost.templateIds.includes(t.templateid)"
                  @change="toggleCreateTemplate(t.templateid)"
                />
                <span class="text-sm">{{ t.name }}</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Monitorado por</label>
            <select class="form-control" v-model="newHost.proxy_id">
              <option value="">Servidor (sem proxy)</option>
              <option v-for="p in instanceProxies" :key="p.proxyid" :value="p.proxyid">{{ p.name }}</option>
            </select>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showCreateModal = false; createError = ''">Cancelar</button>
            <button class="btn btn-primary" @click="createHost" :disabled="creating">
              <span v-if="creating" class="spinner"></span>
              Criar Host
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit Host Modal -->
    <Transition name="fade">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false; editError = ''">
        <div class="modal modal-lg">
          <div class="modal-title">Editar Host — {{ editHost.host }}</div>
          <div v-if="editError" class="alert alert-error">{{ editError }}</div>

          <div class="form-group">
            <label class="form-label">Hostname (técnico) *</label>
            <input type="text" class="form-control" v-model="editHost.host" />
          </div>
          <div class="form-group">
            <label class="form-label">Nome visível</label>
            <input type="text" class="form-control" v-model="editHost.name" />
          </div>
          <div class="form-group">
            <label class="form-label">Descrição</label>
            <input type="text" class="form-control" v-model="editHost.description" />
          </div>

          <div class="form-group">
            <label class="form-label">Grupos</label>
            <div class="checklist">
              <label v-for="g in hostGroups" :key="g.groupid" class="checklist-item">
                <input
                  type="checkbox"
                  :checked="editHost.groupIds.includes(g.groupid)"
                  @change="toggleEditGroup(g.groupid)"
                />
                <span class="text-sm">{{ g.name }}</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Interface principal</label>
            <div class="interface-row">
              <div style="flex: 1">
                <label class="form-label text-sm" style="margin-bottom: 4px">
                  <input type="radio" v-model="editHost.useip" value="1" style="margin-right: 4px" />IP
                  <input type="radio" v-model="editHost.useip" value="0" style="margin-left: 8px; margin-right: 4px" />DNS
                </label>
                <input
                  type="text"
                  class="form-control"
                  :placeholder="editHost.useip == '1' ? '192.168.1.100' : 'hostname.example.com'"
                  :value="editHost.useip == '1' ? editHost.ip : editHost.dns"
                  @input="editHost.useip == '1' ? (editHost.ip = $event.target.value) : (editHost.dns = $event.target.value)"
                />
              </div>
              <div style="width: 100px">
                <label class="form-label text-sm" style="margin-bottom: 4px">Porta</label>
                <input type="text" class="form-control" v-model="editHost.port" />
              </div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Monitorado por</label>
            <select class="form-control" v-model="editHost.proxy_id">
              <option value="">Servidor (sem proxy)</option>
              <option v-for="p in instanceProxies" :key="p.proxyid" :value="p.proxyid">{{ p.name }}</option>
            </select>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false; editError = ''">Cancelar</button>
            <button class="btn btn-primary" @click="saveEdit" :disabled="savingEdit">
              <span v-if="savingEdit" class="spinner"></span>
              Salvar
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Templates Modal -->
    <Transition name="fade">
      <div v-if="showTemplatesModal" class="modal-overlay" @click.self="showTemplatesModal = false; templatesError = ''">
        <div class="modal modal-lg">
          <div class="modal-title">Templates — {{ templatesHost?.host }}</div>
          <div v-if="templatesError" class="alert alert-error">{{ templatesError }}</div>
          <div v-if="loadingTemplates" class="table-empty">Carregando...</div>
          <div v-else class="checklist">
            <label v-for="t in allTemplates" :key="t.templateid" class="checklist-item">
              <input
                type="checkbox"
                :checked="selectedTemplateIds.includes(t.templateid)"
                @change="toggleTemplate(t.templateid)"
              />
              <span class="text-sm">{{ t.name }}</span>
            </label>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showTemplatesModal = false; templatesError = ''">Cancelar</button>
            <button class="btn btn-primary" @click="saveTemplates" :disabled="savingTemplates">
              <span v-if="savingTemplates" class="spinner"></span>
              Salvar
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete Modal -->
    <Transition name="fade">
      <div v-if="deleteHostTarget" class="modal-overlay" @click.self="deleteHostTarget = null">
        <div class="modal">
          <div class="modal-title">Confirmar exclusão</div>
          <p>Excluir o host <strong>{{ deleteHostTarget.host }}</strong>?</p>
          <p class="text-muted text-sm" style="margin-top: 8px">Esta ação remove o host da instância Zabbix.</p>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="deleteHostTarget = null">Cancelar</button>
            <button class="btn btn-danger" @click="doDeleteHost" :disabled="deletingHost">
              <span v-if="deletingHost" class="spinner"></span>
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
const hosts = ref([])
const hostGroups = ref([])
const selectedInstance = ref('')
const selectedGroup = ref('')
const searchHost = ref('')
const loading = ref(false)
const error = ref('')
const canWrite = ref(false)
const instanceProxies = ref([])

// Create modal
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const loadingCreateTemplates = ref(false)
const allCreateTemplates = ref([])
const newHost = ref({ host: '', name: '', ip: '127.0.0.1', port: '10050', group_id: '', proxy_id: '', templateIds: [] })

// Edit modal
const showEditModal = ref(false)
const editHost = ref({ hostid: '', host: '', name: '', description: '', groupIds: [], ip: '', dns: '', port: '10050', useip: '1', interfaceid: '', proxy_id: '' })
const savingEdit = ref(false)
const editError = ref('')

// Templates modal
const showTemplatesModal = ref(false)
const templatesHost = ref(null)
const allTemplates = ref([])
const selectedTemplateIds = ref([])
const loadingTemplates = ref(false)
const savingTemplates = ref(false)
const templatesError = ref('')

// Delete modal
const deleteHostTarget = ref(null)
const deletingHost = ref(false)

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

const filteredHosts = computed(() => {
  if (!searchHost.value) return hosts.value
  const q = searchHost.value.toLowerCase()
  return hosts.value.filter(h =>
    h.host.toLowerCase().includes(q) || h.name.toLowerCase().includes(q)
  )
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
      await loadHosts()
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar dados'
  }
}

function onInstanceGroupChange() {
  selectedInstance.value = ''
  selectedGroup.value = ''
  hosts.value = []
  searchHost.value = ''
  filteredInstances.value = instances.value.filter(
    i => i.group && String(i.group.id) === String(selectedInstanceGroup.value)
  )
}

async function loadHosts() {
  if (!selectedInstance.value) { hosts.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const [hostsRes, groupsRes, proxiesRes] = await Promise.all([
      client.get(`/instances/${selectedInstance.value}/hosts`, { params: { group_id: selectedGroup.value || undefined } }),
      client.get(`/instances/${selectedInstance.value}/hosts/groups`),
      client.get(`/instances/${selectedInstance.value}/proxies`),
    ])
    hosts.value = hostsRes.data
    hostGroups.value = groupsRes.data
    instanceProxies.value = proxiesRes.data
    const inst = instances.value.find(i => String(i.id) === String(selectedInstance.value))
    canWrite.value = inst?.can_write ?? false
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar hosts'
  } finally {
    loading.value = false
  }
}

async function openCreateModal() {
  showCreateModal.value = true
  if (allCreateTemplates.value.length === 0) {
    loadingCreateTemplates.value = true
    try {
      const { data } = await client.get('/templates', { params: { instance_id: selectedInstance.value } })
      allCreateTemplates.value = data
    } catch (err) {
      console.error('Erro ao carregar templates:', err)
    } finally {
      loadingCreateTemplates.value = false
    }
  }
}

function toggleCreateTemplate(templateid) {
  const idx = newHost.value.templateIds.indexOf(templateid)
  if (idx === -1) newHost.value.templateIds.push(templateid)
  else newHost.value.templateIds.splice(idx, 1)
}

async function createHost() {
  if (!newHost.value.host || !newHost.value.group_id) return
  creating.value = true
  createError.value = ''
  try {
    await client.post(`/instances/${selectedInstance.value}/hosts`, {
      host: newHost.value.host,
      name: newHost.value.name || newHost.value.host,
      groups: [{ groupid: newHost.value.group_id }],
      templates: newHost.value.templateIds.map(id => ({ templateid: id })),
      interfaces: [{ type: 1, main: 1, useip: 1, ip: newHost.value.ip, dns: '', port: newHost.value.port }],
      monitored_by: newHost.value.proxy_id ? 1 : 0,
      proxyid: newHost.value.proxy_id || '0',
    })
    showCreateModal.value = false
    newHost.value = { host: '', name: '', ip: '127.0.0.1', port: '10050', group_id: '', proxy_id: '', templateIds: [] }
    showToast('Host criado com sucesso', 'success')
    await loadHosts()
  } catch (e) {
    createError.value = e?.response?.data?.detail || e?.message || 'Erro ao criar host'
  } finally {
    creating.value = false
  }
}

async function toggleHost(h) {
  const enable = h.status !== '0'
  try {
    await client.patch(`/hosts/${h.hostid}/toggle`, {
      instance_id: selectedInstance.value,
      enable,
    })
    h.status = enable ? '0' : '1'
    showToast(`Host ${enable ? 'habilitado' : 'desabilitado'}`, 'success')
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message, 'error')
  }
}

function openEditModal(h) {
  const mainIface = (h.interfaces || []).find(i => i.main == 1) || {}
  editHost.value = {
    hostid: h.hostid,
    host: h.host,
    name: h.name !== h.host ? h.name : '',
    description: h.description || '',
    groupIds: (h.groups || []).map(g => g.groupid),
    ip: mainIface.ip || '',
    dns: mainIface.dns || '',
    port: mainIface.port || '10050',
    useip: String(mainIface.useip ?? 1),
    interfaceid: mainIface.interfaceid || '',
    proxy_id: h.monitoringProxy?.proxyid || '',
  }
  editError.value = ''
  showEditModal.value = true
}

function toggleEditGroup(groupid) {
  const idx = editHost.value.groupIds.indexOf(groupid)
  if (idx === -1) editHost.value.groupIds.push(groupid)
  else editHost.value.groupIds.splice(idx, 1)
}

async function saveEdit() {
  if (!editHost.value.host || editHost.value.groupIds.length === 0) {
    editError.value = 'Hostname e pelo menos um grupo são obrigatórios.'
    return
  }
  savingEdit.value = true
  editError.value = ''
  try {
    const payload = {
      instance_id: selectedInstance.value,
      host: editHost.value.host,
      name: editHost.value.name || editHost.value.host,
      description: editHost.value.description,
      groups: editHost.value.groupIds.map(id => ({ groupid: id })),
      monitored_by: editHost.value.proxy_id ? 1 : 0,
      proxyid: editHost.value.proxy_id || '0',
    }
    if (editHost.value.interfaceid) {
      payload.interfaces = [{
        interfaceid: editHost.value.interfaceid,
        type: 1, main: 1,
        useip: parseInt(editHost.value.useip),
        ip: editHost.value.ip,
        dns: editHost.value.dns,
        port: editHost.value.port,
      }]
    }
    await client.put(`/hosts/${editHost.value.hostid}`, payload)
    showToast('Host atualizado', 'success')
    showEditModal.value = false
    await loadHosts()
  } catch (e) {
    editError.value = e?.response?.data?.detail || e?.message || 'Erro ao atualizar host'
  } finally {
    savingEdit.value = false
  }
}

async function openTemplatesModal(h) {
  templatesHost.value = h
  selectedTemplateIds.value = (h.parentTemplates || []).map(t => t.templateid)
  showTemplatesModal.value = true
  loadingTemplates.value = true
  templatesError.value = ''
  try {
    const { data } = await client.get(`/instances/${selectedInstance.value}/templates`)
    allTemplates.value = data
  } catch (e) {
    templatesError.value = e?.response?.data?.detail || e?.message
  } finally {
    loadingTemplates.value = false
  }
}

function toggleTemplate(templateid) {
  const idx = selectedTemplateIds.value.indexOf(templateid)
  if (idx === -1) selectedTemplateIds.value.push(templateid)
  else selectedTemplateIds.value.splice(idx, 1)
}

async function saveTemplates() {
  savingTemplates.value = true
  templatesError.value = ''
  try {
    await client.put(`/hosts/${templatesHost.value.hostid}`, {
      instance_id: selectedInstance.value,
      templates: selectedTemplateIds.value.map(id => ({ templateid: id })),
    })
    templatesHost.value.parentTemplates = allTemplates.value.filter(
      t => selectedTemplateIds.value.includes(t.templateid)
    )
    showToast('Templates atualizados', 'success')
    showTemplatesModal.value = false
  } catch (e) {
    templatesError.value = e?.response?.data?.detail || e?.message
  } finally {
    savingTemplates.value = false
  }
}

function confirmDeleteHost(h) {
  deleteHostTarget.value = h
}

async function doDeleteHost() {
  deletingHost.value = true
  try {
    await client.delete(`/hosts/${deleteHostTarget.value.hostid}`, {
      params: { instance_id: selectedInstance.value },
    })
    hosts.value = hosts.value.filter(h => h.hostid !== deleteHostTarget.value.hostid)
    showToast('Host excluído', 'success')
    deleteHostTarget.value = null
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message || 'Erro ao excluir host', 'error')
  } finally {
    deletingHost.value = false
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
.filter-select { width: 180px; }
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
  padding: 2px 6px;
  border-radius: 3px;
}

.badge-unknown { background: var(--bg); border: 1px solid var(--border); }
.badge-online  { color: var(--success); }
.badge-offline { color: var(--danger); }

.actions { display: flex; gap: 6px; align-items: center; }

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

.interface-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
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
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-lg { max-width: 560px; }

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
