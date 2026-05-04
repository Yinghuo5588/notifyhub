<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Plus, Save, Trash2 } from 'lucide-vue-next'
import type { FilterRulePayload } from '@/types/channel'

interface FilterRuleLike {
  id: number
  name: string
  field_path: string
  match_type: 'keyword' | 'regex'
  pattern: string
  mode: 'whitelist' | 'blacklist'
  is_active: boolean
}

const props = defineProps<{
  rules: FilterRuleLike[]
  loading?: boolean
}>()

const emit = defineEmits<{
  create: [payload: FilterRulePayload]
  update: [ruleId: number, payload: FilterRulePayload]
  toggle: [ruleId: number]
  remove: [ruleId: number]
}>()

const form = reactive<FilterRulePayload>({
  name: '',
  field_path: '',
  match_type: 'keyword',
  pattern: '',
  mode: 'blacklist',
  is_active: true,
})

const editId = defineModel<number | null>('editId', {
  default: null,
})

watch(editId, id => {
  if (!id) {
    reset()
    return
  }

  const rule = props.rules.find(item => item.id === id)
  if (!rule) return

  form.name = rule.name
  form.field_path = rule.field_path
  form.match_type = rule.match_type
  form.pattern = rule.pattern
  form.mode = rule.mode
  form.is_active = rule.is_active
})

function reset() {
  form.name = ''
  form.field_path = ''
  form.match_type = 'keyword'
  form.pattern = ''
  form.mode = 'blacklist'
  form.is_active = true
  editId.value = null
}

function submit() {
  if (!form.pattern.trim()) return

  const payload: FilterRulePayload = {
    name: form.name,
    field_path: form.field_path,
    match_type: form.match_type,
    pattern: form.pattern,
    mode: form.mode,
    is_active: form.is_active,
  }

  if (editId.value) {
    emit('update', editId.value, payload)
  } else {
    emit('create', payload)
  }

  reset()
}

function edit(rule: FilterRuleLike) {
  editId.value = rule.id
}

function modeText(mode: string) {
  return mode === 'whitelist' ? '白名单' : '黑名单'
}

function matchText(type: string) {
  return type === 'regex' ? '正则' : '关键字'
}
</script>

<template>
  <div class="form-card">
    <h3 class="text-lg font-semibold mb-3" style="color: var(--text)">
      过滤规则
    </h3>

    <p class="helper-text text-xs mb-4">
      白名单：有白名单时必须匹配才发送；黑名单：命中后不发送。字段路径为空表示全文匹配。
    </p>

    <div v-if="rules.length" class="data-list mb-4">
      <div
        v-for="rule in rules"
        :key="rule.id"
        class="list-row"
        :class="rule.mode === 'whitelist' ? 'border-green-400/20' : 'border-rose-400/20'"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div class="flex-1 text-sm">
            <span
              class="font-medium"
              :class="rule.mode === 'whitelist' ? 'text-emerald-400' : 'text-rose-400'"
            >
              {{ modeText(rule.mode) }}
            </span>

            <span style="color: var(--muted)" class="mx-1">|</span>

            <span style="color: var(--text)">
              {{ matchText(rule.match_type) }}
            </span>

            <template v-if="rule.field_path">
              <span style="color: var(--muted)" class="mx-1">|</span>
              <span class="font-mono text-xs" style="color: var(--muted)">
                {{ rule.field_path }}
              </span>
            </template>

            <span style="color: var(--muted)" class="mx-1">|</span>

            <code class="bg-black/10 px-2 py-1 rounded-lg text-xs">
              {{ rule.pattern }}
            </code>

            <span v-if="rule.name" class="ml-1" style="color: var(--muted)">
              ({{ rule.name }})
            </span>

            <span v-if="!rule.is_active" class="text-amber-400 ml-1">
              [已禁用]
            </span>
          </div>

          <div class="grid grid-cols-2 sm:flex gap-2 shrink-0">
            <button class="btn btn-secondary" type="button" @click="edit(rule)">
              编辑
            </button>

            <button class="btn btn-ghost" type="button" @click="emit('toggle', rule.id)">
              {{ rule.is_active ? '禁用' : '启用' }}
            </button>

            <button class="btn btn-danger" type="button" @click="emit('remove', rule.id)">
              <Trash2 class="w-4 h-4" />
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <form
      class="rounded-2xl border border-dashed p-4"
      style="border-color: var(--line)"
      @submit.prevent="submit"
    >
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div>
          <label>规则名称</label>
          <input v-model="form.name" placeholder="可选">
        </div>

        <div>
          <label>字段路径</label>
          <input v-model="form.field_path" placeholder="如 Series.Name，空=全文">
        </div>

        <div>
          <label>匹配方式</label>
          <select v-model="form.match_type">
            <option value="keyword">关键字</option>
            <option value="regex">正则表达式</option>
          </select>
        </div>

        <div>
          <label>模式</label>
          <select v-model="form.mode">
            <option value="blacklist">黑名单</option>
            <option value="whitelist">白名单</option>
          </select>
        </div>

        <div>
          <label>匹配内容 *</label>
          <input v-model="form.pattern" required placeholder="关键字或正则">
        </div>
      </div>

      <label class="flex items-center gap-3 mt-4 mb-0 cursor-pointer">
        <input v-model="form.is_active" type="checkbox" class="w-4 h-4">
        <span class="text-sm" style="color: var(--text-soft)">
          启用规则
        </span>
      </label>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4">
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="loading"
        >
          <Save v-if="editId" class="w-4 h-4" />
          <Plus v-else class="w-4 h-4" />
          {{ editId ? '保存规则' : '添加规则' }}
        </button>

        <button
          v-if="editId"
          type="button"
          class="btn btn-secondary"
          @click="reset"
        >
          取消编辑
        </button>
      </div>
    </form>
  </div>
</template>