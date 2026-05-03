import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    mobileMoreOpen: false,
  }),

  actions: {
    openMobileMore() {
      this.mobileMoreOpen = true
    },

    closeMobileMore() {
      this.mobileMoreOpen = false
    },

    toggleMobileMore() {
      this.mobileMoreOpen = !this.mobileMoreOpen
    },
  },
})