<template>
  <div class="flex flex-col min-h-[calc(100vh-3.5rem)] pb-20 relative">
    <!-- هدر تاپیک -->
    <div v-if="topic" class="bg-white/80 backdrop-blur border-b border-gray-100 px-4 py-3 sticky top-14 z-30 flex items-center justify-between shadow-sm">
      <!-- دکمه بازگشت (در راست برای فارسی/RTL) -->
      <button @click="router.push('/')" class="w-9 h-9 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-xl flex items-center justify-center transition-colors shrink-0">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
        </svg>
      </button>

      <!-- نام و مشخصات تاپیک در وسط هدر (تراز به راست/RTL) -->
      <div class="flex items-center space-x-3 space-x-reverse text-right overflow-hidden flex-1 justify-start px-3">
        <img
          v-if="topic.image"
          :src="getImageUrl(topic.image)"
          class="w-10 h-10 rounded-xl object-cover border border-gray-150 shadow-sm shrink-0"
        />
        <div
          v-else
          class="w-10 h-10 bg-gradient-to-tr from-indigo-500 to-indigo-700 text-white rounded-xl flex items-center justify-center font-bold text-sm shrink-0"
        >
          {{ topic.name.charAt(0) }}
        </div>
        <div class="overflow-hidden">
          <h2 class="font-black text-gray-800 text-sm truncate">{{ topic.name }}</h2>
          <p class="text-[10px] text-gray-400 truncate mt-0.5">{{ topic.description || 'بدون توضیحات' }}</p>
        </div>
      </div>

      <!-- تنظیمات تاپیک به سبک تلگرام (سه نقطه عمودی در چپ/RTL) -->
      <div class="relative flex items-center shrink-0">
        <template v-if="isCreator">
          <button
            @click="menuOpen = !menuOpen"
            class="w-9 h-9 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-xl flex items-center justify-center transition-all duration-200"
            title="تنظیمات تاپیک"
          >
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </button>

          <!-- منوی کشویی شناور -->
          <div v-if="menuOpen" class="absolute left-0 top-11 w-48 bg-white/95 backdrop-blur-md rounded-2xl border border-gray-150 shadow-xl py-2 z-50 animate-zoom-in text-right">
            <!-- لایه کلیک برای بستن منو با کلیک در بیرون -->
            <div class="fixed inset-0 z-[-1] bg-transparent" @click="menuOpen = false"></div>

            <button
              @click="openSettings"
              class="w-full px-4 py-2.5 hover:bg-indigo-50/50 text-gray-700 text-xs font-black flex items-center justify-between transition-colors"
            >
              <span>اتصالات پیام‌رسان</span>
              <svg class="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
            </button>

            <button
              @click="openEdit"
              class="w-full px-4 py-2.5 hover:bg-indigo-50/50 text-gray-700 text-xs font-black flex items-center justify-between transition-colors"
            >
              <span>ویرایش تاپیک</span>
              <svg class="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>

            <div class="border-t border-gray-100 my-1.5"></div>

            <button
              @click="deleteTopicClick"
              class="w-full px-4 py-2.5 hover:bg-red-50 text-red-600 text-xs font-black flex items-center justify-between transition-colors"
            >
              <span>حذف تاپیک</span>
              <svg class="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- فید پست‌ها -->
    <div class="flex-1 px-4 py-4 space-y-6">
      <div v-if="loadingPosts" class="space-y-4">
        <div v-for="i in 2" :key="i" class="bg-white rounded-3xl p-5 border border-gray-50 shadow-sm animate-pulse space-y-3">
          <div class="flex items-center space-x-3 space-x-reverse justify-end">
            <div class="h-3 bg-gray-200 rounded w-16"></div>
            <div class="w-8 h-8 bg-gray-200 rounded-full"></div>
          </div>
          <div class="h-4 bg-gray-200 rounded w-3/4 mr-auto"></div>
          <div class="h-3 bg-gray-150 rounded w-full"></div>
        </div>
      </div>

      <div v-else-if="posts.length === 0" class="text-center py-24 text-gray-400">
        <div class="w-16 h-16 bg-gray-50 text-gray-300 rounded-full flex items-center justify-center mx-auto mb-3">
          <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <p class="text-sm font-bold text-gray-500">هنوز پستی در این تاپیک ارسال نشده است.</p>
        <p class="text-xs text-gray-400 mt-1">اولین پست را از انتهای صفحه ارسال کنید.</p>
      </div>

      <div v-else class="space-y-6">
        <!-- کامپوننت PostCard -->
        <PostCard
          v-for="post in posts"
          :key="post.id"
          :post="post"
          :current-user-id="currentUserId"
          @delete="handleDeletePost"
          @react="handleReact"
          @refresh="loadPosts"
        />
      </div>
    </div>

    <!-- باکس متنی ثابت در پایین صفحه برای ارسال پست -->
    <div v-if="isCreator" class="fixed bottom-0 left-0 right-0 max-w-md w-full mx-auto bg-white/95 backdrop-blur-md border-t border-gray-150 p-3 flex items-center space-x-2 space-x-reverse z-40">
      <!-- دکمه الصاق رسانه -->
      <div class="relative shrink-0">
        <button
          @click="triggerMediaSelect"
          :class="selectedFile ? 'bg-emerald-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
          class="w-10 h-10 rounded-xl flex items-center justify-center transition-all shadow-sm"
          title="افزودن عکس/فیلم/صدا"
        >
          <svg v-if="!selectedFile" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
        </button>
        <!-- فیلتر فایل مخفی -->
        <input type="file" ref="mediaInput" @change="handleFileChange" accept="image/*,video/*,audio/*" class="hidden" />
      </div>

      <!-- اینپوت متنی اصلی -->
      <div class="flex-1 relative">
        <!-- دکمه بهبود با هوش مصنوعی (شناور) -->
        <button
          v-if="showAiButton"
          @click="showAiToast"
          type="button"
          class="absolute -top-9 left-1 z-10 flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-full text-[10px] font-extrabold shadow-md hover:scale-105 active:scale-95 transition-all animate-fade-in cursor-pointer"
        >
          <span class="text-[12px] animate-pulse">⭐</span>
          <span>بهبود با هوش مصنوعی</span>
          <span class="bg-black/20 text-white text-[8px] px-1.5 py-0.5 rounded-full font-black">به زودی</span>
        </button>
        <textarea
          ref="textareaRef"
          v-model="postContent"
          rows="1"
          placeholder="تفکر خود را ارسال کنید..."
          @keydown.enter.exact.prevent="sendNewPost"
          @input="adjustTextareaHeight"
          class="w-full min-h-[40px] max-h-[120px] bg-gray-50 text-right px-4 py-[11px] leading-tight rounded-xl border border-gray-250 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white resize-none transition-all"
        ></textarea>
        <!-- پیش نمایش نام فایل انتخابی -->
        <span v-if="selectedFile" class="absolute -top-6 right-2 text-[9px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-100 font-bold flex items-center gap-1.5 max-w-[180px] sm:max-w-[240px]">
          <span class="truncate">📁 {{ selectedFile.name }}</span>
          <button @click="clearSelectedFile" class="text-emerald-900 hover:text-red-500 font-extrabold focus:outline-none transition-colors" title="حذف فایل">✕</button>
        </span>
      </div>

      <!-- دکمه ارسال پیام -->
      <button
        @click="sendNewPost"
        :disabled="sendingPost || (!postContent.trim() && !selectedFile)"
        class="w-10 h-10 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-100 disabled:text-gray-400 text-white rounded-xl flex items-center justify-center shrink-0 shadow-md active:scale-90 transition-all font-bold"
      >
        <span v-if="sendingPost" class="animate-spin text-xs">🌀</span>
        <svg v-else class="w-5 h-5 -scale-x-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>

    <!-- نوار وضعیت قفل بودن برای سایر کاربران -->
    <div v-else class="fixed bottom-0 left-0 right-0 max-w-md w-full mx-auto bg-gray-50/95 backdrop-blur-md border-t border-gray-150 p-4 text-center z-40">
      <span class="text-xs font-black text-gray-400">🔒 فقط سازنده تاپیک مجاز به ارسال پیام در آن است.</span>
    </div>

    <!-- تنظیمات اتصالات تاپیک -->
    <TopicSettingsModal
      v-if="settingsOpen && topic"
      :topic="topic"
      @close="settingsOpen = false"
      @updated="onTopicUpdated"
    />

    <!-- ویرایش مشخصات تاپیک -->
    <TopicModal
      v-if="editOpen && topic"
      :topic="topic"
      @close="editOpen = false"
      @saved="onTopicUpdated"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchTopics, deleteTopic, fetchPosts, createPost, deletePost, reactToPost, fetchProfile } from '../api'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'
import PostCard from '../components/notes/PostCard.vue'
import TopicSettingsModal from '../components/notes/TopicSettingsModal.vue'
import TopicModal from '../components/notes/TopicModal.vue'


const route = useRoute()
const router = useRouter()
const { hasToken, getToken, showGlobalLoginModal } = useAuth()
const { showToast } = useToast()

const topicId = route.params.id
const topic = ref(null)
const posts = ref([])

const loadingPosts = ref(true)
const sendingPost = ref(false)
const postContent = ref('')

const showAiButton = computed(() => {
  if (!postContent.value) return false
  const lines = postContent.value.split('\n')
  if (lines.length > 3) return true
  if (postContent.value.length > 150) return true
  return false
})

const showAiToast = () => {
  showToast('این قابلیت (بهبود متن با هوش مصنوعی) در حال توسعه است و به زودی اضافه می‌شود.', 'info')
}

const mediaInput = ref(null)
const selectedFile = ref(null)
const mediaType = ref('text')

const settingsOpen = ref(false)
const editOpen = ref(false)

const textareaRef = ref(null)

const adjustTextareaHeight = () => {
  if (!textareaRef.value) return
  textareaRef.value.style.height = 'auto'
  textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 120)}px`
}
const menuOpen = ref(false)


const openSettings = () => {
  menuOpen.value = false
  settingsOpen.value = true
}

const openEdit = () => {
  menuOpen.value = false
  editOpen.value = true
}

const deleteTopicClick = () => {
  menuOpen.value = false
  confirmDeleteTopic()
}

const currentUser = ref(null)
const currentUserId = computed(() => currentUser.value?.id || currentUser.value?.phone || null)

const getImageUrl = (url) => {
  if (!url) return ''
  const mediaIdx = url.indexOf('/media/')
  if (mediaIdx !== -1) {
    url = url.slice(mediaIdx)
  }
  const staticIdx = url.indexOf('/static/')
  if (staticIdx !== -1) {
    url = url.slice(staticIdx)
  }
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  if (url.startsWith('//')) {
    url = url.slice(1)
  }
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  if (apiBase === '/') {
    return url
  }
  const base = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase
  const path = url.startsWith('/') ? url : '/' + url
  return `${base}${path}`
}

// چک کردن اینکه آیا کاربر لاگین شده سازنده تاپیک است
const isCreator = computed(() => {
  if (!hasToken() || !topic.value) return false
  if (!topic.value.created_by) return true
  if (!currentUser.value) return false
  return String(topic.value.created_by) === String(currentUser.value.id) ||
         (topic.value.created_by_phone && currentUser.value.phone && String(topic.value.created_by_phone) === String(currentUser.value.phone))
})

const loadTopicData = async () => {
  try {
    const res = await fetchTopics()
    const allTopics = res.data ?? []
    topic.value = allTopics.find(t => t.id === parseInt(topicId))
    if (!topic.value) {
      showToast('تاپیک یافت نشد', 'error')
      router.push('/')
    }
  } catch (err) {
    //
  }
}

const loadPosts = async () => {
  loadingPosts.value = true
  try {
    const res = await fetchPosts(topicId)
    posts.value = res.data ?? []
  } catch (err) {
    //
  } finally {
    loadingPosts.value = false
  }
}

const fetchCurrentUserProfile = async () => {
  if (!hasToken()) return
  try {
    const res = await fetchProfile()
    currentUser.value = res.data
  } catch (err) {
    //
  }
}

const triggerMediaSelect = () => {
  mediaInput.value.click()
}

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  selectedFile.value = file
  
  if (file.type.startsWith('image/')) {
    mediaType.value = 'image'
  } else if (file.type.startsWith('video/')) {
    mediaType.value = 'video'
  } else if (file.type.startsWith('audio/')) {
    mediaType.value = 'audio'
  } else {
    mediaType.value = 'text'
  }
}

const clearSelectedFile = () => {
  selectedFile.value = null
  mediaType.value = 'text'
  if (mediaInput.value) {
    mediaInput.value.value = ''
  }
}

const sendNewPost = async () => {
  if (!hasToken()) {
    showGlobalLoginModal.value = true
    return
  }

  const content = postContent.value.trim()
  if (!content && !selectedFile.value) {
    return
  }

  sendingPost.value = true
  try {
    const formData = new FormData()
    formData.append('topic', topicId)
    formData.append('content', content)
    formData.append('media_type', mediaType.value)
    if (selectedFile.value) {
      formData.append('media_file', selectedFile.value)
    }

    await createPost(formData)
    showToast('پست جدید ارسال و در کانال‌های فعال بازنشر شد', 'success')
    postContent.value = ''
    clearSelectedFile()
    loadPosts()
    loadTopicData() // توضیحات تاپیک را به‌روز کند
    nextTick(() => {
      adjustTextareaHeight()
    })
  } catch (err) {
    showToast('خطا در ارسال پست', 'error')
  } finally {
    sendingPost.value = false
  }
}

const handleDeletePost = async (id) => {
  if (!window.confirm('پست حذف شود؟ (با حذف این پست، پیام‌های مرتبط در پیام‌رسان‌ها نیز حذف خواهند شد)')) return
  try {
    await deletePost(id)
    posts.value = posts.value.filter(p => p.id !== id)
    showToast('پست با موفقیت حذف شد', 'success')
    loadTopicData()
  } catch (err) {
    //
  }
}

const handleReact = async ({ postId, emoji }) => {
  if (!hasToken()) {
    showGlobalLoginModal.value = true
    return
  }
  try {
    await reactToPost(postId, emoji)
    // به‌روزرسانی محلی پست خاص برای افزایش عملکرد و جلوگیری از فلش زدن کل صفحه
    const postIndex = posts.value.findIndex(p => p.id === postId)
    if (postIndex !== -1) {
      const p = posts.value[postIndex]
      const currentReaction = p.user_reaction
      
      // آپدیت خلاصه واکنش‌ها
      const summary = { ...p.reactions_summary }
      if (currentReaction) {
        summary[currentReaction] = Math.max(0, (summary[currentReaction] || 1) - 1)
        if (summary[currentReaction] === 0) delete summary[currentReaction]
      }
      
      if (emoji && currentReaction !== emoji) {
        summary[emoji] = (summary[emoji] || 0) + 1
        p.user_reaction = emoji
      } else {
        p.user_reaction = null
      }
      p.reactions_summary = summary
    }
  } catch (err) {
    //
  }
}

const confirmDeleteTopic = async () => {
  if (!window.confirm('آیا مطمئن هستید که می‌خواهید این تاپیک را به همراه تمام پست‌های آن برای همیشه حذف کنید؟ این عمل غیر قابل بازگشت است.')) return
  try {
    await deleteTopic(topicId)
    showToast('تاپیک با موفقیت حذف شد', 'success')
    router.push('/')
  } catch (err) {
    showToast('خطا در حذف تاپیک', 'error')
  }
}

const onTopicUpdated = () => {
  settingsOpen.value = false
  editOpen.value = false
  loadTopicData()
}

onMounted(() => {
  loadTopicData()
  loadPosts()
  fetchCurrentUserProfile()
  nextTick(() => {
    adjustTextareaHeight()
  })
})
</script>

<style scoped>
/* اسکرول‌بار مخفی و باریک چت تلگرام */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 99px;
}

.animate-fade-in {
  animation: fadeIn 0.25s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
