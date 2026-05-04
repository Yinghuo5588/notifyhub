<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { Radio, Search } from 'lucide-vue-next'

import { getLogsApi } from '@/api/logs'
import PaginationBar from '@/components/ui/PaginationBar.vue'
import { formatShortDateTime } from '@/utils/format'

const filters = reactive({
  page: 1,
  page_size: 10,
  channel_id: '',
  keyword: '',
})

const queryKey = computed(() => ['logs', { ...filters }])

const { data, isLoading, isError, refetch } = useQuery({
  queryKey,
  queryFn: () => getLogsApi(filters),
})

function search() {
  filters.page = 1
  refetch()
}

function clearFilters() {
  filters.page = 1
  filters.channel_id = ''
  filters.keyword = ''
}

function changePage(page: number) {
  filters.page = page
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Webhook Logs
          </div>

          <h2 class="page-title mt-2">
            Webhook 日志
          </h2>

          <p class="page-subtitle">
            查看原始请求、解析结果、来源 IP 和过滤结果。
          </p>
        </div>

        <div class="glass-panel rounded-2xl px-4 py-3 text-sm" style="color: var(--muted)">
          共 {{ data?.total || 0 }} 条
        </div>
      </div>
    </div>

    <div class="glass-panel rounded-2xl p-4 mb-4">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div class="sm:col-span-2">
          <input
            v-model="filters.keyword"
            type="text"
            placeholder="搜索请求体、解析数据、请求头、IP..."
            @keyup.enter="search"
          >
        </div>

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

    <template v-else-if="data">
      <div v-if="data.items.length" class="data-list">
        <RouterLink
          v-for="item in data.items"
          :key="item.id"
          :to="`/logs/${item.id}`"
          class="list-card no-underline block"
        >
          <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <Radio class="w-5 h-5 text-brand" />

                <h3 class="font-semibold" style="color: var(--text)">
                  {{ item.channel_name || '未知频道' }}
                </h3>

                <span
                  class="badge"
                  :class="item.filter_passed ? 'badge-green' : 'badge-yellow'"
                >
                  {{ item.filter_passed ? '通过' : '过滤' }}
                </span>

                <span v-if="item.content_type" class="badge badge-gray">
                  {{ item.content_type.split(';')[0] }}
                </span>
              </div>

              <p
                v-if="item.data_preview"
                class="text-sm mt-2 line-clamp-2"
                style="color: var(--muted)"
              >
                {{ item.data_preview }}
              </p>

              <div class="text-xs mt-3 flex flex-wrap gap-x-3 gap-y-1" style="color: var(--muted)">
                <span>IP：{{ item.ip_address || 'unknown' }}</span>
                <span>时间：{{ formatShortDateTime(item.created_at) }}</span>
                <span v-if="item.filter_detail">过滤：{{ item.filter_detail }}</span>
              </div>
            </div>

            <span class="btn btn-secondary sm:w-auto">
              详情
            </span>
          </div>
        </RouterLink>
      </div>

      <div v-else class="empty-state form-card">
        <Radio class="w-14 h-14 mx-auto mb-4 text-brand" />

        <div class="text-lg font-semibold" style="color: var(--text)">
          暂无 Webhook 日志
        </div>

        <p class="page-subtitle">
          等第一条 Webhook 请求打进来，这里就会有记录。
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