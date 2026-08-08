<script setup lang="ts">
import { computed } from 'vue'
import { ConfigProvider } from 'reka-ui'
import { useDark, useToggle } from '@vueuse/core'
import { 
  CheckCircle2Icon,
  AlertCircleIcon,
  AlertTriangleIcon,
  InfoIcon
} from '@lucide/vue'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import { useLanguageStore } from '@/stores/languageStore'
import ChangelogModal from '@/components/ChangelogModal.vue'
import LoginCard from '@/components/LoginCard.vue'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'

// Dark/Light theme manager via VueUse
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleDark = useToggle(isDark)

const toastStore = useToastStore()
const userStore = useUserStore()
const languageStore = useLanguageStore()

const isToastActive = computed(() => toastStore.isToastActive)
const toastMsg = computed(() => toastStore.toastMsg)

const toastConfig = computed(() => {
  switch (toastStore.toastType) {
    case 'success':
      return {
        bgClass: 'bg-background/95 border-border shadow-lg text-foreground',
        iconClass: 'text-emerald-500',
        icon: CheckCircle2Icon
      }
    case 'error':
      return {
        bgClass: 'bg-background/95 border-destructive/40 shadow-lg text-destructive',
        iconClass: 'text-destructive',
        icon: AlertCircleIcon
      }
    case 'warning':
      return {
        bgClass: 'bg-background/95 border-amber-500/30 shadow-lg text-foreground',
        iconClass: 'text-amber-500',
        icon: AlertTriangleIcon
      }
    case 'info':
    default:
      return {
        bgClass: 'bg-background/95 border-border shadow-lg text-foreground',
        iconClass: 'text-blue-500',
        icon: InfoIcon
      }
  }
})

const handleLoginStateChange = (state: string) => {
  if (state === 'success') {
    userStore.isLoginModalOpen = false
    userStore.loadProfile()
    toastStore.triggerToast(languageStore.t('ورود با موفقیت انجام شد.', 'Logged in successfully.'), 'success')
  }
}
</script>

<template>
  <ConfigProvider :dir="languageStore.dir">
    <div 
      class="min-h-screen bg-background text-foreground font-sans transition-colors duration-300 flex flex-col relative" 
      :dir="languageStore.dir"
    >
      
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
          class="fixed top-6 left-1/2 -translate-x-1/2 z-[100] px-4 w-full max-w-[500px] pointer-events-none"
        >
          <div :class="['w-full text-xs font-semibold px-4 py-3 rounded-2xl border flex items-center gap-3 pointer-events-auto transition-all duration-300 shadow-md', toastConfig.bgClass]">
            <component :is="toastConfig.icon" :class="['size-4.5 shrink-0', toastConfig.iconClass]" />
            <span class="whitespace-nowrap overflow-hidden text-ellipsis">{{ toastMsg }}</span>
          </div>
        </div>
      </transition>

      <!-- Changelog Modal (Global) -->
      <ChangelogModal />

      <!-- Login Dialog Modal (Global) -->
      <Dialog :open="userStore.isLoginModalOpen" @update:open="(val) => userStore.isLoginModalOpen = val">
        <DialogContent 
          :show-close-button="true" 
          class="max-w-[380px] p-0 overflow-hidden flex flex-col text-start rounded-3xl transition-all duration-300 focus-within:max-sm:top-[20%] focus-within:max-sm:-translate-y-[20%]" 
          :dir="languageStore.dir"
          @pointer-down-outside="(e) => e.preventDefault()"
          @escape-key-down="(e) => e.preventDefault()"
        >
          <DialogTitle class="sr-only">{{ languageStore.t('ورود به حساب کاربری', 'User Login') }}</DialogTitle>
          <DialogDescription class="sr-only">{{ languageStore.t('ورود به حساب کاربری تفکر', 'Tafakor User Login') }}</DialogDescription>
          <LoginCard @stateChange="handleLoginStateChange" />
        </DialogContent>
      </Dialog>

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
  transition: opacity 0.3s ease, transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-slide-enter-from {
  opacity: 0;
  transform: translate(-50%, -12px);
}

.toast-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}
</style>