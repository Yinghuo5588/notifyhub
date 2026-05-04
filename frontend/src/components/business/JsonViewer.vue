<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChevronDown, ChevronUp, Copy } from 'lucide-vue-next'

import { copyText } from '@/utils/format'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{
  value: unknown
  title?: string
  maxHeight?: string
  defaultCollapsed?: boolean
}>()

const toast = useToastStore()
const collapsed = ref(!!props.defaultCollapsed)

const formatted = computed(() => {
  if (typeof props.value === 'string') {
    try {
      return JSON.stringify(JSON.parse(props.value), null, 2)
    } catch {
      return props.value
    }
  }

  try {
    return JSON.stringify(props.value, null, 2)
  } catch {
    return String(props.value)
  }
})

async function copy() {
  await copyText(formatted.value)
  toast.success('已复制')
}
</script>

<template>
  <div class="form-card">
    <div class="flex items-center justify-between gap-3 mb-3">
      <h3 class="text-lg font-semibold" style="color: var(--text)">
        {{ title || 'JSON' }}
      </h3>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="btn btn-secondary sm:w-auto"
          @click="collapsed = !collapsed"
        >
          <ChevronDown v-if="collapsed" class="w-4 h-4" />
          <ChevronUp v-else class="w-4 h-4" />
          {{ collapsed ? '展开' : '收起' }}
        </button>

        <button
          type="button"
          class="btn btn-ghost sm:w-auto"
          @click="copy"
        >
          <Copy class="w-4 h-4" />
          复制
        </button>
      </div>
    </div>

    <pre
      v-show="!collapsed"
      class="rounded-2xl bg-black/30 p-4 overflow-x-auto text-xs leading-relaxed"
      :style="{
        color: 'var(--text)',
        maxHeight: maxHeight || '420px',
      }"
    >{{ formatted }}</pre>
  </div>
</template>