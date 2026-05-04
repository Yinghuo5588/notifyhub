<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Radio, Settings, ToggleLeft, ToggleRight } from 'lucide-vue-next'

import { getSubscriptionsApi, toggleSubscriptionApi } from '@/api/subscriptions'
import { getErrorMessage } from '@/api/http'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const queryClient = useQueryClient()

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['subscriptions'],
  queryFn: getSubscriptionsApi,
})

const toggleMutation = useMutation({
  mutationFn: toggleSubscriptionApi,
  onSuccess: () => {
    toast.success('订阅状态已更新')
    queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div>
        <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
          Subscriptions
        </div>

        <h2 class="page-title mt-2">
          共享订阅
        </h2>

        <p class="page-subtitle">
          管理员共享给你的 Webhook 频道。你可以配置自己的模板、通知渠道和过滤规则。
        </p>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载共享订阅...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        共享订阅加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else-if="data?.length" class="data-list">
      <div
        v-for="sub in data"
        :key="sub.id"
        class="list-card"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <Radio class="w-5 h-5 text-brand" />

              <h3 class="text-lg font-semibold" style="color: var(--text)">
                {{ sub.channel_name || '(已删除频道)' }}
              </h3>

              <span
                class="badge"
                :class="sub.is_active ? 'badge-green' : 'badge-gray'"
              >
                {{ sub.is_active ? '已启用' : '未启用' }}
              </span>
            </div>

            <p v-if="sub.channel_description" class="muted-text text-sm mt-2">
              {{ sub.channel_description }}
            </p>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3 text-xs" style="color: var(--muted)">
              <div>
                模板：
                <span style="color: var(--text)">
                  {{ sub.template_name || '未配置' }}
                </span>
              </div>

              <div>
                通知渠道：
                <span style="color: var(--text)">
                  {{ sub.notifier_name || '未配置' }}
                </span>
              </div>

              <div>
                今日发送：
                <span style="color: var(--text)">
                  {{ sub.sends_today }} / {{ sub.limits?.per_day_limit ?? '?' }}
                </span>
              </div>

              <div>
                本小时：
                <span style="color: var(--text)">
                  {{ sub.sends_this_hour }} / {{ sub.limits?.per_hour_limit ?? '?' }}
                </span>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:flex gap-2 shrink-0">
            <RouterLink :to="`/subscriptions/${sub.id}/edit`" class="btn btn-secondary">
              <Settings class="w-4 h-4" />
              配置
            </RouterLink>

            <button
              type="button"
              class="btn"
              :class="sub.is_active ? 'btn-ghost' : 'btn-secondary'"
              :disabled="toggleMutation.isPending.value"
              @click="toggleMutation.mutate(sub.id)"
            >
              <ToggleRight v-if="sub.is_active" class="w-4 h-4" />
              <ToggleLeft v-else class="w-4 h-4" />
              {{ sub.is_active ? '暂停' : '启用' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state form-card">
      <Radio class="w-14 h-14 mx-auto mb-4 text-brand" />

      <div class="text-lg font-semibold" style="color: var(--text)">
        还没有可用订阅
      </div>

      <p class="page-subtitle">
        等管理员共享频道后，你就可以在这里接管并配置自己的通知流。
      </p>
    </div>
  </div>
</template>