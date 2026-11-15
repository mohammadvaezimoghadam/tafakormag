<script setup lang="ts">
import { ref, watch } from 'vue'
import { searchBookTitles } from '../api'
import type { BookTitleItem } from '../types'
import { useLanguageStore } from '@/stores/languageStore'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'insert', text: string): void
}>()

const languageStore = useLanguageStore()
const query = ref('')
const results = ref<BookTitleItem[]>([])
const isLoading = ref(false)
let debounceTimeout: any = null

watch(query, (val) => {
  clearTimeout(debounceTimeout)
  if (!val.trim()) {
    results.value = []
    return
  }
  debounceTimeout = setTimeout(async () => {
    isLoading.value = true
    try {
      results.value = await searchBookTitles(val.trim())
    } catch {
      results.value = []
    } finally {
      isLoading.value = false
    }
  }, 300)
})

const selectTitle = (book: BookTitleItem) => {
  const parts = [`> 📖 **معرفی کتاب: ${book.title}**`]
  if (book.author) parts.push(`> *پدیدآور: ${book.author}*`)
  if (book.publisher) parts.push(`> *ناشر: ${book.publisher}*`)
  parts.push(`\n[مشاهده نسخه و گردش در تفاخر شاپ](/apps/shop)`)
  const formattedText = parts.join('\n')
  emit('insert', formattedText)
  emit('update:open', false)
  query.value = ''
  results.value = []
}

const close = () => {
  emit('update:open', false)
  query.value = ''
  results.value = []
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs select-none">
    <div
      class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col max-h-[85vh] text-zinc-900 dark:text-zinc-100"
      dir="rtl"
    >
      <!-- Header -->
      <div class="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between bg-zinc-50 dark:bg-zinc-800/40">
        <div>
          <h3 class="text-xs sm:text-sm font-bold">درج معرفی کتاب در متن یادداشت</h3>
          <p class="text-[11px] text-zinc-500">جستجو در شناسنامه کتب تفاخر</p>
        </div>
        <button
          @click="close"
          type="button"
          class="size-7 rounded-lg flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-sm cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- Search Input -->
      <div class="p-3 border-b border-zinc-100 dark:border-zinc-800">
        <input
          v-model="query"
          placeholder="نام کتاب یا نویسنده را بنویسید..."
          class="w-full px-3 py-2 text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50 focus:outline-hidden focus:border-zinc-900 dark:focus:border-zinc-400"
        />
      </div>

      <!-- Results List -->
      <div class="flex-1 overflow-y-auto p-3 space-y-1.5 min-h-[160px] max-h-[300px]">
        <div v-if="isLoading" class="text-center py-6 text-xs text-zinc-400">
          در حال جستجو...
        </div>

        <div v-else-if="results.length === 0 && query.trim()" class="text-center py-6 text-xs text-zinc-400">
          کتابی یافت نشد.
        </div>

        <div v-else-if="results.length === 0" class="text-center py-6 text-xs text-zinc-400">
          عنوان کتاب مورد نظر را برای ارجاع در یادداشت جستجو فرمایید.
        </div>

        <button
          v-for="b in results"
          :key="b.id"
          @click="selectTitle(b)"
          type="button"
          class="w-full text-start p-2.5 rounded-lg border border-transparent hover:border-zinc-200 dark:hover:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 transition-all flex items-center justify-between cursor-pointer"
        >
          <div class="truncate">
            <h4 class="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
              {{ b.title }}
            </h4>
            <p class="text-[10px] text-zinc-500 truncate">
              {{ b.author }} <span v-if="b.publisher">• {{ b.publisher }}</span>
            </p>
          </div>
          <span class="text-[11px] text-zinc-400 shrink-0">انتخاب ↵</span>
        </button>
      </div>
    </div>
  </div>
</template>

