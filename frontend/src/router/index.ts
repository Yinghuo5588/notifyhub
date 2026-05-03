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
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: 'Webhook 频道' },
  },
  {
    path: '/templates',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '通知模板' },
  },
  {
    path: '/templates/shared',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '共享模板' },
  },
  {
    path: '/notifiers',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '通知渠道' },
  },
  {
    path: '/history',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '发送历史' },
  },
  {
    path: '/history/:id',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '历史详情' },
  },
  {
    path: '/logs',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '请求日志' },
  },
  {
    path: '/logs/:id',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '日志详情' },
  },
  {
    path: '/subscriptions',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '共享订阅' },
  },
  {
    path: '/settings',
    component: () => import('@/pages/PlaceholderPage.vue'),
    meta: { requiresAuth: true, title: '系统设置' },
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