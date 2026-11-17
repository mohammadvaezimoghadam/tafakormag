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
  BookPlusIcon,
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
import AddShelfBookDialog from '@/components/shelf/AddShelfBookDialog.vue'
import DonateSpecificBookDialog from '@/components/shelf/DonateSpecificBookDialog.vue'

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
const isStaff = computed(() => userStore.user?.is_staff ?? false)
const books = ref<ShelfBook[]>([])
const campaigns = ref<HomeDonationCampaign[]>([])

const isLoadingBooks = ref(false)
const isLoadingCampaigns = ref(false)

const hasAuthSession = computed(
  () => userStore.isAuthenticated || Boolean(localStorage.getItem('auth_token'))
)

const visibleBooks = computed(() => {
  const pool = isStaff.value
    ? books.value
    : books.value.filter((b) => (b as any).is_gift === true)
  return pool.filter((book) => (book.quantity ?? 1) > 0)
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

const isAddBookDialogOpen = ref(false)
const isDonateBookDialogOpen = ref(false)
const donatingBook = ref<ShelfBook | null>(null)

const toastStore = useToastStore()
const isQrDialogOpen = ref(false)
const selectedQrBook = ref<ShelfBook | null>(null)

const getQrBookUrl = (book: ShelfBook | null): string => {
  if (!book) return 'https://tafakormag.ir'
  const code = getShortCode(book)
  return code ? `https://tafakormag.ir/b/${code}` : `https://tafakormag.ir/b/${book.id}`
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

const handleOpenAddBook = () => {
  if (!hasAuthSession.value) {
    userStore.isLoginModalOpen = true
    return
  }
  isAddBookDialogOpen.value = true
}

const handleBookAdded = () => {
  loadAllHomeSections()
}

const handleDonateBookClick = (book: ShelfBook) => {
  if (!hasAuthSession.value) {
    userStore.isLoginModalOpen = true
    return
  }
  donatingBook.value = book
  isDonateBookDialogOpen.value = true
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
    <!-- 1. Asymmetric Action Hub: 3-Button for Admins / Single Hero Card for Normal Users -->
    <div class="flex items-stretch gap-2 w-full">
      <!-- Primary Hero Gateway: Topics List -->
      <button
        type="button"
        @click="emit('open-topics')"
        :class="isStaff ? 'flex-[4]' : 'flex-1 w-full'"
        class="min-w-0 h-[84px] rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 hover:border-primary/40 hover:bg-muted/40 active:scale-[0.985] transition-all duration-150 shadow-xs px-3 py-2.5 flex items-center gap-2.5 text-start cursor-pointer"
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

      <!-- Secondary Compact Card 1: Register Book (Admins Only) -->
      <button
        v-if="isStaff"
        type="button"
        @click="handleOpenAddBook"
        class="flex-[2] min-w-0 h-[84px] rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 hover:border-primary/40 hover:bg-muted/40 active:scale-[0.985] transition-all duration-150 shadow-xs px-1.5 py-2 flex flex-col items-center justify-center gap-1.5 cursor-pointer select-none"
      >
        <BookPlusIcon class="size-[22px] text-primary shrink-0" />
        <span class="text-[10.5px] font-bold text-foreground max-w-full text-center leading-tight line-clamp-2">
          {{ languageStore.t('ثبت کتاب', 'Add Book') }}
        </span>
      </button>

      <!-- Secondary Compact Card 2: Book Donations List (Admins Only) -->
      <button
        v-if="isStaff"
        type="button"
        @click="handleOpenBookDonations"
        class="flex-[2] min-w-0 h-[84px] rounded-2xl bg-card/85 dark:bg-card/65 backdrop-blur-md border border-border/70 hover:border-primary/40 hover:bg-muted/40 active:scale-[0.985] transition-all duration-150 shadow-xs px-1.5 py-2 flex flex-col items-center justify-center gap-1.5 cursor-pointer select-none"
      >
        <HandHeartIcon class="size-[22px] text-primary shrink-0" />
        <span class="text-[10.5px] font-bold text-foreground max-w-full text-center leading-tight line-clamp-2">
          {{ languageStore.t('اهدای کتاب', 'Donate Book') }}
        </span>
      </button>
    </div>

    <!-- 2. My Shelf / Gifted Books Horizontal Slider -->
    <section class="flex flex-col gap-3">
      <div class="flex items-center justify-between px-0.5">
        <h2 class="text-sm font-extrabold text-foreground">
          {{ isStaff ? languageStore.t('کتاب‌های من', 'My Books') : languageStore.t('کتاب‌های هدیه گرفته', 'Gifted Books') }}
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

      <!-- Empty State Card (Authenticated with 0 books) -->
      <div
        v-else-if="visibleBooks.length === 0"
        class="rounded-2xl border border-border/60 bg-card/85 dark:bg-card/65 backdrop-blur-md p-6 flex flex-col items-center justify-center text-center gap-3 shadow-xs"
      >
        <div class="size-14 flex items-center justify-center">
          <!-- Admin Empty State Vector (Bookshelf Stack) -->
          <svg
            v-if="isStaff"
            viewBox="0 0 100 100"
            class="size-14"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect x="22" y="56" width="56" height="14" rx="2" stroke="currentColor" stroke-width="1.6" class="text-muted-foreground/50" />
            <line x1="28" y1="56" x2="28" y2="70" stroke="currentColor" stroke-width="1.2" stroke-opacity="0.3" class="text-muted-foreground" />
            <line x1="36" y1="63" x2="68" y2="63" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 3" stroke-opacity="0.3" class="text-muted-foreground" />
            <rect x="26" y="38" width="48" height="14" rx="2" stroke="currentColor" stroke-width="1.6" class="text-muted-foreground/50" />
            <line x1="32" y1="38" x2="32" y2="52" stroke="currentColor" stroke-width="1.2" stroke-opacity="0.3" class="text-muted-foreground" />
            <line x1="40" y1="45" x2="64" y2="45" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 3" stroke-opacity="0.3" class="text-muted-foreground" />
            <path d="M 46 38 L 46 48 L 50 45 L 54 48 L 54 38" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" class="text-primary" />
          </svg>

          <!-- Normal User Empty State Vector (Gift Book with Ribbon & Heart) -->
          <svg
            v-else
            viewBox="0 0 100 100"
            class="size-14"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect x="24" y="44" width="52" height="28" rx="4" stroke="currentColor" stroke-width="1.6" class="text-muted-foreground/50" />
            <line x1="50" y1="44" x2="50" y2="72" stroke="currentColor" stroke-width="1.2" stroke-dasharray="2 3" stroke-opacity="0.4" class="text-muted-foreground" />
            <path d="M 38 44 L 38 58 L 43 54 L 48 58 L 48 44" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" class="text-primary" />
            <path d="M 50 32 C 47 26 38 26 38 34 C 38 41 50 46 50 46 C 50 46 62 41 62 34 C 62 26 53 26 50 32 Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="text-primary" />
          </svg>
        </div>

        <div class="flex flex-col gap-1 max-w-sm">
          <span class="text-xs font-bold text-foreground">
            {{
              isStaff
                ? languageStore.t('کتابی در انبار جهت نمایش یافت نشد', 'No books found in shelf')
                : languageStore.t('هنوز کتابی به شما اهدا نشده است', 'No books gifted to you yet')
            }}
          </span>
          <span class="text-[11px] text-muted-foreground leading-relaxed">
            {{
              isStaff
                ? languageStore.t('می‌توانید با دکمه ثبت کتاب، اثر جدیدی به انبار تفکر بیفزایید.', 'You can add books to Tafakor shelf.')
                : languageStore.t('کتاب‌های اهدایی که از طریق تفکر دریافت می‌کنید در این بخش قرار می‌گیرند.', 'Gifted books received through Tafakor will appear here.')
            }}
          </span>
        </div>

        <Button
          v-if="isStaff"
          type="button"
          size="sm"
          class="rounded-xl font-bold bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-3.5 text-xs gap-1.5"
          @click="handleOpenAddBook"
        >
          <BookPlusIcon class="size-3.5" />
          <span>{{ languageStore.t('ثبت کتاب جدید', 'Add Book') }}</span>
        </Button>
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

            <div class="absolute top-1.5 start-1.5 px-1.5 py-0.5 rounded-md bg-background/95 border border-border/60 text-[10px] font-bold text-foreground shadow-2xs">
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
              <!-- Admin: Dedicated Donate Button -->
              <Button
                v-if="isStaff && !book.is_gift"
                type="button"
                size="xs"
                class="w-full h-7 rounded-xl text-[10.5px] font-bold gap-1 justify-center bg-black text-white hover:bg-neutral-800 dark:bg-secondary dark:text-secondary-foreground dark:hover:bg-secondary/80 transition-colors shadow-2xs"
                @click.stop="handleDonateBookClick(book)"
              >
                <HandHeartIcon class="size-3.5" />
                <span>{{ languageStore.t('اهدا', 'Donate') }}</span>
              </Button>

              <!-- Recipient / Gift: Show Emerald Gift Badge -->
              <div
                v-else
                class="w-full py-1 text-center text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 rounded-xl truncate flex items-center justify-center gap-1 shadow-2xs"
              >
                <SparklesIcon class="size-3 text-emerald-600 shrink-0" />
                <span class="truncate">هدیه از طرف {{ book.gifted_by_name || 'ادمین تفکر' }}</span>
              </div>
            </div>
          </div>
        </div>
      </HorizontalSliderRow>
    </section>

    <!-- 3. Donation Campaigns Horizontal Slider (پویش‌های نیکوکاری و اهدا) -->
    <section v-if="isLoadingCampaigns || campaigns.length > 0" class="flex flex-col gap-3">
      <div class="flex items-center justify-between px-0.5">
        <div class="flex items-center gap-2">
          <h2 class="text-sm font-extrabold text-foreground">
            {{ languageStore.t('پویش‌های نیکوکاری و اهدا', 'Donation Campaigns') }}
          </h2>
          <span class="size-2 rounded-full bg-primary shrink-0" />
        </div>

        <button
          type="button"
          @click="emit('open-donations')"
          class="flex items-center gap-0.5 text-xs font-bold text-primary hover:opacity-80 active:scale-95 transition-all select-none cursor-pointer"
        >
          <span>{{ languageStore.t('همه', 'All') }}</span>
          <ChevronLeftIcon v-if="languageStore.isFa" class="size-3.5" />
          <ChevronRightIcon v-else class="size-3.5" />
        </button>
      </div>

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
                  ? 'bg-emerald-600 text-white border-transparent'
                  : 'bg-background/95 text-emerald-700 dark:text-emerald-400 border-emerald-500/30'
              "
            >
              <span
                v-if="camp.status === 'active' || !camp.status"
                class="size-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0"
              />
              <CheckCircle2Icon
                v-else-if="camp.status === 'completed' || camp.status === 'executed'"
                class="size-3.5 text-white shrink-0"
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

    <!-- Add Book to Shelf Dialog -->
    <AddShelfBookDialog
      v-model:open="isAddBookDialogOpen"
      @saved="handleBookAdded"
    />

    <!-- Donate Specific Book Dialog -->
    <DonateSpecificBookDialog
      v-model:open="isDonateBookDialogOpen"
      :book="donatingBook"
      @donated="handleBookAdded"
    />

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
