<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
    :class="variantClasses"
  >
    <BaseSpinner v-if="loading" size="sm" />
    <slot v-else />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import BaseSpinner from './BaseSpinner.vue'

const props = defineProps({
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' }, // primary | danger | outline
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false }
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500'
    case 'danger':
      return 'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500'
    case 'outline':
      return 'border border-gray-300 text-gray-700 hover:bg-gray-100 focus:ring-indigo-500'
    default:
      return 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500'
  }
})
</script>