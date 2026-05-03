<script setup lang="ts">
import { Bell, History, Home, MoreHorizontal, Webhook } from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const ui = useUiStore()

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function isMoreActive() {
  return [
    '/templates',
    '/notifiers',
    '/logs',
    '/settings',
    '/subscriptions',
    '/admin',
  ].some(path => route.path.startsWith(path))
}
</script>

<template>
  <nav class="ios-tabbar lg:hidden">
    <RouterLink
      to="/"
      class="ios-tabbar__item"
      :class="{ active: isActive('/') }"
    >
      <Home class="w-4 h-4" />
      <span>首页</span>
    </RouterLink>

    <RouterLink
      to="/channels"
      class="ios-tabbar__item"
      :class="{ active: isActive('/channels') }"
    >
      <Webhook class="w-4 h-4" />
      <span>频道</span>
    </RouterLink>

    <RouterLink
      to="/history"
      class="ios-tabbar__item"
      :class="{ active: isActive('/history') }"
    >
      <History class="w-4 h-4" />
      <span>历史</span>
    </RouterLink>

    <button
      type="button"
      class="ios-tabbar__item"
      :class="{ active: isMoreActive() }"
      @click="ui.toggleMobileMore()"
    >
      <MoreHorizontal class="w-4 h-4" />
      <span>更多</span>
    </button>
  </nav>
</template>