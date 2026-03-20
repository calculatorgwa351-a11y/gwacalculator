<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { getAvatarColor, getInitials } from '@/utils/avatar'

const themeStore = useThemeStore()
const authStore = useAuthStore()
const router = useRouter()

const logout = async () => {
  await authStore.logout()
  router.push('/')
}

const emit = defineEmits(['view-change'])
const props = defineProps<{
  activeView: string
}>()

const setView = (view: string) => {
  emit('view-change', view)
}
</script>

<template>
  <aside id="sidebar" class="w-64 glass dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col sticky top-0 h-screen z-50 transition-transform duration-300">
    <div class="p-6">
      <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-tr from-blue-600 to-blue-800 rounded-xl flex items-center justify-center text-white shadow-lg">
            <span class="font-black text-xl italic">G</span>
          </div>
          <span class="font-black text-xl tracking-tight text-slate-800 dark:text-white">GWA<span class="text-blue-600 dark:text-blue-400">calculator</span></span>
        </div>
      </div>

      <nav class="space-y-1" aria-label="Sidebar Navigation">
        <router-link
          to="/profile"
          class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A9 9 0 1118.364 4.561 9 9 0 015.12 17.804z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          Profile
        </router-link>
        <button 
          @click="setView('overview')"
          :class="['sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all', activeView === 'overview' ? 'active bg-blue-600 text-white' : 'text-slate-600 dark:text-slate-400']"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
          Dashboard
        </button>
        <button 
          @click="setView('grades')"
          :class="['sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all', activeView === 'grades' ? 'active bg-blue-600 text-white' : 'text-slate-600 dark:text-slate-400']"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
          My Evaluation
        </button>
        <button 
          @click="setView('social')"
          :class="['sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all', activeView === 'social' ? 'active bg-blue-600 text-white' : 'text-slate-600 dark:text-slate-400']"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"/></svg>
          Student Feed
        </button>
        <button 
          @click="setView('handbook')"
          :class="['sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all', activeView === 'handbook' ? 'active bg-blue-600 text-white' : 'text-slate-600 dark:text-slate-400']"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
          Handbook
        </button>

        <router-link
          v-if="authStore.isAdmin"
          to="/admin"
          class="sidebar-link w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h4m-6 6v2a2 2 0 002 2h6a2 2 0 002-2v-6a2 2 0 00-2-2h-1M9 17H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v2"/></svg>
          Admin Console
        </router-link>
      </nav>

      <div
        v-if="authStore.user"
        class="mt-6 p-4 rounded-2xl bg-white/60 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-11 h-11 rounded-2xl text-white flex items-center justify-center font-black"
            :style="{ backgroundColor: getAvatarColor(authStore.user.school_id) }"
          >
            {{ getInitials(authStore.user.name) }}
          </div>
          <div class="min-w-0">
            <div class="font-black text-slate-900 dark:text-white text-sm truncate">{{ authStore.user.name }}</div>
            <div class="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-widest truncate">
              {{ authStore.user.school_id }}
            </div>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <span v-if="authStore.user.department" class="px-2 py-1 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400">
            {{ authStore.user.department }}
          </span>
          <span v-if="authStore.user.course" class="px-2 py-1 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400">
            {{ authStore.user.course }}
          </span>
          <span v-if="authStore.isAdmin" class="px-2 py-1 rounded-full bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-900/30 text-[10px] font-black uppercase tracking-widest text-blue-700 dark:text-blue-300">
            Admin
          </span>
        </div>
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
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
        Sign Out
      </button>
    </div>
  </aside>
</template>
