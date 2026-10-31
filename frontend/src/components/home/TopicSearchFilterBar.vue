<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { SearchIcon, XIcon, BotIcon, MessageSquareIcon, LayersIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import type { TopicFilterType } from '@/types/topic'

const props = withDefaults(defineProps<{
  searchQuery?: string
  activeFilter?: TopicFilterType
  totalCount?: number
  filteredCount?: number
}>(), {
  searchQuery: '',
  activeFilter: 'all',
  totalCount: 0,
  filteredCount: 0
})

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'update:search-query', val: string): void
  (e: 'update:activeFilter', val: TopicFilterType): void
  (e: 'update:active-filter', val: TopicFilterType): void
  (e: 'clearSearch'): void
  (e: 'clear-search'): void
}>()

const languageStore = useLanguageStore()
const searchInputRef = ref<HTMLInputElement | null>(null)

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:searchQuery', target.value)
  emit('update:search-query', target.value)
}

const handleClear = async () => {
  emit('update:searchQuery', '')
  emit('update:search-query', '')
  emit('clearSearch')
  emit('clear-search')
  await nextTick()
  if (searchInputRef.value) {
    searchInputRef.value.focus()
  }
}

const setFilter = (filter: TopicFilterType) => {
  emit('update:activeFilter', filter)
  emit('update:active-filter', filter)
}

const filterCountLabel = computed(() => {
  const count = props.filteredCount ?? 0
  return languageStore.t(`${languageStore.n(count)} مورد یافت شد`, `${count} found`)
})
</script>

<template>
  <div class="w-full flex flex-col gap-2.5 select-none font-sans" :dir="languageStore.dir">
    <!-- Top Search Input Container (Flutter: 46px height, 14px radius, 0.8px border) -->
    <div
      class="w-full h-[46px] rounded-[14px] bg-card/80 dark:bg-card/50 backdrop-blur-md border border-border/70 dark:border-border/60 shadow-[0_2px_8px_rgba(0,0,0,0.02)] dark:shadow-[0_2px_8px_rgba(0,0,0,0.15)] flex items-center px-3.5 gap-2.5 transition-all focus-within:border-primary/50 focus-within:shadow-sm"
    >
      <!-- Search Icon -->
      <SearchIcon class="size-4 text-muted-foreground/70 shrink-0 transition-colors" />

      <!-- Input Field -->
      <input
        ref="searchInputRef"
        :value="searchQuery"
        @input="handleInput"
        type="text"
        :placeholder="languageStore.t('جستجو در عنوان یا متن تاپیک‌ها...', 'Search topics by title or description...')"
        class="flex-1 bg-transparent border-0 outline-none text-xs sm:text-[13px] font-semibold text-foreground placeholder:text-muted-foreground/50 w-full font-sans focus:outline-none focus:ring-0 p-0 text-start"
      />

      <!-- Clear Button (Shown only when there is query text) -->
      <button
        v-if="searchQuery"
        @click="handleClear"
        type="button"
        class="size-6 rounded-full bg-muted/80 hover:bg-muted text-muted-foreground hover:text-foreground flex items-center justify-center transition-all cursor-pointer border-0 active:scale-90 shrink-0"
        :title="languageStore.t('پاک کردن متن', 'Clear text')"
      >
        <XIcon class="size-3" />
      </button>

      <!-- Topic Counter Pill -->
      <div
        v-if="!searchQuery && (totalCount ?? 0) > 0"
        class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-muted/60 text-muted-foreground/80 shrink-0 hidden sm:flex items-center"
      >
        <span>{{ languageStore.n(totalCount ?? 0) }}</span>
        <span class="ms-1">{{ languageStore.t('تاپیک', 'topics') }}</span>
      </div>
    </div>

    <!-- Filter Chips Row (Apple segmented filter style) -->
    <div class="flex items-center justify-between gap-1.5 px-0.5">
      <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
        <!-- Filter: All -->
        <button
          type="button"
          @click="setFilter('all')"
          :class="[
            'h-7 px-3 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all duration-200 cursor-pointer active:scale-95 border select-none',
            activeFilter === 'all'
              ? 'bg-primary text-primary-foreground border-primary shadow-xs'
              : 'bg-card/60 dark:bg-card/40 text-muted-foreground hover:text-foreground border-border/60 hover:bg-muted/40'
          ]"
        >
          <LayersIcon class="size-3 shrink-0" />
          <span>{{ languageStore.t('همه تاپیک‌ها', 'All Topics') }}</span>
        </button>

        <!-- Filter: Bots Active -->
        <button
          type="button"
          @click="setFilter('bots')"
          :class="[
            'h-7 px-3 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all duration-200 cursor-pointer active:scale-95 border select-none',
            activeFilter === 'bots'
              ? 'bg-primary text-primary-foreground border-primary shadow-xs'
              : 'bg-card/60 dark:bg-card/40 text-muted-foreground hover:text-foreground border-border/60 hover:bg-muted/40'
          ]"
        >
          <BotIcon class="size-3 shrink-0" />
          <span>{{ languageStore.t('متصل به ربات', 'With Bots') }}</span>
        </button>

        <!-- Filter: Unread / Has Posts -->
        <button
          type="button"
          @click="setFilter('unread')"
          :class="[
            'h-7 px-3 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all duration-200 cursor-pointer active:scale-95 border select-none',
            activeFilter === 'unread'
              ? 'bg-primary text-primary-foreground border-primary shadow-xs'
              : 'bg-card/60 dark:bg-card/40 text-muted-foreground hover:text-foreground border-border/60 hover:bg-muted/40'
          ]"
        >
          <MessageSquareIcon class="size-3 shrink-0" />
          <span>{{ languageStore.t('دارای پیام جدید', 'Has Unread') }}</span>
        </button>
      </div>

      <!-- Active Filter Count indicator -->
      <span
        v-if="searchQuery || activeFilter !== 'all'"
        class="text-[10px] font-bold text-muted-foreground/70 shrink-0 whitespace-nowrap"
      >
        {{ filterCountLabel }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
