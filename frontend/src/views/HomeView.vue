<template>
  <div class="px-4 py-4">

    <!-- سرچ‌بار برای فیلتر تاپیک‌ها -->
    <div class="relative mb-6">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="جستجوی تاپیک‌ها..."
        class="w-full bg-white text-right px-4 py-3 pr-10 rounded-2xl border border-gray-100 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm transition-all"
      />
      <span class="absolute right-3 top-3.5 text-gray-400">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </span>
    </div>

    <!-- دسته‌بندی تاپیک‌ها به صورت دو چیپس کنار هم (فقط در حالت لاگین) -->
    <div v-if="hasToken() && !loading && currentUser" class="flex justify-center items-center gap-3 mb-6">
      <button
        @click="filterTab = 'others'"
        :class="filterTab === 'others' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-100 scale-105 border-indigo-600' : 'bg-white text-gray-500 border-gray-150 hover:text-gray-700 hover:bg-gray-50'"
        class="flex-1 max-w-[160px] py-2.5 px-4 rounded-2xl border text-xs font-black transition-all duration-300 active:scale-95 flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        <span>تاپیک‌های دیگران</span>
      </button>

      <button
        @click="filterTab = 'mine'"
        :class="filterTab === 'mine' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-100 scale-105 border-indigo-600' : 'bg-white text-gray-500 border-gray-150 hover:text-gray-700 hover:bg-gray-50'"
        class="flex-1 max-w-[160px] py-2.5 px-4 rounded-2xl border text-xs font-black transition-all duration-300 active:scale-95 flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span>تاپیک‌های من</span>
      </button>
    </div>

    <!-- انیمیشن لودینگ یا لودینگ‌های استخوان‌بندی‌شده -->
    <Transition name="fade" mode="out-in">
      <div v-if="loading" class="space-y-4">
        <div v-for="i in 3" :key="i" class="bg-white rounded-3xl p-5 border border-gray-50 shadow-sm animate-pulse flex items-center justify-between">
          <div class="flex items-center space-x-4 space-x-reverse text-right">
            <div class="w-14 h-14 bg-gray-200 rounded-2xl"></div>
            <div class="space-y-2">
              <div class="h-4 bg-gray-200 rounded w-24"></div>
              <div class="h-3 bg-gray-150 rounded w-48"></div>
            </div>
          </div>
          <div class="w-8 h-8 bg-gray-100 rounded-full"></div>
        </div>
      </div>

      <!-- اگر هیچ تاپیکی وجود نداشت -->
      <div v-else-if="filteredTopics.length === 0" class="text-center py-20 text-gray-400">
        <div class="w-20 h-20 bg-indigo-50 text-indigo-500 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce">
          <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <p class="text-lg font-bold text-gray-600">هنوز تاپیکی ساخته نشده است!</p>
        <p class="text-xs text-gray-400 mt-2">روی دکمهٔ + کلیک کنید و اولین تاپیک را بسازید</p>
      </div>

      <!-- کارت‌های تاپیک‌ها -->
      <div v-else class="space-y-4">
        <div
          v-for="topic in filteredTopics"
          :key="topic.id"
          @click="viewTopic(topic.id)"
          class="bg-white rounded-3xl p-4 border border-gray-50 shadow-sm hover:shadow-md active:scale-[0.98] transition-all duration-300 cursor-pointer flex items-center justify-between hover:border-indigo-100 group relative overflow-hidden"
        >
          <!-- بک‌گراند هاور افکت شیک -->
          <div class="absolute inset-0 bg-gradient-to-l from-indigo-50/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

          <div class="flex items-center space-x-4 space-x-reverse text-right z-10 w-full pr-2">
            <!-- تصویر یا آواتار تاپیک -->
            <div class="relative shrink-0">
              <img
                v-if="topic.image"
                :src="getImageUrl(topic.image)"
                alt="Topic cover"
                class="w-14 h-14 rounded-2xl object-cover border border-gray-100 shadow-inner"
              />
              <div
                v-else
                class="w-14 h-14 bg-gradient-to-tr from-indigo-500 to-indigo-700 text-white rounded-2xl flex items-center justify-center font-bold text-lg shadow-md"
              >
                {{ topic.name.charAt(0) }}
              </div>
              <!-- بج تعداد پست‌ها -->
              <span class="absolute -top-1.5 -right-1.5 px-1.5 py-0.5 bg-rose-500 text-white text-[10px] font-black rounded-full shadow">
                {{ topic.post_count || 0 }}
              </span>
            </div>

            <!-- مشخصات و توصیحات تاپیک -->
            <div class="space-y-1 overflow-hidden w-full pr-1">
              <div class="flex items-center space-x-2 space-x-reverse">
                <h3 class="font-extrabold text-gray-800 text-base group-hover:text-indigo-600 transition-colors">
                  {{ topic.name }}
                </h3>
                <span v-if="topic.telegram_bot_active || topic.bale_bot_active" class="flex space-x-1 shrink-0">
                  <span v-if="topic.telegram_bot_active" title="تلگرام فعال" class="text-xs">🔹</span>
                  <span v-if="topic.bale_bot_active" title="بله فعال" class="text-xs">🟢</span>
                </span>
              </div>
              <p class="text-xs text-gray-400 truncate w-11/12 leading-relaxed">
                {{ topic.description || 'هنوز پستی در این تاپیک ارسال نشده است.' }}
              </p>
            </div>
          </div>

          <!-- دکمه فلش شیک -->
          <div class="w-9 h-9 bg-gray-50 text-gray-400 group-hover:bg-indigo-600 group-hover:text-white rounded-full flex items-center justify-center shrink-0 transition-all z-10 shadow-sm active:scale-90">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
            </svg>
          </div>
        </div>
      </div>
    </Transition>

    <!-- FAB دکمه شناور ایجاد تاپیک جدید -->
    <button
      v-if="hasToken()"
      @click="handleCreateTopicClick"
      class="fixed bottom-24 right-6 w-14 h-14 bg-indigo-600 mb-2 text-white rounded-2xl shadow-xl flex items-center justify-center active:scale-90 active:rotate-90 hover:scale-105 transition-all duration-300 z-40 hover:bg-indigo-700"
    >
      <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
      </svg>
    </button>

    <!-- مدال ساخت تاپیک جدید -->
    <TopicModal
      v-if="modalOpen"
      @close="modalOpen = false"
      @saved="onTopicSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchTopics, fetchProfile } from '../api'
import { useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'
import TopicModal from '../components/notes/TopicModal.vue'

const router = useRouter()
const { hasToken } = useAuth()
const { showToast } = useToast()

const topics = ref([])
const loading = ref(true)
const searchQuery = ref('')
const modalOpen = ref(false)
const currentUser = ref(null)
const filterTab = ref('others')

const loadTopics = async () => {
  loading.value = true
  try {
    const res = await fetchTopics()
    topics.value = res.data ?? []
  } catch (err) {
    // خطا توسط اینترسپتور مدیریت می‌شود
  } finally {
    loading.value = false
  }
}

const filteredTopics = computed(() => {
  let list = topics.value

  if (hasToken() && currentUser.value) {
    if (filterTab.value === 'mine') {
      list = list.filter(t => t.created_by === currentUser.value.id)
    } else if (filterTab.value === 'others') {
      list = list.filter(t => t.created_by !== currentUser.value.id)
    }
  }

  if (!searchQuery.value.trim()) return list
  const query = searchQuery.value.toLowerCase()
  return list.filter(t => t.name.toLowerCase().includes(query) || (t.description && t.description.toLowerCase().includes(query)))
})

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

const viewTopic = (id) => {
  router.push({ name: 'topic', params: { id } })
}

const handleCreateTopicClick = () => {
  if (!hasToken()) {
    showToast('برای ایجاد تاپیک جدید، لطفا ابتدا وارد حساب کاربری خود شوید.', 'error')
    router.push({ name: 'login' })
    return
  }
  modalOpen.value = true
}

const onTopicSaved = () => {
  modalOpen.value = false
  loadTopics()
}

onMounted(async () => {
  loadTopics()
  if (hasToken()) {
    try {
      const res = await fetchProfile()
      currentUser.value = res.data
    } catch (err) {
      // خطا توسط اینترسپتور مدیریت می‌شود
    }
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>