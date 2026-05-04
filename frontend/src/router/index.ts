import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    component: () => import('@/pages/auth/LoginPage.vue'),
    meta: { public: true, layout: 'auth' },
  },
  {
    path: '/',
    component: () => import('@/pages/dashboard/DashboardPage.vue'),
    meta: { requiresAuth: true },
  },

  // 频道
  {
    path: '/channels',
    component: () => import('@/pages/channels/ChannelListPage.vue'),
    meta: { requiresAuth: true, title: 'Webhook 频道' },
  },
  {
    path: '/channels/new',
    component: () => import('@/pages/channels/ChannelFormPage.vue'),
    meta: { requiresAuth: true, title: '新建频道' },
  },
  {
    path: '/channels/:id/edit',
    component: () => import('@/pages/channels/ChannelFormPage.vue'),
    meta: { requiresAuth: true, title: '编辑频道' },
  },

  // 模板，第五阶段迁移表单
  {
    path: '/templates',
    component: () => import('@/pages/templates/TemplateListPage.vue'),
    meta: { requiresAuth: true, title: '通知模板' },
  },
  {
    path: '/templates/shared',
    component: () => import('@/pages/templates/SharedTemplateListPage.vue'),
    meta: { requiresAuth: true, title: '共享模板' },
  },
  {
    path: '/templates/new',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '新建模板' },
  },
  {
    path: '/templates/:id/edit',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '编辑模板' },
  },

  // 通知渠道
  {
    path: '/notifiers',
    component: () => import('@/pages/notifiers/NotifierListPage.vue'),
    meta: { requiresAuth: true, title: '通知渠道' },
  },
  {
    path: '/notifiers/new',
    component: () => import('@/pages/notifiers/NotifierFormPage.vue'),
    meta: { requiresAuth: true, title: '新建通知渠道' },
  },
  {
    path: '/notifiers/:id/edit',
    component: () => import('@/pages/notifiers/NotifierFormPage.vue'),
    meta: { requiresAuth: true, title: '编辑通知渠道' },
  },

  // 设置
  {
    path: '/settings',
    component: () => import('@/pages/settings/SettingsPage.vue'),
    meta: { requiresAuth: true, title: '系统设置' },
  },

  // 第四阶段尚未迁移
  {
    path: '/history',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '发送历史' },
  },
  {
    path: '/history/:id',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '发送历史详情' },
  },
  {
    path: '/logs',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '请求日志' },
  },
  {
    path: '/logs/:id',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '请求日志详情' },
  },
  {
    path: '/subscriptions',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '共享订阅' },
  },
  {
    path: '/subscriptions/:id/edit',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '订阅配置' },
  },
  {
    path: '/admin/users',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '用户管理' },
  },

  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async to => {
  const auth = useAuthStore()

  if (to.meta.public) return true

  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      return '/login'
    }
  }

  if (to.meta.requiresAdmin && !auth.user?.is_admin) {
    return '/'
  }

  return true
})

export default router