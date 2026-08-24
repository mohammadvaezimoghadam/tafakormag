<script setup lang="ts">
import { HomeIcon, HandHeartIcon, UserIcon, LayersIcon } from '@lucide/vue'
import { Badge } from '@/components/ui/badge'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

// V-model active tab binding ('home' | 'donate' | 'marketplace' | 'profile')
const activeTab = defineModel<'home' | 'donate' | 'marketplace' | 'profile'>({ default: 'home' })

const emit = defineEmits<{
  (e: 'change', tab: 'home' | 'donate' | 'marketplace' | 'profile'): void
}>()

const selectTab = (tab: 'home' | 'donate' | 'marketplace' | 'profile') => {
  activeTab.value = tab
  emit('change', tab)
}
</script>

<template>
  <div 
    class="inline-flex items-center gap-1 bg-background/60 backdrop-blur-md border border-border/60 rounded-xl p-1.5 shadow-md select-none font-sans" 
    :dir="languageStore.dir"
  >
    
    <!-- Home Tab -->
    <button
      @click="selectTab('home')"
      :class="[
        'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border border-transparent',
        activeTab === 'home'
          ? 'bg-primary/10 text-primary font-bold shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
      ]"
      :title="languageStore.t('خانه', 'Home')"
    >
      <HomeIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('خانه', 'Home') }}</span>
    </button>

    <!-- Donate Tab -->
    <button
      @click="selectTab('donate')"
      :class="[
        'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border border-transparent',
        activeTab === 'donate'
          ? 'bg-primary/10 text-primary font-bold shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
      ]"
      :title="languageStore.t('اهدا', 'Donate')"
    >
      <HandHeartIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('اهدا', 'Donate') }}</span>
    </button>

    <!-- Marketplace Tab (New) -->
    <button
      @click="selectTab('marketplace')"
      :class="[
        'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border border-transparent relative',
        activeTab === 'marketplace'
          ? 'bg-primary/10 text-primary font-bold shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
      ]"
      :title="languageStore.t('بازارچه', 'Marketplace')"
    >
      <!-- Floating 'New' Badge on Top (Green) -->
      <span class="absolute -top-2 left-1/2 -translate-x-1/2 text-[8px] px-1.5 py-0.2 bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-extrabold rounded-full shadow-2xs backdrop-blur-xs whitespace-nowrap pointer-events-none leading-tight">
        {{ languageStore.t('جدید', 'New') }}
      </span>

      <LayersIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('بازارچه', 'Marketplace') }}</span>
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
      :title="languageStore.t('پروفایل', 'Profile')"
    >
      <UserIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('پروفایل', 'Profile') }}</span>
    </button>

  </div>
</template>

