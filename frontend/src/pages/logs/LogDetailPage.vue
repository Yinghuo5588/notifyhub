<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRoute } from 'vue-router'

import { getLogDetailApi } from '@/api/logs'
import JsonViewer from '@/components/business/JsonViewer.vue'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const itemId = computed(() => Number(route.params.id))

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['log-detail', itemId.value]),
  queryFn: () => getLogDetailApi(itemId.value),
})
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col gap-3">
        <RouterLink to="/logs" class="text-sm text-brand hover:underline">
          返回请求日志
        </RouterLink>

        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Webhook Log Detail
          </div>

          <h2 class="page-title mt-2">
            请求日志 #{{ itemId }}
          </h2>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载请求日志...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        请求日志加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else-if="data" class="max-w-5xl space-y-4">
      <div class="form-card">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
          请求信息
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div>
            <span style="color: var(--muted)">频道</span>
            <span class="ml-2" style="color: var(--text)">
              {{ data.channel_name || '未知频道' }}
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">时间</span>
            <span class="ml-2" style="color: var(--text)">
              {{ formatDateTime(data.created_at) }}
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">来源 IP</span>
            <span class="ml-2 font-mono" style="color: var(--text)">
              {{ data.ip_address || 'unknown' }}
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">Content-Type</span>
            <span class="ml-2 font-mono text-xs" style="color: var(--text)">
              {{ data.content_type || '-' }}
            </span>
          </div>

          <div>
            <span style="color: var(--muted)">过滤结果</span>
            <span
              class="ml-2 badge"
              :class="data.filter_passed ? 'badge-green' : 'badge-yellow'"
            >
              {{ data.filter_passed ? '通过' : '已过滤' }}
            </span>
          </div>

          <div v-if="data.filter_detail">
            <span style="color: var(--muted)">过滤详情</span>
            <span class="ml-2" style="color: var(--text)">
              {{ data.filter_detail }}
            </span>
          </div>
        </div>
      </div>

      <JsonViewer
        title="解析后的数据 JSON"
        :value="data.parsed_data"
        max-height="520px"
      />

      <JsonViewer
        title="请求头"
        :value="data.request_headers"
        max-height="320px"
        :default-collapsed="true"
      />

      <div class="form-card">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
          原始请求体
        </h3>

        <pre
          class="rounded-2xl bg-black/20 p-4 overflow-x-auto text-xs whitespace-pre-wrap max-h-96"
          style="color: var(--text)"
        >{{ data.request_body || '(空)' }}</pre>
      </div>

      <RouterLink to="/logs" class="btn btn-secondary">
        返回列表
      </RouterLink>
    </div>
  </div>
</template>