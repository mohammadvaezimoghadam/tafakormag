<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { PlusIcon } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { useTopicStore, type Topic } from '@/stores/topicStore'
import { useLanguageStore } from '@/stores/languageStore'
import TopicCard from '@/components/TopicCard.vue'
import TopicSearchFilterBar from './TopicSearchFilterBar.vue'
import type { TopicFilterType } from '@/types/topic'
import TopicListSkeleton from './TopicListSkeleton.vue'
import TopicEmptyState from './TopicEmptyState.vue'

const props = withDefaults(defineProps<{
  externalSearchQuery?: string
}>(), {
  externalSearchQuery: ''
})

const emit = defineEmits<{
  (e: 'selectTopic', topic: Topic): void
  (e: 'select-topic', topic: Topic): void
  (e: 'createTopic'): void
  (e: 'create-topic'): void
  (e: 'update:externalSearchQuery', val: string): void
  (e: 'update:external-search-query', val: string): void
}>()

const topicStore = useTopicStore()
const languageStore = useLanguageStore()
const { topics, loading } = storeToRefs(topicStore)

// Internal Search & Filter States
const internalSearchQuery = ref('')
const activeFilter = ref<TopicFilterType>('all')

// Effective search query: combine external (from header) and internal (from search bar)
const effectiveSearchQuery = computed({
  get: () => props.externalSearchQuery || internalSearchQuery.value,
  set: (val: string) => {
    internalSearchQuery.value = val
    emit('update:externalSearchQuery', val)
  }
})

// Filtered topics computation
const filteredTopics = computed<Topic[]>(() => {
  const query = effectiveSearchQuery.value.toLowerCase().trim()
  const filter = activeFilter.value

  return topics.value.filter((topic) => {
    // 1. Bot & Unread status filters
    if (filter === 'bots') {
      const hasBot = Boolean(topic.telegram_bot_active || topic.bale_bot_active)
      if (!hasBot) return false
    } else if (filter === 'unread') {
      const hasUnread = Boolean(topic.unreadCount && topic.unreadCount > 0)
      if (!hasUnread) return false
    }

    // 2. Query search across title and description
    if (query) {
      const titleMatch = topic.title?.toLowerCase().includes(query) ?? false
      const descMatch = topic.description?.toLowerCase().includes(query) ?? false
      if (!titleMatch && !descMatch) return false
    }

    return true
  })
})

const isSearching = computed(() => {
  return Boolean(effectiveSearchQuery.value.trim() || activeFilter.value !== 'all')
})

const handleClearFilters = () => {
  effectiveSearchQuery.value = ''
  activeFilter.value = 'all'
}

const handleSelectTopic = (topic: Topic) => {
  emit('selectTopic', topic)
}

const handleCreateTopic = () => {
  emit('createTopic')
}
</script>

<template>
  <div class="w-full flex flex-col gap-4 pb-24 relative select-none" :dir="languageStore.dir">
    <!-- Search and Filter Bar Component (SOLID: SRP) -->
    <TopicSearchFilterBar
      v-model:search-query="effectiveSearchQuery"
      v-model:active-filter="activeFilter"
      :total-count="topics.length"
      :filtered-count="filteredTopics.length"
      @clear-search="handleClearFilters"
    />

    <!-- Main Topics Content Area -->
    <div class="w-full">
      <!-- Loading State: Shimmer Skeleton -->
      <TopicListSkeleton v-if="loading" :count="4" />

      <!-- Loaded Content -->
      <template v-else>
        <!-- Standalone Topic Cards List (Responsive 2-column on desktop) -->
        <div v-if="filteredTopics.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-3.5 w-full">
          <TopicCard
            v-for="topic in filteredTopics"
            :key="topic.id"
            v-bind="topic"
            @click="handleSelectTopic(topic)"
          />
        </div>

        <!-- Empty State -->
        <TopicEmptyState
          v-else
          :is-searching="isSearching"
          :search-query="effectiveSearchQuery"
          @reset-search="handleClearFilters"
          @create-topic="handleCreateTopic"
        />
      </template>
    </div>

    <!-- Floating Action Button (FAB) to Create Topic (iOS 18 pill/fab style) -->
    <Button
      @click="handleCreateTopic"
      class="fixed bottom-24 right-6 md:right-[max(1.5rem,calc(50vw-32rem+1.5rem))] z-45 size-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg outline-none cursor-pointer p-0"
      :title="languageStore.t('ایجاد تاپیک جدید', 'Create New Topic')"
    >
      <PlusIcon class="size-6" />
    </Button>
  </div>
</template>
