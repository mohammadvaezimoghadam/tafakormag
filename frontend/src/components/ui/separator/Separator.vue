<script setup lang="ts">
import type { SeparatorProps } from "reka-ui"
import type { HTMLAttributes } from "vue"
import { Separator } from "reka-ui"
import { cn } from "@/lib/utils"

const props = withDefaults(
  defineProps<SeparatorProps & { class?: HTMLAttributes["class"] }>(),
  {
    orientation: "horizontal",
    decorative: true,
  }
)
</script>

<template>
  <Separator
    data-slot="separator-root"
    :decorative="decorative"
    :orientation="orientation"
    :class="
      cn(
        'shrink-0 bg-border/60 transition-colors duration-300',
        orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]',
        props.class
      )
    "
  />
</template>
