<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import AdminSidebar from '@/components/AdminSidebar.vue'
import StudentEditModal from '@/components/StudentEditModal.vue'
import StudentAnalyticsModal from '@/components/StudentAnalyticsModal.vue'
import StudentCreateModal from '@/components/StudentCreateModal.vue'
import AdminAnalyticsCharts from '@/components/AdminAnalyticsCharts.vue'
import AdminAuditPanel from '@/components/AdminAuditPanel.vue'
import AdminReportsPanel from '@/components/AdminReportsPanel.vue'
import type { User, Analytics } from '@/types'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { apiFetch } from '@/utils/apiClient'

const students = ref<User[]>([])
const analytics = ref<Analytics | null>(null)
const isLoading = ref(true)
const searchTerm = ref('')
const isModalOpen = ref(false)
const selectedUser = ref<User | null>(null)
const isAnalyticsOpen = ref(false)
const analyticsStudentId = ref<number | null>(null)
const isCreateOpen = ref(false)
const activeTab = ref<'overview' | 'analytics' | 'audit' | 'reports'>('overview')
const resetMessage = ref('')
const authStore = useAuthStore()
const router = useRouter()

const fetchAdminData = async () => {
  isLoading.value = true
  try {
    if (!authStore.hydrated) await authStore.fetchMe()
    if (!authStore.user) {
      router.push('/')
      return
    }
    if (!authStore.isAdmin) {
      router.push('/dashboard')
      return
    }

    const studentsRes = await apiFetch('/api/admin/students')
    const analyticsRes = await apiFetch('/api/analytics')

    if (studentsRes.ok) students.value = await studentsRes.json()
    if (analyticsRes.ok) analytics.value = await analyticsRes.json()
  } catch (err) {
    console.error('Failed to fetch admin data:', err)
  } finally {
    isLoading.value = false
  }
}

const filteredStudents = computed(() => {
  if (!searchTerm.value) return students.value
  const term = searchTerm.value.toLowerCase()
  return students.value.filter(
    (s) =>
      s.name.toLowerCase().includes(term) ||
      s.school_id.toLowerCase().includes(term) ||
      (s.department && s.department.toLowerCase().includes(term))
  )
})

const clearSearch = () => {
  searchTerm.value = ''
}

const deleteStudent = async (id: number) => {
  if (!confirm('Are you sure you want to permanently delete this student?')) return

  try {
    const res = await apiFetch(`/api/admin/student/${id}`, { method: 'DELETE' })
    if (res.ok) {
      students.value = students.value.filter((s) => s.id !== id)
    } else {
      const data = await res.json()
      alert(`Error: ${data.detail || 'Failed to delete student'}`)
    }
  } catch (err) {
    console.error('Failed to delete student:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

const openEditModal = (user: User) => {
  selectedUser.value = user
  isModalOpen.value = true
}

const openCreateModal = () => {
  isCreateOpen.value = true
}

const openAnalyticsModal = (user: User) => {
  analyticsStudentId.value = user.id
  isAnalyticsOpen.value = true
}

const fixDummyNames = async () => {
  try {
    const res = await apiFetch('/api/admin/seed/filipino_names', { method: 'POST' })
    if (res.ok) {
      await fetchAdminData()
    } else {
      const data = await res.json()
      alert(`Error: ${data.detail || 'Failed to update names'}`)
    }
  } catch (err) {
    console.error('Failed to seed Filipino names:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

const handleSaveStudent = async (updatedUser: User) => {
  try {
    const res = await apiFetch(`/api/admin/student/${updatedUser.id}`, {
      method: 'PUT',
      json: updatedUser
    })

    if (res.ok) {
      await fetchAdminData()
      isModalOpen.value = false
    } else {
      const data = await res.json()
      alert(`Error: ${data.detail || 'Failed to save student'}`)
    }
  } catch (err) {
    console.error('Failed to save student:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

const handleCreateStudent = async (payload: any) => {
  try {
    const res = await apiFetch('/api/admin/students', {
      method: 'POST',
      json: payload
    })
    if (res.ok) {
      isCreateOpen.value = false
      await fetchAdminData()
    } else {
      const data = await res.json()
      alert(`Error: ${data.detail || 'Failed to create student'}`)
    }
  } catch (err) {
    console.error('Failed to create student:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

const resetPassword = async (student: User) => {
  if (!confirm(`Reset password for ${student.name}?`)) return
  try {
    const res = await apiFetch(`/api/admin/student/${student.id}/reset_password`, { method: 'POST' })
    const data = await res.json()
    if (res.ok) {
      resetMessage.value = `Temporary password for ${student.name}: ${data.password}`
      alert(resetMessage.value)
    } else {
      alert(`Error: ${data.detail || 'Failed to reset password'}`)
    }
  } catch (err) {
    console.error('Failed to reset password:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

onMounted(() => {
  fetchAdminData()
})
</script>

<template>
  <div class="flex min-h-screen">
    <AdminSidebar />

    <main class="flex-1 p-8 overflow-y-auto">
      <header class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-8">
        <div>
          <h1 class="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Admin Console</h1>
          <p class="text-slate-500 dark:text-slate-400 font-medium">Academic oversight and student directory</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            @click="openCreateModal"
            class="px-4 py-2 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-blue-700 transition-all"
          >
            Create Student
          </button>
          <button
            @click="fixDummyNames"
            class="px-4 py-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-[10px] font-black uppercase tracking-widest rounded-xl hover:opacity-90 transition-all"
          >
            Filipino Names
          </button>
        </div>
      </header>

      <div class="flex flex-wrap items-center gap-2 mb-8">
        <button
          @click="activeTab = 'overview'"
          class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest"
          :class="activeTab === 'overview' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200'"
        >
          Overview
        </button>
        <button
          @click="activeTab = 'analytics'"
          class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest"
          :class="activeTab === 'analytics' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200'"
        >
          Analytics
        </button>
        <button
          @click="activeTab = 'audit'"
          class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest"
          :class="activeTab === 'audit' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200'"
        >
          Audit Log
        </button>
        <button
          @click="activeTab = 'reports'"
          class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest"
          :class="activeTab === 'reports' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200'"
        >
          Reports
        </button>
      </div>

      <div v-if="activeTab === 'overview'" class="space-y-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/50 dark:shadow-none">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-2">Average GWA</h3>
            <div class="text-4xl font-black text-slate-900 dark:text-white tracking-tight tabular-nums">{{ analytics?.average_gwa?.toFixed(3) ?? '-' }}</div>
          </div>
          <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/50 dark:shadow-none">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-2">Failure Rate</h3>
            <div class="text-4xl font-black text-slate-900 dark:text-white tracking-tight tabular-nums">{{ analytics?.failure_rate ? (analytics.failure_rate * 100).toFixed(1) + '%' : '-' }}</div>
          </div>
          <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/50 dark:shadow-none">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-2">Total Students</h3>
            <div class="text-4xl font-black text-slate-900 dark:text-white tracking-tight tabular-nums">{{ students.length }}</div>
          </div>
        </div>

        <div class="bg-white dark:bg-slate-800 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/50 dark:shadow-none overflow-hidden">
          <div class="px-8 py-6 border-b border-slate-50 dark:border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <h3 class="font-black text-slate-900 dark:text-white tracking-tight">Student Directory</h3>
            <div class="relative max-w-xs w-full">
              <input
                v-model="searchTerm"
                type="text"
                placeholder="Search records..."
                class="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm transition-all dark:text-white"
              >
              <svg class="w-4 h-4 absolute left-3 top-2.5 text-slate-300 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <button v-if="searchTerm" @click="clearSearch" class="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead class="bg-slate-50/50 dark:bg-slate-900/50 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase tracking-widest">
                <tr>
                  <th class="px-8 py-4">Student</th>
                  <th class="px-8 py-4 text-center">Department</th>
                  <th class="px-8 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr v-for="s in filteredStudents" :key="s.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group">
                  <td class="px-8 py-5">
                    <div class="flex items-center gap-4">
                      <div class="w-11 h-11 rounded-2xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center font-black text-slate-400 dark:text-slate-500 text-sm shadow-sm group-hover:bg-blue-600 group-hover:text-white transition-all">
                        {{ s.name.charAt(0) }}
                      </div>
                      <div>
                        <div class="font-black text-slate-900 dark:text-white text-sm">{{ s.name }}</div>
                        <div class="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-widest">{{ s.school_id }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-8 py-5 text-center text-sm font-bold text-slate-600 dark:text-slate-300">
                    {{ s.department || 'General' }}
                  </td>
                  <td class="px-8 py-5 text-right">
                    <div class="flex justify-end gap-2">
                      <button @click="openAnalyticsModal(s)" class="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-all active:scale-95">
                        Analytics
                      </button>
                      <button @click="resetPassword(s)" class="px-4 py-2 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-all active:scale-95">
                        Reset Pass
                      </button>
                      <button @click="openEditModal(s)" class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all active:scale-95">
                        Edit
                      </button>
                      <button @click="deleteStudent(s.id)" class="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-red-100 transition-all active:scale-95">
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'analytics'">
        <AdminAnalyticsCharts />
      </div>

      <div v-else-if="activeTab === 'audit'">
        <AdminAuditPanel />
      </div>

      <div v-else-if="activeTab === 'reports'">
        <AdminReportsPanel :students="students" />
      </div>
    </main>

    <StudentEditModal :is-open="isModalOpen" :user="selectedUser" @close="isModalOpen = false" @save="handleSaveStudent" />

    <StudentAnalyticsModal :is-open="isAnalyticsOpen" :student-id="analyticsStudentId" @close="isAnalyticsOpen = false" />

    <StudentCreateModal v-if="isCreateOpen" @close="isCreateOpen = false" @save="handleCreateStudent" />
  </div>
</template>
