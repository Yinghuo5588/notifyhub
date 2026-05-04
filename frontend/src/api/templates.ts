import { http } from './http'
import type {
  NotificationTemplate,
  TemplatePayload,
  TemplatePreviewPayload,
  TemplatePreviewResp,
} from '@/types/template'

export function getTemplatesApi() {
  return http.get<NotificationTemplate[]>('/templates').then(r => r.data)
}

export function getSharedTemplatesApi() {
  return http.get<NotificationTemplate[]>('/templates/shared').then(r => r.data)
}

export function getTemplateApi(id: number) {
  return http.get<NotificationTemplate>(`/templates/${id}`).then(r => r.data)
}

export function createTemplateApi(payload: TemplatePayload) {
  return http.post<NotificationTemplate>('/templates', payload).then(r => r.data)
}

export function updateTemplateApi(id: number, payload: TemplatePayload) {
  return http.put<NotificationTemplate>(`/templates/${id}`, payload).then(r => r.data)
}

export function deleteTemplateApi(id: number) {
  return http.delete<{ ok: boolean }>(`/templates/${id}`).then(r => r.data)
}

export function previewTemplateApi(payload: TemplatePreviewPayload) {
  return http.post<TemplatePreviewResp>('/templates/preview', payload).then(r => r.data)
}

export function extractTemplateVariablesApi(payload: { sample_data: string }) {
  return http.post<{ variables: string[] }>('/templates/extract-variables', payload).then(r => r.data)
}