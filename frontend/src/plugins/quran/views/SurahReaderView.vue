<template>
  <div class="max-w-4xl mx-auto px-4 py-8 pb-32 space-y-6" :dir="languageStore.dir">
    
    <!-- Top Navigation Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 p-3 bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800/80 rounded-2xl shadow-xs">
      <div class="flex items-center gap-2">
        <router-link
          to="/apps/quran"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-xs font-semibold text-zinc-700 dark:text-zinc-300 transition-colors"
        >
          <span>←</span>
          <span>{{ languageStore.t('فهرست سوره‌ها', 'All Surahs') }}</span>
        </router-link>

        <!-- Surah Dropdown Selector -->
        <select
          v-if="allSurahs.length > 0"
          :value="surahNumber"
          @change="onSurahSelect"
          class="px-3 py-1.5 bg-zinc-100 dark:bg-zinc-800 border-none rounded-xl text-xs font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none"
        >
          <option v-for="s in allSurahs" :key="s.number" :value="s.number">
            {{ s.number }}. {{ s.name }} ({{ s.ayah_count }} آیه)
          </option>
        </select>
      </div>

      <div class="flex items-center gap-1.5">
        <!-- Prev Surah Button -->
        <router-link
          v-if="surahDetail?.prev_surah || surahNumber > 1"
          :to="`/apps/quran/surahs/${surahDetail?.prev_surah?.number || surahNumber - 1}`"
          class="px-2.5 py-1.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-xl text-xs font-semibold"
          :title="languageStore.t('سوره قبلی', 'Previous Surah')"
        >
          <span>⏮</span>
        </router-link>

        <!-- Next Surah Button -->
        <router-link
          v-if="surahDetail?.next_surah || surahNumber < 114"
          :to="`/apps/quran/surahs/${surahDetail?.next_surah?.number || surahNumber + 1}`"
          class="px-2.5 py-1.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-xl text-xs font-semibold"
          :title="languageStore.t('سوره بعدی', 'Next Surah')"
        >
          <span>⏭</span>
        </router-link>

        <!-- Settings Popover Toggle -->
        <div class="relative">
          <button
            @click="showSettings = !showSettings"
            type="button"
            class="px-3 py-1.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-xl text-xs font-semibold flex items-center gap-1 cursor-pointer"
          >
            <span>⚙️</span>
            <span>{{ languageStore.t('تنظیمات', 'Settings') }}</span>
          </button>

          <!-- Settings Dropdown Dialog -->
          <div
            v-if="showSettings"
            class="absolute left-0 sm:right-0 sm:left-auto top-full mt-2 z-50 animate-in fade-in zoom-in-95 duration-150"
          >
            <EditionSwitcher
              :show-close="true"
              @close="showSettings = false"
              @change-translation="handleTranslationChange"
            />
          </div>
        </div>

        <!-- Search Shortcut -->
        <router-link
          to="/apps/quran/search"
          class="p-1.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-xl text-xs"
          :title="languageStore.t('جستجو', 'Search')"
        >
          <span>🔍</span>
        </router-link>
      </div>
    </div>

    <!-- Surah Header Banner -->
    <SurahHeader
      v-if="surah"
      :surah="surah"
    />

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 text-xs text-zinc-400">
      {{ languageStore.t('در حال بارگذاری آیات سوره...', 'Loading verses...') }}
    </div>

    <!-- Ayahs List -->
    <div v-else class="space-y-4">
      <AyahCard
        v-for="ayah in ayahs"
        :key="ayah.id"
        :ayah="ayah"
        :surah="surah!"
        :is-playing="audio.isPlaying.value"
        :is-current-audio="isAyahPlaying(ayah)"
        :is-bookmarked="reader.isBookmarked(surah!.number, ayah.number_in_surah)"
        :font-size="reader.fontSize.value"
        :show-translation="reader.showTranslation.value"
        @play="handlePlayAyah"
        @toggle-bookmark="handleToggleBookmark"
      />
    </div>

    <!-- Floating Audio Bar -->
    <QuranAudioBar />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLanguageStore } from '@/stores/languageStore'
import { quranApi } from '../api'
import { useQuranAudio } from '../composables/useQuranAudio'
import { useQuranReader } from '../composables/useQuranReader'
import SurahHeader from '../components/SurahHeader.vue'
import AyahCard from '../components/AyahCard.vue'
import EditionSwitcher from '../components/EditionSwitcher.vue'
import QuranAudioBar from '../components/QuranAudioBar.vue'
import type { QuranSurah, QuranSurahDetail, QuranAyah } from '../types'

const route = useRoute()
const router = useRouter()
const languageStore = useLanguageStore()
const audio = useQuranAudio()
const reader = useQuranReader()

const surahNumber = computed(() => Number(route.params.number || 1))
const surah = ref<QuranSurah | null>(null)
const surahDetail = ref<QuranSurahDetail | null>(null)
const allSurahs = ref<QuranSurah[]>([])
const ayahs = ref<QuranAyah[]>([])
const loading = ref(true)
const showSettings = ref(false)

let unsubscribeAudioListener: (() => void) | null = null

const loadSurahAndAyahs = async () => {
  loading.value = true
  try {
    const [surahsList, detailData, ayahsData] = await Promise.all([
      allSurahs.value.length === 0 ? quranApi.getSurahs() : Promise.resolve(allSurahs.value),
      quranApi.getSurahDetail(surahNumber.value).catch(() => null),
      quranApi.getSurahAyahs(surahNumber.value, {
        edition: reader.arabicEdition.value || 'quran-simple',
        with_translation: reader.translationEdition.value !== 'none' ? reader.translationEdition.value : undefined,
      }),
    ])

    if (allSurahs.value.length === 0) {
      allSurahs.value = surahsList
    }
    surahDetail.value = detailData
    surah.value = ayahsData.surah
    ayahs.value = ayahsData.ayahs

    // Persist last read state
    if (surah.value) {
      reader.saveLastRead(surah.value.number, surah.value.name, 1)
    }

    // Scroll to hash target if provided (e.g. #ayah-5)
    await nextTick()
    if (route.hash) {
      const targetEl = document.querySelector(route.hash)
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  } catch (err) {
    console.error('Failed to load surah and ayahs:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSurahAndAyahs()

  // Subscribe to audio changes for auto-scroll
  unsubscribeAudioListener = audio.onAyahChanged((sNum, aNum) => {
    if (sNum === surahNumber.value) {
      const el = document.getElementById(`ayah-${aNum}`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  })
})

onUnmounted(() => {
  if (unsubscribeAudioListener) {
    unsubscribeAudioListener()
  }
})

watch(() => route.params.number, () => {
  loadSurahAndAyahs()
})

const onSurahSelect = (e: Event) => {
  const target = e.target as HTMLSelectElement
  router.push(`/apps/quran/surahs/${target.value}`)
}

const handleTranslationChange = () => {
  loadSurahAndAyahs()
}

const isAyahPlaying = (ayah: QuranAyah) => {
  return (
    audio.currentSurah.value?.number === surahNumber.value &&
    audio.currentAyahNumber.value === ayah.number_in_surah
  )
}

const handlePlayAyah = (ayah: QuranAyah) => {
  if (!surah.value) return
  if (isAyahPlaying(ayah)) {
    audio.togglePlayPause()
  } else {
    audio.playAyah(surah.value, ayah.number_in_surah, ayah)
  }
}

const handleToggleBookmark = (ayah: QuranAyah) => {
  if (!surah.value) return
  reader.toggleBookmark(surah.value, ayah)
}
</script>
