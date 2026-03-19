<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps<{
  userId: number
}>()

const chartRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const initChart = async () => {
  if (!chartRef.value) return

  try {
    const res = await fetch(`/api/analytics/user-timeline?user_id=${props.userId}`)
    if (!res.ok) return
    const data = await res.json()

    const ctx = chartRef.value.getContext('2d')
    if (!ctx) return

    const labels = data.timeline.map((item: any) => new Date(item.timestamp).toLocaleDateString())
    const values = data.timeline.map((item: any) => item.gwa)

    if (chart) chart.destroy()

    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'GWA over time',
          data: values,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 6,
          pointHoverRadius: 8,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index',
        },
        scales: {
          y: {
            beginAtZero: false,
            reverse: true,
            suggestedMin: 1.0,
            suggestedMax: 5.0,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              font: { weight: 'bold' }
            }
          },
          x: {
            grid: { display: false },
            ticks: {
              font: { weight: 'bold' }
            }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1e293b',
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 13 },
            padding: 12,
            cornerRadius: 12
          }
        }
      }
    })
  } catch (err) {
    console.error('Failed to init chart:', err)
  }
}

onMounted(() => {
  initChart()
})

watch(() => props.userId, () => {
  initChart()
})
</script>

<template>
  <div class="h-64 relative">
    <canvas ref="chartRef"></canvas>
  </div>
</template>
