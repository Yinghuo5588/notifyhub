import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

export const http = axios.create({
  baseURL: '/api',
  withCredentials: true,
  timeout: 15000,
})

http.interceptors.response.use(
  res => res,
  err => {
    const status = err.response?.status

    if (status === 401) {
      const auth = useAuthStore()
      auth.clearUser()

      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }

    return Promise.reject(err)
  },
)

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.detail || err.message || '请求失败'
  }

  return err instanceof Error ? err.message : '未知错误'
}