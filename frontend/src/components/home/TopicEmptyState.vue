<script setup lang="ts">
import { SearchXIcon, MessageSquareDashedIcon, PlusIcon, RotateCcwIcon } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { useLanguageStore } from '@/stores/languageStore'

defineProps<{
  isSearching: boolean
  searchQuery?: string
}>()

const emit = defineEmits<{
  (e: 'resetSearch'): void
  (e: 'createTopic'): void
}>()

const languageStore = useLanguageStore()
</script>

<template>
  <div
    class="w-full flex flex-col items-center justify-center py-12 px-4 rounded-3xl bg-card/40 dark:bg-card/20 border border-border/60 text-center select-none"
    :dir="languageStore.dir"
  >
    <!-- Searching Empty State -->
    <template v-if="isSearching">
      <div class="size-14 rounded-2xl bg-muted/60 border border-border/70 flex items-center justify-center text-muted-foreground mb-3.5 shadow-xs">
        <SearchXIcon class="size-7 stroke-[1.75]" />
      </div>

      <h3 class="text-sm font-bold text-foreground mb-1">
        {{ languageStore.t('تاپیکی یافت نشد', 'No topics found') }}
      </h3>

      <p class="text-xs text-muted-foreground max-w-[280px] leading-relaxed mb-4">
        {{ languageStore.t(
          `هیچ تاپیکی با عبارت «${searchQuery}» یا فیلتر جاری همخوانی ندارد.`,
          `No topics match "${searchQuery}" or the current filter.`
        ) }}
      </p>

      <Button
        variant="outline"
        size="sm"
        @click="emit('resetSearch')"
        class="rounded-xl text-xs font-bold h-8.5 gap-1.5 cursor-pointer shadow-xs active:scale-95"
      >
        <RotateCcwIcon class="size-3.5" />
        <span>{{ languageStore.t('پاک کردن فیلترها', 'Clear filters') }}</span>
      </Button>
    </template>

    <!-- Initial / No Topics Empty State -->
    <template v-else>
      <div class="size-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-3.5 shadow-xs">
        <MessageSquareDashedIcon class="size-7 stroke-[1.75]" />
      </div>

      <h3 class="text-sm font-bold text-foreground mb-1">
        {{ languageStore.t('هنوز تاپیکی ایجاد نشده است', 'No topics created yet') }}
      </h3>

      <p class="text-xs text-muted-foreground max-w-[280px] leading-relaxed mb-4">
        {{ languageStore.t(
          'برای شروع گفتگو و انتشار مطالب، اولین تاپیک را بسازید.',
          'Create the first topic to start discussions and publish content.'
        ) }}
      </p>

      <Button
        variant="default"
        size="sm"
        @click="emit('createTopic')"
        class="rounded-xl text-xs font-bold h-8.5 gap-1.5 cursor-pointer shadow-xs active:scale-95"
      >
        <PlusIcon class="size-4" />
        <span>{{ languageStore.t('ایجاد تاپیک جدید', 'Create New Topic') }}</span>
      </Button>
    </template>
  </div>
</template>
