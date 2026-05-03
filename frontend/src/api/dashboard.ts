import { http } from './http'
import type { DashboardResp } from '@/types/dashboard'

export function getDashboardApi() {
  return http.get<DashboardResp>('/dashboard').then(r => r.data)
}