<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { PinIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  title: string
  description: string
  image?: string
  unreadCount?: number
  time: string
  labels?: string[]
  pinned?: boolean
}>(), {
  unreadCount: 0,
  labels: () => [],
  pinned: false
})

const emit = defineEmits<{
  (e: 'click'): void
}>()

// Generate first letter of title for placeholder avatar
const avatarPlaceholder = computed(() => {
  return props.title ? props.title.trim().charAt(0) : languageStore.t('ت', 'T')
})

const formatTime = (isoString: string) => {
  if (!isoString) return ''
  if (isoString === 'هم‌اکنون') return languageStore.t('هم‌اکنون', 'just now')
  // If it's not a valid ISO date, return as is (for mock data in playground)
  if (isoString.includes(':') && !isoString.includes('-')) {
    return languageStore.n(isoString)
  }
  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return languageStore.n(isoString)
    
    return date.toLocaleDateString(languageStore.currentLanguage === 'fa' ? 'fa-IR' : 'en-US', {
      numberingSystem: languageStore.currentLanguage === 'fa' ? 'arabext' : 'latn'
    })
  } catch (e) {
    return languageStore.n(isoString)
  }
}
</script>

<template>
  <div
    @click="emit('click')"
    class="w-full flex items-center gap-3.5 p-3 rounded-2xl hover:bg-muted/40 transition-all duration-200 cursor-pointer select-none border-0 group relative text-start"
    :dir="languageStore.dir"
  >
    <!-- Avatar / Image -->
    <div class="relative shrink-0">
      <img
        v-if="image"
        :src="image"
        class="size-11 rounded-2xl object-cover bg-muted border border-border/10 shadow-xs"
        alt="Avatar"
      />
      <div
        v-else
        class="size-11 rounded-2xl bg-primary/10 border border-primary/20 text-primary text-sm font-extrabold flex items-center justify-center select-none"
      >
        {{ avatarPlaceholder }}
      </div>
      
      <!-- Pinned Badge Badge -->
      <div 
        v-if="pinned"
        class="absolute -top-1 -right-1 size-5 rounded-full bg-background border border-border/50 shadow-xs flex items-center justify-center text-muted-foreground"
      >
        <PinIcon class="size-2.5 rotate-45" />
      </div>
    </div>

    <!-- Middle Content Section (Title, Labels, Description) -->
    <div class="flex-1 flex flex-col min-w-0 text-start gap-1.5">
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Title -->
        <span class="text-xs font-bold text-foreground truncate select-all text-start" dir="auto">
          {{ title }}
        </span>
        
        <!-- Category Labels -->
        <div class="flex items-center gap-1 shrink-0">
          <Badge
            v-for="label in labels"
            :key="label"
            variant="secondary"
            class="text-[8px] font-bold px-1.5 h-4 border border-border/50"
          >
            {{ label }}
          </Badge>
        </div>
      </div>

      <!-- Description / Last Message -->
      <p class="text-[11px] text-muted-foreground truncate leading-relaxed text-start" dir="auto">
        {{ description }}
      </p>
    </div>

    <!-- Left Section (Time, Unread Count Badge) -->
    <div class="flex flex-col items-end shrink-0 gap-2">
      <!-- Time Stamp -->
      <span class="text-[10px] text-muted-foreground font-bold select-none">
        {{ formatTime(time) }}
      </span>

      <!-- Unread Count Badge -->
      <Badge 
        v-if="unreadCount > 0"
        variant="default"
        class="h-5 min-w-5 rounded-full text-[10px] font-black px-1.5 shadow-xs"
      >
        {{ languageStore.n(unreadCount) }}
      </Badge>
    </div>
  </div>
</template>
