<script setup lang="ts">
import { computed } from 'vue'
import { ConfigProvider } from 'reka-ui'
import { useDark, useToggle } from '@vueuse/core'
import { 
  SunIcon, 
  MoonIcon,
  CheckCircle2Icon
} from '@lucide/vue'
import { useToastStore } from '@/stores/toastStore'

// Dark/Light theme manager via VueUse
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleDark = useToggle(isDark)

const toastStore = useToastStore()
const isToastActive = computed(() => toastStore.isToastActive)
const toastMsg = computed(() => toastStore.toastMsg)
</script>

<template>
  <ConfigProvider dir="rtl">
    <div class="min-h-screen bg-background text-foreground font-sans transition-colors duration-300 flex flex-col relative" dir="rtl">
      
      <!-- Main Application Container -->
      <main class="w-full flex-1 flex flex-col items-center p-4 sm:p-6">
        <router-view v-slot="{ Component }">
          <transition 
            name="fade" 
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </main>



      <!-- Dynamic Premium Toast Notification (Global) -->
      <transition name="toast-slide">
        <div 
          v-if="isToastActive" 
          class="fixed top-6 inset-x-0 flex justify-center z-50 px-6 pointer-events-none"
        >
          <div class="bg-primary text-primary-foreground text-xs font-bold px-4 py-2.5 rounded-xl shadow-lg border border-primary/20 flex items-center gap-2 pointer-events-auto">
            <CheckCircle2Icon class="size-4 text-primary-foreground" />
            <span>{{ toastMsg }}</span>
          </div>
        </div>
      </transition>

    </div>
  </ConfigProvider>
</template>

<style>
/* Smooth fade transitions for page swaps */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Toast Animation */
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-slide-enter-from {
  transform: translateY(-20px);
  opacity: 0;
}

.toast-slide-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>