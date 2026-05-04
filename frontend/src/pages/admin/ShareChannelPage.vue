<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useMutation, useQuery } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { Save } from 'lucide-vue-next'

import { getShareChannelApi, saveShareChannelApi } from '@/api/admin'
import { getErrorMessage } from '@/api/http'
import ShareUserSelector from '@/components/business/ShareUserSelector.vue'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const channelId = computed(() => Number(route.params.id))
const selectedIds = ref<number[]>([])

const limits = reactive({
  per_hour_limit: 10,
  per_day_limit: 50,
  min_interval: 30,
  global_hour_limit: 100,
  global_day_limit: 500,
})

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['share-channel', channelId.value]),
  queryFn: () => getShareChannelApi(channelId.value),
})

watch(
  data,
  value => {
    if (!value) return

    selectedIds.value = value.users.filter(u => u.selected).map(u => u.id)

    limits.per_hour_limit = value.channel.per_hour_limit
    limits.per_day_limit = value.channel.per_day_limit
    limits.min_interval = value.channel.min_interval
    limits.global_hour_limit = value.channel.global_hour_limit
    limits.global_day_limit = value.channel.global_day_limit
  },
  { immediate: true },
)

const saveMutation = useMutation({
  mutationFn: () =>
    saveShareChannelApi(channelId.value, {
      user_ids: selectedIds.value,
      ...limits,
    }),
  onSuccess: () => {
    toast.success('共享设置已保存')
    router.push('/channels')
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col gap-3">
        <RouterLink to="/channels" class="text-sm text-brand hover:underline">
          返回频道列表
        </RouterLink>

        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Share Channel
          </div>

          <h2 class="page-title mt-2">
            共享频道
          </h2>

          <p class="page-subtitle">
            {{ data?.channel.name || '' }}
          </p>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载共享设置...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        共享设置加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else-if="data" class="grid grid-cols-1 lg:grid-cols-2 gap-4 max-w-6xl">
      <ShareUserSelector
        :users="data.users"
        :selected-ids="selectedIds"
        @update="ids => selectedIds = ids"
      />

      <div class="form-card">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
          频率限制
        </h3>

        <div class="space-y-4">
          <div class="border-b pb-4" style="border-color: var(--line)">
            <p class="text-xs mb-3" style="color: var(--muted)">
              每用户限制
            </p>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label>每小时上限</label>
                <input v-model.number="limits.per_hour_limit" type="number" min="1">
              </div>

              <div>
                <label>每日上限</label>
                <input v-model.number="limits.per_day_limit" type="number" min="1">
              </div>
            </div>

            <div class="mt-3">
              <label>最小发送间隔，秒</label>
              <input v-model.number="limits.min_interval" type="number" min="0">
            </div>
          </div>

          <div>
            <p class="text-xs mb-3" style="color: var(--muted)">
              全局限制，所有用户合计
            </p>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label>全局每小时上限</label>
                <input v-model.number="limits.global_hour_limit" type="number" min="1">
              </div>

              <div>
                <label>全局每日上限</label>
                <input v-model.number="limits.global_day_limit" type="number" min="1">
              </div>
            </div>
          </div>

          <button
            type="button"
            class="btn btn-primary"
            :disabled="saveMutation.isPending.value"
            @click="saveMutation.mutate()"
          >
            <Save class="w-4 h-4" />
            {{ saveMutation.isPending.value ? '保存中...' : '保存共享设置' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>