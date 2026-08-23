<template>
  <div class="max-w-4xl mx-auto px-4 py-8 space-y-6">
    
    <!-- Top Navigation -->
    <div class="flex items-center justify-between">
      <router-link
        to="/apps/quran"
        class="inline-flex items-center gap-2 text-sm font-semibold text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
      >
        <span>←</span>
        <span>بازگشت به فهرست سوره‌ها</span>
      </router-link>

      <div class="flex items-center gap-2">
        <select
          v-model="selectedTranslation"
          @change="reloadAyahs"
          class="px-3 py-1.5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-xs text-zinc-700 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
        >
          <option value="fa.ansarian">ترجمه انصاریان</option>
          <option value="fa.makarem">ترجمه مکارم</option>
          <option value="en.sahih">ترجمه انگلیسی</option>
          <option value="">بدون ترجمه</option>
        </select>
      </div>
    </div>

    <!-- Surah Title Banner -->
    <div v-if="surah" class="text-center p-8 bg-gradient-to-b from-emerald-500/10 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-3xl space-y-2">
      <span class="inline-block px-3 py-1 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 rounded-full text-xs font-semibold">
        سوره {{ surah.number }} • {{ surah.revelation_type === 'Meccan' ? 'مکی' : 'مدنی' }} • {{ surah.ayah_count }} آیه
      </span>
      <h1 class="text-3xl sm:text-4xl font-bold font-serif text-zinc-900 dark:text-zinc-100">
        سورة {{ surah.name }}
      </h1>
      <p class="text-sm text-zinc-500 dark:text-zinc-400">
        {{ surah.english_name }} ({{ surah.english_name_translation }})
      </p>

      <!-- Bismillah -->
      <div v-if="surah.bismillah_pre" class="pt-6">
        <p class="text-2xl sm:text-3xl font-serif text-emerald-800 dark:text-emerald-400 select-text">
          بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
        </p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 text-zinc-400 text-sm">
      در حال بارگذاری آیات...
    </div>

    <!-- Ayahs List -->
    <div v-else class="space-y-4">
      <div
        v-for="ayah in ayahs"
        :key="ayah.id"
        class="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800/80 rounded-3xl space-y-4 hover:border-emerald-500/40 transition-colors shadow-sm"
      >
        <div class="flex items-center justify-between text-xs text-zinc-400">
          <span class="w-8 h-8 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 flex items-center justify-center font-bold">
            {{ ayah.number_in_surah }}
          </span>

          <button
            @click="copyVerseMarkdown(ayah)"
            class="px-3 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/50 text-zinc-600 dark:text-zinc-400 hover:text-emerald-600 dark:hover:text-emerald-400 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
          >
            <span>📋</span>
            <span>کپی مارک‌داون</span>
          </button>
        </div>

        <!-- Arabic Text -->
        <p class="text-xl sm:text-2xl text-right font-serif leading-loose text-zinc-900 dark:text-zinc-100 select-text">
          {{ ayah.text }}
          <span class="inline-block mx-1.5 text-emerald-600 font-sans text-sm font-bold">﴿{{ ayah.number_in_surah }}﴾</span>
        </p>

        <!-- Translation -->
        <p
          v-if="ayah.translation"
          class="text-sm sm:text-base text-zinc-600 dark:text-zinc-300 leading-relaxed italic border-r-2 border-emerald-500/30 pr-4 pt-1"
        >
          {{ ayah.translation.text }}
        </p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { quranApi } from '../api'
import type { QuranSurah, QuranAyah } from '../types'

const route = useRoute()
const surahNumber = Number(route.params.number || 1)

const surah = ref<QuranSurah | null>(null)
const ayahs = ref<QuranAyah[]>([])
const selectedTranslation = ref('fa.ansarian')
const loading = ref(true)

const loadSurahAndAyahs = async () => {
  loading.value = true
  try {
    const data = await quranApi.getSurahAyahs(surahNumber, {
      edition: 'quran-simple',
      with_translation: selectedTranslation.value || undefined,
    })
    surah.value = data.surah
    ayahs.value = data.ayahs
  } catch (err) {
    console.error('Failed to load surah ayahs:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSurahAndAyahs()
})

const reloadAyahs = () => {
  loadSurahAndAyahs()
}

const copyVerseMarkdown = async (ayah: QuranAyah) => {
  if (!surah.value) return
  try {
    const formatted = await quranApi.formatReference({
      surah_number: surah.value.number,
      ayah_number: ayah.number_in_surah,
      edition_id: 'quran-simple',
      translation_id: selectedTranslation.value || undefined,
      include_citation: true,
    })
    await navigator.clipboard.writeText(formatted.markdown)
    alert('متن آیه در کلیپ‌بورد کپی شد.')
  } catch (err) {
    console.error('Failed to copy verse markdown:', err)
  }
}
</script>
