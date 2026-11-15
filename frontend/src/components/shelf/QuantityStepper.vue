<script setup lang="ts">
import { computed } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { MinusIcon, PlusIcon } from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    modelValue: number
    min?: number
    max?: number
    label?: string
    unit?: string
    hint?: string
    compact?: boolean
    disabled?: boolean
  }>(),
  {
    min: 1,
    max: 10000,
    unit: '',
    hint: '',
    compact: false,
    disabled: false,
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
}>()

const languageStore = useLanguageStore()

const resolvedUnit = computed(() => props.unit || languageStore.t('جلد', 'copies'))

const clamp = (raw: number): number => {
  const floored = Math.floor(Number.isFinite(raw) ? raw : props.min)
  const lower = Math.max(props.min, floored)
  return props.max !== undefined ? Math.min(props.max, lower) : lower
}

const decrement = () => {
  if (props.disabled) return
  emit('update:modelValue', clamp(props.modelValue - 1))
}

const increment = () => {
  if (props.disabled) return
  emit('update:modelValue', clamp(props.modelValue + 1))
}

const handleInput = (val: string | number) => {
  const parsed = Number(String(val).replace(/[^\d]/g, ''))
  if (!parsed) return
  emit('update:modelValue', clamp(parsed))
}

const handleBlur = (event: FocusEvent) => {
  const target = event.target as HTMLInputElement | null
  const parsed = Number(target?.value || '')
  const next = clamp(parsed || props.min)
  emit('update:modelValue', next)
  if (target) {
    target.value = String(next)
  }
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <div v-if="label || hint" class="flex items-center justify-between gap-2">
      <Label v-if="label" class="text-xs font-bold">
        {{ label }}
      </Label>
      <span v-if="hint" class="text-[11px] text-muted-foreground">
        {{ hint }}
      </span>
    </div>

    <div
      class="flex items-center justify-between gap-2 rounded-2xl border border-border/60 bg-background/70 px-2.5"
      :class="compact ? 'py-1.5' : 'py-2'"
    >
      <div class="flex items-center gap-1.5">
        <Button
          type="button"
          size="icon-xs"
          variant="outline"
          class="rounded-xl"
          :disabled="disabled || modelValue <= min"
          @click="decrement"
        >
          <MinusIcon class="size-3.5" />
        </Button>

        <Input
          :model-value="modelValue"
          type="number"
          inputmode="numeric"
          :min="min"
          :max="max"
          dir="ltr"
          :disabled="disabled"
          class="w-16 h-8 text-center font-bold text-xs rounded-xl bg-input/50 border-transparent px-1.5"
          @update:model-value="handleInput"
          @blur="handleBlur"
        />

        <Button
          type="button"
          size="icon-xs"
          variant="outline"
          class="rounded-xl"
          :disabled="disabled || (max !== undefined && modelValue >= max)"
          @click="increment"
        >
          <PlusIcon class="size-3.5" />
        </Button>
      </div>

      <span class="text-xs font-bold text-muted-foreground shrink-0">
        {{ languageStore.n(modelValue) }} {{ resolvedUnit }}
      </span>
    </div>
  </div>
</template>

