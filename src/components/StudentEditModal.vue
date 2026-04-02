<script setup lang="ts">
import { ref, watch } from 'vue'
import type { User } from '@/types'

const props = defineProps<{
  user: User | null
  isOpen: boolean
  isSaving?: boolean
  errorMessage?: string
}>()

const emit = defineEmits(['close', 'save'])

const name = ref('')
const schoolId = ref('')
const department = ref('')
const course = ref('')
const password = ref('')

watch(() => props.user, (newUser) => {
  if (newUser) {
    name.value = newUser.name
    schoolId.value = newUser.school_id
    department.value = newUser.department || ''
    course.value = newUser.course || ''
    password.value = ''
  }
})

const handleSave = () => {
  if (!props.user || props.isSaving) return

  const updatedUser = {
    ...props.user,
    name: name.value,
    school_id: schoolId.value,
    department: department.value,
    course: course.value,
    password: password.value
  }

  emit('save', updatedUser)
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in p-4">
    <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] shadow-xl border border-slate-100 dark:border-slate-700 w-full max-w-md">
      <h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight mb-6">Edit Student</h2>

      <form @submit.prevent="handleSave" class="space-y-6">
        <div v-if="props.errorMessage" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-600">
          {{ props.errorMessage }}
        </div>

        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Full Name</label>
          <input v-model="name" :disabled="props.isSaving" type="text" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium disabled:opacity-60 dark:text-white">
        </div>

        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">School ID</label>
          <input v-model="schoolId" :disabled="props.isSaving" type="text" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium disabled:opacity-60 dark:text-white">
        </div>

        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Department</label>
          <input v-model="department" :disabled="props.isSaving" type="text" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium disabled:opacity-60 dark:text-white">
        </div>

        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Course</label>
          <input v-model="course" :disabled="props.isSaving" type="text" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium disabled:opacity-60 dark:text-white">
        </div>

        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">New Password (optional)</label>
          <input v-model="password" :disabled="props.isSaving" type="password" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium disabled:opacity-60 dark:text-white">
        </div>

        <div class="flex justify-end gap-4 pt-6 border-t border-slate-50 dark:border-slate-700">
          <button type="button" :disabled="props.isSaving" @click="emit('close')" class="px-6 py-3 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all disabled:opacity-60">Cancel</button>
          <button type="submit" :disabled="props.isSaving" class="inline-flex min-w-36 items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-all disabled:opacity-70">
            <svg v-if="props.isSaving" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
            </svg>
            {{ props.isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
