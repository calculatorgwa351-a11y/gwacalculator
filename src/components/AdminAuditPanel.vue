<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import type { AdminAuditResponse } from '@/types'
import { apiFetch } from '@/utils/apiClient'

const page = ref(1)
const limit = ref(10)
const total = ref(0)
const items = ref<AdminAuditResponse['items']>([])
const isLoading = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit.value)))

const fetchAudit = async () => {
  isLoading.value = true
  try {
    const res = await apiFetch(`/api/admin/audit?page=${page.value}&limit=${limit.value}`)
    if (res.ok) {
      const data = (await res.json()) as AdminAuditResponse
      items.value = data.items || []
      total.value = data.total || 0
    }
  } catch (err) {
    console.error('Failed to fetch audit log:', err)
  } finally {
    isLoading.value = false
  }
}

watch(page, () => {
  fetchAudit()
})

onMounted(() => {
  fetchAudit()
})
</script>

<template>
  <div class="space-y-6">
    <div class="bg-white dark:bg-slate-800 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">
      <div class="px-8 py-6 border-b border-slate-50 dark:border-slate-700 flex items-center justify-between">
        <h3 class="font-black text-slate-900 dark:text-white tracking-tight">Audit Log</h3>
        <div class="text-xs font-black uppercase tracking-widest text-slate-400">Page {{ page }} of {{ totalPages }}</div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead class="bg-slate-50/50 dark:bg-slate-900/50 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase tracking-widest">
            <tr>
              <th class="px-8 py-4">Timestamp</th>
              <th class="px-8 py-4">Admin</th>
              <th class="px-8 py-4">Action</th>
              <th class="px-8 py-4">Target</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr v-if="isLoading">
              <td colspan="4" class="px-8 py-6 text-sm text-slate-400">Loading...</td>
            </tr>
            <tr v-else-if="items.length === 0">
              <td colspan="4" class="px-8 py-6 text-sm text-slate-400">No audit events yet.</td>
            </tr>
            <tr v-for="entry in items" :key="entry.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
              <td class="px-8 py-5 text-sm font-semibold text-slate-600 dark:text-slate-300">
                {{ new Date(entry.timestamp).toLocaleString() }}
              </td>
              <td class="px-8 py-5 text-sm font-semibold text-slate-600 dark:text-slate-300">
                {{ entry.admin_name || entry.admin_user_id }}
              </td>
              <td class="px-8 py-5 text-sm font-semibold text-slate-600 dark:text-slate-300">
                {{ entry.action }}
              </td>
              <td class="px-8 py-5 text-sm font-semibold text-slate-600 dark:text-slate-300">
                {{ entry.target_type || '-' }} {{ entry.target_id || '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="flex items-center justify-center gap-3">
      <button
        class="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-xs font-black uppercase tracking-widest"
        :disabled="page === 1"
        @click="page = Math.max(1, page - 1)"
      >
        Prev
      </button>
      <button
        class="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-xs font-black uppercase tracking-widest"
        :disabled="page === totalPages"
        @click="page = Math.min(totalPages, page + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>
