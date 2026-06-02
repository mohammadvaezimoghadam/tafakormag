<template>
  <div class="bg-white rounded-3xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300 relative text-right flex flex-col space-y-4">
    <!-- هدر پست (اطلاعات نویسنده و دکمه حذف) -->
    <div class="flex items-center justify-between">
      <!-- دکمه حذف (فقط برای سازنده پست) -->
      <button
        v-if="isAuthor"
        @click="$emit('delete', post.id)"
        class="text-gray-300 hover:text-red-500 hover:bg-red-50 p-1.5 rounded-xl transition-colors shrink-0"
        title="حذف پست"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
      <div v-else class="w-5"></div>

      <!-- اطلاعات نویسنده -->
      <div class="flex items-center space-x-3 space-x-reverse overflow-hidden">
        <div class="text-right">
          <span class="font-extrabold text-gray-800 text-xs block leading-none">{{ post.author_name }}</span>
          <span class="text-[10px] text-gray-400 block mt-1 leading-none">{{ formatTime(post.created_at) }}</span>
        </div>
        <div class="w-9 h-9 bg-gradient-to-tr from-indigo-500 to-indigo-600 text-white rounded-full flex items-center justify-center font-bold text-sm shrink-0 shadow">
          {{ post.author_name.charAt(0) }}
        </div>
      </div>
    </div>

    <!-- بدنه پست (مدیا و متن) -->
    <div class="space-y-3">
      <!-- نمایش تصاویر -->
      <div v-if="post.media_type === 'image' && post.media_file" class="rounded-2xl overflow-hidden border border-gray-100 shadow-sm relative group cursor-pointer" @click="lightboxOpen = true">
        <img :src="getImageUrl(post.media_file)" class="w-full max-h-72 object-cover group-hover:scale-105 transition-transform duration-500" alt="Post media" />
        <div class="absolute inset-0 bg-black/10 group-hover:bg-black/0 transition-colors"></div>
      </div>

      <!-- نمایش ویدیو -->
      <div v-else-if="post.media_type === 'video' && post.media_file" class="rounded-2xl overflow-hidden border border-gray-100 shadow-sm bg-black">
        <video :src="getImageUrl(post.media_file)" controls class="w-full max-h-80 object-contain"></video>
      </div>

      <!-- نمایش صوت -->
      <div v-else-if="post.media_type === 'audio' && post.media_file" class="bg-indigo-50/40 border border-indigo-50 p-3 rounded-2xl flex items-center justify-between shadow-inner">
        <audio :src="getImageUrl(post.media_file)" controls class="w-full h-10 outline-none text-indigo-600"></audio>
      </div>

      <!-- متن پست با پشتیبانی از لاین برک و فرمت ساده -->
      <div class="text-gray-700 text-sm leading-relaxed whitespace-pre-line text-right px-1" v-html="formatMarkdown(post.content)"></div>
    </div>

    <!-- فوتر پست (بخش واکنش‌ها و نظرات) -->
    <div class="flex items-center justify-between border-t border-gray-50 pt-3 mt-1">
      <!-- دکمه نظرات -->
      <button
        @click="toggleComments"
        :class="commentsOpen ? 'text-indigo-600 bg-indigo-50/55' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'"
        class="flex items-center space-x-2 space-x-reverse px-3 py-1.5 rounded-xl transition-all text-xs font-extrabold active:scale-95"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <span>{{ post.comments_count || 0 }} نظر</span>
      </button>

      <!-- واکنش‌ها -->
      <div class="flex items-center space-x-1.5 space-x-reverse">
        <button
          v-for="emoji in reactionEmojis"
          :key="emoji"
          @click="$emit('react', { postId: post.id, emoji })"
          :class="post.user_reaction === emoji ? 'bg-indigo-100 text-indigo-800 scale-105 border-indigo-300 ring-2 ring-indigo-500/25' : 'bg-gray-50 text-gray-500 hover:bg-gray-100 border-gray-100'"
          class="flex items-center space-x-1 space-x-reverse px-2.5 py-1.5 rounded-xl border text-xs font-black transition-all active:scale-90"
        >
          <span class="text-sm leading-none">{{ emoji }}</span>
          <span v-if="post.reactions_summary[emoji]" class="text-[10px] leading-none">{{ post.reactions_summary[emoji] }}</span>
        </button>
      </div>
    </div>

    <!-- کشوی نظرات (Comments Panel) -->
    <Transition name="fade-comments">
      <div v-if="commentsOpen" class="border-t border-gray-50 pt-4 mt-2 space-y-4 text-right">
        <h4 class="text-xs font-black text-indigo-700 px-1">💬 نظرات کاربران</h4>

        <!-- لیست کامنت‌ها -->
        <div v-if="loadingComments" class="text-center text-xs text-gray-400 py-3">در حال بارگذاری نظرات...</div>
        <div v-else-if="comments.length === 0" class="text-center text-xs text-gray-400 py-5 bg-gray-50/50 rounded-2xl">
          هنوز نظری ثبت نشده است. اولین نظر را شما بنویسید!
        </div>
        <div v-else class="space-y-3 max-h-60 overflow-y-auto pl-1">
          <div
            v-for="comment in comments"
            :key="comment.id"
            class="bg-gray-50/70 p-3 rounded-2xl border border-gray-100 space-y-1 w-fit max-w-[90%] mr-auto"
          >
            <div class="flex items-center space-x-2 space-x-reverse justify-end text-[10px]">
              <span class="text-gray-400">{{ formatTime(comment.created_at) }}</span>
              <span class="font-extrabold text-indigo-800">{{ comment.user_name }}</span>
            </div>
            <p class="text-xs text-gray-700 leading-relaxed">{{ comment.content }}</p>
          </div>
        </div>

        <!-- اینپوت ارسال کامنت -->
        <div class="flex items-center space-x-2 space-x-reverse pt-2">
          <input
            v-model="commentText"
            type="text"
            placeholder="نظر خود را بنویسید..."
            @keydown.enter="submitComment"
            class="flex-1 bg-gray-50 text-right px-4 py-2.5 rounded-xl border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          />
          <button
            @click="submitComment"
            :disabled="!commentText.trim() || submittingComment"
            class="w-9 h-9 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-100 disabled:text-gray-400 text-white rounded-xl flex items-center justify-center shrink-0 shadow transition-all active:scale-95"
          >
            <span v-if="submittingComment" class="animate-spin text-xs">🌀</span>
            <svg v-else class="w-4 h-4 rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </div>
      </div>
    </Transition>

    <!-- لایت‌باکس تصویر (Full Image Overlay) -->
    <Teleport to="body">
      <div v-if="lightboxOpen" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center" @click="lightboxOpen = false">
        <button class="absolute top-6 right-6 text-white/75 hover:text-white p-2">
          <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <img :src="getImageUrl(post.media_file)" class="max-w-[95%] max-h-[85vh] rounded-2xl shadow-2xl object-contain animate-zoom-in" />
      </div>
    </Teleport>

    <!-- مودال ورود سریع شناور برای مهمان -->
    <QuickLoginModal
      v-if="showQuickLogin"
      @close="showQuickLogin = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { fetchComments, createComment } from '../../api'
import { useAuth } from '../../composables/useAuth'
import { useToast } from '../../composables/useToast'
import QuickLoginModal from '../auth/QuickLoginModal.vue'

const showQuickLogin = ref(false)

const props = defineProps({
  post: { type: Object, required: true },
  currentUserId: { type: [Number, String], default: null }
})

const emit = defineEmits(['delete', 'react', 'refresh'])

const { hasToken } = useAuth()
const { showToast } = useToast()

const reactionEmojis = ["👍", "👎", "❤️", "😂", "🎉"]

const commentsOpen = ref(false)
const loadingComments = ref(false)
const comments = ref([])
const commentText = ref('')
const submittingComment = ref(false)

const lightboxOpen = ref(false)

const isAuthor = computed(() => {
  if (!props.currentUserId || !props.post) return false
  return props.post.author === props.currentUserId || props.post.author_phone === props.currentUserId
})

const getImageUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  if (apiBase === '/') {
    return url
  }
  const base = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase
  const path = url.startsWith('/') ? url : '/' + url
  return `${base}${path}`
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleDateString('fa-IR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// پارسر ساده مارک‌داون جهت استایل‌دهی به بولد، ایتالیک و کد
const formatMarkdown = (text) => {
  if (!text) return ''
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="bg-gray-100 text-red-500 px-1.5 py-0.5 rounded font-mono text-xs">$1</code>')
  return html
}

const toggleComments = () => {
  commentsOpen.value = !commentsOpen.value
  if (commentsOpen.value && comments.value.length === 0) {
    loadComments()
  }
}

const loadComments = async () => {
  loadingComments.value = true
  try {
    const res = await fetchComments(props.post.id)
    comments.value = res.data ?? []
  } catch (err) {
    //
  } finally {
    loadingComments.value = false
  }
}

const submitComment = async () => {
  if (!hasToken()) {
    showQuickLogin.value = true
    return
  }

  const content = commentText.value.trim()
  if (!content) return

  submittingComment.value = true
  try {
    const res = await createComment(props.post.id, content)
    comments.value.push(res.data)
    commentText.value = ''
    emit('refresh') // برای بروزرسانی شمارنده کامنت در فوتر پست
  } catch (err) {
    showToast('خطا در ارسال نظر', 'error')
  } finally {
    submittingComment.value = false
  }
}
</script>

<style scoped>
.animate-zoom-in {
  animation: zoomIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.fade-comments-enter-active,
.fade-comments-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  max-height: 400px;
  opacity: 1;
}

.fade-comments-enter-from,
.fade-comments-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

@keyframes zoomIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
