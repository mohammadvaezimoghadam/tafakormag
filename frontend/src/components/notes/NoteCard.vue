<template>
  <div
    @click="$emit('edit', note)"
    class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 active:scale-[0.98] transition-transform cursor-pointer relative"
  >
    <div class="flex items-start justify-between mb-2">
      <h3 v-if="note.title" class="font-semibold text-gray-800 text-base line-clamp-1">{{ note.title }}</h3>
      <div class="flex items-center gap-2 ml-auto">
        <span v-if="note.is_sent_to_telegram" class="text-blue-500" title="ارسال شده در تلگرام">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.19.19 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.87-1.25 4.79-2.08 5.76-2.47 2.74-1.14 3.31-1.34 3.68-1.34.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg>
        </span>
        <span v-if="note.is_sent_to_bale" class="text-emerald-500" title="ارسال شده در بله">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-4-4 1.41-1.41L11 14.17l6.59-6.59L19 9l-8 8z"/></svg>
        </span>
      </div>
    </div>
    <p class="text-sm text-gray-600 line-clamp-2 mb-3">{{ note.content }}</p>
    <div class="flex items-center justify-between text-xs text-gray-400">
      <span>{{ relativeTime(note.created_at) }}</span>
      <button
        @click.stop="$emit('delete', note.id)"
        class="text-red-400 hover:text-red-600 p-1 rounded-lg hover:bg-red-50 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { faIR as fa } from 'date-fns/locale/fa-IR'

const props = defineProps({
  note: { type: Object, required: true }
})

defineEmits(['edit', 'delete'])

const relativeTime = (date) => {
  if (!date) return ''
  return formatDistanceToNow(new Date(date), { addSuffix: true, locale: fa })
}
</script>