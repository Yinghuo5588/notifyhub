<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { Eye, FileText, RefreshCw, Save } from 'lucide-vue-next'

import {
  createTemplateApi,
  extractTemplateVariablesApi,
  getTemplateApi,
  previewTemplateApi,
  updateTemplateApi,
} from '@/api/templates'
import { getErrorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import TemplatePreview from '@/components/business/TemplatePreview.vue'
import type { TemplatePayload } from '@/types/template'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()
const queryClient = useQueryClient()

const templateId = computed(() => {
  const raw = route.params.id
  return raw ? Number(raw) : null
})

const isEdit = computed(() => !!templateId.value)

const form = reactive<TemplatePayload>({
  name: '',
  description: '',
  subject_template: "[通知] {{ title | default('新消息') }}",
  body_template: '收到新通知:\n{{ data | tojson(indent=2) }}',
  body_format: 'text',
  sample_data: '{\n "title": "测试标题",\n "message": "测试内容"\n}',
  is_shared: false,
})

const variables = ref<string[]>([])
const previewSubject = ref('')
const previewBody = ref('')
const localError = ref('')

const {
  data: item,
  isLoading,
  isError,
  refetch,
} = useQuery({
  queryKey: computed(() => ['template', templateId.value]),
  queryFn: () => getTemplateApi(templateId.value!),
  enabled: computed(() => !!templateId.value),
})

watch(
  item,
  value => {
    if (!value) return

    form.name = value.name
    form.description = value.description || ''
    form.subject_template = value.subject_template || ''
    form.body_template = value.body_template || ''
    form.body_format = value.body_format === 'html' ? 'html' : 'text'
    form.sample_data = value.sample_data || '{}'
    form.is_shared = value.is_shared
    variables.value = value.variables || []
  },
  { immediate: true },
)

const saveMutation = useMutation({
  mutationFn: async () => {
    localError.value = ''

    if (!form.name.trim()) {
      throw new Error('模板名称不能为空')
    }

    if (isEdit.value && templateId.value) {
      return updateTemplateApi(templateId.value, form)
    }

    return createTemplateApi(form)
  },
  onSuccess: data => {
    toast.success(isEdit.value ? '模板已保存' : '模板已创建')

    queryClient.invalidateQueries({ queryKey: ['templates'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })

    if (isEdit.value) {
      queryClient.invalidateQueries({ queryKey: ['template', templateId.value] })
    } else {
      router.replace(`/templates/${data.id}/edit`)
    }
  },
  onError: err => {
    localError.value = getErrorMessage(err)
  },
})

const previewMutation = useMutation({
  mutationFn: () => {
    return previewTemplateApi({
      subject_template: form.subject_template,
      body_template: form.body_template,
      sample_data: form.sample_data,
    })
  },
  onSuccess: data => {
    previewSubject.value = data.subject
    previewBody.value = data.body
    toast.success('预览已更新')
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const variableMutation = useMutation({
  mutationFn: () => extractTemplateVariablesApi({ sample_data: form.sample_data }),
  onSuccess: data => {
    variables.value = data.variables
    toast.success(`已提取 ${data.variables.length} 个变量`)
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

function submit() {
  saveMutation.mutate()
}

function preview() {
  previewMutation.mutate()
}

function extractVars() {
  variableMutation.mutate()
}

function insertVar(name: string) {
  const tag = `{{ ${name} }}`
  form.body_template += form.body_template.endsWith('\n') ? tag : `\n${tag}`
  toast.success(`已插入变量 ${name}`)
}

function formatSampleJson() {
  try {
    const parsed = JSON.parse(form.sample_data || '{}')
    form.sample_data = JSON.stringify(parsed, null, 2)
    toast.success('JSON 已格式化')
  } catch {
    toast.error('示例数据不是有效 JSON')
  }
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col gap-3">
        <RouterLink to="/templates" class="text-sm text-brand hover:underline">
          返回模板列表
        </RouterLink>

        <div>
          <div
            class="text-xs uppercase tracking-[0.28em]"
            style="color: var(--muted)"
          >
            Template Studio
          </div>

          <h2 class="page-title mt-2">
            {{ isEdit ? '编辑模板' : '新建模板' }}
          </h2>

          <p class="page-subtitle">
            使用 Jinja2 语法渲染标题和正文，可通过示例 JSON 即时预览。
          </p>
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

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div class="lg:col-span-2">
        <form @submit.prevent="submit">
          <div class="form-card space-y-4">
            <div class="flex items-center gap-2">
              <FileText class="w-5 h-5 text-brand" />
              <h3 class="text-lg font-semibold" style="color: var(--text)">
                模板内容
              </h3>
            </div>

            <div
              v-if="localError"
              class="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300"
            >
              {{ localError }}
            </div>

            <div>
              <label>模板名称 *</label>
              <input
                v-model="form.name"
                type="text"
                required
                placeholder="如：Emby 入库通知"
              >
            </div>

            <div>
              <label>描述</label>
              <input
                v-model="form.description"
                type="text"
                placeholder="可选"
              >
            </div>

            <label
              v-if="auth.user?.is_admin"
              class="flex items-center gap-3 mb-0 cursor-pointer"
            >
              <input
                v-model="form.is_shared"
                type="checkbox"
                class="w-4 h-4"
              >

              <span class="text-sm" style="color: var(--text-soft)">
                设为共享模板，普通用户仅可见标题和简介
              </span>
            </label>

            <div>
              <label>通知标题模板</label>
              <input
                v-model="form.subject_template"
                type="text"
                class="font-mono text-sm"
              >
            </div>

            <div>
              <label>正文模板，Jinja2 语法</label>
              <textarea
                v-model="form.body_template"
                rows="14"
                class="font-mono text-sm"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label>正文格式</label>
                <select v-model="form.body_format">
                  <option value="text">
                    纯文本
                  </option>
                  <option value="html">
                    HTML
                  </option>
                </select>
              </div>

              <div class="flex items-end">
                <button
                  type="button"
                  class="btn btn-ghost w-full"
                  :disabled="previewMutation.isPending.value"
                  @click="preview"
                >
                  <Eye class="w-4 h-4" />
                  {{ previewMutation.isPending.value ? '预览中...' : '即时预览' }}
                </button>
              </div>
            </div>

            <div>
              <div class="flex items-center justify-between gap-3 mb-2">
                <label class="mb-0">示例数据 JSON</label>

                <button
                  type="button"
                  class="text-xs text-brand hover:underline"
                  @click="formatSampleJson"
                >
                  格式化
                </button>
              </div>

              <textarea
                v-model="form.sample_data"
                rows="8"
                class="font-mono text-sm"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="saveMutation.isPending.value"
            >
              <Save class="w-4 h-4" />
              {{ saveMutation.isPending.value ? '保存中...' : isEdit ? '保存修改' : '创建模板' }}
            </button>

            <RouterLink to="/templates" class="btn btn-secondary">
              取消
            </RouterLink>
          </div>
        </form>
      </div>

      <div class="space-y-4">
        <div class="form-card">
          <div class="flex items-center justify-between gap-3 mb-4">
            <h3 class="text-lg font-semibold" style="color: var(--text)">
              变量助手
            </h3>

            <button
              type="button"
              class="btn btn-ghost sm:w-auto"
              :disabled="variableMutation.isPending.value"
              @click="extractVars"
            >
              <RefreshCw class="w-4 h-4" />
              提取
            </button>
          </div>

          <div v-if="variables.length" class="space-y-1 max-h-64 overflow-y-auto">
            <button
              v-for="name in variables"
              :key="name"
              type="button"
              class="block w-full text-left px-3 py-2 text-xs font-mono text-brand hover:bg-sky-400/10 rounded-xl transition truncate"
              :title="`点击插入 {{ ${name} }}`"
              @click="insertVar(name)"
            >
              {{ name }}
            </button>
          </div>

          <p v-else class="helper-text text-xs">
            暂无变量。可以点击"提取"，从示例 JSON 中生成变量列表。
          </p>
        </div>

        <div class="form-card">
          <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
            语法速查
          </h3>

          <div class="space-y-3 text-xs" style="color: var(--muted)" v-pre>
            <div>
              <div class="font-medium" style="color: var(--text)">
                变量输出
              </div>
              <code class="bg-black/10 px-2 py-1 rounded-lg inline-block mt-1">
                {{ '{{ name }}' }}
              </code>
            </div>

            <div>
              <div class="font-medium" style="color: var(--text)">
                默认值
              </div>
              <code class="bg-black/10 px-2 py-1 rounded-lg inline-block mt-1">
                {{ '{{ name | default("未知") }}' }}
              </code>
            </div>

            <div>
              <div class="font-medium" style="color: var(--text)">
                条件判断
              </div>
              <code class="bg-black/10 px-2 py-1 rounded-lg block mt-1">
                {{ '{% if x is defined %}...{% endif %}' }}
              </code>
            </div>

            <div>
              <div class="font-medium" style="color: var(--text)">
                内置时间
              </div>
              <code class="bg-black/10 px-2 py-1 rounded-lg inline-block mt-1">
                {{ '{{ _timestamp }}' }}
              </code>
            </div>
          </div>
        </div>

        <TemplatePreview
          :subject="previewSubject"
          :body="previewBody"
          :loading="previewMutation.isPending.value"
        />
      </div>
    </div>
  </div>
</template>