import { http } from './http'
import type { User } from '@/types/user'

export interface LoginPayload {
  username: string
  password: string
}

export function loginApi(payload: LoginPayload) {
  return http.post<User>('/auth/login', payload).then(r => r.data)
}

export function logoutApi() {
  return http.post<{ ok: boolean }>('/auth/logout').then(r => r.data)
}

export function meApi() {
  return http.get<User>('/auth/me').then(r => r.data)
}