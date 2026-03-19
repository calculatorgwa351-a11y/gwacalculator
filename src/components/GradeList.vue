<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { SubjectGrade } from '@/types'
import GradeEditModal from './GradeEditModal.vue'

const grades = ref<SubjectGrade[]>([])
const isLoading = ref(true)
const isModalOpen = ref(false)
const selectedGrade = ref<SubjectGrade | null>(null)

const fetchGrades = async () => {
  isLoading.value = true
  try {
    const res = await fetch('/api/grades')
    if (res.ok) {
      grades.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch grades:', err)
  } finally {
    isLoading.value = false
  }
}

const openEditModal = (grade: SubjectGrade) => {
  selectedGrade.value = grade
  isModalOpen.value = true
}

const handleSaveGrade = async (updatedGrade: SubjectGrade) => {
  try {
    const res = await fetch(`/api/grades/${updatedGrade.id}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedGrade)
      }
    )

    if (res.ok) {
      await fetchGrades()
      isModalOpen.value = false
    } else {
      const data = await res.json()
      alert(`Error: ${data.detail || 'Failed to save grade'}`)
    }
  } catch (err) {
    console.error('Failed to save grade:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

const handleDeleteGrade = async (id: number) => {
  if (!confirm('Are you sure you want to delete this grade?')) return

  try {
    const res = await fetch(`/api/grades/${id}`, { method: 'DELETE' })
    if (res.ok) {
      await fetchGrades()
    } else {
      const data = await res.json()
      alert(`Error: ${data.detail || 'Failed to delete grade'}`)
    }
  } catch (err) {
    console.error('Failed to delete grade:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

onMounted(() => {
  fetchGrades()
})
</script>

<template>
  <div class="space-y-6">
    <div v-if="isLoading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-100 dark:border-slate-700 animate-pulse">
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-full mb-2"></div>
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-3/4"></div>
      </div>
    </div>

    <div v-else-if="grades.length === 0" class="text-center p-12 text-slate-400 dark:text-slate-500 italic">
      No grades recorded yet. Start by adding your first subject!
    </div>

    <div v-for="grade in grades" :key="grade.id" class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm animate-in">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div :class="['w-10 h-10 rounded-xl flex items-center justify-center font-bold', grade.failed ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400']">
            {{ grade.grade.toFixed(2) }}
          </div>
          <div>
            <div class="font-bold text-slate-800 dark:text-white">{{ grade.subject }}</div>
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
              Units: {{ grade.units }} · {{ grade.year }} Year, {{ grade.semester }} Semester
            </div>
          </div>
        </div>
        <div class="flex gap-2">
          <button @click="openEditModal(grade)" class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all active:scale-95">
            Edit
          </button>
          <button @click="handleDeleteGrade(grade.id)" class="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-red-100 transition-all active:scale-95">
            Delete
          </button>
        </div>
      </div>
    </div>

    <GradeEditModal 
      :is-open="isModalOpen" 
      :grade="selectedGrade" 
      @close="isModalOpen = false" 
      @save="handleSaveGrade"
    />
  </div>
</template>
