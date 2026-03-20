import { defineStore } from 'pinia'

interface SessionState {
  expired: boolean
  message: string
}

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    expired: false,
    message: 'Your session has expired. Please sign in again.'
  }),
  actions: {
    setExpired(message?: string) {
      this.expired = true
      if (message) this.message = message
    },
    clear() {
      this.expired = false
      this.message = 'Your session has expired. Please sign in again.'
    }
  }
})
