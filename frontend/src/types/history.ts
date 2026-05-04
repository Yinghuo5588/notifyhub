export interface HistoryChannelOption {
  id: number
  name: string
}

export interface HistoryItem {
  id: number
  channel_id: number
  channel_name: string
  webhook_log_id?: number | null
  notifier_type: string
  subject: string
  body_preview?: string
  body?: string
  status: string
  error_message: string
  retry_count: number
  created_at?: string | null
}

export interface HistoryDetail extends HistoryItem {
  body: string
  webhook_log?: {
    id: number
    ip_address: string
    content_type: string
    filter_passed: boolean
    filter_detail: string
    created_at?: string | null
  } | null
}

export interface HistoryListResp {
  items: HistoryItem[]
  page: number
  page_size: number
  total: number
  total_pages: number
  filters: {
    status: string
    channel_id: string
    keyword: string
  }
  channels: HistoryChannelOption[]
}