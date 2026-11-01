<script setup lang="ts">
import { computed } from 'vue'
import { parseMarkdownToHtml } from '@/utils/textFormatter'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<{
  content?: string
  text?: string
  className?: string
}>(), {
  content: '',
  text: '',
  className: ''
})

const parsedContent = computed(() => parseMarkdownToHtml(props.content || props.text || ''))
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

:deep(strong) {
  font-weight: 800 !important;
  color: inherit;
}

:deep(em) {
  font-style: italic;
  display: inline;
  font-synthesis: style;
  letter-spacing: 0.01em;
}

:deep(u) {
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1.5px;
}

:deep(del) {
  text-decoration: line-through;
  opacity: 0.75;
}
</style>
