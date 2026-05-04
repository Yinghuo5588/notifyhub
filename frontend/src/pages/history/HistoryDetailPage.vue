<script setup lang="ts">
import { computed } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { useRoute } from 'vue-router'
import { RefreshCw } from 'lucide-vue-next'

import { getHistoryDetailApi, resendHistoryApi } from '@/api/history'
import { getErrorMessage } from '@/api/http'
import JsonViewer from '@/components/business/JsonViewer.vue'
import StatusBadge from '@/components/business/StatusBadge.vue'
import { useToastStore } from '@/stores/toast'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const toast = useToastStore()
const queryClient = useQueryClient()

const itemId = computed(() => Number(route.params.id))

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['history-detail', itemId.value]),
  queryFn: () => getHistoryDetailApi(itemId.value),
})

const resendMutation = useMutation({
  mutationFn: () => resendHistoryApi(itemId.value),
  onSuccess: result => {
    if (result.ok) {
      toast.success(result.msg || '重发成功')
    } else {
      toast.error(result.msg || '重发失败')
    }

    queryClient.invalidateQueries({ queryKey: ['history'] })
    queryClient.invalidateQueries({ queryKey: ['history-detail', itemId.value] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

function resend() {
  if (!window.confirm('确定重新发送此通知？')) return
  resendMutation.mutate()
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col gap-3">
        <RouterLink to="/history" class="text-sm text-brand hover:underline">
          返回发送历史
        </RouterLink>

        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            History Detail
          </div>

          <h2 class="page-title mt-2">
            通知详情 #{{ itemId }}
          </h2>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载通知详情...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        通知详情加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else-if="data" class="max-w-4xl space-y-4">
      <div class="form-card">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
          基本信息
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span style="color: var(--muted)">状态</span>
            <span class="ml-2">
              <StatusBadge :status="data.status" />
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">通知类型</span>
            <span class="ml-2" style="color: var(--text)">
              {{ data.notifier_type }}
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">频道</span>
            <span class="ml-2" style="color: var(--text)">
              {{ data.channel_name || '未知频道' }}
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">发送时间</span>
            <span class="ml-2" style="color: var(--text)">
              {{ formatDateTime(data.created_at) }}
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">重试次数</span>
            <span class="ml-2" style="color: var(--text)">
              {{ data.retry_count }}
            </span>
          </div>
        </div>

        <div
          v-if="data.error_message"
          class="mt-4 rounded-2xl border border-rose-400/20 bg-rose-500/10 p-3 text-sm text-rose-300"
        >
          {{ data.error_message }}
        </div>
      </div>

      <div class="form-card">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
          通知内容
        </h3>

        <div class="space-y-4">
          <div>
            <label>标题</label>
            <div
              class="rounded-2xl bg-black/10 p-3 text-sm"
              style="color: var(--text)"
            >
              {{ data.subject || '(无标题)' }}
            </div>
          </div>

          <div>
            <label>正文</label>
            <pre
              class="rounded-2xl bg-black/10 p-3 text-sm whitespace-pre-wrap overflow-x-auto"
              style="color: var(--text)"
            >{{ data.body }}</pre>
          </div>
        </div>
      </div>

      <div v-if="data.webhook_log" class="form-card">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
          关联 Webhook 请求
        </h3>

        <div class="text-sm space-y-2" style="color: var(--muted)">
          <div>
            请求时间：
            <span style="color: var(--text)">
              {{ formatDateTime(data.webhook_log.created_at) }}
            </span>
          </div>

          <div>
            来源 IP：
            <span style="color: var(--text)">
              {{ data.webhook_log.ip_address }}
            </span>
          </div>

          <div>
            Content-Type：
            <span style="color: var(--text)">
              {{ data.webhook_log.content_type }}
            </span>
          </div>

          <div>
            过滤结果：
            <span
              class="badge"
              :class="data.webhook_log.filter_passed ? 'badge-green' : 'badge-yellow'"
            >
              {{ data.webhook_log.filter_passed ? '通过' : '过滤' }}
            </span>
            <span v-if="data.webhook_log.filter_detail" class="ml-2">
              {{ data.webhook_log.filter_detail }}
            </span>
          </div>

          <RouterLink
            :to="`/logs/${data.webhook_log.id}`"
            class="btn btn-ghost sm:w-auto mt-2"
          >
            查看完整请求日志
          </RouterLink>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button
          v-if="data.status === 'failed'"
          type="button"
          class="btn btn-primary"
          :disabled="resendMutation.isPending.value"
          @click="resend"
        >
          <RefreshCw class="w-4 h-4" />
          {{ resendMutation.isPending.value ? '发送中...' : '重新发送' }}
        </button>

        <RouterLink to="/history" class="btn btn-secondary">
          返回列表
        </RouterLink>
      </div>
    </div>
  </div>
</template>