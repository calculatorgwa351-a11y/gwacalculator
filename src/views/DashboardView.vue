<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import GwaChart from '@/components/GwaChart.vue'
import PostList from '@/components/PostList.vue'
import GradeList from '@/components/GradeList.vue'
import Handbook from '@/components/Handbook.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import type { DashboardSummary } from '@/types'

const authStore = useAuthStore()
const router = useRouter()
const user = computed(() => authStore.user)
const activeView = ref('overview')
const summary = ref<DashboardSummary | null>(null)
const postsRefreshKey = ref(0)

const newPostContent = ref('')

const fetchDashboardData = async () => {
  try {
    if (!authStore.hydrated) await authStore.fetchMe()
    if (!authStore.user) {
      router.push('/')
      return
    }

    const res = await fetch('/api/dashboard/summary')
    if (res.status === 401) {
      await authStore.fetchMe()
      router.push('/')
      return
    }
    if (res.ok) {
      summary.value = (await res.json()) as DashboardSummary
    }
  } catch (err) {
    console.error('Failed to fetch dashboard data:', err)
  }
}

const setView = (view: string) => {
  activeView.value = view
}

const handleCreatePost = async () => {
  if (!newPostContent.value) return

  try {
    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newPostContent.value })
    })

    if (res.ok) {
      newPostContent.value = ''
      postsRefreshKey.value += 1
      await fetchDashboardData()
    }
  } catch (err) {
    console.error('Failed to create post:', err)
  }
}

onMounted(() => {
  fetchDashboardData()
})

const viewTitles: Record<string, string> = {
  overview: 'Dashboard Overview',
  grades: 'My Evaluation',
  social: 'Student Feed',
  handbook: 'Student Handbook'
}

const honorsBadge = computed(() => {
  const honors = summary.value?.honors
  if (!honors) return null
  if (!honors.eligible || !honors.title) return null
  return honors.title
})
</script>

<template>
  <div class="flex min-h-screen">
    <Sidebar :active-view="activeView" @view-change="setView" />

    <main class="flex-1 p-8 overflow-y-auto">
      <header class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
            {{ viewTitles[activeView] }}
          </h1>
          <p class="text-slate-500 dark:text-slate-400 font-medium">
            Welcome back, {{ user?.name || 'Student' }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <router-link
            v-if="authStore.isAdmin"
            to="/admin"
            class="px-4 py-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-[10px] font-black uppercase tracking-widest rounded-xl hover:opacity-90 transition-all"
          >
            Admin Dashboard
          </router-link>
        </div>
      </header>

      <div v-show="activeView === 'overview'" class="space-y-8 animate-in">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div class="lg:col-span-2 bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/50 dark:shadow-none relative overflow-hidden">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-6">Performance History</h3>
            <GwaChart v-if="user" :user-id="user.id" />

            <div
              v-if="(summary?.grade_count ?? 0) === 0"
              class="absolute inset-0 flex items-center justify-center p-8"
            >
              <div class="max-w-md w-full bg-white/80 dark:bg-slate-900/70 backdrop-blur rounded-[2rem] border border-slate-100 dark:border-slate-700 p-6 text-center shadow-lg">
                <div class="text-sm font-black text-slate-900 dark:text-white">No grades yet</div>
                <div class="mt-1 text-sm text-slate-500 dark:text-slate-400 font-medium">
                  Add your subjects to calculate your GWA and check Latin honors eligibility.
                </div>
                <button
                  class="mt-4 px-5 py-3 bg-blue-600 text-white text-xs font-black uppercase tracking-widest rounded-2xl hover:bg-blue-700 transition-all active:scale-95"
                  @click="setView('grades')"
                >
                  Add Subject
                </button>
              </div>
            </div>
          </div>

          <div class="space-y-8">
            <div class="bg-gradient-to-br from-blue-600 to-blue-800 p-8 rounded-[2.5rem] text-white shadow-xl shadow-blue-500/20">
              <h3 class="text-[10px] font-black uppercase tracking-[0.2em] opacity-60 mb-2">Current GWA</h3>
              <div class="text-5xl font-black tracking-tight mb-4 tabular-nums">
                {{ summary?.gwa?.toFixed(3) ?? '—' }}
              </div>
              <div v-if="honorsBadge" class="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-[10px] font-black uppercase tracking-widest">
                <span class="w-2 h-2 bg-emerald-400 rounded-full"></span>
                {{ honorsBadge }}
              </div>
              <div v-else class="text-xs font-bold opacity-80 leading-relaxed">
                {{ summary?.honors?.reason ?? 'Add your subjects to see your Latin honors eligibility.' }}
              </div>
            </div>

            <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
              <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-4">Quick Stats</h3>
              <div class="grid grid-cols-2 gap-4">
                <div class="p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Subjects</div>
                  <div class="text-2xl font-black text-slate-900 dark:text-white tabular-nums">{{ summary?.grade_count ?? 0 }}</div>
                </div>
                <div class="p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
                  <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">My Posts</div>
                  <div class="text-2xl font-black text-slate-900 dark:text-white tabular-nums">{{ summary?.post_count ?? 0 }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeView === 'grades'">
        <GradeList />
      </div>

      <div v-show="activeView === 'social'">
        <div class="mb-8">
          <form @submit.prevent="handleCreatePost" class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
            <textarea v-model="newPostContent" placeholder="What's on your mind?" class="w-full p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"></textarea>
            <div class="flex justify-end mt-4">
              <button type="submit" class="px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-all">Post</button>
            </div>
          </form>
        </div>
        <PostList :key="postsRefreshKey" />
      </div>

      <div v-show="activeView === 'handbook'">
        <Handbook />
      </div>
    </main>
  </div>
</template>
