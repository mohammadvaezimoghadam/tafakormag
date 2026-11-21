<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import {
  confirmGift,
  extractApiErrorMessage,
  getMyShelfSummary,
  listIncomingGifts,
  listMyShelfBooks,
  rejectGift,
} from '@/api/shelf'
import type {
  IncomingGiftItem,
  ShelfBook,
  ShelfSummary,
} from '@/types/shelf'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  BookCheckIcon,
  BookOpenIcon,
  CheckIcon,
  EyeIcon,
  GiftIcon,
  Loader2Icon,
  SearchIcon,
  SmartphoneIcon,
  SparklesIcon,
} from '@lucide/vue'

const emit = defineEmits<{
  (e: 'shelf-changed'): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()
const userStore = useUserStore()

const books = ref<ShelfBook[]>([])
const incomingGifts = ref<IncomingGiftItem[]>([])
const isActioningGift = ref<number | null>(null)

const summary = ref<ShelfSummary>({
  total: 0,
  total_copies: 0,
})

const isLoading = ref(true)
const searchQuery = ref('')

// View-Only Book Detail Modal
const isViewDetailOpen = ref(false)
const viewingBook = ref<ShelfBook | null>(null)

const filteredBooks = computed(() => {
  return books.value
})

let searchDebounce: ReturnType<typeof setTimeout> | null = null
const hasActiveFilter = computed(() => Boolean(searchQuery.value.trim()))

const loadShelfData = async () => {
  isLoading.value = true
  try {
    const [listData, summaryData, giftsData] = await Promise.all([
      listMyShelfBooks({
        search: searchQuery.value,
      }),
      getMyShelfSummary().catch(() => ({
        total: 0,
        total_copies: 0,
      })),
      listIncomingGifts().catch(() => []),
    ])
    books.value = listData
    summary.value = summaryData
    incomingGifts.value = giftsData
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در دریافت قفسه کتاب', 'Failed to load shelf')),
      'error'
    )
  } finally {
    isLoading.value = false
  }
}

const refreshSummaryOnly = async () => {
  try {
    summary.value = await getMyShelfSummary()
  } catch {
    // non-fatal background refresh
  }
}

const handleConfirmGift = async (transferId: number) => {
  isActioningGift.value = transferId
  try {
    const res = await confirmGift(transferId)
    toastStore.triggerToast(
      res.message || languageStore.t('کتاب با موفقیت به قفسه شما اضافه شد', 'Book added to your shelf'),
      'success'
    )
    await loadShelfData()
    emit('shelf-changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در دریافت کتاب', 'Failed to accept gift')),
      'error'
    )
  } finally {
    isActioningGift.value = null
  }
}

const handleRejectGift = async (transferId: number) => {
  isActioningGift.value = transferId
  try {
    const res = await rejectGift(transferId)
    toastStore.triggerToast(
      res.message || languageStore.t('هدیه با موفقیت رد شد', 'Gift rejected'),
      'info'
    )
    incomingGifts.value = incomingGifts.value.filter((g) => g.transfer_id !== transferId)
    await refreshSummaryOnly()
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در رد هدیه', 'Failed to reject gift')),
      'error'
    )
  } finally {
    isActioningGift.value = null
  }
}

onMounted(() => {
  loadShelfData()
})

const handleSearchInput = () => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    loadShelfData()
  }, 300)
}

const clearFilters = () => {
  searchQuery.value = ''
  loadShelfData()
}

const openViewDetailDialog = (book: ShelfBook) => {
  viewingBook.value = book
  isViewDetailOpen.value = true
}

const resolveMediaUrl = (raw?: string | null): string | null => {
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw
  }
  return `/${raw}`
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Header / Summary Card -->
    <Card class="rounded-3xl border-border/60 shadow-sm py-4">
      <CardContent class="px-4 flex flex-col gap-3">
        <div class="flex items-center justify-between gap-3 flex-wrap">
          <div class="flex items-center gap-2.5">
            <div class="size-10 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <BookOpenIcon class="size-5 text-primary" />
            </div>
            <div class="flex flex-col">
              <h2 class="text-base font-extrabold text-foreground">
                {{ languageStore.t('قفسه کتاب من', 'My Bookshelf') }}
              </h2>
              <p class="text-xs text-muted-foreground">
                {{ languageStore.t('مشاهده کتاب‌ها و هدایای دریافتی', 'View books and received gifts') }}
              </p>
            </div>
          </div>
        </div>

        <!-- Clean Summary Banner -->
        <div class="rounded-2xl bg-muted/40 border border-border/40 px-3.5 py-2.5 flex items-center justify-between text-xs">
          <span class="text-muted-foreground font-medium">
            {{ languageStore.t('موجودی کل کتاب‌های قفسه:', 'Total Shelf Books:') }}
          </span>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-foreground text-sm">
              {{ languageStore.n(books.reduce((acc, b) => acc + (b.quantity || 1), 0)) }} {{ languageStore.t('جلد', 'copies') }}
            </span>
            <span class="text-muted-foreground text-[11px]">
              ({{ languageStore.n(books.length) }} {{ languageStore.t('عنوان', 'titles') }})
            </span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Incoming Gifts Banner (Pending receipt) -->
    <Card
      v-if="incomingGifts.length > 0"
      class="rounded-3xl border-border/60 bg-muted/30 overflow-hidden shadow-xs"
    >
      <CardContent class="p-4 flex flex-col gap-3">
        <div class="flex items-center gap-2.5">
          <div class="size-9 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center shrink-0 shadow-2xs">
            <GiftIcon class="size-4.5" />
          </div>
          <div class="flex flex-col">
            <h3 class="text-sm font-extrabold text-foreground flex items-center gap-1.5">
              <span>{{ languageStore.t('هدایای در انتظار دریافت', 'Pending Book Gifts') }}</span>
              <Badge class="bg-primary text-primary-foreground text-[10px] px-1.5 py-0 h-4 rounded-full">
                {{ languageStore.n(incomingGifts.length) }}
              </Badge>
            </h3>
            <span class="text-[11px] text-muted-foreground">
              {{
                languageStore.t(
                  'کتاب‌هایی که به شماره همراه شما اهدا شده‌اند. برای مشاهده در قفسه تحویل را تأیید کنید.',
                  'Books gifted to your phone number. Confirm to add to your shelf.'
                )
              }}
            </span>
          </div>
        </div>

        <div class="flex flex-col gap-2.5">
          <div
            v-for="gift in incomingGifts"
            :key="gift.transfer_id"
            class="rounded-2xl border border-border/60 bg-card p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-11 h-15 rounded-xl bg-muted/60 border border-border/40 overflow-hidden shrink-0 flex items-center justify-center">
                <img
                  v-if="resolveMediaUrl(gift.cover_image)"
                  :src="resolveMediaUrl(gift.cover_image)!"
                  :alt="gift.book_title"
                  class="size-full object-cover"
                />
                <BookOpenIcon v-else class="size-5 text-muted-foreground/60" />
              </div>

              <div class="flex flex-col gap-0.5 min-w-0">
                <span class="text-xs font-bold text-foreground truncate">
                  {{ gift.book_title }}
                </span>
                <span v-if="gift.book_author" class="text-[10.5px] text-muted-foreground truncate">
                  {{ gift.book_author }}
                </span>
                <div class="flex items-center gap-2 mt-1 flex-wrap">
                  <Badge variant="outline" class="text-[10px] py-0 border-border/70">
                    {{ languageStore.t('اهدا از:', 'From:') }}
                    <span class="font-bold ms-1 text-foreground">{{ gift.from_user_name }}</span>
                  </Badge>
                  <Badge variant="secondary" class="text-[10px] py-0 font-mono tracking-wider">
                    {{ gift.short_code }}
                  </Badge>
                  <span v-if="gift.quantity > 1" class="text-[10px] font-bold text-muted-foreground">
                    ({{ languageStore.n(gift.quantity) }} {{ languageStore.t('جلد', 'copies') }})
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 self-end sm:self-center shrink-0">
              <Button
                type="button"
                size="xs"
                class="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 font-bold text-[11px] h-8 gap-1.5 shadow-2xs"
                :disabled="isActioningGift === gift.transfer_id"
                @click="handleConfirmGift(gift.transfer_id)"
              >
                <Loader2Icon v-if="isActioningGift === gift.transfer_id" class="size-3 animate-spin" />
                <CheckIcon v-else class="size-3.5" />
                <span>{{ languageStore.t('تحویل گرفتم', 'Accept Gift') }}</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="xs"
                class="rounded-xl text-[11px] h-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                :disabled="isActioningGift === gift.transfer_id"
                @click="handleRejectGift(gift.transfer_id)"
              >
                <span>{{ languageStore.t('رد هدیه', 'Reject') }}</span>
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Search Input -->
    <div class="relative">
      <SearchIcon class="size-4 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3.5 pointer-events-none" />
      <Input
        v-model="searchQuery"
        class="ps-10 h-10 bg-card border-border/60 rounded-2xl"
        :placeholder="languageStore.t('جستجو در قفسه کتاب من...', 'Search my bookshelf...')"
        @input="handleSearchInput"
      />
    </div>

    <!-- Loading State: 3-Column Skeletons -->
    <div v-if="isLoading" class="grid grid-cols-3 gap-2.5 sm:gap-3.5">
      <div
        v-for="n in 6"
        :key="n"
        class="rounded-2xl border border-border/60 bg-card/50 p-2.5 flex flex-col gap-2"
      >
        <Skeleton class="h-[112px] w-full rounded-xl" />
        <div class="flex flex-col gap-1.5">
          <Skeleton class="h-3.5 w-full rounded-md" />
          <Skeleton class="h-2.5 w-2/3 rounded-md" />
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredBooks.length === 0" class="py-10 px-6 flex flex-col items-center text-center gap-3">
      <div class="size-14 flex items-center justify-center">
        <!-- Search Empty State -->
        <div v-if="hasActiveFilter" class="size-12 rounded-2xl bg-muted flex items-center justify-center text-muted-foreground">
          <BookOpenIcon class="size-6" />
        </div>

        <!-- Bookshelf Stack Vector -->
        <svg
          v-else
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
      </div>
      <div class="flex flex-col gap-1 max-w-sm">
        <span class="text-sm font-bold text-foreground">
          {{
            hasActiveFilter
              ? languageStore.t('کتابی با این عبارت پیدا نشد', 'No matching books found')
              : languageStore.t('هنوز کتابی در قفسه شما ثبت نشده است', 'No books in your bookshelf yet')
          }}
        </span>
        <span class="text-xs text-muted-foreground leading-relaxed">
          {{
            hasActiveFilter
              ? languageStore.t('عبارت جستجو را تغییر دهید یا پاک کنید.', 'Try changing or clearing your search.')
              : languageStore.t('کتاب‌های اهدا شده به شما پس از تأیید در این بخش نمایش داده می‌شوند.', 'Books gifted to you will appear here.')
          }}
        </span>
      </div>
      <div v-if="hasActiveFilter" class="flex items-center gap-2">
        <Button type="button" variant="outline" size="sm" class="rounded-xl" @click="clearFilters">
          {{ languageStore.t('پاک کردن جستجو', 'Reset Search') }}
        </Button>
      </div>
    </div>

    <!-- Books Grid: 3 columns -->
    <div v-else class="grid grid-cols-3 gap-2.5 sm:gap-3.5">
      <div
        v-for="book in filteredBooks"
        :key="book.id"
        role="button"
        tabindex="0"
        @click="openViewDetailDialog(book)"
        @keydown.enter.prevent="openViewDetailDialog(book)"
        class="w-full min-w-0 h-auto rounded-2xl border border-border/60 bg-card/85 dark:bg-card/65 backdrop-blur-md shadow-xs transition-all overflow-hidden flex flex-col select-none cursor-pointer hover:border-primary/40 hover:shadow-sm group"
      >
        <!-- Cover Container -->
        <div class="h-[112px] w-full bg-muted/50 dark:bg-muted/30 relative flex items-center justify-center overflow-hidden">
          <img
            v-if="resolveMediaUrl(book.book_title.cover_image)"
            :src="resolveMediaUrl(book.book_title.cover_image)!"
            :alt="book.book_title.title"
            class="size-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <SmartphoneIcon
            v-else-if="book.book_format === 'digital'"
            class="size-7 text-muted-foreground/70"
          />
          <BookOpenIcon v-else class="size-7 text-muted-foreground/70" />

          <!-- Top-Start Badge: Gift Only -->
          <div
            v-if="book.is_gift"
            class="absolute top-1.5 start-1.5 px-1.5 py-0.5 rounded-md bg-foreground text-background text-[9.5px] font-bold shadow-2xs flex items-center gap-1 backdrop-blur-xs"
          >
            <SparklesIcon class="size-2.5" />
            <span>{{ languageStore.t('هدیه', 'Gift') }}</span>
          </div>

          <!-- Quantity Badge (if multiple copies) -->
          <div
            v-if="(book.quantity ?? 1) > 1"
            class="absolute top-1.5 end-1.5 px-1.5 py-0.5 rounded-md bg-background/95 border border-border/60 text-[9.5px] font-bold text-foreground shadow-2xs"
          >
            <span>{{ languageStore.n(book.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}</span>
          </div>
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

          <div class="flex flex-col gap-1.5 pt-1.5 border-t border-border/40">
            <!-- Gift Origin Label -->
            <div
              v-if="book.is_gift"
              class="w-full py-1.5 px-2 text-center text-[10px] font-bold text-foreground bg-muted/80 border border-border/70 rounded-xl truncate flex items-center justify-center gap-1 shadow-2xs"
            >
              <SparklesIcon class="size-3 text-muted-foreground shrink-0" />
              <span class="truncate">هدیه از طرف {{ book.gifted_by_name || 'ادمین تفکر' }}</span>
            </div>

            <!-- Action Row -->
            <div class="flex items-center justify-center pt-0.5">
              <button
                type="button"
                class="w-full flex items-center justify-center gap-1.5 text-[10.5px] font-bold text-muted-foreground hover:text-foreground py-1 rounded-md hover:bg-muted/50 transition-colors cursor-pointer"
                :title="languageStore.t('مشخصات کتاب', 'Book Details')"
                @click.stop="openViewDetailDialog(book)"
              >
                <EyeIcon class="size-3.5" />
                <span>{{ languageStore.t('مشخصات کتاب', 'Book Details') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Client View-Only Details Dialog -->
    <Dialog v-model:open="isViewDetailOpen">
      <DialogContent class="sm:max-w-md rounded-3xl p-5">
        <DialogHeader class="gap-1 text-start">
          <DialogTitle class="text-base font-extrabold text-foreground flex items-center gap-2">
            <BookOpenIcon class="size-5 text-foreground shrink-0" />
            <span>{{ languageStore.t('مشخصات کتاب', 'Book Details') }}</span>
          </DialogTitle>
          <DialogDescription class="text-xs text-muted-foreground">
            {{ viewingBook?.book_title.title }}
          </DialogDescription>
        </DialogHeader>

        <div v-if="viewingBook" class="flex flex-col gap-4 py-2">
          <!-- Book Header Card -->
          <div class="flex items-center gap-3 bg-muted/30 p-3 rounded-2xl border border-border/50">
            <div class="w-14 h-20 rounded-xl overflow-hidden bg-muted/60 border border-border/40 shrink-0 flex items-center justify-center">
              <img
                v-if="resolveMediaUrl(viewingBook.book_title.cover_image)"
                :src="resolveMediaUrl(viewingBook.book_title.cover_image)!"
                :alt="viewingBook.book_title.title"
                class="size-full object-cover"
              />
              <BookOpenIcon v-else class="size-6 text-muted-foreground/60" />
            </div>

            <div class="flex flex-col gap-1 min-w-0 flex-1">
              <h3 class="text-sm font-black text-foreground line-clamp-2">
                {{ viewingBook.book_title.title }}
              </h3>
              <p class="text-xs text-muted-foreground">
                {{ viewingBook.book_title.author }}
              </p>
              <div class="flex items-center gap-1.5 mt-1 flex-wrap">
                <Badge
                  v-if="viewingBook.is_gift"
                  class="bg-secondary text-secondary-foreground border border-border text-[10px] px-2 py-0.5 rounded-full font-bold"
                >
                  هدیه از طرف {{ viewingBook.gifted_by_name || 'ادمین تفکر' }}
                </Badge>
              </div>
            </div>
          </div>

          <!-- Info Details -->
          <div class="flex flex-col gap-2 text-xs">
            <div class="flex items-center justify-between p-2 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground">{{ languageStore.t('تعداد جلد:', 'Volumes / Copies:') }}</span>
              <span class="font-extrabold text-foreground">
                {{ languageStore.n(viewingBook.quantity || 1) }} {{ languageStore.t('جلد', 'copies') }}
              </span>
            </div>
            <div v-if="viewingBook.book_title.publisher" class="flex items-center justify-between p-2 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground">{{ languageStore.t('ناشر:', 'Publisher:') }}</span>
              <span class="font-bold text-foreground">{{ viewingBook.book_title.publisher }}</span>
            </div>
            <div v-if="viewingBook.book_title.category" class="flex items-center justify-between p-2 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground">{{ languageStore.t('دسته‌بندی:', 'Category:') }}</span>
              <span class="font-bold text-foreground">{{ viewingBook.book_title.category }}</span>
            </div>
            <div v-if="viewingBook.personal_note" class="flex flex-col gap-1 p-2.5 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground font-semibold">{{ languageStore.t('یادداشت شخصی شما:', 'Personal Note:') }}</span>
              <p class="text-foreground leading-relaxed text-[11.5px]">{{ viewingBook.personal_note }}</p>
            </div>
            <div v-if="viewingBook.book_title.description" class="flex flex-col gap-1 p-2.5 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground font-semibold">{{ languageStore.t('توضیحات کتاب:', 'Description:') }}</span>
              <p class="text-muted-foreground leading-relaxed text-[11.5px]">{{ viewingBook.book_title.description }}</p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" class="w-full rounded-2xl bg-primary text-primary-foreground hover:bg-primary/90 font-bold" @click="isViewDetailOpen = false">
            {{ languageStore.t('بستن', 'Close') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
