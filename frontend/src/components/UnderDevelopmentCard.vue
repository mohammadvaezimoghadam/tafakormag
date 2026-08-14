<script setup lang="ts">
import { computed } from 'vue'
import { 
  ConstructionIcon, 
  ZapIcon, 
  ClockIcon, 
  ChevronRightIcon, 
  ChevronLeftIcon,
  CheckCircle2Icon 
} from '@lucide/vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

export interface UnderDevelopmentCardProps {
  /** Title of the card/feature */
  title?: string
  /** Description explaining what is coming */
  description?: string
  /** Lucide icon component to display in the top center */
  icon?: any
  /** Estimated version or timeline (e.g. 'نسخه ۲.۰' / 'بهار ۱۴۰۵') */
  eta?: string
  /** List of upcoming sub-features or highlights */
  features?: string[]
  /** Action button text (if omitted, button is hidden) */
  actionText?: string
  /** Whether to show a return/back button */
  showBackButton?: boolean
  /** Back button text */
  backButtonText?: string
  /** Animation speed for the linear background pattern ('slow' | 'normal' | 'fast') */
  patternSpeed?: 'slow' | 'normal' | 'fast'
  /** Visual pattern style */
  patternStyle?: 'stripes' | 'grid' | 'dots'
}

const props = withDefaults(defineProps<UnderDevelopmentCardProps>(), {
  title: '',
  description: '',
  icon: ConstructionIcon,
  eta: '',
  features: () => [],
  actionText: '',
  showBackButton: false,
  backButtonText: '',
  patternSpeed: 'normal',
  patternStyle: 'stripes'
})

const emit = defineEmits<{
  (e: 'action'): void
  (e: 'back'): void
}>()

// Localized default texts
const displayTitle = computed(() => {
  if (props.title) return props.title
  return languageStore.t('در حال توسعه', 'Under Development')
})

const displayDescription = computed(() => {
  if (props.description) return props.description
  return languageStore.t(
    'این بخش به‌زودی با امکانات جدید در دسترس شما قرار می‌گیرد.',
    'This feature is currently under construction and will be available soon.'
  )
})

const displayBackText = computed(() => {
  if (props.backButtonText) return props.backButtonText
  return languageStore.t('بازگشت', 'Back')
})
</script>

<template>
  <div 
    class="under-dev-card relative w-full overflow-hidden rounded-2xl border border-border/60 bg-card/50 dark:bg-card/30 backdrop-blur-xl p-6 sm:p-8 text-center flex flex-col items-center justify-center shadow-sm select-none font-sans"
    :dir="languageStore.dir"
  >
    <!-- 1. DYNAMIC MOVING LINEAR PATTERN BACKGROUND -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden z-0 rounded-2xl">
      <!-- Animated moving pattern layer -->
      <div 
        class="absolute -inset-[100%] opacity-15 dark:opacity-10 transition-opacity"
        :class="[
          `pattern-${patternStyle}`,
          `speed-${patternSpeed}`
        ]"
      />
      
      <!-- Radial gradient mask for smooth fading toward edges -->
      <div class="absolute inset-0 bg-radial-[circle_at_center,transparent_35%,var(--color-card)_95%]" />
      
      <!-- Ambient central radial glow -->
      <div class="ambient-glow absolute top-0 left-1/2 -translate-x-1/2 w-48 h-24 bg-primary/10 dark:bg-primary/15 blur-2xl rounded-full pointer-events-none -z-10" />
    </div>

    <!-- 2. CONTENT LAYER WITH PROPER SHADCN SCALE & SPACINGS -->
    <div class="relative z-10 w-full flex flex-col items-center max-w-sm mx-auto gap-5">
      
      <!-- Center Top Lucide Icon Container -->
      <div class="relative group/icon">
        <div class="absolute -inset-2 bg-primary/15 rounded-2xl blur-md opacity-70 group-hover/icon:opacity-100 transition-opacity duration-200" />
        <div class="relative size-14 sm:size-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs backdrop-blur-md transition-transform duration-200 group-hover/icon:scale-105">
          <component :is="icon" class="size-7 sm:size-8 shrink-0 transition-transform duration-200 group-hover/icon:rotate-6" />
        </div>
      </div>

      <!-- Header: Title & Description -->
      <div class="flex flex-col items-center gap-1.5 text-center">
        <h3 class="text-base sm:text-lg font-bold text-foreground tracking-tight leading-snug">
          {{ displayTitle }}
        </h3>
        <p class="text-xs sm:text-sm text-muted-foreground leading-relaxed max-w-xs sm:max-w-sm">
          {{ displayDescription }}
        </p>
      </div>

      <!-- Features Checklist (Properly spaced) -->
      <div 
        v-if="features && features.length > 0"
        class="w-full grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 rounded-xl bg-muted/30 border border-border/40 text-start text-xs text-foreground/90 backdrop-blur-xs"
      >
        <div 
          v-for="(feature, idx) in features" 
          :key="idx"
          class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-background/50 dark:bg-card/50 border border-border/30"
        >
          <CheckCircle2Icon class="size-3.5 text-primary shrink-0" />
          <span class="truncate font-medium text-xs">{{ feature }}</span>
        </div>
      </div>

      <!-- ETA / Timeline Pill -->
      <Badge 
        v-if="eta"
        variant="outline"
        class="px-3 py-1 text-xs font-semibold gap-1.5 rounded-full border-border/60 bg-muted/40 text-muted-foreground shadow-2xs"
      >
        <ClockIcon class="size-3.5 text-primary/80" />
        <span>{{ languageStore.t('زمان تقریبی:', 'Est. Timeline:') }}</span>
        <span class="text-foreground font-bold">{{ eta }}</span>
      </Badge>

      <!-- Actions Footer -->
      <div 
        v-if="actionText || showBackButton" 
        class="flex items-center justify-center gap-3 flex-wrap w-full pt-1"
      >
        <Button 
          v-if="actionText"
          @click="emit('action')"
          variant="default"
          size="sm"
          class="h-9 px-4 text-xs font-bold rounded-xl shadow-xs hover:scale-101 active:scale-98 transition-all cursor-pointer flex items-center gap-2"
        >
          <ZapIcon class="size-3.5" />
          <span>{{ actionText }}</span>
        </Button>

        <Button 
          v-if="showBackButton"
          @click="emit('back')"
          variant="outline"
          size="sm"
          class="h-9 px-3.5 text-xs font-semibold rounded-xl border-border/60 hover:bg-muted/50 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <component :is="languageStore.isFa ? ChevronRightIcon : ChevronLeftIcon" class="size-3.5" />
          <span>{{ displayBackText }}</span>
        </Button>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* 1. Moving Stripes Pattern */
.pattern-stripes {
  background-image: repeating-linear-gradient(
    -45deg,
    var(--color-primary) 0,
    var(--color-primary) 1.5px,
    transparent 0,
    transparent 20px
  );
  animation: linear-stripes-move 25s linear infinite;
}

/* 2. Moving Grid Pattern */
.pattern-grid {
  background-size: 24px 24px;
  background-image: 
    linear-gradient(to right, var(--color-primary) 1px, transparent 1px),
    linear-gradient(to bottom, var(--color-primary) 1px, transparent 1px);
  animation: grid-move 20s linear infinite;
}

/* 3. Moving Dot Matrix Pattern */
.pattern-dots {
  background-size: 18px 18px;
  background-image: radial-gradient(circle, var(--color-primary) 1px, transparent 1px);
  animation: dots-move 25s linear infinite;
}

/* Animation Speeds */
.speed-slow {
  animation-duration: 40s !important;
}
.speed-normal {
  animation-duration: 22s !important;
}
.speed-fast {
  animation-duration: 12s !important;
}

/* Keyframe Animations */
@keyframes linear-stripes-move {
  0% {
    transform: translate3d(0, 0, 0);
  }
  100% {
    transform: translate3d(40px, 40px, 0);
  }
}

@keyframes grid-move {
  0% {
    transform: translate3d(0, 0, 0);
  }
  100% {
    transform: translate3d(24px, 24px, 0);
  }
}

@keyframes dots-move {
  0% {
    transform: translate3d(0, 0, 0);
  }
  100% {
    transform: translate3d(18px, 18px, 0);
  }
}

.under-dev-card {
  will-change: transform, box-shadow;
}
</style>
