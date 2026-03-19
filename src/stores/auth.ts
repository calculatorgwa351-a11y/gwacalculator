import { defineStore } from 'pinia'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  hydrated: boolean
  isLoading: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    hydrated: false,
    isLoading: false
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
    isAdmin: (state) => !!state.user?.is_admin
  },
  actions: {
    async fetchMe() {
      if (this.isLoading) return
      this.isLoading = true
      try {
        const res = await fetch('/api/me')
        if (!res.ok) {
          this.user = null
          return
        }
        this.user = (await res.json()) as User
      } catch (err) {
        console.error('Failed to fetch /api/me:', err)
        this.user = null
      } finally {
        this.hydrated = true
        this.isLoading = false
      }
    },
    async logout() {
      try {
        await fetch('/api/logout', { method: 'POST' })
      } catch (err) {
        console.error('Logout failed:', err)
      } finally {
        this.user = null
        this.hydrated = true
      }
    }
  }
})

