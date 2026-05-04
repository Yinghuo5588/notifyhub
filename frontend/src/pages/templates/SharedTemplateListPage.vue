<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { FileText } from 'lucide-vue-next'

import { getSharedTemplatesApi } from '@/api/templates'

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['shared-templates'],
  queryFn: getSharedTemplatesApi,
})
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Shared Templates
          </div>

          <h2 class="page-title mt-2">
            共享模板
          </h2>

          <p class="page-subtitle">
            管理员共享给你的模板。这里只展示标题和简介，不暴露正文源码。
          </p>
        </div>

        <RouterLink to="/subscriptions" class="btn btn-ghost sm:w-auto">
          去配置订阅
        </RouterLink>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载共享模板...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        共享模板加载失败
      </div>
      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else-if="data?.length" class="data-list">
      <div
        v-for="item in data"
        :key="item.id"
        class="list-card"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <FileText class="w-5 h-5 text-brand" />

              <h3 class="text-lg font-semibold" style="color: var(--text)">
                {{ item.name }}
              </h3>

              <span class="badge badge-purple">
                共享
              </span>

              <span class="badge badge-blue">
                {{ item.body_format }}
              </span>
            </div>

            <p v-if="item.description" class="muted-text text-sm mt-2">
              {{ item.description }}
            </p>

            <div class="text-xs mt-2" style="color: var(--muted)">
              仅可引用使用
            </div>
          </div>

          <RouterLink to="/subscriptions" class="btn btn-secondary sm:w-auto">
            去使用
          </RouterLink>
        </div>
      </div>
    </div>

    <div v-else class="empty-state form-card">
      <FileText class="w-14 h-14 mx-auto mb-4 text-brand" />

      <div class="text-lg font-semibold" style="color: var(--text)">
        还没有共享模板
      </div>

      <p class="page-subtitle">
        等管理员共享后，你就能在订阅配置里直接引用它们。
      </p>
    </div>
  </div>
</template>