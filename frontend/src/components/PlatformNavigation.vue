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
import { useDark, useToggle } from '@vueuse/core'
import { useLanguageStore } from '@/stores/languageStore'
import { useUserStore } from '@/stores/userStore'

const props = withDefaults(defineProps<{
  mode?: 'auto' | 'inline' | 'mobile' | 'desktop'
  showMobileNav?: boolean
}>(), {
  mode: 'auto',
  showMobileNav: true
})

const languageStore = useLanguageStore()
const userStore = useUserStore()

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

// Theme toggle
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleTheme = useToggle(isDark)

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
    <!-- ======================================================================= -->
    <aside
      v-if="props.mode === 'auto' || props.mode === 'desktop'"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
      :class="[
        'hidden md:flex fixed top-0 bottom-0 start-0 z-50 h-screen select-none font-sans',
        'bg-background/90 dark:bg-card/90 backdrop-blur-2xl border-e border-border/60',
        'flex flex-col justify-between py-6 px-3',
        'transition-[width,box-shadow] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]',
        isHovered 
          ? 'w-60 shadow-2xl shadow-black/10 dark:shadow-black/50' 
          : 'w-20 shadow-none'
      ]"
      :dir="languageStore.dir"
    >
      <!-- Top Section: Brand & Logo -->
      <div 
        @click="selectTab('home')"
        class="h-14 flex items-center rounded-2xl cursor-pointer hover:bg-muted/40 active:scale-98 transition-all duration-200 overflow-hidden"
        :class="isHovered ? 'px-3 gap-3 justify-start' : 'px-0 justify-center'"
        :title="languageStore.t('صفحه اصلی تفکر', 'Tafakor Home')"
      >
        <!-- Modern Geometric Brand Mark -->
        <div class="size-11 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 shadow-xs transition-transform duration-300 group-hover:scale-105">
          <svg class="size-6 text-primary fill-primary/10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
            <path d="M6 6h10" />
            <path d="M6 10h7" />
          </svg>
        </div>

        <!-- Brand Name & Tagline (Smooth Slide/Fade on Hover) -->
        <div 
          class="flex flex-col text-start overflow-hidden transition-all duration-300"
          :class="isHovered ? 'max-w-[150px] opacity-100' : 'max-w-0 opacity-0 pointer-events-none'"
        >
          <span class="font-black text-lg text-foreground tracking-tight whitespace-nowrap leading-tight">
            {{ languageStore.t('تفکر', 'Tafakor') }}
          </span>
          <span class="text-[10px] text-muted-foreground font-medium truncate">
            {{ languageStore.t('ترویج اندیشه و دانایی', 'Thought & Wisdom') }}
          </span>
        </div>
      </div>

      <!-- Center Section: Navigation Links -->
      <nav class="flex flex-col gap-2 w-full my-auto">
        <button
          v-for="item in navItems"
          :key="'desktop-' + item.id"
          @click="selectTab(item.id)"
          :class="[
            'relative w-full h-12 rounded-2xl flex items-center transition-all duration-200 active:scale-95 cursor-pointer outline-none border border-transparent overflow-hidden',
            isHovered ? 'px-3.5 justify-start' : 'px-0 justify-center',
            activeTab === item.id
              ? 'bg-primary/10 text-primary font-bold shadow-xs'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
          ]"
          :title="languageStore.t(item.labelFa, item.labelEn)"
        >
          <!-- Nav Icon -->
          <component 
            :is="item.icon" 
            class="size-6 shrink-0 transition-transform duration-200"
            :class="activeTab === item.id ? 'scale-105' : ''"
          />

          <!-- Nav Label (Smooth Slide/Fade) -->
          <span 
            class="whitespace-nowrap text-sm font-semibold transition-all duration-300 overflow-hidden"
            :class="isHovered ? 'max-w-[140px] opacity-100 ms-3.5' : 'max-w-0 opacity-0 ms-0 pointer-events-none'"
          >
            {{ languageStore.t(item.labelFa, item.labelEn) }}
          </span>

          <!-- Active Indicator Pill on the start edge -->
          <span 
            v-if="activeTab === item.id"
            class="absolute start-1 top-1/2 -translate-y-1/2 w-1 h-5 rounded-full bg-primary"
          />
        </button>
      </nav>

      <!-- Bottom Section: Theme Toggle & User Info -->
      <div class="border-t border-border/50 pt-4 flex flex-col gap-2 w-full">
        <!-- Theme Toggle -->
        <button
          @click="toggleTheme()"
          :class="[
            'w-full h-11 rounded-2xl flex items-center transition-all duration-200 active:scale-95 cursor-pointer outline-none border border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40 overflow-hidden',
            isHovered ? 'px-3.5 justify-start' : 'px-0 justify-center'
          ]"
          :title="isDark ? languageStore.t('حالت روشن', 'Light Mode') : languageStore.t('حالت تاریک', 'Dark Mode')"
        >
          <SunIcon v-if="isDark" class="size-5 shrink-0 text-amber-400" />
          <MoonIcon v-else class="size-5 shrink-0 text-slate-600 dark:text-slate-300" />

          <span 
            class="whitespace-nowrap text-xs font-semibold overflow-hidden transition-all duration-300"
            :class="isHovered ? 'max-w-[140px] opacity-100 ms-3' : 'max-w-0 opacity-0 ms-0 pointer-events-none'"
          >
            {{ isDark ? languageStore.t('حالت روشن', 'Light Mode') : languageStore.t('حالت تاریک', 'Dark Mode') }}
          </span>
        </button>

        <!-- User Quick Profile Summary Button -->
        <button
          @click="selectTab('profile')"
          :class="[
            'w-full h-11 rounded-2xl flex items-center transition-all duration-200 active:scale-95 cursor-pointer outline-none border border-transparent overflow-hidden',
            activeTab === 'profile'
              ? 'bg-primary/10 text-primary font-bold'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/40',
            isHovered ? 'px-3.5 justify-start' : 'px-0 justify-center'
          ]"
          :title="languageStore.t('پروفایل کاربری', 'User Profile')"
        >
          <div class="size-7 rounded-full bg-primary/15 border border-primary/20 flex items-center justify-center text-primary font-bold text-xs shrink-0 overflow-hidden">
            <span v-if="userStore.user?.username">{{ userStore.user.username.slice(0, 2).toUpperCase() }}</span>
            <UserIcon v-else class="size-4" />
          </div>

          <div 
            class="flex flex-col text-start overflow-hidden transition-all duration-300"
            :class="isHovered ? 'max-w-[130px] opacity-100 ms-2.5' : 'max-w-0 opacity-0 ms-0 pointer-events-none'"
          >
            <span class="text-xs font-bold text-foreground truncate">
              {{ userStore.user?.phone_number || userStore.user?.username || languageStore.t('حساب کاربری', 'Account') }}
            </span>
            <span class="text-[10px] text-muted-foreground truncate">
              {{ userStore.isAuthenticated ? languageStore.t('مشاهده پروفایل', 'View Profile') : languageStore.t('ورود به حساب', 'Sign In') }}
            </span>
          </div>
        </button>
      </div>

    </aside>
  </template>
</template>
