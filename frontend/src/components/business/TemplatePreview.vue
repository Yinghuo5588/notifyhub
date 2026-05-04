<script setup lang="ts">
defineProps<{
  subject: string
  body: string
  loading?: boolean
}>()
</script>

<template>
  <div class="form-card">
    <div class="flex items-center justify-between gap-3 mb-4">
      <h3 class="text-lg font-semibold" style="color: var(--text)">
        预览
      </h3>

      <span v-if="loading" class="text-xs" style="color: var(--muted)">
        渲染中...
      </span>
    </div>

    <div class="space-y-4">
      <div>
        <label>标题</label>
        <div
          class="rounded-2xl bg-black/10 p-3 text-sm min-h-[44px]"
          style="color: var(--text)"
        >
          {{ subject || '暂无标题预览' }}
        </div>
      </div>

      <div>
        <label>正文</label>
        <pre
          class="rounded-2xl bg-black/10 p-3 text-sm whitespace-pre-wrap overflow-x-auto min-h-[140px]"
          style="color: var(--text)"
        >{{ body || '暂无正文预览' }}</pre>
      </div>
    </div>
  </div>
</template>