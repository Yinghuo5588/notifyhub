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
  {
    path: '/channels',
    component: () => import('@/pages/channels/ChannelListPage.vue'),
    meta: { requiresAuth: true, title: 'Webhook 频道' },
  },
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
    path: '/notifiers',
    component: () => import('@/pages/notifiers/NotifierListPage.vue'),
    meta: { requiresAuth: true, title: '通知渠道' },
  },
  {
    path: '/settings',
    component: () => import('@/pages/settings/SettingsPage.vue'),
    meta: { requiresAuth: true, title: '系统设置' },
  },

  // 第三阶段尚未迁移的复杂页面，继续占位
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
    path: '/admin/users',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '用户管理' },
  },

  // 新建/编辑复杂表单暂时走旧页面
  {
    path: '/channels/new',
    beforeEnter() {
      window.location.href = '/channels/new'
      return false
    },
  },
  {
    path: '/channels/:id/edit',
    beforeEnter(to) {
      window.location.href = `/channels/${to.params.id}/edit`
      return false
    },
  },
  {
    path: '/templates/new',
    beforeEnter() {
      window.location.href = '/templates/new'
      return false
    },
  },
  {
    path: '/templates/:id/edit',
    beforeEnter(to) {
      window.location.href = `/templates/${to.params.id}/edit`
      return false
    },
  },
  {
    path: '/notifiers/new',
    beforeEnter() {
      window.location.href = '/notifiers/new'
      return false
    },
  },
  {
    path: '/notifiers/:id/edit',
    beforeEnter(to) {
      window.location.href = `/notifiers/${to.params.id}/edit`
      return false
    },
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