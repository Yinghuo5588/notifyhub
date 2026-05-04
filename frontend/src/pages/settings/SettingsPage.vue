<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useMutation, useQuery } from '@tanstack/vue-query'
import { KeyRound, Save, Settings, UserRound } from 'lucide-vue-next'

import {
  getProfileApi,
  updatePasswordApi,
  updateProfileApi,
} from '@/api/settings'
import { getErrorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatDateTime } from '@/utils/format'

const auth = useAuthStore()
const toast = useToastStore()

const profileForm = reactive({
  username: '',
  email: '',
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordError = ref('')

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['settings-profile'],
  queryFn: getProfileApi,
})

const profileMutation = useMutation({
  mutationFn: updateProfileApi,
  onSuccess: user => {
    auth.user = user
    toast.success('资料已更新')
  },
  onError: err => {
    toast.error(getErrorMessage(err))
  },
})

const passwordMutation = useMutation({
  mutationFn: updatePasswordApi,
  onSuccess: user => {
    auth.user = user
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordError.value = ''
    toast.success('密码修改成功')
  },
  onError: err => {
    passwordError.value = getErrorMessage(err)
  },
})

onMounted(() => {
  if (auth.user) {
    profileForm.username = auth.user.username
    profileForm.email = auth.user.email || ''
  }
})

function syncProfile() {
  if (!data.value) return
  profileForm.username = data.value.username
  profileForm.email = data.value.email || ''
}

function saveProfile() {
  if (!profileForm.username.trim()) {
    toast.error('用户名不能为空')
    return
  }

  profileMutation.mutate({
    username: profileForm.username,
    email: profileForm.email,
  })
}

function savePassword() {
  passwordError.value = ''

  if (!passwordForm.old_password || !passwordForm.new_password) {
    passwordError.value = '请填写原密码和新密码'
    return
  }

  if (passwordForm.new_password.length < 6) {
    passwordError.value = '新密码至少 6 位'
    return
  }

  if (passwordForm.new_password !== passwordForm.confirm_password) {
    passwordError.value = '两次密码不一致'
    return
  }

  passwordMutation.mutate({
    old_password: passwordForm.old_password,
    new_password: passwordForm.new_password,
    confirm_password: passwordForm.confirm_password,
  })
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div>
        <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
          Settings
        </div>

        <h2 class="page-title mt-2">
          系统设置
        </h2>

        <p class="page-subtitle">
          账号资料、安全设置和基础信息都放在这里。
        </p>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载设置...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        设置加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else class="max-w-3xl space-y-4">
      <div v-if="data" style="display: none">
        {{ syncProfile() }}
      </div>

      <div
        v-if="auth.user?.must_change_pwd"
        class="rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm text-amber-300"
      >
        当前账号需要尽快修改默认密码后再继续使用。
      </div>

      <div class="form-card">
        <div class="flex items-center gap-2 mb-4">
          <UserRound class="w-5 h-5 text-brand" />
          <h3 class="text-lg font-semibold" style="color: var(--text)">
            个人信息
          </h3>
        </div>

        <form class="space-y-4" @submit.prevent="saveProfile">
          <div>
            <label>用户名</label>
            <input
              v-model="profileForm.username"
              type="text"
              required
              placeholder="输入用户名"
            >
          </div>

          <div>
            <label>邮箱</label>
            <input
              v-model="profileForm.email"
              type="email"
              placeholder="your@email.com"
            >
          </div>

          <button
            type="submit"
            class="btn btn-primary sm:w-auto"
            :disabled="profileMutation.isPending.value"
          >
            <Save class="w-4 h-4" />
            {{ profileMutation.isPending.value ? '保存中...' : '保存资料' }}
          </button>
        </form>
      </div>

      <div class="form-card">
        <div class="flex items-center gap-2 mb-4">
          <KeyRound class="w-5 h-5 text-brand" />
          <h3 class="text-lg font-semibold" style="color: var(--text)">
            修改密码
          </h3>
        </div>

        <div
          v-if="passwordError"
          class="mb-4 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300"
        >
          {{ passwordError }}
        </div>

        <form class="space-y-4" @submit.prevent="savePassword">
          <div>
            <label>原密码</label>
            <input
              v-model="passwordForm.old_password"
              type="password"
              required
              autocomplete="current-password"
            >
          </div>

          <div>
            <label>新密码，至少 6 位</label>
            <input
              v-model="passwordForm.new_password"
              type="password"
              required
              minlength="6"
              autocomplete="new-password"
            >
          </div>

          <div>
            <label>确认新密码</label>
            <input
              v-model="passwordForm.confirm_password"
              type="password"
              required
              minlength="6"
              autocomplete="new-password"
            >
          </div>

          <button
            type="submit"
            class="btn btn-ghost sm:w-auto"
            :disabled="passwordMutation.isPending.value"
          >
            <KeyRound class="w-4 h-4" />
            {{ passwordMutation.isPending.value ? '修改中...' : '修改密码' }}
          </button>
        </form>
      </div>

      <div class="form-card">
        <div class="flex items-center gap-2 mb-4">
          <Settings class="w-5 h-5 text-brand" />
          <h3 class="text-lg font-semibold" style="color: var(--text)">
            账号信息
          </h3>
        </div>

        <div class="text-sm space-y-2" style="color: var(--muted)">
          <div>
            角色：
            <span style="color: var(--text)">
              {{ auth.user?.is_admin ? '管理员' : '普通用户' }}
            </span>
          </div>

          <div>
            状态：
            <span
              class="badge"
              :class="auth.user?.is_active ? 'badge-green' : 'badge-red'"
            >
              {{ auth.user?.is_active ? '正常' : '禁用' }}
            </span>
          </div>

          <div>
            注册时间：
            <span style="color: var(--text)">
              {{ formatDateTime(auth.user?.created_at) || '未知' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>