<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { getErrorMessage } from '@/api/http'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)
const error = ref('')

async function submit() {
  if (!form.username || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const user = await auth.login({
      username: form.username,
      password: form.password,
    })

    toast.success('登录成功')

    if (user.must_change_pwd) {
      router.push('/settings')
    } else {
      router.push('/')
    }
  } catch (err) {
    error.value = getErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-md glass-panel rounded-[28px] p-6 sm:p-8">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold" style="color: var(--text)">
        NotifyHub
      </h1>
      <p class="mt-2" style="color: var(--muted)">
        Webhook 通知中继系统
      </p>
      <p class="text-sm mt-1" style="color: var(--muted)">
        登录后进入你的消息指挥台
      </p>
    </div>

    <div
      v-if="error"
      class="mb-4 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300"
    >
      {{ error }}
    </div>

    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label>用户名</label>
        <input
          v-model="form.username"
          type="text"
          required
          autofocus
          autocomplete="username"
          placeholder="请输入用户名"
        >
      </div>

      <div>
        <label>密码</label>
        <input
          v-model="form.password"
          type="password"
          required
          autocomplete="current-password"
          placeholder="请输入密码"
        >
      </div>

      <button
        type="submit"
        class="btn btn-primary w-full"
        :disabled="loading"
      >
        {{ loading ? '登录中...' : '登 录' }}
      </button>
    </form>
  </div>
</template>