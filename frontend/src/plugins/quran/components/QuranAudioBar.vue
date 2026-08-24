<template>
  <div
    v-if="audio.currentSurah.value && audio.currentAyahNumber.value !== null"
    class="fixed bottom-3 inset-x-3 sm:max-w-2xl sm:mx-auto z-40 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 rounded-3xl p-3 sm:p-4 shadow-2xl transition-all duration-300 animate-in slide-in-from-bottom-5"
    :dir="languageStore.dir"
  >
    <!-- Progress Bar (Clickable) -->
    <div class="mb-2">
      <div
        @click="handleSeek"
        class="h-1.5 w-full bg-zinc-100 dark:bg-zinc-800 rounded-full cursor-pointer overflow-hidden relative group"
      >
        <div
          class="h-full bg-emerald-600 dark:bg-emerald-500 rounded-full transition-all duration-150"
          :style="{ width: `${audio.progress.value}%` }"
        />
      </div>
      <div class="flex items-center justify-between text-[10px] text-zinc-400 font-mono mt-1 px-1">
        <span>{{ formatTime(audio.currentTime.value) }}</span>
        <span>{{ formatTime(audio.duration.value) }}</span>
      </div>
    </div>

    <!-- Controls & Info Row -->
    <div class="flex items-center justify-between gap-3">
      
      <!-- Track Metadata -->
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="w-9 h-9 rounded-2xl bg-emerald-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
          📖
        </div>
        <div class="min-w-0">
          <h4 class="font-bold text-xs sm:text-sm text-zinc-900 dark:text-zinc-100 truncate">
            سوره {{ audio.currentSurah.value.name }} • آیه {{ audio.currentAyahNumber.value }}
          </h4>
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400 truncate">
            {{ audio.currentReciter.value?.nameFa }}
          </p>
        </div>
      </div>

      <!-- Playback Controls -->
      <div class="flex items-center gap-1.5 sm:gap-2">
        <!-- Prev Ayah -->
        <button
          @click="audio.prevAyah"
          type="button"
          :title="languageStore.t('آیه قبلی', 'Previous Ayah')"
          class="w-8 h-8 rounded-xl bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 flex items-center justify-center text-xs transition-colors cursor-pointer"
        >
          ⏭
        </button>

        <!-- Play / Pause Button -->
        <button
          @click="audio.togglePlayPause"
          type="button"
          :class="[
            'w-10 h-10 rounded-2xl flex items-center justify-center text-sm font-bold transition-all shadow-md active:scale-95 cursor-pointer',
            audio.isPlaying.value
              ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/30'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20'
          ]"
        >
          <span v-if="audio.isLoading.value" class="animate-spin text-xs">⌛</span>
          <span v-else-if="audio.isPlaying.value">⏸</span>
          <span v-else>▶</span>
        </button>

        <!-- Next Ayah -->
        <button
          @click="audio.nextAyah"
          type="button"
          :title="languageStore.t('آیه بعدی', 'Next Ayah')"
          class="w-8 h-8 rounded-xl bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 flex items-center justify-center text-xs transition-colors cursor-pointer"
        >
          ⏮
        </button>

        <!-- Repeat Mode Toggle -->
        <button
          @click="cycleRepeatMode"
          type="button"
          :title="getRepeatTitle()"
          :class="[
            'px-2 h-8 rounded-xl text-[11px] font-bold flex items-center gap-1 transition-colors cursor-pointer',
            audio.repeatMode.value !== 'none'
              ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
              : 'bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-500'
          ]"
        >
          <span>🔁</span>
          <span class="text-[10px] hidden sm:inline">{{ audio.repeatMode.value === 'ayah' ? 'آیه' : audio.repeatMode.value === 'surah' ? 'سوره' : 'خاموش' }}</span>
        </button>

        <!-- Playback Rate Menu -->
        <select
          :value="audio.playbackRate.value"
          @change="e => audio.setPlaybackRate(Number((e.target as HTMLSelectElement).value))"
          class="h-8 px-2 bg-zinc-100 dark:bg-zinc-800 border-none rounded-xl text-[11px] font-bold text-zinc-700 dark:text-zinc-300 focus:outline-none cursor-pointer"
        >
          <option :value="0.75">0.75x</option>
          <option :value="1.0">1.0x</option>
          <option :value="1.25">1.25x</option>
          <option :value="1.5">1.5x</option>
          <option :value="2.0">2.0x</option>
        </select>

        <!-- Close Audio Bar -->
        <button
          @click="audio.stop"
          type="button"
          :title="languageStore.t('بستن پخش‌کننده', 'Close')"
          class="w-7 h-7 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-800 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 flex items-center justify-center text-xs transition-colors cursor-pointer ml-1"
        >
          ✕
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { useLanguageStore } from '@/stores/languageStore'
import { useQuranAudio } from '../composables/useQuranAudio'

const languageStore = useLanguageStore()
const audio = useQuranAudio()

const formatTime = (seconds: number) => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const handleSeek = (e: MouseEvent) => {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  const percent = (clickX / rect.width) * 100
  audio.seek(percent)
}

const cycleRepeatMode = () => {
  const current = audio.repeatMode.value
  if (current === 'none') {
    audio.setRepeatMode('surah')
  } else if (current === 'surah') {
    audio.setRepeatMode('ayah')
  } else {
    audio.setRepeatMode('none')
  }
}

const getRepeatTitle = () => {
  const mode = audio.repeatMode.value
  if (mode === 'ayah') return 'تکرار همین آیه'
  if (mode === 'surah') return 'تکرار کل سوره'
  return 'پخش بدون تکرار'
}
</script>
