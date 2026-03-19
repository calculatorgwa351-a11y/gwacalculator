<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import GwaChart from '@/components/GwaChart.vue'
import PostList from '@/components/PostList.vue'
import GradeList from '@/components/GradeList.vue'
import Handbook from '@/components/Handbook.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const user = computed(() => authStore.user)
const activeView = ref('overview')
const gwa = ref(0)
const honors = ref<any>(null)

const newPostContent = ref('')

const fetchDashboardData = async () => {
  try {
    if (!authStore.hydrated) await authStore.fetchMe()
    if (!authStore.user) {
      router.push('/')
      return
    }

    const res = await fetch('/api/grades')
    if (res.status === 401) {
      await authStore.fetchMe()
      router.push('/')
      return
    }
    if (res.ok) {
      await res.json()
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
    const formData = new FormData()
    formData.append('content', newPostContent.value)

    const res = await fetch('/api/posts', {
      method: 'POST',
      body: formData
    })

    if (res.ok) {
      newPostContent.value = ''
      // Ideally, the PostList component should re-fetch posts
      // For now, we'll just reload the page
      window.location.reload()
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
      </header>

      <div v-show="activeView === 'overview'" class="space-y-8 animate-in">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div class="lg:col-span-2 bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/50 dark:shadow-none">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-6">Performance History</h3>
            <GwaChart v-if="user" :user-id="user.id" />
          </div>

          <div class="space-y-8">
            <div class="bg-gradient-to-br from-blue-600 to-blue-800 p-8 rounded-[2.5rem] text-white shadow-xl shadow-blue-500/20">
              <h3 class="text-[10px] font-black uppercase tracking-[0.2em] opacity-60 mb-2">Current GWA</h3>
              <div class="text-5xl font-black tracking-tight mb-4 tabular-nums">1.25</div>
              <div class="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-[10px] font-bold">
                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                Honors Eligible
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
        <PostList />
      </div>

      <div v-show="activeView === 'handbook'">
        <Handbook />
      </div>
    </main>
  </div>
</template>
