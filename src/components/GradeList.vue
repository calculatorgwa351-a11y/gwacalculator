<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { SubjectGrade } from '@/types'
import { apiFetch } from '@/utils/apiClient'

const grades = ref<SubjectGrade[]>([])
const isLoading = ref(true)
const loadError = ref('')

const fetchGrades = async () => {
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await apiFetch('/api/grades')
    if (res.ok) {
      grades.value = await res.json()
    } else {
      const data = await res.json().catch(() => ({}))
      loadError.value = data.detail || data.error || 'Failed to load grades.'
    }
  } catch (err) {
    console.error('Failed to fetch grades:', err)
    loadError.value = 'Failed to load grades.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchGrades()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Recorded Grades</h3>
        <p class="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
          Grades are managed by the admin and appear here automatically once uploaded.
        </p>
      </div>
    </div>

    <div v-if="loadError" class="p-4 rounded-2xl border border-red-200 bg-red-50 text-red-600 text-sm font-semibold">
      {{ loadError }}
    </div>

    <div v-else-if="isLoading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-100 dark:border-slate-700 animate-pulse">
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-full mb-2"></div>
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-3/4"></div>
      </div>
    </div>

    <div v-else-if="grades.length === 0" class="text-center p-12 text-slate-400 dark:text-slate-500 italic">
      No grades have been uploaded yet. Your evaluation will appear here after the admin publishes your records.
    </div>

    <div v-for="grade in grades" :key="grade.id" class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm animate-in">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div :class="['w-10 h-10 rounded-xl flex items-center justify-center font-bold', grade.failed ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400']">
            {{ grade.grade.toFixed(2) }}
          </div>
          <div>
            <div class="font-bold text-slate-800 dark:text-white">{{ grade.subject }}</div>
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
              Units: {{ grade.units }} | {{ grade.year }} Year, {{ grade.semester }} Semester
            </div>
          </div>
        </div>
        <div class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-300">
          Read Only
        </div>
      </div>
    </div>
  </div>
</template>
