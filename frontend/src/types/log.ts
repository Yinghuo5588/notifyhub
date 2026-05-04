export interface LogChannelOption {
  id: number
  name: string
}

export interface WebhookLogItem {
  id: number
  channel_id: number
  channel_name: string
  content_type: string
  ip_address: string
  filter_passed: boolean
  filter_detail: string
  data_preview?: string
  created_at?: string | null
}

export interface WebhookLogDetail extends WebhookLogItem {
  request_headers: Record<string, unknown>
  request_body: string
  parsed_data: unknown
}

export interface LogListResp {
  items: WebhookLogItem[]
  page: number
  page_size: number
  total: number
  total_pages: number
  filters: {
    channel_id: string
    keyword: string
  }
  channels: LogChannelOption[]
}