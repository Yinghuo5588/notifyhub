<script setup lang="ts">
import {
  Bell,
  FileText,
  History,
  Home,
  LogOut,
  Radio,
  Settings,
  Users,
  Webhook,
} from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const navItems = [
  { label: '仪表盘', path: '/', icon: Home },
  { label: 'Webhook 频道', path: '/channels', icon: Webhook },
  { label: '通知模板', path: '/templates', icon: FileText },
  { label: '通知渠道', path: '/notifiers', icon: Bell },
  { label: '发送历史', path: '/history', icon: History },
  { label: '请求日志', path: '/logs', icon: Radio },
  { label: '系统设置', path: '/settings', icon: Settings },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

async function logout() {
  try {
    await auth.logout()
    toast.success('已退出登录')
    router.push('/login')
  } catch {
    auth.clearUser()
    router.push('/login')
  }
}
</script>

<template>
  <aside
    class="hidden lg:flex w-72 shrink-0 flex-col min-h-screen"
    style="background: linear-gradient(180deg, var(--panel-strong), var(--panel)); border-right: 1px solid var(--line); box-shadow: var(--shadow-soft);"
  >
    <div class="p-5 border-b" style="border-color: var(--line);">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold" style="color: var(--text)">
            NotifyHub
          </h1>
          <p class="text-xs mt-2" style="color: var(--muted)">
            Webhook 通知中继 · 控制与分发中心
          </p>
        </div>

        <ThemeToggle />
      </div>
    </div>

    <nav class="flex-1 py-4 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 mx-3 my-1 px-4 py-3 rounded-[18px] text-sm font-semibold transition no-underline"
        :class="isActive(item.path) ? 'bg-white/50 dark:bg-white/10' : 'hover:bg-white/30'"
        style="color: var(--text);"
      >
        <component :is="item.icon" class="w-5 h-5 text-brand" />
        <span>{{ item.label }}</span>
      </RouterLink>

      <RouterLink
        v-if="auth.user?.is_admin"
        to="/admin/users"
        class="flex items-center gap-3 mx-3 my-1 px-4 py-3 rounded-[18px] text-sm font-semibold transition no-underline hover:bg-white/30"
        :class="route.path.startsWith('/admin') ? 'bg-white/50 dark:bg-white/10' : ''"
        style="color: var(--text);"
      >
        <Users class="w-5 h-5 text-brand" />
        <span>用户管理</span>
      </RouterLink>

      <RouterLink
        v-if="!auth.user?.is_admin"
        to="/subscriptions"
        class="flex items-center gap-3 mx-3 my-1 px-4 py-3 rounded-[18px] text-sm font-semibold transition no-underline hover:bg-white/30"
        :class="route.path.startsWith('/subscriptions') ? 'bg-white/50 dark:bg-white/10' : ''"
        style="color: var(--text);"
      >
        <Radio class="w-5 h-5 text-brand" />
        <span>共享订阅</span>
      </RouterLink>
    </nav>

    <div class="p-4 border-t" style="border-color: var(--line);">
      <div class="glass-panel rounded-2xl px-4 py-3 flex items-center justify-between gap-3">
        <div class="min-w-0">
          <div class="font-medium text-sm truncate" style="color: var(--text)">
            {{ auth.user?.username }}
          </div>
          <div class="text-xs" style="color: var(--muted)">
            {{ auth.user?.is_admin ? '管理员' : '普通用户' }}
          </div>
        </div>

        <button
          type="button"
          class="inline-flex items-center gap-1 text-sm shrink-0"
          style="color: var(--muted)"
          @click="logout"
        >
          <LogOut class="w-4 h-4" />
          退出
        </button>
      </div>
    </div>
  </aside>
</template>