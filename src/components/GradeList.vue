<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { SubjectGrade, GradeUpsert } from '@/types'
import GradeEditModal from './GradeEditModal.vue'
import { apiFetch } from '@/utils/apiClient'
import { useAuthStore } from '@/stores/auth'

const grades = ref<SubjectGrade[]>([])
const isLoading = ref(true)
const isModalOpen = ref(false)
const selectedGrade = ref<SubjectGrade | null>(null)
const authStore = useAuthStore()

const showBulk = ref(false)
const bulkItems = ref<GradeUpsert[]>([])
const templates = ref<Record<string, Record<string, string[]>>>({})
const selectedDepartment = ref('')
const selectedCourse = ref('')
const importStatus = ref('')

const courseOptions = computed(() => {
  if (!selectedDepartment.value) return []
  return Object.keys(templates.value[selectedDepartment.value] || {})
})

const resetCourseOnDepartmentChange = () => {
  if (!selectedDepartment.value) {
    selectedCourse.value = ''
    return
  }
  if (!courseOptions.value.includes(selectedCourse.value)) {
    selectedCourse.value = ''
  }
}

const fetchGrades = async () => {
  isLoading.value = true
  try {
    const res = await apiFetch('/api/grades')
    if (res.ok) {
      grades.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch grades:', err)
  } finally {
    isLoading.value = false
  }
}

const fetchTemplates = async () => {
  try {
    if (!authStore.hydrated) await authStore.fetchMe()
    const res = await apiFetch('/api/subjects/templates')
    if (res.ok) {
      const data = await res.json()
      templates.value = data.templates || {}
      selectedDepartment.value = authStore.user?.department || ''
      selectedCourse.value = authStore.user?.course || ''
    }
  } catch (err) {
    console.error('Failed to fetch templates:', err)
  }
}

const openEditModal = (grade: SubjectGrade) => {
  selectedGrade.value = grade
  isModalOpen.value = true
}

const openCreateModal = () => {
  selectedGrade.value = null
  isModalOpen.value = true
}

const toggleBulk = () => {
  showBulk.value = !showBulk.value
  if (showBulk.value && bulkItems.value.length === 0) {
    bulkItems.value = [{ subject: '', units: 3, grade: 1.0, year: 1, semester: 1 }]
  }
}

const addBulkRow = () => {
  bulkItems.value.push({ subject: '', units: 3, grade: 1.0, year: 1, semester: 1 })
}

const removeBulkRow = (index: number) => {
  bulkItems.value.splice(index, 1)
}

const applyTemplate = () => {
  if (!selectedDepartment.value || !selectedCourse.value) return
  const subjects = templates.value[selectedDepartment.value]?.[selectedCourse.value] || []
  bulkItems.value = subjects.map((subject) => ({
    subject,
    units: 3,
    grade: 1.0,
    year: 1,
    semester: 1
  }))
  showBulk.value = true
}

const handleSaveGrade = async (gradeUpsert: GradeUpsert) => {
  try {
    const isEdit = typeof gradeUpsert.id === 'number'
    const url = isEdit ? `/api/grades/${gradeUpsert.id}` : '/api/grades'
    const method = isEdit ? 'PUT' : 'POST'

    const res = await apiFetch(url, {
      method,
      json: gradeUpsert
    })

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
    const res = await apiFetch(`/api/grades/${id}`, { method: 'DELETE' })
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

const saveBulkGrades = async () => {
  if (bulkItems.value.length === 0) return
  try {
    const res = await apiFetch('/api/grades/bulk', {
      method: 'POST',
      json: { items: bulkItems.value }
    })
    if (res.ok) {
      bulkItems.value = []
      showBulk.value = false
      await fetchGrades()
    } else {
      const data = await res.json()
      alert(`Error: ${data.detail || 'Failed to save bulk grades'}`)
    }
  } catch (err) {
    console.error('Failed to save bulk grades:', err)
    alert('An unexpected error occurred. Please try again later.')
  }
}

const exportCsv = () => {
  window.open('/api/grades/export.csv', '_blank')
}

const importCsv = async (file: File) => {
  importStatus.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiFetch('/api/grades/import', {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    if (res.ok) {
      importStatus.value = `Imported ${data.inserted} new and updated ${data.updated} grades.`
      await fetchGrades()
    } else {
      importStatus.value = data.detail || 'Import failed.'
    }
  } catch (err) {
    importStatus.value = 'Import failed. Please try again.'
    console.error('Import failed:', err)
  }
}

const onFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) importCsv(file)
  if (target) target.value = ''
}

onMounted(() => {
  fetchGrades()
  fetchTemplates()
})

watch(selectedDepartment, () => {
  resetCourseOnDepartmentChange()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Subjects</h3>
      <div class="flex flex-wrap items-center gap-2">
        <select v-model="selectedDepartment" class="px-3 py-2 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-xs font-bold">
          <option value="">Department</option>
          <option v-for="dept in Object.keys(templates)" :key="dept" :value="dept">{{ dept }}</option>
        </select>
        <select v-model="selectedCourse" class="px-3 py-2 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-xs font-bold">
          <option value="">Course</option>
          <option v-for="course in courseOptions" :key="course" :value="course">{{ course }}</option>
        </select>
        <button
          @click="applyTemplate"
          class="px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all"
        >
          Use Template
        </button>
        <button
          @click="toggleBulk"
          class="px-3 py-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-[10px] font-black uppercase tracking-widest rounded-xl hover:opacity-90 transition-all"
        >
          Bulk Entry
        </button>
        <label class="px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-600 transition-all">
          Import CSV
          <input type="file" accept=".csv" class="hidden" @change="onFileChange">
        </label>
        <button
          @click="exportCsv"
          class="px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all"
        >
          Export CSV
        </button>
        <button
          @click="openCreateModal"
          class="px-3 py-2 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-blue-700 transition-all active:scale-95"
        >
          Add Subject
        </button>
      </div>
    </div>

    <div v-if="importStatus" class="p-4 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border border-emerald-100 dark:border-emerald-900/30 rounded-2xl text-sm font-semibold">
      {{ importStatus }}
    </div>

    <div v-if="showBulk" class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm space-y-4">
      <div class="flex items-center justify-between">
        <div class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Bulk Entry</div>
        <button @click="addBulkRow" class="px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl">Add Row</button>
      </div>
      <div class="space-y-3">
        <div v-for="(item, index) in bulkItems" :key="index" class="grid grid-cols-1 md:grid-cols-6 gap-2">
          <input v-model="item.subject" type="text" placeholder="Subject" class="md:col-span-2 px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl text-sm font-medium dark:text-white">
          <input v-model.number="item.units" type="number" min="0.5" step="0.5" placeholder="Units" class="px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl text-sm font-medium dark:text-white">
          <input v-model.number="item.grade" type="number" min="1" max="5" step="0.01" placeholder="Grade" class="px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl text-sm font-medium dark:text-white">
          <input v-model.number="item.year" type="number" min="1" max="10" placeholder="Year" class="px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl text-sm font-medium dark:text-white">
          <div class="flex items-center gap-2">
            <input v-model.number="item.semester" type="number" min="1" max="3" placeholder="Sem" class="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl text-sm font-medium dark:text-white">
            <button @click="removeBulkRow(index)" class="px-3 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest rounded-xl">Remove</button>
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-3">
        <button @click="toggleBulk" class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-xs font-black uppercase tracking-widest rounded-xl">Cancel</button>
        <button @click="saveBulkGrades" class="px-4 py-2 bg-blue-600 text-white text-xs font-black uppercase tracking-widest rounded-xl">Save Bulk</button>
      </div>
    </div>

    <div v-if="isLoading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-100 dark:border-slate-700 animate-pulse">
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-full mb-2"></div>
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-3/4"></div>
      </div>
    </div>

    <div v-else-if="grades.length === 0" class="text-center p-12 text-slate-400 dark:text-slate-500 italic">
      No subjects recorded yet. Click “Add Subject” to start calculating your GWA.
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
