<script setup lang="ts">
import { ref, watch } from 'vue'
import { 
  LanguagesIcon, 
  Wand2Icon, 
  CheckIcon, 
  XIcon, 
  Loader2Icon,
  AlertCircleIcon
} from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { 
  Sheet, 
  SheetContent, 
  SheetHeader, 
  SheetTitle, 
  SheetDescription,
  SheetClose
} from '@/components/ui/sheet'
import { 
  Tabs, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs'
import { 
  ToggleGroup, 
  ToggleGroupItem 
} from '@/components/ui/toggle-group'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Alert, 
  AlertTitle, 
  AlertDescription 
} from '@/components/ui/alert'
import { useLanguageStore } from '@/stores/languageStore'

interface Props {
  text: string
  open: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'apply', refinedText: string): void
}>()

const languageStore = useLanguageStore()

// Reactive state
const activeTab = ref('grammar')
const selectedLanguage = ref('English')
const selectedStyle = ref('Professional')
const previewText = ref('')
const loading = ref(false)
const hasGenerated = ref(false)
const errorMessage = ref<string | null>(null)

// Technical Requirement: Reset state on tab switch or when drawer opens
const resetState = () => {
  previewText.value = ''
  loading.value = false
  hasGenerated.value = false
  errorMessage.value = null
}

// Watch drawer opening state to reset
watch(() => props.open, (newVal) => {
  if (newVal) {
    resetState()
  }
})

// Watch tab switching to reset
watch(activeTab, () => {
  resetState()
})

// Localized Farsi helper maps
const getLanguageLabelFa = (lang: string) => {
  const map: Record<string, string> = {
    English: 'انگلیسی',
    Spanish: 'اسپانیایی',
    French: 'فرانسوی',
    German: 'آلمانی',
    Arabic: 'عربی'
  }
  return map[lang] || lang
}

const getStyleLabelFa = (style: string) => {
  const map: Record<string, string> = {
    Professional: 'رسمی',
    Casual: 'صمیمی',
    Creative: 'خلاقانه',
    Summarized: 'خلاصه شده'
  }
  return map[style] || style
}

// AI Refinement Simulation
const handleRefine = () => {
  if (!props.text) return
  loading.value = true
  hasGenerated.value = false
  errorMessage.value = null
  
  // Technical Requirement: Error handling scenario (e.g. 15% simulated connection failure chance)
  const isNetworkError = Math.random() < 0.15
  
  setTimeout(() => {
    if (isNetworkError) {
      errorMessage.value = languageStore.isFa 
        ? 'ارتباط با سرور هوش مصنوعی برقرار نشد. لطفا اتصال اینترنت خود را بررسی کنید.'
        : 'Connection to AI service failed. Please check your internet connection.'
      loading.value = false
      return
    }
    
    let result = ''
    const source = props.text.trim()
    
    if (activeTab.value === 'grammar') {
      // Simulate expert grammar & clarity improvement
      const corrected = source
        .replace(/\b(dont)\b/gi, "don't")
        .replace(/\b(cant)\b/gi, "can't")
        .replace(/\b(wont)\b/gi, "won't")
        .replace(/\b(im)\b/gi, "I'm")
        .replace(/\b(youre)\b/gi, "you're")
      
      result = `${corrected}`
    } else if (activeTab.value === 'translation') {
      // Simulate natural language translation
      const targetLang = selectedLanguage.value
      const translations: Record<string, string> = {
        English: `Translated text to English:\n"${source}"`,
        Spanish: `Traducción al español:\n"Esta es la traducción de su texto original: ${source}"`,
        French: `Traduction en français:\n"Il s'agit de la traduction de votre texte original : ${source}"`,
        German: `Deutsche Übersetzung:\n"Dies ist die Übersetzung Ihres Originaltextes: ${source}"`,
        Arabic: `الترجمة إلى العربية:\n"هذه هي ترجمة النص الأصلي: ${source}"`
      }
      result = translations[targetLang] || `[Translated to ${targetLang}]: ${source}`
    } else if (activeTab.value === 'style') {
      // Simulate tone and style shifting
      const targetStyle = selectedStyle.value
      if (targetStyle === 'Professional') {
        result = `I am writing to convey the following information:\n\n"${source}"\n\nShould you require any further assistance, please let me know.`
      } else if (targetStyle === 'Casual') {
        result = `Hey! Just wanted to share this with you:\n\n"${source}" 😊`
      } else if (targetStyle === 'Creative') {
        result = `✨ Let the thoughts flow: ${source} ✨ Let's explore the endless possibilities!`
      } else if (targetStyle === 'Summarized') {
        result = `Summary of the text:\n- Main point: ${source}`
      }
    }
    
    previewText.value = result
    loading.value = false
    hasGenerated.value = true
  }, 1200)
}

const handleApply = () => {
  emit('apply', previewText.value)
  emit('update:open', false)
}
</script>

<template>
  <Sheet :open="props.open" @update:open="val => emit('update:open', val)">
    <!-- Technical Requirement: z-[60] for drawer layout, bg-card coloring, backdrop-blur and z-[58] for backdrop overlay -->
    <!-- :showCloseButton="false" is set to hide the default top-right close button in favor of our left-aligned button -->
    <SheetContent 
      :showCloseButton="false" 
      side="bottom" 
      class="h-[75vh] flex flex-col p-0 rounded-t-[calc(var(--radius)*1.5)] gap-0 border-t border-border/40 dark:border-border/10 bg-card z-[60] overflow-hidden" 
      overlayClass="backdrop-blur-sm z-[58] bg-black/40"
      :dir="languageStore.dir"
    >
      
      <!-- Custom Close Button positioned absolutely on the top-left corner -->
      <SheetClose as-child>
        <Button 
          variant="ghost" 
          size="icon-sm"
          class="absolute top-4 left-4 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-xl active:scale-95 transition-all cursor-pointer z-10"
          :title="languageStore.t('بستن', 'Close')"
        >
          <XIcon class="size-4" />
        </Button>
      </SheetClose>

      <!-- Header -->
      <SheetHeader class="px-6 pt-5 pb-3 border-b border-border/10 shrink-0 text-start pr-12 pl-12">
        <div class="flex items-center gap-2">
          <Wand2Icon class="size-5 text-primary" />
          <SheetTitle class="text-base font-bold text-foreground">
            {{ languageStore.t('دستیار بهبود متن', 'AI Text Refiner Assistant') }}
          </SheetTitle>
        </div>
        <SheetDescription class="text-xs text-muted-foreground">
          {{ languageStore.t('متن خود را بهبود دهید، به زبان دیگری ترجمه کنید یا لحن آن را تغییر دهید.', 'Refine your text, translate it to another language, or change the tone of your message instantly.') }}
        </SheetDescription>
      </SheetHeader>

      <!-- Main Tabs Container -->
      <Tabs v-model="activeTab" class="w-full flex-1 flex flex-col min-h-0 overflow-hidden">
        
        <!-- Tabs List & Action Run Button Bar -->
        <div class="px-6 py-2 bg-muted/20 border-b border-border/10 flex items-center justify-between gap-3 shrink-0">
          <TabsList class="grid grid-cols-3 w-60 h-8 p-1 bg-muted/60 dark:bg-muted/30 rounded-xl">
            <TabsTrigger value="grammar" class="text-xs rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground">
              {{ languageStore.t('بهبود کلی', 'Clarity') }}
            </TabsTrigger>
            <TabsTrigger value="translation" class="text-xs rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground">
              {{ languageStore.t('ترجمه', 'Translate') }}
            </TabsTrigger>
            <TabsTrigger value="style" class="text-xs rounded-lg font-bold data-[state=active]:bg-background data-[state=active]:text-foreground">
              {{ languageStore.t('لحن', 'Tone') }}
            </TabsTrigger>
          </TabsList>
          
          <Button 
            variant="default"
            size="sm"
            class="h-8 rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer bg-primary text-primary-foreground hover:opacity-90 shrink-0"
            :disabled="loading || !props.text"
            @click="handleRefine"
          >
            <Loader2Icon v-if="loading" class="size-3.5 animate-spin" />
            <Wand2Icon v-else class="size-3.5" />
            <span>{{ loading ? languageStore.t('در حال پردازش...', 'Processing...') : languageStore.t('بهبود هوش مصنوعی', 'AI Refine') }}</span>
          </Button>
        </div>

        <!-- Technical Requirement: Interactive Chips Row (Mobile Responsive Flex Wrap) instead of Select Dropdown -->
        <!-- :spacing="8" is passed to spacing-out chips and override the default spacing-0 rounded-none rules, keeping them rounded-full -->
        <div 
          v-if="activeTab !== 'grammar'" 
          class="px-6 py-2.5 bg-muted/5 border-b border-border/10 flex flex-col gap-1.5 shrink-0 text-start"
        >
          <div class="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            <span v-if="activeTab === 'translation'">{{ languageStore.t('زبان مقصد را انتخاب کنید:', 'Select Target Language:') }}</span>
            <span v-else>{{ languageStore.t('لحن پیام را انتخاب کنید:', 'Select Tone Style:') }}</span>
          </div>

          <!-- Language Selection Chips (Fully rounded and animated with design tokens) -->
          <ToggleGroup 
            v-if="activeTab === 'translation'" 
            v-model="selectedLanguage" 
            type="single" 
            :spacing="8"
            class="flex flex-wrap gap-1.5 justify-start bg-transparent border-none p-0"
          >
            <ToggleGroupItem 
              v-for="lang in ['English', 'Spanish', 'French', 'German', 'Arabic']"
              :key="lang"
              :value="lang"
              variant="outline"
              class="h-7 text-xs px-3 rounded-full hover:scale-105 active:scale-95 transition-all duration-200 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground cursor-pointer shadow-none border-border/40"
            >
              {{ languageStore.isFa ? getLanguageLabelFa(lang) : lang }}
            </ToggleGroupItem>
          </ToggleGroup>

          <!-- Style Selection Chips (Fully rounded and animated with design tokens) -->
          <ToggleGroup 
            v-else-if="activeTab === 'style'" 
            v-model="selectedStyle" 
            type="single" 
            :spacing="8"
            class="flex flex-wrap gap-1.5 justify-start bg-transparent border-none p-0"
          >
            <ToggleGroupItem 
              v-for="style in ['Professional', 'Casual', 'Creative', 'Summarized']"
              :key="style"
              :value="style"
              variant="outline"
              class="h-7 text-xs px-3 rounded-full hover:scale-105 active:scale-95 transition-all duration-200 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground cursor-pointer shadow-none border-border/40"
            >
              {{ languageStore.isFa ? getStyleLabelFa(style) : style }}
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <!-- Columns Panel: Left (Source), Right (Refined Preview) -->
        <div class="flex-1 p-6 overflow-hidden flex flex-col md:flex-row gap-4 min-h-0">
          
          <!-- Source Area -->
          <div class="flex-1 flex flex-col gap-2 min-h-0 max-h-[140px] md:max-h-none bg-muted/10 border border-border/40 dark:border-border/20 rounded-2xl p-4">
            <div class="text-[10px] font-bold text-muted-foreground uppercase tracking-wider text-start">
              {{ languageStore.t('متن اصلی', 'Original Text') }}
            </div>
            <ScrollArea class="flex-1 w-full text-xs text-foreground/80 leading-relaxed overflow-y-auto whitespace-pre-wrap select-text pr-2 text-start">
              {{ props.text || languageStore.t('متنی وارد نشده است. ابتدا پیامی بنویسید.', 'No text provided. Type a message in the input box first.') }}
            </ScrollArea>
          </div>

          <!-- AI Output Preview Area -->
          <div class="flex-1 flex flex-col gap-2 min-h-0 max-h-[200px] md:max-h-none bg-muted/5 border border-border/30 dark:border-border/10 rounded-2xl p-4 relative">
            <div class="text-[10px] font-bold text-muted-foreground uppercase tracking-wider text-start">
              {{ languageStore.t('خروجی هوش مصنوعی', 'AI Refined Output') }}
            </div>
            
            <!-- Loading indicator with premium glow/scale/pulse micro-animations -->
            <div v-if="loading" class="flex-1 flex flex-col items-center justify-center gap-3 animate-in fade-in-0 duration-300">
              <div class="relative size-12 flex items-center justify-center">
                <Loader2Icon class="size-10 animate-spin text-primary relative z-10" />
                <div class="absolute inset-0 bg-primary/10 rounded-full animate-ping opacity-75" />
              </div>
              <span class="text-xs font-bold text-muted-foreground animate-pulse">
                {{ languageStore.t('هوش مصنوعی در حال بهبود متن شماست...', 'AI is refining your text...') }}
              </span>
            </div>

            <!-- Technical Requirement: Connection Error Banner Handling -->
            <div v-else-if="errorMessage" class="flex-1 flex flex-col items-center justify-center p-4 animate-in zoom-in-95 duration-200">
              <Alert variant="destructive" class="rounded-2xl max-w-sm text-start">
                <AlertCircleIcon class="size-4" />
                <AlertTitle>{{ languageStore.t('خطا در ارتباط', 'Connection Error') }}</AlertTitle>
                <AlertDescription class="text-xs">
                  {{ errorMessage }}
                </AlertDescription>
              </Alert>
              <Button 
                variant="outline" 
                size="sm"
                class="mt-4 rounded-xl text-xs font-bold border-destructive/30 hover:bg-destructive/10 text-destructive cursor-pointer hover:scale-105 active:scale-95 transition-transform"
                @click="handleRefine"
              >
                {{ languageStore.t('تلاش مجدد', 'Retry') }}
              </Button>
            </div>

            <!-- Empty state with subtle pulse transition -->
            <div v-else-if="!hasGenerated && !previewText" class="flex-1 flex flex-col items-center justify-center gap-3 text-center px-4 animate-in fade-in-0 duration-300">
              <Wand2Icon class="size-8 text-muted-foreground/30 animate-pulse" />
              <div class="text-xs font-bold text-muted-foreground">
                {{ languageStore.t('آماده برای بهبود متن', 'Ready to Refine') }}
              </div>
              <p class="text-[10px] text-muted-foreground/60 max-w-[220px] leading-relaxed">
                {{ languageStore.t('یک تب را انتخاب کنید و روی "اجرای هوش مصنوعی" کلیک کنید.', 'Choose a tab and click "Run AI" to start.') }}
              </p>
            </div>

            <!-- ScrollArea wrapping styled dynamic textarea for post-generation touches -->
            <ScrollArea v-else class="flex-1 w-full overflow-hidden animate-in fade-in duration-300">
              <textarea 
                v-model="previewText"
                class="w-full min-h-[120px] md:min-h-[220px] bg-transparent border-none outline-none focus-visible:ring-0 focus-visible:ring-offset-0 focus:ring-0 focus:outline-none focus-visible:outline-none text-xs font-semibold leading-relaxed text-foreground resize-none select-text pr-2 text-start"
                placeholder="AI Output will appear here..."
              />
            </ScrollArea>

            <!-- Apply CTA Button -->
            <div v-if="hasGenerated && !loading && !errorMessage" class="absolute bottom-4 right-4 z-10 animate-in zoom-in-95 duration-200">
              <Button
                variant="default"
                size="sm"
                class="h-8 rounded-lg text-xs font-bold bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg flex items-center gap-1.5 cursor-pointer border-none hover:scale-105 active:scale-95 transition-transform"
                @click="handleApply"
              >
                <CheckIcon class="size-3.5" />
                <span>{{ languageStore.t('تایید و اعمال', 'Accept & Apply') }}</span>
              </Button>
            </div>
          </div>

        </div>

      </Tabs>
    </SheetContent>
  </Sheet>
</template>
