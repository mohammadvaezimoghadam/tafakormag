<template>
  <div class="space-y-4 p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-xl max-w-sm w-full" :dir="languageStore.dir">
    <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
      <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
        <span>⚙️</span>
        <span>{{ languageStore.t('تنظیمات نمایش و تلاوت', 'Reader & Audio Settings') }}</span>
      </h3>
      <button
        v-if="showClose"
        @click="$emit('close')"
        type="button"
        class="w-7 h-7 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 flex items-center justify-center text-xs"
      >
        ✕
      </button>
    </div>

    <!-- Translation Selector -->
    <div class="space-y-1.5">
      <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300">
        {{ languageStore.t('مترجم قرآن', 'Translation') }}
      </label>
      <select
        :value="reader.translationEdition.value"
        @change="e => onTranslationChange((e.target as HTMLSelectElement).value)"
        class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
      >
        <option value="fa.ansarian">ترجمه فارسی (استاد انصاریان)</option>
        <option value="fa.makarem">ترجمه فارسی (آیت‌الله مکارم)</option>
        <option value="en.sahih">ترجمه انگلیسی (Sahih International)</option>
        <option value="none">بدون ترجمه</option>
      </select>
    </div>

    <!-- Reciter Selector -->
    <div class="space-y-1.5">
      <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300">
        {{ languageStore.t('قاری تلاوت', 'Reciter') }}
      </label>
      <select
        :value="audio.currentReciterId.value"
        @change="e => audio.setReciter((e.target as HTMLSelectElement).value)"
        class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
      >
        <option v-for="r in audio.availableReciters" :key="r.id" :value="r.id">
          {{ r.nameFa }} ({{ r.style }})
        </option>
      </select>
    </div>

    <!-- Font Size Slider -->
    <div class="space-y-1.5">
      <div class="flex items-center justify-between text-xs font-semibold text-zinc-700 dark:text-zinc-300">
        <span>{{ languageStore.t('اندازه قلم متن آیات', 'Font Size') }}</span>
        <span class="text-emerald-600 dark:text-emerald-400 font-mono">{{ reader.fontSize.value }}px</span>
      </div>
      <input
        type="range"
        min="18"
        max="40"
        step="2"
        :value="reader.fontSize.value"
        @input="e => reader.setFontSize(Number((e.target as HTMLInputElement).value))"
        class="w-full accent-emerald-600 cursor-pointer"
      />
    </div>

    <!-- Translation Visibility Toggle -->
    <div class="flex items-center justify-between pt-2 border-t border-zinc-100 dark:border-zinc-800 text-xs">
      <span class="font-semibold text-zinc-700 dark:text-zinc-300">
        {{ languageStore.t('نمایش ترجمه در زیر آیات', 'Show Translation') }}
      </span>
      <input
        type="checkbox"
        :checked="reader.showTranslation.value"
        @change="e => reader.setShowTranslation((e.target as HTMLInputElement).checked)"
        class="size-4 accent-emerald-600 rounded cursor-pointer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLanguageStore } from '@/stores/languageStore'
import { useQuranReader } from '../composables/useQuranReader'
import { useQuranAudio } from '../composables/useQuranAudio'

const languageStore = useLanguageStore()
const reader = useQuranReader()
const audio = useQuranAudio()

withDefaults(defineProps<{
  showClose?: boolean
}>(), {
  showClose: false,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'change-translation', translationId: string): void
}>()

const onTranslationChange = (val: string) => {
  reader.setTranslationEdition(val)
  reader.setShowTranslation(val !== 'none')
  emit('change-translation', val)
}
</script>
