<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { DashboardSummary, SubjectGrade } from '@/types'
import { apiFetch } from '@/utils/apiClient'

const props = defineProps<{
  summary?: DashboardSummary | null
}>()

const grades = ref<SubjectGrade[]>([])
const isLoading = ref(true)
const loadError = ref('')

type GwaSummaryCard = {
  key: string
  label: string
  gwa: number | null
  message: string
  band: string
  count: number
}

const yearLabels: Record<number, string> = {
  1: 'First Year',
  2: 'Second Year',
  3: 'Third Year',
  4: 'Fourth Year'
}

const formatGwa = (gwa: number | null) => (typeof gwa === 'number' ? gwa.toFixed(3) : 'N/A')

const calculateWeightedGwa = (items: SubjectGrade[]) => {
  const validItems = items.filter((item) => typeof item.units === 'number' && typeof item.grade === 'number')
  const totalUnits = validItems.reduce((sum, item) => sum + item.units, 0)
  if (totalUnits <= 0) return null
  const totalWeighted = validItems.reduce((sum, item) => sum + item.units * item.grade, 0)
  return Number((totalWeighted / totalUnits).toFixed(3))
}

const getSemesterFeedback = (gwa: number | null) => {
  if (gwa === null) {
    return {
      band: 'Waiting for Result',
      message: 'Your admin-uploaded semester grades will show here once available.'
    }
  }
  if (gwa >= 1.0 && gwa <= 1.5) {
    return {
      band: 'Excellent',
      message: 'Excellent work! Keep aiming high, future achiever!'
    }
  }
  if (gwa <= 2.0) {
    return {
      band: 'Very Good',
      message: "Great job! You're on the right track, padayon!"
    }
  }
  if (gwa <= 2.75) {
    return {
      band: 'Good',
      message: 'Good effort! With more focus, you can do even better!'
    }
  }
  if (gwa <= 3.0) {
    return {
      band: 'Passing',
      message: 'You passed! Keep pushing, you can improve next time!'
    }
  }
  return {
    band: 'Needs Improvement',
    message: "Don't give up! Every setback is a chance to grow."
  }
}

const getOverallFeedback = (gwa: number | null) => {
  if (gwa === null) {
    return {
      band: 'Waiting for Result',
      message: 'Your overall GWA will appear after the admin uploads your grades.'
    }
  }
  if (gwa >= 1.0 && gwa <= 1.5) {
    return {
      band: 'Outstanding',
      message: 'Outstanding performance! You are truly excelling in your academic journey!'
    }
  }
  if (gwa <= 2.0) {
    return {
      band: 'Very Strong',
      message: 'Very strong performance! Keep pushing towards excellence!'
    }
  }
  if (gwa <= 2.75) {
    return {
      band: 'Doing Well',
      message: "You're doing well overall. Stay consistent and aim higher!"
    }
  }
  if (gwa <= 3.0) {
    return {
      band: 'Room to Improve',
      message: "You made it through, but there's room for improvement. Keep going!"
    }
  }
  return {
    band: 'Bounce Back',
    message: 'This is not the end. Use this as motivation to bounce back stronger!'
  }
}

const toneClass = (band: string) => {
  switch (band) {
    case 'Excellent':
    case 'Outstanding':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300'
    case 'Very Good':
    case 'Very Strong':
      return 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-300'
    case 'Good':
    case 'Doing Well':
      return 'border-cyan-200 bg-cyan-50 text-cyan-700 dark:border-cyan-500/30 dark:bg-cyan-500/10 dark:text-cyan-300'
    case 'Passing':
    case 'Room to Improve':
      return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300'
    case 'Needs Improvement':
    case 'Bounce Back':
      return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300'
    default:
      return 'border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'
  }
}

const semesterSummaries = computed<GwaSummaryCard[]>(() => {
  const groups = new Map<string, SubjectGrade[]>()
  for (const grade of grades.value) {
    const key = `${grade.year}-${grade.semester}`
    const existing = groups.get(key) || []
    existing.push(grade)
    groups.set(key, existing)
  }

  return Array.from(groups.entries())
    .sort((a, b) => {
      const [aYear, aSem] = a[0].split('-').map(Number)
      const [bYear, bSem] = b[0].split('-').map(Number)
      return aYear - bYear || aSem - bSem
    })
    .map(([key, items]) => {
      const [year, semester] = key.split('-').map(Number)
      const gwa = calculateWeightedGwa(items)
      const feedback = getSemesterFeedback(gwa)
      return {
        key,
        label: `${yearLabels[year] || `Year ${year}`} - ${semester}${semester === 1 ? 'st' : semester === 2 ? 'nd' : semester === 3 ? 'rd' : 'th'} Semester`,
        gwa,
        count: items.length,
        band: feedback.band,
        message: feedback.message
      }
    })
})

const yearlySummaries = computed<GwaSummaryCard[]>(() =>
  [1, 2, 3, 4].map((year) => {
    const items = grades.value.filter((grade) => grade.year === year)
    const gwa = calculateWeightedGwa(items)
    const feedback = getSemesterFeedback(gwa)
    return {
      key: `year-${year}`,
      label: yearLabels[year],
      gwa,
      count: items.length,
      band: feedback.band,
      message: feedback.message
    }
  })
)

const overallSummary = computed(() => {
  const gwa = calculateWeightedGwa(grades.value)
  const feedback = getOverallFeedback(gwa)
  return {
    gwa,
    band: feedback.band,
    message: feedback.message,
    count: grades.value.length
  }
})

const honorsTitle = computed(() => props.summary?.honors?.title || 'No Latin Honors Yet')
const honorsReason = computed(() => {
  if (!grades.value.length) return 'Latin honors will be evaluated automatically once your academic record is complete.'
  return props.summary?.honors?.reason || 'Your Latin honors standing is computed automatically from your uploaded grades.'
})
const nextHonorsTarget = computed(() => props.summary?.honors_progress?.next_target || 'Cum Laude')
const honorsEligibility = computed(() => {
  if (!grades.value.length) {
    return {
      label: 'Eligibility Pending',
      message: 'Eligibility will appear once your grades are complete.',
      detail: 'Current standing will appear after the admin uploads your full academic record.',
      tone: 'border-slate-200 bg-white/10 text-blue-50/90'
    }
  }

  const gwa = overallSummary.value.gwa
  const honors = props.summary?.honors
  if (honors?.eligible && honors.title) {
    return {
      label: 'Eligible',
      message: `Eligible for ${honors.title}`,
      detail: `Current standing: ${formatGwa(gwa)} qualifies for ${honors.title}.`,
      tone: 'border-emerald-300/40 bg-emerald-400/10 text-emerald-100'
    }
  }

  const nextTarget = props.summary?.honors_progress?.next_target
  const gap = props.summary?.honors_progress?.gap_to_next_target
  return {
    label: 'Not Yet Eligible',
    message: 'Not eligible for Latin honors yet.',
    detail:
      nextTarget && typeof gap === 'number'
        ? `Current standing: ${formatGwa(gwa)}. You need to improve by ${gap.toFixed(3)} to reach ${nextTarget}.`
        : `Current standing: ${formatGwa(gwa)}. Keep improving your GWA to qualify for Latin honors.`,
    tone: 'border-amber-300/40 bg-amber-400/10 text-amber-100'
  }
})

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
        <h3 class="text-xs font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300">Recorded Grades</h3>
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

    <template v-else>
      <section class="space-y-4">
        <div>
          <h3 class="text-xs font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300">Per Semester GWA</h3>
          <p class="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
            Every semester result comes with a quick performance message to help you track your progress.
          </p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <div
            v-for="semester in semesterSummaries"
            :key="semester.key"
            class="bg-white dark:bg-slate-800 p-5 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm space-y-3"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="text-xs font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300">{{ semester.label }}</div>
                <div class="mt-2 text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ formatGwa(semester.gwa) }}</div>
              </div>
              <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
                {{ semester.count }} Subject{{ semester.count === 1 ? '' : 's' }}
              </div>
            </div>
            <div :class="['rounded-2xl border px-4 py-3 text-sm font-semibold leading-relaxed', toneClass(semester.band)]">
                  <div class="text-xs font-black uppercase tracking-[0.16em] mb-1">{{ semester.band }}</div>
              <div>{{ semester.message }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="space-y-4">
        <div>
          <h3 class="text-xs font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300">Yearly GWA</h3>
          <p class="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
            Your first year to fourth year standing is computed automatically from the uploaded semester grades.
          </p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <div
            v-for="year in yearlySummaries"
            :key="year.key"
            class="bg-white dark:bg-slate-800 p-5 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm space-y-3"
          >
            <div class="text-xs font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300">{{ year.label }}</div>
            <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ formatGwa(year.gwa) }}</div>
            <div :class="['rounded-2xl border px-4 py-3 text-sm font-semibold leading-relaxed', toneClass(year.band)]">
              <div class="text-xs font-black uppercase tracking-[0.16em] mb-1">{{ year.band }}</div>
              <div>{{ year.message }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-gradient-to-br from-slate-900 to-blue-950 dark:from-slate-950 dark:to-slate-900 text-white p-6 rounded-[2rem] shadow-xl shadow-slate-900/20 space-y-5">
        <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div>
            <div class="text-xs font-black uppercase tracking-[0.16em] text-blue-200/80">Overall GWA</div>
            <div class="mt-2 text-5xl font-black tracking-tight tabular-nums">{{ formatGwa(overallSummary.gwa) }}</div>
            <div class="mt-3 text-base font-medium text-blue-50/90 leading-relaxed">{{ overallSummary.count }} uploaded subjects included in this result.</div>
          </div>
          <div class="lg:max-w-sm w-full rounded-[1.5rem] bg-white/10 border border-white/10 p-4">
            <div class="text-xs font-black uppercase tracking-[0.16em] text-blue-200/80">Latin Honors Standing</div>
            <div class="mt-2 text-2xl font-black">{{ honorsTitle }}</div>
            <div
              :class="[
                'mt-4 rounded-2xl border px-4 py-3',
                honorsEligibility.tone
              ]"
            >
              <div class="text-[10px] font-black uppercase tracking-[0.16em] opacity-80">{{ honorsEligibility.label }}</div>
              <div class="mt-1 text-base font-black leading-snug">{{ honorsEligibility.message }}</div>
              <div class="mt-2 text-sm font-medium leading-relaxed opacity-90">{{ honorsEligibility.detail }}</div>
            </div>
            <div class="mt-3 text-base leading-relaxed text-blue-50/90">{{ honorsReason }}</div>
            <div class="mt-3 text-xs font-black uppercase tracking-[0.16em] text-blue-200/80">
              Next target: {{ nextHonorsTarget }}
            </div>
          </div>
        </div>

        <div class="rounded-[1.5rem] bg-white/10 border border-white/10 px-5 py-4">
          <div class="text-xs font-black uppercase tracking-[0.16em] text-blue-200/80 mb-2">{{ overallSummary.band }}</div>
          <div class="text-base md:text-lg font-semibold leading-relaxed">{{ overallSummary.message }}</div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div class="rounded-2xl bg-white/10 px-4 py-3">
            <div class="text-xs font-black uppercase tracking-[0.16em] text-blue-200/80">Cum Laude</div>
            <div class="mt-1 font-semibold">1.46 to 1.75</div>
          </div>
          <div class="rounded-2xl bg-white/10 px-4 py-3">
            <div class="text-xs font-black uppercase tracking-[0.16em] text-blue-200/80">Magna Cum Laude</div>
            <div class="mt-1 font-semibold">1.21 to 1.45</div>
          </div>
          <div class="rounded-2xl bg-white/10 px-4 py-3">
            <div class="text-xs font-black uppercase tracking-[0.16em] text-blue-200/80">Summa Cum Laude</div>
            <div class="mt-1 font-semibold">1.00 to 1.20</div>
          </div>
        </div>
      </section>

      <section class="space-y-4">
        <div>
          <h3 class="text-xs font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300">Uploaded Subject Grades</h3>
          <p class="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
            These are the read-only grades uploaded by the admin for each subject and semester.
          </p>
        </div>

        <div v-for="grade in grades" :key="grade.id" class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm animate-in">
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <div :class="['w-10 h-10 rounded-xl flex items-center justify-center font-bold', grade.failed ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400']">
                {{ grade.grade.toFixed(2) }}
              </div>
              <div>
                <div class="font-bold text-slate-800 dark:text-white">{{ grade.subject }}</div>
                <div class="text-xs font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300">
                  Units: {{ grade.units }} | {{ grade.year }} Year, {{ grade.semester }} Semester
                </div>
              </div>
            </div>
            <div class="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-xs font-black uppercase tracking-[0.16em] text-slate-600 dark:text-slate-200">
              Read Only
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
