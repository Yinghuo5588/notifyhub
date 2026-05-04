export interface SubscriptionFilter {
  id: number
  subscription_id: number
  name: string
  field_path: string
  match_type: 'keyword' | 'regex'
  pattern: string
  mode: 'whitelist' | 'blacklist'
  is_active: boolean
  created_at?: string | null
}

export interface SubscriptionLimits {
  per_hour_limit: number
  per_day_limit: number
  min_interval: number
  global_hour_limit: number
  global_day_limit: number
}

export interface Subscription {
  id: number
  channel_id: number
  channel_name: string
  channel_description: string
  template_id: number | null
  template_name: string
  notifier_config_id: number | null
  notifier_name: string
  notifier_type: string
  custom_recipients: string
  is_active: boolean
  sends_today: number
  sends_this_hour: number
  last_send_at?: string | null
  hour_reset_at?: string | null
  day_reset_at?: string | null
  created_at?: string | null
  limits?: SubscriptionLimits | null
  filters?: SubscriptionFilter[]
}

export interface SubscriptionUpdatePayload {
  template_id: number | null
  notifier_config_id: number | null
  custom_recipients: string
  is_active: boolean
}

export interface SubscriptionFilterPayload {
  name: string
  field_path: string
  match_type: 'keyword' | 'regex'
  pattern: string
  mode: 'whitelist' | 'blacklist'
  is_active: boolean
}

export interface SubscriptionFormOptions {
  my_templates: Array<{
    id: number
    name: string
    description: string
    body_format: string
    is_shared: boolean
  }>
  shared_templates: Array<{
    id: number
    name: string
    description: string
    body_format: string
    is_shared: boolean
  }>
  my_notifiers: Array<{
    id: number
    name: string
    notifier_type: string
    is_shared: boolean
  }>
  shared_notifiers: Array<{
    id: number
    name: string
    notifier_type: string
    is_shared: boolean
  }>
}