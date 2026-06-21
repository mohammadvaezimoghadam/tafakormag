<script setup lang="ts">
import { computed } from 'vue'
import { 
  PencilIcon, 
  CopyIcon, 
  PinIcon, 
  Trash2Icon 
} from '@lucide/vue'

const props = defineProps<{
  isOpen: boolean
  triggerRect: DOMRect | null
  postId: string | number
  postText?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit', id: string | number): void
  (e: 'delete', id: string | number): void
  (e: 'pin', id: string | number): void
  (e: 'react', id: string | number, emoji: string): void
  (e: 'copy', id: string | number): void
}>()

// List of reaction emojis
const emojis = ['👍', '❤️', '🔥', '😂', '😮', '😢', '🎉', '👏', '🤔', '👀', '🚀', '💯']

// Calculate dynamic styles for the floating menu based on trigger card's position
const menuWidth = 224 // w-56 is 224px
const menuHeight = 210 // reaction bar + menu + gaps

const menuStyle = computed(() => {
  if (!props.triggerRect) {
    return {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    }
  }

  const rect = props.triggerRect
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  // Check where we have more vertical space
  const spaceBelow = viewportHeight - rect.bottom
  const spaceAbove = rect.top

  let top = 0
  
  if (spaceBelow > menuHeight + 20) {
    top = rect.bottom + 8
  } else if (spaceAbove > menuHeight + 20) {
    top = rect.top - menuHeight - 8
  } else {
    // Falls back to centering on the card vertical axis with padding
    top = Math.max(16, rect.top + (rect.height - menuHeight) / 2)
  }

  // Center horizontally relative to trigger card
  let left = rect.left + (rect.width - menuWidth) / 2
  
  // Bound check to keep inside viewport with 16px padding on sides
  left = Math.max(16, Math.min(viewportWidth - menuWidth - 16, left))

  return {
    top: `${top}px`,
    left: `${left}px`,
    position: 'fixed' as const
  }
})

const handleReact = (emoji: string) => {
  emit('react', props.postId, emoji)
  emit('close')
}

const handleAction = (action: 'edit' | 'delete' | 'pin' | 'copy') => {
  if (action === 'copy') {
    if (props.postText) {
      navigator.clipboard.writeText(props.postText)
    }
    emit('copy', props.postId)
  } else if (action === 'edit') {
    emit('edit', props.postId)
  } else if (action === 'delete') {
    emit('delete', props.postId)
  } else if (action === 'pin') {
    emit('pin', props.postId)
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
        class="flex flex-col gap-2 pointer-events-auto select-none scale-up text-right w-56 animate-menu-pop"
        :style="menuStyle"
        @click.stop
      >
        <!-- Horizontal Scrollable Reactions Bar -->
        <div 
          class="flex items-center gap-2.5 overflow-x-auto no-scrollbar bg-white/70 dark:bg-card/75 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-full px-4.5 py-2.5 shadow-lg w-full"
          dir="rtl"
        >
          <button 
            v-for="emoji in emojis" 
            :key="emoji"
            @click="handleReact(emoji)"
            class="text-xl hover:scale-130 transition-transform duration-200 active:scale-90 cursor-pointer shrink-0"
          >
            {{ emoji }}
          </button>
        </div>

        <!-- Vertical Dropdown Menu Options -->
        <div 
          class="bg-white/75 dark:bg-card/80 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-2xl p-1.5 shadow-xl flex flex-col gap-0.5 w-full"
          dir="rtl"
        >
          <!-- Copy Text -->
          <button 
            @click="handleAction('copy')" 
            class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
          >
            <span>کپی متن پست</span>
            <CopyIcon class="size-3.5 text-muted-foreground" />
          </button>

          <!-- Edit Post -->
          <button 
            @click="handleAction('edit')" 
            class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
          >
            <span>ویرایش پست</span>
            <PencilIcon class="size-3.5 text-muted-foreground" />
          </button>

          <!-- Pin Post -->
          <button 
            @click="handleAction('pin')" 
            class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
          >
            <span>سنجاق کردن</span>
            <PinIcon class="size-3.5 text-muted-foreground" />
          </button>

          <!-- Divider -->
          <div class="h-[1px] bg-border/40 my-1" />

          <!-- Delete Post -->
          <button 
            @click="handleAction('delete')" 
            class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-destructive hover:bg-destructive/10 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
          >
            <span>حذف پست</span>
            <Trash2Icon class="size-3.5 text-destructive" />
          </button>
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
