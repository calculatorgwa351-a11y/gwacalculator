<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits(['close', 'save'])

const name = ref('')
const schoolId = ref('')
const department = ref('')
const course = ref('')
const password = ref('password123')

const handleSave = () => {
  if (!name.value || !schoolId.value || !password.value) return
  emit('save', {
    name: name.value,
    school_id: schoolId.value,
    department: department.value,
    course: course.value,
    password: password.value
  })
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in">
    <div class="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] shadow-xl border border-slate-100 dark:border-slate-700 w-full max-w-md">
      <h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight mb-6">Create Student</h2>

      <form @submit.prevent="handleSave" class="space-y-6">
        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Full Name</label>
          <input v-model="name" type="text" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
        </div>

        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">School ID</label>
          <input v-model="schoolId" type="text" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Department</label>
            <input v-model="department" type="text" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
          </div>
          <div class="space-y-2">
            <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Course</label>
            <input v-model="course" type="text" class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
          </div>
        </div>

        <div class="space-y-2">
          <label class="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 ml-1">Temporary Password</label>
          <input v-model="password" type="text" required class="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white">
        </div>

        <div class="flex justify-end gap-4 pt-6 border-t border-slate-50 dark:border-slate-700">
          <button type="button" @click="emit('close')" class="px-6 py-3 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-all">Cancel</button>
          <button type="submit" class="px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-all">Create</button>
        </div>
      </form>
    </div>
  </div>
</template>
