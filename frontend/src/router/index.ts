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

  // 模板，第五阶段迁移
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
    component: () => import('@/pages/templates/TemplateFormPage.vue'),
    meta: { requiresAuth: true, title: '新建模板' },
  },
  {
    path: '/templates/:id/edit',
    component: () => import('@/pages/templates/TemplateFormPage.vue'),
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

  // 发送历史，第五阶段迁移
  {
    path: '/history',
    component: () => import('@/pages/history/HistoryListPage.vue'),
    meta: { requiresAuth: true, title: '发送历史' },
  },
  {
    path: '/history/:id',
    component: () => import('@/pages/history/HistoryDetailPage.vue'),
    meta: { requiresAuth: true, title: '发送历史详情' },
  },

  // Webhook 日志，第五阶段迁移
  {
    path: '/logs',
    component: () => import('@/pages/logs/LogListPage.vue'),
    meta: { requiresAuth: true, title: '请求日志' },
  },
  {
    path: '/logs/:id',
    component: () => import('@/pages/logs/LogDetailPage.vue'),
    meta: { requiresAuth: true, title: '请求日志详情' },
  },
  {
    path: '/subscriptions',
    component: () => import('@/pages/subscriptions/SubscriptionListPage.vue'),
    meta: { requiresAuth: true, title: '共享订阅' },
  },
  {
    path: '/subscriptions/:id/edit',
    component: () => import('@/pages/subscriptions/SubscriptionFormPage.vue'),
    meta: { requiresAuth: true, title: '订阅配置' },
  },
  {
    path: '/admin/users',
    component: () => import('@/pages/admin/UserListPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '用户管理' },
  },
  {
    path: '/admin/channels/:id/share',
    component: () => import('@/pages/admin/ShareChannelPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '共享频道' },
  },
  {
    path: '/admin/notifiers/:id/share',
    component: () => import('@/pages/admin/ShareNotifierPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '共享通知渠道' },
  },
  {
    path: '/admin/templates/:id/share',
    component: () => import('@/pages/admin/ShareTemplatePage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '共享模板' },
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