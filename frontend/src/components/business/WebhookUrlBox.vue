<script setup lang="ts">
import { Copy, RefreshCw } from 'lucide-vue-next'
import { copyText } from '@/utils/format'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{
  url: string
  tokenPreview?: string
  canRegenerate?: boolean
  regenerating?: boolean
}>()

const emit = defineEmits<{
  regenerate: []
}>()

const toast = useToastStore()

async function copy() {
  await copyText(props.url)
  toast.success('Webhook 地址已复制')
}
</script>

<template>
  <div class="form-card">
    <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
      Webhook 地址
    </h3>

    <div class="space-y-3">
      <div>
        <label>接收地址</label>

        <div class="flex flex-col sm:flex-row gap-2">
          <input
            :value="url"
            readonly
            class="font-mono text-xs"
          >

          <button
            type="button"
            class="btn btn-primary sm:w-auto"
            @click="copy"
          >
            <Copy class="w-4 h-4" />
            复制
          </button>
        </div>

        <p class="helper-text text-xs mt-2">
          将此地址填入 Emby、青龙、Jellyfin 等应用的 Webhook 设置中。
        </p>
      </div>

      <div
        v-if="tokenPreview"
        class="flex flex-col sm:flex-row sm:items-center gap-2 text-sm"
        style="color: var(--muted)"
      >
        <span>Token</span>

        <code class="rounded-xl bg-black/10 px-3 py-2 font-mono text-xs">
          {{ tokenPreview }}
        </code>

        <button
          v-if="canRegenerate"
          type="button"
          class="text-xs text-rose-400 hover:underline sm:w-auto"
          :disabled="regenerating"
          @click="emit('regenerate')"
        >
          <RefreshCw class="w-3 h-3 inline mr-1" />
          {{ regenerating ? '生成中...' : '重新生成' }}
        </button>
      </div>
    </div>
  </div>
</template>