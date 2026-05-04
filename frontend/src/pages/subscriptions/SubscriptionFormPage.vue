<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { useRoute } from 'vue-router'
import { Save } from 'lucide-vue-next'

import {
  createSubscriptionFilterApi,
  deleteSubscriptionFilterApi,
  getSubscriptionApi,
  getSubscriptionFormOptionsApi,
  toggleSubscriptionFilterApi,
  updateSubscriptionApi,
  updateSubscriptionFilterApi,
} from '@/api/subscriptions'
import { getErrorMessage } from '@/api/http'
import FilterRuleEditor from '@/components/business/FilterRuleEditor.vue'
import { useToastStore } from '@/stores/toast'
import type {
  SubscriptionFilterPayload,
  SubscriptionUpdatePayload,
} from '@/types/subscription'

const route = useRoute()
const toast = useToastStore()
const queryClient = useQueryClient()

const subId = computed(() => Number(route.params.id))
const filterEditId = ref<number | null>(null)

const form = reactive<SubscriptionUpdatePayload>({
  template_id: null,
  notifier_config_id: null,
  custom_recipients: '',
  is_active: false,
})

const { data: sub, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['subscription', subId.value]),
  queryFn: () => getSubscriptionApi(subId.value),
})

const { data: options, isLoading: optionsLoading } = useQuery({
  queryKey: computed(() => ['subscription-options', subId.value]),
  queryFn: () => getSubscriptionFormOptionsApi(subId.value),
})

watch(
  sub,
  value => {
    if (!value) return

    form.template_id = value.template_id
    form.notifier_config_id = value.notifier_config_id
    form.custom_recipients = value.custom_recipients || ''
    form.is_active = value.is_active
  },
  { immediate: true },
)

const selectedSharedNotifier = computed(() => {
  if (!form.notifier_config_id) return null

  return (options.value?.shared_notifiers || []).find(
    item => item.id === form.notifier_config_id,
  )
})

const saveMutation = useMutation({
  mutationFn: () => updateSubscriptionApi(subId.value, form),
  onSuccess: data => {
    toast.success('订阅已保存')
    queryClient.setQueryData(['subscription', subId.value], data)
    queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const createFilterMutation = useMutation({
  mutationFn: (payload: SubscriptionFilterPayload) =>
    createSubscriptionFilterApi(subId.value, payload),
  onSuccess: () => {
    toast.success('规则已添加')
    queryClient.invalidateQueries({ queryKey: ['subscription', subId.value] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const updateFilterMutation = useMutation({
  mutationFn: ({
    ruleId,
    payload,
  }: {
    ruleId: number
    payload: SubscriptionFilterPayload
  }) => updateSubscriptionFilterApi(subId.value, ruleId, payload),
  onSuccess: () => {
    toast.success('规则已更新')
    queryClient.invalidateQueries({ queryKey: ['subscription', subId.value] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const toggleFilterMutation = useMutation({
  mutationFn: (ruleId: number) => toggleSubscriptionFilterApi(subId.value, ruleId),
  onSuccess: () => {
    toast.success('规则状态已更新')
    queryClient.invalidateQueries({ queryKey: ['subscription', subId.value] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const deleteFilterMutation = useMutation({
  mutationFn: (ruleId: number) => deleteSubscriptionFilterApi(subId.value, ruleId),
  onSuccess: () => {
    toast.success('规则已删除')
    queryClient.invalidateQueries({ queryKey: ['subscription', subId.value] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const busy = computed(() => {
  return (
    saveMutation.isPending.value ||
    createFilterMutation.isPending.value ||
    updateFilterMutation.isPending.value ||
    toggleFilterMutation.isPending.value ||
    deleteFilterMutation.isPending.value
  )
})

function submit() {
  if (form.is_active && selectedSharedNotifier.value && !form.custom_recipients.trim()) {
    toast.error('使用共享通知渠道时必须填写收件人')
    return
  }

  saveMutation.mutate()
}

function updateFilter(ruleId: number, payload: SubscriptionFilterPayload) {
  updateFilterMutation.mutate({ ruleId, payload })
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
        <RouterLink to="/subscriptions" class="text-sm text-brand hover:underline">
          返回订阅列表
        </RouterLink>

        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Subscription Config
          </div>

          <h2 class="page-title mt-2">
            配置订阅
          </h2>

          <p class="page-subtitle">
            {{ sub?.channel_name || '' }}
          </p>
        </div>
      </div>
    </div>

    <div v-if="isLoading || optionsLoading" class="form-card">
      正在加载订阅配置...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        订阅加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <template v-else-if="sub">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="lg:col-span-2 space-y-4">
          <form class="form-card space-y-4" @submit.prevent="submit">
            <div>
              <label>通知模板</label>

              <select v-model.number="form.template_id">
                <option :value="null">
                  请选择模板
                </option>

                <optgroup v-if="options?.my_templates.length" label="我的模板">
                  <option
                    v-for="item in options.my_templates"
                    :key="item.id"
                    :value="item.id"
                  >
                    {{ item.name }}
                  </option>
                </optgroup>

                <optgroup v-if="options?.shared_templates.length" label="共享模板">
                  <option
                    v-for="item in options.shared_templates"
                    :key="item.id"
                    :value="item.id"
                  >
                    {{ item.name }}{{ item.description ? ` — ${item.description}` : '' }}
                  </option>
                </optgroup>
              </select>
            </div>

            <div>
              <label>通知渠道</label>

              <select v-model.number="form.notifier_config_id">
                <option :value="null">
                  请选择
                </option>

                <optgroup v-if="options?.my_notifiers.length" label="我的通知渠道">
                  <option
                    v-for="item in options.my_notifiers"
                    :key="item.id"
                    :value="item.id"
                  >
                    {{ item.name }} ({{ item.notifier_type }})
                  </option>
                </optgroup>

                <optgroup v-if="options?.shared_notifiers.length" label="共享通知渠道">
                  <option
                    v-for="item in options.shared_notifiers"
                    :key="item.id"
                    :value="item.id"
                  >
                    {{ item.name }} (共享 · {{ item.notifier_type }})
                  </option>
                </optgroup>
              </select>
            </div>

            <div v-if="selectedSharedNotifier">
              <label>收件人 *</label>

              <input
                v-model="form.custom_recipients"
                type="text"
                placeholder="使用共享渠道时必填，多个用逗号分隔"
              >

              <p class="helper-text text-xs mt-2">
                共享渠道的核心配置由管理员维护，你只需要填写自己的接收目标。
              </p>
            </div>

            <label class="flex items-center gap-3 mb-0 cursor-pointer">
              <input
                v-model="form.is_active"
                type="checkbox"
                class="w-4 h-4"
              >

              <span class="text-sm" style="color: var(--text-soft)">
                启用此订阅
              </span>
            </label>

            <button
              type="submit"
              class="btn btn-primary"
              :disabled="saveMutation.isPending.value"
            >
              <Save class="w-4 h-4" />
              {{ saveMutation.isPending.value ? '保存中...' : '保存订阅' }}
            </button>
          </form>

          <FilterRuleEditor
            v-model:edit-id="filterEditId"
            :rules="sub.filters || []"
            :loading="busy"
            @create="payload => createFilterMutation.mutate(payload)"
            @update="updateFilter"
            @toggle="ruleId => toggleFilterMutation.mutate(ruleId)"
            @remove="removeFilter"
          />
        </div>

        <div class="space-y-4">
          <div class="form-card">
            <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
              订阅状态
            </h3>

            <div class="space-y-2 text-sm" style="color: var(--muted)">
              <div class="flex justify-between">
                <span>今日已发送</span>
                <span style="color: var(--text)">
                  {{ sub.sends_today }} / {{ sub.limits?.per_day_limit ?? '?' }}
                </span>
              </div>

              <div class="flex justify-between">
                <span>本小时</span>
                <span style="color: var(--text)">
                  {{ sub.sends_this_hour }} / {{ sub.limits?.per_hour_limit ?? '?' }}
                </span>
              </div>

              <div class="flex justify-between">
                <span>发送间隔</span>
                <span style="color: var(--text)">
                  至少 {{ sub.limits?.min_interval ?? '?' }} 秒
                </span>
              </div>
            </div>
          </div>

          <div class="form-card">
            <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
              使用提示
            </h3>

            <ul class="space-y-2 text-sm" style="color: var(--muted)">
              <li>可以选择自己的模板，也可以引用管理员共享模板。</li>
              <li>共享模板仅显示标题和简介，不展示正文源码。</li>
              <li>使用共享通知渠道时必须填写收件人。</li>
              <li>过滤规则可控制哪些通知真正发送。</li>
              <li>配置完成后记得勾选启用。</li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>