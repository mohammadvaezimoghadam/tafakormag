<script setup lang="ts">
import { computed } from 'vue'
import { PencilIcon } from '@lucide/vue'

const props = withDefaults(defineProps<{
  name: string
  phone: string
  avatar?: string
  statusText?: string
  statusVariant?: 'success' | 'warning' | 'info' | 'muted'
  topicsCount?: number
  postsCount?: number
  connectionsCount?: number
}>(), {
  statusText: 'فعال',
  statusVariant: 'success',
  topicsCount: 3,
  postsCount: 15,
  connectionsCount: 1
})

const emit = defineEmits<{
  (e: 'edit'): void
}>()

// Generate fallback letter
const nameLetter = computed(() => {
  return props.name ? props.name.trim().charAt(0) : 'ک'
})

// Helper for Farsi digits
const toPersianDigits = (num: number | string) => {
  const id = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
  return num.toString().replace(/[0-9]/g, (w) => id[+w]!)
}

// Compute status indicator color
const statusDotColor = computed(() => {
  switch (props.statusVariant) {
    case 'warning':
      return 'bg-amber-500'
    case 'info':
      return 'bg-blue-500'
    case 'muted':
      return 'bg-muted-foreground/60'
    case 'success':
    default:
      return 'bg-emerald-500'
  }
})

// Compute status pulse glow color
const statusBgGlow = computed(() => {
  switch (props.statusVariant) {
    case 'warning':
      return 'bg-amber-500/40'
    case 'info':
      return 'bg-blue-500/40'
    case 'muted':
      return 'bg-muted-foreground/20'
    case 'success':
    default:
      return 'bg-emerald-500/40'
  }
})
</script>

<template>
  <div
    class="w-full bg-card/25 dark:bg-card/15 backdrop-blur-md border border-border/50 rounded-3xl overflow-hidden relative shadow-xs flex flex-col items-center select-none pt-0 pb-6 transition-all duration-300 hover:border-border/80 group"
    dir="rtl"
  >
    <!-- Decorative Header Banner -->
    <div class="w-full h-16 bg-gradient-to-tr from-primary/15 via-primary/5 to-transparent border-b border-border/20 relative overflow-hidden">
      <!-- Ambient background blur bubbles for depth -->
      <div class="absolute -top-10 -right-10 size-24 rounded-full bg-primary/10 blur-xl transition-all duration-500 group-hover:scale-110" />
      <div class="absolute -bottom-8 -left-6 size-16 rounded-full bg-primary/5 blur-lg" />
    </div>

    <!-- Floating Edit Account button (Top-Right) -->
    <button
      @click="emit('edit')"
      class="absolute top-3.5 right-3.5 size-7.5 rounded-full bg-background/55 dark:bg-card/40 backdrop-blur-xs border border-border/50 hover:bg-muted/80 text-muted-foreground hover:text-foreground active:scale-95 transition-all flex items-center justify-center cursor-pointer shadow-xs"
      title="ویرایش حساب کاربری"
    >
      <PencilIcon class="size-3.5 shrink-0" />
    </button>

    <!-- Overlapping Circular Avatar -->
    <div class="relative shrink-0 select-none -mt-9 transition-transform duration-300 group-hover:scale-102">
      <img
        v-if="avatar"
        :src="avatar"
        class="size-18 rounded-full object-cover ring-4 ring-background/90 dark:ring-card shadow-md"
        alt="Profile Avatar"
      />
      <div
        v-else
        class="size-18 rounded-full bg-primary/10 border-2 border-primary/20 flex items-center justify-center text-primary text-xl font-bold ring-4 ring-background/90 dark:ring-card shadow-md"
      >
        {{ nameLetter }}
      </div>

      <!-- Overlapping Discord-style Status indicator dot -->
      <div
        :class="[
          'absolute bottom-0 right-0.5 size-4.5 rounded-full border-3 border-background dark:border-card shadow-xs flex items-center justify-center',
          statusDotColor
        ]"
      >
        <span 
          v-if="statusVariant === 'success' || statusVariant === 'warning'"
          :class="['absolute inset-0 rounded-full animate-ping opacity-75', statusBgGlow]" 
        />
      </div>
    </div>

    <!-- User Information -->
    <div class="mt-10 flex flex-col items-center justify-center text-center px-4 w-full">
      <!-- Full Name -->
      <h3 class="text-sm font-black text-foreground select-all leading-normal">
        {{ name }}
      </h3>
      
      <!-- Phone Number -->
      <span class="text-xs text-muted-foreground/80 mt-4 select-all font-semibold font-sans">
        {{ phone }}
      </span>
    </div>

    <!-- Statistics Section (Topics, Posts, Connections) -->
    <div class="grid grid-cols-3 gap-2 w-full mt-6 pt-5 px-6 border-t border-border/40 text-center">
      <div class="flex flex-col gap-0.5">
        <span class="text-sm font-black text-foreground">{{ toPersianDigits(topicsCount) }}</span>
        <span class="text-[9.5px] font-medium text-muted-foreground">تاپیک‌ها</span>
      </div>
      <div class="flex flex-col gap-0.5">
        <span class="text-sm font-black text-foreground">{{ toPersianDigits(postsCount) }}</span>
        <span class="text-[9.5px] font-medium text-muted-foreground">پست‌ها</span>
      </div>
      <div class="flex flex-col gap-0.5">
        <span class="text-sm font-black text-foreground">{{ toPersianDigits(connectionsCount) }}</span>
        <span class="text-[9.5px] font-medium text-muted-foreground">اتصال‌ها</span>
      </div>
    </div>
  </div>
</template>
