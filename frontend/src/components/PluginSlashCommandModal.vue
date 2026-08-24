<template>
  <div
    v-if="isOpen"
    class="w-full text-start flex flex-col gap-2.5 pb-3 mb-2 border-b border-border/40 bg-card/60 dark:bg-card/40 backdrop-blur-md rounded-2xl p-3 border shadow-xs transition-all"
    :dir="languageStore.dir"
  >
    <!-- Header with Shadcn-style Breadcrumbs & Close -->
    <div class="flex items-center justify-between gap-2">
      <nav class="flex items-center gap-1.5 text-xs overflow-x-auto no-scrollbar py-0.5">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="h-7 px-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shrink-0 transition-colors"
          :class="[
            currentStep === 'plugins'
              ? 'text-foreground bg-muted/60'
              : 'text-muted-foreground hover:text-foreground'
          ]"
          @click="setStep('plugins')"
        >
          <BookOpenIcon class="size-3.5 text-primary" />
          <span>{{ languageStore.t('افزونه‌ها', 'Plugins') }}</span>
        </Button>

        <template v-if="currentStep === 'surah' || currentStep === 'ayah'">
          <ChevronLeftIcon v-if="languageStore.dir === 'rtl'" class="size-3 text-muted-foreground/50 shrink-0" />
          <ChevronRightIcon v-else class="size-3 text-muted-foreground/50 shrink-0" />
          
          <Button
            type="button"
            variant="ghost"
            size="sm"
            class="h-7 px-2 rounded-xl text-xs font-bold flex items-center gap-1 shrink-0 transition-colors"
            :class="[
              currentStep === 'surah'
                ? 'text-foreground bg-muted/60'
                : 'text-muted-foreground hover:text-foreground'
            ]"
            @click="setStep('surah')"
          >
            <span>{{ languageStore.t('قرآن کریم', 'Holy Quran') }}</span>
          </Button>
        </template>

        <template v-if="currentStep === 'ayah' && selectedSurah">
          <ChevronLeftIcon v-if="languageStore.dir === 'rtl'" class="size-3 text-muted-foreground/50 shrink-0" />
          <ChevronRightIcon v-else class="size-3 text-muted-foreground/50 shrink-0" />
          
          <Badge variant="secondary" class="h-6 px-2 text-xs font-bold shrink-0 truncate max-w-[140px] rounded-lg">
            سوره {{ selectedSurah.name }}
          </Badge>
        </template>
      </nav>

      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        class="h-7 w-7 rounded-xl text-muted-foreground hover:text-foreground active:scale-95 shrink-0"
        :title="languageStore.t('بستن', 'Close')"
        @click="handleClose"
      >
        <XIcon class="size-3.5" />
      </Button>
    </div>

    <!-- STEP 1: PLUGINS LIST -->
    <div v-if="currentStep === 'plugins'" class="flex flex-col gap-1.5">
      <Button
        type="button"
        variant="outline"
        class="w-full h-auto p-2.5 rounded-xl hover:bg-muted/60 flex items-center justify-between text-start transition-all cursor-pointer border-border/40 hover:border-primary/30 group"
        @click="selectPlugin('quran')"
      >
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="size-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-105 transition-transform shrink-0">
            <BookOpenIcon class="size-4" />
          </div>
          <div class="flex flex-col min-w-0 text-start">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-bold text-foreground">
                {{ languageStore.t('قرآن کریم', 'Holy Quran') }}
              </span>
              <Badge variant="secondary" class="font-mono text-[10px] px-1.5 py-0 h-4">
                /quran
              </Badge>
            </div>
            <p class="text-[11px] text-muted-foreground truncate font-normal mt-0.5">
              {{ languageStore.t('جستجو و درج آیه و سوره به همراه ترجمه', 'Search and insert Quranic verses with translation') }}
            </p>
          </div>
        </div>

        <span class="text-xs text-muted-foreground group-hover:text-foreground group-hover:-translate-x-0.5 transition-transform shrink-0">
          {{ languageStore.isFa ? '←' : '→' }}
        </span>
      </Button>
    </div>

    <!-- STEP 2: SURAH PICKER -->
    <div v-else-if="currentStep === 'surah'" class="flex flex-col gap-2 min-h-0">
      <!-- Search Input -->
      <div class="relative shrink-0">
        <input
          ref="surahSearchInputRef"
          type="text"
          v-model="surahQuery"
          :placeholder="languageStore.t('جستجوی سوره (نام، شماره، آل عمران، بقره)...', 'Search surah (name, number)...')"
          class="w-full h-8 px-3 py-1.5 pr-8.5 bg-muted/40 border border-border/50 focus:border-primary/50 focus:ring-1 focus:ring-primary/20 rounded-xl text-xs text-foreground placeholder:text-muted-foreground/60 outline-none transition-colors"
        />
        <SearchIcon class="absolute right-2.5 top-2.5 size-3.5 text-muted-foreground/60 pointer-events-none" />
        <button
          v-if="surahQuery"
          type="button"
          @click="surahQuery = ''"
          class="absolute left-2.5 top-2 size-4 text-muted-foreground hover:text-foreground text-xs flex items-center justify-center cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- Surahs List -->
      <div v-if="loadingSurahs" class="text-center py-4 text-xs text-muted-foreground flex items-center justify-center gap-1.5">
        <span class="size-1.5 bg-primary rounded-full animate-ping" />
        <span>{{ languageStore.t('در حال دریافت سوره‌ها...', 'Loading surahs...') }}</span>
      </div>

      <div v-else-if="filteredSurahs.length === 0" class="text-center py-4 text-xs text-muted-foreground">
        {{ languageStore.t('سوره‌ای یافت نشد.', 'No surahs found.') }}
      </div>

      <div v-else class="flex flex-col gap-1 overflow-y-auto pr-0.5 max-h-48 scrollbar-thin">
        <button
          v-for="s in filteredSurahs"
          :key="s.number"
          type="button"
          @click="selectSurah(s)"
          class="w-full px-2.5 py-2 rounded-xl hover:bg-muted/60 flex items-center justify-between text-start transition-colors cursor-pointer group border border-transparent hover:border-border/40"
        >
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="size-6 rounded-lg bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary flex items-center justify-center font-bold text-[10px] font-mono shrink-0 transition-colors">
              {{ s.number }}
            </span>
            <div class="flex flex-col min-w-0">
              <span class="text-xs font-bold text-foreground block truncate">
                سوره {{ s.name }}
              </span>
              <span class="text-[10px] text-muted-foreground block truncate">
                {{ s.english_name_translation || s.english_name }}
              </span>
            </div>
          </div>

          <div class="flex items-center gap-1.5 shrink-0 text-[10px] text-muted-foreground">
            <span class="font-medium">{{ s.ayah_count }} {{ languageStore.t('آیه', 'Ayahs') }}</span>
            <Badge variant="outline" class="text-[9px] px-1 py-0 h-4 border-border/40 font-normal">
              {{ s.revelation_type === 'Meccan' ? 'مکی' : 'مدنی' }}
            </Badge>
          </div>
        </button>
      </div>
    </div>

    <!-- STEP 3: AYAH PICKER & LIVE PREVIEW -->
    <div v-else-if="currentStep === 'ayah' && selectedSurah" class="flex flex-col gap-2.5 min-h-0">
      <!-- Input Controls Row with Shadcn DropdownMenu & Number Input -->
      <div class="grid grid-cols-2 gap-2 shrink-0">
        <!-- Ayah Number Input -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold text-muted-foreground">
            {{ languageStore.t('شماره آیه (۱ تا', 'Ayah (1 to') }} {{ selectedSurah.ayah_count }})
          </label>
          <input
            type="number"
            v-model.number="selectedAyahNumber"
            :min="1"
            :max="selectedSurah.ayah_count"
            @input="fetchVersePreview"
            class="w-full h-8 px-2.5 py-1 bg-muted/40 border border-border/50 focus:border-primary/50 focus:ring-1 focus:ring-primary/20 rounded-xl text-xs font-bold text-foreground outline-none transition-colors"
          />
        </div>

        <!-- Translation Selector using DropdownMenu -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold text-muted-foreground">
            {{ languageStore.t('ترجمه', 'Translation') }}
          </label>
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button
                variant="outline"
                size="sm"
                class="w-full h-8 px-2.5 rounded-xl border-border/50 text-xs font-bold justify-between hover:bg-muted/60 transition-colors text-start"
              >
                <span class="truncate">{{ activeTranslationLabel }}</span>
                <ChevronDownIcon class="size-3.5 text-muted-foreground shrink-0" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent class="w-48 rounded-2xl p-1 shadow-xl border-border/60" :dir="languageStore.dir">
              <DropdownMenuItem
                v-for="opt in translationOptions"
                :key="opt.value"
                class="rounded-xl px-2.5 py-1.5 text-xs font-bold flex items-center justify-between cursor-pointer"
                @click="setTranslation(opt.value)"
              >
                <span>{{ opt.label }}</span>
                <CheckIcon v-if="selectedTranslation === opt.value" class="size-3.5 text-primary" />
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <!-- Quick Verse Slider using Shadcn Slider -->
      <div class="flex flex-col gap-1.5 shrink-0 px-0.5 pt-0.5">
        <div class="flex items-center justify-between text-[10px] text-muted-foreground font-mono">
          <span>۱</span>
          <span class="font-bold text-foreground text-xs">
            {{ languageStore.t('آیه', 'Ayah') }} {{ selectedAyahNumber }}
          </span>
          <span>{{ selectedSurah.ayah_count }}</span>
        </div>
        <Slider
          :min="1"
          :max="selectedSurah.ayah_count"
          :step="1"
          v-model="ayahSliderValue"
          class="w-full"
        />
      </div>

      <!-- Live Verse Preview Box -->
      <div class="border border-border/50 bg-muted/30 dark:bg-muted/15 rounded-2xl p-3 flex flex-col gap-1.5 flex-1 overflow-y-auto max-h-28 scrollbar-thin">
        <div class="flex items-center justify-between text-[10px] font-bold text-muted-foreground">
          <span>{{ languageStore.t('متن و ترجمه آیه', 'Verse Text & Translation') }}</span>
          <span v-if="loadingPreview" class="text-[9px] text-primary flex items-center gap-1">
            <span class="size-1 bg-primary rounded-full animate-ping" />
            {{ languageStore.t('در حال دریافت...', 'Loading...') }}
          </span>
        </div>

        <div v-if="previewAyah" class="flex flex-col gap-1.5">
          <p class="text-xs text-right font-serif font-semibold leading-relaxed text-foreground select-text">
            ﴿ {{ previewAyah.text }} ﴾
          </p>
          <p v-if="previewAyah.translation?.text" class="text-[11px] text-muted-foreground leading-normal italic border-r-2 border-primary/50 pr-2 select-text">
            {{ previewAyah.translation.text }}
          </p>
        </div>
        <div v-else-if="!loadingPreview" class="text-[10px] text-muted-foreground text-center py-2">
          {{ languageStore.t('آیه یافت نشد.', 'Verse not found.') }}
        </div>
      </div>

      <!-- Footer Action Buttons -->
      <div class="flex items-center justify-between gap-2 shrink-0 pt-1">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="h-8 px-2.5 rounded-xl text-xs font-bold text-muted-foreground hover:text-foreground transition-colors"
          @click="setStep('surah')"
        >
          {{ languageStore.isFa ? '← تغییر سوره' : 'Back to surahs' }}
        </Button>

        <Button
          type="button"
          variant="default"
          size="sm"
          :disabled="!previewAyah || loadingPreview"
          class="h-8 px-3.5 rounded-xl text-xs font-bold shadow-xs shadow-primary/20 gap-1.5"
          @click="confirmAndInsert"
        >
          <CheckIcon class="size-3.5" />
          <span>{{ languageStore.t('تأیید و درج در پیام', 'Insert Verse') }}</span>
        </Button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { quranApi } from '@/plugins/quran/api'
import type { QuranSurah, QuranAyah } from '@/plugins/quran/types'
import {
  BookOpenIcon,
  SearchIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  CheckIcon,
  XIcon,
} from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'

export type SlashModalStep = 'plugins' | 'surah' | 'ayah'

const props = withDefaults(defineProps<{
  isOpen: boolean
  initialStep?: SlashModalStep
}>(), {
  isOpen: false,
  initialStep: 'plugins',
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select-plugin', pluginIdentifier: string, token: string): void
  (e: 'select-surah', surah: QuranSurah, token: string): void
  (e: 'confirm', payload: {
    token: string
    surah: QuranSurah
    ayahNumber: number
    ayah: QuranAyah
    markdown: string
  }): void
}>()

const languageStore = useLanguageStore()

const currentStep = ref<SlashModalStep>(props.initialStep)
const surahs = ref<QuranSurah[]>([])
const loadingSurahs = ref(false)
const surahQuery = ref('')
const surahSearchInputRef = ref<HTMLInputElement | null>(null)

const selectedSurah = ref<QuranSurah | null>(null)
const selectedAyahNumber = ref(1)
const selectedTranslation = ref('fa.ansarian')
const previewAyah = ref<QuranAyah | null>(null)
const loadingPreview = ref(false)

const translationOptions = [
  { value: 'fa.ansarian', label: 'حسین انصاریان (فارسی)' },
  { value: 'fa.makarem', label: 'مکارم شیرازی (فارسی)' },
  { value: 'en.sahih', label: 'English (Sahih)' },
  { value: '', label: 'بدون ترجمه' },
]

const activeTranslationLabel = computed(() => {
  const opt = translationOptions.find(o => o.value === selectedTranslation.value)
  return opt ? opt.label : 'انتخاب ترجمه'
})

const setTranslation = (val: string) => {
  selectedTranslation.value = val
  fetchVersePreview()
}

// Shadcn Slider computed binding (expects array)
const ayahSliderValue = computed<number[]>({
  get: () => [selectedAyahNumber.value],
  set: (val: number[]) => {
    if (val && val.length > 0 && typeof val[0] === 'number') {
      selectedAyahNumber.value = val[0]
      fetchVersePreview()
    }
  },
})

// Surah Name Normalizer for robust search & slugification
const slugifySurah = (name: string, number: number): string => {
  const cleanName = name
    .toLowerCase()
    .replace(/^al-/, '')
    .replace(/^ال/, '')
    .replace(/[\s\-\'\’\:\.]+/g, '')
    .replace(/[أإآ]/g, 'a')
    .replace(/[ة]/g, 'h')
    .replace(/[ي]/g, 'y')
  return cleanName || `surah${number}`
}

const filteredSurahs = computed(() => {
  if (!surahQuery.value.trim()) return surahs.value
  const q = surahQuery.value.trim().toLowerCase()
  return surahs.value.filter(s => {
    return (
      s.name.toLowerCase().includes(q) ||
      (s.english_name && s.english_name.toLowerCase().includes(q)) ||
      (s.english_name_translation && s.english_name_translation.toLowerCase().includes(q)) ||
      String(s.number) === q
    )
  })
})

const loadSurahs = async () => {
  if (surahs.value.length > 0) return
  loadingSurahs.value = true
  try {
    surahs.value = await quranApi.getSurahs()
  } catch (err) {
    console.error('[SlashModal] Failed to load surahs:', err)
  } finally {
    loadingSurahs.value = false
  }
}

watch(() => props.isOpen, (open) => {
  if (open) {
    currentStep.value = props.initialStep || 'plugins'
    loadSurahs()
    if (currentStep.value === 'surah') {
      nextTick(() => surahSearchInputRef.value?.focus())
    }
  }
})

const setStep = (step: SlashModalStep) => {
  currentStep.value = step
  if (step === 'surah') {
    nextTick(() => surahSearchInputRef.value?.focus())
  }
}

const selectPlugin = (identifier: string) => {
  if (identifier === 'quran') {
    emit('select-plugin', 'quran', '/quran ')
    setStep('surah')
  }
}

const selectSurah = (surah: QuranSurah) => {
  selectedSurah.value = surah
  selectedAyahNumber.value = 1
  const slug = slugifySurah(surah.english_name || surah.name, surah.number)
  const token = `/quran-sureh:${slug}`
  emit('select-surah', surah, token)
  setStep('ayah')
  fetchVersePreview()
}

const fetchVersePreview = async () => {
  if (!selectedSurah.value) return
  loadingPreview.value = true
  try {
    previewAyah.value = await quranApi.getAyah(
      selectedSurah.value.number,
      selectedAyahNumber.value,
      {
        edition: 'quran-simple',
        with_translation: selectedTranslation.value || undefined,
      }
    )
  } catch (err) {
    previewAyah.value = null
    console.error('[SlashModal] Failed to load ayah preview:', err)
  } finally {
    loadingPreview.value = false
  }
}

const confirmAndInsert = async () => {
  if (!selectedSurah.value || !previewAyah.value) return
  const surah = selectedSurah.value
  const slug = slugifySurah(surah.english_name || surah.name, surah.number)
  const token = `/quran-sureh:${slug}-ayeh:${selectedAyahNumber.value}`

  let markdown = ''
  try {
    const formatted = await quranApi.formatReference({
      surah_number: surah.number,
      ayah_number: selectedAyahNumber.value,
      edition_id: 'quran-simple',
      translation_id: selectedTranslation.value || undefined,
      include_citation: true,
    })
    markdown = formatted.markdown
  } catch (err) {
    // Client-side fallback formatting
    markdown = `> ﴿${previewAyah.value.text}﴾\n`
    if (previewAyah.value.translation?.text) {
      markdown += `> *${previewAyah.value.translation.text}*\n`
    }
    markdown += `> — **سوره ${surah.name} (${surah.number}:${selectedAyahNumber.value})**`
  }

  emit('confirm', {
    token,
    surah,
    ayahNumber: selectedAyahNumber.value,
    ayah: previewAyah.value,
    markdown,
  })
  handleClose()
}

const handleClose = () => {
  emit('close')
}

onMounted(() => {
  if (props.isOpen) {
    loadSurahs()
  }
})
</script>
