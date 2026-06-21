<script setup lang="ts">
import { ChevronLeftIcon } from '@lucide/vue'
import { Badge } from '@/components/ui/badge'

const props = withDefaults(defineProps<{
  title: string
  description: string
  icon: any // Accepts a Lucide icon component reference
  badgeText?: string
  badgeVariant?: 'default' | 'secondary' | 'destructive'
}>(), {
  badgeVariant: 'default'
})

const emit = defineEmits<{
  (e: 'click'): void
}>()
</script>

<template>
  <button
    @click="emit('click')"
    class="w-full flex items-center justify-start p-3.5 rounded-2xl bg-card/45 backdrop-blur-md border border-border/40 hover:bg-muted/40 hover:border-primary/20 transition-all duration-200 cursor-pointer select-none text-right relative active:scale-[0.995] group gap-3.5 outline-none font-inherit text-foreground"
    dir="rtl"
  >
    <!-- Right side: Icon Container (No border, lighter bg) -->
    <div class="size-10 rounded-xl bg-primary/[0.03] flex items-center justify-center text-primary shrink-0 transition-transform duration-200 group-hover:scale-102">
      <component :is="icon" class="size-5 shrink-0" />
    </div>

    <!-- Middle: Title & Description -->
    <div class="flex-1 flex flex-col text-right gap-1 min-w-0">
      <span class="text-xs font-bold text-foreground truncate select-all leading-none">
        {{ title }}
      </span>
      <span class="text-[10px] text-muted-foreground truncate leading-relaxed">
        {{ description }}
      </span>
    </div>

    <!-- Left side: Badge & Arrow indicator -->
    <div class="flex items-center gap-2 shrink-0">
      <!-- Badge element -->
      <Badge
        v-if="badgeText"
        :variant="badgeVariant"
        class="text-[8.5px] font-bold px-2 h-4.5"
      >
        {{ badgeText }}
      </Badge>

      <!-- RTL pointing back chevron -->
      <ChevronLeftIcon class="size-4 text-muted-foreground/60 transition-transform duration-200 group-hover:-translate-x-0.5" />
    </div>
  </button>
</template>
