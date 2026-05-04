<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Bell, Edit, Plus, Send, Share2, Trash2 } from 'lucide-vue-next'

import {
  deleteNotifierApi,
  getNotifiersApi,
  testNotifierApi,
} from '@/api/notifiers'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { getErrorMessage } from '@/api/http'
import { formatShortDateTime } from '@/utils/format'

const auth = useAuthStore()
const toast = useToastStore()
const queryClient = useQueryClient()

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['notifiers'],
  queryFn: getNotifiersApi,
})

const deleteMutation = useMutation({
  mutationFn: deleteNotifierApi,
  onSuccess: () => {
    toast.success('通知渠道已删除')
    queryClient.invalidateQueries({ queryKey: ['notifiers'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const testMutation = useMutation({
  mutationFn: testNotifierApi,
  onSuccess: data => {
    if (data.ok) {
      toast.success(data.msg || '测试发送成功')
    } else {
      toast.error(data.msg || '测试发送失败')
    }
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

function remove(id: number) {
  if (!window.confirm('确定删除此通知渠道配置？')) return
  deleteMutation.mutate(id)
}

function test(id: number) {
  if (!window.confirm('确定发送一条测试通知？')) return
  testMutation.mutate(id)
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Notifiers
          </div>

          <h2 class="page-title mt-2">
            通知渠道
          </h2>

          <p class="page-subtitle">
            配置邮件、飞书等通知发送方式，让消息真正飞出去。
          </p>
        </div>

        <a href="/notifiers/new" class="btn btn-primary sm:w-auto">
          <Plus class="w-4 h-4" />
          新建渠道
        </a>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载通知渠道...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        通知渠道加载失败
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
              <Bell class="w-5 h-5 text-brand" />

              <h3 class="text-lg font-semibold" style="color: var(--text)">
                {{ item.name }}
              </h3>

              <span class="badge badge-blue">
                {{ item.notifier_type }}
              </span>

              <span class="badge" :class="item.is_active ? 'badge-green' : 'badge-gray'">
                {{ item.is_active ? '启用' : '禁用' }}
              </span>

              <span v-if="item.is_shared" class="badge badge-purple">
                共享
              </span>
            </div>

            <div class="text-xs mt-2" style="color: var(--muted)">
              更新：{{ formatShortDateTime(item.updated_at) || '未知' }}
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:flex gap-2 shrink-0">
            <a
              v-if="item.is_shared && auth.user?.is_admin"
              :href="`/admin/notifiers/${item.id}/share`"
              class="btn btn-ghost"
            >
              <Share2 class="w-4 h-4" />
              共享管理
            </a>

            <button
              type="button"
              class="btn btn-ghost"
              :disabled="testMutation.isPending.value"
              @click="test(item.id)"
            >
              <Send class="w-4 h-4" />
              测试
            </button>

            <a :href="`/notifiers/${item.id}/edit`" class="btn btn-secondary">
              <Edit class="w-4 h-4" />
              编辑
            </a>

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
      <Bell class="w-14 h-14 mx-auto mb-4 text-brand" />

      <div class="text-lg font-semibold" style="color: var(--text)">
        还没有通知渠道
      </div>

      <p class="page-subtitle">
        先配置一个发送出口，不然消息只能在系统里原地打转。
      </p>

      <a href="/notifiers/new" class="btn btn-primary sm:w-auto mt-3">
        创建第一个渠道
      </a>
    </div>
  </div>
</template>