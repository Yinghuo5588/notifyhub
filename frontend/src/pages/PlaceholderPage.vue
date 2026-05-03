<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Bell,
  Construction,
  FileText,
  History,
  Radio,
  Settings,
  Users,
  Webhook,
} from 'lucide-vue-next'

const route = useRoute()

const title = computed(() => {
  return String(route.meta.title || '页面')
})

const icon = computed(() => {
  const path = route.path

  if (path.startsWith('/channels')) return Webhook
  if (path.startsWith('/templates')) return FileText
  if (path.startsWith('/notifiers')) return Bell
  if (path.startsWith('/history')) return History
  if (path.startsWith('/logs')) return Radio
  if (path.startsWith('/subscriptions')) return Radio
  if (path.startsWith('/settings')) return Settings
  if (path.startsWith('/admin')) return Users

  return Construction
})
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div>
        <div
          class="text-xs uppercase tracking-[0.28em]"
          style="color: var(--muted)"
        >
          Coming Soon
        </div>

        <h2 class="page-title mt-2">
          {{ title }}
        </h2>

        <p class="page-subtitle">
          这个页面会在后续阶段迁移。当前阶段先保证登录、鉴权、布局、主题和仪表盘闭环。
        </p>
      </div>
    </div>

    <div class="form-card text-center py-12">
      <component
        :is="icon"
        class="w-14 h-14 mx-auto mb-4 text-brand"
      />

      <div class="text-xl font-semibold mb-2" style="color: var(--text)">
        {{ title }} 正在排队迁移
      </div>

      <p class="helper-text max-w-lg mx-auto">
        旧 Jinja2 页面暂时仍然可用。等对应 API 和页面组件完成后，这里会替换为正式 Vue 页面。
      </p>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md mx-auto mt-6">
        <RouterLink to="/" class="btn btn-primary">
          返回仪表盘
        </RouterLink>

        <a
          :href="'http://127.0.0.1:9800' + route.path"
          target="_blank"
          rel="noopener"
          class="btn btn-secondary"
        >
          打开旧页面
        </a>
      </div>
    </div>
  </div>
</template>