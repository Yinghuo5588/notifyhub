<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import {
  Bell,
  Check,
  FileText,
  History,
  Radio,
  Users,
  Webhook,
  X,
  Zap,
} from 'lucide-vue-next'

import { getDashboardApi } from '@/api/dashboard'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['dashboard'],
  queryFn: getDashboardApi,
})

function statusText(status: string) {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    rate_limited: '限频',
    filtered: '过滤',
    pending: '处理中',
  }

  return map[status] || status
}

function statusClass(status: string) {
  if (status === 'success') return 'badge-green'
  if (status === 'failed') return 'badge-red'
  if (status === 'rate_limited') return 'badge-yellow'
  if (status === 'filtered') return 'badge-gray'
  return 'badge-blue'
}

function formatTime(value?: string | null) {
  if (!value) return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const now = Date.now()
  const diff = Math.floor((now - date.getTime()) / 1000)

  if (diff >= 0 && diff < 60) return '刚刚'
  if (diff >= 60 && diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff >= 3600 && diff < 86400) return `${Math.floor(diff / 3600)} 小时前`

  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')

  return `${month}-${day} ${hour}:${minute}`
}

function trendMax(success: number[], failed: number[]) {
  const max = Math.max(...success, ...failed, 1)
  return max || 1
}
</script>

<template>
  <div>
    <div class="page-hero hero-card">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div
            class="text-xs uppercase tracking-[0.28em]"
            style="color: var(--muted)"
          >
            Control Deck
          </div>

          <h2 class="page-title mt-2">
            仪表盘
          </h2>

          <p class="page-subtitle">
            欢迎回来，{{ auth.user?.username }}。这里是你的通知流量观测台。
          </p>
        </div>

        <div
          class="glass-panel rounded-2xl px-4 py-3 text-sm max-w-sm"
          style="color: var(--muted)"
        >
          <div class="font-semibold" style="color: var(--text)">
            今日概览
          </div>
          <div class="mt-1">
            如果今天消息很多，别慌，系统会把它们排好队。
          </div>
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="form-card">
      正在加载仪表盘数据...
    </div>

    <div v-else-if="isError" class="form-card">
      <div class="text-rose-400 mb-3">
        仪表盘加载失败
      </div>

      <button class="btn btn-primary sm:w-auto" @click="refetch()">
        重试
      </button>
    </div>

    <template v-else-if="data">
      <!-- 顶部核心统计 -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4">
        <div class="stat-card">
          <Webhook class="w-8 h-8 text-brand mb-3" />
          <div class="stat-value">
            {{ data.stats.channels }}
          </div>
          <div class="stat-label text-sm mt-1">
            我的频道
          </div>
        </div>

        <div class="stat-card">
          <Users
            v-if="auth.user?.is_admin"
            class="w-8 h-8 text-brand mb-3"
          />
          <Radio
            v-else
            class="w-8 h-8 text-brand mb-3"
          />

          <div class="stat-value">
            {{ data.stats.extra_count }}
          </div>
          <div class="stat-label text-sm mt-1">
            {{ auth.user?.is_admin ? '系统用户' : '共享订阅' }}
          </div>
        </div>

        <div class="stat-card">
          <Check class="w-8 h-8 text-emerald-400 mb-3" />
          <div class="stat-value text-emerald-400">
            {{ data.stats.today_ok }}
          </div>
          <div class="stat-label text-sm mt-1">
            今日成功
          </div>
        </div>

        <div class="stat-card">
          <X class="w-8 h-8 text-rose-400 mb-3" />
          <div class="stat-value text-rose-400">
            {{ data.stats.today_fail }}
          </div>
          <div class="stat-label text-sm mt-1">
            今日失败
          </div>
        </div>
      </div>

      <!-- 今日小统计 -->
      <div class="grid grid-cols-3 gap-3 sm:gap-4 mb-4">
        <div class="form-card text-center">
          <Radio class="w-6 h-6 mx-auto text-brand mb-2" />
          <div class="text-xl font-bold">
            {{ data.stats.today_hooks }}
          </div>
          <div class="helper-text text-xs mt-1">
            今日接收
          </div>
        </div>

        <div class="form-card text-center">
          <Bell class="w-6 h-6 mx-auto text-brand mb-2" />
          <div class="text-xl font-bold">
            {{ data.stats.today_sent }}
          </div>
          <div class="helper-text text-xs mt-1">
            今日处理
          </div>
        </div>

        <div class="form-card text-center">
          <Zap class="w-6 h-6 mx-auto text-amber-400 mb-2" />
          <div class="text-xl font-bold text-amber-400">
            {{ data.stats.today_limited }}
          </div>
          <div class="helper-text text-xs mt-1">
            今日限频
          </div>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <RouterLink to="/channels" class="action-card">
          <div class="flex items-center gap-3">
            <Webhook class="w-6 h-6 text-brand" />
            <div class="text-lg font-semibold" style="color: var(--text)">
              Webhook 频道
            </div>
          </div>

          <p class="muted-text text-sm mt-2">
            管理 Webhook 接收端点，复制接收地址，配置模板和通知渠道。
          </p>
        </RouterLink>

        <RouterLink
          :to="auth.user?.is_admin ? '/admin/users' : '/subscriptions'"
          class="action-card"
        >
          <div class="flex items-center gap-3">
            <Users
              v-if="auth.user?.is_admin"
              class="w-6 h-6 text-brand"
            />
            <Radio
              v-else
              class="w-6 h-6 text-brand"
            />

            <div class="text-lg font-semibold" style="color: var(--text)">
              {{ auth.user?.is_admin ? '用户管理' : '共享订阅' }}
            </div>
          </div>

          <p class="muted-text text-sm mt-2">
            {{
              auth.user?.is_admin
                ? '创建用户、启用禁用账号、管理系统协作边界。'
                : '查看管理员共享给你的频道，并配置自己的订阅。'
            }}
          </p>
        </RouterLink>

        <RouterLink to="/notifiers" class="action-card">
          <div class="flex items-center gap-3">
            <Bell class="w-6 h-6 text-brand" />
            <div class="text-lg font-semibold" style="color: var(--text)">
              通知渠道
            </div>
          </div>

          <p class="muted-text text-sm mt-2">
            配置邮件、飞书等通知发送方式，让消息真正飞出去。
          </p>
        </RouterLink>
      </div>

      <!-- 7天趋势 -->
      <div class="glass-panel rounded-2xl p-5 mb-4">
        <div class="flex items-center justify-between mb-4 gap-3">
          <h3 class="font-semibold" style="color: var(--text)">
            7 天趋势
          </h3>

          <div class="flex items-center gap-4 text-xs">
            <span class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-emerald-400 inline-block" />
              <span style="color: var(--muted)">成功</span>
            </span>

            <span class="flex items-center gap-1.5">
              <span class="w-3 h-3 rounded-full bg-rose-400 inline-block" />
              <span style="color: var(--muted)">失败</span>
            </span>
          </div>
        </div>

        <div class="grid grid-cols-7 gap-2 items-end h-40">
          <div
            v-for="(day, idx) in data.trend.days"
            :key="day"
            class="flex flex-col items-center justify-end h-full gap-2"
          >
            <div class="flex items-end gap-1 h-28">
              <div
                class="w-3 sm:w-5 rounded-t-lg bg-emerald-400/90"
                :style="{
                  height:
                    Math.max(
                      4,
                      (data.trend.success[idx] / trendMax(data.trend.success, data.trend.failed)) * 100
                    ) + '%',
                }"
                :title="`成功 ${data.trend.success[idx]}`"
              />

              <div
                class="w-3 sm:w-5 rounded-t-lg bg-rose-400/90"
                :style="{
                  height:
                    Math.max(
                      4,
                      (data.trend.failed[idx] / trendMax(data.trend.success, data.trend.failed)) * 100
                    ) + '%',
                }"
                :title="`失败 ${data.trend.failed[idx]}`"
              />
            </div>

            <div
              class="text-[11px] sm:text-xs whitespace-nowrap"
              style="color: var(--muted)"
            >
              {{ day }}
            </div>
          </div>
        </div>
      </div>

      <!-- 最近通知 -->
      <div class="list-card">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h3 class="font-semibold text-lg" style="color: var(--text)">
            最近通知
          </h3>

          <RouterLink to="/history" class="btn btn-ghost sm:w-auto">
            查看全部
          </RouterLink>
        </div>

        <div v-if="data.recent_logs.length" class="data-list">
          <RouterLink
            v-for="log in data.recent_logs"
            :key="log.id"
            :to="`/history/${log.id}`"
            class="list-row block hover:border-sky-400/30 transition no-underline"
          >
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div
                  class="text-sm truncate"
                  style="color: var(--text)"
                >
                  {{ log.subject || '(无标题)' }}
                </div>

                <div
                  class="text-xs mt-1"
                  style="color: var(--muted)"
                >
                  {{ formatTime(log.created_at) }}
                  <span class="mx-1">·</span>
                  {{ log.notifier_type }}
                  <span v-if="log.retry_count > 0" class="mx-1">·</span>
                  <span v-if="log.retry_count > 0">
                    重试 {{ log.retry_count }} 次
                  </span>
                </div>

                <div
                  v-if="log.error_message"
                  class="text-xs text-rose-400 mt-1 truncate"
                >
                  {{ log.error_message }}
                </div>
              </div>

              <span class="badge shrink-0" :class="statusClass(log.status)">
                {{ statusText(log.status) }}
              </span>
            </div>
          </RouterLink>
        </div>

        <div v-else class="empty-state">
          <div class="text-lg font-semibold" style="color: var(--text)">
            还没有最近通知
          </div>

          <p class="page-subtitle">
            等第一条消息跑起来，这里就会开始热闹。
          </p>
        </div>
      </div>
    </template>
  </div>
</template>