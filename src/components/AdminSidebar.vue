<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const themeStore = useThemeStore()
const authStore = useAuthStore()
const router = useRouter()
const emit = defineEmits(['close'])
const props = defineProps<{
  isOpen?: boolean
}>()

const logout = async () => {
  await authStore.logout()
  emit('close')
  router.push('/')
}
</script>

<template>
  <aside
    id="admin-sidebar"
    class="fixed inset-y-0 left-0 w-72 max-w-[85vw] glass dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col h-screen z-50 transition-transform duration-300 lg:sticky lg:top-0 lg:w-64 lg:max-w-none"
    :class="props.isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
  >
    <div class="p-6">
      <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 bg-gradient-to-tr from-blue-600 to-blue-800 rounded-xl flex items-center justify-center text-white shadow-lg"
          >
            <span class="font-black text-xl italic">G</span>
          </div>
          <span class="font-black text-xl tracking-tight text-slate-800 dark:text-white">Admin<span class="text-blue-600 dark:text-blue-400">console</span></span>
        </div>
        <button
          type="button"
          class="lg:hidden w-10 h-10 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center"
          @click="emit('close')"
          aria-label="Close menu"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <nav class="space-y-1" aria-label="Admin Navigation">
        <router-link
          to="/admin"
          @click="emit('close')"
          class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all bg-blue-600 text-white"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h4m-6 6v2a2 2 0 002 2h6a2 2 0 002-2v-6a2 2 0 00-2-2h-1M9 17H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v2"/></svg>
          Overview
        </router-link>

        <router-link
          to="/dashboard"
          @click="emit('close')"
          class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
          Student App
        </router-link>
      </nav>

      <div v-if="authStore.user" class="mt-6 px-4 py-3 rounded-2xl bg-white/60 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
        <div class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Signed in</div>
        <div class="font-black text-slate-900 dark:text-white text-sm truncate">{{ authStore.user.name }}</div>
        <div class="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-widest truncate">{{ authStore.user.school_id }}</div>
      </div>
    </div>

    <div class="mt-auto p-6 border-t border-slate-100 dark:border-slate-800">
      <button
        @click="themeStore.toggleTheme"
        class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800 transition-all"
      >
        <svg v-if="themeStore.isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
        Theme
      </button>
      <button
        @click="logout"
        class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all mt-1"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a2 2 0 013-3h4a3 3 0 013 3v1"/></svg>
        Sign Out
      </button>
    </div>
  </aside>
</template>
