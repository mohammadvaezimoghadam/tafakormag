<script setup lang="ts">
import { ref } from 'vue'
import { 
  HomeIcon, 
  LayersIcon, 
  HandHeartIcon, 
  UserIcon,
  SunIcon,
  MoonIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const props = withDefaults(defineProps<{
  mode?: 'auto' | 'inline' | 'mobile' | 'desktop'
  showMobileNav?: boolean
  dark?: boolean
}>(), {
  mode: 'auto',
  showMobileNav: true,
  dark: false
})

const languageStore = useLanguageStore()

// V-model active tab binding ('home' | 'topics' | 'donate' | 'marketplace' | 'profile')
const activeTab = defineModel<'home' | 'topics' | 'donate' | 'marketplace' | 'profile'>({ default: 'home' })

const emit = defineEmits<{
  (e: 'change', tab: 'home' | 'topics' | 'donate' | 'marketplace' | 'profile'): void
  (e: 'toggle-theme'): void
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
    <!-- Standard fixed bottom bar: edge-to-edge, flush at bottom, icon on top,  -->
    <!-- text underneath.                                                       -->
    <!-- ======================================================================= -->
    <nav 
      v-if="(props.mode === 'auto' || props.mode === 'mobile') && props.showMobileNav" 
      class="md:hidden fixed bottom-0 inset-x-0 z-45 w-full bg-background/95 dark:bg-card/95 backdrop-blur-xl border-t border-border/80 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] dark:shadow-[0_-4px_20px_rgba(0,0,0,0.3)] select-none font-sans" 
      :dir="languageStore.dir"
      style="padding-bottom: max(env(safe-area-inset-bottom), 0.25rem);"
    >
      <div class="grid grid-cols-4 items-center h-16 w-full max-w-lg mx-auto px-1">
        <button
          v-for="item in navItems"
          :key="'mobile-' + item.id"
          type="button"
          @click="selectTab(item.id)"
          :class="[
            'flex flex-col items-center justify-center gap-1 h-full w-full py-1.5 rounded-lg transition-all duration-200 active:scale-95 cursor-pointer outline-none',
            activeTab === item.id
              ? 'text-primary'
              : 'text-muted-foreground hover:text-foreground'
          ]"
          :title="languageStore.t(item.labelFa, item.labelEn)"
        >
          <div class="relative flex items-center justify-center">
            <component 
              :is="item.icon" 
              class="size-[22px] transition-all duration-200 shrink-0" 
              :class="[
                activeTab === item.id ? 'stroke-[2.5px] scale-105' : 'stroke-[1.75px]'
              ]"
            />
          </div>
          <span 
            class="text-[11px] leading-none transition-all duration-200 tracking-tight"
            :class="[
              activeTab === item.id ? 'font-bold' : 'font-medium'
            ]"
          >
            {{ languageStore.t(item.labelFa, item.labelEn) }}
          </span>
        </button>
      </div>
    </nav>

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
        'flex flex-col py-6 px-3',
        'transition-[width] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]',
        isHovered ? 'w-60' : 'w-[72px]'
      ]"
      :dir="languageStore.dir"
    >
      <!-- Top Section: Brand Typography (تفکر) - Stationary in place, unclipped throughout transitions -->
      <div 
        @click="selectTab('home')"
        class="h-12 w-full flex items-center justify-start rounded-xl cursor-pointer hover:bg-muted/30 transition-colors duration-200 shrink-0 select-none overflow-hidden"
        :title="languageStore.t('صفحه اصلی تفکر', 'Tafakor Home')"
      >
        <div class="w-12 h-12 flex items-center justify-center shrink-0">
          <span class="font-black text-2xl text-foreground select-none">
            {{ languageStore.t('تفکر', 'Tafakor') }}
          </span>
        </div>
      </div>

      <!-- Navigation Links (Centered vertically like Instagram, 100% stationary icons with animated text) -->
      <nav class="flex-1 flex flex-col justify-center gap-3 w-full my-auto">
        <button
          v-for="item in navItems"
          :key="'desktop-' + item.id"
          @click="selectTab(item.id)"
          class="w-full h-12 rounded-xl flex items-center justify-start p-0 transition-colors duration-200 cursor-pointer outline-none bg-transparent hover:bg-muted/30 active:scale-95 overflow-hidden"
          :title="languageStore.t(item.labelFa, item.labelEn)"
        >
          <!-- Nav Icon (Permanently fixed 48px slot, strictly stationary with zero sub-pixel shift) -->
          <div class="w-12 h-12 flex items-center justify-center shrink-0">
            <component 
              :is="item.icon" 
              class="size-6 shrink-0 transition-colors duration-200"
              :class="[
                activeTab === item.id 
                  ? 'stroke-[2.25px] text-foreground' 
                  : 'stroke-[1.75px] text-muted-foreground'
              ]"
            />
          </div>

          <!-- Nav Label (Smooth slide/fade animation while icon stays completely still) -->
          <span 
            class="inline-block whitespace-nowrap text-base transition-all duration-300 overflow-hidden pe-3"
            :class="[
              isHovered ? 'max-w-[160px] opacity-100' : 'max-w-0 opacity-0 pointer-events-none',
              activeTab === item.id 
                ? 'font-bold text-foreground' 
                : 'font-normal text-muted-foreground'
            ]"
          >
            {{ languageStore.t(item.labelFa, item.labelEn) }}
          </span>
        </button>
      </nav>

      <!-- Bottom Section: Dark/Light Mode Toggle Button (Icon only, 100% stationary at the bottom) -->
      <div class="mt-auto w-full pt-2 flex items-center justify-start">
        <button
          type="button"
          @click="emit('toggle-theme')"
          class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-all duration-200 cursor-pointer active:scale-95 outline-none"
          :title="props.dark ? languageStore.t('حالت روشن', 'Light Mode') : languageStore.t('حالت تاریک', 'Dark Mode')"
          :aria-label="props.dark ? languageStore.t('حالت روشن', 'Light Mode') : languageStore.t('حالت تاریک', 'Dark Mode')"
        >
          <SunIcon v-if="props.dark" class="size-6 text-amber-400 hover:rotate-45 transition-transform duration-300" />
          <MoonIcon v-else class="size-6 text-muted-foreground hover:text-foreground hover:-rotate-12 transition-transform duration-300" />
        </button>
      </div>

    </aside>
  </template>
</template>
