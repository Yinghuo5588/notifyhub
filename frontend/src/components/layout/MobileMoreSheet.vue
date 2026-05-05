<script setup lang="ts">
import {
  Bell,
  FileText,
  LogOut,
  Radio,
  Settings,
  Users,
  Moon,
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useThemeStore } from '@/stores/theme'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()
const theme = useThemeStore()
const toast = useToastStore()

async function logout() {
  try {
    await auth.logout()
    toast.success('已退出登录')
  } finally {
    ui.closeMobileMore()
    router.push('/login')
  }
}

function go(path: string) {
  ui.closeMobileMore()
  router.push(path)
}

function toggleTheme() {
  theme.toggleTheme()
  ui.closeMobileMore()
}
</script>

<template>
  <div
    v-if="ui.mobileMoreOpen"
    class="fixed inset-0 bg-black/20 backdrop-blur-sm z-[85] lg:hidden"
    @click="ui.closeMobileMore()"
  />

  <div
    v-if="ui.mobileMoreOpen"
    class="mobile-sheet-enter fixed left-1/2 bottom-[86px] z-[90] w-[min(92vw,420px)] -translate-x-1/2 rounded-[28px] p-4 glass-panel lg:hidden"
  >
    <div class="w-11 h-1.5 rounded-full mx-auto mb-4 bg-slate-400/40" />

    <div class="text-sm font-semibold mb-3 px-1" style="color: var(--text)">
      更多功能
    </div>

    <div class="grid grid-cols-2 gap-3">
      <button class="sheet-btn" type="button" @click="go('/templates')">
        <FileText class="w-4 h-4" />
        <span>通知模板</span>
      </button>

      <button class="sheet-btn" type="button" @click="go('/notifiers')">
        <Bell class="w-4 h-4" />
        <span>通知渠道</span>
      </button>

      <button class="sheet-btn" type="button" @click="go('/logs')">
        <Radio class="w-4 h-4" />
        <span>请求日志</span>
      </button>

      <button class="sheet-btn" type="button" @click="go('/settings')">
        <Settings class="w-4 h-4" />
        <span>设置</span>
      </button>

      <button
        v-if="auth.user?.is_admin"
        class="sheet-btn"
        type="button"
        @click="go('/admin/users')"
      >
        <Users class="w-4 h-4" />
        <span>用户管理</span>
      </button>

      <button
        v-else
        class="sheet-btn"
        type="button"
        @click="go('/subscriptions')"
      >
        <Radio class="w-4 h-4" />
        <span>共享订阅</span>
      </button>

      <button class="sheet-btn" type="button" @click="toggleTheme">
        <Moon class="w-4 h-4" />
        <span>切换主题</span>
      </button>

      <button class="sheet-btn text-rose-400" type="button" @click="logout">
        <LogOut class="w-4 h-4" />
        <span>退出登录</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.sheet-btn {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.9rem 0.9rem;
  border-radius: 22px;
  color: var(--text);
  text-decoration: none;
  background: rgba(255,255,255,0.52);
  border: 1px solid rgba(255,255,255,0.58);
  text-align: left;
  font-weight: 650;
  transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
  -webkit-tap-highlight-color: transparent;
}

.sheet-btn:active {
  transform: scale(0.985);
}

.sheet-btn:hover {
  background: rgba(255,255,255,0.68);
  border-color: rgba(10,132,255,0.18);
}

html[data-theme="dark"] .sheet-btn {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.10);
}

html[data-theme="dark"] .sheet-btn:hover {
  background: rgba(255,255,255,0.09);
}
</style>