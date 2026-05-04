import { http } from './http'
import type { NotificationTemplate } from '@/types/template'

export function getTemplatesApi() {
  return http.get<NotificationTemplate[]>('/templates').then(r => r.data)
}

export function getSharedTemplatesApi() {
  return http.get<NotificationTemplate[]>('/templates/shared').then(r => r.data)
}

export function deleteTemplateApi(id: number) {
  return http.delete<{ ok: boolean }>(`/templates/${id}`).then(r => r.data)
}

export function previewTemplateApi(payload: {
  subject_template: string
  body_template: string
  sample_data: string
}) {
  return http
    .post<{ subject: string; body: string }>('/templates/preview', payload)
    .then(r => r.data)
}