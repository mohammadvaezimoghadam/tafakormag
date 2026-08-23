<template>
  <div class="max-w-5xl mx-auto px-4 py-8 space-y-6" :dir="languageStore.dir">
    
    <!-- Top Hero Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-emerald-600 to-teal-700 p-6 sm:p-8 rounded-3xl text-white shadow-xl">
      <div class="space-y-1.5">
        <div class="inline-flex items-center gap-2 px-3 py-1 bg-white/15 backdrop-blur-md rounded-full text-xs font-semibold">
          <span>📖</span>
          <span>{{ languageStore.t('افزونه رسمی قرآن کریم', 'Official Quran Plugin') }}</span>
        </div>
        <h1 class="text-2xl sm:text-4xl font-black font-serif">
          {{ languageStore.t('قرآن کریم', 'Holy Quran') }}
        </h1>
        <p class="text-xs sm:text-sm text-emerald-100 max-w-lg">
          {{ languageStore.t('مطالعه، تلاوت صوتی، جستجوی دقیق آیات و درج ارجاعات قرآنی در یادداشت‌ها', 'Read, listen to recitations, search verses, and insert citations into notes') }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <router-link
          to="/apps/quran/search"
          class="px-4 py-2.5 bg-white text-emerald-800 hover:bg-emerald-50 rounded-2xl text-xs font-bold shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
        >
          <span>🔍</span>
          <span>{{ languageStore.t('جستجوی آیات', 'Search Quran') }}</span>
        </router-link>
      </div>
    </div>

    <!-- Continue Reading Banner (Last Read) -->
    <div
      v-if="reader.lastRead.value"
      class="p-4 bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-500/30 rounded-2xl flex items-center justify-between gap-3 shadow-xs"
    >
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-sm">
          📑
        </div>
        <div>
          <span class="text-[11px] font-semibold text-emerald-800 dark:text-emerald-300 block">
            {{ languageStore.t('آخرین موقعیت مطالعه شما', 'Continue Reading') }}
          </span>
          <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
            سوره {{ reader.lastRead.value.surahName }} • آیه {{ reader.lastRead.value.ayahNumber }}
          </span>
        </div>
      </div>

      <router-link
        :to="`/apps/quran/surahs/${reader.lastRead.value.surahNumber}#ayah-${reader.lastRead.value.ayahNumber}`"
        class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs"
      >
        {{ languageStore.t('ادامه مطالعه', 'Resume') }}
      </router-link>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex items-center gap-2 p-1.5 bg-zinc-100 dark:bg-zinc-800/60 rounded-2xl">
      <button
        @click="activeTab = 'surahs'"
        type="button"
        :class="[
          'flex-1 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer',
          activeTab === 'surahs'
            ? 'bg-white dark:bg-zinc-900 text-emerald-600 dark:text-emerald-400 shadow-xs'
            : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
        ]"
      >
        <span>📑</span>
        <span>{{ languageStore.t('۱۱۴ سوره قرآن', '114 Surahs') }}</span>
      </button>

      <button
        @click="activeTab = 'juzs'"
        type="button"
        :class="[
          'flex-1 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer',
          activeTab === 'juzs'
            ? 'bg-white dark:bg-zinc-900 text-emerald-600 dark:text-emerald-400 shadow-xs'
            : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
        ]"
      >
        <span>📚</span>
        <span>{{ languageStore.t('۳۰ جزء', '30 Juzs') }}</span>
      </button>

      <button
        @click="activeTab = 'bookmarks'"
        type="button"
        :class="[
          'flex-1 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer',
          activeTab === 'bookmarks'
            ? 'bg-white dark:bg-zinc-900 text-emerald-600 dark:text-emerald-400 shadow-xs'
            : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
        ]"
      >
        <span>★</span>
        <span>{{ languageStore.t('نشان‌شده‌ها', 'Bookmarks') }} ({{ reader.bookmarks.value.length }})</span>
      </button>
    </div>

    <!-- TAB 1: SURAHS -->
    <div v-if="activeTab === 'surahs'" class="space-y-4">
      <!-- Search Input -->
      <div class="relative">
        <input
          type="text"
          v-model="surahSearchQuery"
          :placeholder="languageStore.t('جستجوی سوره (نام، شماره، ترجمه انگلیسی)...', 'Search Surahs...')"
          class="w-full px-5 py-3.5 pr-11 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl text-xs sm:text-sm text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 shadow-xs"
        />
        <span class="absolute right-4 top-3.5 text-zinc-400 text-sm">🔍</span>
      </div>

      <div v-if="loadingSurahs" class="text-center py-16 text-xs text-zinc-400">
        {{ languageStore.t('در حال بارگذاری فهرست سوره‌ها...', 'Loading Surahs...') }}
      </div>

      <div v-else-if="filteredSurahs.length === 0" class="text-center py-16 text-xs text-zinc-400">
        {{ languageStore.t('سوره‌ای با این مشخصات یافت نشد.', 'No surahs found.') }}
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        <router-link
          v-for="s in filteredSurahs"
          :key="s.number"
          :to="`/apps/quran/surahs/${s.number}`"
          class="group p-4 bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800/80 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 rounded-3xl shadow-xs hover:shadow-md transition-all duration-200 flex items-center justify-between"
        >
          <div class="flex items-center gap-3.5">
            <div class="w-10 h-10 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-bold text-xs flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition-colors">
              {{ s.number }}
            </div>
            <div>
              <h3 class="font-bold text-zinc-900 dark:text-zinc-100 text-sm group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                {{ s.name }}
              </h3>
              <p class="text-[11px] text-zinc-400 mt-0.5">
                {{ s.english_name_translation || s.english_name }}
              </p>
            </div>
          </div>

          <div class="text-left space-y-0.5">
            <span class="inline-block px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded-lg text-[10px] font-medium">
              {{ s.ayah_count }} {{ languageStore.t('آیه', 'Ayahs') }}
            </span>
            <p class="text-[10px] text-zinc-400 text-center">
              {{ s.revelation_type === 'Meccan' ? languageStore.t('مکی', 'Meccan') : languageStore.t('مدنی', 'Medinan') }}
            </p>
          </div>
        </router-link>
      </div>
    </div>

    <!-- TAB 2: JUZS -->
    <div v-else-if="activeTab === 'juzs'" class="space-y-4">
      <div v-if="loadingJuzs" class="text-center py-16 text-xs text-zinc-400">
        {{ languageStore.t('در حال بارگذاری اجزاء...', 'Loading Juzs...') }}
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        <router-link
          v-for="j in juzs"
          :key="j.number"
          :to="`/apps/quran/juz/${j.number}`"
          class="p-4 bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800/80 hover:border-emerald-500/50 rounded-3xl space-y-2 shadow-xs hover:shadow-md transition-all"
        >
          <div class="flex items-center justify-between">
            <div class="w-9 h-9 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 font-bold text-xs flex items-center justify-center">
              {{ j.number }}
            </div>
            <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              {{ languageStore.t(`جزء ${j.number}`, `Juz ${j.number}`) }}
            </span>
          </div>

          <div>
            <h3 class="font-bold text-zinc-900 dark:text-zinc-100 text-sm">
              {{ j.name || `جزء ${j.number}` }}
            </h3>
            <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              از سوره {{ j.start_surah_name || j.start_surah }} (آیه {{ j.start_ayah }}) تا سوره {{ j.end_surah_name || j.end_surah }} (آیه {{ j.end_ayah }})
            </p>
          </div>
        </router-link>
      </div>
    </div>

    <!-- TAB 3: BOOKMARKS -->
    <div v-else-if="activeTab === 'bookmarks'" class="space-y-4">
      <div v-if="reader.bookmarks.value.length === 0" class="text-center py-16 text-xs text-zinc-400">
        {{ languageStore.t('هنوز آیه‌ای را نشان نکرده‌اید.', 'No bookmarks yet.') }}
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="bm in reader.bookmarks.value"
          :key="bm.id"
          class="p-4 bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800/80 rounded-3xl flex items-center justify-between gap-3 shadow-xs"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-bold text-xs text-emerald-600 dark:text-emerald-400">
                سوره {{ bm.surahName }} • آیه {{ bm.ayahNumber }}
              </span>
            </div>
            <p class="text-xs font-serif text-zinc-700 dark:text-zinc-300 truncate mt-1">
              {{ bm.textPreview }}
            </p>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <router-link
              :to="`/apps/quran/surahs/${bm.surahNumber}#ayah-${bm.ayahNumber}`"
              class="px-3 py-1.5 bg-emerald-600 text-white rounded-xl text-xs font-bold"
            >
              {{ languageStore.t('مشاهده', 'View') }}
            </router-link>
            <button
              @click="reader.removeBookmark(bm.id)"
              type="button"
              class="w-7 h-7 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 hover:text-red-500 flex items-center justify-center text-xs"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { quranApi } from '../api'
import { useQuranReader } from '../composables/useQuranReader'
import type { QuranSurah, QuranJuz } from '../types'

const languageStore = useLanguageStore()
const reader = useQuranReader()

const activeTab = ref<'surahs' | 'juzs' | 'bookmarks'>('surahs')
const surahs = ref<QuranSurah[]>([])
const juzs = ref<QuranJuz[]>([])
const surahSearchQuery = ref('')
const loadingSurahs = ref(false)
const loadingJuzs = ref(false)

onMounted(async () => {
  loadingSurahs.value = true
  try {
    surahs.value = await quranApi.getSurahs()
  } catch (err) {
    console.error('Failed to load surahs:', err)
  } finally {
    loadingSurahs.value = false
  }

  loadingJuzs.value = true
  try {
    juzs.value = await quranApi.getJuzs()
  } catch (err) {
    console.error('Failed to load juzs:', err)
  } finally {
    loadingJuzs.value = false
  }
})

const filteredSurahs = computed(() => {
  if (!surahSearchQuery.value.trim()) return surahs.value
  const q = surahSearchQuery.value.trim().toLowerCase()
  return surahs.value.filter(s =>
    s.name.toLowerCase().includes(q) ||
    s.english_name.toLowerCase().includes(q) ||
    s.english_name_translation.toLowerCase().includes(q) ||
    String(s.number) === q
  )
})
</script>
