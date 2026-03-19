<script setup lang="ts">
// No script logic needed for now
</script>

<template>
  <div class="space-y-8 animate-in">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div class="lg:col-span-2 space-y-4 md:space-y-8">
        <!-- Latin Honors Policy -->
        <div class="bg-white dark:bg-slate-800 p-6 md:p-8 rounded-[2rem] border border-slate-200 dark:border-slate-700 shadow-sm">
          <h3 class="text-xl md:text-2xl font-black text-slate-800 dark:text-white tracking-tight mb-6 flex items-center gap-3">
            <span class="p-2 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-xl">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
            </span>
            Latin Honors Policy
          </h3>
          <div class="prose prose-slate dark:prose-invert max-w-none">
            <p class="text-sm md:text-base text-slate-600 dark:text-slate-400 font-medium mb-4">Graduating students who meet the following academic requirements shall be awarded Latin Honors:</p>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <div class="p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
                <div class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Summa Cum Laude</div>
                <div class="text-lg md:text-xl font-black text-slate-800 dark:text-white">1.00 - 1.20</div>
              </div>
              <div class="p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
                <div class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Magna Cum Laude</div>
                <div class="text-lg md:text-xl font-black text-slate-800 dark:text-white">1.21 - 1.45</div>
              </div>
              <div class="p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
                <div class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Cum Laude</div>
                <div class="text-lg md:text-xl font-black text-slate-800 dark:text-white">1.46 - 1.75</div>
              </div>
            </div>
            
            <h4 class="font-black text-slate-800 dark:text-white mb-3">General Requirements:</h4>
            <ul class="space-y-2">
              <li class="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400 font-medium">
                <svg class="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                Must have completed the degree within the prescribed period.
              </li>
              <li class="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400 font-medium">
                <svg class="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                No failing grade (5.0) in any academic or non-academic subject.
              </li>
              <li class="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400 font-medium">
                <svg class="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                No grade lower than 2.5 in any subject (including elective/minor).
              </li>
              <li class="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400 font-medium">
                <svg class="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                Must have carried a regular load (min. 15 units) every semester.
              </li>
            </ul>
          </div>
        </div>

        <!-- Grading Scale Detail -->
        <div class="bg-white dark:bg-slate-800 p-8 rounded-[2rem] border border-slate-200 dark:border-slate-700 shadow-sm">
          <h3 class="text-2xl font-black text-slate-800 dark:text-white tracking-tight mb-6 flex items-center gap-3">
            <span class="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>
            </span>
            Official Grading Scale
          </h3>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-slate-100 dark:border-slate-700">
                  <th class="py-4 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Numerical Grade</th>
                  <th class="py-4 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Percentage Equiv.</th>
                  <th class="py-4 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Description</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-50 dark:divide-slate-700">
                <tr>
                  <td class="py-4 text-sm font-black text-slate-800 dark:text-white">1.0 - 1.2</td>
                  <td class="py-4 text-sm font-medium text-slate-500 dark:text-slate-400">96 - 100%</td>
                  <td class="py-4 text-sm font-bold text-emerald-600 dark:text-emerald-400">Excellent</td>
                </tr>
                <tr>
                  <td class="py-4 text-sm font-black text-slate-800 dark:text-white">1.3 - 1.5</td>
                  <td class="py-4 text-sm font-medium text-slate-500 dark:text-slate-400">91 - 95%</td>
                  <td class="py-4 text-sm font-bold text-emerald-600 dark:text-emerald-400">Very Good</td>
                </tr>
                <tr>
                  <td class="py-4 text-sm font-black text-slate-800 dark:text-white">1.6 - 2.5</td>
                  <td class="py-4 text-sm font-medium text-slate-500 dark:text-slate-400">81 - 90%</td>
                  <td class="py-4 text-sm font-bold text-blue-500 dark:text-blue-400">Good / Satisfactory</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
