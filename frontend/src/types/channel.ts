export interface Channel {
  id: number
  name: string
  description: string
  channel_uuid: string
  token: string
  template_id: number | null
  template_name: string
  notifier_config_id: number | null
  notifier_name: string
  notifier_type: string
  is_active: boolean
  is_shared: boolean
  per_hour_limit: number
  per_day_limit: number
  min_interval: number
  global_hour_limit: number
  global_day_limit: number
  created_at?: string | null
  updated_at?: string | null
}