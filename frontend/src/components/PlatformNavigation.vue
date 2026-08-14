<script setup lang="ts">
import { HomeIcon, HandHeartIcon, UserIcon } from '@lucide/vue'
import { Badge } from '@/components/ui/badge'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

// V-model active tab binding ('home' | 'donate' | 'profile')
const activeTab = defineModel<'home' | 'donate' | 'profile'>({ default: 'home' })

const emit = defineEmits<{
  (e: 'change', tab: 'home' | 'donate' | 'profile'): void
}>()

const selectTab = (tab: 'home' | 'donate' | 'profile') => {
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

    <!-- Donate Tab (Middle) -->
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

