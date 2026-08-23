<script setup lang="ts">
import { computed } from 'vue'
import { 
  SparklesIcon, 
  ClockIcon, 
  LayersIcon, 
  StarIcon, 
  CheckIcon
} from '@lucide/vue'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'
import { useLanguageStore } from '@/stores/languageStore'
import type { MarketplaceApp, AppIconSize } from '@/types/marketplace'

const languageStore = useLanguageStore()

export interface MarketplaceAppIconProps {
  /** Optional full app object */
  app?: MarketplaceApp
  /** App / Plugin Name */
  title?: string
  /** Short subtitle or category */
  category?: string
  /** Icon image URL (PNG, SVG, WebP) */
  iconUrl?: string
  /** Lucide icon component fallback */
  icon?: any
  /** Whether the plugin is in Coming Soon / به‌زودی state */
  isComingSoon?: boolean
  /** Custom badge text (e.g. 'ویژه', 'جدید', 'به‌زودی') */
  badge?: string
  /** Badge color variant */
  badgeVariant?: 'default' | 'secondary' | 'outline' | 'destructive'
  /** Sizing variant */
  size?: AppIconSize
  /** Star rating value (0-5) */
  rating?: number
  /** Whether this app is already installed */
  isInstalled?: boolean
  /** Whether to show the title below icon */
  showTitle?: boolean
  /** Whether to show category below title */
  showCategory?: boolean
  /** Whether clicking is disabled */
  disabled?: boolean
  /** Custom class for root container */
  class?: string
}

const props = withDefaults(defineProps<MarketplaceAppIconProps>(), {
  title: '',
  category: '',
  iconUrl: '',
  icon: undefined,
  isComingSoon: false,
  badge: '',
  badgeVariant: 'secondary',
  size: 'responsive',
  rating: 0,
  isInstalled: false,
  showTitle: true,
  showCategory: false,
  disabled: false,
  class: ''
})

const emit = defineEmits<{
  (e: 'click', app?: MarketplaceApp): void
}>()

// Resolved fields taking app object or individual props
const appTitle = computed(() => props.app?.title || props.title || languageStore.t('افزونه', 'Plugin'))
const appCategory = computed(() => props.app?.category || props.category || '')
const appIconUrl = computed(() => props.app?.iconUrl || props.iconUrl || '')
const appIconComponent = computed(() => props.app?.icon || props.icon || LayersIcon)
const appIsComingSoon = computed(() => props.app?.isComingSoon ?? props.isComingSoon)
const appBadge = computed(() => {
  if (props.app?.badge) return props.app.badge
  if (props.badge) return props.badge
  if (appIsComingSoon.value) return languageStore.t('به‌زودی', 'Soon')
  if (props.app?.isInstalled || props.isInstalled) return languageStore.t('نصب‌شده', 'Installed')
  return ''
})
const appBadgeVariant = computed(() => {
  if (props.app?.badgeVariant) return props.app.badgeVariant
  if (props.badgeVariant) return props.badgeVariant
  if (appIsComingSoon.value) return 'secondary'
  if (props.app?.isInstalled || props.isInstalled) return 'default'
  return 'secondary'
})
const appRating = computed(() => props.app?.rating ?? props.rating)

const handleClick = () => {
  if (props.disabled) return
  emit('click', props.app)
}

// First letter for avatar fallback
const fallbackLetter = computed(() => {
  const t = appTitle.value.trim()
  return t ? t.charAt(0).toUpperCase() : 'A'
})

// Dimension styling classes based on size prop
const iconBoxSizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'size-14 rounded-2xl p-2'
    case 'md':
      return 'size-18 rounded-2xl p-2.5'
    case 'lg':
      return 'size-22 rounded-3xl p-3'
    case 'responsive':
    default:
      return 'w-full aspect-square rounded-2xl sm:rounded-3xl p-2.5 sm:p-3'
  }
})

const lucideIconSizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'size-6'
    case 'md':
      return 'size-8'
    case 'lg':
      return 'size-10'
    case 'responsive':
    default:
      return 'size-7 sm:size-9'
  }
})
</script>

<template>
  <button
    type="button"
    @click="handleClick"
    :disabled="disabled"
    :class="cn(
      'group relative flex flex-col items-center text-center select-none font-sans outline-none cursor-pointer transition-all duration-200 focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
      disabled ? 'cursor-not-allowed opacity-60' : 'hover:-translate-y-1 active:scale-95',
      props.class
    )"
    :dir="languageStore.dir"
    :title="appTitle"
    :aria-label="appTitle + (appIsComingSoon ? ' (' + languageStore.t('به‌زودی', 'Coming Soon') + ')' : '')"
  >
    <!-- Top Floating Status Badge -->
    <div 
      v-if="appBadge" 
      class="absolute -top-2.5 left-1/2 -translate-x-1/2 z-20 pointer-events-none transition-transform duration-200 group-hover:scale-105"
    >
      <Badge
        :variant="appBadgeVariant"
        class="text-[9px] sm:text-[10px] font-extrabold px-1.5 sm:px-2 py-0.2 shadow-xs border backdrop-blur-xs whitespace-nowrap leading-tight"
        :class="cn(
          appIsComingSoon && 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30'
        )"
      >
        <SparklesIcon v-if="appIsComingSoon" class="size-2.5 me-0.5 shrink-0 inline-block animate-pulse" />
        <CheckIcon v-else-if="props.app?.isInstalled || props.isInstalled" class="size-2.5 me-0.5 shrink-0 inline-block" />
        <span>{{ appBadge }}</span>
      </Badge>
    </div>

    <!-- 1. ICON SQUIRCLE / SQUARE CONTAINER -->
    <div
      :class="cn(
        'relative flex items-center justify-center overflow-hidden border shadow-sm transition-all duration-200',
        iconBoxSizeClasses,
        // Active / Available State Styling
        !appIsComingSoon && [
          'bg-gradient-to-b from-card to-card/80 border-border/80 group-hover:border-primary/40 group-hover:shadow-md group-hover:shadow-primary/5',
          'dark:from-card dark:to-muted/30 dark:border-border/60'
        ],
        // Coming Soon State Styling
        appIsComingSoon && [
          'bg-muted/30 border-dashed border-border/80 group-hover:border-primary/40 group-hover:bg-muted/40',
          'dark:bg-card/20 dark:border-border/60'
        ]
      )"
    >
      <!-- Glass subtle top-glare highlight -->
      <div 
        class="absolute inset-x-0 top-0 h-1/2 bg-gradient-to-b from-white/10 to-transparent pointer-events-none rounded-t-2xl z-10" 
      />

      <!-- A) Standard / Active Image Icon -->
      <template v-if="!appIsComingSoon">
        <!-- If iconUrl image is provided -->
        <Avatar v-if="appIconUrl" class="size-full rounded-xl sm:rounded-2xl overflow-hidden shadow-2xs">
          <AvatarImage 
            :src="appIconUrl" 
            :alt="appTitle" 
            class="size-full object-cover transition-transform duration-300 group-hover:scale-108" 
          />
          <AvatarFallback class="size-full bg-primary/10 text-primary font-black text-sm sm:text-base flex items-center justify-center">
            {{ fallbackLetter }}
          </AvatarFallback>
        </Avatar>

        <!-- Vector Icon Fallback -->
        <div 
          v-else 
          class="size-full rounded-xl sm:rounded-2xl bg-primary/10 text-primary flex items-center justify-center transition-transform duration-300 group-hover:scale-108"
        >
          <component :is="appIconComponent" :class="cn('shrink-0', lucideIconSizeClasses)" />
        </div>
      </template>

      <!-- B) Coming Soon State -->
      <template v-else>
        <!-- Grayscale / Dimmed Image Icon with Coming Soon overlay -->
        <div v-if="appIconUrl" class="relative size-full rounded-xl sm:rounded-2xl overflow-hidden opacity-35 grayscale">
          <img :src="appIconUrl" :alt="appTitle" class="size-full object-cover" />
        </div>

        <!-- Coming Soon Vector Icon & Subtle Pulsing Clock Glow -->
        <div 
          v-else 
          class="size-full rounded-xl sm:rounded-2xl bg-muted/50 text-muted-foreground/80 flex flex-col items-center justify-center gap-1 transition-colors duration-200 group-hover:text-primary"
        >
          <component 
            :is="appIconComponent || ClockIcon" 
            :class="cn('shrink-0 opacity-70 transition-transform duration-200 group-hover:scale-110', lucideIconSizeClasses)" 
          />
        </div>

        <!-- Subtle overlay lock / clock tag inside container -->
        <div class="absolute inset-0 bg-background/25 backdrop-blur-[1px] flex items-center justify-center z-10 pointer-events-none">
          <div class="size-6 sm:size-7 rounded-full bg-card/90 border border-border/80 text-muted-foreground flex items-center justify-center shadow-xs">
            <ClockIcon class="size-3.5 sm:size-4 text-amber-600 dark:text-amber-400" />
          </div>
        </div>
      </template>
    </div>

    <!-- 2. APP TITLE & DETAILS BELOW ICON -->
    <div v-if="showTitle" class="mt-2 w-full flex flex-col items-center px-0.5 gap-0.5">
      <!-- Title -->
      <span 
        class="w-full text-[11px] sm:text-xs font-bold text-foreground leading-snug line-clamp-1 group-hover:text-primary transition-colors duration-200"
        :title="appTitle"
      >
        {{ appTitle }}
      </span>

      <!-- Optional Category / Subtitle -->
      <span 
        v-if="showCategory && appCategory" 
        class="text-[9px] sm:text-[10px] text-muted-foreground line-clamp-1 leading-tight"
      >
        {{ appCategory }}
      </span>

      <!-- Optional Rating snippet -->
      <div 
        v-if="appRating && appRating > 0 && !appIsComingSoon" 
        class="flex items-center gap-0.5 mt-0.5 text-[9px] sm:text-[10px] text-muted-foreground font-medium"
      >
        <StarIcon class="size-2.5 text-amber-500 fill-amber-500 shrink-0" />
        <span>{{ appRating.toFixed(1) }}</span>
      </div>
    </div>
  </button>
</template>