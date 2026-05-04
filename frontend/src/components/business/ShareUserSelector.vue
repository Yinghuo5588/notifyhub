<script setup lang="ts">
import type { ShareUserItem } from '@/types/admin'

const props = defineProps<{
  users: ShareUserItem[]
  selectedIds: number[]
}>()

const emit = defineEmits<{
  update: [ids: number[]]
}>()

function toggle(id: number) {
  if (props.selectedIds.includes(id)) {
    emit('update', props.selectedIds.filter(item => item !== id))
  } else {
    emit('update', [...props.selectedIds, id])
  }
}

function toggleAll() {
  if (props.selectedIds.length === props.users.length) {
    emit('update', [])
  } else {
    emit('update', props.users.map(item => item.id))
  }
}
</script>

<template>
  <div class="form-card">
    <div class="flex items-center justify-between gap-3 mb-4">
      <h3 class="text-lg font-semibold" style="color: var(--text)">
        共享给以下用户
      </h3>

      <button type="button" class="btn btn-ghost sm:w-auto" @click="toggleAll">
        全选 / 取消
      </button>
    </div>

    <div v-if="users.length" class="space-y-2 max-h-96 overflow-y-auto">
      <label
        v-for="u in users"
        :key="u.id"
        class="flex items-center justify-between gap-3 p-3 rounded-2xl cursor-pointer"
        style="border: 1px solid var(--line)"
      >
        <div class="flex items-center gap-3">
          <input
            type="checkbox"
            class="w-4 h-4"
            :checked="selectedIds.includes(u.id)"
            @change="toggle(u.id)"
          >

          <div>
            <div class="text-sm font-medium" style="color: var(--text)">
              {{ u.username }}
            </div>

            <div v-if="u.email" class="text-xs" style="color: var(--muted)">
              {{ u.email }}
            </div>
          </div>

          <span v-if="!u.is_active" class="badge badge-red">
            已禁用
          </span>
        </div>

        <div v-if="u.sends_today !== undefined" class="text-xs" style="color: var(--muted)">
          今日 {{ u.sends_today }}
          <span v-if="u.subscription_active" class="text-emerald-400 ml-1">活跃</span>
          <span v-else-if="u.selected" class="ml-1">未激活</span>
        </div>
      </label>
    </div>

    <p v-else class="helper-text text-sm">
      暂无其他用户。
    </p>
  </div>
</template>