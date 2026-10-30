<script setup lang="ts">
import { ref } from 'vue'
import { StoreIcon, LayersIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import StoreCatalogView from '@/components/marketplace/store/StoreCatalogView.vue'
import MarketplaceAppsView from '@/components/marketplace/MarketplaceAppsView.vue'

const languageStore = useLanguageStore()

/**
 * Modularity & Decoupling:
 * Two-tab header switcher:
 * - 'store': Official Tafakor Store (Quran, Books, Cultural goods, Audio/Digital, Donations)
 * - 'apps': Plugins & Mini-apps Bazaar (Quran reader, Nahj, Sahifeh, AI, etc.)
 * 
 * To remove or disable either section in the future, simply remove the tab or component.
 */
const activeTab = ref<'store' | 'apps'>('store')
</script>

<template>
  <div class="w-full flex flex-col font-sans select-none" :dir="languageStore.dir">
    
    <!-- Top Two-Tab Switcher (Segmented Header Control) -->
    <div class="w-full flex justify-center mb-5">
      <div class="inline-flex p-1 rounded-2xl bg-muted/60 dark:bg-muted/40 backdrop-blur-xl border border-border/70 shadow-xs">
        
        <!-- Tab 1: Official Store -->
        <button
          @click="activeTab = 'store'"
          type="button"
          :class="[
            'px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all duration-200 cursor-pointer active:scale-95',
            activeTab === 'store'
              ? 'bg-background text-foreground shadow-xs border border-border/50'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/30 border border-transparent'
          ]"
        >
          <StoreIcon class="size-3.5 text-primary" />
          <span>{{ languageStore.t('فروشگاه تفکر', 'Tafakor Store') }}</span>
        </button>

        <!-- Tab 2: Apps / Bazaar -->
        <button
          @click="activeTab = 'apps'"
          type="button"
          :class="[
            'px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all duration-200 cursor-pointer active:scale-95',
            activeTab === 'apps'
              ? 'bg-background text-foreground shadow-xs border border-border/50'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/30 border border-transparent'
          ]"
        >
          <LayersIcon class="size-3.5 text-muted-foreground" />
          <span>{{ languageStore.t('بازارچه افزونه‌ها', 'App Marketplace') }}</span>
        </button>

      </div>
    </div>

    <!-- Active View Display with Smooth Fade Transition -->
    <transition name="fade" mode="out-in">
      <StoreCatalogView v-if="activeTab === 'store'" key="store" />
      <MarketplaceAppsView v-else key="apps" />
    </transition>

  </div>
</template>
