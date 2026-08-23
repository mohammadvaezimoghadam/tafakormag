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
          <span>{{ languageStore.t('صفحه اصلی قرآن', 'Quran Home') }}</span>
        </router-link>

        <!-- Juz Dropdown Selector -->
        <select
          :value="juzNumber"
          @change="onJuzSelect"
          class="px-3 py-1.5 bg-zinc-100 dark:bg-zinc-800 border-none rounded-xl text-xs font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none"
        >
          <option v-for="n in 30" :key="n" :value="n">
            {{ languageStore.t(`جزء ${n}`, `Juz ${n}`) }}
          </option>
        </select>
      </div>

      <div class="flex items-center gap-1.5">
        <!-- Prev Juz -->
        <router-link
          v-if="juzNumber > 1"
          :to="`/apps/quran/juz/${juzNumber - 1}`"
          class="px-2.5 py-1.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-xl text-xs font-semibold"
          :title="languageStore.t('جزء قبلی', 'Previous Juz')"
        >
          <span>⏮</span>
        </router-link>

        <!-- Next Juz -->
        <router-link
          v-if="juzNumber < 30"
          :to="`/apps/quran/juz/${juzNumber + 1}`"
          class="px-2.5 py-1.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-xl text-xs font-semibold"
          :title="languageStore.t('جزء بعدی', 'Next Juz')"
        >
          <span>⏭</span>
        </router-link>
      </div>
    </div>

    <!-- Juz Title Banner -->
    <div class="text-center p-6 bg-gradient-to-b from-emerald-500/15 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-3xl space-y-2 shadow-xs">
      <span class="inline-block px-3 py-1 bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 rounded-full text-xs font-bold">
        {{ languageStore.t(`قرآن کریم • جزء ${juzNumber}`, `Holy Quran • Juz ${juzNumber}`) }}
      </span>
      <h1 class="text-2xl sm:text-4xl font-bold font-serif text-zinc-900 dark:text-zinc-100">
        {{ currentJuzInfo?.name || `جزء ${juzNumber}` }}
      </h1>
      <p v-if="currentJuzInfo" class="text-xs text-zinc-500 dark:text-zinc-400">
        از سوره {{ currentJuzInfo.start_surah_name || currentJuzInfo.start_surah }} (آیه {{ currentJuzInfo.start_ayah }}) تا سوره {{ currentJuzInfo.end_surah_name || currentJuzInfo.end_surah }} (آیه {{ currentJuzInfo.end_ayah }})
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 text-xs text-zinc-400">
      {{ languageStore.t('در حال بارگذاری آیات جزء...', 'Loading Juz verses...') }}
    </div>

    <!-- Ayahs List -->
    <div v-else class="space-y-4">
      <div v-for="ayah in ayahs" :key="ayah.id" class="space-y-3">
        <!-- Surah Separator Banner (If Ayah is #1 of its Surah) -->
        <div
          v-if="ayah.number_in_surah === 1"
          class="p-4 bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-500/30 rounded-2xl text-center space-y-1 my-4"
        >
          <h2 class="text-lg font-bold font-serif text-emerald-800 dark:text-emerald-300">
            سورة {{ ayah.surah_name || `سوره شماره ${ayah.surah}` }}
          </h2>
          <p v-if="ayah.surah !== 9" class="text-base font-serif text-emerald-700 dark:text-emerald-400">
            بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
          </p>
        </div>

        <AyahCard
          :ayah="ayah"
          :surah="getSurahForAyah(ayah)"
          :is-playing="audio.isPlaying.value"
          :is-current-audio="isAyahPlaying(ayah)"
          :is-bookmarked="reader.isBookmarked(ayah.surah, ayah.number_in_surah)"
          :font-size="reader.fontSize.value"
          :show-translation="reader.showTranslation.value"
          @play="handlePlayAyah"
          @toggle-bookmark="handleToggleBookmark"
        />
      </div>
    </div>

    <!-- Floating Audio Bar -->
    <QuranAudioBar />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLanguageStore } from '@/stores/languageStore'
import { quranApi } from '../api'
import { useQuranAudio } from '../composables/useQuranAudio'
import { useQuranReader } from '../composables/useQuranReader'
import AyahCard from '../components/AyahCard.vue'
import QuranAudioBar from '../components/QuranAudioBar.vue'
import type { QuranJuz, QuranAyah, QuranSurah } from '../types'

const route = useRoute()
const router = useRouter()
const languageStore = useLanguageStore()
const audio = useQuranAudio()
const reader = useQuranReader()

const juzNumber = computed(() => Number(route.params.number || 1))
const allJuzs = ref<QuranJuz[]>([])
const ayahs = ref<QuranAyah[]>([])
const loading = ref(true)

const currentJuzInfo = computed(() => {
  return allJuzs.value.find(j => j.number === juzNumber.value)
})

const loadJuzData = async () => {
  loading.value = true
  try {
    const [juzsList, juzAyahsRes] = await Promise.all([
      allJuzs.value.length === 0 ? quranApi.getJuzs() : Promise.resolve(allJuzs.value),
      quranApi.getJuzAyahs(juzNumber.value, {
        edition: reader.arabicEdition.value || 'quran-simple',
        with_translation: reader.translationEdition.value !== 'none' ? reader.translationEdition.value : undefined,
      }),
    ])

    if (allJuzs.value.length === 0) {
      allJuzs.value = juzsList
    }

    if ('results' in juzAyahsRes && Array.isArray(juzAyahsRes.results)) {
      ayahs.value = juzAyahsRes.results
    } else if ('ayahs' in juzAyahsRes && Array.isArray(juzAyahsRes.ayahs)) {
      ayahs.value = juzAyahsRes.ayahs
    } else if (Array.isArray(juzAyahsRes)) {
      ayahs.value = juzAyahsRes as QuranAyah[]
    }
  } catch (err) {
    console.error('Failed to load juz data:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadJuzData()
})

watch(() => route.params.number, () => {
  loadJuzData()
})

const onJuzSelect = (e: Event) => {
  const target = e.target as HTMLSelectElement
  router.push(`/apps/quran/juz/${target.value}`)
}

const getSurahForAyah = (ayah: QuranAyah): QuranSurah => {
  return {
    number: ayah.surah,
    name: ayah.surah_name || `سوره ${ayah.surah}`,
    english_name: ayah.surah_english_name || '',
    english_name_translation: '',
    revelation_type: 'Meccan',
    ayah_count: 0,
    juz_start: juzNumber.value,
    bismillah_pre: true,
  }
}

const isAyahPlaying = (ayah: QuranAyah) => {
  return (
    audio.currentSurah.value?.number === ayah.surah &&
    audio.currentAyahNumber.value === ayah.number_in_surah
  )
}

const handlePlayAyah = (ayah: QuranAyah) => {
  const s = getSurahForAyah(ayah)
  if (isAyahPlaying(ayah)) {
    audio.togglePlayPause()
  } else {
    audio.playAyah(s, ayah.number_in_surah, ayah)
  }
}

const handleToggleBookmark = (ayah: QuranAyah) => {
  const s = getSurahForAyah(ayah)
  reader.toggleBookmark(s, ayah)
}
</script>
