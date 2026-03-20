<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { Comment, Post, PostsFeedResponse } from '@/types'
import { apiFetch } from '@/utils/apiClient'

const posts = ref<Post[]>([])
const isLoading = ref(true)
const commentDraft = ref<Record<number, string>>({})
const replyTo = ref<Record<number, Comment | null>>({})
const editPostId = ref<number | null>(null)
const editDraft = ref('')

const page = ref(1)
const limit = ref(5)
const total = ref(0)

const department = ref('')
const course = ref('')
const mine = ref(false)

const departmentOptions = ['COTE', 'COED', 'CBM']
const courseOptions: Record<string, string[]> = {
  COTE: ['Computer Science', 'Computer Engineering'],
  COED: ['Elementary Education', 'Secondary Education'],
  CBM: ['Business Administration', 'Accountancy']
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit.value)))

const buildThread = (comments: Comment[]) => {
  const sorted = [...comments].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
  const roots = sorted.filter((c) => !c.parent_comment_id)
  const replies = sorted.filter((c) => c.parent_comment_id)
  const replyMap: Record<number, Comment[]> = {}
  for (const reply of replies) {
    const parentId = reply.parent_comment_id || 0
    if (!replyMap[parentId]) replyMap[parentId] = []
    replyMap[parentId].push(reply)
  }
  return roots.map((root) => ({
    comment: root,
    replies: replyMap[root.id] || []
  }))
}

const fetchPosts = async () => {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('limit', String(limit.value))
    if (department.value) params.set('department', department.value)
    if (course.value) params.set('course', course.value)
    if (mine.value) params.set('mine', '1')

    const res = await apiFetch(`/api/posts/feed?${params.toString()}`)
    if (res.ok) {
      const data = (await res.json()) as PostsFeedResponse
      posts.value = data.items || []
      total.value = data.total || 0
    }
  } catch (err) {
    console.error('Failed to fetch posts:', err)
  } finally {
    isLoading.value = false
  }
}

const reactToPost = async (postId: number, type: string) => {
  try {
    const res = await apiFetch(`/api/posts/${postId}/react`, {
      method: 'POST',
      json: { type }
    })
    if (res.ok) {
      const data = await res.json()
      const post = posts.value.find((p) => p.id === postId)
      if (post) post.reactions = data.reactions
    }
  } catch (err) {
    console.error('Failed to react:', err)
  }
}

const startEditPost = (post: Post) => {
  editPostId.value = post.id
  editDraft.value = post.content
}

const cancelEditPost = () => {
  editPostId.value = null
  editDraft.value = ''
}

const saveEditPost = async (postId: number) => {
  if (!editDraft.value.trim()) return
  try {
    const res = await apiFetch(`/api/posts/${postId}`, {
      method: 'PUT',
      json: { content: editDraft.value }
    })
    if (res.ok) {
      const post = posts.value.find((p) => p.id === postId)
      if (post) post.content = editDraft.value
      cancelEditPost()
    }
  } catch (err) {
    console.error('Failed to update post:', err)
  }
}

const deletePost = async (postId: number) => {
  if (!confirm('Delete this post?')) return
  try {
    const res = await apiFetch(`/api/posts/${postId}`, { method: 'DELETE' })
    if (res.ok) posts.value = posts.value.filter((p) => p.id !== postId)
  } catch (err) {
    console.error('Failed to delete post:', err)
  }
}

const addComment = async (postId: number) => {
  const content = (commentDraft.value[postId] || '').trim()
  if (!content) return

  const parent = replyTo.value[postId]
  try {
    const res = await apiFetch(`/api/posts/${postId}/comments`, {
      method: 'POST',
      json: { content, parent_id: parent?.id }
    })
    if (res.ok) {
      const newComment = await res.json()
      const post = posts.value.find((p) => p.id === postId)
      if (post) post.comments = [...(post.comments || []), newComment]
      commentDraft.value[postId] = ''
      replyTo.value[postId] = null
    }
  } catch (err) {
    console.error('Failed to comment:', err)
  }
}

const deleteComment = async (postId: number, commentId: number) => {
  if (!confirm('Delete this comment?')) return
  try {
    const res = await apiFetch(`/api/posts/${postId}/comments/${commentId}`, { method: 'DELETE' })
    if (res.ok) {
      const post = posts.value.find((p) => p.id === postId)
      if (post) post.comments = (post.comments || []).filter((c) => c.id !== commentId)
    }
  } catch (err) {
    console.error('Failed to delete comment:', err)
  }
}

const setReplyTo = (postId: number, comment: Comment) => {
  replyTo.value[postId] = comment
}

const clearReplyTo = (postId: number) => {
  replyTo.value[postId] = null
}

watch([page, department, course, mine], () => {
  fetchPosts()
})

watch(department, () => {
  course.value = ''
  page.value = 1
})

watch(course, () => {
  page.value = 1
})

watch(mine, () => {
  page.value = 1
})

onMounted(() => {
  fetchPosts()
})
</script>

<template>
  <div class="space-y-6">
    <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm flex flex-wrap items-center gap-3">
      <select v-model="department" class="px-3 py-2 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm font-semibold">
        <option value="">All departments</option>
        <option v-for="dept in departmentOptions" :key="dept" :value="dept">{{ dept }}</option>
      </select>
      <select v-model="course" class="px-3 py-2 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm font-semibold">
        <option value="">All courses</option>
        <option v-for="c in courseOptions[department] || []" :key="c" :value="c">{{ c }}</option>
      </select>
      <label class="flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-300">
        <input v-model="mine" type="checkbox" class="accent-blue-600">
        My posts only
      </label>
      <div class="ml-auto text-xs font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
        Page {{ page }} of {{ totalPages }}
      </div>
    </div>

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
      No posts to show yet. Be the first to share.
    </div>

    <div v-for="post in posts" :key="post.id" class="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-sm animate-in">
      <div class="flex items-start justify-between gap-4 mb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center font-bold">
            {{ post.author.charAt(0) }}
          </div>
          <div>
            <div class="font-bold text-slate-800 dark:text-white">{{ post.author }}</div>
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
              {{ new Date(post.timestamp).toLocaleDateString() }}
            </div>
            <div class="text-[10px] font-black uppercase tracking-widest text-slate-300 dark:text-slate-500">
              {{ post.department || 'General' }} | {{ post.course || 'Student' }}
            </div>
          </div>
        </div>
        <div v-if="post.can_edit" class="flex items-center gap-2">
          <button
            v-if="editPostId !== post.id"
            @click="startEditPost(post)"
            class="px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-[10px] font-black uppercase tracking-widest rounded-xl"
          >
            Edit
          </button>
          <button
            v-if="editPostId !== post.id"
            @click="deletePost(post.id)"
            class="px-3 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest rounded-xl"
          >
            Delete
          </button>
        </div>
      </div>

      <div v-if="editPostId === post.id" class="space-y-3">
        <textarea
          v-model="editDraft"
          class="w-full p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium dark:text-white"
        ></textarea>
        <div class="flex justify-end gap-2">
          <button @click="cancelEditPost" class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-200 text-xs font-black uppercase tracking-widest rounded-xl">Cancel</button>
          <button @click="saveEditPost(post.id)" class="px-4 py-2 bg-blue-600 text-white text-xs font-black uppercase tracking-widest rounded-xl">Save</button>
        </div>
      </div>

      <p v-else class="text-slate-600 dark:text-slate-300 font-medium leading-relaxed mb-6">
        {{ post.content }}
      </p>

      <div class="flex items-center gap-2 pt-4 border-t border-slate-50 dark:border-slate-700">
        <button
          v-for="(count, type) in post.reactions"
          :key="type"
          @click="reactToPost(post.id, type)"
          class="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-all active:scale-95"
        >
          <span v-if="type === 'like'">Like</span>
          <span v-else-if="type === 'love'">Love</span>
          <span v-else-if="type === 'wow'">Wow</span>
          <span class="text-xs font-black text-slate-400 dark:text-slate-500">{{ count }}</span>
        </button>
      </div>

      <div class="mt-4 space-y-3">
        <div v-if="post.comments?.length" class="space-y-2">
          <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Comments</div>
          <div v-for="entry in buildThread(post.comments)" :key="entry.comment.id" class="space-y-2">
            <div class="p-3 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
              <div class="flex items-center justify-between">
                <div class="text-xs font-black text-slate-700 dark:text-slate-200">{{ entry.comment.user }}</div>
                <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">{{ new Date(entry.comment.timestamp).toLocaleDateString() }}</div>
              </div>
              <div class="text-sm text-slate-600 dark:text-slate-300 font-medium mt-1">{{ entry.comment.content }}</div>
              <div class="mt-2 flex items-center gap-2">
                <button @click="setReplyTo(post.id, entry.comment)" class="text-[10px] font-black uppercase tracking-widest text-blue-600">Reply</button>
                <button v-if="entry.comment.can_delete" @click="deleteComment(post.id, entry.comment.id)" class="text-[10px] font-black uppercase tracking-widest text-red-500">Delete</button>
              </div>
            </div>
            <div v-for="reply in entry.replies" :key="reply.id" class="ml-6 p-3 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700">
              <div class="flex items-center justify-between">
                <div class="text-xs font-black text-slate-700 dark:text-slate-200">{{ reply.user }}</div>
                <div class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">{{ new Date(reply.timestamp).toLocaleDateString() }}</div>
              </div>
              <div class="text-sm text-slate-600 dark:text-slate-300 font-medium mt-1">{{ reply.content }}</div>
              <div class="mt-2 flex items-center gap-2">
                <button v-if="reply.can_delete" @click="deleteComment(post.id, reply.id)" class="text-[10px] font-black uppercase tracking-widest text-red-500">Delete</button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="replyTo[post.id]" class="flex items-center justify-between text-xs text-slate-500">
          Replying to {{ replyTo[post.id]?.user }}
          <button class="text-blue-600 font-bold" @click="clearReplyTo(post.id)">Cancel</button>
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

    <div v-if="totalPages > 1" class="flex items-center justify-center gap-3">
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
