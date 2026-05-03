import { defineStore } from 'pinia'

type Theme = 'light' | 'dark'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: 'light' as Theme,
  }),

  actions: {
    init() {
      const stored = localStorage.getItem('notifyhub-theme') as Theme | null
      const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'

      this.setTheme(stored || preferred)
    },

    setTheme(theme: Theme) {
      this.theme = theme
      localStorage.setItem('notifyhub-theme', theme)
      document.documentElement.setAttribute('data-theme', theme)
    },

    toggleTheme() {
      this.setTheme(this.theme === 'dark' ? 'light' : 'dark')
    },
  },
})