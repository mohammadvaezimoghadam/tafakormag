<template>
  <div
    :id="`ayah-${ayah.number_in_surah}`"
    :class="[
      'p-5 sm:p-6 bg-white dark:bg-zinc-900 border rounded-3xl space-y-4 transition-all duration-300 shadow-sm relative group',
      isCurrentAudio
        ? 'border-emerald-500 ring-2 ring-emerald-500/20 bg-emerald-50/20 dark:bg-emerald-950/20 shadow-md shadow-emerald-500/5'
        : 'border-zinc-200/80 dark:border-zinc-800/80 hover:border-emerald-500/40'
    ]"
    :dir="languageStore.dir"
  >
    <!-- Card Toolbar -->
    <div class="flex items-center justify-between text-xs text-zinc-400 gap-2 border-b border-zinc-100 dark:border-zinc-800/60 pb-3">
      <!-- Ayah Badge -->
      <div class="flex items-center gap-2">
        <span
          :class="[
            'w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs transition-colors',
            isCurrentAudio
              ? 'bg-emerald-600 text-white'
              : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300'
          ]"
        >
          {{ ayah.number_in_surah }}
        </span>
        <span class="text-[11px] text-zinc-400 hidden sm:inline">
          {{ languageStore.t(`آیه ${ayah.number_in_surah} از ${surah.name}`, `Ayah ${ayah.number_in_surah} of ${surah.name}`) }}
        </span>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-1.5">
        <!-- Play / Pause Audio -->
        <button
          @click="$emit('play', ayah)"
          type="button"
          :title="isPlaying && isCurrentAudio ? 'توقف پخش' : 'تلاوت صوتی این آیه'"
          :class="[
            'px-2.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer',
            isCurrentAudio && isPlaying
              ? 'bg-emerald-600 text-white shadow-sm animate-pulse'
              : 'bg-zinc-100 hover:bg-emerald-50 dark:bg-zinc-800 dark:hover:bg-emerald-950/40 text-zinc-700 dark:text-zinc-300 hover:text-emerald-600 dark:hover:text-emerald-400'
          ]"
        >
          <span v-if="isCurrentAudio && isPlaying">⏸</span>
          <span v-else>▶</span>
          <span class="text-[11px]">{{ isCurrentAudio && isPlaying ? languageStore.t('در حال پخش', 'Playing') : languageStore.t('صوت', 'Play') }}</span>
        </button>

        <!-- Bookmark Toggle -->
        <button
          @click="$emit('toggle-bookmark', ayah)"
          type="button"
          :title="isBookmarked ? 'حذف از نشان‌شده‌ها' : 'نشان کردن این آیه'"
          :class="[
            'p-1.5 rounded-xl text-xs transition-colors cursor-pointer',
            isBookmarked
              ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400'
              : 'bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'
          ]"
        >
          <span>{{ isBookmarked ? '★' : '☆' }}</span>
        </button>

        <!-- Copy Markdown Quote -->
        <button
          @click="copyVerseMarkdown"
          type="button"
          :title="languageStore.t('کپی متن و ترجمه به صورت مارک‌داون', 'Copy Markdown')"
          class="px-2.5 py-1.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1 cursor-pointer"
        >
          <span>📋</span>
          <span class="hidden sm:inline text-[11px]">{{ languageStore.t('کپی نقل‌قول', 'Copy Quote') }}</span>
        </button>
      </div>
    </div>

    <!-- Arabic Text -->
    <div class="pt-2">
      <p
        class="text-right font-serif leading-loose text-zinc-900 dark:text-zinc-100 select-text tracking-wide"
        :style="{ fontSize: `${fontSize || 24}px` }"
      >
        {{ ayah.text }}
        <span class="inline-block mx-1.5 text-emerald-600 dark:text-emerald-400 font-sans text-base font-bold align-middle select-none">
          ﴿{{ ayah.number_in_surah }}﴾
        </span>
      </p>
    </div>

    <!-- Translation -->
    <div
      v-if="showTranslation && ayah.translation?.text"
      class="pt-1"
    >
      <div class="p-3.5 bg-zinc-50/80 dark:bg-zinc-800/40 rounded-2xl border-r-3 border-emerald-500/60 space-y-1">
        <p class="text-xs sm:text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed italic text-right select-text">
          {{ ayah.translation.text }}
        </p>
        <div v-if="ayah.translation.author || ayah.translation.edition_name" class="text-[10px] text-zinc-400 text-left">
          {{ ayah.translation.author || ayah.translation.edition_name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLanguageStore } from '@/stores/languageStore'
import { quranApi } from '../api'
import type { QuranSurah, QuranAyah } from '../types'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  ayah: QuranAyah
  surah: QuranSurah
  isPlaying?: boolean
  isCurrentAudio?: boolean
  isBookmarked?: boolean
  fontSize?: number
  showTranslation?: boolean
}>(), {
  isPlaying: false,
  isCurrentAudio: false,
  isBookmarked: false,
  fontSize: 24,
  showTranslation: true,
})

const emit = defineEmits<{
  (e: 'play', ayah: QuranAyah): void
  (e: 'toggle-bookmark', ayah: QuranAyah): void
}>()

const copyVerseMarkdown = async () => {
  try {
    const formatted = await quranApi.formatReference({
      surah_number: props.surah.number,
      ayah_number: props.ayah.number_in_surah,
      edition_id: props.ayah.edition || 'quran-simple',
      translation_id: props.ayah.translation?.edition_id || undefined,
      include_citation: true,
    })

    if (navigator.clipboard) {
      await navigator.clipboard.writeText(formatted.markdown)
      alert(languageStore.t('نقل‌قول آیه با موفقیت در کلیپ‌بورد کپی شد.', 'Verse citation copied to clipboard.'))
    }
  } catch (err) {
    console.error('Failed to copy verse markdown:', err)
  }
}
</script>
