<template>
  <div>
    <div class="header">
      <TitlePage title="Dashboard" />
        <button class="btn btn-secondary btn-sm" @click="fetchDataDashboard" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>↻</span> Refresh
        </button>
    </div>

<!-- {{ data }} -->
    <!-- Global health bar -->
    <div v-if="data" class="health-bar">
      <div class="health-indicator">
        <strong>{{ data?.healthy ?? 0 }} de {{ data?.total_instances ?? 0 }} instâncias saudáveis</strong>
      </div>
      <div class="health-stats">
        <div class="health-stat">
          <span class="badge badge-online">● Online</span>
          <strong>{{ data?.healthy ?? 0 }}</strong>
        </div>
        <div class="health-stat">
          <span class="badge badge-slow">● Lentas</span>
          <strong>{{ data?.degraded ?? 0 }}</strong>
        </div>
        <div class="health-stat">
          <span class="badge badge-offline">● Offline</span>
          <strong>{{ data?.offline ?? 0 }}</strong>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="alert alert-error">
      {{ error }}
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !data" class="card-grid">
      <div v-for="i in 4" :key="i" class="instance-card skeleton">
        <div class="skeleton-line" style="height: 16px; margin-bottom: 12px"></div>
        <div class="skeleton-line" style="height: 12px; margin-bottom: 8px; width: 60%"></div>
        <div class="skeleton-line" style="height: 12px; width: 40%"></div>
      </div>
    </div>

    <!-- Instance cards -->
    <div v-if="data" class="card-grid">
      <div
        v-for="inst in data?.instances ?? []"
        :key="inst.id"
        class="instance-card"
        @click="goToHosts(inst.id)"
        role="button"
        tabindex="0"
      >
        <div class="instance-card-header">
          <span class="instance-card-name">{{ inst.name }}</span>
          <span v-html="statusBadge(inst.status)" class="status-badge"></span>
        </div>
        <div class="instance-card-body">
          <div class="instance-card-row">
            <span>Versão</span>
            <strong>{{ inst.zabbix_version || '—' }}</strong>
          </div>
          <div class="instance-card-row">
            <span>Hosts</span>
            <strong>{{ inst.total_hosts ?? '—' }}</strong>
          </div>
          <div class="instance-card-row">
            <span>Problemas</span>
            <strong :style="inst.hosts_in_problem > 0 ? 'color: var(--danger)' : ''">
              {{ inst.hosts_in_problem ?? '—' }}
            </strong>
          </div>
          <div class="instance-card-row">
            <span>Latência</span>
            <strong v-html="latencyLabel(inst.latency_ms)"></strong>
          </div>
          <div v-if="inst.error" class="instance-card-error">
            {{ inst.error }}
          </div>
        </div>
      </div>

      <!-- Add new instance card -->
      <router-link to="/instances/new" class="instance-card add-card">
        <div class="add-card-content">
          <div class="add-icon">+</div>
          <div>Nova Instância</div>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import TitlePage from '@/components/ui/TitlePage.vue'

const router = useRouter()
const { client } = useApi()

const data = ref(null)
const loading = ref(false)
const error = ref('')

const fetchDataDashboard = async () => {
  loading.value = true
  error.value = ''
  try {
    const  response  = await client.get('/dashboard')
    data.value = response?.data
  } catch (e) {
    console.error('Dashboard error:', e)
    error.value = e?.response?.data?.detail || e?.message || 'Erro ao carregar dashboard'
  } finally {
    loading.value = false
    if (!data.value) {
      error.value = 'Nenhum dado disponível'
    }
  }
}

const goToHosts = (instanceId) => {
  router.push(`/hosts?instance_id=${instanceId}`)
}

const statusBadge = (status) => {
  const statusMap = {
    online: '<span class="badge badge-online">● Online</span>',
    degraded: '<span class="badge badge-slow">● Lentas</span>',
    offline: '<span class="badge badge-offline">● Offline</span>'
  }
  return statusMap[status] || '<span class="badge">Unknown</span>'
}

const latencyLabel = (latencyMs) => {
  if (!latencyMs) return '—'
  if (latencyMs < 100) return `<span style="color: var(--success)">${latencyMs}ms</span>`
  if (latencyMs < 500) return `<span style="color: var(--warning)">${latencyMs}ms</span>`
  return `<span style="color: var(--danger)">${latencyMs}ms</span>`
}

onMounted(() => {
  fetchDataDashboard()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--text);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-top-color: var(--text);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.health-bar {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.health-indicator {
  font-size: 16px;
  font-weight: 500;
}

.health-stats {
  display: flex;
  gap: 24px;
}

.health-stat {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 3px;
}

.badge-online {
  color: var(--success);
}

.badge-slow {
  color: var(--warning);
}

.badge-offline {
  color: var(--danger);
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 24px;
}

.alert-error {
  background: #fee;
  border: 1px solid #fcc;
  color: var(--danger);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.instance-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.instance-card:hover:not(.add-card) {
  border-color: var(--text);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.instance-card.skeleton {
  cursor: default;
  opacity: 0.4;
}

.skeleton-line {
  background: #e0e0e0;
  border-radius: 4px;
}

.instance-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.instance-card-name {
  font-weight: 600;
  font-size: 16px;
}

.status-badge {
  font-size: 12px;
}

.instance-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.instance-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.instance-card-row span {
  color: var(--text-muted);
}

.instance-card-row strong {
  color: var(--text);
  font-weight: 600;
}

.instance-card-error {
  font-size: 11px;
  color: var(--danger);
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.add-card {
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--text-muted);
  border: 2px dashed var(--border);
  min-height: 140px;
  transition: all 0.2s;
}

.add-card:hover {
  border-color: var(--text);
  color: var(--text);
  background: var(--bg-hover);
}

.add-card-content {
  text-align: center;
}

.add-icon {
  font-size: 28px;
  margin-bottom: 8px;
  font-weight: 300;
}
</style>
