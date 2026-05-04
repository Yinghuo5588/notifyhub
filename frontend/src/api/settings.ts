import { http } from './http'
import type { User } from '@/types/user'

export interface ProfilePayload {
  username: string
  email: string
}

export interface PasswordPayload {
  old_password: string
  new_password: string
  confirm_password: string
}

export function getProfileApi() {
  return http.get<User>('/settings/profile').then(r => r.data)
}

export function updateProfileApi(payload: ProfilePayload) {
  return http.put<User>('/settings/profile', payload).then(r => r.data)
}

export function updatePasswordApi(payload: PasswordPayload) {
  return http.put<User>('/settings/password', payload).then(r => r.data)
}