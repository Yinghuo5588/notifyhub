<script setup lang="ts">
const props = defineProps<{
  page: number
  totalPages: number
  total?: number
}>()

const emit = defineEmits<{
  change: [page: number]
}>()

function go(page: number) {
  if (page < 1) return
  if (page > props.totalPages) return
  if (page === props.page) return
  emit('change', page)
}
</script>

<template>
  <div
    v-if="totalPages > 1"
    class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4"
  >
    <div class="text-xs" style="color: var(--muted)">
      共 {{ total || 0 }} 条，第 {{ page }} / {{ totalPages }} 页
    </div>

    <div class="flex items-center gap-2">
      <button
        type="button"
        class="btn btn-secondary sm:w-auto"
        :disabled="page <= 1"
        @click="go(page - 1)"
      >
        上一页
      </button>

      <button
        type="button"
        class="btn btn-secondary sm:w-auto"
        :disabled="page >= totalPages"
        @click="go(page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>