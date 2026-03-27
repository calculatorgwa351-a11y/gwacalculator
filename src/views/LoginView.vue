<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { apiFetch } from '@/utils/apiClient'

const router = useRouter()
const authStore = useAuthStore()
const schoolId = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)
const showPassword = ref(false)

const handleLogin = async () => {
  if (!schoolId.value || !password.value) {
    error.value = 'Please enter both school ID and password'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('school_id', schoolId.value)
    formData.append('password', password.value)

    const res = await apiFetch('/api/login', { method: 'POST', body: formData, skipAuthError: true })
    const data = await res.json()

    if (res.ok && data.success) {
      const redirectTarget =
        typeof data.redirect === 'string'
          ? data.redirect
          : data.is_admin
            ? '/admin'
            : '/dashboard'

      await authStore.fetchMe()
      router.push(redirectTarget)
    } else {
      error.value = data.error || 'Invalid credentials'
    }
  } catch (err) {
    error.value = 'An error occurred. Please try again later.'
    console.error('Login error:', err)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md space-y-8 animate-in">
      <div class="text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-tr from-blue-600 to-blue-800 rounded-3xl shadow-xl shadow-blue-500/20 mb-6">
          <span class="text-4xl font-black text-white italic">G</span>
        </div>
        <h1 class="text-4xl font-black text-slate-900 dark:text-white tracking-tight">Welcome Back</h1>
        <p class="mt-2 text-slate-500 dark:text-slate-400 font-medium">Sign in to your academic dashboard</p>
        <p class="mt-3 text-sm text-slate-500 dark:text-slate-400">
          Student accounts are created by the admin. Use the school ID and password assigned to you.
        </p>
      </div>

      <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] shadow-xl border border-slate-100 dark:border-slate-700">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div v-if="error" class="p-4 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800 rounded-2xl text-sm font-bold animate-in">
            {{ error }}
          </div>

          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">School ID</label>
            <input
              v-model="schoolId"
              type="text"
              required
              class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"
              placeholder="e.g. admin or 20240001"
            >
          </div>

          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Password</label>
            <div class="relative">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                class="w-full px-5 py-4 pr-28 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"
                placeholder="Enter your password"
              >
              <button
                type="button"
                class="absolute inset-y-0 right-3 my-2 px-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-black uppercase tracking-[0.16em] text-slate-600 dark:text-slate-200 hover:text-blue-600 dark:hover:text-blue-300 transition-colors"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
              >
                {{ showPassword ? 'Hide' : 'View' }}
              </button>
            </div>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-2xl shadow-lg shadow-blue-600/20 transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
          >
            <span v-if="isLoading">Signing in...</span>
            <span v-else>Sign In</span>
          </button>
        </form>

        <div class="mt-8 pt-6 border-t border-slate-50 dark:border-slate-700 text-center">
          <p class="text-sm font-semibold text-slate-500 dark:text-slate-400">
            Need an account? Please contact the admin to register your student profile.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
