<script setup lang="ts">
import { useLanguageStore } from '@/stores/languageStore'
import { 
  PencilIcon, 
  CopyIcon, 
  Trash2Icon,
  SendIcon
} from '@lucide/vue'
import {
  DropdownMenuRoot,
  DropdownMenuPortal,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from 'reka-ui'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  isOpen: boolean
  triggerRect?: DOMRect | null
  touchPos?: { x: number; y: number } | null
  postId: string | number
  postText?: string
  isOwner?: boolean
}>(), {
  isOpen: false,
  triggerRect: null,
  touchPos: null,
  isOwner: false
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', id: string | number): void
  (e: 'delete', id: string | number): void
  (e: 'publication-status', id: string | number): void
  (e: 'pin', id: string | number): void
  (e: 'react', id: string | number, emoji: string): void
  (e: 'copy', id: string | number): void
}>()

const copyToClipboard = async (text: string) => {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (err) {
      console.warn("navigator.clipboard failed, trying fallback:", err)
    }
  }
  
  // Fallback using textarea
  try {
    const textArea = document.createElement("textarea")
    textArea.value = text
    textArea.style.position = "fixed"
    textArea.style.top = "0"
    textArea.style.left = "0"
    textArea.style.width = "2em"
    textArea.style.height = "2em"
    textArea.style.padding = "0"
    textArea.style.border = "none"
    textArea.style.outline = "none"
    textArea.style.boxShadow = "none"
    textArea.style.background = "transparent"
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    return successful
  } catch (err) {
    console.error("Fallback copy failed:", err)
    return false
  }
}

const handleAction = async (action: 'edit' | 'delete' | 'copy' | 'publication-status') => {
  if (action === 'copy') {
    if (props.postText) {
      await copyToClipboard(props.postText)
    }
    emit('copy', props.postId)
  } else if (action === 'edit') {
    emit('edit', props.postId)
  } else if (action === 'delete') {
    emit('delete', props.postId)
  } else if (action === 'publication-status') {
    emit('publication-status', props.postId)
  }
  emit('close')
}
</script>

<template>
  <DropdownMenuRoot :open="isOpen" @update:open="(val: boolean) => { if (!val) emit('close') }">
    <DropdownMenuPortal>
      <DropdownMenuContent
        :dir="languageStore.dir"
        :side-offset="6"
        align="end"
        class="bg-popover/90 backdrop-blur-xl border border-border/60 rounded-2xl p-1.5 shadow-xl flex flex-col gap-0.5 w-56 z-50 animate-in fade-in-0 zoom-in-95 duration-100 outline-none select-none text-start"
      >
        <!-- Copy Text -->
        <DropdownMenuItem
          @click="handleAction('copy')"
          class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all outline-none"
        >
          <span>{{ languageStore.t('کپی متن پست', 'Copy Post Text') }}</span>
          <CopyIcon class="size-3.5 text-muted-foreground" />
        </DropdownMenuItem>

        <!-- Publication Status -->
        <DropdownMenuItem
          @click="handleAction('publication-status')"
          class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all outline-none"
        >
          <span>{{ languageStore.t('وضعیت انتشار', 'Publication Status') }}</span>
          <SendIcon class="size-3.5 text-primary" />
        </DropdownMenuItem>

        <template v-if="isOwner">
          <!-- Edit Post -->
          <DropdownMenuItem
            @click="handleAction('edit')"
            class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all outline-none"
          >
            <span>{{ languageStore.t('ویرایش پست', 'Edit Post') }}</span>
            <PencilIcon class="size-3.5 text-muted-foreground" />
          </DropdownMenuItem>

          <!-- Divider -->
          <DropdownMenuSeparator class="h-px bg-border/40 my-1" />

          <!-- Delete Post -->
          <DropdownMenuItem
            @click="handleAction('delete')"
            class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-destructive hover:bg-destructive/10 flex items-center justify-between cursor-pointer transition-all outline-none"
          >
            <span>{{ languageStore.t('حذف پست', 'Delete Post') }}</span>
            <Trash2Icon class="size-3.5 text-destructive" />
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>
