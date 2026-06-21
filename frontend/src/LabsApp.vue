<script setup lang="ts">
import { ConfigProvider } from 'reka-ui'
import { useDark, useToggle } from '@vueuse/core'
import { 
  SunIcon, 
  MoonIcon, 
  PaletteIcon, 
  FlaskConicalIcon,
  SparklesIcon
} from '@lucide/vue'

// Dark/Light theme manager via VueUse
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleDark = useToggle(isDark)
</script>

<template>
  <ConfigProvider dir="rtl">
    <div class="min-h-screen bg-background text-foreground font-sans transition-colors duration-300 flex flex-col" dir="rtl">
      
      <!-- Top Navigation Header for Design Labs -->
      <header class="sticky top-0 z-50 w-full border-b border-border/80 bg-background/80 backdrop-blur-md flex justify-center">
        <div class="w-full max-w-6xl px-6 h-16 flex items-center justify-between">
          
          <!-- Logo & Brand -->
          <div class="flex items-center gap-2">
            <div class="size-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground shadow-sm animate-pulse">
              <SparklesIcon class="size-4 text-amber-400" />
            </div>
            <div>
              <span class="font-extrabold tracking-tight text-sm">آزمایشگاه طراحی AVA (Design Labs)</span>
              <span class="text-[9px] block text-muted-foreground mt-0.5 leading-none">محیط‌های تستی و شوکیس</span>
            </div>
          </div>

          <!-- Navigation Links (Showcase and Playground only) -->
          <nav class="flex items-center gap-2">
            <router-link 
              to="/showcase" 
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all text-muted-foreground hover:text-foreground hover:bg-muted/50 [&.router-link-active]:bg-primary/5 [&.router-link-active]:text-primary [&.router-link-active]:font-bold border border-transparent [&.router-link-active]:border-primary/10"
            >
              <PaletteIcon class="size-4" />
              <span>نمایشگاه دیزاین</span>
            </router-link>

            <router-link 
              to="/playground" 
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all text-muted-foreground hover:text-foreground hover:bg-muted/50 [&.router-link-active]:bg-primary/5 [&.router-link-active]:text-primary [&.router-link-active]:font-bold border border-transparent [&.router-link-active]:border-primary/10"
            >
              <FlaskConicalIcon class="size-4" />
              <span>زمین بازی</span>
            </router-link>
          </nav>

          <!-- Utilities (Theme Switcher) -->
          <div class="flex items-center gap-2">
            <button 
              @click="toggleDark()" 
              class="size-8 rounded-lg border border-border/80 bg-background flex items-center justify-center hover:bg-muted transition-colors shadow-sm outline-none cursor-pointer"
              title="تغییر تم"
            >
              <SunIcon v-if="isDark" class="size-4 text-amber-500" />
              <MoonIcon v-else class="size-4 text-primary" />
            </button>
          </div>

        </div>
      </header>

      <!-- Main Application Container -->
      <main class="flex-1 w-full bg-linear-to-b from-background via-card/10 to-muted/20">
        <router-view v-slot="{ Component }">
          <transition 
            name="fade" 
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </main>

    </div>
  </ConfigProvider>
</template>

<style>
/* Smooth fade transitions for page swaps */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
