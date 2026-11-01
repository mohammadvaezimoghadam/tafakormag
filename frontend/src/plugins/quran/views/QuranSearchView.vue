<template>
  <div class="max-w-4xl mx-auto px-4 py-8 pb-32 space-y-6" :dir="languageStore.dir">
    
    <!-- Top Navigation -->
    <div class="flex items-center justify-between">
      <router-link
        to="/apps/quran"
        class="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
      >
        <span>←</span>
        <span>{{ languageStore.t('بازگشت به صفحه اصلی قرآن', 'Back to Quran Home') }}</span>
      </router-link>
    </div>

    <!-- Search Header -->
    <div class="bg-gradient-to-r from-emerald-600 to-teal-700 p-6 sm:p-8 rounded-3xl text-white shadow-xl space-y-2">
      <div class="inline-flex items-center gap-2 px-3 py-1 bg-white/15 backdrop-blur-md rounded-full text-xs font-semibold">
        <span>🔍</span>
        <span>{{ languageStore.t('موتور جستجوی هوشمند قرآن', 'Quran Search Engine') }}</span>
      </div>
      <h1 class="text-2xl sm:text-3xl font-black font-serif">
        {{ languageStore.t('جستجوی متنی در آیات قرآن', 'Full-Text Quran Search') }}
      </h1>
      <p class="text-xs sm:text-sm text-emerald-100">
        {{ languageStore.t('جستجوی دقیق بدون وابستگی به اعراب و با یکسان‌سازی حروف و علائم', 'Normalized search across all Quranic ayahs with diacritic preservation') }}
      </p>
    </div>

    <!-- Search Input & Filters -->
    <div class="space-y-3">
      <div class="relative">
        <input
          type="text"
          v-model="searchQuery"
          @keyup.enter="performSearch"
          :placeholder="languageStore.t('جستجوی کلمه یا عبارت در آیات (مثال: الرحمن، الصبر، تقوا)...', 'Search verses (e.g. mercy, patience)...')"
          class="w-full px-5 py-4 pr-12 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl text-xs sm:text-sm text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 shadow-xs"
        />
        <button
          @click="performSearch"
          type="button"
          class="absolute left-3 top-2.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
        >
          {{ languageStore.t('جستجو', 'Search') }}
        </button>
      </div>

      <div class="flex flex-wrap items-center gap-3 text-xs">
        <select
          v-model="selectedTranslation"
          @change="onFilterChange"
          class="px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-xs text-zinc-700 dark:text-zinc-300"
        >
          <option value="fa.ansarian">همراه با ترجمه انصاریان</option>
          <option value="fa.makarem">همراه با ترجمه مکارم</option>
          <option value="en.sahih">همراه با ترجمه انگلیسی (Sahih)</option>
          <option value="">بدون ترجمه</option>
        </select>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="loading" class="text-center py-20 text-zinc-400 text-xs">
      {{ languageStore.t('در حال جستجو...', 'Searching...') }}
    </div>

    <div v-else-if="hasSearched && searchResults.length === 0" class="text-center py-20 text-zinc-400 text-xs">
      {{ languageStore.t(`هیچ آیه‌ای مطابق با عبارت «${searchQuery}» یافت نشد.`, `No verses found matching "${searchQuery}".`) }}
    </div>

    <div v-else-if="searchResults.length > 0" class="space-y-4">
      <div class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 flex items-center justify-between px-1">
        <span>{{ languageStore.t(`تعداد نتایج یافت‌شده: ${totalMatches} آیه`, `Found ${totalMatches} verses`) }}</span>
      </div>

      <div
        v-for="item in searchResults"
        :key="item.id"
        class="p-6 bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800/80 rounded-3xl space-y-4 shadow-xs hover:border-emerald-500/40 transition-colors"
      >
        <!-- Item Header -->
        <div class="flex items-center justify-between text-xs text-zinc-500">
          <router-link
            :to="`/apps/quran/surahs/${item.surah_number}#ayah-${item.number_in_surah}`"
            class="font-bold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1.5"
          >
            <span>📖</span>
            <span>سوره {{ item.surah_name }} ({{ item.surah_number }}) • آیه {{ item.number_in_surah }}</span>
          </router-link>
          
          <div class="flex items-center gap-2">
            <span class="text-[11px] text-zinc-400">جزء {{ item.juz }}</span>
            <button
              @click="copyResultMarkdown(item)"
              type="button"
              class="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 rounded-lg text-[11px] font-semibold flex items-center gap-1"
            >
              <span>📋</span>
              <span>{{ languageStore.t('کپی', 'Copy') }}</span>
            </button>
          </div>
        </div>

        <!-- Highlighted / Arabic Text -->
        <div class="pt-1">
          <p
            v-if="item.highlighted_text"
            v-html="item.highlighted_text"
            class="text-lg sm:text-xl text-right font-serif leading-loose text-zinc-900 dark:text-zinc-100 select-text [&_mark]:bg-emerald-200 dark:[&_mark]:bg-emerald-900/60 [&_mark]:text-emerald-950 dark:[&_mark]:text-emerald-100 [&_mark]:px-1 [&_mark]:rounded-sm"
          />
          <p
            v-else
            class="text-lg sm:text-xl text-right font-serif leading-loose text-zinc-900 dark:text-zinc-100 select-text"
          >
            {{ item.text }}
          </p>
        </div>

        <!-- Translation -->
        <p
          v-if="item.translation?.text"
          class="text-xs sm:text-sm text-zinc-600 dark:text-zinc-300 leading-relaxed italic border-r-2 border-emerald-500/30 pr-3.5 pt-1"
        >
          {{ item.translation.text }}
        </p>

        <!-- Actions -->
        <div class="pt-2 border-t border-zinc-100 dark:border-zinc-800/60 flex items-center justify-end gap-2">
          <router-link
            :to="`/apps/quran/surahs/${item.surah_number}#ayah-${item.number_in_surah}`"
            class="px-3 py-1.5 bg-emerald-50 dark:bg-emerald-950/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 rounded-xl text-xs font-bold transition-colors"
          >
            {{ languageStore.t('مطالعه در سوره', 'Read in Surah') }} ↗
          </router-link>
        </div>
      </div>
    </div>

    <!-- Sticky Audio Bar -->
    <QuranAudioBar />

  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { quranApi } from '../api'
import QuranAudioBar from '../components/QuranAudioBar.vue'
import type { QuranSearchResult } from '../types'

const languageStore = useLanguageStore()

const searchQuery = ref('')
const selectedTranslation = ref('fa.ansarian')
const searchResults = ref<QuranSearchResult[]>([])
const totalMatches = ref(0)
const loading = ref(false)
const hasSearched = ref(false)

const performSearch = async () => {
  if (!searchQuery.value.trim() || searchQuery.value.trim().length < 2) return
  loading.value = true
  hasSearched.value = true
  try {
    const res = await quranApi.search({
      q: searchQuery.value.trim(),
      edition: 'quran-simple',
      with_translation: selectedTranslation.value || undefined,
      page_size: 50,
    })
    searchResults.value = res.results
    totalMatches.value = res.total_matches
  } catch (err) {
    console.error('Search failed:', err)
  } finally {
    loading.value = false
  }
}

const onFilterChange = () => {
  if (hasSearched.value) {
    performSearch()
  }
}

const copyResultMarkdown = async (item: QuranSearchResult) => {
  try {
    const formatted = await quranApi.formatReference({
      surah_number: item.surah_number,
      ayah_number: item.number_in_surah,
      edition_id: 'quran-simple',
      translation_id: selectedTranslation.value || undefined,
      include_citation: true,
    })
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(formatted.markdown)
      alert(languageStore.t('نقل‌قول آیه کپی شد.', 'Verse copied to clipboard.'))
    }
  } catch (err) {
    console.error('Failed to copy reference:', err)
  }
}
</script>
