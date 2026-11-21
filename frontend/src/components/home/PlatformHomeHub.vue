<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'

import { useUserStore } from '@/stores/userStore'
import {
  listHomeDonationCampaigns,
  listMyShelfBooks,
} from '@/api/shelf'
import type {
  HomeDonationCampaign,
  ShelfBook,
} from '@/types/shelf'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToastStore } from '@/stores/toastStore'
import { generateQrDataUrl } from '@/utils/qrCode'
import HorizontalSliderRow from '@/components/home/HorizontalSliderRow.vue'
import { getCampaignCategoryLabel, getCampaignStatusConfig } from '@/utils/kindness'
import {
  BookOpenIcon,
  CheckCircle2Icon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  HandHeartIcon,
  LayersIcon,
  QrCodeIcon,
  Share2Icon,
  SmartphoneIcon,
  SparklesIcon,
} from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    topicsCount?: number
  }>(),
  {
    topicsCount: 0,
  }
)

const emit = defineEmits<{
  (e: 'open-topics'): void
  (e: 'open-donations'): void
  (e: 'open-book-donations'): void
  (e: 'open-shelf'): void
  (e: 'open-shelf-book', book: ShelfBook): void
  (e: 'open-campaign', campaignId: string | number): void
}>()

const languageStore = useLanguageStore()
const userStore = useUserStore()
const books = ref<ShelfBook[]>([])
const campaigns = ref<HomeDonationCampaign[]>([])

const isLoadingBooks = ref(false)
const isLoadingCampaigns = ref(false)

const hasAuthSession = computed(
  () =>
    userStore.isAuthenticated ||
    Boolean(
      (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('auth_token')) ||
        (typeof localStorage !== 'undefined' && localStorage.getItem('auth_token'))
    )
)

const visibleBooks = computed(() => {
  return books.value.filter((book) => (book.available_quantity ?? book.quantity ?? 1) > 0)
})

const topicsSubtitle = computed(() => {
  if (props.topicsCount > 0) {
    return languageStore.t(
      `${languageStore.n(props.topicsCount)} تاپیک و کانال موضوعی`,
      `${props.topicsCount} topics & channels`
    )
  }
  return languageStore.t('کانال‌ها، مقالات و گفتگوها', 'Channels, notes & discussions')
})

const getShortCode = (book: ShelfBook): string | null => {
  return book.physical_copy_summary?.short_code || (book as any).short_code || null
}

const getFormatBadge = (book: ShelfBook): string => {
  return book.book_format === 'digital'
    ? languageStore.t('دیجیتال', 'Digital')
    : languageStore.t('چاپی', 'Physical')
}

const getDispositionLabel = (book: ShelfBook): string | null => {
  if (book.disposition === 'for_donation') {
    return languageStore.t('اهدا', 'Donate')
  }
  if (book.disposition === 'for_sale') {
    return languageStore.t('فروشی', 'Sale')
  }
  if (book.disposition === 'circulating') {
    return languageStore.t('در گردش', 'Circulating')
  }
  return null
}

const resolveMediaUrl = (raw?: string | null): string | null => {
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw
  }
  return `/${raw}`
}

const getCampaignCover = (campaign: HomeDonationCampaign): string | null => {
  const firstAtt = campaign.attachments?.find((a) => !a.is_video && a.url)?.url
  return resolveMediaUrl(firstAtt || campaign.cover_image)
}

const getCampaignProgressPercent = (campaign: HomeDonationCampaign): number => {
  const target = Number(campaign.target_amount) || 0
  const collected = Number(campaign.collected_amount) || 0
  if (target <= 0) return 0
  return Math.min(100, Math.max(0, Math.round((collected / target) * 100)))
}

const getCampaignStatusLabel = (status: string): string => {
  return getCampaignStatusConfig(status, languageStore.isFa).label
}

const formatToman = (val: string | number | null | undefined): string => {
  const num = Number(val ?? 0)
  if (!Number.isFinite(num)) return '۰'
  return num.toLocaleString(languageStore.isFa ? 'fa-IR' : 'en-US')
}

const loadAllHomeSections = async () => {
  isLoadingBooks.value = true
  isLoadingCampaigns.value = true

  const isAuth = hasAuthSession.value

  const booksPromise = isAuth
    ? listMyShelfBooks()
    : Promise.resolve([] as ShelfBook[])

  const campaignsPromise = listHomeDonationCampaigns()

  const [booksRes, campaignsRes] = await Promise.allSettled([
    booksPromise,
    campaignsPromise,
  ])

  books.value = booksRes.status === 'fulfilled' ? booksRes.value : []
  campaigns.value = campaignsRes.status === 'fulfilled' ? campaignsRes.value : []

  isLoadingBooks.value = false
  isLoadingCampaigns.value = false
}

onMounted(() => {
  loadAllHomeSections()
})

watch(
  () => [userStore.isAuthenticated, userStore.user?.id],
  () => {
    loadAllHomeSections()
  }
)

const toastStore = useToastStore()
const isQrDialogOpen = ref(false)
const selectedQrBook = ref<ShelfBook | null>(null)

const getQrBookUrl = (book: ShelfBook | null): string => {
  const origin = typeof window !== 'undefined' && window.location ? window.location.origin : 'https://tafakormag.ir'
  if (!book) return origin
  const code = getShortCode(book)
  return code ? `${origin}/b/${code}` : `${origin}/marketplace`
}

const handleShowBookQr = (book: ShelfBook) => {
  selectedQrBook.value = book
  isQrDialogOpen.value = true
}

const copyShortCode = async (code: string) => {
  try {
    await navigator.clipboard.writeText(code)
    toastStore.triggerToast(
      languageStore.t('کد کتاب کپی شد', 'Code copied'),
      'success'
    )
  } catch {
    toastStore.triggerToast(
      languageStore.t('کپی ناموفق بود', 'Failed to copy'),
      'error'
    )
  }
}

const copyQrLink = async (book: ShelfBook | null) => {
  if (!book) return
  const url = getQrBookUrl(book)
  try {
    await navigator.clipboard.writeText(url)
    toastStore.triggerToast(
      languageStore.t('لینک شناسنامه کتاب کپی شد', 'Link copied'),
      'success'
    )
  } catch {
    toastStore.triggerToast(
      languageStore.t('کپی ناموفق بود', 'Failed to copy'),
      'error'
    )
  }
}

const handleOpenBookDonations = () => {
  emit('open-book-donations')
}

defineExpose({
  reload: loadAllHomeSections,
})
</script>

<template>
  <div class="flex flex-col gap-6 w-full pb-24">
    <!-- 1. Hero Gateway: Topics List -->
    <div class="w-full">
      <button
        type="button"
        @click="emit('open-topics')"
        class="w-full min-w-0 h-[84px] rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 hover:border-primary/40 hover:bg-muted/40 active:scale-[0.985] transition-all duration-150 shadow-xs px-3 py-2.5 flex items-center gap-2.5 text-start cursor-pointer"
      >
        <LayersIcon class="size-7 text-foreground shrink-0" />

        <div class="flex-1 min-w-0 flex flex-col justify-center gap-0.5">
          <span class="text-[14px] font-extrabold text-foreground truncate leading-tight">
            {{ languageStore.t('لیست تاپیک‌ها', 'Topics List') }}
          </span>
          <span class="text-[11px] text-muted-foreground truncate leading-tight">
            {{ topicsSubtitle }}
          </span>
        </div>

        <ChevronLeftIcon
          v-if="languageStore.isFa"
          class="size-4 text-muted-foreground/70 shrink-0"
        />
        <ChevronRightIcon
          v-else
          class="size-4 text-muted-foreground/70 shrink-0"
        />
      </button>
    </div>

    <!-- 2. My Bookshelf Horizontal Slider -->
    <section class="flex flex-col gap-3">
      <div class="flex items-center justify-between px-0.5">
        <h2 class="text-sm font-extrabold text-foreground">
          {{ languageStore.t('قفسه کتاب من', 'My Bookshelf') }}
        </h2>

        <button
          v-if="hasAuthSession"
          type="button"
          @click="emit('open-shelf')"
          class="flex items-center gap-0.5 text-xs font-bold text-primary hover:opacity-80 active:scale-95 transition-all select-none cursor-pointer"
        >
          <span>{{ languageStore.t('همه', 'All') }}</span>
          <ChevronLeftIcon v-if="languageStore.isFa" class="size-3.5" />
          <ChevronRightIcon v-else class="size-3.5" />
        </button>
      </div>

      <!-- Loading State: Skeletons -->
      <div v-if="isLoadingBooks" class="grid grid-flow-col auto-cols-[calc((100%-10px)/2)] sm:auto-cols-[calc((100%-20px)/3)] gap-2.5 overflow-hidden pb-2">
        <div
          v-for="n in 3"
          :key="'home-book-sk-' + n"
          class="w-full min-w-0 h-[212px] rounded-2xl border border-border/60 bg-card/70 overflow-hidden flex flex-col"
        >
          <Skeleton class="h-[110px] w-full rounded-none" />
          <div class="p-2.5 flex flex-col gap-2">
            <Skeleton class="h-3.5 w-24" />
            <Skeleton class="h-3 w-16" />
          </div>
        </div>
      </div>

      <!-- Unauthenticated State Card -->
      <div
        v-else-if="!hasAuthSession"
        class="rounded-2xl border border-border/60 bg-card/85 dark:bg-card/65 backdrop-blur-md p-6 flex flex-col items-center justify-center text-center gap-3 shadow-xs"
      >
        <div class="size-11 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shadow-2xs">
          <HandHeartIcon class="size-5.5" />
        </div>
        <div class="flex flex-col gap-1 max-w-xs">
          <span class="text-xs font-bold text-foreground">
            {{ languageStore.t('مشاهده کتاب‌های اهدایی', 'View Gifted Books') }}
          </span>
          <span class="text-[11px] text-muted-foreground leading-relaxed">
            {{ languageStore.t('برای مشاهده کتاب‌های اهدایی تفکر، وارد حساب کاربری خود شوید.', 'Login to your account to view books gifted through Tafakor.') }}
          </span>
        </div>
        <Button
          type="button"
          size="sm"
          class="rounded-xl font-bold bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-4 text-xs"
          @click="userStore.isLoginModalOpen = true"
        >
          {{ languageStore.t('ورود به حساب', 'Login') }}
        </Button>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="visibleBooks.length === 0"
        class="py-6 px-4 flex flex-col items-center justify-center text-center gap-2"
      >
        <div class="size-10 rounded-2xl bg-muted/50 flex items-center justify-center text-muted-foreground/70">
          <BookOpenIcon class="size-5.5" />
        </div>

        <span class="text-xs font-semibold text-muted-foreground">
          {{ languageStore.t('هنوز کتابی در قفسه شما ثبت نشده است', 'No books in your shelf yet') }}
        </span>
      </div>

      <!-- Book Slider Row -->
      <HorizontalSliderRow
        v-else
        layout="grid"
        track-class="auto-cols-[calc((100%-10px)/2)] sm:auto-cols-[calc((100%-20px)/3)] gap-2.5"
      >
        <div
          v-for="book in visibleBooks"
          :key="book.id"
          role="button"
          tabindex="0"
          @click="emit('open-shelf-book', book)"
          @keydown.enter.prevent="emit('open-shelf-book', book)"
          class="w-full min-w-0 h-auto snap-start rounded-2xl border border-border/60 bg-card/85 dark:bg-card/65 backdrop-blur-md shadow-xs hover:border-primary/40 hover:shadow-sm transition-all overflow-hidden flex flex-col select-none cursor-pointer"
        >
          <div class="h-[112px] w-full bg-muted/50 dark:bg-muted/30 relative flex items-center justify-center overflow-hidden">
            <img
              v-if="resolveMediaUrl(book.book_title.cover_image)"
              :src="resolveMediaUrl(book.book_title.cover_image)!"
              :alt="book.book_title.title"
              class="size-full object-cover"
            />
            <SmartphoneIcon
              v-else-if="book.book_format === 'digital'"
              class="size-7 text-muted-foreground/70"
            />
            <BookOpenIcon v-else class="size-7 text-muted-foreground/70" />

            <!-- Quantity badge -->
            <div
              class="absolute top-1.5 start-1.5 px-1.5 py-0.5 rounded-md bg-background/95 border border-border/60 text-[10px] font-bold text-foreground shadow-2xs"
            >
              <span>{{ languageStore.n(book.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}</span>
            </div>

            <!-- QR Code Button on Book Cover -->
            <button
              type="button"
              @click.stop="handleShowBookQr(book)"
              class="absolute top-1.5 end-1.5 p-1 rounded-md bg-background/95 hover:bg-muted border border-border/60 text-foreground shadow-2xs transition-all active:scale-90 select-none cursor-pointer"
              :title="languageStore.t('شناسنامه و بارکد کتاب', 'Book QR Code')"
            >
              <QrCodeIcon class="size-3.5 text-foreground" />
            </button>
          </div>

          <div class="p-2.5 flex-1 flex flex-col justify-between gap-2 text-start">
            <div class="flex flex-col gap-1">
              <h3 class="text-[11.5px] font-bold text-foreground line-clamp-2 leading-snug">
                {{ book.book_title.title }}
              </h3>
              <p class="text-[10px] text-muted-foreground truncate">
                {{ book.book_title.author }}
              </p>
            </div>

            <div class="flex flex-col gap-2 pt-1.5 border-t border-border/40">
              <!-- Recipient / Gift: Show Neutral Gift Badge -->
              <div
                v-if="book.is_gift"
                class="w-full py-1 text-center text-[10px] font-bold text-foreground bg-muted/80 border border-border/70 rounded-xl truncate flex items-center justify-center gap-1 shadow-2xs"
              >
                <SparklesIcon class="size-3 text-muted-foreground shrink-0" />
                <span class="truncate">هدیه از طرف {{ book.gifted_by_name || 'ادمین تفکر' }}</span>
              </div>
              <div
                v-else
                class="w-full py-1 text-center text-[10px] font-medium text-muted-foreground bg-muted/40 border border-border/40 rounded-xl truncate"
              >
                <span>{{ book.reading_status_display || languageStore.t('در قفسه', 'In Shelf') }}</span>
              </div>
            </div>
          </div>
        </div>
      </HorizontalSliderRow>
    </section>

    <!-- 3. Donation Campaigns Horizontal Slider (پویش‌های نیکوکاری و اهدا) -->
    <section class="flex flex-col gap-3">
      <div class="flex items-center justify-between px-0.5">
        <div class="flex items-center gap-2">
          <h2 class="text-sm font-extrabold text-foreground">
            {{ languageStore.t('پویش‌های نیکوکاری و اهدا', 'Donation Campaigns') }}
          </h2>
          <span class="size-2 rounded-full bg-primary shrink-0" />
        </div>

        <button
          v-if="campaigns.length > 0"
          type="button"
          @click="emit('open-donations')"
          class="flex items-center gap-0.5 text-xs font-bold text-primary hover:opacity-80 active:scale-95 transition-all select-none cursor-pointer"
        >
          <span>{{ languageStore.t('همه', 'All') }}</span>
          <ChevronLeftIcon v-if="languageStore.isFa" class="size-3.5" />
          <ChevronRightIcon v-else class="size-3.5" />
        </button>
      </div>

      <!-- Loading State: Skeletons -->
      <div v-if="isLoadingCampaigns" class="grid grid-flow-col auto-cols-[100%] sm:auto-cols-[calc((100%-12px)/2)] gap-3 overflow-hidden pb-2">
        <div
          v-for="n in 2"
          :key="'home-camp-sk-' + n"
          class="w-full min-w-0 h-[238px] rounded-[18px] border border-border/60 bg-card/70 overflow-hidden flex flex-col"
        >
          <Skeleton class="h-[110px] w-full rounded-none" />
          <div class="p-3 flex flex-col gap-2">
            <Skeleton class="h-4 w-40" />
            <Skeleton class="h-3 w-full" />
            <Skeleton class="h-2 w-full rounded-full mt-2" />
          </div>
        </div>
      </div>

      <!-- Seamless Empty State (No Box) -->
      <div
        v-else-if="campaigns.length === 0"
        class="py-6 px-4 flex flex-col items-center justify-center text-center gap-2"
      >
        <div class="size-10 rounded-2xl bg-muted/50 flex items-center justify-center text-muted-foreground/70">
          <HandHeartIcon class="size-5.5" />
        </div>

        <span class="text-xs font-semibold text-muted-foreground">
          {{ languageStore.t('در حال حاضر پویش نیکوکاری فعالی وجود ندارد', 'No active donation campaigns at the moment') }}
        </span>
      </div>

      <HorizontalSliderRow
        v-else
        layout="grid"
        track-class="auto-cols-[100%] sm:auto-cols-[calc((100%-12px)/2)] gap-3"
      >
        <div
          v-for="camp in campaigns"
          :key="camp.id"
          role="button"
          tabindex="0"
          @click="emit('open-campaign', camp.id)"
          @keydown.enter="emit('open-campaign', camp.id)"
          class="w-full min-w-0 snap-start rounded-[18px] border border-border/60 bg-card/85 dark:bg-card/65 backdrop-blur-md shadow-xs hover:border-primary/40 hover:shadow-md transition-all overflow-hidden flex flex-col select-none cursor-pointer"
        >
          <!-- Cover Header with Status Pill & Category Tag -->
          <div class="h-[110px] w-full relative bg-gradient-to-br from-primary/10 via-primary/5 to-muted/60 flex items-center justify-center overflow-hidden">
            <img
              v-if="getCampaignCover(camp)"
              :src="getCampaignCover(camp)!"
              :alt="camp.title"
              class="size-full object-cover"
            />
            <HandHeartIcon v-else class="size-9 text-primary/60" />

            <div class="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-black/50 to-transparent pointer-events-none" />

            <div
              class="absolute top-2.5 start-2.5 px-2.5 py-1 rounded-xl backdrop-blur-md text-[10.5px] font-bold flex items-center gap-1.5 shadow-2xs border"
              :class="
                camp.status === 'completed' || camp.status === 'executed'
                  ? 'bg-foreground text-background border-transparent'
                  : 'bg-background/95 text-foreground border-border/60'
              "
            >
              <span
                v-if="camp.status === 'active' || !camp.status"
                class="size-1.5 rounded-full bg-primary animate-pulse shrink-0"
              />
              <CheckCircle2Icon
                v-else-if="camp.status === 'completed' || camp.status === 'executed'"
                class="size-3.5 text-background shrink-0"
              />
              <span>
                {{ getCampaignStatusLabel(camp.status) }}
              </span>
            </div>

            <div class="absolute bottom-2 end-2.5 px-2 py-0.5 rounded-lg bg-background/90 border border-border/50 text-[10px] font-semibold text-foreground">
              {{ getCampaignCategoryLabel(camp.category, languageStore.isFa) }}
            </div>
          </div>

          <!-- Campaign Details & Progress Bar -->
          <div class="p-3 flex-1 flex flex-col justify-between gap-2.5 text-start">
            <div class="flex flex-col gap-1">
              <h3 class="text-[13px] font-extrabold text-foreground truncate">
                {{ camp.title }}
              </h3>
              <p class="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed min-h-[30px]">
                {{ camp.description }}
              </p>
            </div>

            <div class="flex flex-col gap-1.5">
              <div class="flex items-center justify-between gap-2 text-[11px]">
                <span class="font-extrabold text-primary truncate">
                  {{ languageStore.n(getCampaignProgressPercent(camp)) }}٪ {{ languageStore.t('تامین شده', 'funded') }}
                </span>
                <span class="text-muted-foreground shrink-0">
                  {{ languageStore.n(camp.donors_count) }} {{ languageStore.t('حامی', 'supporters') }}
                </span>
              </div>

              <div class="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  class="h-full rounded-full bg-primary transition-all duration-300"
                  :style="{ width: `${getCampaignProgressPercent(camp)}%` }"
                />
              </div>

              <div class="flex items-center justify-between text-[10px] text-muted-foreground pt-0.5">
                <span>
                  {{ formatToman(camp.collected_amount) }} {{ languageStore.t('تومان', 'Toman') }}
                </span>
                <span>
                  {{ languageStore.t('هدف:', 'Goal:') }} {{ formatToman(camp.target_amount) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </HorizontalSliderRow>
    </section>

    <!-- Book QR Dialog -->
    <Dialog v-model:open="isQrDialogOpen">
      <DialogContent class="sm:max-w-md rounded-2xl bg-card border-border/80">
        <DialogHeader>
          <DialogTitle class="text-base font-extrabold flex items-center gap-2 text-foreground">
            <QrCodeIcon class="size-5 text-primary" />
            <span>{{ languageStore.t('شناسنامه و بارکد کتاب', 'Book QR Code') }}</span>
          </DialogTitle>
          <DialogDescription class="text-xs text-muted-foreground">
            {{ selectedQrBook?.book_title.title }} — {{ selectedQrBook?.book_title.author }}
          </DialogDescription>
        </DialogHeader>

        <div v-if="selectedQrBook" class="flex flex-col items-center gap-4 py-3">
          <div class="p-4 bg-white rounded-2xl border border-border/60 shadow-xs flex items-center justify-center">
            <img
              :src="generateQrDataUrl(getQrBookUrl(selectedQrBook), 2)"
              :alt="selectedQrBook.book_title.title"
              class="size-48 object-contain"
            />
          </div>

          <div
            v-if="getShortCode(selectedQrBook)"
            class="flex items-center gap-2 bg-muted/60 px-3 py-1.5 rounded-xl border border-border/60"
          >
            <span class="text-xs text-foreground font-mono font-bold tracking-wider">
              {{ getShortCode(selectedQrBook) }}
            </span>
            <Button
              type="button"
              variant="ghost"
              size="icon-xs"
              @click="copyShortCode(getShortCode(selectedQrBook)!)"
              :title="languageStore.t('کپی کد', 'Copy Code')"
            >
              <CopyIcon class="size-3.5" />
            </Button>
          </div>
        </div>

        <DialogFooter class="flex sm:justify-between items-center gap-2">
          <Button
            type="button"
            variant="outline"
            class="rounded-xl w-full sm:w-auto"
            @click="copyQrLink(selectedQrBook)"
          >
            <Share2Icon class="size-4" data-icon="inline-start" />
            <span>{{ languageStore.t('کپی لینک اشتراک', 'Copy Share Link') }}</span>
          </Button>
          <Button
            type="button"
            class="rounded-xl w-full sm:w-auto"
            @click="isQrDialogOpen = false"
          >
            {{ languageStore.t('بستن', 'Close') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
