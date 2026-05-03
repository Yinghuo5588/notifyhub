import { defineStore } from 'pinia'
import type { User } from '@/types/user'
import { loginApi, logoutApi, meApi, type LoginPayload } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    loaded: false,
  }),

  getters: {
    isLoggedIn: state => !!state.user,
    isAdmin: state => !!state.user?.is_admin,
  },

  actions: {
    async fetchMe() {
      const data = await meApi()
      this.user = data
      this.loaded = true
      return data
    },

    async login(payload: LoginPayload) {
      const data = await loginApi(payload)
      this.user = data
      this.loaded = true
      return data
    },

    async logout() {
      await logoutApi()
      this.clearUser()
    },

    clearUser() {
      this.user = null
      this.loaded = false
    },
  },
})