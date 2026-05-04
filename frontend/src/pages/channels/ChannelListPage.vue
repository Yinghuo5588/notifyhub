<script setup lang="ts">
import { computed } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Copy, Edit, Plus, Share2, Trash2, Webhook } from 'lucide-vue-next'

import { deleteChannelApi, getChannelsApi } from '@/api/channels'
import { useToastStore } from '@/stores/toast'
import { useAuthStore } from '@/stores/auth'
import { copyText, formatShortDateTime } from '@/utils/format'
import { getErrorMessage } from '@/api/http'

const toast = useToastStore()
const auth = useAuthStore()
const queryClient = useQueryClient()

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['channels'],
  queryFn: getChannelsApi,
})

const deleteMutation = useMutation({
  mutationFn: deleteChannelApi,
  onSuccess: () => {
    toast.success('频道已删除')
    queryClient.invalidateQueries({ queryKey: ['channels'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const origin = computed(() => window.location.origin)

function webhookUrl(channel_uuid: string, token: string) {
  return `${origin.value}/hook/${channel_uuid}?token=${token}`
}

async function copyWebhook(channel_uuid: string, token: string) {
  await copyText(webhookUrl(channel_uuid, token))
  toast.success('Webhook 地址已复制')
}

function remove(id: number) {
  if (!window.confirm('确定删除此频道？所有关联订阅也会被删除。')) return
  deleteMutation.mutate(id)
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Channels
          </div>
          <h2 class="page-title mt-2">
            Webhook 频道
          </h2>
          <p class="page-subtitle">
            每个频道对应一个独立 Webhook 接收地址。
          </p>
        </div>

        <RouterLink to="/channels/new" class="btn btn-primary sm:w-auto">
          <Plus class="w-4 h-4" />
          新建频道
        </RouterLink>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载频道...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        频道加载失败
      </div>
      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else-if="data?.length" class="data-list">
      <div
        v-for="ch in data"
        :key="ch.id"
        class="list-card"
      >
        <div class="flex flex-col gap-4">
          <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <Webhook class="w-5 h-5 text-brand" />

                <h3 class="text-lg font-semibold" style="color: var(--text)">
                  {{ ch.name }}
                </h3>

                <span class="badge" :class="ch.is_active ? 'badge-green' : 'badge-gray'">
                  {{ ch.is_active ? '启用' : '禁用' }}
                </span>

                <span v-if="ch.is_shared" class="badge badge-blue">
                  共享
                </span>
              </div>

              <p v-if="ch.description" class="muted-text text-sm mt-2">
                {{ ch.description }}
              </p>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3 text-xs" style="color: var(--muted)">
                <div>
                  模板：
                  <span style="color: var(--text)">
                    {{ ch.template_name || '未配置' }}
                  </span>
                </div>
                <div>
                  渠道：
                  <span style="color: var(--text)">
                    {{ ch.notifier_name || '未配置' }}
                  </span>
                </div>
                <div>
                  创建：
                  <span style="color: var(--text)">
                    {{ formatShortDateTime(ch.created_at) }}
                  </span>
                </div>
                <div>
                  Token：
                  <code>{{ ch.token.slice(0, 12) }}...</code>
                </div>
              </div>

              <div class="mt-3">
                <label class="text-xs">Webhook 地址</label>
                <div class="flex flex-col sm:flex-row gap-2">
                  <input
                    :value="webhookUrl(ch.channel_uuid, ch.token)"
                    readonly
                    class="font-mono text-xs"
                  >
                  <button
                    type="button"
                    class="btn btn-ghost sm:w-auto"
                    @click="copyWebhook(ch.channel_uuid, ch.token)"
                  >
                    <Copy class="w-4 h-4" />
                    复制
                  </button>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:flex gap-2 shrink-0">
              <RouterLink
                v-if="ch.is_shared && auth.user?.is_admin"
                :to="`/admin/channels/${ch.id}/share`"
                class="btn btn-ghost"
              >
                <Share2 class="w-4 h-4" />
                共享管理
              </RouterLink>

              <RouterLink :to="`/channels/${ch.id}/edit`" class="btn btn-secondary">
                <Edit class="w-4 h-4" />
                编辑
              </RouterLink>

              <button
                type="button"
                class="btn btn-danger"
                :disabled="deleteMutation.isPending.value"
                @click="remove(ch.id)"
              >
                <Trash2 class="w-4 h-4" />
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state form-card">
      <Webhook class="w-14 h-14 mx-auto mb-4 text-brand" />
      <div class="text-lg font-semibold" style="color: var(--text)">
        还没有频道
      </div>
      <p class="page-subtitle">
        先建一个 Webhook 入口，让消息有地方落地。
      </p>
      <RouterLink to="/channels/new" class="btn btn-primary sm:w-auto mt-3">
        创建第一个频道
      </RouterLink>
    </div>
  </div>
</template>