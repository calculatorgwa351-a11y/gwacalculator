<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onErrorCaptured } from 'vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()

// Implement Vue's errorCaptured lifecycle hook to catch errors in descendants
onErrorCaptured((err, instance, info) => {
  console.error('Component captured error:', {
    error: err,
    instance,
    info
  })
  
  // Return false to prevent the error from propagating further
  return true
})
</script>

<template>
  <div class="min-h-screen text-slate-900 bg-slate-50 dark:bg-[#0f172a] dark:text-slate-200 transition-colors duration-300">
    <div
      v-if="session.expired"
      class="sticky top-0 z-50 bg-amber-50 text-amber-900 border-b border-amber-100 px-6 py-3 text-sm font-semibold flex items-center justify-between"
    >
      <span>{{ session.message }}</span>
      <button
        class="px-3 py-1 rounded-lg bg-amber-100 hover:bg-amber-200 transition"
        @click="session.clear()"
      >
        Dismiss
      </button>
    </div>
    <RouterView />
  </div>
</template>

<style>
/* Any global styles that aren't in Tailwind could go here */
:root {
  --ctu-blue: #0038a8;
  --ctu-orange: #f58220;
}

body {
  font-family: 'Inter', sans-serif;
}

.glass {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

.dark .glass {
  background: rgba(26, 32, 44, 0.9);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-in {
  animation: fadeIn 0.4s ease-out forwards;
}
</style>
