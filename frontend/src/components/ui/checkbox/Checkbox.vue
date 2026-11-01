<script setup lang="ts">
import { CheckIcon } from '@lucide/vue'
import { CheckboxIndicator, CheckboxRoot } from 'reka-ui'
import { cn } from '@/lib/utils'

const props = defineProps<{
  checked?: boolean | 'indeterminate'
  defaultChecked?: boolean
  disabled?: boolean
  required?: boolean
  name?: string
  value?: string
  id?: string
  class?: any
}>()

const emit = defineEmits<{
  (e: 'update:checked', value: boolean | 'indeterminate'): void
}>()
</script>

<template>
  <CheckboxRoot
    v-slot="slotProps"
    :model-value="checked"
    :default-value="defaultChecked"
    :disabled="disabled"
    :required="required"
    :name="name"
    :value="value"
    :id="id"
    @update:model-value="(val: boolean | 'indeterminate') => emit('update:checked', val)"
    data-slot="checkbox"
    :class="cn(
      'peer h-4 w-4 shrink-0 rounded-md border border-border bg-background p-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:border-primary data-[state=checked]:text-primary-foreground aria-invalid:border-destructive dark:aria-invalid:border-destructive/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 focus-visible:ring-3 aria-invalid:ring-3 flex items-center justify-center transition-colors',
      props.class
    )"
  >
    <CheckboxIndicator
      data-slot="checkbox-indicator"
      class="flex items-center justify-center text-current"
    >
      <slot v-bind="slotProps">
        <CheckIcon class="size-3" />
      </slot>
    </CheckboxIndicator>
  </CheckboxRoot>
</template>
