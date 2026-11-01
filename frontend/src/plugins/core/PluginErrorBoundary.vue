<template>
  <div 
    v-if="hasError" 
    class="p-6 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-3xl text-center space-y-4 my-4 shadow-sm"
    :dir="languageStore.dir"
  >
    <div class="w-12 h-12 rounded-2xl bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 mx-auto flex items-center justify-center text-xl shadow-xs">
      ⚠️
    </div>
    
    <div class="space-y-1.5">
      <h3 class="font-bold text-red-900 dark:text-red-200 text-base sm:text-lg">
        {{ languageStore.t('خطا در اجرای افزونه', 'Plugin Execution Error') }}
      </h3>
      <p class="text-xs sm:text-sm text-red-700 dark:text-red-400 max-w-md mx-auto leading-relaxed">
        {{ errorMessage || languageStore.t('افزونه با مشکلی مواجه شد اما سایر بخش‌های تفکر بدون مشکل فعال هستند.', 'This plugin encountered an issue, but the rest of Tafakor remains unaffected.') }}
      </p>
    </div>

    <!-- Collapsible Error Diagnostics -->
    <div v-if="errorDetails" class="text-start max-w-md mx-auto">
      <button 
        @click="showDetails = !showDetails"
        type="button"
        class="text-[11px] font-medium text-red-600 dark:text-red-400 underline underline-offset-2 cursor-pointer focus:outline-none"
      >
        {{ showDetails ? languageStore.t('بستن جزئیات فنی', 'Hide Details') : languageStore.t('مشاهده جزئیات خطا', 'Show Error Details') }}
      </button>
      <pre 
        v-if="showDetails" 
        class="mt-2 p-3 bg-red-100/60 dark:bg-red-900/40 rounded-xl text-[10px] font-mono text-red-900 dark:text-red-200 overflow-x-auto max-h-32 border border-red-200 dark:border-red-800/60 whitespace-pre-wrap"
      >{{ errorDetails }}</pre>
    </div>

    <!-- Actions -->
    <div class="pt-2 flex items-center justify-center gap-3">
      <button
        @click="resetError"
        type="button"
        class="px-4 py-2 bg-red-600 hover:bg-red-700 active:scale-95 text-white rounded-xl text-xs font-bold transition-all shadow-sm cursor-pointer"
      >
        {{ languageStore.t('تلاش مجدد', 'Retry') }}
      </button>
      <router-link
        to="/"
        class="px-4 py-2 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 rounded-xl text-xs font-semibold transition-all"
      >
        {{ languageStore.t('بازگشت به خانه', 'Back to Home') }}
      </router-link>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  pluginName?: string
}>(), {
  pluginName: 'Plugin'
})

const hasError = ref(false)
const errorMessage = ref('')
const errorDetails = ref('')
const showDetails = ref(false)

onErrorCaptured((err: any, _instance, info) => {
  console.error(`[PluginErrorBoundary] Error in plugin '${props.pluginName}':`, err, info)
  hasError.value = true
  errorMessage.value = err?.message || 'Unknown plugin execution failure.'
  errorDetails.value = `${err?.stack || err?.toString() || ''}\nInfo: ${info || ''}`
  // Return false to prevent bubbling up and crashing the root Vue tree
  return false
})

const resetError = () => {
  hasError.value = false
  errorMessage.value = ''
  errorDetails.value = ''
  showDetails.value = false
}
</script>
