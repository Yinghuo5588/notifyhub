export interface DashboardStats {
  channels: number
  templates: number
  notifier_configs: number
  extra_count: number
  today_hooks: number
  today_sent: number
  today_ok: number
  today_fail: number
  today_limited: number
}

export interface RecentLog {
  id: number
  channel_id: number
  notifier_type: string
  subject: string
  body: string
  status: string
  error_message?: string
  retry_count: number
  created_at?: string | null
}

export interface DashboardTrend {
  days: string[]
  success: number[]
  failed: number[]
}

export interface DashboardResp {
  stats: DashboardStats
  recent_logs: RecentLog[]
  trend: DashboardTrend
}