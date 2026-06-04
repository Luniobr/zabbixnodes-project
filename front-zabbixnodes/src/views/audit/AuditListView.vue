<template>
  <div>
    <div>
     <TitlePage title="Auditoria"/>
    </div>

    <div class="card mb-4" style="padding:14px 20px">
      <div class="flex items-center gap-3" style="flex-wrap:wrap">
        <div class="flex items-center gap-2">
          <label class="form-label" style="margin:0">Instância:</label>
          <select 
            class="form-control" 
            style="min-width:180px" 
            v-model.number="filters.instance_id" 
            @change="load"
          >
            <option value="">Todas</option>
            <option v-for="inst in instances" :key="inst.id" :value="inst.id">
              {{ inst.name }}
            </option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <label class="form-label" style="margin:0">Ação:</label>
          <select 
            class="form-control" 
            style="min-width:160px" 
            v-model="filters.action" 
            @change="load"
          >
            <option value="">Todas</option>
            <option>CREATE_INSTANCE</option>
            <option>UPDATE_INSTANCE</option>
            <option>DELETE_INSTANCE</option>
            <option>ENABLE_INSTANCE</option>
            <option>DISABLE_INSTANCE</option>
            <option>CREATE_HOST</option>
            <option>UPDATE_HOST</option>
            <option>DELETE_HOST</option>
            <option>ENABLE_HOST</option>
            <option>DISABLE_HOST</option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <label class="form-label" style="margin:0">Resultado:</label>
          <select 
            class="form-control" 
            style="min-width:120px" 
            v-model="filters.result" 
            @change="load"
          >
            <option value="">Todos</option>
            <option value="success">Sucesso</option>
            <option value="error">Erro</option>
          </select>
        </div>
        
        <button class="btn btn-secondary btn-sm" @click="resetFilters">Limpar filtros</button>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Data/Hora</th>
            <th>Usuário</th>
            <th>Ação</th>
            <th>Instância</th>
            <th>Objeto</th>
            <th>Resultado</th>
            <th>IP</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" style="text-align:center;padding:24px;color:var(--text-muted)">Carregando...</td>
          </tr>
          <tr v-else-if="logs.length === 0">
            <td colspan="7" style="text-align:center;padding:24px;color:var(--text-muted)">Nenhum registro encontrado</td>
          </tr>
          <tr v-else v-for="log in logs" :key="log.id">
            <td class="text-sm">{{ formatDate(log.created_at) }}</td>
            <td>{{ log.username || '—' }}</td>
            <td><code>{{ log.action }}</code></td>
            <td>{{ log.instance_name || '—' }}</td>
            <td>
              <span v-if="log.object_type" class="text-muted text-sm">{{ log.object_type }}</span>
              <span v-if="log.object_name">: {{ log.object_name }}</span>
            </td>
            <td v-html="resultBadge(log.result)"></td>
            <td class="text-sm text-muted">{{ log.ip_address || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center gap-3 mt-4" v-if="total > 0">
      <span class="text-sm text-muted">{{ total }} registros</span>
      <div class="pagination">
        <button class="page-btn" @click="prevPage" :disabled="page <= 1">‹</button>
        <span class="page-btn active">{{ page }}</span>
        <button class="page-btn" @click="nextPage" :disabled="page * pageSize >= total">›</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';

// Configuração do Axios (Você pode mover isso para um arquivo centralizado 'api.js' depois)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // Altere para a URL do seu FastAPI
});

// Interceptor para injetar o token que seu router.beforeEach já valida
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

// Estado Reativo
const logs = ref([]);
const instances = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(50);
const loading = ref(false);
const error = ref('');

const filters = reactive({
  instance_id: '',
  action: '',
  result: ''
});

// Buscar lista de instâncias para popular o <select> do filtro
const loadInstances = async () => {
  try {
    // Altere para a rota real de instâncias do seu backend FastAPI se for diferente
    const response = await api.get('/instances'); 
    instances.value = response.data; 
  } catch (e) {
    console.error('Erro ao carregar instâncias:', e);
  }
};

// Carregar os Logs de Auditoria (Consumindo seu endpoint FastAPI)
const load = async () => {
  loading.value = true;
  error.value = '';
  try {
    // Garante que as instâncias existem para o filtro
    if (instances.value.length === 0) {
      await loadInstances();
    }
    
    // Montando os Query Params exatamente como o FastAPI espera
    const params = { 
      page: page.value, 
      page_size: pageSize.value 
    };
    
    if (filters.instance_id) params.instance_id = filters.instance_id;
    if (filters.action) params.action = filters.action;
    if (filters.result) params.result = filters.result;
    
    // Chamada GET para o prefixo "/audit" do seu APIRouter
    const response = await api.get('/audit', { params });
    
    // O FastAPI vai retornar o Schema 'AuditLogPage' (total, page, page_size, items)
    logs.value = response.data.items;
    total.value = response.data.total;
  } catch (e) {
    // Captura mensagens de erro do Axios ou do servidor
    error.value = e.response?.data?.detail || e.message || 'Erro ao carregar dados de auditoria.';
  } finally {
    loading.value = false;
  }
};

// Paginação e Filtros
const prevPage = () => {
  if (page.value > 1) {
    page.value--;
    load();
  }
};

const nextPage = () => {
  if (page.value * pageSize.value < total.value) {
    page.value++;
    load();
  }
};

const resetFilters = () => {
  filters.instance_id = '';
  filters.action = '';
  filters.result = '';
  page.value = 1;
  load();
};

// Formatação de UI
const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString('pt-BR');
};

const resultBadge = (result) => {
  if (result === 'success') {
    return `<span class="badge badge-success">Sucesso</span>`;
  }
  return `<span class="badge badge-error">Erro</span>`;
};

// Ciclo de Vida inicial
onMounted(() => {
  load();
});
</script>

<style scoped>
/* ===== Seus estilos originais mantidos intactos ===== */
:root {
  --primary: #d40000;
  --primary-dark: #a30000;
  --primary-light: #ff4444;
  --sidebar-bg: #1f2d3d;
  --sidebar-text: #b8c4ce;
  --sidebar-active: rgba(255,255,255,0.14);
  --sidebar-hover: rgba(255,255,255,0.07);
  --topbar-bg: #172131;
  --topbar-text: #d0dce8;
  --bg: #f4f5f7;
  --surface: #ffffff;
  --bg-card: #ffffff;
  --bg-secondary: #f4f5f7;
  --border: #e0e0e0;
  --text: #1a1a2e;
  --text-muted: #6b7280;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #3b82f6;
  --shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08);
  --radius: 6px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 12px;
}

.card {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
  border: 1px solid var(--border);
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.badge-success { background: #dcfce7; color: #15803d; }
.badge-error   { background: #fee2e2; color: #b91c1c; }

.table-wrapper {
  overflow-x: auto;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}

table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
}
thead tr { background: #f8f9fa; }
th {
  padding: 10px 14px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  vertical-align: middle;
}
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background: #fafafa; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  border: none;
  text-decoration: none;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: #f3f4f6; color: var(--text); border: 1px solid var(--border); }
.btn-secondary:hover { background: #e5e7eb; text-decoration: none; }
.btn-sm { padding: 4px 10px; font-size: 12px; }

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 5px;
  color: var(--text);
}
.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--text);
  background: var(--surface);
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
}
.form-control:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(212,0,0,0.1);
}

.alert {
  padding: 10px 16px;
  border-radius: var(--radius);
  font-size: 13px;
  margin-bottom: 16px;
}
.alert-error { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.mb-4 { margin-bottom: 16px; }
.mt-4 { margin-top: 16px; }
.text-muted { color: var(--text-muted); }
.text-sm { font-size: 12px; }

.pagination { display: flex; gap: 4px; align-items: center; margin-top: 16px; }
.page-btn {
  padding: 5px 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s;
}
.page-btn:hover { background: #f3f4f6; }
.page-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
