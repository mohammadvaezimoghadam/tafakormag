<template>
  <div
    class="text-center p-6 sm:p-8 bg-gradient-to-b from-emerald-500/15 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-3xl space-y-4 shadow-sm"
    :dir="languageStore.dir"
  >
    <!-- Metadata Badges -->
    <div class="flex flex-wrap items-center justify-center gap-2">
      <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 rounded-full text-xs font-bold shadow-2xs">
        <span>سوره شماره {{ surah.number }}</span>
      </span>

      <span class="inline-flex items-center gap-1 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-full text-xs font-semibold">
        <span>{{ surah.revelation_type === 'Meccan' ? languageStore.t('مکی', 'Meccan') : languageStore.t('مدنی', 'Medinan') }}</span>
      </span>

      <span class="inline-flex items-center gap-1 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-full text-xs font-semibold">
        <span>{{ surah.ayah_count }} {{ languageStore.t('آیه', 'Ayahs') }}</span>
      </span>

      <span class="inline-flex items-center gap-1 px-3 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-full text-xs font-semibold">
        <span>{{ languageStore.t(`جزء ${surah.juz_start}`, `Juz ${surah.juz_start}`) }}</span>
      </span>
    </div>

    <!-- Surah Titles -->
    <div class="space-y-1">
      <h1 class="text-3xl sm:text-5xl font-bold font-serif text-zinc-900 dark:text-zinc-100 tracking-wide">
        سورة {{ surah.name }}
      </h1>
      <p class="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 font-medium">
        {{ surah.english_name }} • {{ surah.english_name_translation }}
      </p>
    </div>

    <!-- Bismillah (Suppressed for Surah 9 At-Tawbah) -->
    <div
      v-if="surah.number !== 9 && (showBismillah ?? surah.bismillah_pre !== false)"
      class="pt-4 border-t border-emerald-500/15 max-w-sm mx-auto"
    >
      <p class="text-2xl sm:text-3xl font-serif text-emerald-800 dark:text-emerald-400 select-text leading-relaxed">
        بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLanguageStore } from '@/stores/languageStore'
import type { QuranSurah } from '../types'

const languageStore = useLanguageStore()

withDefaults(defineProps<{
  surah: QuranSurah
  showBismillah?: boolean
}>(), {
  showBismillah: true,
})
</script>
