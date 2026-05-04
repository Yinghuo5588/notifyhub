import { http } from './http'
import type { NotifierConfig, NotifierType } from '@/types/notifier'

export function getNotifierTypesApi() {
  return http.get<NotifierType[]>('/notifiers/types').then(r => r.data)
}

export function getNotifiersApi() {
  return http.get<NotifierConfig[]>('/notifiers').then(r => r.data)
}

export function deleteNotifierApi(id: number) {
  return http.delete<{ ok: boolean }>(`/notifiers/${id}`).then(r => r.data)
}

export function testNotifierApi(id: number) {
  return http
    .post<{ ok: boolean; msg: string }>(`/notifiers/${id}/test`)
    .then(r => r.data)
}