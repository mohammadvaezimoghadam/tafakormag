<script setup lang="ts">
import { ref } from 'vue'
import { 
  HomeIcon, 
  LayersIcon, 
  HandHeartIcon, 
  UserIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const props = withDefaults(defineProps<{
  mode?: 'auto' | 'inline' | 'mobile' | 'desktop'
  showMobileNav?: boolean
}>(), {
  mode: 'auto',
  showMobileNav: true
})

const languageStore = useLanguageStore()

// V-model active tab binding ('home' | 'topics' | 'donate' | 'marketplace' | 'profile')
const activeTab = defineModel<'home' | 'topics' | 'donate' | 'marketplace' | 'profile'>({ default: 'home' })

const emit = defineEmits<{
  (e: 'change', tab: 'home' | 'topics' | 'donate' | 'marketplace' | 'profile'): void
}>()

const selectTab = (tab: 'home' | 'topics' | 'donate' | 'marketplace' | 'profile') => {
  activeTab.value = tab
  emit('change', tab)
}

// Hover state for Desktop Sidebar expansion
const isHovered = ref(false)

// Navigation items definition
const navItems = [
  { id: 'home', labelFa: 'خانه', labelEn: 'Home', icon: HomeIcon },
  { id: 'topics', labelFa: 'تاپیک‌ها', labelEn: 'Topics', icon: LayersIcon },
  { id: 'donate', labelFa: 'اهدا', labelEn: 'Donate', icon: HandHeartIcon },
  { id: 'profile', labelFa: 'پروفایل', labelEn: 'Profile', icon: UserIcon },
] as const
</script>

<template>
  <!-- ======================================================================= -->
  <!-- 1. INLINE MODE (Used in Playground or standalone preview boxes)         -->
  <!-- ======================================================================= -->
  <div 
    v-if="props.mode === 'inline'"
    class="inline-flex items-center gap-1 bg-background/80 backdrop-blur-md border border-border/60 rounded-xl p-1.5 shadow-md select-none font-sans" 
    :dir="languageStore.dir"
  >
    <button
      v-for="item in navItems"
      :key="'inline-' + item.id"
      @click="selectTab(item.id)"
      :class="[
        'px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border border-transparent',
        activeTab === item.id
          ? 'bg-primary/10 text-primary font-bold shadow-xs'
          : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
      ]"
      :title="languageStore.t(item.labelFa, item.labelEn)"
    >
      <component :is="item.icon" class="size-3.5 shrink-0" />
      <span>{{ languageStore.t(item.labelFa, item.labelEn) }}</span>
    </button>
  </div>

  <template v-else>
    <!-- ======================================================================= -->
    <!-- 2. MOBILE BOTTOM NAVIGATION (Visible on mobile/tablet screens < md)    -->
    <!-- ======================================================================= -->
    <div 
      v-if="(props.mode === 'auto' || props.mode === 'mobile') && props.showMobileNav" 
      class="md:hidden fixed bottom-6 inset-x-0 flex justify-center z-45 pointer-events-none px-6"
    >
      <div 
        class="pointer-events-auto inline-flex items-center gap-1 bg-background/80 dark:bg-card/85 backdrop-blur-xl border border-border/70 rounded-2xl p-1.5 shadow-xl select-none font-sans" 
        :dir="languageStore.dir"
      >
        <button
          v-for="item in navItems"
          :key="'mobile-' + item.id"
          @click="selectTab(item.id)"
          :class="[
            'px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-200 active:scale-95 cursor-pointer border border-transparent',
            activeTab === item.id
              ? 'bg-primary/10 text-primary font-bold shadow-xs'
              : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
          ]"
          :title="languageStore.t(item.labelFa, item.labelEn)"
        >
          <component :is="item.icon" class="size-4 shrink-0" />
          <span>{{ languageStore.t(item.labelFa, item.labelEn) }}</span>
        </button>
      </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 3. DESKTOP INSTAGRAM-STYLE SIDEBAR (Visible on laptop/desktop >= md)   -->
    <!-- Seamless blend, stationary icons with zero shift, unclipped brand text  -->
    <!-- ======================================================================= -->
    <aside
      v-if="props.mode === 'auto' || props.mode === 'desktop'"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
      :class="[
        'hidden md:flex fixed top-0 bottom-0 start-0 z-50 h-screen select-none font-sans',
        'bg-background border-none shadow-none',
        'flex flex-col py-8 px-3',
        'transition-[width] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]',
        isHovered ? 'w-60' : 'w-[92px]'
      ]"
      :dir="languageStore.dir"
    >
      <!-- Top Section: Brand Typography (تفکر) - Fixed position, unclipped throughout transitions -->
      <div 
        @click="selectTab('home')"
        class="h-14 flex items-center justify-start px-2 rounded-2xl cursor-pointer hover:bg-muted/30 transition-colors duration-200 shrink-0 select-none mb-6 overflow-visible"
        :title="languageStore.t('صفحه اصلی تفکر', 'Tafakor Home')"
      >
        <span class="font-black text-2xl text-foreground whitespace-nowrap overflow-visible">
          {{ languageStore.t('تفکر', 'Tafakor') }}
        </span>
      </div>

      <!-- Navigation Links (Under the brand logo, icons completely stationary with zero shift) -->
      <nav class="flex flex-col gap-2 w-full">
        <button
          v-for="item in navItems"
          :key="'desktop-' + item.id"
          @click="selectTab(item.id)"
          :class="[
            'w-full h-12 rounded-xl flex items-center justify-start px-2.5 gap-6 transition-colors duration-200 cursor-pointer outline-none bg-transparent hover:bg-muted/30 active:scale-95 overflow-hidden'
          ]"
          :title="languageStore.t(item.labelFa, item.labelEn)"
        >
          <!-- Nav Icon (Stationary in place, size strictly fixed at size-6, bolder stroke when active) -->
          <div class="size-6 flex items-center justify-center shrink-0">
            <component 
              :is="item.icon" 
              class="size-6 shrink-0 transition-colors duration-200"
              :class="[
                activeTab === item.id 
                  ? 'stroke-[2.5px] text-foreground' 
                  : 'stroke-[1.75px] text-muted-foreground'
              ]"
            />
          </div>

          <!-- Nav Label (Generous 24px gap-6, smooth slide/fade, no layout shift for icon) -->
          <span 
            class="inline-block whitespace-nowrap text-base transition-all duration-300 overflow-hidden"
            :class="[
              isHovered ? 'max-w-[150px] opacity-100' : 'max-w-0 opacity-0 pointer-events-none',
              activeTab === item.id 
                ? 'font-bold text-foreground' 
                : 'font-normal text-muted-foreground'
            ]"
          >
            {{ languageStore.t(item.labelFa, item.labelEn) }}
          </span>
        </button>
      </nav>

    </aside>
  </template>
</template>
