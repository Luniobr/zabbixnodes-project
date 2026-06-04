import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layout/AppLayout.vue'),
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'instances',
          name: 'instances',
          component: () => import('@/views/instances/InstancesListView.vue'),
        },
        {
          path: 'instances/new',
          name: 'instance-new',
          component: () => import('@/views/instances/InstanceFormView.vue'),
        },
        {
          path: 'instances/:id/edit',
          name: 'instance-edit',
          component: () => import('@/views/instances/InstanceFormView.vue'),
        },
        {
          path: 'instance-groups',
          name: 'instance-groups',
          component: () => import('@/views/instance_groups/InstanceGroupsListView.vue'),
        },
        {
          path: 'hosts',
          name: 'hosts',
          component: () => import('@/views/hosts/HostsListView.vue'),
        },
        {
          path: 'host-groups',
          name: 'host-groups',
          component: () => import('@/views/host_groups/HostGroupsListView.vue'),
        },
        {
          path: 'proxies',
          name: 'proxies',
          component: () => import('@/views/proxies/ProxiesListView.vue'),
        },
        {
          path: 'templates',
          name: 'templates',
          component: () => import('@/views/templates/TemplatesListView.vue'),
        },
        {
          path: 'triggers',
          name: 'triggers',
          component: () => import('@/views/triggers/TriggersListView.vue'),
        },
        {
          path: 'compliance',
          name: 'compliance',
          component: () => import('@/views/compliance/ComplianceView.vue'),
        },
        {
          path: 'orchestration',
          name: 'orchestration',
          component: () => import('@/views/orchestration/OrchestrationView.vue'),
        },
        {
          path: 'health',
          name: 'health',
          component: () => import('@/views/health/HealthView.vue'),
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/reports/ReportsView.vue'),
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/users/UsersListView.vue'),
        },
        {
          path: 'audit',
          name: 'audit',
          component: () => import('@/views/audit/AuditListView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('useAuth')

  if (!token && !to.meta.public) {
    return { name: 'login' }
  }

  if (token && to.meta.public) {
    return { name: 'dashboard' }
  }
})
export default router
