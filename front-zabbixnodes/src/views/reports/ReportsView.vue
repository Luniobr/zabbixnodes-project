<template>
  <div>
    <div class="header">
      <TitlePage title="Relatórios" />
    </div>

    <div class="reports-grid">

      <!-- Health Score -->
      <div class="report-card">
        <div class="report-title">Health Score</div>
        <div class="report-desc">
          Score de saúde (0–100) de todas as instâncias ativas, com breakdown por dimensão.
        </div>
        <button class="btn btn-primary btn-full" @click="generate('health', {})" :disabled="loading.health">
          <span v-if="loading.health" class="spinner"></span>
          Gerar PDF
        </button>
        <div v-if="errors.health" class="report-error">{{ errors.health }}</div>
      </div>

      <!-- Inventário -->
      <div class="report-card">
        <div class="report-title">Inventário de Hosts</div>
        <div class="report-desc">
          Lista completa de hosts com grupos, templates e interfaces de rede.
        </div>
        <div class="form-group">
          <label class="form-label">Instância (opcional)</label>
          <select class="form-control" v-model="filters.inventory.instance_id">
            <option value="">Todas as instâncias</option>
            <option v-for="inst in instances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
          </select>
        </div>
        <button
          class="btn btn-primary btn-full"
          @click="generate('inventory', { instance_id: filters.inventory.instance_id || undefined })"
          :disabled="loading.inventory"
        >
          <span v-if="loading.inventory" class="spinner"></span>
          Gerar PDF
        </button>
        <div v-if="errors.inventory" class="report-error">{{ errors.inventory }}</div>
      </div>

      <!-- Triggers -->
      <div class="report-card">
        <div class="report-title">Triggers Ativas</div>
        <div class="report-desc">
          Problemas ativos no momento, filtrados por instância e severidade mínima.
        </div>
        <div class="filter-row">
          <div class="form-group" style="flex: 1">
            <label class="form-label">Instância</label>
            <select class="form-control" v-model="filters.triggers.instance_id">
              <option value="">Todas</option>
              <option v-for="inst in instances" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
            </select>
          </div>
          <div class="form-group" style="min-width: 110px">
            <label class="form-label">Severidade mín.</label>
            <select class="form-control" v-model="filters.triggers.min_severity">
              <option value="0">Todas</option>
              <option value="2">Warning</option>
              <option value="3">Average</option>
              <option value="4">High</option>
              <option value="5">Disaster</option>
            </select>
          </div>
        </div>
        <button
          class="btn btn-primary btn-full"
          @click="generate('triggers', {
            instance_id: filters.triggers.instance_id || undefined,
            min_severity: filters.triggers.min_severity
          })"
          :disabled="loading.triggers"
        >
          <span v-if="loading.triggers" class="spinner"></span>
          Gerar PDF
        </button>
        <div v-if="errors.triggers" class="report-error">{{ errors.triggers }}</div>
      </div>

      <!-- Auditoria -->
      <div class="report-card">
        <div class="report-title">Auditoria</div>
        <div class="report-desc">
          Log de ações realizadas na plataforma. Restrito a superadmin. Máximo de 500 registros.
        </div>
        <div class="filter-row">
          <div class="form-group" style="flex: 1">
            <label class="form-label">De</label>
            <input type="date" class="form-control" v-model="filters.audit.date_from" />
          </div>
          <div class="form-group" style="flex: 1">
            <label class="form-label">Até</label>
            <input type="date" class="form-control" v-model="filters.audit.date_to" />
          </div>
        </div>
        <button
          class="btn btn-primary btn-full"
          @click="generate('audit', {
            date_from: filters.audit.date_from || undefined,
            date_to: filters.audit.date_to || undefined
          })"
          :disabled="loading.audit"
        >
          <span v-if="loading.audit" class="spinner"></span>
          Gerar PDF
        </button>
        <div v-if="errors.audit" class="report-error">{{ errors.audit }}</div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import TitlePage from '@/components/ui/TitlePage.vue'

const { client } = useApi()

const instances = reactive([])

const loading = reactive({ health: false, inventory: false, triggers: false, audit: false })
const errors  = reactive({ health: '',    inventory: '',    triggers: '',    audit: ''    })

const filters = reactive({
  inventory: { instance_id: '' },
  triggers:  { instance_id: '', min_severity: '0' },
  audit:     { date_from: '', date_to: '' },
})

async function init() {
  try {
    const { data } = await client.get('/instances')
    instances.splice(0, instances.length, ...data.filter(i => i.is_active))
  } catch (_) {}
}

async function generate(type, params) {
  loading[type] = true
  errors[type] = ''
  try {
    // Remove undefined/empty values from params
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    )

    const response = await client.get(`/reports/${type}`, {
      params: cleanParams,
      responseType: 'blob',
    })

    // Extract filename from Content-Disposition header
    const cd = response.headers['content-disposition'] || ''
    const match = cd.match(/filename="([^"]+)"/)
    const filename = match ? match[1] : `zabbixnodes_${type}.pdf`

    // Trigger browser download
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    // axios wraps blob errors — try to parse the JSON error message
    if (e.response?.data instanceof Blob) {
      try {
        const text = await e.response.data.text()
        const json = JSON.parse(text)
        errors[type] = json.detail || `HTTP ${e.response.status}`
      } catch (_) {
        errors[type] = `HTTP ${e.response?.status || 'Erro'}`
      }
    } else {
      errors[type] = e?.response?.data?.detail || e?.message || 'Erro ao gerar relatório'
    }
  } finally {
    loading[type] = false
  }
}

onMounted(init)
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.report-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-title {
  font-size: 16px;
  font-weight: 600;
}

.report-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

.report-error {
  font-size: 12px;
  color: var(--danger);
}

.filter-row {
  display: flex;
  gap: 8px;
}

.form-group { margin: 0; }

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 5px;
}

.form-control {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary, #d40000);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

.btn-primary {
  background: var(--primary, #d40000);
  color: #fff;
  border-color: var(--primary, #d40000);
}
.btn-primary:hover:not(:disabled) { opacity: 0.85; background: var(--primary, #d40000); }

.btn-full { width: 100%; }

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
</style>
