<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import type { GradeDistribution, TopBottomResponse, AtRiskResponse } from '@/types'
import { apiFetch } from '@/utils/apiClient'

type NumberMap = Record<string, number>

const isLoading = ref(true)
const departmentAvg = ref<NumberMap>({})
const failureRates = ref<NumberMap>({})
const gradeDistribution = ref<GradeDistribution | null>(null)
const topBottom = ref<TopBottomResponse | null>(null)
const atRisk = ref<AtRiskResponse | null>(null)

const deptChartRef = ref<HTMLCanvasElement | null>(null)
const failureChartRef = ref<HTMLCanvasElement | null>(null)
const distChartRef = ref<HTMLCanvasElement | null>(null)

let deptChart: Chart | null = null
let failureChart: Chart | null = null
let distChart: Chart | null = null

const destroyCharts = () => {
  deptChart?.destroy()
  failureChart?.destroy()
  distChart?.destroy()
  deptChart = null
  failureChart = null
  distChart = null
}

const buildBarChart = (canvas: HTMLCanvasElement, labels: string[], values: number[], opts: { label: string; reverseY?: boolean }) => {
  const ctx = canvas.getContext('2d')
  if (!ctx || labels.length === 0 || values.length === 0) return null

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: opts.label,
          data: values,
          backgroundColor: 'rgba(37, 99, 235, 0.2)',
          borderColor: '#2563eb',
          borderWidth: 2,
          borderRadius: 12
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          titleFont: { size: 14, weight: 'bold' },
          bodyFont: { size: 13 },
          padding: 12,
          cornerRadius: 12
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { weight: 'bold' as const } }
        },
        y: {
          beginAtZero: true,
          reverse: !!opts.reverseY,
          grid: { color: 'rgba(0, 0, 0, 0.05)' },
          ticks: { font: { weight: 'bold' as const } }
        }
      }
    }
  })
}

const renderCharts = () => {
  destroyCharts()

  if (deptChartRef.value) {
    const labels = Object.keys(departmentAvg.value)
    const values = labels.map((k) => departmentAvg.value[k])
    deptChart = buildBarChart(deptChartRef.value, labels, values, { label: 'Avg GWA (by department)', reverseY: false })
  }

  if (failureChartRef.value) {
    const labels = Object.keys(failureRates.value)
    const values = labels.map((k) => failureRates.value[k])
    failureChart = buildBarChart(failureChartRef.value, labels, values, { label: 'Failure rate % (by department)' })
  }

  if (distChartRef.value && gradeDistribution.value) {
    const labels = gradeDistribution.value.buckets.map((b) => b.label)
    const values = gradeDistribution.value.buckets.map((b) => b.count)
    distChart = buildBarChart(distChartRef.value, labels, values, { label: 'Grade distribution (all students)' })
  }
}

const fetchAnalytics = async () => {
  isLoading.value = true
  try {
    const [deptRes, failRes, distRes] = await Promise.all([
      apiFetch('/api/analytics/department_avg'),
      apiFetch('/api/analytics/failure_rates'),
      apiFetch('/api/analytics/grade_distribution')
    ])

    if (deptRes.ok) departmentAvg.value = (await deptRes.json()) as NumberMap
    if (failRes.ok) failureRates.value = (await failRes.json()) as NumberMap
    if (distRes.ok) gradeDistribution.value = (await distRes.json()) as GradeDistribution

    const [topRes, riskRes] = await Promise.all([
      apiFetch('/api/analytics/top_bottom'),
      apiFetch('/api/analytics/at_risk')
    ])
    if (topRes.ok) topBottom.value = (await topRes.json()) as TopBottomResponse
    if (riskRes.ok) atRisk.value = (await riskRes.json()) as AtRiskResponse

  } catch (err) {
    console.error('Failed to fetch admin analytics:', err)
  } finally {
    isLoading.value = false
    await nextTick()
    renderCharts()
  }
}

onMounted(() => {
  fetchAnalytics()
})

onBeforeUnmount(() => {
  destroyCharts()
})
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Department Avg</h3>
      </div>
      <div class="h-64 relative">
        <canvas ref="deptChartRef"></canvas>
        <div v-if="isLoading" class="absolute inset-0 animate-pulse bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800"></div>
      </div>
    </div>

    <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Failure Rates</h3>
      </div>
      <div class="h-64 relative">
        <canvas ref="failureChartRef"></canvas>
        <div v-if="isLoading" class="absolute inset-0 animate-pulse bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800"></div>
      </div>
    </div>

    <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">Grade Distribution</h3>
      </div>
      <div class="h-64 relative">
        <canvas ref="distChartRef"></canvas>
        <div v-if="isLoading" class="absolute inset-0 animate-pulse bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800"></div>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
    <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
      <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 mb-4">Top Performers</h3>
      <div v-if="isLoading" class="text-sm text-slate-400">Loading...</div>
      <div v-else class="space-y-3">
        <div v-for="student in topBottom?.top || []" :key="student.id" class="flex items-center justify-between bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 px-4 py-3">
          <div>
            <div class="font-bold text-slate-900 dark:text-white text-sm">{{ student.name }}</div>
            <div class="text-[10px] text-slate-400 uppercase tracking-widest font-black">{{ student.school_id }}</div>
          </div>
          <div class="text-sm font-black text-emerald-600 dark:text-emerald-300">{{ student.gwa.toFixed(3) }}</div>
        </div>
      </div>
    </div>

    <div class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm">
      <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 mb-4">Needs Attention</h3>
      <div v-if="isLoading" class="text-sm text-slate-400">Loading...</div>
      <div v-else class="space-y-3 max-h-72 overflow-auto">
        <div v-for="student in atRisk?.items || []" :key="student.id" class="bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 px-4 py-3">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-bold text-slate-900 dark:text-white text-sm">{{ student.name }}</div>
              <div class="text-[10px] text-slate-400 uppercase tracking-widest font-black">{{ student.school_id }}</div>
            </div>
            <div class="text-sm font-black text-amber-600 dark:text-amber-300">{{ student.gwa ? student.gwa.toFixed(3) : 'N/A' }}</div>
          </div>
          <div class="text-xs text-slate-500 dark:text-slate-400 mt-2">
            {{ student.reasons.join(', ') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
