<template>
  <div class="users-container">
    <div>
      <TitlePage title="Usuários" />
    </div>

    <div v-if="!isSuperadmin && !loading" class="alert alert-error">
      Acesso restrito a superadmin.
    </div>

    <div v-if="isSuperadmin">
      <div class="card mb-4" style="padding:14px 20px">
        <div class="flex items-center gap-3">
          <button class="btn btn-primary btn-sm" @click="openCreateModal">
            + Novo Usuário
          </button>
        </div>
      </div>

      <div v-if="error" class="alert alert-error">
        {{ error }}
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Usuário</th>
              <th>Email</th>
              <th>Papel</th>
              <th>Status</th>
              <th>Último login</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" style="text-align:center;padding:24px;color:var(--text-muted)">
                Carregando...
              </td>
            </tr>
            <tr v-for="u in users" :key="u.id">
              <td><strong>{{ u.username }}</strong></td>
              <td class="text-muted text-sm">{{ u.email || '—' }}</td>
              <td>
                <span class="badge" :class="{
                  'badge-online': u.role === 'superadmin',
                  'badge-unknown': u.role === 'admin' || u.role === 'operator',
                  'badge-offline': u.role === 'viewer'
                }">
                  {{ roleLabel(u.role) }}
                </span>
              </td>
              <td>
                <span class="badge" :class="u.is_active ? 'badge-online' : 'badge-offline'">
                  {{ u.is_active ? 'Ativo' : 'Inativo' }}
                </span>
              </td>
              <td class="text-sm text-muted">
                {{ u.last_login ? formatDate(u.last_login) : '—' }}
              </td>
              <td>
                <div class="flex gap-2">
                  <button class="btn btn-secondary btn-sm btn-icon" title="Permissões de instância"
                    @click="openPermissionsModal(u)">🔑</button>
                  <button class="btn btn-secondary btn-sm btn-icon" title="Editar"
                    @click="openEditModal(u)">✏️</button>
                  <button class="btn btn-secondary btn-sm btn-icon" title="Resetar senha"
                    @click="openResetModal(u)">🔒</button>
                  <button class="btn btn-danger btn-sm btn-icon" title="Deletar"
                    @click="confirmDelete(u)" :disabled="u.id === currentUserId">🗑</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-title">Novo Usuário</div>
        <div v-if="createError" class="alert alert-error">{{ createError }}</div>
        
        <div class="form-group">
          <label class="form-label">Username *</label>
          <input type="text" class="form-control" v-model="newUser.username" placeholder="joao.silva">
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input type="email" class="form-control" v-model="newUser.email" placeholder="joao@empresa.com">
        </div>
        <div class="form-group">
          <label class="form-label">Senha *</label>
          <input type="password" class="form-control" v-model="newUser.password">
        </div>
        <div class="form-group">
          <label class="form-label">Papel</label>
          <select class="form-control" v-model="newUser.role">
            <option value="viewer">Viewer — leitura nas instâncias autorizadas</option>
            <option value="operator">Operator — leitura e escrita nas instâncias autorizadas</option>
            <option value="superadmin">Superadmin — acesso total sem restrições</option>
          </select>
          <div class="form-hint" v-if="newUser.role !== 'superadmin'">
            Após criar, configure as instâncias acessíveis via botão 🔑
          </div>
          <div class="form-hint" v-if="newUser.role === 'superadmin'" style="color:var(--warning)">
            Superadmin acessa todas as instâncias e pode gerenciar usuários.
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="createUser" :disabled="creating">
            <span v-if="creating" class="spinner"></span>
            Criar
          </button>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-title">Editar Usuário</div>
        <div v-if="editError" class="alert alert-error">{{ editError }}</div>
        
        <div class="form-group">
          <label class="form-label">Username *</label>
          <input type="text" class="form-control" v-model="editUser.username">
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input type="email" class="form-control" v-model="editUser.email">
        </div>
        <div class="form-group">
          <label class="form-label">Papel</label>
          <select class="form-control" v-model="editUser.role">
            <option value="viewer">Viewer — leitura nas instâncias autorizadas</option>
            <option value="operator">Operator — leitura e escrita nas instâncias autorizadas</option>
            <option value="superadmin">Superadmin — acesso total sem restrições</option>
          </select>
        </div>
        <div class="form-group">
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
            <input type="checkbox" v-model="editUser.is_active">
            <span class="form-label" style="margin:0">Ativo</span>
          </label>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveEdit" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            Salvar
          </button>
        </div>
      </div>
    </div>

    <div v-if="showResetModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-title">Resetar Senha — <span>{{ resetTarget?.username }}</span></div>
        <div v-if="resetError" class="alert alert-error">{{ resetError }}</div>
        
        <div class="form-group">
          <label class="form-label">Nova senha *</label>
          <input type="password" class="form-control" v-model="resetPassword" placeholder="Mínimo 8 caracteres">
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showResetModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="doReset" :disabled="resetting">
            <span v-if="resetting" class="spinner"></span>
            Confirmar
          </button>
        </div>
      </div>
    </div>

    <div v-if="showPermissionsModal" class="modal-overlay">
      <div class="modal" style="max-width:560px">
        <div class="modal-title">
          Permissões — <span>{{ permTarget?.username }}</span>
          <span class="badge badge-unknown text-sm" style="margin-left:8px">{{ roleLabel(permTarget?.role) }}</span>
        </div>
        
        <div v-if="permTarget?.role === 'superadmin'" class="alert alert-info" style="margin-bottom:12px">
          Superadmin tem acesso total a todas as instâncias — permissões individuais são ignoradas.
        </div>
        <div v-if="permTarget?.role !== 'superadmin'" class="text-muted text-sm" style="margin-bottom:12px">
          Marque as instâncias que este usuário pode acessar. <strong>Escrita</strong> permite criar, editar e excluir objetos.
        </div>

        <div v-if="loadingPerms" style="text-align:center;padding:16px;color:var(--text-muted)">Carregando...</div>

        <div v-if="!loadingPerms && permTarget?.role !== 'superadmin'">
          <div style="display:grid;grid-template-columns:1fr 90px 90px;gap:8px;padding:6px 0;border-bottom:2px solid var(--border);font-size:11px;font-weight:600;text-transform:uppercase;color:var(--text-muted)">
            <span>Instância</span>
            <span style="text-align:center">Acesso</span>
            <span style="text-align:center">Escrita</span>
          </div>
          
          <div style="max-height:300px;overflow-y:auto">
            <div v-for="inst in allInstances" :key="inst.id" style="display:grid;grid-template-columns:1fr 90px 90px;gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid var(--border)">
              <div style="display:flex;align-items:center;gap:6px">
                <span class="badge" :class="inst.status === 'online' ? 'badge-online' : 'badge-offline'"
                  style="width:6px;height:6px;padding:0;border-radius:50%"></span>
                <span class="text-sm">{{ inst.name }}</span>
                <span v-if="inst.group?.name" class="text-muted text-sm">({{ inst.group?.name }})</span>
              </div>
              <div style="text-align:center">
                <input type="checkbox"
                  :checked="permIds.includes(inst.id)"
                  @change="togglePerm(inst.id)"
                  style="width:16px;height:16px;cursor:pointer">
              </div>
              <div style="text-align:center">
                <input type="checkbox"
                  :checked="writeIds.includes(inst.id)"
                  :disabled="!permIds.includes(inst.id)"
                  @change="toggleWrite(inst.id)"
                  style="width:16px;height:16px;cursor:pointer"
                  :style="!permIds.includes(inst.id) ? 'opacity:0.3' : ''">
              </div>
            </div>
          </div>
          
          <div style="margin-top:8px;display:flex;gap:8px">
            <button class="btn btn-secondary btn-sm" @click="selectAllPerms">Selecionar tudo (leitura)</button>
            <button class="btn btn-secondary btn-sm" @click="clearAllPerms">Limpar tudo</button>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showPermissionsModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="savePermissions" :disabled="savingPerms || permTarget?.role === 'superadmin'">
            <span v-if="savingPerms" class="spinner"></span>
            Salvar
          </button>
        </div>
      </div>
    </div>

    <div v-if="deleteTarget" class="modal-overlay">
      <div class="modal">
        <div class="modal-title">Confirmar exclusão</div>
        <p>Excluir o usuário <strong>{{ deleteTarget?.username }}</strong>?</p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="deleteTarget = null">Cancelar</button>
          <button class="btn btn-danger" @click="doDelete" :disabled="deleting">
            <span v-if="deleting" class="spinner"></span>
            Excluir
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import TitlePage from '@/components/ui/TitlePage.vue'
import { ref, onMounted } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // Altere para a URL do seu FastAPI
});

api.interceptors.request.use((config) => {
  const authData = localStorage.getItem('useAuth');
  if (authData) {
    // Caso seu localStorage salve uma string pura ou um objeto JSON stringificado
    // Ajuste se o seu token precisar do prefixo "Bearer " exigido pelo FastAPI (get_current_user)
    const token = authData.startsWith('{') ? JSON.parse(authData).token : authData;
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Estados Reativos
const users = ref([])
const allInstances = ref([])
const currentUserId = ref(null)
const isSuperadmin = ref(false)
const loading = ref(false)
const error = ref('')

// Cadastro
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const newUser = ref({ username: '', email: '', password: '', role: 'viewer' })

// Edição
const showEditModal = ref(false)
const saving = ref(false)
const editError = ref('')
const editTarget = ref(null)
const editUser = ref({ username: '', email: '', role: '', is_active: true })

// Reset de Senha
const showResetModal = ref(false)
const resetting = ref(false)
const resetError = ref('')
const resetTarget = ref(null)
const resetPassword = ref('')

// Permissões
const showPermissionsModal = ref(false)
const loadingPerms = ref(false)
const savingPerms = ref(false)
const permTarget = ref(null)
const permIds = ref([])
const writeIds = ref([])

// Exclusão
const deleteTarget = ref(null)
const deleting = ref(false)

// Inicialização do Componente
onMounted(async () => {
  await init()
})

const init = async () => {
  loading.value = true
  error.value = ''
  try {
    // 1. Decodificar informações do usuário autenticado atual (ajustar conforme seu auth real)
    // O mock abaixo espelha o comportamento do endpoint FastAPI dependendo de require_superadmin
    const token = localStorage.getItem('useAuth')
    
    // ATENÇÃO: Substitua pelo seu endpoint real que devolve o usuário logado (Ex: api.get('/auth/me'))
    // Para fluxo do seu backend FastAPI, precisamos garantir o ID e a role para as validações em tela
    const me = { id: 1, role: 'superadmin' } 
    
    currentUserId.value = me.id
    isSuperadmin.value = me.role === 'superadmin'

    if (!isSuperadmin.value) return

    // 2. Busca paralela mapeada para os endpoints FastAPI informados
    const [usersRes, instancesRes] = await Promise.all([
      api.get('/users'),
      api.get('/instances') // Presumindo existência desse endpoint mapeado nas suas rotas
    ])

    users.value = usersRes.data
    allInstances.value = instancesRes.data || []
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

// Auxiliares de Formatação
const roleLabel = (role) => {
  const roles = { superadmin: 'Superadmin', operator: 'Operator', viewer: 'Viewer' }
  return roles[role] || role
}

const formatDate = (iso) => {
  return new Date(iso).toLocaleString('pt-BR')
}

// Métodos: Criação
const openCreateModal = () => {
  newUser.value = { username: '', email: '', password: '', role: 'viewer' }
  createError.value = ''
  showCreateModal.value = true
}

const createUser = async () => {
  if (!newUser.value.username || !newUser.value.password) return
  creating.value = true
  createError.value = ''
  try {
    const res = await api.post('/users', newUser.value)
    users.value.push(res.data)
    showCreateModal.value = false
    showToast('Usuário criado com sucesso', 'success')
  } catch (e) {
    createError.value = e.response?.data?.detail || e.message
  } finally {
    creating.value = false
  }
}

// Métodos: Edição
const openEditModal = (u) => {
  editTarget.value = u
  editUser.value = { username: u.username, email: u.email || '', role: u.role, is_active: u.is_active }
  editError.value = ''
  showEditModal.value = true
}

const saveEdit = async () => {
  saving.value = true
  editError.value = ''
  try {
    const res = await api.put(`/users/${editTarget.value.id}`, editUser.value)
    Object.assign(editTarget.value, res.data)
    showToast('Usuário atualizado com sucesso', 'success')
    showEditModal.value = false
  } catch (e) {
    editError.value = e.response?.data?.detail || e.message
  } finally {
    saving.value = false
  }
}

// Métodos: Reset de Senha
const openResetModal = (u) => {
  resetTarget.value = u
  resetPassword.value = ''
  resetError.value = ''
  showResetModal.value = true
}

const doReset = async () => {
  if (!resetPassword.value) return
  resetting.value = true
  resetError.value = ''
  try {
    await api.post(`/users/${resetTarget.value.id}/reset-password`, { password: resetPassword.value })
    showToast('Senha alterada com sucesso', 'success')
    showResetModal.value = false
  } catch (e) {
    resetError.value = e.response?.data?.detail || e.message
  } finally {
    resetting.value = false
  }
}

// Métodos: Permissões
const openPermissionsModal = async (u) => {
  permTarget.value = u
  permIds.value = []
  writeIds.value = []
  showPermissionsModal.value = true
  loadingPerms.value = true
  try {
    const res = await api.get(`/users/${u.id}/permissions`)
    // Mapeando a resposta vinda do backend: [{"instance_id": ..., "can_write": ...}]
    permIds.value = res.data.map(p => p.instance_id)
    writeIds.value = res.data.filter(p => p.can_write).map(p => p.instance_id)
  } catch (e) {
    showToast(e.response?.data?.detail || e.message, 'error')
  } finally {
    loadingPerms.value = false
  }
}

const selectAllPerms = () => {
  permIds.value = allInstances.value.map(i => i.id)
}

const clearAllPerms = () => {
  permIds.value = []
  writeIds.value = []
}

const togglePerm = (instId) => {
  const idx = permIds.value.indexOf(instId)
  if (idx === -1) {
    permIds.value.push(instId)
    writeIds.value.push(instId) // Comportamento original: assume can_write=true ao marcar acesso
  } else {
    permIds.value.splice(idx, 1)
    const wi = writeIds.value.indexOf(instId)
    if (wi !== -1) writeIds.value.splice(wi, 1)
  }
}

const toggleWrite = (instId) => {
  const idx = writeIds.value.indexOf(instId)
  if (idx === -1) {
    writeIds.value.push(instId)
  } else {
    writeIds.value.splice(idx, 1)
  }
}

const savePermissions = async () => {
  savingPerms.value = true
  try {
    const permissionsPayload = permIds.value.map(id => ({
      instance_id: id,
      can_write: writeIds.value.includes(id)
    }))
    
    await api.put(`/users/${permTarget.value.id}/permissions`, {
      permissions: permissionsPayload
    })
    
    showToast('Permissões salvas com sucesso', 'success')
    showPermissionsModal.value = false
  } catch (e) {
    showToast(e.response?.data?.detail || e.message, 'error')
  } finally {
    savingPerms.value = false
  }
}

// Métodos: Exclusão
const confirmDelete = (u) => {
  deleteTarget.value = u
}

const doDelete = async () => {
  deleting.value = true
  try {
    await api.delete(`/users/${deleteTarget.value.id}`)
    users.value = users.value.filter(u => u.id !== deleteTarget.value.id)
    showToast('Usuário excluído com sucesso', 'success')
    deleteTarget.value = null
  } catch (e) {
    showToast(e.response?.data?.detail || e.message, 'error')
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
/* O escopo garante que as regras do Zabbix se apliquem perfeitamente ao seu HTML transformado */
.users-container {
  width: 100%;
}
</style>