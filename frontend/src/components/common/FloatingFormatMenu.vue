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
  hasText?: boolean
  mode?: 'full' | 'context' | 'auto'
}>(), {
  show: false,
  coords: null,
  selectedText: '',
  hasText: false,
  mode: 'auto'
})

const emit = defineEmits<{
  (e: 'format', type: FormatType): void
  (e: 'action', type: ActionType): void
}>()

const languageStore = useLanguageStore()

const isContextMode = computed(() => {
  if (props.mode === 'context') return true
  if (props.mode === 'full') return false
  return !props.selectedText || props.selectedText.trim().length === 0
})

const handleFormat = (type: FormatType) => {
  emit('format', type)
}

const handleAction = (type: ActionType) => {
  emit('action', type)
}

// تشخیص فرمت‌های فعال روی متن انتخاب‌شده
const isBoldActive = computed(() => {
  const s = props.selectedText.trim()
  return (s.startsWith('**') && s.endsWith('**') && s.length >= 4)
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
      class="floating-format-menu absolute z-50 bg-card/95 dark:bg-zinc-900/95 backdrop-blur-md border border-border/80 dark:border-border/40 shadow-2xl rounded-2xl p-1 flex items-center gap-0.5 select-none -translate-x-1/2 max-w-[calc(100vw-24px)] overflow-x-auto scrollbar-none pointer-events-auto"
      :style="menuStyle"
      :dir="languageStore.dir"
      @mousedown.prevent
      @pointerdown.prevent
      @touchstart.stop
      @touchend.stop
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

      <!-- ================= A) Context Mode (Long Press / Caret Mode) ================= -->
      <template v-if="isContextMode">
        <!-- Paste Button with Label -->
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="h-7.5 px-2.5 rounded-xl text-xs font-bold text-foreground hover:bg-muted/80 active:scale-95 transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
          :title="languageStore.t('جایگذاری (Paste)', 'Paste (Ctrl+V)')"
          @click="handleAction('paste')"
          @pointerdown.prevent
        >
          <ClipboardPasteIcon class="size-3.5 text-primary stroke-[2.2]" />
          <span>{{ languageStore.t('جایگذاری', 'Paste') }}</span>
        </Button>

        <!-- Select All Button with Label (if input has text) -->
        <Button
          v-if="props.hasText"
          type="button"
          variant="ghost"
          size="sm"
          class="h-7.5 px-2.5 rounded-xl text-xs font-bold text-foreground hover:bg-muted/80 active:scale-95 transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
          :title="languageStore.t('انتخاب همه (Select All)', 'Select All (Ctrl+A)')"
          @click="handleAction('select-all')"
          @pointerdown.prevent
        >
          <CheckCheckIcon class="size-3.5 text-muted-foreground stroke-[2.2]" />
          <span>{{ languageStore.t('انتخاب همه', 'Select All') }}</span>
        </Button>
      </template>

      <!-- ================= B) Full Selection Mode (With Text Selected) ================= -->
      <template v-else>
        <!-- Copy Button -->
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          class="h-7 w-7 rounded-xl text-foreground/80 hover:text-foreground hover:bg-muted/80 active:scale-95 transition-all cursor-pointer shrink-0"
          :title="languageStore.t('کپی (Copy)', 'Copy (Ctrl+C)')"
          @click="handleAction('copy')"
          @pointerdown.prevent
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
          @pointerdown.prevent
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
          @pointerdown.prevent
        >
          <CheckCheckIcon class="size-3.5 stroke-[2.2]" />
        </Button>

        <!-- Paste Button -->
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          class="h-7 w-7 rounded-xl text-foreground/80 hover:text-foreground hover:bg-muted/80 active:scale-95 transition-all cursor-pointer shrink-0"
          :title="languageStore.t('جایگذاری (Paste)', 'Paste (Ctrl+V)')"
          @click="handleAction('paste')"
          @pointerdown.prevent
        >
          <ClipboardPasteIcon class="size-3.5 stroke-[2.2]" />
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
          @pointerdown.prevent
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
          @pointerdown.prevent
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
          @pointerdown.prevent
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
          @pointerdown.prevent
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
          @pointerdown.prevent
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
          @pointerdown.prevent
        >
          <QuoteIcon class="size-3.5 stroke-[2.5]" />
        </Button>
      </template>
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
