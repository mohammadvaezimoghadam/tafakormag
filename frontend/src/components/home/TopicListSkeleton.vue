<script setup lang="ts">
import { Skeleton } from '@/components/ui/skeleton'

withDefaults(defineProps<{
  count?: number
}>(), {
  count: 4
})
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5 w-full animate-pulse select-none" aria-busy="true" aria-label="Loading topics">
    <div
      v-for="i in count"
      :key="'topic-skel-' + i"
      class="w-full flex items-center gap-3.5 p-3.5 rounded-2xl bg-card/60 dark:bg-card/40 border border-border/60 shadow-[0_2px_8px_rgba(0,0,0,0.02)] text-start"
    >
      <!-- Avatar Skeleton -->
      <Skeleton class="size-11 rounded-2xl shrink-0 bg-muted/80" />

      <!-- Center Info Skeleton -->
      <div class="flex-1 flex flex-col gap-2 min-w-0">
        <div class="flex items-center gap-2">
          <Skeleton class="h-4 w-28 rounded-md bg-muted/80" />
          <Skeleton class="h-3.5 w-12 rounded-md bg-muted/60" />
        </div>
        <Skeleton class="h-3 w-44 rounded-md bg-muted/60" />
      </div>

      <!-- Trailing Skeleton -->
      <div class="flex flex-col items-end shrink-0 gap-2 ms-1">
        <Skeleton class="h-3 w-10 rounded-md bg-muted/60" />
        <Skeleton class="size-5 rounded-full bg-muted/70" />
      </div>
    </div>
  </div>
</template>
