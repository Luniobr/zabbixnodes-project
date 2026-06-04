<template>
  <div>
    <!-- Header -->
    <div class="header">
      <TitlePage title="Grupos de Instâncias" />
      <button class="btn btn-primary btn-sm" @click="openCreate">
        + Novo Grupo
      </button>
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
            <th style="width: 16px"></th>
            <th>Nome</th>
            <th>Descrição</th>
            <th style="width: 100px; text-align: center">Instâncias</th>
            <th style="width: 120px">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="table-empty">Carregando...</td>
          </tr>
          <tr v-else-if="groups.length === 0">
            <td colspan="5" class="table-empty">Nenhum grupo cadastrado</td>
          </tr>
          <tr v-for="g in groups" :key="g.id">
            <td>
              <div
                class="color-dot"
                :style="g.color ? `background: ${g.color}` : 'background: var(--border)'"
              ></div>
            </td>
            <td><strong>{{ g.name }}</strong></td>
            <td class="text-sm text-muted">{{ g.description || '—' }}</td>
            <td style="text-align: center">
              <span class="badge">{{ instanceCount(g.id) }}</span>
            </td>
            <td>
              <div class="actions">
                <button class="btn btn-secondary btn-sm btn-icon" title="Editar" @click="openEdit(g)">✏️</button>
                <button
                  class="btn btn-danger btn-sm btn-icon"
                  title="Excluir"
                  @click="confirmDelete(g)"
                  :disabled="instanceCount(g.id) > 0"
                >🗑</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <Transition name="fade">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false; createError = ''">
        <div class="modal">
          <div class="modal-title">Novo Grupo</div>
          <div v-if="createError" class="alert alert-error">{{ createError }}</div>

          <div class="form-group">
            <label class="form-label">Nome *</label>
            <input
              type="text"
              class="form-control"
              v-model="form.name"
              placeholder="Ex: Clientes, Produção, Região Sul"
              ref="createInputRef"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Descrição</label>
            <input type="text" class="form-control" v-model="form.description" placeholder="Descrição opcional" />
          </div>
          <div class="form-group">
            <label class="form-label">Cor de identificação</label>
            <div class="color-picker-row">
              <input type="color" v-model="form.color" class="color-input" />
              <span class="text-sm text-muted">{{ form.color || 'Nenhuma cor' }}</span>
              <button v-if="form.color" class="btn btn-secondary btn-sm" @click="form.color = ''">✕ Remover</button>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showCreateModal = false; createError = ''">Cancelar</button>
            <button class="btn btn-primary" @click="doCreate" :disabled="creating">
              <span v-if="creating" class="spinner"></span>
              Criar Grupo
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit Modal -->
    <Transition name="fade">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false; editError = ''">
        <div class="modal">
          <div class="modal-title">Editar Grupo — {{ editTarget?.name }}</div>
          <div v-if="editError" class="alert alert-error">{{ editError }}</div>

          <div class="form-group">
            <label class="form-label">Nome *</label>
            <input type="text" class="form-control" v-model="form.name" />
          </div>
          <div class="form-group">
            <label class="form-label">Descrição</label>
            <input type="text" class="form-control" v-model="form.description" />
          </div>
          <div class="form-group">
            <label class="form-label">Cor de identificação</label>
            <div class="color-picker-row">
              <input type="color" v-model="form.color" class="color-input" />
              <span class="text-sm text-muted">{{ form.color || 'Nenhuma cor' }}</span>
              <button v-if="form.color" class="btn btn-secondary btn-sm" @click="form.color = ''">✕ Remover</button>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false; editError = ''">Cancelar</button>
            <button class="btn btn-secondary" title="Clonar este grupo" @click="cloneFromEdit">⧉ Clonar</button>
            <button class="btn btn-primary" @click="doEdit" :disabled="saving">
              <span v-if="saving" class="spinner"></span>
              Salvar
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
          <p>Excluir o grupo <strong>{{ deleteTarget.name }}</strong>?</p>
          <p class="text-muted text-sm" style="margin-top: 8px">
            As instâncias vinculadas ficarão sem grupo.
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useApi } from '@/composables/useApi'
import TitlePage from '@/components/ui/TitlePage.vue'

const { client } = useApi()

// State
const groups = ref([])
const instances = ref([])
const loading = ref(false)
const error = ref('')

// Form compartilhado entre criar e editar
const form = ref({ name: '', description: '', color: '#3b82f6' })

// Create modal
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const createInputRef = ref(null)

// Edit modal
const showEditModal = ref(false)
const editTarget = ref(null)
const saving = ref(false)
const editError = ref('')

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

function instanceCount(groupId) {
  return instances.value.filter((i) => i.group && i.group.id === groupId).length
}

async function init() {
  loading.value = true
  try {
    const [groupsRes, instancesRes] = await Promise.all([
      client.get('/instance-groups'),
      client.get('/instances'),
    ])
    groups.value = groupsRes.data
    instances.value = instancesRes.data
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar dados'
  } finally {
    loading.value = false
  }
}

async function openCreate() {
  form.value = { name: '', description: '', color: '#3b82f6' }
  createError.value = ''
  showCreateModal.value = true
  await nextTick()
  createInputRef.value?.focus()
}

async function doCreate() {
  if (!form.value.name) { createError.value = 'Nome é obrigatório.'; return }
  creating.value = true
  createError.value = ''
  try {
    const { data } = await client.post('/instance-groups', form.value)
    groups.value.push(data)
    groups.value.sort((a, b) => a.name.localeCompare(b.name))
    showToast('Grupo criado', 'success')
    showCreateModal.value = false
  } catch (e) {
    createError.value = e?.response?.data?.detail || e?.message || 'Erro ao criar grupo'
  } finally {
    creating.value = false
  }
}

function openEdit(g) {
  editTarget.value = g
  form.value = { name: g.name, description: g.description || '', color: g.color || '' }
  editError.value = ''
  showEditModal.value = true
}

async function doEdit() {
  if (!form.value.name) { editError.value = 'Nome é obrigatório.'; return }
  saving.value = true
  editError.value = ''
  try {
    const { data } = await client.put(`/instance-groups/${editTarget.value.id}`, form.value)
    Object.assign(editTarget.value, data)
    showToast('Grupo atualizado', 'success')
    showEditModal.value = false
  } catch (e) {
    editError.value = e?.response?.data?.detail || e?.message || 'Erro ao atualizar grupo'
  } finally {
    saving.value = false
  }
}

function cloneFromEdit() {
  const source = editTarget.value
  showEditModal.value = false
  editError.value = ''
  form.value = {
    name: `Cópia de ${source.name}`,
    description: source.description || '',
    color: source.color || '',
  }
  createError.value = ''
  showCreateModal.value = true
}

function confirmDelete(g) {
  deleteTarget.value = g
}

async function doDelete() {
  deleting.value = true
  try {
    await client.delete(`/instance-groups/${deleteTarget.value.id}`)
    groups.value = groups.value.filter((g) => g.id !== deleteTarget.value.id)
    showToast('Grupo excluído', 'success')
    deleteTarget.value = null
  } catch (e) {
    showToast(e?.response?.data?.detail || e?.message || 'Erro ao excluir grupo', 'error')
  } finally {
    deleting.value = false
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

.color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}

.text-sm { font-size: 12px; }
.text-muted { color: var(--text-muted); }

.badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
  background: var(--bg);
  border: 1px solid var(--border);
}

.actions { display: flex; gap: 8px; align-items: center; }

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
  max-width: 440px;
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

.form-control {
  width: 100%;
  padding: 8px 12px;
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

.color-picker-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-input {
  width: 48px;
  height: 36px;
  padding: 2px;
  border: 1px solid var(--border);
  border-radius: 4px;
  cursor: pointer;
  background: var(--card-bg);
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
