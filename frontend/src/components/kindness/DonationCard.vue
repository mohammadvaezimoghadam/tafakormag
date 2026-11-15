<script setup lang="ts">
import { computed } from 'vue'
import type { DonationCampaignProps } from '@/types/kindness'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useLanguageStore } from '@/stores/languageStore'
import {
  formatKindnessNumber,
  getCampaignCategoryLabel,
  getCampaignStatusConfig,
} from '@/utils/kindness'
import {
  BanIcon,
  CheckCircle2Icon,
  ChevronLeftIcon,
  ChevronRightIcon,
  HandHeartIcon,
  HeartIcon,
  ImagesIcon,
  PencilIcon,
  Share2Icon,
  Trash2Icon,
  UsersIcon,
} from '@lucide/vue'

const props = withDefaults(defineProps<DonationCampaignProps>(), {
  authorName: undefined,
  authorAvatar: undefined,
  timestamp: undefined,
  deadline: null,
  iban: null,
  isEmbedded: false,
})

const emit = defineEmits<{
  (e: 'open-detail', campaignId: string | number): void
  (e: 'donate-click', campaignId: string | number): void
  (e: 'topic-click', topicId: string | number): void
  (e: 'transparency-click', imageIndex: number, imageUrl: string): void
  (e: 'share-click', campaignId: string | number): void
  (e: 'edit-click', campaignId: string | number): void
  (e: 'delete-click', campaignId: string | number): void
}>()

const languageStore = useLanguageStore()

const hasDonations = computed(() =>
  Boolean(
    (props.donorsCount && props.donorsCount > 0) ||
      (props.collectedAmount && props.collectedAmount > 0) ||
      (props.recentDonors && props.recentDonors.length > 0)
  )
)

const primaryMediaUrl = computed(() =>
  props.mediaGallery && props.mediaGallery.length > 0 ? props.mediaGallery[0] : null
)

const extraMediaCount = computed(() =>
  props.mediaGallery && props.mediaGallery.length > 1 ? props.mediaGallery.length - 1 : 0
)

const completionPercentage = computed(() => {
  if (!props.targetAmount || props.targetAmount <= 0) return 0
  const pct = Math.round((props.collectedAmount / props.targetAmount) * 100)
  return Math.min(100, Math.max(0, pct))
})

const categoryLabel = computed(() =>
  getCampaignCategoryLabel(props.category, languageStore.isFa)
)

const statusConfig = computed(() =>
  getCampaignStatusConfig(props.status, languageStore.isFa)
)
</script>

<template>
  <Card
    role="button"
    tabindex="0"
    @click="emit('open-detail', id)"
    @keydown.enter.self="emit('open-detail', id)"
    @keydown.space.prevent.self="emit('open-detail', id)"
    class="group relative w-full overflow-hidden rounded-2xl border border-border/70 dark:border-border/60 bg-card/95 backdrop-blur-md text-card-foreground shadow-[0_2px_8px_rgba(0,0,0,0.03)] hover:shadow-[0_6px_18px_rgba(0,0,0,0.07)] hover:border-primary/40 transition-all duration-200 text-start font-sans flex flex-col py-0 gap-0 cursor-pointer select-none"
    :dir="languageStore.dir"
  >
    <!-- 1. COMPACT COVER VISUAL WITH STATUS & CATEGORY PILLS -->
    <div class="relative w-full aspect-[16/10] bg-gradient-to-br from-primary/10 via-primary/5 to-muted/60 flex items-center justify-center overflow-hidden border-b border-border/40">
      <img
        v-if="primaryMediaUrl"
        :src="primaryMediaUrl"
        :alt="title"
        class="size-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
      />
      <div v-else class="flex flex-col items-center justify-center gap-1.5 text-primary/65">
        <HandHeartIcon class="size-8 stroke-[1.75]" />
      </div>

      <div
        v-if="primaryMediaUrl"
        class="absolute inset-x-0 bottom-0 h-14 bg-gradient-to-t from-black/55 via-black/15 to-transparent pointer-events-none"
      />

      <!-- Top-Start: Localized Status Pill -->
      <Badge
        :variant="statusConfig.variant"
        class="absolute top-2 start-2 rounded-lg text-[10px] px-2 py-0.5 font-semibold backdrop-blur-md shadow-2xs border border-border/40"
        :class="
          statusConfig.variant === 'secondary'
            ? 'bg-background/90 text-foreground'
            : ''
        "
      >
        <CheckCircle2Icon v-if="status === 'executed' || status === 'completed'" class="size-3 shrink-0" data-icon="inline-start" />
        <BanIcon v-else-if="status === 'inactive'" class="size-3 shrink-0" data-icon="inline-start" />
        <span>{{ statusConfig.label }}</span>
      </Badge>

      <!-- Bottom-End: Localized Persian/English Category Badge (never raw slug) -->
      <span class="absolute bottom-2 end-2 max-w-[75%] truncate px-2 py-0.5 rounded-lg bg-background/90 dark:bg-card/90 backdrop-blur-md border border-border/50 text-[10px] font-semibold text-foreground shadow-2xs">
        {{ categoryLabel }}
      </span>

      <!-- Bottom-Start: Extra Photos Indicator -->
      <span
        v-if="extraMediaCount > 0"
        class="absolute bottom-2 start-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-black/65 text-white text-[9.5px] font-bold"
      >
        <ImagesIcon class="size-2.5 shrink-0" />
        <span>+{{ formatKindnessNumber(extraMediaCount, languageStore.isFa) }}</span>
      </span>
    </div>

    <!-- 2. UNCLUTTERED BODY: Title + Progress Only -->
    <CardContent class="p-3 flex-1 flex flex-col justify-between gap-2.5">
      <div class="flex flex-col gap-1 text-start">
        <h3 class="text-xs sm:text-[13px] font-bold leading-snug text-foreground line-clamp-2 min-h-[2.35rem]">
          {{ title }}
        </h3>
      </div>

      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between gap-1 text-[10.5px]">
          <span class="font-extrabold text-primary shrink-0">
            {{ formatKindnessNumber(completionPercentage, languageStore.isFa) }}٪
            {{ languageStore.t('پیشرفت', 'funded') }}
          </span>
          <span class="inline-flex items-center gap-1 text-muted-foreground font-medium truncate">
            <UsersIcon class="size-3 text-primary/80 shrink-0" />
            <span>
              {{ formatKindnessNumber(donorsCount, languageStore.isFa) }}
              {{ languageStore.t('حامی', 'supporters') }}
            </span>
          </span>
        </div>

        <Progress :model-value="completionPercentage" class="h-1.5 w-full bg-muted rounded-full" />

        <div class="flex items-center justify-between gap-1.5 text-[10px] text-muted-foreground pt-0.5">
          <span class="font-semibold text-foreground truncate">
            {{ formatKindnessNumber(collectedAmount, languageStore.isFa) }}
            <span class="font-normal text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
          </span>
          <span class="truncate shrink-0">
            {{ languageStore.t('هدف:', 'Goal:') }}
            {{ formatKindnessNumber(targetAmount, languageStore.isFa) }}
          </span>
        </div>
      </div>
    </CardContent>

    <!-- 3. TWO-ROW GRID-SAFE FOOTER (All 4 Actions Fit Cleanly Inside 2-Column Grid) -->
    <CardFooter class="px-2.5 pb-2.5 pt-2 bg-muted/15 border-t border-border/40 flex flex-col gap-1.5">
      <!-- Row 1: Primary Full-Width CTA -->
      <Button
        v-if="status === 'active'"
        type="button"
        variant="default"
        size="sm"
        class="w-full h-8 px-2.5 text-[11px] font-bold rounded-xl shadow-xs active:scale-[0.98] transition-all cursor-pointer gap-1.5"
        @click.stop="emit('donate-click', id)"
      >
        <HeartIcon class="fill-current size-3.5 shrink-0" />
        <span class="truncate">{{ languageStore.t('مشارکت در مهربانی', 'Support Campaign') }}</span>
      </Button>

      <Button
        v-else
        type="button"
        variant="outline"
        size="sm"
        class="w-full h-8 px-2.5 text-[11px] font-bold rounded-xl shadow-none active:scale-[0.98] transition-all cursor-pointer gap-1.5"
        @click.stop="emit('open-detail', id)"
      >
        <BanIcon v-if="status === 'inactive'" class="size-3.5 text-destructive shrink-0" />
        <CheckCircle2Icon v-else class="size-3.5 text-primary shrink-0" />
        <span class="truncate">
          {{ status === 'inactive'
            ? languageStore.t('مشاهده جزئیات (متوقف)', 'View Details (Inactive)')
            : languageStore.t('مشاهده جزئیات پویش', 'View Campaign Details')
          }}
        </span>
      </Button>

      <!-- Row 2: Details Link + Owner/Share Icon Actions (Always Visible & Never Clipped) -->
      <div class="flex items-center justify-between gap-1 w-full">
        <button
          type="button"
          class="inline-flex items-center gap-0.5 text-[10.5px] font-semibold text-muted-foreground hover:text-primary transition-colors cursor-pointer py-1 px-1 rounded-md min-w-0 truncate"
          @click.stop="emit('open-detail', id)"
        >
          <span class="truncate">{{ languageStore.t('جزئیات پویش', 'Details') }}</span>
          <ChevronLeftIcon v-if="languageStore.isFa" class="size-3 shrink-0" />
          <ChevronRightIcon v-else class="size-3 shrink-0" />
        </button>

        <div class="flex items-center gap-1 shrink-0">
          <Button
            v-if="canEdit && status !== 'inactive'"
            type="button"
            variant="outline"
            size="icon"
            class="size-7 rounded-lg border-border/60 hover:bg-muted/60 text-primary hover:text-primary shrink-0 cursor-pointer shadow-none active:scale-95 transition-all"
            :title="languageStore.t('ویرایش پویش', 'Edit Campaign')"
            :aria-label="languageStore.t('ویرایش پویش', 'Edit Campaign')"
            @click.stop="emit('edit-click', id)"
          >
            <PencilIcon class="size-3.5" />
          </Button>

          <Button
            v-if="canEdit && status !== 'inactive'"
            type="button"
            variant="outline"
            size="icon"
            class="size-7 rounded-lg border-destructive/30 hover:bg-destructive/10 text-destructive hover:text-destructive shrink-0 cursor-pointer shadow-none active:scale-95 transition-all"
            :title="hasDonations ? languageStore.t('متوقف‌سازی پویش', 'Deactivate Campaign') : languageStore.t('حذف پویش', 'Delete Campaign')"
            :aria-label="hasDonations ? languageStore.t('متوقف‌سازی پویش', 'Deactivate Campaign') : languageStore.t('حذف پویش', 'Delete Campaign')"
            @click.stop="emit('delete-click', id)"
          >
            <Trash2Icon class="size-3.5" />
          </Button>

          <Button
            type="button"
            variant="outline"
            size="icon"
            class="size-7 rounded-lg border-border/60 hover:bg-muted/60 text-muted-foreground hover:text-foreground shrink-0 cursor-pointer shadow-none active:scale-95 transition-all"
            :title="languageStore.t('اشتراک‌گذاری', 'Share')"
            :aria-label="languageStore.t('اشتراک‌گذاری', 'Share')"
            @click.stop="emit('share-click', id)"
          >
            <Share2Icon class="size-3.5" />
          </Button>
        </div>
      </div>
    </CardFooter>
  </Card>
</template>
