<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useMutation, useQuery } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { Save } from 'lucide-vue-next'

import { getShareTemplateApi, saveShareTemplateApi } from '@/api/admin'
import { getErrorMessage } from '@/api/http'
import ShareUserSelector from '@/components/business/ShareUserSelector.vue'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const id = computed(() => Number(route.params.id))
const selectedIds = ref<number[]>([])

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: computed(() => ['share-template', id.value]),
  queryFn: () => getShareTemplateApi(id.value),
})

watch(
  data,
  value => {
    if (!value) return
    selectedIds.value = value.users.filter(u => u.selected).map(u => u.id)
  },
  { immediate: true },
)

const saveMutation = useMutation({
  mutationFn: () => saveShareTemplateApi(id.value, { user_ids: selectedIds.value }),
  onSuccess: () => {
    toast.success('共享设置已保存')
    router.push('/templates')
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col gap-3">
        <RouterLink to="/templates" class="text-sm text-brand hover:underline">
          返回模板列表
        </RouterLink>

        <div>
          <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
            Share Template
          </div>

          <h2 class="page-title mt-2">
            共享模板
          </h2>

          <p class="page-subtitle">
            {{ data?.template.name || '' }}。普通用户仅可见标题和简介，不暴露正文源码。
          </p>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载共享设置...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        共享设置加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else-if="data" class="max-w-3xl space-y-4">
      <ShareUserSelector
        :users="data.users"
        :selected-ids="selectedIds"
        @update="ids => selectedIds = ids"
      />

      <button
        type="button"
        class="btn btn-primary"
        :disabled="saveMutation.isPending.value"
        @click="saveMutation.mutate()"
      >
        <Save class="w-4 h-4" />
        {{ saveMutation.isPending.value ? '保存中...' : '保存共享设置' }}
      </button>
    </div>
  </div>
</template>