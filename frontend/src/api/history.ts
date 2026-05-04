import { http } from './http'
import type { HistoryDetail, HistoryListResp } from '@/types/history'

export interface HistoryQuery {
  page?: number
  page_size?: number
  status?: string
  channel_id?: string
  keyword?: string
}

export function getHistoryApi(params: HistoryQuery) {
  return http.get<HistoryListResp>('/history', { params }).then(r => r.data)
}

export function getHistoryDetailApi(id: number) {
  return http.get<HistoryDetail>(`/history/${id}`).then(r => r.data)
}

export function resendHistoryApi(id: number) {
  return http.post<{ ok: boolean; msg: string }>(`/history/${id}/resend`).then(r => r.data)
}