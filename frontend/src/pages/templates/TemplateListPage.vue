<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Edit, FileText, Plus, Share2, Trash2 } from 'lucide-vue-next'

import { deleteTemplateApi, getTemplatesApi } from '@/api/templates'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { getErrorMessage } from '@/api/http'
import { formatShortDateTime } from '@/utils/format'

const auth = useAuthStore()
const toast = useToastStore()
const queryClient = useQueryClient()

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['templates'],
  queryFn: getTemplatesApi,
})

const deleteMutation = useMutation({
  mutationFn: deleteTemplateApi,
  onSuccess: () => {
    toast.success('模板已删除')
    queryClient.invalidateQueries({ queryKey: ['templates'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

function remove(id: number) {
  if (!window.confirm('确定删除此模板？')) return
  deleteMutation.mutate(id)
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Templates
          </div>
          <h2 class="page-title mt-2">
            通知模板
          </h2>
          <p class="page-subtitle">
            使用 Jinja2 语法自定义通知标题和正文。
          </p>
        </div>

        <div class="flex flex-col sm:flex-row gap-2">
          <RouterLink
            v-if="!auth.user?.is_admin"
            to="/templates/shared"
            class="btn btn-ghost sm:w-auto"
          >
            共享模板
          </RouterLink>

          <RouterLink to="/templates/new" class="btn btn-primary sm:w-auto">
            <Plus class="w-4 h-4" />
            新建模板
          </RouterLink>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载模板...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        模板加载失败
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

              <span v-if="item.is_shared" class="badge badge-purple">
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
              更新：{{ formatShortDateTime(item.updated_at) || '未知' }}
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:flex gap-2 shrink-0">
            <a
              v-if="item.is_shared && auth.user?.is_admin"
              :href="`/admin/templates/${item.id}/share`"
              class="btn btn-ghost"
            >
              <Share2 class="w-4 h-4" />
              共享管理
            </a>

            <RouterLink :to="`/templates/${item.id}/edit`" class="btn btn-secondary">
              <Edit class="w-4 h-4" />
              编辑
            </RouterLink>

            <button
              type="button"
              class="btn btn-danger"
              :disabled="deleteMutation.isPending.value"
              @click="remove(item.id)"
            >
              <Trash2 class="w-4 h-4" />
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state form-card">
      <FileText class="w-14 h-14 mx-auto mb-4 text-brand" />
      <div class="text-lg font-semibold" style="color: var(--text)">
        还没有模板
      </div>
      <p class="page-subtitle">
        先做一个好模板，后面的通知才会看起来像作品。
      </p>
      <RouterLink to="/templates/new" class="btn btn-primary sm:w-auto mt-3">
        创建第一个模板
      </RouterLink>
    </div>
  </div>
</template>