<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm" :dir="languageStore.dir">
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200">
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/50 dark:bg-zinc-900/50">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-lg font-bold">
            📖
          </div>
          <div>
            <h3 class="font-bold text-zinc-900 dark:text-zinc-100 text-base">
              {{ languageStore.t('انتخاب و درج آیه قرآن', 'Select & Insert Quran Verse') }}
            </h3>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              {{ languageStore.t('جستجو و درج آیه به همراه ترجمه در متن یادداشت', 'Search and insert Quranic verse with translation') }}
            </p>
          </div>
        </div>
        <button
          @click="close"
          type="button"
          class="w-8 h-8 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-800 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 flex items-center justify-center transition-colors cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- Mode Switcher Tabs -->
      <div class="flex items-center px-6 pt-3 gap-2 border-b border-zinc-100 dark:border-zinc-800">
        <button
          @click="activeMode = 'browse'"
          type="button"
          :class="[
            'pb-2.5 text-xs font-bold transition-all border-b-2 cursor-pointer',
            activeMode === 'browse'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
          ]"
        >
          {{ languageStore.t('انتخاب سوره و آیه', 'Browse by Surah') }}
        </button>
        <button
          @click="activeMode = 'search'"
          type="button"
          :class="[
            'pb-2.5 text-xs font-bold transition-all border-b-2 cursor-pointer',
            activeMode === 'search'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
          ]"
        >
          {{ languageStore.t('جستجوی متنی آیه', 'Search Verses') }}
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 overflow-y-auto space-y-4 flex-1">
        
        <!-- MODE 1: BROWSE -->
        <div v-if="activeMode === 'browse'" class="space-y-4">
          <!-- Surah & Ayah Selector -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">
                {{ languageStore.t('سوره', 'Surah') }}
              </label>
              <select
                v-model="selectedSurahNumber"
                @change="onSurahChange"
                class="w-full px-3.5 py-2.5 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs sm:text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
              >
                <option v-for="s in surahs" :key="s.number" :value="s.number">
                  {{ s.number }}. سوره {{ s.name }} ({{ s.ayah_count }} آیه)
                </option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">
                {{ languageStore.t('شماره آیه', 'Ayah Number') }}
              </label>
              <input
                type="number"
                v-model.number="selectedAyahNumber"
                :min="1"
                :max="currentSurah?.ayah_count || 286"
                @input="fetchSelectedVerse"
                class="w-full px-3.5 py-2.5 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs sm:text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
              />
            </div>
          </div>

          <!-- Translation Selector -->
          <div>
            <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5">
              {{ languageStore.t('مترجم', 'Translation') }}
            </label>
            <select
              v-model="selectedTranslationId"
              @change="fetchSelectedVerse"
              class="w-full px-3.5 py-2.5 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs sm:text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
            >
              <option value="fa.ansarian">ترجمه فارسی (استاد انصاریان)</option>
              <option value="fa.makarem">ترجمه فارسی (آیت‌الله مکارم)</option>
              <option value="en.sahih">ترجمه انگلیسی (Sahih International)</option>
              <option value="">بدون ترجمه (فقط متن عربی)</option>
            </select>
          </div>
        </div>

        <!-- MODE 2: SEARCH -->
        <div v-else class="space-y-3">
          <div class="relative">
            <input
              type="text"
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              :placeholder="languageStore.t('جستجوی کلمه در آیات (مثال: نصرالله، صابرین)...', 'Search verses...')"
              class="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs sm:text-sm text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
            />
            <button
              @click="handleSearch"
              type="button"
              class="absolute left-2 top-1.5 px-3 py-1 bg-emerald-600 text-white rounded-lg text-xs font-bold"
            >
              {{ languageStore.t('جستجو', 'Search') }}
            </button>
          </div>

          <!-- Search Results List -->
          <div v-if="searchLoading" class="text-center py-6 text-xs text-zinc-400">
            {{ languageStore.t('در حال جستجو...', 'Searching...') }}
          </div>
          <div v-else-if="searchResults.length > 0" class="max-h-48 overflow-y-auto space-y-2 border border-zinc-100 dark:border-zinc-800 rounded-xl p-2">
            <div
              v-for="r in searchResults"
              :key="r.id"
              @click="selectSearchResult(r)"
              class="p-2.5 rounded-xl hover:bg-emerald-50 dark:hover:bg-emerald-950/40 border border-transparent hover:border-emerald-500/30 cursor-pointer transition-colors space-y-1"
            >
              <div class="flex items-center justify-between text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                <span>سوره {{ r.surah_name }} ({{ r.surah_number }}:{{ r.number_in_surah }})</span>
              </div>
              <p class="text-xs text-right font-serif line-clamp-2 text-zinc-800 dark:text-zinc-200">
                {{ r.text }}
              </p>
            </div>
          </div>
        </div>

        <!-- Live Preview Box -->
        <div class="border border-emerald-500/20 bg-emerald-50/40 dark:bg-emerald-950/20 rounded-2xl p-4 space-y-2.5">
          <div class="flex items-center justify-between text-xs text-emerald-700 dark:text-emerald-400 font-semibold">
            <span>{{ languageStore.t('پیش‌نمایش آیه انتخابی', 'Selected Verse Preview') }}</span>
            <span v-if="loading">{{ languageStore.t('در حال بارگذاری...', 'Loading...') }}</span>
          </div>

          <div v-if="previewAyah" class="space-y-2">
            <p class="text-base sm:text-lg text-right font-serif leading-loose text-zinc-900 dark:text-zinc-100 select-text">
              ﴿ {{ previewAyah.text }} ﴾
            </p>
            <p v-if="previewAyah.translation?.text" class="text-xs sm:text-sm text-zinc-600 dark:text-zinc-300 leading-relaxed italic border-r-2 border-emerald-500/40 pr-3 select-text">
              {{ previewAyah.translation.text }}
            </p>
          </div>
          <div v-else-if="!loading" class="text-xs text-zinc-400 text-center py-4">
            {{ languageStore.t('آیه انتخاب شده یافت نشد.', 'Verse not found.') }}
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-end gap-3">
        <button
          @click="close"
          type="button"
          class="px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          {{ languageStore.t('انصراف', 'Cancel') }}
        </button>
        <button
          @click="insertVerseIntoComposer"
          type="button"
          :disabled="!previewAyah || loading"
          class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/20 transition-all cursor-pointer"
        >
          {{ languageStore.t('درج در یادداشت', 'Insert into Note') }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { quranApi } from '../api'
import type { QuranSurah, QuranAyah, QuranSearchResult } from '../types'

const languageStore = useLanguageStore()

const props = defineProps<{
  onInsert?: (markdown: string) => void
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'insert', markdown: string): void
}>()

const isOpen = ref(true)
const activeMode = ref<'browse' | 'search'>('browse')
const loading = ref(false)
const searchLoading = ref(false)
const surahs = ref<QuranSurah[]>([])
const selectedSurahNumber = ref(1)
const selectedAyahNumber = ref(1)
const selectedTranslationId = ref('fa.ansarian')
const previewAyah = ref<QuranAyah | null>(null)
const searchQuery = ref('')
const searchResults = ref<QuranSearchResult[]>([])

const currentSurah = computed(() => {
  return surahs.value.find(s => s.number === selectedSurahNumber.value)
})

onMounted(async () => {
  try {
    loading.value = true
    surahs.value = await quranApi.getSurahs()
    await fetchSelectedVerse()
  } catch (err) {
    console.error('Failed to load surahs:', err)
  } finally {
    loading.value = false
  }
})

const onSurahChange = () => {
  selectedAyahNumber.value = 1
  fetchSelectedVerse()
}

const fetchSelectedVerse = async () => {
  if (!selectedSurahNumber.value || !selectedAyahNumber.value) return
  loading.value = true
  try {
    previewAyah.value = await quranApi.getAyah(
      selectedSurahNumber.value,
      selectedAyahNumber.value,
      {
        edition: 'quran-simple',
        with_translation: selectedTranslationId.value || undefined,
      }
    )
  } catch (err) {
    previewAyah.value = null
    console.error('Failed to fetch ayah preview:', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  searchLoading.value = true
  try {
    const res = await quranApi.search({
      q: searchQuery.value.trim(),
      edition: 'quran-simple',
      with_translation: selectedTranslationId.value || undefined,
      page_size: 15,
    })
    searchResults.value = res.results
  } catch (err) {
    console.error('Search failed in picker:', err)
  } finally {
    searchLoading.value = false
  }
}

const selectSearchResult = (r: QuranSearchResult) => {
  selectedSurahNumber.value = r.surah_number
  selectedAyahNumber.value = r.number_in_surah
  activeMode.value = 'browse'
  fetchSelectedVerse()
}

const insertVerseIntoComposer = async () => {
  if (!previewAyah.value) return
  try {
    const formatted = await quranApi.formatReference({
      surah_number: selectedSurahNumber.value,
      ayah_number: selectedAyahNumber.value,
      edition_id: 'quran-simple',
      translation_id: selectedTranslationId.value || undefined,
      include_citation: true,
    })

    if (props.onInsert) {
      props.onInsert(formatted.markdown)
    }
    emit('insert', formatted.markdown)
    close()
  } catch (err) {
    console.error('Failed to format reference, using fallback:', err)
    // Client-side fallback formatting
    const sName = currentSurah.value?.name || `سوره ${selectedSurahNumber.value}`
    let md = `> ﴿${previewAyah.value.text}﴾\n`
    if (previewAyah.value.translation?.text) {
      md += `> *${previewAyah.value.translation.text}*\n`
    }
    md += `> — **سوره ${sName} (${selectedSurahNumber.value}:${selectedAyahNumber.value})**`
    if (props.onInsert) props.onInsert(md)
    emit('insert', md)
    close()
  }
}

const close = () => {
  isOpen.value = false
  emit('close')
}
</script>
