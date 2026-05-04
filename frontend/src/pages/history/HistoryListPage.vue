<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { History, RefreshCw, Search } from 'lucide-vue-next'

import { getHistoryApi, resendHistoryApi } from '@/api/history'
import { getErrorMessage } from '@/api/http'
import StatusBadge from '@/components/business/StatusBadge.vue'
import PaginationBar from '@/components/ui/PaginationBar.vue'
import { useToastStore } from '@/stores/toast'
import { formatShortDateTime } from '@/utils/format'

const toast = useToastStore()
const queryClient = useQueryClient()

const filters = reactive({
  page: 1,
  page_size: 10,
  status: '',
  channel_id: '',
  keyword: '',
})

const queryKey = computed(() => ['history', { ...filters }])

const { data, isLoading, isError, refetch } = useQuery({
  queryKey,
  queryFn: () => getHistoryApi(filters),
})

const resendMutation = useMutation({
  mutationFn: resendHistoryApi,
  onSuccess: result => {
    if (result.ok) {
      toast.success(result.msg || '重发成功')
    } else {
      toast.error(result.msg || '重发失败')
    }

    queryClient.invalidateQueries({ queryKey: ['history'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

function search() {
  filters.page = 1
  refetch()
}

function clearFilters() {
  filters.page = 1
  filters.status = ''
  filters.channel_id = ''
  filters.keyword = ''
}

function changePage(page: number) {
  filters.page = page
}

function resend(id: number) {
  if (!window.confirm('确定重新发送此通知？')) return
  resendMutation.mutate(id)
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            History
          </div>

          <h2 class="page-title mt-2">
            发送历史
          </h2>

          <p class="page-subtitle">
            查看每条通知的发送状态、错误信息和重发记录。
          </p>
        </div>

        <div class="glass-panel rounded-2xl px-4 py-3 text-sm" style="color: var(--muted)">
          共 {{ data?.total || 0 }} 条
        </div>
      </div>
    </div>

    <div class="glass-panel rounded-2xl p-4 mb-4">
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div class="sm:col-span-2">
          <input
            v-model="filters.keyword"
            type="text"
            placeholder="搜索标题、正文或错误信息..."
            @keyup.enter="search"
          >
        </div>

        <select v-model="filters.status">
          <option value="">
            全部状态
          </option>
          <option value="success">
            成功
          </option>
          <option value="failed">
            失败
          </option>
          <option value="rate_limited">
            限频
          </option>
          <option value="filtered">
            过滤
          </option>
          <option value="pending">
            处理中
          </option>
        </select>

        <select v-model="filters.channel_id">
          <option value="">
            全频道
          </option>

          <option
            v-for="ch in data?.channels || []"
            :key="ch.id"
            :value="String(ch.id)"
          >
            {{ ch.name }}
          </option>
        </select>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
        <button type="button" class="btn btn-primary" @click="search">
          <Search class="w-4 h-4" />
          搜索
        </button>

        <button type="button" class="btn btn-secondary" @click="clearFilters">
          清除筛选
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载发送历史...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        发送历史加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <template v-else-if="data">
      <div v-if="data.items.length" class="data-list">
        <div
          v-for="item in data.items"
          :key="item.id"
          class="list-card"
        >
          <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
            <RouterLink
              :to="`/history/${item.id}`"
              class="flex-1 min-w-0 no-underline"
            >
              <div class="flex items-center gap-2 flex-wrap">
                <History class="w-5 h-5 text-brand" />

                <h3 class="font-semibold truncate" style="color: var(--text)">
                  {{ item.subject || '(无标题)' }}
                </h3>

                <StatusBadge :status="item.status" />
              </div>

              <p
                v-if="item.body_preview"
                class="text-sm mt-2 line-clamp-2"
                style="color: var(--muted)"
              >
                {{ item.body_preview }}
              </p>

              <div class="text-xs mt-3 flex flex-wrap gap-x-3 gap-y-1" style="color: var(--muted)">
                <span>频道：{{ item.channel_name || '未知频道' }}</span>
                <span>类型：{{ item.notifier_type }}</span>
                <span>时间：{{ formatShortDateTime(item.created_at) }}</span>
                <span v-if="item.retry_count > 0">重试：{{ item.retry_count }} 次</span>
              </div>

              <div
                v-if="item.error_message"
                class="text-xs text-rose-400 mt-2 truncate"
              >
                {{ item.error_message }}
              </div>
            </RouterLink>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:flex gap-2 shrink-0">
              <RouterLink :to="`/history/${item.id}`" class="btn btn-secondary">
                详情
              </RouterLink>

              <button
                v-if="item.status === 'failed'"
                type="button"
                class="btn btn-ghost"
                :disabled="resendMutation.isPending.value"
                @click="resend(item.id)"
              >
                <RefreshCw class="w-4 h-4" />
                重发
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state form-card">
        <History class="w-14 h-14 mx-auto mb-4 text-brand" />

        <div class="text-lg font-semibold" style="color: var(--text)">
          暂无发送历史
        </div>

        <p class="page-subtitle">
          等第一条通知发出去，这里就会开始记录。
        </p>
      </div>

      <PaginationBar
        :page="data.page"
        :total-pages="data.total_pages"
        :total="data.total"
        @change="changePage"
      />
    </template>
  </div>
</template>