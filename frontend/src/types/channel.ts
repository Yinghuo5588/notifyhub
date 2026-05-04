export interface FilterRule {
  id: number
  channel_id: number
  name: string
  field_path: string
  match_type: 'keyword' | 'regex'
  pattern: string
  mode: 'whitelist' | 'blacklist'
  is_active: boolean
  created_at?: string | null
}

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
  filter_rules?: FilterRule[]
}

export interface ChannelPayload {
  name: string
  description: string
  template_id: number | null
  notifier_config_id: number | null
  is_active: boolean
  is_shared: boolean
}

export interface ChannelFormOptions {
  templates: Array<{
    id: number
    name: string
    description: string
    body_format: string
    is_shared: boolean
  }>
  notifiers: Array<{
    id: number
    name: string
    notifier_type: string
    is_active: boolean
    is_shared: boolean
  }>
}

export interface FilterRulePayload {
  name: string
  field_path: string
  match_type: 'keyword' | 'regex'
  pattern: string
  mode: 'whitelist' | 'blacklist'
  is_active: boolean
}