<script setup lang="ts">
import { HomeIcon, UserIcon } from '@lucide/vue'

// V-model active tab binding ('home' | 'profile')
const activeTab = defineModel<'home' | 'profile'>({ default: 'home' })

const emit = defineEmits<{
  (e: 'change', tab: 'home' | 'profile'): void
}>()

const selectTab = (tab: 'home' | 'profile') => {
  activeTab.value = tab
  emit('change', tab)
}
</script>

<template>
  <div class="inline-flex items-center gap-1 bg-background/60 backdrop-blur-md border border-border/60 rounded-xl p-1.5 shadow-md select-none font-sans" dir="rtl">
    
    <!-- Home Tab -->
    <button
      @click="selectTab('home')"
      :class="[
        'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border border-transparent',
        activeTab === 'home'
          ? 'bg-primary/10 text-primary font-bold shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
      ]"
      title="خانه"
    >
      <HomeIcon class="size-3.5 shrink-0" />
      <span>خانه</span>
    </button>

    <!-- Profile Tab -->
    <button
      @click="selectTab('profile')"
      :class="[
        'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border border-transparent',
        activeTab === 'profile'
          ? 'bg-primary/10 text-primary font-bold shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
      ]"
      title="پروفایل"
    >
      <UserIcon class="size-3.5 shrink-0" />
      <span>پروفایل</span>
    </button>

  </div>
</template>
