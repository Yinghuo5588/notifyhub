<script setup lang="ts">
import { Moon, Sun } from 'lucide-vue-next'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <div class="inline-flex items-center gap-1 rounded-full border px-1 py-1 glass-panel">
    <button
      type="button"
      class="rounded-full px-3 py-2 text-sm"
      :class="theme.theme === 'light' ? 'bg-white/80' : 'text-muted'"
      @click="theme.setTheme('light')"
    >
      <Sun class="w-4 h-4" />
    </button>

    <button
      type="button"
      class="rounded-full px-3 py-2 text-sm"
      :class="theme.theme === 'dark' ? 'bg-white/10' : 'text-muted'"
      @click="theme.setTheme('dark')"
    >
      <Moon class="w-4 h-4" />
    </button>
  </div>
</template>