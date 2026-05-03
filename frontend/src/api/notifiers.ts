import { http } from './http'
import type { NotifierType } from '@/types/notifier'

export function getNotifierTypesApi() {
  return http.get<NotifierType[]>('/notifiers/types').then(r => r.data)
}