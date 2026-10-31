<script setup lang="ts">
import { HomeIcon, HandHeartIcon, UserIcon, LayersIcon } from '@lucide/vue'
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
    class="inline-flex items-center gap-1 bg-card/85 dark:bg-card/75 backdrop-blur-xl border border-border/70 dark:border-border/60 rounded-2xl p-1.5 shadow-[0_8px_30px_rgba(0,0,0,0.06)] dark:shadow-[0_8px_30px_rgba(0,0,0,0.35)] select-none font-sans" 
    :dir="languageStore.dir"
  >
    <!-- Home Tab -->
    <button
      @click="selectTab('home')"
      type="button"
      :class="[
        'px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border',
        activeTab === 'home'
          ? 'bg-primary/10 text-primary font-bold border-primary/20 shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40 border-transparent'
      ]"
      :title="languageStore.t('خانه', 'Home')"
    >
      <HomeIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('خانه', 'Home') }}</span>
    </button>

    <!-- Donate Tab -->
    <button
      @click="selectTab('donate')"
      type="button"
      :class="[
        'px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border',
        activeTab === 'donate'
          ? 'bg-primary/10 text-primary font-bold border-primary/20 shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40 border-transparent'
      ]"
      :title="languageStore.t('اهدا', 'Donate')"
    >
      <HandHeartIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('اهدا', 'Donate') }}</span>
    </button>

    <!-- Marketplace Tab -->
    <button
      @click="selectTab('marketplace')"
      type="button"
      :class="[
        'px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border relative',
        activeTab === 'marketplace'
          ? 'bg-primary/10 text-primary font-bold border-primary/20 shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40 border-transparent'
      ]"
      :title="languageStore.t('بازارچه', 'Marketplace')"
    >
      <!-- Floating 'New' Badge on Top -->
      <span class="absolute -top-2 left-1/2 -translate-x-1/2 text-[8px] px-1.5 py-0.2 bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-extrabold rounded-full shadow-2xs backdrop-blur-xs whitespace-nowrap pointer-events-none leading-tight">
        {{ languageStore.t('جدید', 'New') }}
      </span>

      <LayersIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('بازارچه', 'Marketplace') }}</span>
    </button>

    <!-- Profile Tab -->
    <button
      @click="selectTab('profile')"
      type="button"
      :class="[
        'px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border',
        activeTab === 'profile'
          ? 'bg-primary/10 text-primary font-bold border-primary/20 shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40 border-transparent'
      ]"
      :title="languageStore.t('پروفایل', 'Profile')"
    >
      <UserIcon class="size-3.5 shrink-0" />
      <span>{{ languageStore.t('پروفایل', 'Profile') }}</span>
    </button>

  </div>
</template>
