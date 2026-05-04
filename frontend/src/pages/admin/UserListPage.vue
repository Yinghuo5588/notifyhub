<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { KeyRound, Plus, Trash2, Users } from 'lucide-vue-next'

import {
  batchAdminUsersApi,
  createAdminUserApi,
  deleteAdminUserApi,
  getAdminUsersApi,
  resetAdminUserPasswordApi,
  toggleAdminUserApi,
} from '@/api/admin'
import { getErrorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatDateTime } from '@/utils/format'

const auth = useAuthStore()
const toast = useToastStore()
const queryClient = useQueryClient()

const selected = ref<number[]>([])
const resetUserId = ref<number | null>(null)
const resetPassword = ref('')

const form = reactive({
  username: '',
  password: '',
  email: '',
  is_admin: false,
})

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['admin-users'],
  queryFn: getAdminUsersApi,
})

const selectedCount = computed(() => selected.value.length)

const createMutation = useMutation({
  mutationFn: createAdminUserApi,
  onSuccess: () => {
    toast.success('用户已创建')
    form.username = ''
    form.password = ''
    form.email = ''
    form.is_admin = false
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const toggleMutation = useMutation({
  mutationFn: toggleAdminUserApi,
  onSuccess: () => {
    toast.success('用户状态已更新')
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const deleteMutation = useMutation({
  mutationFn: deleteAdminUserApi,
  onSuccess: () => {
    toast.success('用户已删除')
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const resetMutation = useMutation({
  mutationFn: ({ id, password }: { id: number; password: string }) =>
    resetAdminUserPasswordApi(id, password),
  onSuccess: () => {
    toast.success('密码已重置')
    resetUserId.value = null
    resetPassword.value = ''
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

const batchMutation = useMutation({
  mutationFn: batchAdminUsersApi,
  onSuccess: data => {
    toast.success(`已处理 ${data.count} 个用户`)
    selected.value = []
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  },
  onError: err => toast.error(getErrorMessage(err)),
})

function createUser() {
  if (!form.username.trim()) {
    toast.error('请输入用户名')
    return
  }

  if (form.password.length < 6) {
    toast.error('密码至少 6 位')
    return
  }

  createMutation.mutate({ ...form })
}

function toggleSelect(id: number) {
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter(item => item !== id)
  } else {
    selected.value.push(id)
  }
}

function selectAll() {
  const ids = (data.value || [])
    .filter(item => item.id !== auth.user?.id)
    .map(item => item.id)

  selected.value = selected.value.length === ids.length ? [] : ids
}

function removeUser(id: number) {
  if (!window.confirm('确定删除此用户？该用户所有数据也会被清除。')) return
  deleteMutation.mutate(id)
}

function batch(action: 'enable' | 'disable' | 'delete') {
  if (!selected.value.length) {
    toast.warning('请先选择用户')
    return
  }

  const label = action === 'enable' ? '启用' : action === 'disable' ? '禁用' : '删除'
  if (!window.confirm(`确定${label}选中的 ${selected.value.length} 个用户？`)) return

  batchMutation.mutate({
    action,
    user_ids: selected.value,
  })
}

function submitReset() {
  if (!resetUserId.value) return

  if (resetPassword.value.length < 6) {
    toast.error('密码至少 6 位')
    return
  }

  resetMutation.mutate({
    id: resetUserId.value,
    password: resetPassword.value,
  })
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div>
        <div class="text-xs uppercase tracking-[0.28em]" style="color: var(--muted)">
          Admin
        </div>

        <h2 class="page-title mt-2">
          用户管理
        </h2>

        <p class="page-subtitle">
          创建、启用、禁用、重置密码、批量操作都在这里。
        </p>
      </div>
    </div>

    <div class="form-card mb-4">
      <h3 class="text-lg font-semibold mb-4" style="color: var(--text)">
        创建新用户
      </h3>

      <form class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3" @submit.prevent="createUser">
        <input v-model="form.username" type="text" required placeholder="用户名">
        <input v-model="form.email" type="email" placeholder="邮箱">
        <input v-model="form.password" type="password" required minlength="6" placeholder="初始密码">

        <label class="flex items-center gap-3 mb-0 cursor-pointer">
          <input v-model="form.is_admin" type="checkbox" class="w-4 h-4">
          <span class="text-sm" style="color: var(--text-soft)">管理员</span>
        </label>

        <button
          type="submit"
          class="btn btn-primary"
          :disabled="createMutation.isPending.value"
        >
          <Plus class="w-4 h-4" />
          创建
        </button>
      </form>
    </div>

    <div v-if="selectedCount" class="form-card mb-4">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <span class="text-sm" style="color: var(--text)">
          已选 <strong>{{ selectedCount }}</strong> 个用户
        </span>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <button class="btn btn-ghost" type="button" @click="batch('enable')">
            批量启用
          </button>

          <button class="btn btn-secondary" type="button" @click="batch('disable')">
            批量禁用
          </button>

          <button class="btn btn-danger" type="button" @click="batch('delete')">
            批量删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载用户...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        用户加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <div v-else class="list-card">
      <div class="table-responsive">
        <table class="w-full text-sm min-w-[820px]">
          <thead>
            <tr style="color: var(--muted); border-bottom: 1px solid var(--line)">
              <th class="px-4 py-3 w-10">
                <input type="checkbox" class="w-4 h-4" @change="selectAll">
              </th>
              <th class="text-left px-4 py-3 font-medium">用户名</th>
              <th class="text-left px-4 py-3 font-medium">邮箱</th>
              <th class="text-left px-4 py-3 font-medium">角色</th>
              <th class="text-left px-4 py-3 font-medium">状态</th>
              <th class="text-left px-4 py-3 font-medium">创建时间</th>
              <th class="text-left px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="item in data || []"
              :key="item.id"
              style="border-bottom: 1px solid var(--line)"
            >
              <td class="px-4 py-3">
                <input
                  v-if="item.id !== auth.user?.id"
                  type="checkbox"
                  class="w-4 h-4"
                  :checked="selected.includes(item.id)"
                  @change="toggleSelect(item.id)"
                >
              </td>

              <td class="px-4 py-3 font-medium" style="color: var(--text)">
                <div class="flex items-center gap-2">
                  <Users class="w-4 h-4 text-brand" />
                  {{ item.username }}
                  <span v-if="item.id === auth.user?.id" class="text-xs" style="color: var(--muted)">
                    当前用户
                  </span>
                </div>
              </td>

              <td class="px-4 py-3" style="color: var(--muted)">
                {{ item.email || '-' }}
              </td>

              <td class="px-4 py-3">
                <span class="badge" :class="item.is_admin ? 'badge-purple' : 'badge-gray'">
                  {{ item.is_admin ? '管理员' : '用户' }}
                </span>
              </td>

              <td class="px-4 py-3">
                <span class="badge" :class="item.is_active ? 'badge-green' : 'badge-red'">
                  {{ item.is_active ? '正常' : '禁用' }}
                </span>
              </td>

              <td class="px-4 py-3" style="color: var(--muted)">
                {{ formatDateTime(item.created_at) }}
              </td>

              <td class="px-4 py-3">
                <div v-if="item.id !== auth.user?.id" class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="btn"
                    :class="item.is_active ? 'btn-secondary' : 'btn-ghost'"
                    @click="toggleMutation.mutate(item.id)"
                  >
                    {{ item.is_active ? '禁用' : '启用' }}
                  </button>

                  <button
                    type="button"
                    class="btn btn-ghost"
                    @click="resetUserId = item.id"
                  >
                    <KeyRound class="w-4 h-4" />
                    重置密码
                  </button>

                  <button
                    type="button"
                    class="btn btn-danger"
                    @click="removeUser(item.id)"
                  >
                    <Trash2 class="w-4 h-4" />
                    删除
                  </button>
                </div>

                <span v-else class="text-xs" style="color: var(--muted)">
                  不可操作自己
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      v-if="resetUserId"
      class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
      @click.self="resetUserId = null"
    >
      <div class="glass-panel rounded-[24px] p-6 w-full max-w-sm">
        <h3 class="font-medium mb-4" style="color: var(--text)">
          重置密码
        </h3>

        <form class="space-y-4" @submit.prevent="submitReset">
          <input
            v-model="resetPassword"
            type="password"
            required
            minlength="6"
            placeholder="新密码，至少 6 位"
          >

          <div class="grid grid-cols-2 gap-2">
            <button
              type="button"
              class="btn btn-secondary"
              @click="resetUserId = null"
            >
              取消
            </button>

            <button type="submit" class="btn btn-primary">
              确认重置
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>