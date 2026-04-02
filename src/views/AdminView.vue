<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import AdminSidebar from '@/components/AdminSidebar.vue'
import StudentEditModal from '@/components/StudentEditModal.vue'
import StudentAnalyticsModal from '@/components/StudentAnalyticsModal.vue'
import StudentCreateModal from '@/components/StudentCreateModal.vue'
import AdminAnalyticsCharts from '@/components/AdminAnalyticsCharts.vue'
import AdminAuditPanel from '@/components/AdminAuditPanel.vue'
import AdminReportsPanel from '@/components/AdminReportsPanel.vue'
import AdminGradeManagerModal from '@/components/AdminGradeManagerModal.vue'
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
const isGradeManagerOpen = ref(false)
const selectedGradeStudent = ref<User | null>(null)
const activeTab = ref<'overview' | 'analytics' | 'audit' | 'reports'>('overview')
const resetMessage = ref('')
const isSidebarOpen = ref(false)
const isSavingStudent = ref(false)
const studentFormError = ref('')
const statusBanner = ref('')
const isRestoringDemoData = ref(false)
const isRenamingStudents = ref(false)
const isResettingDemoPasswords = ref(false)
const activePasswordResetStudentId = ref<number | null>(null)
const toasts = ref<{ id: number; tone: 'success' | 'error' | 'info'; message: string }[]>([])
const isUtilitiesOpen = ref(false)
const authStore = useAuthStore()
const router = useRouter()
let toastId = 0

const pushToast = (message: string, tone: 'success' | 'error' | 'info' = 'success') => {
  const id = ++toastId
  toasts.value.push({ id, tone, message })
  window.setTimeout(() => {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }, 4500)
}

const dismissToast = (id: number) => {
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

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

    const [studentsRes, analyticsRes] = await Promise.all([
      apiFetch('/api/admin/students'),
      apiFetch('/api/analytics')
    ])

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

const averageGwaValue = computed(() => analytics.value?.average_gwa ?? null)
const failureRateValue = computed(() => analytics.value?.failure_rate ?? null)
const failureRatePercent = computed(() => {
  if (failureRateValue.value == null) return null
  return Math.max(0, Math.min(100, failureRateValue.value * 100))
})
const averageGwaProgress = computed(() => {
  if (averageGwaValue.value == null) return null
  const normalized = ((5 - averageGwaValue.value) / 4) * 100
  return Math.max(0, Math.min(100, normalized))
})
const averageGwaLabel = computed(() => {
  if (averageGwaValue.value == null) return 'Waiting for student grades'
  if (averageGwaValue.value <= 1.75) return 'Latin honors range'
  if (averageGwaValue.value <= 2.5) return 'Good standing'
  if (averageGwaValue.value <= 3.0) return 'Needs support'
  return 'High academic risk'
})
const failureRateLabel = computed(() => {
  if (failureRatePercent.value == null) return 'Waiting for grade data'
  if (failureRatePercent.value <= 5) return 'Very low failure rate'
  if (failureRatePercent.value <= 15) return 'Manageable failure rate'
  if (failureRatePercent.value <= 30) return 'Needs attention'
  return 'Intervention recommended'
})

const deleteStudent = async (id: number) => {
  if (!confirm('Are you sure you want to permanently delete this student?')) return

  try {
    const res = await apiFetch(`/api/admin/student/${id}`, { method: 'DELETE' })
    if (res.ok) {
      const deletedStudent = students.value.find((s) => s.id === id)
      students.value = students.value.filter((s) => s.id !== id)
      pushToast(`${deletedStudent?.name ?? 'Student'} was deleted.`, 'success')
    } else {
      const data = await res.json()
      pushToast(data.detail || 'Failed to delete student', 'error')
    }
  } catch (err) {
    console.error('Failed to delete student:', err)
    pushToast('An unexpected error occurred. Please try again later.', 'error')
  }
}

const openEditModal = (user: User) => {
  studentFormError.value = ''
  selectedUser.value = user
  isModalOpen.value = true
}

const openCreateModal = () => {
  studentFormError.value = ''
  isCreateOpen.value = true
}

const openAnalyticsModal = (user: User) => {
  analyticsStudentId.value = user.id
  isAnalyticsOpen.value = true
}

const openGradeManager = (user: User) => {
  selectedGradeStudent.value = user
  isGradeManagerOpen.value = true
}

const closeGradeManager = async () => {
  isGradeManagerOpen.value = false
  selectedGradeStudent.value = null
  await fetchAdminData()
}

const handleManageGradesFromAnalytics = () => {
  const student = students.value.find((entry) => entry.id === analyticsStudentId.value) || null
  if (!student) return
  isAnalyticsOpen.value = false
  openGradeManager(student)
}

const restoreDemoData = async () => {
  isRestoringDemoData.value = true
  isUtilitiesOpen.value = false
  try {
    const res = await apiFetch('/api/admin/seed/demo_data?student_count=12', { method: 'POST' })
    const data = await res.json()
    if (res.ok) {
      await fetchAdminData()
      statusBanner.value = 'Demo student data is ready again.'
      pushToast(
        `Demo data restored: ${data.created_students ?? 0} created, ${data.seeded_grades ?? 0} grades refreshed, ${data.reset_passwords ?? 0} passwords reset to password123.`,
        'success'
      )
    } else {
      pushToast(data.detail || 'Failed to restore demo data', 'error')
    }
  } catch (err) {
    console.error('Failed to restore demo data:', err)
    pushToast('An unexpected error occurred. Please try again later.', 'error')
  } finally {
    isRestoringDemoData.value = false
  }
}

const fixDummyNames = async () => {
  isRenamingStudents.value = true
  isUtilitiesOpen.value = false
  try {
    const res = await apiFetch('/api/admin/seed/filipino_names', { method: 'POST' })
    if (res.ok) {
      await fetchAdminData()
      statusBanner.value = 'Student names were updated to Filipino-style names.'
      pushToast('Filipino names applied to demo students.', 'success')
    } else {
      const data = await res.json()
      pushToast(data.detail || 'Failed to update names', 'error')
    }
  } catch (err) {
    console.error('Failed to seed Filipino names:', err)
    pushToast('An unexpected error occurred. Please try again later.', 'error')
  } finally {
    isRenamingStudents.value = false
  }
}

const resetDemoPasswords = async () => {
  isResettingDemoPasswords.value = true
  isUtilitiesOpen.value = false
  try {
    const res = await apiFetch('/api/admin/seed/demo_passwords', { method: 'POST' })
    const data = await res.json()
    if (res.ok) {
      statusBanner.value = 'Demo student passwords are ready to use again.'
      pushToast(`${data.updated ?? 0} demo student passwords were reset to ${data.password ?? 'password123'}.`, 'success')
    } else {
      pushToast(data.detail || 'Failed to reset demo passwords', 'error')
    }
  } catch (err) {
    console.error('Failed to reset demo passwords:', err)
    pushToast('An unexpected error occurred. Please try again later.', 'error')
  } finally {
    isResettingDemoPasswords.value = false
  }
}

const handleSaveStudent = async (updatedUser: User) => {
  isSavingStudent.value = true
  studentFormError.value = ''
  try {
    const res = await apiFetch(`/api/admin/student/${updatedUser.id}`, {
      method: 'PUT',
      json: updatedUser
    })

    if (res.ok) {
      await fetchAdminData()
      statusBanner.value = `${updatedUser.name} was updated successfully.`
      pushToast(`${updatedUser.name} was updated successfully.`, 'success')
      isModalOpen.value = false
    } else {
      const data = await res.json()
      studentFormError.value = data.detail || 'Failed to save student'
      pushToast(studentFormError.value, 'error')
    }
  } catch (err) {
    console.error('Failed to save student:', err)
    studentFormError.value = 'An unexpected error occurred. Please try again later.'
    pushToast(studentFormError.value, 'error')
  } finally {
    isSavingStudent.value = false
  }
}

const handleCreateStudent = async (payload: any) => {
  isSavingStudent.value = true
  studentFormError.value = ''
  try {
    const res = await apiFetch('/api/admin/students', {
      method: 'POST',
      json: payload
    })
    if (res.ok) {
      isCreateOpen.value = false
      await fetchAdminData()
      statusBanner.value = `${payload.name} was created successfully.`
      pushToast(`${payload.name} was created successfully.`, 'success')
    } else {
      const data = await res.json()
      studentFormError.value = data.detail || 'Failed to create student'
      pushToast(studentFormError.value, 'error')
    }
  } catch (err) {
    console.error('Failed to create student:', err)
    studentFormError.value = 'An unexpected error occurred. Please try again later.'
    pushToast(studentFormError.value, 'error')
  } finally {
    isSavingStudent.value = false
  }
}

const resetPassword = async (student: User) => {
  if (!confirm(`Reset password for ${student.name}?`)) return
  activePasswordResetStudentId.value = student.id
  try {
    const res = await apiFetch(`/api/admin/student/${student.id}/reset_password`, { method: 'POST' })
    const data = await res.json()
    if (res.ok) {
      resetMessage.value = `Temporary password for ${student.name}: ${data.password}`
      statusBanner.value = resetMessage.value
      pushToast(resetMessage.value, 'info')
    } else {
      pushToast(data.detail || 'Failed to reset password', 'error')
    }
  } catch (err) {
    console.error('Failed to reset password:', err)
    pushToast('An unexpected error occurred. Please try again later.', 'error')
  } finally {
    activePasswordResetStudentId.value = null
  }
}

onMounted(() => {
  fetchAdminData()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 lg:flex">
    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
      @click="isSidebarOpen = false"
    />

    <div class="pointer-events-none fixed right-4 top-4 z-[70] flex w-full max-w-sm flex-col gap-3">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto rounded-2xl border px-4 py-3 shadow-xl backdrop-blur"
          :class="{
            'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200': toast.tone === 'success',
            'border-red-200 bg-red-50 text-red-600 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200': toast.tone === 'error',
            'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200': toast.tone === 'info'
          }"
        >
          <div class="flex items-start justify-between gap-3">
            <p class="text-sm font-semibold leading-6">{{ toast.message }}</p>
            <button class="text-[10px] font-black uppercase tracking-[0.18em] opacity-70 transition hover:opacity-100" @click="dismissToast(toast.id)">
              Close
            </button>
          </div>
        </div>
      </transition-group>
    </div>

    <AdminSidebar :is-open="isSidebarOpen" @close="isSidebarOpen = false" />

    <main class="w-full flex-1 overflow-y-auto p-4 pt-20 sm:p-6 sm:pt-24 md:p-8 md:pt-24 lg:pt-8">
      <div class="fixed inset-x-0 top-0 z-30 flex items-center justify-between border-b border-slate-200/70 bg-white/95 px-4 py-4 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 lg:hidden">
        <button
          type="button"
          class="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
          @click="isSidebarOpen = true"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div class="text-right">
          <div class="text-xs font-black uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">Admin Console</div>
          <div class="text-sm font-bold text-slate-900 dark:text-white">Student management</div>
        </div>
      </div>

      <header class="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 class="text-2xl font-black tracking-tight text-slate-900 dark:text-white sm:text-3xl">Admin Console</h1>
          <p class="text-slate-500 dark:text-slate-400 font-medium">Academic oversight and student directory</p>
        </div>
        <div class="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:flex xl:flex-wrap xl:items-center xl:justify-end">
          <button
            @click="openCreateModal"
            class="w-full rounded-xl bg-blue-600 px-4 py-3 text-[10px] font-black uppercase tracking-widest text-white transition-all hover:bg-blue-700 xl:w-auto"
          >
            Create Student
          </button>
          <div class="relative sm:col-span-2 xl:w-auto">
            <button
              @click="isUtilitiesOpen = !isUtilitiesOpen"
              class="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-[10px] font-black uppercase tracking-widest text-slate-700 shadow-sm transition-all hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800 xl:w-auto"
            >
              Demo Tools
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div
              v-if="isUtilitiesOpen"
              class="absolute right-0 z-20 mt-2 w-full min-w-[18rem] rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl dark:border-slate-700 dark:bg-slate-900 xl:w-80"
            >
              <div class="mb-3 px-1">
                <div class="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Demo utilities</div>
                <div class="mt-1 text-sm font-semibold text-slate-700 dark:text-slate-200">Use these only when you need to refresh sample student data.</div>
              </div>
              <div class="space-y-2">
                <button
                  @click="restoreDemoData"
                  :disabled="isRestoringDemoData"
                  class="flex w-full items-center justify-between rounded-xl bg-emerald-50 px-4 py-3 text-left text-emerald-700 transition-all hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-emerald-900/20 dark:text-emerald-300"
                >
                  <span>
                    <span class="block text-[10px] font-black uppercase tracking-[0.18em]">Restore demo data</span>
                    <span class="mt-1 block text-xs font-medium">Create missing demo students and refresh sample grades/posts.</span>
                  </span>
                  <span class="text-[10px] font-black uppercase tracking-[0.18em]">{{ isRestoringDemoData ? 'Running...' : 'Run' }}</span>
                </button>
                <button
                  @click="resetDemoPasswords"
                  :disabled="isResettingDemoPasswords"
                  class="flex w-full items-center justify-between rounded-xl bg-amber-50 px-4 py-3 text-left text-amber-700 transition-all hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-amber-900/20 dark:text-amber-300"
                >
                  <span>
                    <span class="block text-[10px] font-black uppercase tracking-[0.18em]">Reset demo passwords</span>
                    <span class="mt-1 block text-xs font-medium">Set all `2024xxxx` students back to `password123`.</span>
                  </span>
                  <span class="text-[10px] font-black uppercase tracking-[0.18em]">{{ isResettingDemoPasswords ? 'Running...' : 'Run' }}</span>
                </button>
                <button
                  @click="fixDummyNames"
                  :disabled="isRenamingStudents"
                  class="flex w-full items-center justify-between rounded-xl bg-slate-100 px-4 py-3 text-left text-slate-700 transition-all hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  <span>
                    <span class="block text-[10px] font-black uppercase tracking-[0.18em]">Apply Filipino names</span>
                    <span class="mt-1 block text-xs font-medium">Rename demo student records using the Filipino seed list.</span>
                  </span>
                  <span class="text-[10px] font-black uppercase tracking-[0.18em]">{{ isRenamingStudents ? 'Running...' : 'Run' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div v-if="statusBanner" class="mb-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200">
        <div class="flex items-center justify-between gap-3">
          <span>{{ statusBanner }}</span>
          <button class="text-xs font-black uppercase tracking-[0.16em] opacity-70 hover:opacity-100" @click="statusBanner = ''">
            Dismiss
          </button>
        </div>
      </div>

      <div class="-mx-1 mb-8 overflow-x-auto pb-1">
        <div class="flex min-w-max items-center gap-2 px-1">
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
      </div>

      <div v-if="activeTab === 'overview'" class="space-y-8">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 xl:gap-8">
          <div class="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-xl shadow-slate-200/50 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none sm:p-8">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-2">Average GWA</h3>
            <div class="text-4xl font-black text-slate-900 dark:text-white tracking-tight tabular-nums">
              <span v-if="averageGwaValue !== null">{{ averageGwaValue.toFixed(3) }}</span>
              <span v-else-if="isLoading">...</span>
              <span v-else>—</span>
            </div>
            <div class="mt-4 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
              <div
                class="h-full rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 transition-all duration-500"
                :style="{ width: `${averageGwaProgress ?? 0}%` }"
              />
            </div>
            <div class="mt-3 text-sm font-semibold text-slate-500 dark:text-slate-400">
              {{ averageGwaLabel }}
            </div>
          </div>
          <div class="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-xl shadow-slate-200/50 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none sm:p-8">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-2">Failure Rate</h3>
            <div class="text-4xl font-black text-slate-900 dark:text-white tracking-tight tabular-nums">
              <span v-if="failureRatePercent !== null">{{ failureRatePercent.toFixed(1) }}%</span>
              <span v-else-if="isLoading">...</span>
              <span v-else>—</span>
            </div>
            <div class="mt-4 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
              <div
                class="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500 transition-all duration-500"
                :style="{ width: `${failureRatePercent ?? 0}%` }"
              />
            </div>
            <div class="mt-3 text-sm font-semibold text-slate-500 dark:text-slate-400">
              {{ failureRateLabel }}
            </div>
          </div>
          <div class="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-xl shadow-slate-200/50 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none sm:p-8 sm:col-span-2 xl:col-span-1">
            <h3 class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-2">Total Students</h3>
            <div class="text-4xl font-black text-slate-900 dark:text-white tracking-tight tabular-nums">{{ students.length }}</div>
          </div>
        </div>

        <div class="overflow-hidden rounded-[2rem] border border-slate-100 bg-white shadow-xl shadow-slate-200/50 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none sm:rounded-[2.5rem]">
          <div class="flex flex-col gap-4 border-b border-slate-50 px-5 py-5 dark:border-slate-700 sm:px-8 sm:py-6 md:flex-row md:items-center md:justify-between">
            <h3 class="font-black text-slate-900 dark:text-white tracking-tight">Student Directory</h3>
            <div class="relative w-full md:max-w-xs">
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

          <div v-if="isLoading" class="space-y-4 p-5 sm:p-8">
            <div v-for="index in 3" :key="index" class="animate-pulse rounded-[1.75rem] border border-slate-100 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
              <div class="mb-3 h-4 w-40 rounded bg-slate-200 dark:bg-slate-700"></div>
              <div class="h-4 w-28 rounded bg-slate-200 dark:bg-slate-700"></div>
            </div>
          </div>

          <div v-else-if="filteredStudents.length === 0" class="p-8 text-center text-sm font-medium text-slate-500 dark:text-slate-400">
            No students matched your search.
          </div>

          <template v-else>
            <div class="hidden overflow-x-auto md:block">
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
                        <button @click="openGradeManager(s)" class="px-4 py-2 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-all active:scale-95">
                          Manage Grades
                        </button>
                        <button @click="resetPassword(s)" :disabled="activePasswordResetStudentId === s.id" class="px-4 py-2 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-all active:scale-95 disabled:cursor-not-allowed disabled:opacity-70">
                          {{ activePasswordResetStudentId === s.id ? 'Resetting...' : 'Reset Pass' }}
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

            <div class="space-y-4 p-4 sm:p-6 md:hidden">
              <article
                v-for="s in filteredStudents"
                :key="s.id"
                class="rounded-[1.75rem] border border-slate-100 bg-slate-50 p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900"
              >
                <div class="flex items-start gap-4">
                  <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white text-sm font-black text-slate-500 shadow-sm dark:bg-slate-800 dark:text-slate-300">
                    {{ s.name.charAt(0) }}
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="truncate text-base font-black text-slate-900 dark:text-white">{{ s.name }}</div>
                    <div class="mt-1 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">{{ s.school_id }}</div>
                    <div class="mt-3 inline-flex rounded-full bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-slate-600 shadow-sm dark:bg-slate-800 dark:text-slate-300">
                      {{ s.department || 'General' }}
                    </div>
                  </div>
                </div>

                <div class="mt-4 grid grid-cols-2 gap-2">
                  <button @click="openAnalyticsModal(s)" class="rounded-xl bg-blue-50 px-3 py-3 text-[10px] font-black uppercase tracking-widest text-blue-700 transition-all active:scale-[0.98] dark:bg-blue-900/20 dark:text-blue-300">
                    Analytics
                  </button>
                  <button @click="openGradeManager(s)" class="rounded-xl bg-emerald-50 px-3 py-3 text-[10px] font-black uppercase tracking-widest text-emerald-700 transition-all active:scale-[0.98] dark:bg-emerald-900/20 dark:text-emerald-300">
                    Grades
                  </button>
                  <button @click="resetPassword(s)" :disabled="activePasswordResetStudentId === s.id" class="rounded-xl bg-amber-50 px-3 py-3 text-[10px] font-black uppercase tracking-widest text-amber-700 transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70 dark:bg-amber-900/20 dark:text-amber-300">
                    {{ activePasswordResetStudentId === s.id ? 'Resetting...' : 'Reset Pass' }}
                  </button>
                  <button @click="openEditModal(s)" class="rounded-xl bg-slate-200 px-3 py-3 text-[10px] font-black uppercase tracking-widest text-slate-700 transition-all active:scale-[0.98] dark:bg-slate-700 dark:text-slate-200">
                    Edit
                  </button>
                  <button @click="deleteStudent(s.id)" class="col-span-2 rounded-xl bg-red-50 px-3 py-3 text-[10px] font-black uppercase tracking-widest text-red-600 transition-all active:scale-[0.98] dark:bg-red-900/20 dark:text-red-300">
                    Delete Student
                  </button>
                </div>
              </article>
            </div>
          </template>
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

    <StudentEditModal
      :is-open="isModalOpen"
      :user="selectedUser"
      :is-saving="isSavingStudent"
      :error-message="studentFormError"
      @close="isModalOpen = false"
      @save="handleSaveStudent"
    />

    <StudentAnalyticsModal
      :is-open="isAnalyticsOpen"
      :student-id="analyticsStudentId"
      @close="isAnalyticsOpen = false"
      @manage-grades="handleManageGradesFromAnalytics"
    />

    <StudentCreateModal
      v-if="isCreateOpen"
      :is-saving="isSavingStudent"
      :error-message="studentFormError"
      @close="isCreateOpen = false"
      @save="handleCreateStudent"
    />

    <AdminGradeManagerModal
      :is-open="isGradeManagerOpen"
      :student="selectedGradeStudent"
      @close="closeGradeManager"
    />
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
