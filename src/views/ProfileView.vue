<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import { apiFetch } from '@/utils/apiClient'
import { getAvatarColor, getInitials } from '@/utils/avatar'

const authStore = useAuthStore()
const router = useRouter()

const name = ref('')
const department = ref('')
const course = ref('')
const password = ref('')
const isLoading = ref(false)
const success = ref('')
const error = ref('')
const isSidebarOpen = ref(false)

const user = computed(() => authStore.user)

const hydrate = async () => {
  if (!authStore.hydrated) await authStore.fetchMe()
  if (!authStore.user) {
    router.push('/')
    return
  }
  name.value = authStore.user.name
  department.value = authStore.user.department || ''
  course.value = authStore.user.course || ''
}

const saveProfile = async () => {
  isLoading.value = true
  success.value = ''
  error.value = ''
  try {
    const res = await apiFetch('/api/me', {
      method: 'PUT',
      json: {
        name: name.value,
        department: department.value,
        course: course.value,
        password: password.value || undefined
      }
    })
    const data = await res.json()
    if (res.ok) {
      authStore.user = data
      password.value = ''
      success.value = 'Profile updated.'
    } else {
      error.value = data.detail || 'Failed to update profile'
    }
  } catch (err) {
    error.value = 'An unexpected error occurred.'
    console.error('Failed to update profile:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  hydrate()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 lg:flex">
    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 z-40 bg-slate-950/50 backdrop-blur-sm lg:hidden"
      @click="isSidebarOpen = false"
    ></div>
    <Sidebar
      :active-view="'profile'"
      :is-open="isSidebarOpen"
      @view-change="() => router.push('/dashboard')"
      @close="isSidebarOpen = false"
    />

    <main class="w-full flex-1 p-4 pt-20 sm:p-6 sm:pt-24 md:p-8 md:pt-24 lg:pt-8 overflow-y-auto">
      <div class="fixed inset-x-0 top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/95 px-4 py-3 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 lg:hidden">
        <button
          type="button"
          class="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-700 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
          @click="isSidebarOpen = true"
          aria-label="Open menu"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
        <div class="text-sm font-black tracking-tight text-slate-900 dark:text-white">Profile</div>
        <div class="w-11"></div>
      </div>

      <header class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">Profile</h1>
          <p class="text-slate-500 dark:text-slate-400 font-medium">Manage your academic identity</p>
        </div>
      </header>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
          <div class="flex items-center gap-4">
            <div
              class="w-16 h-16 rounded-2xl text-white flex items-center justify-center text-xl font-black"
              :style="{ backgroundColor: getAvatarColor(user?.school_id) }"
            >
              {{ getInitials(user?.name) }}
            </div>
            <div>
              <div class="text-lg font-black text-slate-900 dark:text-white">{{ user?.name }}</div>
              <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
                {{ user?.school_id }}
              </div>
            </div>
          </div>
          <div class="mt-4 text-sm text-slate-500 dark:text-slate-400 font-medium">
            Department: {{ user?.department || 'General' }}
          </div>
          <div class="text-sm text-slate-500 dark:text-slate-400 font-medium">
            Course: {{ user?.course || 'Student' }}
          </div>
        </div>

        <div class="lg:col-span-2 bg-white dark:bg-slate-800 p-5 sm:p-8 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
          <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 mb-6">Edit Profile</h3>

          <form @submit.prevent="saveProfile" class="space-y-6">
            <div v-if="success" class="p-4 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-2xl text-sm font-bold">
              {{ success }}
            </div>
            <div v-if="error" class="p-4 bg-red-50 text-red-600 border border-red-100 rounded-2xl text-sm font-bold">
              {{ error }}
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Full Name</label>
                <input v-model="name" type="text" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
              </div>
              <div class="space-y-2">
                <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Department</label>
                <input v-model="department" type="text" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Course</label>
                <input v-model="course" type="text" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
              </div>
              <div class="space-y-2">
                <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">New Password</label>
                <input v-model="password" type="password" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
              </div>
            </div>

            <div class="flex justify-stretch sm:justify-end">
              <button
                type="submit"
                :disabled="isLoading"
                class="w-full sm:w-auto px-6 py-3 bg-blue-600 text-white text-xs font-black uppercase tracking-widest rounded-2xl hover:bg-blue-700 transition-all disabled:opacity-50"
              >
                <span v-if="isLoading">Saving...</span>
                <span v-else>Save Changes</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>
