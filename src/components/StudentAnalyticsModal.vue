<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Chart from 'chart.js/auto'
import type { AdminStudentDetail } from '@/types'
import { apiFetch } from '@/utils/apiClient'

const props = defineProps<{
  isOpen: boolean
  studentId: number | null
}>()

const emit = defineEmits(['close', 'manage-grades'])

const isLoading = ref(false)
const detail = ref<AdminStudentDetail | null>(null)
const loadError = ref('')

const timelineRef = ref<HTMLCanvasElement | null>(null)
const gradesRef = ref<HTMLCanvasElement | null>(null)

let timelineChart: Chart | null = null
let gradesChart: Chart | null = null

const destroyCharts = () => {
  timelineChart?.destroy()
  gradesChart?.destroy()
  timelineChart = null
  gradesChart = null
}

const renderCharts = async () => {
  destroyCharts()
  if (!detail.value || !props.studentId) return

  // Timeline (cumulative GWA)
  if (timelineRef.value) {
    try {
      const res = await apiFetch(`/api/analytics/user-timeline?user_id=${props.studentId}`)
      if (res.ok) {
        const data = await res.json()
        const labels = (data.timeline || []).map((item: any) => new Date(item.timestamp).toLocaleDateString())
        const values = (data.timeline || []).map((item: any) => item.gwa)

        const ctx = timelineRef.value.getContext('2d')
        if (ctx) {
          timelineChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels,
              datasets: [
                {
                  label: 'GWA over time',
                  data: values,
                  borderColor: '#2563eb',
                  backgroundColor: 'rgba(37, 99, 235, 0.12)',
                  fill: true,
                  tension: 0.35,
                  pointRadius: 4,
                  pointHoverRadius: 6,
                  pointBackgroundColor: '#2563eb',
                  pointBorderColor: '#fff',
                  pointBorderWidth: 2
                }
              ]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: false } },
              scales: {
                y: { reverse: false, min: 1.0, max: 5.0 },
                x: { grid: { display: false } }
              }
            }
          })
        }
      }
    } catch (err) {
      console.error('Failed to render timeline chart:', err)
    }
  }

  // Subject grades (bar)
  if (gradesRef.value) {
    const grades = [...(detail.value.grades || [])]
      .filter((g) => typeof g.grade === 'number')
      .sort((a, b) => new Date(a.timestamp || 0).getTime() - new Date(b.timestamp || 0).getTime())

    const labels = grades.map((g) => g.subject)
    const values = grades.map((g) => g.grade)
    const colors = grades.map((g) => (g.failed ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.22)'))
    const borders = grades.map((g) => (g.failed ? '#ef4444' : '#10b981'))

    const ctx = gradesRef.value.getContext('2d')
    if (ctx) {
      gradesChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Grade',
              data: values,
              backgroundColor: colors,
              borderColor: borders,
              borderWidth: 2,
              borderRadius: 10
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { reverse: false, min: 1.0, max: 5.0, beginAtZero: false },
            x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 6 } }
          }
        }
      })
    }
  }
}

const fetchDetail = async () => {
  if (!props.studentId) return
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await apiFetch(`/api/admin/student/${props.studentId}`)
    if (res.ok) {
      detail.value = (await res.json()) as AdminStudentDetail
      await nextTick()
      await renderCharts()
    } else {
      const data = await res.json().catch(() => ({}))
      loadError.value = data?.detail || data?.error || 'Failed to load student details.'
    }
  } catch (err) {
    console.error('Failed to fetch student detail:', err)
    loadError.value = 'Failed to load student details.'
  } finally {
    isLoading.value = false
  }
}

watch(
  () => [props.isOpen, props.studentId] as const,
  async ([open]) => {
    if (open) {
      detail.value = null
      await fetchDetail()
      await nextTick()
      await renderCharts()
    }
    else {
      detail.value = null
      loadError.value = ''
      destroyCharts()
    }
  }
)

onMounted(() => {
  if (props.isOpen) fetchDetail()
})

onBeforeUnmount(() => {
  destroyCharts()
})
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in p-4">
    <div class="bg-white dark:bg-slate-800 w-full max-w-5xl rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl overflow-hidden">
      <div class="px-8 py-6 border-b border-slate-50 dark:border-slate-700 flex items-center justify-between">
        <div>
          <div class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Student Analytics</div>
          <div class="text-xl font-black text-slate-900 dark:text-white">
            {{ detail?.name || 'Loading…' }}
            <span class="text-slate-400 dark:text-slate-500 font-black text-sm ml-2">{{ detail?.school_id }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="props.studentId"
            @click="emit('manage-grades')"
            class="px-4 py-2 bg-blue-600 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-blue-700 transition-all"
          >
            Manage Grades
          </button>
          <button
            @click="emit('close')"
            class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all"
          >
            Close
          </button>
        </div>
      </div>

      <div class="p-8 space-y-8">
        <div v-if="loadError" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-600">
          {{ loadError }}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="p-6 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Current GWA</div>
            <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums mt-2">{{ detail?.gwa?.toFixed(3) ?? '—' }}</div>
          </div>
          <div class="p-6 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Subjects</div>
            <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums mt-2">{{ detail?.grades?.length ?? 0 }}</div>
          </div>
          <div class="p-6 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Posts</div>
            <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums mt-2">{{ detail?.posts?.length ?? 0 }}</div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
            <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 mb-4">GWA Timeline</h3>
            <div class="h-72 relative">
              <div v-if="isLoading" class="absolute inset-0 animate-pulse bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800"></div>
              <canvas v-else ref="timelineRef"></canvas>
            </div>
          </div>

          <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
            <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 mb-4">Subject Grades</h3>
            <div class="h-72 relative">
              <div v-if="isLoading" class="absolute inset-0 animate-pulse bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800"></div>
              <canvas v-else ref="gradesRef"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
