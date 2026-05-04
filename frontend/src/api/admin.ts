import { http } from './http'
import type {
  AdminUser,
  AdminUserCreatePayload,
  ShareChannelPayload,
  ShareChannelResp,
  ShareNotifierResp,
  ShareTemplateResp,
  ShareUsersPayload,
} from '@/types/admin'

export function getAdminUsersApi() {
  return http.get<AdminUser[]>('/admin/users').then(r => r.data)
}

export function createAdminUserApi(payload: AdminUserCreatePayload) {
  return http.post<AdminUser>('/admin/users', payload).then(r => r.data)
}

export function toggleAdminUserApi(id: number) {
  return http.post<AdminUser>(`/admin/users/${id}/toggle`).then(r => r.data)
}

export function resetAdminUserPasswordApi(id: number, newPassword: string) {
  return http
    .post<AdminUser>(`/admin/users/${id}/reset-password`, {
      new_password: newPassword,
    })
    .then(r => r.data)
}

export function deleteAdminUserApi(id: number) {
  return http.delete<{ ok: boolean }>(`/admin/users/${id}`).then(r => r.data)
}

export function batchAdminUsersApi(payload: {
  action: 'enable' | 'disable' | 'delete'
  user_ids: number[]
}) {
  return http.post<{ ok: boolean; count: number }>('/admin/users/batch', payload).then(r => r.data)
}

export function getShareChannelApi(id: number) {
  return http.get<ShareChannelResp>(`/admin/channels/${id}/share`).then(r => r.data)
}

export function saveShareChannelApi(id: number, payload: ShareChannelPayload) {
  return http.put<{ ok: boolean }>(`/admin/channels/${id}/share`, payload).then(r => r.data)
}

export function getShareNotifierApi(id: number) {
  return http.get<ShareNotifierResp>(`/admin/notifiers/${id}/share`).then(r => r.data)
}

export function saveShareNotifierApi(id: number, payload: ShareUsersPayload) {
  return http.put<{ ok: boolean }>(`/admin/notifiers/${id}/share`, payload).then(r => r.data)
}

export function getShareTemplateApi(id: number) {
  return http.get<ShareTemplateResp>(`/admin/templates/${id}/share`).then(r => r.data)
}

export function saveShareTemplateApi(id: number, payload: ShareUsersPayload) {
  return http.put<{ ok: boolean }>(`/admin/templates/${id}/share`, payload).then(r => r.data)
}