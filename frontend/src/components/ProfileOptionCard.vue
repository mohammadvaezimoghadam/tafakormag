<script setup lang="ts">
import { ChevronLeftIcon, ChevronRightIcon } from '@lucide/vue'
import { Badge } from '@/components/ui/badge'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

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
    class="w-full flex items-center justify-start p-3.5 rounded-2xl bg-card/60 dark:bg-card/40 backdrop-blur-xl border border-border/70 dark:border-border/60 hover:bg-muted/50 hover:border-border shadow-[0_2px_8px_rgba(0,0,0,0.02)] transition-all duration-200 cursor-pointer select-none relative active:scale-[0.99] group gap-3.5 outline-none font-inherit text-foreground"
    :dir="languageStore.dir"
  >
    <!-- Icon Container -->
    <div class="size-10 rounded-xl bg-primary/10 dark:bg-primary/15 border border-primary/20 flex items-center justify-center text-primary shrink-0 transition-transform duration-200 group-hover:scale-105">
      <component :is="icon" class="size-5 shrink-0" />
    </div>

    <!-- Title & Description -->
    <div class="flex-1 flex flex-col text-start gap-1 min-w-0">
      <span class="text-xs font-bold text-foreground truncate select-all leading-none">
        {{ title }}
      </span>
      <span class="text-[10px] text-muted-foreground truncate leading-relaxed">
        {{ description }}
      </span>
    </div>

    <!-- Badge & Arrow indicator -->
    <div class="flex items-center gap-2 shrink-0">
      <!-- Badge element -->
      <Badge
        v-if="badgeText"
        :variant="badgeVariant"
        class="text-[9px] font-bold px-2 py-0.5 rounded-lg border border-border/40"
      >
        {{ badgeText }}
      </Badge>

      <!-- Dynamic chevron pointing backward based on language direction -->
      <component 
        :is="languageStore.isFa ? ChevronLeftIcon : ChevronRightIcon" 
        class="size-4 text-muted-foreground/60 transition-transform duration-200"
        :class="[languageStore.isFa ? 'group-hover:-translate-x-0.5' : 'group-hover:translate-x-0.5']"
      />
    </div>
  </button>
</template>
