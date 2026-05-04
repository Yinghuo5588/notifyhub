import { http } from './http'
import type { LogListResp, WebhookLogDetail } from '@/types/log'

export interface LogQuery {
  page?: number
  page_size?: number
  channel_id?: string
  keyword?: string
}

export function getLogsApi(params: LogQuery) {
  return http.get<LogListResp>('/logs', { params }).then(r => r.data)
}

export function getLogDetailApi(id: number) {
  return http.get<WebhookLogDetail>(`/logs/${id}`).then(r => r.data)
}