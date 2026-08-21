<script setup lang="ts">
import { computed } from 'vue'
import { parseMarkdownToHtml } from '@/utils/textFormatter'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<{
  content?: string
  className?: string
}>(), {
  content: '',
  className: ''
})

const parsedContent = computed(() => parseMarkdownToHtml(props.content || ''))
</script>

<template>
  <div 
    :class="cn('formatted-text-content break-words leading-relaxed select-text text-start', props.className)"
    v-html="parsedContent"
  />
</template>

<style scoped>
/* انیمیشن و بهینه‌سازی تایپوگرافی برای تگ‌های داخلی */
:deep(blockquote) {
  position: relative;
}

:deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  direction: ltr;
  unicode-bidi: embed;
}
</style>
