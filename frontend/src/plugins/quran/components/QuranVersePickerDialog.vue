<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm" :dir="languageStore.dir">
    <div class="bg-background border border-border/50 rounded-3xl w-[calc(100%-1rem)] max-w-[460px] shadow-2xl overflow-hidden flex flex-col max-h-[88vh] animate-in fade-in zoom-in-95 duration-200 text-start font-sans">
      
      <!-- Header Banner (مطابق استانداردهای دیالوگ پلتفرم) -->
      <div class="px-5 py-4 border-b border-border/40 flex items-center justify-between bg-gradient-to-br from-emerald-500/15 via-emerald-500/10 to-transparent shrink-0">
        <div class="flex items-center gap-3 min-w-0">
          <div class="size-9 rounded-2xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-base font-bold shadow-xs shrink-0">
            📖
          </div>
          <div class="min-w-0 flex flex-col text-start">
            <h3 class="font-black text-foreground text-xs sm:text-sm truncate">
              {{ languageStore.t('انتخاب و درج آیه قرآن', 'Select & Insert Quran Verse') }}
            </h3>
            <p class="text-[10px] sm:text-[10.5px] text-muted-foreground mt-0.5 truncate max-w-[240px] sm:max-w-xs">
              {{ languageStore.t('جستجو و درج آیه به همراه ترجمه در متن یادداشت', 'Search and insert Quranic verse with translation') }}
            </p>
          </div>
        </div>
        <button
          @click="close"
          type="button"
          class="size-7 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none shrink-0"
          :title="languageStore.t('بستن', 'Close')"
        >
          ✕
        </button>
      </div>

      <!-- Mode Switcher Tabs -->
      <div class="flex items-center px-5 pt-2.5 gap-2 border-b border-border/40 bg-muted/20 shrink-0">
        <button
          @click="activeMode = 'browse'"
          type="button"
          :class="[
            'pb-2 text-xs font-bold transition-all border-b-2 cursor-pointer',
            activeMode === 'browse'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
        >
          {{ languageStore.t('انتخاب سوره و آیه', 'Browse by Surah') }}
        </button>
        <button
          @click="activeMode = 'search'"
          type="button"
          :class="[
            'pb-2 text-xs font-bold transition-all border-b-2 cursor-pointer',
            activeMode === 'search'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
        >
          {{ languageStore.t('جستجوی متنی آیه', 'Search Verses') }}
        </button>
      </div>

      <!-- Content (Scrollable & Compact on Mobile) -->
      <div class="p-3.5 sm:p-4 overflow-y-auto space-y-3 flex-1 max-h-[calc(88vh-130px)]">
        
        <!-- MODE 1: BROWSE -->
        <div v-if="activeMode === 'browse'" class="space-y-3">
          <!-- Surah & Ayah Selector -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <div>
              <label class="block text-[11px] font-semibold text-foreground/80 mb-1">
                {{ languageStore.t('سوره', 'Surah') }}
              </label>
              <select
                v-model="selectedSurahNumber"
                @change="onSurahChange"
                class="w-full px-3 py-2 bg-muted/50 border border-border/60 rounded-xl text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
              >
                <option v-for="s in surahs" :key="s.number" :value="s.number">
                  {{ s.number }}. سوره {{ s.name }} ({{ s.ayah_count }} آیه)
                </option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-foreground/80 mb-1">
                {{ languageStore.t('شماره آیه', 'Ayah Number') }}
              </label>
              <input
                type="number"
                v-model.number="selectedAyahNumber"
                :min="1"
                :max="currentSurah?.ayah_count || 286"
                @input="fetchSelectedVerse"
                class="w-full px-3 py-2 bg-muted/50 border border-border/60 rounded-xl text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
              />
            </div>
          </div>

          <!-- Translation Selector -->
          <div>
            <label class="block text-[11px] font-semibold text-foreground/80 mb-1">
              {{ languageStore.t('مترجم', 'Translation') }}
            </label>
            <select
              v-model="selectedTranslationId"
              @change="fetchSelectedVerse"
              class="w-full px-3 py-2 bg-muted/50 border border-border/60 rounded-xl text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
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
          <div class="flex items-center gap-2">
            <input
              type="text"
              v-model="searchQuery"
              @keydown.enter="handleSearch"
              :placeholder="languageStore.t('کلمه یا بخشی از آیه را بنویسید...', 'Search keywords...')"
              class="w-full px-3 py-2 bg-muted/50 border border-border/60 rounded-xl text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
            />
            <button
              @click="handleSearch"
              type="button"
              :disabled="searchLoading"
              class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shrink-0 cursor-pointer disabled:opacity-50"
            >
              {{ languageStore.t('جستجو', 'Search') }}
            </button>
          </div>

          <!-- Search Results List -->
          <div v-if="searchLoading" class="text-center py-5 text-xs text-muted-foreground">
            {{ languageStore.t('در حال جستجو...', 'Searching...') }}
          </div>
          <div v-else-if="searchResults.length > 0" class="max-h-44 overflow-y-auto space-y-1.5 border border-border/50 rounded-xl p-1.5">
            <div
              v-for="r in searchResults"
              :key="r.id"
              @click="selectSearchResult(r)"
              class="p-2 rounded-lg hover:bg-emerald-500/10 border border-transparent hover:border-emerald-500/30 cursor-pointer transition-colors space-y-0.5"
            >
              <div class="flex items-center justify-between text-[10.5px] font-bold text-emerald-600 dark:text-emerald-400">
                <span>سوره {{ r.surah_name }} ({{ r.surah_number }}:{{ r.number_in_surah }})</span>
              </div>
              <p class="text-xs text-right font-serif line-clamp-2 text-foreground/90">
                {{ r.text }}
              </p>
            </div>
          </div>
        </div>

        <!-- Live Preview Box -->
        <div class="border border-emerald-500/20 bg-emerald-500/5 rounded-2xl p-3 sm:p-3.5 space-y-2">
          <div class="flex items-center justify-between text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">
            <span>{{ languageStore.t('پیش‌نمایش آیه انتخابی', 'Selected Verse Preview') }}</span>
            <span v-if="loading" class="text-[10px]">{{ languageStore.t('در حال بارگذاری...', 'Loading...') }}</span>
          </div>

          <div v-if="previewAyah" class="space-y-1.5">
            <p class="text-sm sm:text-base text-right font-serif leading-loose text-foreground select-text">
              ﴿ {{ previewAyah.text }} ﴾
            </p>
            <p v-if="previewAyah.translation?.text" class="text-xs text-muted-foreground leading-relaxed italic border-r-2 border-emerald-500/40 pr-2.5 select-text">
              {{ previewAyah.translation.text }}
            </p>
          </div>
          <div v-else-if="!loading" class="text-xs text-muted-foreground text-center py-3">
            {{ languageStore.t('آیه انتخاب شده یافت نشد.', 'Verse not found.') }}
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-4 py-3 border-t border-border/40 bg-muted/20 flex items-center justify-end gap-2 shrink-0">
        <button
          @click="close"
          type="button"
          class="px-3.5 py-1.5 rounded-xl text-xs font-medium text-foreground/80 hover:bg-muted transition-colors cursor-pointer"
        >
          {{ languageStore.t('انصراف', 'Cancel') }}
        </button>
        <button
          @click="insertVerseIntoComposer"
          type="button"
          :disabled="!previewAyah || loading"
          class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-xs font-semibold shadow-xs transition-all cursor-pointer"
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
