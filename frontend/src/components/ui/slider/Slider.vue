<script setup lang="ts">
import type { SliderRootEmits, SliderRootProps } from "reka-ui"
import type { HTMLAttributes } from "vue"
import { reactiveOmit } from "@vueuse/core"
import {
  SliderRange,
  SliderRoot,
  SliderThumb,
  SliderTrack,
  useForwardPropsEmits,
} from "reka-ui"
import { cn } from "@/lib/utils"

defineOptions({
  inheritAttrs: false,
})

const props = defineProps<
  SliderRootProps & { class?: HTMLAttributes["class"] }
>()
const emits = defineEmits<SliderRootEmits>()

const delegatedProps = reactiveOmit(props, "class")
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <SliderRoot
    data-slot="slider"
    :class="
      cn(
        'relative flex w-full touch-none select-none items-center data-[orientation=vertical]:h-full data-[orientation=vertical]:w-auto data-[orientation=vertical]:flex-col',
        props.class,
      )
    "
    v-bind="{ ...$attrs, ...forwarded }"
  >
    <SliderTrack
      data-slot="slider-track"
      class="bg-muted relative h-1.5 w-full grow overflow-hidden rounded-full data-[orientation=vertical]:w-1.5"
    >
      <SliderRange
        data-slot="slider-range"
        class="bg-primary absolute h-full data-[orientation=vertical]:w-full"
      />
    </SliderTrack>
    <SliderThumb
      v-for="(_, key) in (modelValue ?? defaultValue ?? [0])"
      :key="key"
      data-slot="slider-thumb"
      class="border-primary bg-background ring-ring/50 block size-4 rounded-full border shadow-xs transition-colors hover:scale-110 active:scale-95 focus-visible:outline-none focus-visible:ring-3 disabled:pointer-events-none disabled:opacity-50 cursor-grab active:cursor-grabbing"
    />
  </SliderRoot>
</template>
