<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Post } from '@/types'

const posts = ref<Post[]>([])
const isLoading = ref(true)
const commentDraft = ref<Record<number, string>>({})

const fetchPosts = async () => {
  isLoading.value = true
  try {
    const res = await fetch('/api/posts')
    if (res.ok) {
      posts.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch posts:', err)
  } finally {
    isLoading.value = false
  }
}

const reactToPost = async (postId: number, type: string) => {
  try {
    const res = await fetch(`/api/posts/${postId}/react`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type })
    })
    if (res.ok) {
      const data = await res.json()
      const post = posts.value.find(p => p.id === postId)
      if (post) {
        post.reactions = data.reactions
      }
    }
  } catch (err) {
    console.error('Failed to react:', err)
  }
}

const addComment = async (postId: number) => {
  const content = (commentDraft.value[postId] || '').trim()
  if (!content) return

  try {
    const res = await fetch(`/api/posts/${postId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    })

    if (res.ok) {
      const newComment = await res.json()
      const post = posts.value.find((p) => p.id === postId)
      if (post) {
        post.comments = [...(post.comments || []), newComment]
      }
      commentDraft.value[postId] = ''
    }
  } catch (err) {
    console.error('Failed to comment:', err)
  }
}

onMounted(() => {
  fetchPosts()
})
</script>

<template>
  <div class="space-y-6">
    <div v-if="isLoading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-100 dark:border-slate-700 animate-pulse">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-xl"></div>
          <div class="space-y-2">
            <div class="h-3 bg-slate-100 dark:bg-slate-700 rounded w-24"></div>
            <div class="h-2 bg-slate-100 dark:bg-slate-700 rounded w-16"></div>
          </div>
        </div>
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-full mb-2"></div>
        <div class="h-4 bg-slate-50 dark:bg-slate-700 rounded w-3/4"></div>
      </div>
    </div>

    <div v-else-if="posts.length === 0" class="text-center p-12 text-slate-400 dark:text-slate-500 italic">
      No posts to show yet. Be the first to share!
    </div>

    <div v-for="post in posts" :key="post.id" class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm animate-in">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center font-bold">
            {{ post.author.charAt(0) }}
          </div>
          <div>
            <div class="font-bold text-slate-800 dark:text-white">{{ post.author }}</div>
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
              {{ new Date(post.timestamp).toLocaleDateString() }}
            </div>
          </div>
        </div>
      </div>

      <p class="text-slate-600 dark:text-slate-300 font-medium leading-relaxed mb-6">
        {{ post.content }}
      </p>

      <div class="flex items-center gap-2 pt-4 border-t border-slate-50 dark:border-slate-700">
        <button 
          v-for="(count, type) in post.reactions" 
          :key="type"
          @click="reactToPost(post.id, type)"
          class="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-all active:scale-95"
        >
          <span v-if="type === 'like'">👍</span>
          <span v-else-if="type === 'love'">❤️</span>
          <span v-else-if="type === 'wow'">😮</span>
          <span class="text-xs font-black text-slate-400 dark:text-slate-500">{{ count }}</span>
        </button>
      </div>

      <div class="mt-4 space-y-3">
        <div v-if="post.comments?.length" class="space-y-2">
          <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Comments</div>
          <div v-for="c in post.comments" :key="c.id" class="p-3 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <div class="text-xs font-black text-slate-700 dark:text-slate-200">{{ c.user }}</div>
              <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">{{ new Date(c.timestamp).toLocaleDateString() }}</div>
            </div>
            <div class="text-sm text-slate-600 dark:text-slate-300 font-medium mt-1">{{ c.content }}</div>
          </div>
        </div>

        <form @submit.prevent="addComment(post.id)" class="flex items-center gap-2">
          <input
            v-model="commentDraft[post.id]"
            type="text"
            placeholder="Write a comment..."
            class="flex-1 px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"
          >
          <button
            type="submit"
            class="px-4 py-3 bg-blue-600 text-white text-xs font-black uppercase tracking-widest rounded-2xl hover:bg-blue-700 transition-all active:scale-95"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
