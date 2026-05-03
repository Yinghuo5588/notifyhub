<script setup lang="ts">
import { computed } from 'vue'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const colorMap = computed(() => ({
  success: 'bg-emerald-500',
  error: 'bg-rose-500',
  warning: 'bg-amber-500',
  info: 'bg-sky-500',
}))
</script>

<template>
  <div class="fixed top-4 right-4 z-50 space-y-2">
    <div
      v-for="item in toast.items"
      :key="item.id"
      class="toast-enter text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 min-w-64 max-w-sm text-sm"
      :class="colorMap[item.type]"
    >
      <span v-if="item.type === 'success'">✅</span>
      <span v-else-if="item.type === 'error'">❌</span>
      <span v-else-if="item.type === 'warning'">⚠️</span>
      <span v-else>ℹ️</span>

      <span class="flex-1">{{ item.message }}</span>

      <button
        type="button"
        class="text-white/80 hover:text-white ml-2 text-lg leading-none"
        @click="toast.remove(item.id)"
      >
        ×
      </button>
    </div>
  </div>
</template>