<script setup lang="ts">
import { computed } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()
import { 
  PencilIcon, 
  CopyIcon, 
  Trash2Icon 
} from '@lucide/vue'

const props = withDefaults(defineProps<{
  isOpen: boolean
  triggerRect: DOMRect | null
  touchPos: { x: number; y: number } | null
  postId: string | number
  postText?: string
  isOwner?: boolean
}>(), {
  isOwner: false
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', id: string | number): void
  (e: 'delete', id: string | number): void
  (e: 'pin', id: string | number): void
  (e: 'react', id: string | number, emoji: string): void
  (e: 'copy', id: string | number): void
}>()

// Calculate dynamic styles for the floating menu based on touch position or trigger card
const menuWidth = 224 // w-56 is 224px
const menuHeight = computed(() => {
  const optionsHeight = props.isOwner ? 128 : 40
  return optionsHeight
})

const menuStyle = computed(() => {
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  if (!props.touchPos || (props.touchPos.x === 0 && props.touchPos.y === 0)) {
    if (!props.triggerRect) {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      }
    }

    const rect = props.triggerRect
    const spaceBelow = viewportHeight - rect.bottom
    const spaceAbove = rect.top

    let top = 0
    if (spaceBelow > menuHeight.value + 20) {
      top = rect.bottom + 8
    } else if (spaceAbove > menuHeight.value + 20) {
      top = rect.top - menuHeight.value - 8
    } else {
      top = Math.max(16, rect.top + (rect.height - menuHeight.value) / 2)
    }

    let left = rect.left + (rect.width - menuWidth) / 2
    left = Math.max(16, Math.min(viewportWidth - menuWidth - 16, left))

    return {
      top: `${top}px`,
      left: `${left}px`,
      position: 'fixed' as const
    }
  }

  const { x, y } = props.touchPos
  let left = x - menuWidth / 2
  let top = y + 8 // offset menu below touch point

  if (y + menuHeight.value + 24 > viewportHeight) {
    top = y - menuHeight.value - 8 // position above touch point if overflowing below
  }

  left = Math.max(16, Math.min(viewportWidth - menuWidth - 16, left))
  top = Math.max(16, Math.min(viewportHeight - menuHeight.value - 16, top))

  return {
    top: `${top}px`,
    left: `${left}px`,
    position: 'fixed' as const
  }
})

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

const handleAction = async (action: 'edit' | 'delete' | 'copy') => {
  if (action === 'copy') {
    if (props.postText) {
      await copyToClipboard(props.postText)
    }
    emit('copy', props.postId)
  } else if (action === 'edit') {
    emit('edit', props.postId)
  } else if (action === 'delete') {
    emit('delete', props.postId)
  }
  emit('close')
}
</script>

<template>
  <Transition name="fade">
    <div 
      v-if="isOpen" 
      class="fixed inset-0 z-50 bg-black/35 dark:bg-black/55 backdrop-blur-xs flex items-center justify-center pointer-events-auto"
      @click="emit('close')"
      @contextmenu.prevent="emit('close')"
    >
      <!-- Floating Menu Wrapper -->
      <div 
        class="flex flex-col gap-2 pointer-events-auto select-none scale-up text-start w-56 animate-menu-pop"
        :style="menuStyle"
        @click.stop
      >
        <!-- Vertical Dropdown Menu Options -->
        <div 
          class="bg-white/75 dark:bg-card/80 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-2xl p-1.5 shadow-xl flex flex-col gap-0.5 w-full"
          :dir="languageStore.dir"
        >
          <!-- Copy Text -->
          <button 
            @click="handleAction('copy')" 
            class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
          >
            <span>{{ languageStore.t('کپی متن پست', 'Copy Post Text') }}</span>
            <CopyIcon class="size-3.5 text-muted-foreground" />
          </button>

          <template v-if="isOwner">
            <!-- Edit Post -->
            <button 
              @click="handleAction('edit')" 
              class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
            >
              <span>{{ languageStore.t('ویرایش پست', 'Edit Post') }}</span>
              <PencilIcon class="size-3.5 text-muted-foreground" />
            </button>

            <!-- Divider -->
            <div class="h-[1px] bg-border/40 my-1" />

            <!-- Delete Post -->
            <button 
              @click="handleAction('delete')" 
              class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-destructive hover:bg-destructive/10 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
            >
              <span>{{ languageStore.t('حذف پست', 'Delete Post') }}</span>
              <Trash2Icon class="size-3.5 text-destructive" />
            </button>
          </template>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
/* Hide scrollbar for IE, Edge and Firefox */
.no-scrollbar {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes menuPop {
  0% {
    opacity: 0;
    transform: scale(0.92) translateY(5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.animate-menu-pop {
  animation: menuPop 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
</style>
