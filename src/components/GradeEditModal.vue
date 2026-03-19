<script setup lang="ts">
import { ref, watch } from 'vue'
import type { SubjectGrade } from '@/types'

const props = defineProps<{
  grade: SubjectGrade | null
  isOpen: boolean
}>()

const emit = defineEmits(['close', 'save'])

const subject = ref('')
const units = ref(0)
const grade = ref(0)

watch(() => props.grade, (newGrade) => {
  if (newGrade) {
    subject.value = newGrade.subject
    units.value = newGrade.units
    grade.value = newGrade.grade
  }
})

const handleSave = () => {
  if (!props.grade) return

  const updatedGrade = {
    ...props.grade,
    subject: subject.value,
    units: units.value,
    grade: grade.value
  }

  emit('save', updatedGrade)
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in">
    <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] shadow-xl border border-slate-100 dark:border-slate-700 w-full max-w-md">
      <h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight mb-6">Edit Grade</h2>

      <form @submit.prevent="handleSave" class="space-y-6">
        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Subject</label>
          <input v-model="subject" type="text" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Units</label>
            <input v-model.number="units" type="number" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
          </div>
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Grade</label>
            <input v-model.number="grade" type="number" step="0.01" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
          </div>
        </div>

        <div class="flex justify-end gap-4 pt-6 border-t border-slate-50 dark:border-slate-700">
          <button type="button" @click="emit('close')" class="px-6 py-3 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all">Cancel</button>
          <button type="submit" class="px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-all">Save Changes</button>
        </div>
      </form>
    </div>
  </div>
</template>
