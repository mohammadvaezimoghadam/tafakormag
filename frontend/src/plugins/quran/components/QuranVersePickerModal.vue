<template>
  <QuranVersePickerDialog
    :on-insert="onInsert"
    @insert="markdown => $emit('insert', markdown)"
    @close="$emit('close')"
  />
</template>

<script setup lang="ts">
import QuranVersePickerDialog from './QuranVersePickerDialog.vue'

defineProps<{
  onInsert?: (markdown: string) => void
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'insert', markdown: string): void
}>()
</script>
