export interface AdminUser {
  id: number
  username: string
  email: string
  is_admin: boolean
  is_active: boolean
  must_change_pwd: boolean
  created_at?: string | null
}

export interface AdminUserCreatePayload {
  username: string
  password: string
  email: string
  is_admin: boolean
}

export interface ShareUserItem {
  id: number
  username: string
  email: string
  is_active: boolean
  selected: boolean
  subscription_active?: boolean
  sends_today?: number
}

export interface ShareChannelResp {
  channel: {
    id: number
    name: string
    description: string
    is_shared: boolean
    per_hour_limit: number
    per_day_limit: number
    min_interval: number
    global_hour_limit: number
    global_day_limit: number
  }
  users: ShareUserItem[]
}

export interface ShareChannelPayload {
  user_ids: number[]
  per_hour_limit: number
  per_day_limit: number
  min_interval: number
  global_hour_limit: number
  global_day_limit: number
}

export interface ShareNotifierResp {
  notifier: {
    id: number
    name: string
    notifier_type: string
    is_shared: boolean
  }
  users: ShareUserItem[]
}

export interface ShareTemplateResp {
  template: {
    id: number
    name: string
    description: string
    is_shared: boolean
  }
  users: ShareUserItem[]
}

export interface ShareUsersPayload {
  user_ids: number[]
}