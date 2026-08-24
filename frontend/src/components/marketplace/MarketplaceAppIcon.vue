<script setup lang="ts">
import { computed } from 'vue'
import { 
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
  /** Custom badge text (e.g. 'ویژه', 'جدید', 'نصب‌شده') */
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
  badgeVariant: 'outline',
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
  if (appIsComingSoon.value) return ''
  if (props.app?.badge) return props.app.badge
  if (props.badge) return props.badge
  if (props.app?.isInstalled || props.isInstalled) return languageStore.t('نصب‌شده', 'Installed')
  return ''
})

const appBadgeVariant = computed(() => {
  if (props.app?.badgeVariant) return props.app.badgeVariant
  if (props.badgeVariant) return props.badgeVariant
  return 'outline'
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
      return 'size-14 rounded-2xl p-2.5'
    case 'md':
      return 'size-18 rounded-2xl p-3'
    case 'lg':
      return 'size-24 rounded-3xl p-3.5'
    case 'responsive':
    default:
      return 'w-full aspect-square rounded-2xl sm:rounded-3xl p-3 sm:p-3.5'
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
      'group relative flex flex-col items-start text-start select-none font-sans outline-none cursor-pointer transition-all duration-200 focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background w-full p-1 rounded-2xl',
      disabled ? 'cursor-not-allowed opacity-60' : 'hover:-translate-y-1 active:scale-95',
      props.class
    )"
    :dir="languageStore.dir"
    :title="appTitle"
    :aria-label="appTitle + (appIsComingSoon ? ' (' + languageStore.t('به‌زودی', 'Coming Soon') + ')' : '')"
  >
    <!-- Top Floating Status Badge (Bordered Outline Badge) -->
    <div 
      v-if="appBadge" 
      class="absolute -top-2 start-2 z-20 pointer-events-none transition-transform duration-200 group-hover:scale-105"
    >
      <Badge
        :variant="appBadgeVariant"
        class="text-[9px] sm:text-[10px] font-bold px-2 py-0.5 rounded-full border border-border/80 bg-background/95 dark:bg-card/95 text-foreground shadow-2xs backdrop-blur-xs whitespace-nowrap leading-tight"
      >
        <CheckIcon v-if="props.app?.isInstalled || props.isInstalled" class="size-2.5 me-0.5 shrink-0 inline-block text-emerald-500" />
        <span>{{ appBadge }}</span>
      </Badge>
    </div>

    <!-- 1. ICON SQUIRCLE / SQUARE CONTAINER -->
    <div
      :class="cn(
        'relative flex items-center justify-center overflow-hidden border shadow-2xs transition-all duration-200 w-full shrink-0',
        iconBoxSizeClasses,
        // Active / Available State Styling
        !appIsComingSoon && [
          'bg-gradient-to-b from-card to-card/85 border-border/70 group-hover:border-primary/40 group-hover:shadow-xs',
          'dark:from-card dark:to-muted/25 dark:border-border/50'
        ],
        // Coming Soon State Styling
        appIsComingSoon && [
          'bg-muted/20 border-dashed border-border/60 group-hover:border-border/80 group-hover:bg-muted/30',
          'dark:bg-card/20 dark:border-border/40'
        ]
      )"
    >
      <!-- Subtle top-glare highlight -->
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
            class="size-full object-cover transition-transform duration-300 group-hover:scale-105" 
          />
          <AvatarFallback class="size-full bg-primary/10 text-primary font-bold text-xs sm:text-sm flex items-center justify-center">
            {{ fallbackLetter }}
          </AvatarFallback>
        </Avatar>

        <!-- Vector Icon Fallback -->
        <div 
          v-else 
          class="size-full rounded-xl sm:rounded-2xl bg-primary/10 text-primary flex items-center justify-center transition-transform duration-300 group-hover:scale-105"
        >
          <component :is="appIconComponent" :class="cn('shrink-0', lucideIconSizeClasses)" />
        </div>
      </template>

      <!-- B) Coming Soon State -->
      <template v-else>
        <!-- Grayscale / Dimmed Image Icon with Coming Soon overlay -->
        <div v-if="appIconUrl" class="relative size-full rounded-xl sm:rounded-2xl overflow-hidden opacity-25 grayscale">
          <img :src="appIconUrl" :alt="appTitle" class="size-full object-cover" />
        </div>

        <!-- Coming Soon Vector Icon -->
        <div 
          v-else 
          class="size-full rounded-xl sm:rounded-2xl bg-muted/30 text-muted-foreground/40 flex items-center justify-center transition-colors duration-200"
        >
          <component 
            :is="appIconComponent" 
            :class="cn('shrink-0 opacity-40 transition-transform duration-200 group-hover:scale-105', lucideIconSizeClasses)" 
          />
        </div>

        <!-- Clean "به‌زودی" Bordered Badge Overlay on Icon -->
        <div class="absolute inset-0 bg-background/30 backdrop-blur-[1px] flex items-center justify-center z-10 pointer-events-none p-1.5">
          <Badge
            variant="outline"
            class="px-2.5 py-0.5 rounded-full border border-border/80 bg-card/95 dark:bg-card/95 text-[10px] sm:text-[11px] font-bold text-muted-foreground shadow-2xs select-none"
          >
            {{ languageStore.t('به‌زودی', 'Soon') }}
          </Badge>
        </div>
      </template>
    </div>

    <!-- 2. APP TITLE & DETAILS BELOW ICON (Generous breathing room & clean mobile typography) -->
    <div v-if="showTitle" class="mt-3.5 sm:mt-4 pt-1 w-full flex flex-col items-start text-start gap-1 px-0.5">
      <!-- Title -->
      <span 
        class="w-full text-xs sm:text-[13px] font-bold text-foreground leading-normal line-clamp-1 group-hover:text-primary transition-colors duration-200 text-start"
        :title="appTitle"
      >
        {{ appTitle }}
      </span>

      <!-- Optional Category / Subtitle -->
      <span 
        v-if="showCategory && appCategory" 
        class="w-full text-[10.5px] sm:text-[11.5px] text-muted-foreground line-clamp-1 leading-normal text-start"
      >
        {{ appCategory }}
      </span>

      <!-- Optional Rating snippet (Only rendered when available and NOT coming soon) -->
      <div 
        v-if="appRating && appRating > 0 && !appIsComingSoon" 
        class="flex items-center gap-1 mt-1 text-[10px] sm:text-[11px] text-muted-foreground font-medium text-start"
      >
        <StarIcon class="size-3 text-amber-500 fill-amber-500 shrink-0" />
        <span class="font-sans font-bold">{{ languageStore.n(appRating.toFixed(1)) }}</span>
      </div>
    </div>
  </button>
</template>