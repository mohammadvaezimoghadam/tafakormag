<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { PinIcon, SendIcon, BotIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  id?: number | string
  title?: string
  description?: string
  image?: string
  unreadCount?: number
  time?: string
  labels?: string[]
  pinned?: boolean
  telegram_bot_active?: boolean
  bale_bot_active?: boolean
}>(), {
  title: '',
  description: '',
  time: '',
  unreadCount: 0,
  labels: () => [],
  pinned: false,
  telegram_bot_active: false,
  bale_bot_active: false
})

const emit = defineEmits<{
  (e: 'click'): void
}>()

// Generate first letter of title for placeholder avatar
const avatarPlaceholder = computed(() => {
  return props.title && typeof props.title === 'string' && props.title.trim()
    ? props.title.trim().charAt(0)
    : languageStore.t('ت', 'T')
})

const formatTime = (isoString?: string) => {
  if (!isoString || typeof isoString !== 'string') return ''
  if (isoString === 'هم‌اکنون') return languageStore.t('هم‌اکنون', 'just now')
  if (isoString.includes(':') && !isoString.includes('-')) {
    return languageStore.n(isoString)
  }
  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return languageStore.n(isoString)
    
    return date.toLocaleDateString(languageStore.currentLanguage === 'fa' ? 'fa-IR' : 'en-US', {
      numberingSystem: languageStore.currentLanguage === 'fa' ? 'arabext' : 'latn',
      month: 'numeric',
      day: 'numeric'
    })
  } catch (e) {
    return languageStore.n(isoString)
  }
}
</script>

<template>
  <div
    @click="emit('click')"
    class="w-full flex items-center gap-3.5 p-3.5 rounded-2xl bg-card text-card-foreground border border-border/70 dark:border-border/60 shadow-[0_2px_8px_rgba(0,0,0,0.03)] dark:shadow-[0_2px_8px_rgba(0,0,0,0.20)] hover:shadow-md hover:border-primary/40 active:scale-[0.99] transition-all duration-200 cursor-pointer select-none text-start relative group"
    :dir="languageStore.dir"
  >
    <!-- Avatar / Thumbnail (Flutter: 44x44 size-11, rounded-2xl) -->
    <div class="relative shrink-0">
      <img
        v-if="image"
        :src="image"
        class="size-11 rounded-2xl object-cover bg-muted border border-border/10 shadow-xs"
        alt="Avatar"
        loading="lazy"
      />
      <div
        v-else
        class="size-11 rounded-2xl bg-primary/10 border border-primary/20 text-primary text-sm font-black flex items-center justify-center select-none shadow-xs group-hover:bg-primary/15 transition-colors"
      >
        {{ avatarPlaceholder }}
      </div>
      
      <!-- Pinned Pin Pill -->
      <div 
        v-if="pinned"
        class="absolute -top-1 -right-1 size-4.5 rounded-full bg-background border border-border/70 shadow-xs flex items-center justify-center text-primary"
        :title="languageStore.t('پین شده', 'Pinned')"
      >
        <PinIcon class="size-2.5 rotate-45" />
      </div>
    </div>

    <!-- Center Content: Title, Badges, Description -->
    <div class="flex-1 flex flex-col min-w-0 text-start gap-1">
      <div class="flex items-center gap-1.5 flex-wrap">
        <!-- Title -->
        <span class="text-xs sm:text-sm font-bold text-foreground truncate select-all group-hover:text-primary transition-colors text-start" dir="auto">
          {{ title }}
        </span>
        
        <!-- Bot Integration Pills -->
        <div class="flex items-center gap-1 shrink-0">
          <span
            v-if="telegram_bot_active"
            class="text-[9px] font-extrabold px-1.5 py-0.5 rounded-md bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 flex items-center gap-0.5 shadow-2xs"
            :title="languageStore.t('متصل به ربات تلگرام', 'Connected to Telegram Bot')"
          >
            <SendIcon class="size-2.5" />
            <span>{{ languageStore.t('تلگرام', 'Telegram') }}</span>
          </span>

          <span
            v-if="bale_bot_active"
            class="text-[9px] font-extrabold px-1.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center gap-0.5 shadow-2xs"
            :title="languageStore.t('متصل به ربات بله', 'Connected to Bale Bot')"
          >
            <BotIcon class="size-2.5" />
            <span>{{ languageStore.t('بله', 'Bale') }}</span>
          </span>

          <!-- Custom Labels -->
          <Badge
            v-for="label in labels"
            :key="label"
            variant="secondary"
            class="text-[8.5px] font-bold px-1.5 py-0.5 h-auto rounded-md border border-border/50"
          >
            {{ label }}
          </Badge>
        </div>
      </div>

      <!-- Description / Last Message Snippet -->
      <p class="text-[11px] sm:text-[11.5px] text-muted-foreground truncate leading-relaxed text-start" dir="auto">
        {{ description || languageStore.t('بدون توضیحات', 'No description') }}
      </p>
    </div>

    <!-- Trailing Section: Time & Unread Counter -->
    <div class="flex flex-col items-end shrink-0 gap-1.5 ms-1">
      <!-- Time Stamp -->
      <span class="text-[10px] text-muted-foreground/80 font-bold select-none whitespace-nowrap">
        {{ formatTime(time) }}
      </span>

      <!-- Unread Count Badge (Flutter iOS 18 style) -->
      <div 
        v-if="unreadCount > 0"
        class="h-5 min-w-5 px-1.5 rounded-full bg-primary text-primary-foreground text-[10px] font-black flex items-center justify-center shadow-xs"
        :title="languageStore.t(`${unreadCount} پیام جدید`, `${unreadCount} new messages`)"
      >
        {{ languageStore.n(unreadCount) }}
      </div>
      <div v-else class="h-5"></div>
    </div>
  </div>
</template>
