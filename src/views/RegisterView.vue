<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const name = ref('')
const schoolId = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)

const handleRegister = async () => {
  if (!name.value || !schoolId.value || !password.value) {
    error.value = 'Please fill in all fields'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('name', name.value)
    formData.append('school_id', schoolId.value)
    formData.append('password', password.value)

    const res = await fetch('/api/register', {
      method: 'POST',
      body: formData
    })

    const data = await res.json()

    if (res.ok && data.success) {
      router.push('/')
    } else {
      error.value = data.error || 'Registration failed'
    }
  } catch (err) {
    error.value = 'An error occurred. Please try again later.'
    console.error('Registration error:', err)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md space-y-8 animate-in">
      <div class="text-center">
        <h1 class="text-4xl font-black text-slate-900 dark:text-white tracking-tight">Create an Account</h1>
        <p class="mt-2 text-slate-500 dark:text-slate-400 font-medium">Join the community and start tracking your grades</p>
      </div>

      <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] shadow-xl border border-slate-100 dark:border-slate-700">
        <form @submit.prevent="handleRegister" class="space-y-6">
          <div v-if="error" class="p-4 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800 rounded-2xl text-sm font-bold animate-in">
            {{ error }}
          </div>

          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Full Name</label>
            <input 
              v-model="name"
              type="text" 
              required
              class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"
              placeholder="e.g. Juan Dela Cruz"
            >
          </div>

          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">School ID</label>
            <input 
              v-model="schoolId"
              type="text" 
              required
              class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"
              placeholder="e.g. 20240001"
            >
          </div>

          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Password</label>
            <input 
              v-model="password"
              type="password" 
              required
              class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"
              placeholder="••••••••"
            >
          </div>

          <button 
            type="submit" 
            :disabled="isLoading"
            class="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-2xl shadow-lg shadow-blue-600/20 transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
          >
            <span v-if="isLoading">Creating Account...</span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <div class="mt-8 pt-6 border-t border-slate-50 dark:border-slate-700 text-center">
          <router-link to="/" class="text-sm font-bold text-slate-400 hover:text-blue-600 transition-colors">
            Already have an account? <span class="text-blue-600">Sign in</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
