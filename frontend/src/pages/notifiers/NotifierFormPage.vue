<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { Bell, Save, Send } from 'lucide-vue-next'

import {
  createNotifierApi,
  getNotifierApi,
  getNotifierTypesApi,
  testNotifierApi,
  updateNotifierApi,
} from '@/api/notifiers'
import { getErrorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import DynamicConfigForm from '@/components/business/DynamicConfigForm.vue'
import type {
  NotifierCreatePayload,
  NotifierFieldSchema,
  NotifierUpdatePayload,
} from '@/types/notifier'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()
const auth = useAuthStore()
const queryClient = useQueryClient()

const itemId = computed(() => {
  const raw = route.params.id
  return raw ? Number(raw) : null
})

const isEdit = computed(() => !!itemId.value)

const form = reactive({
  name: '',
  notifier_type: '',
  config: {} as Record<string, unknown>,
  is_active: true,
  is_shared: false,
})

const localError = ref('')

const { data: types, isLoading: typesLoading } = useQuery({
  queryKey: ['notifier-types'],
  queryFn: getNotifierTypesApi,
})

const {
  data: item,
  isLoading: itemLoading,
  isError,
  refetch,
} = useQuery({
  queryKey: computed(() => ['notifier', itemId.value]),
  queryFn: () => getNotifierApi(itemId.value!),
  enabled: computed(() => !!itemId.value),
})

const selectedType = computed(() => {
  return (types.value || []).find(item => item.type === form.notifier_type)
})

const selectedSchema = computed<Record<string, NotifierFieldSchema>>(() => {
  return selectedType.value?.schema || {}
})

watch(
  types,
  value => {
    if (!value?.length) return
    if (!form.notifier_type && !isEdit.value) {
      form.notifier_type = value[0].type
    }
  },
  { immediate: true },
)

watch(
  item,
  value => {
    if (!value) return

    form.name = value.name
    form.notifier_type = value.notifier_type
    form.config = { ...(value.config || {}) }
    form.is_active = value.is_active
    form.is_shared = value.is_shared
  },
  { immediate: true },
)

watch(
  () => form.notifier_type,
  () => {
    if (!isEdit.value) {
      form.config = {}
    }
  },
)

const saveMutation = useMutation({
  mutationFn: async () => {
    localError.value = ''

    if (!form.name.trim()) {
      throw new Error('请输入配置名称')
    }

    if (!form.notifier_type) {
      throw new Error('请选择通知类型')
    }

    if (isEdit.value && itemId.value) {
      const payload: NotifierUpdatePayload = {
        name: form.name,
        config: form.config,
        is_active: form.is_active,
        is_shared: form.is_shared,
      }

      return updateNotifierApi(itemId.value, payload)
    }

    const payload: NotifierCreatePayload = {
      name: form.name,
      notifier_type: form.notifier_type,
      config: form.config,
      is_shared: form.is_shared,
    }

    return createNotifierApi(payload)
  },
  onSuccess: data => {
    toast.success(isEdit.value ? '通知渠道已保存' : '通知渠道已创建')

    queryClient.invalidateQueries({ queryKey: ['notifiers'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })

    if (isEdit.value) {
      queryClient.invalidateQueries({ queryKey: ['notifier', itemId.value] })
    } else {
      router.replace(`/notifiers/${data.id}/edit`)
    }
  },
  onError: err => {
    localError.value = getErrorMessage(err)
  },
})

const testMutation = useMutation({
  mutationFn: () => testNotifierApi(itemId.value!),
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

function submit() {
  saveMutation.mutate()
}

function test() {
  if (!itemId.value) {
    toast.warning('请先保存配置后再测试')
    return
  }

  if (!window.confirm('确定发送一条测试通知？')) return
  testMutation.mutate()
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col gap-3">
        <RouterLink to="/notifiers" class="text-sm text-brand hover:underline">
          返回通知渠道列表
        </RouterLink>

        <div>
          <div
            class="text-xs uppercase tracking-[0.28em]"
            style="color: var(--muted)"
          >
            Notifier Editor
          </div>

          <h2 class="page-title mt-2">
            {{ isEdit ? '编辑通知渠道' : '新建通知渠道' }}
          </h2>

          <p class="page-subtitle">
            根据后端 schema 自动生成配置表单。新增渠道时，前端通常不用再手写字段。
          </p>
        </div>
      </div>
    </div>

    <div v-if="typesLoading || itemLoading" class="form-card">
      正在加载通知渠道配置...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        通知渠道加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <template v-else>
      <form class="max-w-3xl" @submit.prevent="submit">
        <div class="form-card space-y-4">
          <div class="flex items-center gap-2 mb-2">
            <Bell class="w-5 h-5 text-brand" />
            <h3 class="text-lg font-semibold" style="color: var(--text)">
              基本配置
            </h3>
          </div>

          <div
            v-if="localError"
            class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300"
          >
            {{ localError }}
          </div>

          <div>
            <label>配置名称 *</label>
            <input
              v-model="form.name"
              type="text"
              required
              placeholder="如：我的 QQ 邮箱、飞书运维群"
            >
          </div>

          <div>
            <label>渠道类型</label>

            <select
              v-model="form.notifier_type"
              :disabled="isEdit"
              required
            >
              <option
                v-for="item in types || []"
                :key="item.type"
                :value="item.type"
              >
                {{ item.name }}
              </option>
            </select>

            <p v-if="isEdit" class="helper-text text-xs mt-2">
              已创建的通知渠道不允许修改类型。如需更换类型，请新建一个渠道。
            </p>
          </div>

          <div
            class="border-t pt-4"
            style="border-color: var(--line)"
          >
            <div class="flex items-center justify-between gap-3 mb-4">
              <div>
                <div class="font-semibold" style="color: var(--text)">
                  配置字段
                </div>

                <p class="helper-text text-xs mt-1">
                  当前类型：{{ selectedType?.name || form.notifier_type || '未选择' }}
                </p>
              </div>

              <span v-if="form.notifier_type" class="badge badge-blue">
                {{ form.notifier_type }}
              </span>
            </div>

            <DynamicConfigForm
              v-if="Object.keys(selectedSchema).length"
              v-model="form.config"
              :schema="selectedSchema"
            />

            <div v-else class="helper-text text-sm">
              当前通知类型没有配置字段。
            </div>
          </div>

          <div
            v-if="isEdit"
            class="border-t pt-4"
            style="border-color: var(--line)"
          >
            <label class="flex items-center gap-3 mb-0 cursor-pointer">
              <input
                v-model="form.is_active"
                type="checkbox"
                class="w-4 h-4"
              >

              <span class="text-sm" style="color: var(--text-soft)">
                启用此通知渠道
              </span>
            </label>
          </div>

          <div
            v-if="auth.user?.is_admin"
            class="border-t pt-4"
            style="border-color: var(--line)"
          >
            <label class="flex items-center gap-3 mb-0 cursor-pointer">
              <input
                v-model="form.is_shared"
                type="checkbox"
                class="w-4 h-4"
              >

              <span class="text-sm" style="color: var(--text-soft)">
                共享给其他用户使用
              </span>
            </label>

            <div
              v-if="isEdit && form.is_shared"
              class="rounded-2xl border border-sky-400/20 bg-sky-400/10 p-3 mt-3 text-sm"
              style="color: var(--text-soft)"
            >
              当前渠道已开启共享，可前往共享管理调整可访问用户范围。
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="saveMutation.isPending.value"
          >
            <Save class="w-4 h-4" />
            {{ saveMutation.isPending.value ? '保存中...' : isEdit ? '保存修改' : '创建渠道' }}
          </button>

          <button
            v-if="isEdit"
            type="button"
            class="btn btn-ghost"
            :disabled="testMutation.isPending.value"
            @click="test"
          >
            <Send class="w-4 h-4" />
            {{ testMutation.isPending.value ? '发送中...' : '发送测试' }}
          </button>

          <RouterLink to="/notifiers" class="btn btn-secondary">
            取消
          </RouterLink>
        </div>
      </form>
    </template>
  </div>
</template>