<script setup lang="ts">
import { computed } from 'vue'
import { 
  PencilIcon, 
  LinkIcon, 
  Trash2Icon 
} from '@lucide/vue'

const props = defineProps<{
  isOpen: boolean
  triggerRect: DOMRect | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit'): void
  (e: 'connections'): void
  (e: 'delete'): void
}>()

const menuWidth = 224 // w-56

// Calculate position of the dropdown relative to the detachable options button
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

  // Place it directly below the options button
  const top = rect.bottom + 8

  // Align it near the options button, making sure it stays inside screen boundaries
  let left = rect.left
  
  // Bound check to keep it inside the screen viewport with a 16px safety margin
  left = Math.max(16, Math.min(viewportWidth - menuWidth - 16, left))

  return {
    top: `${top}px`,
    left: `${left}px`,
    position: 'fixed' as const
  }
})

const handleAction = (action: 'edit' | 'connections' | 'delete') => {
  if (action === 'edit') {
    emit('edit')
  } else if (action === 'connections') {
    emit('connections')
  } else if (action === 'delete') {
    emit('delete')
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
        class="bg-white/75 dark:bg-card/80 backdrop-blur-xl border border-white/30 dark:border-white/10 rounded-2xl p-1.5 shadow-xl flex flex-col gap-0.5 w-56 pointer-events-auto select-none scale-up text-right animate-menu-pop"
        :style="menuStyle"
        @click.stop
        dir="rtl"
      >
        <!-- Edit Topic -->
        <button 
          @click="handleAction('edit')" 
          class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>ویرایش مشخصات تاپیک</span>
          <PencilIcon class="size-3.5 text-muted-foreground" />
        </button>

        <!-- Topic Connections -->
        <button 
          @click="handleAction('connections')" 
          class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>تنظیمات اتصالات تاپیک</span>
          <LinkIcon class="size-3.5 text-muted-foreground" />
        </button>

        <!-- Divider -->
        <div class="h-[1px] bg-border/40 my-1" />

        <!-- Delete Topic -->
        <button 
          @click="handleAction('delete')" 
          class="w-full text-right px-3 py-2 text-xs font-bold rounded-xl text-destructive hover:bg-destructive/10 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>حذف تاپیک</span>
          <Trash2Icon class="size-3.5 text-destructive" />
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
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
