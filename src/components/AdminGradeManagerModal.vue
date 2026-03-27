<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import GradeEditModal from '@/components/GradeEditModal.vue'
import { apiFetch } from '@/utils/apiClient'
import type { AdminGradeImportResponse, GradeUpsert, SubjectGrade, User } from '@/types'

const props = defineProps<{
  isOpen: boolean
  student: User | null
}>()

const emit = defineEmits<{
  close: []
}>()

const grades = ref<SubjectGrade[]>([])
const isLoading = ref(false)
const errorMessage = ref('')
const importResult = ref<AdminGradeImportResponse | null>(null)
const isEditorOpen = ref(false)
const selectedGrade = ref<SubjectGrade | null>(null)
const openYears = ref<number[]>([])

const currentGwa = computed(() => {
  const gwa = grades.value.find((grade) => typeof grade.gwa === 'number')?.gwa
  return typeof gwa === 'number' ? gwa : null
})

const gradesByYear = computed(() => {
  const grouped = new Map<number, SubjectGrade[]>()

  for (const grade of grades.value) {
    const year = grade.year || 1
    if (!grouped.has(year)) {
      grouped.set(year, [])
    }
    grouped.get(year)?.push(grade)
  }

  return Array.from(grouped.entries())
    .sort(([leftYear], [rightYear]) => leftYear - rightYear)
    .map(([year, items]) => ({
      year,
      items: [...items].sort((left, right) => {
        if (left.semester !== right.semester) return left.semester - right.semester
        return left.subject.localeCompare(right.subject)
      })
    }))
})

const syncOpenYears = () => {
  const availableYears = gradesByYear.value.map((group) => group.year)
  const filteredOpenYears = openYears.value.filter((year) => availableYears.includes(year))

  if (filteredOpenYears.length > 0) {
    openYears.value = filteredOpenYears
    return
  }

  openYears.value = availableYears.length > 0 ? [availableYears[0]] : []
}

const isYearOpen = (year: number) => openYears.value.includes(year)

const toggleYear = (year: number) => {
  if (isYearOpen(year)) {
    openYears.value = openYears.value.filter((entry) => entry !== year)
    return
  }

  openYears.value = [...openYears.value, year].sort((left, right) => left - right)
}

const resetState = () => {
  grades.value = []
  isLoading.value = false
  errorMessage.value = ''
  importResult.value = null
  isEditorOpen.value = false
  selectedGrade.value = null
  openYears.value = []
}

const fetchGrades = async () => {
  if (!props.student?.id) return

  isLoading.value = true
  errorMessage.value = ''
  try {
    const res = await apiFetch(`/api/admin/student/${props.student.id}/grades`)
    const data = await res.json().catch(() => [])
    if (res.ok) {
      grades.value = data
      syncOpenYears()
    } else {
      grades.value = []
      errorMessage.value = data.detail || data.error || 'Failed to load student grades.'
    }
  } catch (err) {
    console.error('Failed to fetch student grades:', err)
    grades.value = []
    errorMessage.value = 'Failed to load student grades.'
  } finally {
    isLoading.value = false
  }
}

const openCreateModal = () => {
  selectedGrade.value = null
  isEditorOpen.value = true
}

const openEditModal = (grade: SubjectGrade) => {
  selectedGrade.value = grade
  isEditorOpen.value = true
}

const closeEditor = () => {
  isEditorOpen.value = false
  selectedGrade.value = null
}

const saveGrade = async (payload: GradeUpsert) => {
  if (!props.student?.id) return

  const isEdit = typeof payload.id === 'number'
  const url = isEdit
    ? `/api/admin/student/${props.student.id}/grades/${payload.id}`
    : `/api/admin/student/${props.student.id}/grades`
  const method = isEdit ? 'PUT' : 'POST'

  try {
    const res = await apiFetch(url, {
      method,
      json: payload
    })
    const data = await res.json().catch(() => ({}))
    if (res.ok) {
      closeEditor()
      await fetchGrades()
    } else {
      alert(`Error: ${data.detail || data.error || 'Failed to save grade'}`)
    }
  } catch (err) {
    console.error('Failed to save grade:', err)
    alert('An unexpected error occurred while saving the grade.')
  }
}

const deleteGrade = async (grade: SubjectGrade) => {
  if (!props.student?.id) return
  if (!confirm(`Delete ${grade.subject} for ${props.student.name}?`)) return

  try {
    const res = await apiFetch(`/api/admin/student/${props.student.id}/grades/${grade.id}`, {
      method: 'DELETE'
    })
    const data = await res.json().catch(() => ({}))
    if (res.ok) {
      await fetchGrades()
    } else {
      alert(`Error: ${data.detail || data.error || 'Failed to delete grade'}`)
    }
  } catch (err) {
    console.error('Failed to delete grade:', err)
    alert('An unexpected error occurred while deleting the grade.')
  }
}

const onImportFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  importResult.value = null
  errorMessage.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiFetch('/api/admin/grades/import', {
      method: 'POST',
      body: formData
    })
    const data = (await res.json().catch(() => ({}))) as AdminGradeImportResponse
    importResult.value = {
      success: !!res.ok,
      inserted: data.inserted || 0,
      updated: data.updated || 0,
      students_affected: data.students_affected || 0,
      errors: data.errors || []
    }

    if (res.ok) {
      await fetchGrades()
    } else if (!importResult.value.errors.length) {
      errorMessage.value = 'Import failed.'
    }
  } catch (err) {
    console.error('Failed to import grades:', err)
    errorMessage.value = 'Import failed.'
  } finally {
    target.value = ''
  }
}

const downloadTemplate = () => {
  window.open('/api/admin/grades/import-template.csv', '_blank')
}

watch(
  () => [props.isOpen, props.student?.id] as const,
  async ([open]) => {
    if (open) {
      await fetchGrades()
    } else {
      resetState()
    }
  }
)
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
    <div class="w-full max-w-6xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-[2.5rem] shadow-xl overflow-hidden">
      <div class="px-8 py-6 border-b border-slate-100 dark:border-slate-700 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Admin Grade Management</div>
          <div class="text-xl font-black text-slate-900 dark:text-white">
            {{ props.student?.name || 'Student' }}
            <span class="ml-2 text-sm text-slate-400 dark:text-slate-500">{{ props.student?.school_id }}</span>
          </div>
          <div class="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
            Grades are centrally managed here. Students can only view the results after login.
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            @click="openCreateModal"
            class="px-4 py-2 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-blue-700 transition-all"
          >
            Add Grade
          </button>
          <label class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-600 transition-all">
            Import CSV
            <input type="file" accept=".csv" class="hidden" @change="onImportFileChange">
          </label>
          <button
            @click="downloadTemplate"
            class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all"
          >
            CSV Template
          </button>
          <button
            @click="emit('close')"
            class="px-4 py-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-[10px] font-black uppercase tracking-widest rounded-xl hover:opacity-90 transition-all"
          >
            Close
          </button>
        </div>
      </div>

      <div class="p-8 space-y-6 max-h-[80vh] overflow-y-auto">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-6 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Current GWA</div>
            <div class="mt-2 text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ currentGwa?.toFixed(3) ?? '-' }}</div>
          </div>
          <div class="p-6 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Recorded Subjects</div>
            <div class="mt-2 text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ grades.length }}</div>
          </div>
          <div class="p-6 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Department</div>
            <div class="mt-2 text-lg font-black text-slate-900 dark:text-white">{{ props.student?.department || 'General' }}</div>
          </div>
        </div>

        <div v-if="errorMessage" class="p-4 rounded-2xl border border-red-200 bg-red-50 text-red-600 text-sm font-semibold">
          {{ errorMessage }}
        </div>

        <div
          v-if="importResult"
          class="p-5 rounded-[2rem] border"
          :class="importResult.success ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-800'"
        >
          <div class="text-[10px] font-black uppercase tracking-[0.2em]">Import Results</div>
          <div class="mt-2 text-sm font-semibold">
            Inserted: {{ importResult.inserted }} | Updated: {{ importResult.updated }} | Students affected: {{ importResult.students_affected || 0 }} | Errors: {{ importResult.errors.length }}
          </div>
          <div class="mt-2 text-xs font-medium opacity-80">
            CSV import applies to all matching student IDs in the file, not just the student currently open in this modal.
          </div>
          <div v-if="importResult.errors.length" class="mt-3 space-y-2">
            <div
              v-for="entry in importResult.errors"
              :key="`${entry.line}-${entry.error}`"
              class="px-4 py-3 rounded-xl bg-white/70 border border-current/10 text-sm font-medium"
            >
              Line {{ entry.line }}: {{ entry.error }}
            </div>
          </div>
        </div>

        <div v-if="isLoading" class="space-y-4">
          <div v-for="i in 3" :key="i" class="bg-white dark:bg-slate-900 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 animate-pulse">
            <div class="h-4 bg-slate-100 dark:bg-slate-700 rounded w-full mb-2"></div>
            <div class="h-4 bg-slate-100 dark:bg-slate-700 rounded w-2/3"></div>
          </div>
        </div>

        <div v-else-if="grades.length === 0" class="text-center p-10 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-slate-500 dark:text-slate-400 italic">
          No grades recorded yet for this student. Use Add Grade or import a CSV file for one or more student IDs.
        </div>

        <div v-else class="space-y-6">
          <section
            v-for="yearGroup in gradesByYear"
            :key="yearGroup.year"
            class="bg-white dark:bg-slate-900 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden"
          >
            <button
              type="button"
              class="w-full px-6 py-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-950/50 flex items-center justify-between gap-4 text-left hover:bg-slate-100/80 dark:hover:bg-slate-900 transition-colors"
              @click="toggleYear(yearGroup.year)"
            >
              <div>
                <div class="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Academic Year</div>
                <div class="mt-1 text-xl font-black text-slate-900 dark:text-white">{{ yearGroup.year }} Year</div>
                <div class="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">
                  {{ yearGroup.items.length }} subject{{ yearGroup.items.length === 1 ? '' : 's' }} recorded
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-xs font-black uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                  {{ isYearOpen(yearGroup.year) ? 'Hide Table' : 'Show Table' }}
                </span>
                <span
                  class="w-10 h-10 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 transition-transform"
                  :class="isYearOpen(yearGroup.year) ? 'rotate-180' : ''"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </span>
              </div>
            </button>

            <div v-if="isYearOpen(yearGroup.year)" class="overflow-x-auto">
              <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-800">
                <thead class="bg-white/80 dark:bg-slate-900/80">
                  <tr>
                    <th class="px-6 py-4 text-left text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Semester</th>
                    <th class="px-6 py-4 text-left text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Subject</th>
                    <th class="px-6 py-4 text-left text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Units</th>
                    <th class="px-6 py-4 text-left text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Grade</th>
                    <th class="px-6 py-4 text-left text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Status</th>
                    <th class="px-6 py-4 text-right text-[10px] font-black uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                  <tr
                    v-for="grade in yearGroup.items"
                    :key="grade.id"
                    class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td class="px-6 py-4 text-sm font-bold text-slate-600 dark:text-slate-300">
                      Semester {{ grade.semester }}
                    </td>
                    <td class="px-6 py-4">
                      <div class="font-black text-slate-900 dark:text-white">{{ grade.subject }}</div>
                      <div class="mt-1 text-xs font-semibold text-slate-500 dark:text-slate-400">
                        Recorded for {{ yearGroup.year }} Year
                      </div>
                    </td>
                    <td class="px-6 py-4 text-sm font-bold text-slate-700 dark:text-slate-200">
                      {{ grade.units }}
                    </td>
                    <td class="px-6 py-4">
                      <span
                        :class="[
                          'inline-flex min-w-16 justify-center rounded-xl px-3 py-2 text-sm font-black',
                          grade.failed
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                            : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                        ]"
                      >
                        {{ grade.grade.toFixed(2) }}
                      </span>
                    </td>
                    <td class="px-6 py-4">
                      <span
                        :class="[
                          'inline-flex rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em]',
                          grade.failed
                            ? 'bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-300'
                            : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-300'
                        ]"
                      >
                        {{ grade.failed ? 'Needs Attention' : 'Passing' }}
                      </span>
                    </td>
                    <td class="px-6 py-4">
                      <div class="flex justify-end gap-2">
                        <button
                          @click="openEditModal(grade)"
                          class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all"
                        >
                          Edit
                        </button>
                        <button
                          @click="deleteGrade(grade)"
                          class="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-red-100 dark:hover:bg-red-900/30 transition-all"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>

    <GradeEditModal
      :is-open="isEditorOpen"
      :grade="selectedGrade"
      @close="closeEditor"
      @save="saveGrade"
    />
  </div>
</template>
