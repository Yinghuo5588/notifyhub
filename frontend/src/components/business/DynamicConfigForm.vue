<script setup lang="ts">
import { watch } from 'vue'
import type { NotifierFieldSchema } from '@/types/notifier'

const props = defineProps<{
  schema: Record<string, NotifierFieldSchema>
}>()

const model = defineModel<Record<string, any>>({
  required: true,
})

function defaultValue(field: NotifierFieldSchema) {
  if (field.default !== undefined) return field.default
  if (field.type === 'checkbox') return false
  if (field.type === 'number') return ''
  return ''
}

function ensureDefaults() {
  for (const [key, field] of Object.entries(props.schema)) {
    if (model.value[key] === undefined || model.value[key] === null) {
      model.value[key] = defaultValue(field)
    }
  }
}

watch(
  () => props.schema,
  () => {
    ensureDefaults()
  },
  { immediate: true, deep: true },
)
</script>

<template>
  <div class="space-y-4">
    <template
      v-for="(field, key) in schema"
      :key="key"
    >
      <label
        v-if="field.type === 'checkbox'"
        class="flex items-center gap-3 mb-0 cursor-pointer"
      >
        <input
          v-model="model[key]"
          type="checkbox"
          class="w-4 h-4"
        >

        <span class="text-sm" style="color: var(--text-soft)">
          {{ field.label }}
        </span>
      </label>

      <div v-else-if="field.type === 'textarea'">
        <label>
          {{ field.label }}
          <span v-if="field.required" class="text-rose-400">*</span>
        </label>

        <textarea
          v-model="(model[key] as any)"
          :required="field.required"
          :placeholder="field.placeholder"
          rows="4"
        />
      </div>

      <div v-else-if="field.type === 'select'">
        <label>
          {{ field.label }}
          <span v-if="field.required" class="text-rose-400">*</span>
        </label>

        <select
          v-model="model[key]"
          :required="field.required"
        >
          <option value="">
            请选择
          </option>

          <option
            v-for="opt in field.options || []"
            :key="String(opt.value)"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>
      </div>

      <div v-else-if="field.type === 'json'">
        <label>
          {{ field.label }}
          <span v-if="field.required" class="text-rose-400">*</span>
        </label>

        <textarea
          v-model="(model[key] as any)"
          :required="field.required"
          :placeholder="field.placeholder || '{}'"
          rows="6"
          class="font-mono text-xs"
        />
      </div>

      <div v-else>
        <label>
          {{ field.label }}
          <span v-if="field.required" class="text-rose-400">*</span>
        </label>

        <input
          v-model="model[key]"
          :type="
            field.type === 'password'
              ? 'password'
              : field.type === 'number'
              ? 'number'
              : field.type === 'url'
              ? 'url'
              : 'text'
          "
          :required="field.required"
          :placeholder="field.placeholder"
        >
      </div>
    </template>
  </div>
</template>