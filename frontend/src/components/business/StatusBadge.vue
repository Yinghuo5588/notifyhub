<script setup lang="ts">
const props = defineProps<{
  status: string
}>()

function text() {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    rate_limited: '限频',
    filtered: '过滤',
    pending: '处理中',
  }

  return map[props.status] || props.status
}

function cls() {
  if (props.status === 'success') return 'badge-green'
  if (props.status === 'failed') return 'badge-red'
  if (props.status === 'rate_limited') return 'badge-yellow'
  if (props.status === 'filtered') return 'badge-gray'
  return 'badge-blue'
}
</script>

<template>
  <span class="badge" :class="cls()">
    {{ text() }}
  </span>
</template>