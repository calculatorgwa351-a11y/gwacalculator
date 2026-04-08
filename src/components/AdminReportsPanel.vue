<script setup lang="ts">
import { computed, ref } from 'vue'
import type { User } from '@/types'
import { apiFetch } from '@/utils/apiClient'

const props = defineProps<{
  students: User[]
}>()

const searchTerm = ref('')
const isDownloadingCsv = ref(false)
const downloadingStudentId = ref<number | null>(null)
const actionError = ref('')

const filtered = computed(() => {
  if (!searchTerm.value) return props.students
  const term = searchTerm.value.toLowerCase()
  return props.students.filter(
    (s) =>
      s.name.toLowerCase().includes(term) ||
      s.school_id.toLowerCase().includes(term) ||
      (s.department && s.department.toLowerCase().includes(term))
  )
})

const getFilenameFromDisposition = (disposition: string | null, fallback: string) => {
  if (!disposition) return fallback

  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1])

  const asciiMatch = disposition.match(/filename="?([^"]+)"?/i)
  return asciiMatch?.[1] || fallback
}

const triggerBrowserDownload = (blob: Blob, filename: string) => {
  const downloadUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = downloadUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(downloadUrl)
}

const downloadFile = async (url: string, fallbackFilename: string) => {
  const res = await apiFetch(url)
  if (!res.ok) {
    let message = 'Failed to download report.'
    try {
      const data = await res.json()
      message = data.detail || message
    } catch {
      // Ignore JSON parse failures and keep the generic message.
    }
    throw new Error(message)
  }

  const blob = await res.blob()
  const filename = getFilenameFromDisposition(res.headers.get('content-disposition'), fallbackFilename)
  triggerBrowserDownload(blob, filename)
}

const openCsv = async () => {
  if (isDownloadingCsv.value) return
  isDownloadingCsv.value = true
  actionError.value = ''

  try {
    await downloadFile('/api/admin/reports/students.csv', 'students_report.csv')
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'Failed to download CSV.'
  } finally {
    isDownloadingCsv.value = false
  }
}

const openStudentReport = async (student: User) => {
  if (downloadingStudentId.value === student.id) return
  downloadingStudentId.value = student.id
  actionError.value = ''

  try {
    await downloadFile(`/api/admin/reports/student/${student.id}.html`, `${student.school_id}_report.html`)
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : 'Failed to download student report.'
  } finally {
    downloadingStudentId.value = null
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm flex items-center justify-between gap-4">
      <div>
        <div class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Reports</div>
        <div class="text-lg font-black text-slate-900 dark:text-white">Download student performance reports</div>
      </div>
      <button
        @click="openCsv"
        :disabled="isDownloadingCsv"
        class="px-4 py-2 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-blue-700 transition-all"
      >
        {{ isDownloadingCsv ? 'Downloading...' : 'Download CSV' }}
      </button>
    </div>

    <div
      v-if="actionError"
      class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-600"
    >
      {{ actionError }}
    </div>

    <div class="bg-white dark:bg-slate-800 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">
      <div class="px-8 py-6 border-b border-slate-50 dark:border-slate-700 flex items-center justify-between">
        <h3 class="font-black text-slate-900 dark:text-white tracking-tight">Printable Student Reports</h3>
        <input
          v-model="searchTerm"
          placeholder="Search student..."
          class="px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-xl text-sm font-semibold dark:text-white"
        >
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead class="bg-slate-50/50 dark:bg-slate-900/50 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase tracking-widest">
            <tr>
              <th class="px-8 py-4">Student</th>
              <th class="px-8 py-4 text-center">Department</th>
              <th class="px-8 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr v-for="s in filtered" :key="s.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
              <td class="px-8 py-5">
                <div class="font-black text-slate-900 dark:text-white text-sm">{{ s.name }}</div>
                <div class="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-widest">{{ s.school_id }}</div>
              </td>
              <td class="px-8 py-5 text-center text-sm font-bold text-slate-600 dark:text-slate-300">
                {{ s.department || 'General' }}
              </td>
              <td class="px-8 py-5 text-right">
                <button
                  @click="openStudentReport(s)"
                  :disabled="downloadingStudentId === s.id"
                  class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all"
                >
                  {{ downloadingStudentId === s.id ? 'Downloading...' : 'Download Report' }}
                </button>
              </td>
            </tr>
            <tr v-if="filtered.length === 0">
              <td colspan="3" class="px-8 py-6 text-sm text-slate-400">No students found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
