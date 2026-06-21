import { ref } from 'vue'
import { defineStore } from 'pinia'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export const useToastStore = defineStore('toast', () => {
  const toastMsg = ref('')
  const isToastActive = ref(false)
  const toastType = ref<ToastType>('success')

  const triggerToast = (message: string, type: ToastType = 'success') => {
    toastMsg.value = message
    toastType.value = type
    isToastActive.value = true
    setTimeout(() => {
      isToastActive.value = false
    }, 3000)
  }

  return {
    toastMsg,
    isToastActive,
    toastType,
    triggerToast
  }
})
