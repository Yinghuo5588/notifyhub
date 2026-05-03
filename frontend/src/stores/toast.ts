import { defineStore } from 'pinia'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id: number
  message: string
  type: ToastType
}

let idSeed = 1

export const useToastStore = defineStore('toast', {
  state: () => ({
    items: [] as ToastItem[],
  }),

  actions: {
    show(message: string, type: ToastType = 'info', duration = 4000) {
      const id = idSeed++
      this.items.push({ id, message, type })

      window.setTimeout(() => {
        this.remove(id)
      }, duration)
    },

    success(message: string) {
      this.show(message, 'success')
    },

    error(message: string) {
      this.show(message, 'error')
    },

    warning(message: string) {
      this.show(message, 'warning')
    },

    info(message: string) {
      this.show(message, 'info')
    },

    remove(id: number) {
      this.items = this.items.filter(item => item.id !== id)
    },
  },
})