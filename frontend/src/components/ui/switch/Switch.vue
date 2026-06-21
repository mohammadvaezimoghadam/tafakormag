<script setup lang="ts">
import { SwitchRoot, SwitchThumb } from "reka-ui"
import { cn } from "@/lib/utils"

const props = withDefaults(defineProps<{
  checked?: boolean
  defaultChecked?: boolean
  disabled?: boolean
  required?: boolean
  name?: string
  value?: string
  id?: string
  class?: any
  size?: "sm" | "default"
}>(), {
  size: "default",
})

const emit = defineEmits<{
  (e: 'update:checked', value: boolean): void
}>()
</script>

<template>
  <SwitchRoot
    :model-value="checked"
    :default-value="defaultChecked"
    :disabled="disabled"
    :required="required"
    :name="name"
    :value="value"
    :id="id"
    @update:model-value="(val: boolean) => emit('update:checked', val)"
    data-slot="switch"
    :class="cn(
      'peer inline-flex shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent p-0 justify-start transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-muted/80 aria-invalid:border-destructive dark:aria-invalid:border-destructive/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 focus-visible:ring-3 aria-invalid:ring-3',
      size === 'default' ? 'h-6 w-11' : 'h-4 w-7',
      props.class,
    )"
  >
    <SwitchThumb
      data-slot="switch-thumb"
      :class="cn(
        'pointer-events-none block rounded-full bg-background shadow-lg ring-0 transition-transform dark:data-[state=checked]:bg-background',
        size === 'default' 
          ? 'h-5 w-5 data-[state=checked]:translate-x-5 rtl:data-[state=checked]:-translate-x-5' 
          : 'h-3 w-3 data-[state=checked]:translate-x-3 rtl:data-[state=checked]:-translate-x-3'
      )"
    />
  </SwitchRoot>
</template>
