<script setup lang="ts">
import { computed } from 'vue'
import { 
  BoldIcon, 
  ItalicIcon, 
  UnderlineIcon, 
  StrikethroughIcon, 
  CodeIcon, 
  QuoteIcon,
  CopyIcon,
  ScissorsIcon,
  CheckCheckIcon,
  ClipboardPasteIcon
} from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { useLanguageStore } from '@/stores/languageStore'
import type { FormatType } from '@/utils/textFormatter'

export type ActionType = 'copy' | 'cut' | 'select-all' | 'paste'

export interface MenuCoords {
  top: number
  left: number
  placement?: 'top' | 'bottom'
}

const props = withDefaults(defineProps<{
  show: boolean
  coords?: MenuCoords | null
  selectedText?: string
}>(), {
  show: false,
  coords: null,
  selectedText: ''
})

const emit = defineEmits<{
  (e: 'format', type: FormatType): void
  (e: 'action', type: ActionType): void
}>()

const languageStore = useLanguageStore()

const handleFormat = (type: FormatType) => {
  emit('format', type)
}

const handleAction = (type: ActionType) => {
  emit('action', type)
}

// تشخیص فرمت‌های فعال روی متن انتخاب‌شده
const isBoldActive = computed(() => {
  const s = props.selectedText.trim()
  return s.startsWith('**') && s.endsWith('**') && s.length >= 4
})

const isItalicActive = computed(() => {
  const s = props.selectedText.trim()
  return (s.startsWith('*') && s.endsWith('*') && !s.startsWith('**') && s.length >= 2) ||
         (s.startsWith('_') && s.endsWith('_') && !s.startsWith('__') && s.length >= 2)
})

const isUnderlineActive = computed(() => {
  const s = props.selectedText.trim()
  return s.startsWith('__') && s.endsWith('__') && s.length >= 4
})

const isStrikethroughActive = computed(() => {
  const s = props.selectedText.trim()
  return s.startsWith('~~') && s.endsWith('~~') && s.length >= 4
})

const isCodeActive = computed(() => {
  const s = props.selectedText.trim()
  return s.startsWith('`') && s.endsWith('`') && s.length >= 2
})

const isQuoteActive = computed(() => {
  const s = props.selectedText.trim()
  return s.startsWith('> ') || s.startsWith('>')
})

const menuStyle = computed(() => {
  if (!props.coords) return {}
  return {
    top: `${props.coords.top}px`,
    left: `${props.coords.left}px`,
  }
})
</script>

<template>
  <transition name="format-pop">
    <div
      v-if="props.show"
      class="floating-format-menu absolute z-50 bg-card/95 dark:bg-zinc-900/95 backdrop-blur-md border border-border/80 dark:border-border/40 shadow-2xl rounded-2xl p-1 flex items-center gap-0.5 select-none -translate-x-1/2 max-w-[calc(100vw-32px)] overflow-x-auto scrollbar-none"
      :style="menuStyle"
      :dir="languageStore.dir"
      @mousedown.prevent
      @touchstart.prevent.stop
      @contextmenu.prevent.stop
    >
      <!-- Small Arrow Pointer -->
      <div 
        v-if="props.coords"
        class="absolute left-1/2 -translate-x-1/2 size-2 rotate-45 bg-card/95 dark:bg-zinc-900/95 border-border/80 dark:border-border/40 pointer-events-none"
        :class="[
          props.coords.placement === 'bottom' 
            ? '-top-1 border-t border-l' 
            : '-bottom-1 border-b border-r'
        ]"
      />

      <!-- Clipboard Actions Group (Copy, Cut, Select All, Paste) -->
      <!-- Copy Button -->
      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        class="h-7 w-7 rounded-xl text-foreground/80 hover:text-foreground hover:bg-muted/80 active:scale-95 transition-all cursor-pointer shrink-0"
        :title="languageStore.t('کپی (Copy)', 'Copy (Ctrl+C)')"
        @click="handleAction('copy')"
      >
        <CopyIcon class="size-3.5 stroke-[2.2]" />
      </Button>

      <!-- Cut Button -->
      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        class="h-7 w-7 rounded-xl text-foreground/80 hover:text-foreground hover:bg-muted/80 active:scale-95 transition-all cursor-pointer shrink-0"
        :title="languageStore.t('برش (Cut)', 'Cut (Ctrl+X)')"
        @click="handleAction('cut')"
      >
        <ScissorsIcon class="size-3.5 stroke-[2.2]" />
      </Button>

      <!-- Select All Button -->
      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        class="h-7 w-7 rounded-xl text-foreground/80 hover:text-foreground hover:bg-muted/80 active:scale-95 transition-all cursor-pointer shrink-0"
        :title="languageStore.t('انتخاب همه (Select All)', 'Select All (Ctrl+A)')"
        @click="handleAction('select-all')"
      >
        <CheckCheckIcon class="size-3.5 stroke-[2.2]" />
      </Button>

      <!-- Separator between Clipboard and Formatting -->
      <div class="w-px h-4 bg-border/70 mx-0.5 shrink-0" />

      <!-- Formatting Group -->
      <!-- Bold Button -->
      <Button
        type="button"
        :variant="isBoldActive ? 'secondary' : 'ghost'"
        size="icon-xs"
        class="h-7 w-7 rounded-xl transition-all cursor-pointer shrink-0"
        :class="[
          isBoldActive 
            ? 'bg-primary/15 text-primary hover:bg-primary/20' 
            : 'text-foreground/80 hover:text-foreground hover:bg-muted/80'
        ]"
        :title="languageStore.t('بولد (Ctrl+B)', 'Bold (Ctrl+B)')"
        @click="handleFormat('bold')"
      >
        <BoldIcon class="size-3.5 stroke-[2.5]" />
      </Button>

      <!-- Italic Button -->
      <Button
        type="button"
        :variant="isItalicActive ? 'secondary' : 'ghost'"
        size="icon-xs"
        class="h-7 w-7 rounded-xl transition-all cursor-pointer shrink-0"
        :class="[
          isItalicActive 
            ? 'bg-primary/15 text-primary hover:bg-primary/20' 
            : 'text-foreground/80 hover:text-foreground hover:bg-muted/80'
        ]"
        :title="languageStore.t('ایتالیک (Ctrl+I)', 'Italic (Ctrl+I)')"
        @click="handleFormat('italic')"
      >
        <ItalicIcon class="size-3.5 stroke-[2.5]" />
      </Button>

      <!-- Underline Button -->
      <Button
        type="button"
        :variant="isUnderlineActive ? 'secondary' : 'ghost'"
        size="icon-xs"
        class="h-7 w-7 rounded-xl transition-all cursor-pointer shrink-0"
        :class="[
          isUnderlineActive 
            ? 'bg-primary/15 text-primary hover:bg-primary/20' 
            : 'text-foreground/80 hover:text-foreground hover:bg-muted/80'
        ]"
        :title="languageStore.t('زیرخط (Ctrl+U)', 'Underline (Ctrl+U)')"
        @click="handleFormat('underline')"
      >
        <UnderlineIcon class="size-3.5 stroke-[2.5]" />
      </Button>

      <!-- Strikethrough Button -->
      <Button
        type="button"
        :variant="isStrikethroughActive ? 'secondary' : 'ghost'"
        size="icon-xs"
        class="h-7 w-7 rounded-xl transition-all cursor-pointer shrink-0"
        :class="[
          isStrikethroughActive 
            ? 'bg-primary/15 text-primary hover:bg-primary/20' 
            : 'text-foreground/80 hover:text-foreground hover:bg-muted/80'
        ]"
        :title="languageStore.t('خط‌خورده (Ctrl+Shift+X)', 'Strikethrough (Ctrl+Shift+X)')"
        @click="handleFormat('strikethrough')"
      >
        <StrikethroughIcon class="size-3.5 stroke-[2.5]" />
      </Button>

      <!-- Separator -->
      <div class="w-px h-4 bg-border/70 mx-0.5 shrink-0" />

      <!-- Inline Code Button -->
      <Button
        type="button"
        :variant="isCodeActive ? 'secondary' : 'ghost'"
        size="icon-xs"
        class="h-7 w-7 rounded-xl transition-all cursor-pointer shrink-0"
        :class="[
          isCodeActive 
            ? 'bg-primary/15 text-primary hover:bg-primary/20' 
            : 'text-foreground/80 hover:text-foreground hover:bg-muted/80'
        ]"
        :title="languageStore.t('کد (Ctrl+`)', 'Code (Ctrl+`)')"
        @click="handleFormat('code')"
      >
        <CodeIcon class="size-3.5 stroke-[2.5]" />
      </Button>

      <!-- Quote Button -->
      <Button
        type="button"
        :variant="isQuoteActive ? 'secondary' : 'ghost'"
        size="icon-xs"
        class="h-7 w-7 rounded-xl transition-all cursor-pointer shrink-0"
        :class="[
          isQuoteActive 
            ? 'bg-primary/15 text-primary hover:bg-primary/20' 
            : 'text-foreground/80 hover:text-foreground hover:bg-muted/80'
        ]"
        :title="languageStore.t('نقل‌قول (Ctrl+Shift+Q)', 'Quote (Ctrl+Shift+Q)')"
        @click="handleFormat('quote')"
      >
        <QuoteIcon class="size-3.5 stroke-[2.5]" />
      </Button>
    </div>
  </transition>
</template>

<style scoped>
.format-pop-enter-active,
.format-pop-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.format-pop-enter-from,
.format-pop-leave-to {
  opacity: 0;
  transform: translate(-50%, 6px) scale(0.95);
}
</style>
