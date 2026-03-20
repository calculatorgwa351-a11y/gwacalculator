<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Chart from 'chart.js/auto'
import { apiFetch } from '@/utils/apiClient'

const props = defineProps<{
  userId: number
}>()

type ChartMode = 'cumulative' | 'semester'

const chartRef = ref<HTMLCanvasElement | null>(null)
const mode = ref<ChartMode>('cumulative')
const isLoading = ref(true)
const hasData = ref(false)

const dataset = ref<Record<ChartMode, { labels: string[]; values: number[] }>>({
  cumulative: { labels: [], values: [] },
  semester: { labels: [], values: [] }
})

let chart: Chart | null = null

const buildChart = (labels: string[], values: number[], label: string) => {
  if (!chartRef.value) return
  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return

  if (chart) chart.destroy()

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.12)',
          fill: true,
          tension: 0.35,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      scales: {
        y: {
          beginAtZero: false,
          reverse: false,
          min: 1.0,
          max: 5.0,
          grid: { color: 'rgba(15, 23, 42, 0.06)' },
          ticks: { font: { weight: 'bold' } }
        },
        x: {
          grid: { display: false },
          ticks: { font: { weight: 'bold' } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          titleFont: { size: 13, weight: 'bold' },
          bodyFont: { size: 12 },
          padding: 12,
          cornerRadius: 10
        }
      }
    }
  })
}

const render = () => {
  const selected = dataset.value[mode.value]
  hasData.value = selected.values.length > 0
  if (!hasData.value) return
  const label = mode.value === 'cumulative' ? 'Cumulative GWA' : 'Semester GWA'
  buildChart(selected.labels, selected.values, label)
}

const fetchData = async () => {
  if (!props.userId) return
  isLoading.value = true
  try {
    const [timelineRes, semesterRes] = await Promise.all([
      apiFetch(`/api/analytics/user-timeline?user_id=${props.userId}`),
      apiFetch('/api/analytics/semester_gwa')
    ])

    if (timelineRes.ok) {
      const data = await timelineRes.json()
      const labels = (data.timeline || []).map((item: any) => new Date(item.timestamp).toLocaleDateString())
      const values = (data.timeline || []).map((item: any) => item.gwa)
      dataset.value.cumulative = { labels, values }
    }

    if (semesterRes.ok) {
      const data = await semesterRes.json()
      const labels = (data.items || []).map((item: any) => `Y${item.year} S${item.semester}`)
      const values = (data.items || []).map((item: any) => item.gwa)
      dataset.value.semester = { labels, values }
    }
  } catch (err) {
    console.error('Failed to fetch chart data:', err)
  } finally {
    isLoading.value = false
    render()
  }
}

onMounted(() => {
  fetchData()
})

watch(() => props.userId, () => {
  fetchData()
})

watch(mode, () => {
  render()
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2">
      <button
        class="px-3 py-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all"
        :class="mode === 'cumulative' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-200'"
        @click="mode = 'cumulative'"
      >
        Cumulative
      </button>
      <button
        class="px-3 py-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all"
        :class="mode === 'semester' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-200'"
        @click="mode = 'semester'"
      >
        Per Semester
      </button>
    </div>

    <div class="h-64 relative">
      <div v-if="isLoading" class="absolute inset-0 animate-pulse bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800"></div>
      <div v-else-if="!hasData" class="absolute inset-0 flex items-center justify-center text-sm text-slate-400 dark:text-slate-500">
        No chart data yet.
      </div>
      <canvas v-else ref="chartRef"></canvas>
    </div>
  </div>
</template>
