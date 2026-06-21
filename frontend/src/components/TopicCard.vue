<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { PinIcon } from '@lucide/vue'

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
  return props.title ? props.title.trim().charAt(0) : 'ت'
})
</script>

<template>
  <div
    @click="emit('click')"
    class="w-full flex items-center gap-3.5 p-3 rounded-2xl hover:bg-muted/40 transition-all duration-200 cursor-pointer select-none text-right border-0 group relative"
    dir="rtl"
  >
    <!-- Avatar / Image (RTL: right side) -->
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
      
      <!-- Pinned marker indicator -->
      <span 
        v-if="pinned" 
        class="absolute -top-1 -right-1 size-3.5 bg-primary rounded-full border border-background flex items-center justify-center text-primary-foreground"
        title="سنجاق شده"
      >
        <PinIcon class="size-2 text-primary-foreground fill-primary-foreground" />
      </span>
    </div>

    <!-- Middle Content Section (Title, Labels, Description) -->
    <div class="flex-1 flex flex-col min-w-0 text-right gap-1.5">
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Title -->
        <span class="text-xs font-bold text-foreground truncate select-all">
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
      <p class="text-[11px] text-muted-foreground truncate leading-relaxed">
        {{ description }}
      </p>
    </div>

    <!-- Left Section (Time, Unread Count Badge) -->
    <div class="flex flex-col items-end shrink-0 gap-2">
      <!-- Time Stamp -->
      <span class="text-[10px] text-muted-foreground font-bold select-none">
        {{ time }}
      </span>

      <!-- Unread Count Badge -->
      <Badge 
        v-if="unreadCount > 0"
        variant="default"
        class="h-5 min-w-5 rounded-full text-[10px] font-black px-1.5 shadow-xs"
      >
        {{ unreadCount }}
      </Badge>
    </div>

  </div>
</template>
