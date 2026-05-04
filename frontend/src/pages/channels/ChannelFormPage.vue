<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { Save, Webhook } from 'lucide-vue-next'

import {
  createChannelApi,
  createChannelFilterApi,
  deleteChannelFilterApi,
  getChannelApi,
  getChannelFormOptionsApi,
  regenerateChannelTokenApi,
  toggleChannelFilterApi,
  updateChannelApi,
  updateChannelFilterApi,
} from '@/api/channels'
import { getErrorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import WebhookUrlBox from '@/components/business/WebhookUrlBox.vue'
import FilterRuleEditor from '@/components/business/FilterRuleEditor.vue'
import type { ChannelPayload, FilterRulePayload } from '@/types/channel'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()
const auth = useAuthStore()
const queryClient = useQueryClient()

const channelId = computed(() => {
  const raw = route.params.id
  return raw ? Number(raw) : null
})

const isEdit = computed(() => !!channelId.value)

const form = reactive<ChannelPayload>({
  name: '',
  description: '',
  template_id: null,
  notifier_config_id: null,
  is_active: true,
  is_shared: false,
})

const filterEditId = ref<number | null>(null)

const { data: options, isLoading: optionsLoading } = useQuery({
  queryKey: ['channel-form-options'],
  queryFn: getChannelFormOptionsApi,
})

const {
  data: channel,
  isLoading: channelLoading,
  isError,
  refetch,
} = useQuery({
  queryKey: computed(() => ['channel', channelId.value]),
  queryFn: () => getChannelApi(channelId.value!),
  enabled: computed(() => !!channelId.value),
})

watch(
  channel,
  value => {
    if (!value) return

    form.name = value.name
    form.description = value.description
    form.template_id = value.template_id
    form.notifier_config_id = value.notifier_config_id
    form.is_active = value.is_active
    form.is_shared = value.is_shared
  },
  { immediate: true },
)

const saveMutation = useMutation({
  mutationFn: async () => {
    if (isEdit.value && channelId.value) {
      return updateChannelApi(channelId.value, form)
    }

    return createChannelApi(form)
  },
  onSuccess: data => {
    toast.success(isEdit.value ? '频道已保存' : '频道已创建')

    queryClient.invalidateQueries({ queryKey: ['channels'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })

    if (isEdit.value) {
      queryClient.invalidateQueries({ queryKey: ['channel', channelId.value] })
    } else {
      router.replace(`/channels/${data.id}/edit`)
    }
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const tokenMutation = useMutation({
  mutationFn: () => regenerateChannelTokenApi(channelId.value!),
  onSuccess: data => {
    toast.success('Token 已重新生成')

    queryClient.setQueryData(['channel', channelId.value], data)
    queryClient.invalidateQueries({ queryKey: ['channels'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const createFilterMutation = useMutation({
  mutationFn: (payload: FilterRulePayload) => {
    return createChannelFilterApi(channelId.value!, payload)
  },
  onSuccess: () => {
    toast.success('规则已添加')
    queryClient.invalidateQueries({ queryKey: ['channel', channelId.value] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const updateFilterMutation = useMutation({
  mutationFn: ({
    ruleId,
    payload,
  }: {
    ruleId: number
    payload: FilterRulePayload
  }) => {
    return updateChannelFilterApi(channelId.value!, ruleId, payload)
  },
  onSuccess: () => {
    toast.success('规则已更新')
    queryClient.invalidateQueries({ queryKey: ['channel', channelId.value] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const toggleFilterMutation = useMutation({
  mutationFn: (ruleId: number) => {
    return toggleChannelFilterApi(channelId.value!, ruleId)
  },
  onSuccess: () => {
    toast.success('规则状态已更新')
    queryClient.invalidateQueries({ queryKey: ['channel', channelId.value] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const deleteFilterMutation = useMutation({
  mutationFn: (ruleId: number) => {
    return deleteChannelFilterApi(channelId.value!, ruleId)
  },
  onSuccess: () => {
    toast.success('规则已删除')
    queryClient.invalidateQueries({ queryKey: ['channel', channelId.value] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const origin = computed(() => window.location.origin)

const webhookUrl = computed(() => {
  if (!channel.value) return ''
  return `${origin.value}/hook/${channel.value.channel_uuid}?token=${channel.value.token}`
})

const busy = computed(() => {
  return (
    saveMutation.isPending.value ||
    tokenMutation.isPending.value ||
    createFilterMutation.isPending.value ||
    updateFilterMutation.isPending.value ||
    toggleFilterMutation.isPending.value ||
    deleteFilterMutation.isPending.value
  )
})

function submit() {
  if (!form.name.trim()) {
    toast.error('请输入频道名称')
    return
  }

  saveMutation.mutate()
}

function regenerateToken() {
  if (!window.confirm('重新生成 Token 后旧 Webhook 地址会失效，确定继续？')) return
  tokenMutation.mutate()
}

function createFilter(payload: FilterRulePayload) {
  if (!channelId.value) {
    toast.warning('请先保存频道后再添加过滤规则')
    return
  }

  createFilterMutation.mutate(payload)
}

function updateFilter(ruleId: number, payload: FilterRulePayload) {
  updateFilterMutation.mutate({ ruleId, payload })
}

function toggleFilter(ruleId: number) {
  toggleFilterMutation.mutate(ruleId)
}

function removeFilter(ruleId: number) {
  if (!window.confirm('确定删除此过滤规则？')) return
  deleteFilterMutation.mutate(ruleId)
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col gap-3">
        <RouterLink to="/channels" class="text-sm text-brand hover:underline">
          返回频道列表
        </RouterLink>

        <div>
          <div
            class="text-xs uppercase tracking-[0.28em]"
            style="color: var(--muted)"
          >
            Channel Editor
          </div>

          <h2 class="page-title mt-2">
            {{ isEdit ? '编辑频道' : '新建频道' }}
          </h2>
        </div>
      </div>
    </div>

    <div v-if="channelLoading || optionsLoading" class="form-card">
      正在加载频道配置...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        频道加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <template v-else>
      <form @submit.prevent="submit">
        <div class="form-card mb-4">
          <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
            基本信息
          </h3>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="sm:col-span-2">
              <label>频道名称 *</label>
              <input
                v-model="form.name"
                type="text"
                required
                placeholder="如：Emby 入库通知"
              >
            </div>

            <div class="sm:col-span-2">
              <label>描述</label>
              <input
                v-model="form.description"
                type="text"
                placeholder="可选"
              >
            </div>

            <div>
              <label>通知模板</label>
              <select v-model.number="form.template_id">
                <option :value="null">
                  请选择
                </option>

                <option
                  v-for="item in options?.templates || []"
                  :key="item.id"
                  :value="item.id"
                >
                  {{ item.name }}
                </option>
              </select>

              <RouterLink
                to="/templates/new"
                class="text-xs text-brand hover:underline mt-2 inline-block"
              >
                去新建模板
              </RouterLink>
            </div>

            <div>
              <label>通知渠道</label>
              <select v-model.number="form.notifier_config_id">
                <option :value="null">
                  请选择
                </option>

                <option
                  v-for="item in options?.notifiers || []"
                  :key="item.id"
                  :value="item.id"
                >
                  {{ item.name }} ({{ item.notifier_type }})
                </option>
              </select>

              <RouterLink
                to="/notifiers/new"
                class="text-xs text-brand hover:underline mt-2 inline-block"
              >
                去新建渠道
              </RouterLink>
            </div>
          </div>

          <div class="mt-4 space-y-3">
            <label class="flex items-center gap-3 mb-0 cursor-pointer">
              <input
                v-model="form.is_active"
                type="checkbox"
                class="w-4 h-4"
              >

              <span class="text-sm" style="color: var(--text-soft)">
                启用频道
              </span>
            </label>

            <div
              v-if="auth.user?.is_admin"
              class="border-t pt-4 space-y-3"
              style="border-color: var(--line)"
            >
              <label class="flex items-center gap-3 mb-0 cursor-pointer">
                <input
                  v-model="form.is_shared"
                  type="checkbox"
                  class="w-4 h-4"
                >

                <span class="text-sm" style="color: var(--text-soft)">
                  共享频道，允许分配给其他用户订阅
                </span>
              </label>

              <div
                v-if="isEdit && form.is_shared"
                class="rounded-2xl border border-sky-400/20 bg-sky-400/10 p-3 text-sm"
                style="color: var(--text-soft)"
              >
                当前频道已开启共享，可前往共享管理配置订阅用户和限流规则。
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="saveMutation.isPending.value"
          >
            <Save class="w-4 h-4" />
            {{ saveMutation.isPending.value ? '保存中...' : isEdit ? '保存修改' : '创建频道' }}
          </button>

          <RouterLink to="/channels" class="btn btn-secondary">
            取消
          </RouterLink>
        </div>
      </form>

      <WebhookUrlBox
        v-if="isEdit && channel"
        class="mb-4"
        :url="webhookUrl"
        :token-preview="`${channel.token.slice(0, 16)}...`"
        can-regenerate
        :regenerating="tokenMutation.isPending.value"
        @regenerate="regenerateToken"
      />

      <FilterRuleEditor
        v-if="isEdit && channel"
        v-model:edit-id="filterEditId"
        :rules="channel.filter_rules || []"
        :loading="busy"
        @create="createFilter"
        @update="updateFilter"
        @toggle="toggleFilter"
        @remove="removeFilter"
      />

      <div v-if="!isEdit" class="form-card">
        <Webhook class="w-8 h-8 text-brand mb-3" />

        <div class="font-semibold mb-1" style="color: var(--text)">
          保存后可配置 Webhook 地址和过滤规则
        </div>

        <p class="helper-text text-sm">
          创建频道后，系统会自动生成独立的 Webhook 地址和 Token。之后你可以复制地址、重置 Token，并配置频道级过滤规则。
        </p>
      </div>
    </template>
  </div>
</template>