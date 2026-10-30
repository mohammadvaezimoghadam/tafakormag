<script setup lang="ts">
import { computed } from 'vue'
import { 
  PencilIcon, 
  LinkIcon, 
  Trash2Icon,
  UploadCloudIcon,
  ShieldCheckIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  isOpen: boolean
  triggerRect: DOMRect | null
  isOwner?: boolean
}>(), {
  isOpen: false,
  triggerRect: null,
  isOwner: false,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit'): void
  (e: 'connections'): void
  (e: 'import'): void
  (e: 'admins'): void
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

const handleAction = (action: 'edit' | 'connections' | 'delete' | 'import' | 'admins') => {
  if (action === 'edit') {
    emit('edit')
  } else if (action === 'connections') {
    emit('connections')
  } else if (action === 'import') {
    emit('import')
  } else if (action === 'admins') {
    emit('admins')
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
      class="fixed inset-0 z-50 bg-black/30 dark:bg-black/50 backdrop-blur-xs flex items-center justify-center pointer-events-auto"
      @click="emit('close')"
      @contextmenu.prevent="emit('close')"
    >
      <!-- Floating Menu Wrapper -->
      <div 
        class="bg-card/95 backdrop-blur-2xl border border-border/80 dark:border-border/60 rounded-2xl p-1.5 shadow-[0_12px_40px_rgba(0,0,0,0.12)] flex flex-col gap-0.5 w-56 pointer-events-auto select-none scale-up text-start animate-menu-pop"
        :style="menuStyle"
        @click.stop
        :dir="languageStore.dir"
      >
        <!-- Topic Admins -->
        <button 
          @click="handleAction('admins')" 
          class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-foreground hover:bg-muted/80 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>{{ isOwner ? languageStore.t('مدیریت ادمین‌ها', 'Manage Admins') : languageStore.t('اطلاعات و ادمین‌ها', 'Admins & Info') }}</span>
          <ShieldCheckIcon class="size-3.5 text-primary" />
        </button>

        <!-- Edit Topic -->
        <button 
          v-if="isOwner"
          @click="handleAction('edit')" 
          class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-foreground hover:bg-muted/80 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>{{ languageStore.t('ویرایش مشخصات تاپیک', 'Edit Topic Info') }}</span>
          <PencilIcon class="size-3.5 text-muted-foreground" />
        </button>

        <!-- Topic Connections -->
        <button 
          v-if="isOwner"
          @click="handleAction('connections')" 
          class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-foreground hover:bg-muted/80 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>{{ languageStore.t('تنظیمات اتصالات تاپیک', 'Topic Connections Settings') }}</span>
          <LinkIcon class="size-3.5 text-muted-foreground" />
        </button>

        <!-- Upload Telegram History -->
        <button 
          v-if="isOwner"
          @click="handleAction('import')" 
          class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-foreground hover:bg-muted/80 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>{{ languageStore.t('آپلود تاریخچه تلگرام', 'Upload Telegram History') }}</span>
          <UploadCloudIcon class="size-3.5 text-muted-foreground" />
        </button>

        <!-- Divider -->
        <div v-if="isOwner" class="h-[0.8px] bg-border/60 my-0.5 mx-1" />

        <!-- Delete Topic -->
        <button 
          v-if="isOwner"
          @click="handleAction('delete')" 
          class="w-full text-start px-3 py-2 text-xs font-semibold rounded-xl text-destructive hover:bg-destructive/10 flex items-center justify-between cursor-pointer transition-all active:scale-[0.98]"
        >
          <span>{{ languageStore.t('حذف تاپیک', 'Delete Topic') }}</span>
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

.scale-up {
  transform-origin: top right;
}

@keyframes pop {
  0% { transform: scale(0.96); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.animate-menu-pop {
  animation: pop 0.15s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
</style>
