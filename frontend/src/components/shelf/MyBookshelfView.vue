<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import {
  confirmGift,
  deleteShelfBook,
  extractApiErrorMessage,
  getMyShelfSummary,
  listAdminDonationsReport,
  listIncomingGifts,
  listMyShelfBooks,
  rejectGift,
  updateShelfBook,
} from '@/api/shelf'
import type {
  AdminDonationReportItem,
  IncomingGiftItem,
  ShelfBook,
  ShelfSummary,
} from '@/types/shelf'
import AddShelfBookDialog from './AddShelfBookDialog.vue'
import BookDonationDetailDialog from './BookDonationDetailDialog.vue'
import DonateSpecificBookDialog from './DonateSpecificBookDialog.vue'
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  BookOpenIcon,
  CheckIcon,
  ClockIcon,
  EyeIcon,
  FileTextIcon,
  GiftIcon,
  HandHeartIcon,
  LayersIcon,
  Loader2Icon,
  PencilIcon,
  PlusIcon,
  QrCodeIcon,
  SearchIcon,
  SmartphoneIcon,
  SparklesIcon,
  Trash2Icon,
  UserCheckIcon,
  UserIcon,
} from '@lucide/vue'

const emit = defineEmits<{
  (e: 'shelf-changed'): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()
const userStore = useUserStore()

const isStaff = computed(() => userStore.isStaff)

const books = ref<ShelfBook[]>([])
const incomingGifts = ref<IncomingGiftItem[]>([])
const isActioningGift = ref<number | null>(null)

// Admin Reports State
const adminReports = ref<AdminDonationReportItem[]>([])
const isLoadingReports = ref(false)

const summary = ref<ShelfSummary>({
  total: 0,
  reading_count: 0,
  finished_count: 0,
  want_to_read_count: 0,
  keeping_count: 0,
  offering_count: 0,
})

const isLoading = ref(true)
const searchQuery = ref('')
const isAddEditDialogOpen = ref(false)
const editingBook = ref<ShelfBook | null>(null)
const isDeleteDialogOpen = ref(false)
const deletingBook = ref<ShelfBook | null>(null)
const isDeleting = ref(false)
const isDonateDialogOpen = ref(false)
const donatingBook = ref<ShelfBook | null>(null)
const isClaimDialogOpen = ref(false)

// View-Only Book Detail Modal for recipients
const isViewDetailOpen = ref(false)
const viewingBook = ref<ShelfBook | null>(null)

// Quick Stock Adjust Dialog for Admin
const isStockDialogOpen = ref(false)
const stockBook = ref<ShelfBook | null>(null)
const stockAdjustment = ref(1)
const isUpdatingStock = ref(false)

// Tabs: Admin has 'inventory' | 'reports', Normal user has 'all'
const adminActiveTab = ref<'inventory' | 'reports'>('inventory')
const recipientActiveTab = ref<'all' | 'gifts'>('all')

const receivedCount = computed(() => books.value.filter((b) => b.is_gift === true).length)
const donatedCount = computed(() => books.value.filter((b) => !b.is_gift).length)

const filteredBooks = computed(() => {
  if (!isStaff.value) {
    // Normal user: show received/gifted books only
    return books.value.filter((b) => b.is_gift === true)
  }
  // Admin inventory
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
        reading_count: 0,
        finished_count: 0,
        want_to_read_count: 0,
        keeping_count: 0,
        offering_count: 0,
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

const loadAdminReports = async () => {
  if (!isStaff.value) return
  isLoadingReports.value = true
  try {
    adminReports.value = await listAdminDonationsReport()
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, 'خطا در دریافت گزارش اهدا شده‌ها'),
      'error'
    )
  } finally {
    isLoadingReports.value = false
  }
}

watch(
  () => adminActiveTab.value,
  (tab) => {
    if (tab === 'reports' && isStaff.value) {
      loadAdminReports()
    }
  }
)

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

const openAddDialog = () => {
  editingBook.value = null
  isAddEditDialogOpen.value = true
}

const openEditDialog = (book: ShelfBook) => {
  editingBook.value = book
  isAddEditDialogOpen.value = true
}

const openViewDetailDialog = (book: ShelfBook) => {
  viewingBook.value = book
  isViewDetailOpen.value = true
}

const openStockDialog = (book: ShelfBook) => {
  stockBook.value = book
  stockAdjustment.value = 1
  isStockDialogOpen.value = true
}

const handleStockIncrease = async () => {
  if (!stockBook.value) return
  isUpdatingStock.value = true
  try {
    const newQty = (stockBook.value.quantity || 1) + stockAdjustment.value
    await updateShelfBook(stockBook.value.id, {
      quantity: newQty,
    })
    toastStore.triggerToast('موجودی کتاب با موفقیت افزایش یافت', 'success')
    isStockDialogOpen.value = false
    await loadShelfData()
    emit('shelf-changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, 'خطا در افزایش موجودی کتاب'),
      'error'
    )
  } finally {
    isUpdatingStock.value = false
  }
}

const handleDonateClick = (book: ShelfBook) => {
  donatingBook.value = book
  isDonateDialogOpen.value = true
}

const handleBookSaved = async () => {
  await loadShelfData()
  if (isStaff.value && adminActiveTab.value === 'reports') {
    await loadAdminReports()
  }
  emit('shelf-changed')
}

const confirmDeleteBook = (book: ShelfBook) => {
  deletingBook.value = book
  isDeleteDialogOpen.value = true
}

const executeDeleteBook = async () => {
  if (!deletingBook.value) return
  isDeleting.value = true
  try {
    await deleteShelfBook(deletingBook.value.id)
    books.value = books.value.filter((b) => b.id !== deletingBook.value?.id)
    await refreshSummaryOnly()
    emit('shelf-changed')
    toastStore.triggerToast(
      languageStore.t('کتاب از انبار حذف شد', 'Book removed from shelf'),
      'success'
    )
    isDeleteDialogOpen.value = false
    deletingBook.value = null
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('حذف کتاب انجام نشد', 'Failed to delete book')),
      'error'
    )
  } finally {
    isDeleting.value = false
  }
}

const resolveMediaUrl = (raw?: string | null): string | null => {
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw
  }
  return `/${raw}`
}

const formatDateTime = (raw: string): string => {
  try {
    const d = new Date(raw)
    return new Intl.DateTimeFormat('fa-IR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d)
  } catch {
    return raw
  }
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
              <BookOpenIcon v-if="!isStaff" class="size-5 text-emerald-600" />
              <LayersIcon v-else class="size-5" />
            </div>
            <div class="flex flex-col">
              <h2 class="text-base font-extrabold text-foreground">
                {{ isStaff ? languageStore.t('انبار و اهدای کتاب تفکر', 'Tafakor Book Inventory & Donation') : languageStore.t('اهدا شده به من', 'Gifted to Me') }}
              </h2>
              <p class="text-xs text-muted-foreground">
                {{
                  isStaff
                    ? languageStore.t('مدیریت موجودی کتاب‌های انبار تفکر و ثبت اهدای حضوری', 'Manage inventory and donate')
                    : languageStore.t('فهرست کتاب‌هایی که از طرف تفکر به شما اهدا شده است', 'Books gifted to you by Tafakor')
                }}
              </p>
            </div>
          </div>

          <!-- Header Action Buttons -->
          <div class="flex items-center gap-2 flex-wrap">
            <!-- QR Claim Button (Available for all) -->
            <Button
              v-if="isStaff"
              type="button"
              variant="outline"
              class="rounded-2xl shrink-0 gap-1.5"
              @click="isClaimDialogOpen = true"
            >
              <QrCodeIcon class="size-4 text-primary" />
              <span>{{ languageStore.t('تحویل یا دریافت با بارکد (QR)', 'Handover / Claim by QR') }}</span>
            </Button>

            <!-- Add Book Button (Only for Admin) -->
            <Button
              v-if="isStaff"
              type="button"
              class="rounded-2xl shrink-0 bg-black text-white hover:bg-neutral-800 dark:bg-emerald-600 dark:hover:bg-emerald-700 dark:text-white font-bold"
              @click="openAddDialog"
            >
              <PlusIcon data-icon="inline-start" />
              <span>{{ languageStore.t('ثبت کتاب جدید', 'Add Book') }}</span>
            </Button>
          </div>
        </div>

        <!-- Clean Summary Banner -->
        <div class="rounded-2xl bg-muted/40 border border-border/40 px-3.5 py-2.5 flex items-center justify-between text-xs">
          <span class="text-muted-foreground font-medium">
            {{ isStaff ? languageStore.t('موجودی کل کتاب‌های انبار:', 'Total Inventory:') : languageStore.t('تعداد کل کتاب‌های اهدایی:', 'Total Gifted Books:') }}
          </span>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-foreground text-sm">
              {{ languageStore.n(isStaff ? (summary.total_copies ?? summary.total) : filteredBooks.length) }} {{ languageStore.t('جلد', 'copies') }}
            </span>
            <span v-if="isStaff" class="text-muted-foreground text-[11px]">
              ({{ languageStore.n(summary.total) }} {{ languageStore.t('عنوان', 'titles') }})
            </span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Incoming Gifts Banner (Pending receipt) -->
    <Card
      v-if="incomingGifts.length > 0"
      class="rounded-3xl border-emerald-500/40 bg-emerald-500/5 dark:bg-emerald-500/10 overflow-hidden shadow-xs"
    >
      <CardContent class="p-4 flex flex-col gap-3">
        <div class="flex items-center gap-2.5">
          <div class="size-9 rounded-2xl bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-2xs">
            <GiftIcon class="size-4.5" />
          </div>
          <div class="flex flex-col">
            <h3 class="text-sm font-extrabold text-foreground flex items-center gap-1.5">
              <span>{{ languageStore.t('هدایای در انتظار دریافت', 'Pending Book Gifts') }}</span>
              <Badge class="bg-emerald-600 text-white text-[10px] px-1.5 py-0 h-4 rounded-full">
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
                class="rounded-xl bg-black text-white hover:bg-neutral-800 dark:bg-emerald-600 dark:hover:bg-emerald-700 dark:text-white font-bold text-[11px] h-8 gap-1.5 shadow-2xs"
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

    <!-- Admin 2 Tabs: Inventory vs Reports -->
    <div
      v-if="isStaff"
      class="flex items-center gap-1.5 p-1 bg-muted/60 dark:bg-muted/40 rounded-2xl border border-border/50 self-start text-xs flex-wrap"
    >
      <button
        type="button"
        class="px-3.5 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1.5 cursor-pointer"
        :class="adminActiveTab === 'inventory' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
        @click="adminActiveTab = 'inventory'"
      >
        <LayersIcon class="size-3.5" />
        <span>{{ languageStore.t('کتاب‌های موجود تفکر', 'Current Inventory') }}</span>
        <Badge variant="secondary" class="text-[10px] px-1.5 py-0 h-4 rounded-full">
          {{ languageStore.n(books.length) }}
        </Badge>
      </button>

      <button
        type="button"
        class="px-3.5 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1.5 cursor-pointer"
        :class="adminActiveTab === 'reports' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground'"
        @click="adminActiveTab = 'reports'"
      >
        <FileTextIcon class="size-3.5 text-primary" />
        <span>{{ languageStore.t('گزارش اهدا شده‌ها', 'Donations Report') }}</span>
        <Badge v-if="adminReports.length > 0" class="bg-primary text-primary-foreground text-[10px] px-1.5 py-0 h-4 rounded-full">
          {{ languageStore.n(adminReports.length) }}
        </Badge>
      </button>
    </div>

    <!-- ── TAB 1: INVENTORY (Admin) OR GIFTS (Normal User) ── -->
    <template v-if="!isStaff || adminActiveTab === 'inventory'">
      <!-- Search input -->
      <div class="relative">
        <SearchIcon class="size-4 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3.5 pointer-events-none" />
        <Input
          v-model="searchQuery"
          class="ps-10 h-10 bg-card border-border/60 rounded-2xl"
          :placeholder="isStaff ? languageStore.t('جستجو در کتاب‌های انبار تفکر...', 'Search inventory...') : languageStore.t('جستجو در کتاب‌های اهدا شده به من...', 'Search gifted books...')"
          @input="handleSearchInput"
        />
      </div>

      <!-- Loading state: 3-column grid -->
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

      <!-- Empty state (Seamless / No Box) -->
      <div v-else-if="filteredBooks.length === 0" class="py-10 px-6 flex flex-col items-center text-center gap-3">
        <div class="size-14 flex items-center justify-center">
          <!-- Search Empty State -->
          <div v-if="hasActiveFilter" class="size-12 rounded-2xl bg-muted flex items-center justify-center text-muted-foreground">
            <BookOpenIcon class="size-6" />
          </div>

          <!-- Admin Empty State Vector (Bookshelf Stack) -->
          <svg
            v-else-if="isStaff"
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
            <path d="M 50 32 C 47 26 38 26 38 34 C 38 41 50 46 50 46 C 50 46 62 40 62 32 C 62 24 53 24 50 32 Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="text-primary" />
          </svg>
        </div>
        <div class="flex flex-col gap-1 max-w-sm">
          <span class="text-sm font-bold text-foreground">
            {{
              hasActiveFilter
                ? languageStore.t('کتابی با این عبارت پیدا نشد', 'No matching books found')
                : isStaff
                ? languageStore.t('هنوز کتابی در انبار تفکر ثبت نشده است', 'No books registered in inventory yet')
                : languageStore.t('هنوز کتابی به شما اهدا نشده است', 'No books gifted to you yet')
            }}
          </span>
          <span class="text-xs text-muted-foreground leading-relaxed">
            {{
              hasActiveFilter
                ? languageStore.t('عبارت جستجو را تغییر دهید یا پاک کنید.', 'Try changing or clearing your search.')
                : isStaff
                ? languageStore.t('با دکمه «ثبت کتاب جدید»، عناوین موجود در انبار تفکر را اضافه فرمایید.', 'Click "Add Book" to add inventory copies.')
                : languageStore.t('کتاب‌هایی که از طرف تفکر به شما اهدا شود، پس از تحویل در اینجا نمایش داده خواهند شد.', 'Books gifted to you will appear here.')
            }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <Button v-if="hasActiveFilter" type="button" variant="outline" size="sm" class="rounded-xl" @click="clearFilters">
            {{ languageStore.t('پاک کردن جستجو', 'Reset Search') }}
          </Button>
          <Button v-else-if="isStaff" type="button" size="sm" class="rounded-xl" @click="openAddDialog">
            <PlusIcon data-icon="inline-start" />
            <span>{{ languageStore.t('ثبت اولین کتاب', 'Add First Book') }}</span>
          </Button>
        </div>
      </div>

      <!-- Shelf Books Grid: 3 columns -->
      <div v-else class="grid grid-cols-3 gap-2.5 sm:gap-3.5">
        <div
          v-for="book in filteredBooks"
          :key="book.id"
          role="button"
          tabindex="0"
          @click="isStaff ? openEditDialog(book) : openViewDetailDialog(book)"
          @keydown.enter.prevent="isStaff ? openEditDialog(book) : openViewDetailDialog(book)"
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

            <!-- Stock / Quantity Badge (Admin Mode) -->
            <div
              v-if="isStaff"
              class="absolute top-1.5 start-1.5 px-1.5 py-0.5 rounded-md bg-background/95 border text-[10px] font-bold shadow-2xs"
              :class="(book.quantity ?? 1) <= 0 ? 'text-amber-600 dark:text-amber-400 border-amber-500/40' : 'text-foreground border-border/60'"
            >
              <span>{{ languageStore.n(book.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}</span>
            </div>

            <!-- Gift Badge (Recipient Mode) -->
            <div
              v-if="!isStaff || book.is_gift"
              class="absolute bottom-1.5 start-1.5 px-1.5 py-0.5 rounded-md bg-emerald-600/90 text-white text-[9.5px] font-bold shadow-2xs flex items-center gap-1 backdrop-blur-xs"
            >
              <SparklesIcon class="size-2.5" />
              <span>{{ languageStore.t('هدیه', 'Gift') }}</span>
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
              <!-- ── RECIPIENT MODE: Emerald Gift Badge Only (No Edit, Delete, Donate) ── -->
              <div
                v-if="!isStaff"
                class="w-full py-1.5 px-2 text-center text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 rounded-xl truncate flex items-center justify-center gap-1 shadow-2xs"
              >
                <SparklesIcon class="size-3 text-emerald-600 shrink-0" />
                <span class="truncate">هدیه از طرف {{ book.gifted_by_name || 'ادمین تفکر' }}</span>
              </div>

              <!-- ── ADMIN MODE: Stock Count, + افزایش موجودی, ویرایش, and اهدا ── -->
              <template v-else>
                <!-- Dedicated Donate Button -->
                <Button
                  type="button"
                  size="xs"
                  class="w-full h-7 rounded-xl text-[10.5px] font-bold gap-1 justify-center bg-black text-white hover:bg-neutral-800 dark:bg-emerald-600 dark:text-white dark:hover:bg-emerald-700 transition-colors shadow-2xs"
                  :disabled="(book.available_quantity ?? (book.quantity - (book.reserved_quantity ?? 0))) <= 0"
                  @click.stop="handleDonateClick(book)"
                >
                  <HandHeartIcon class="size-3.5" />
                  <span>{{ languageStore.t('اهدا', 'Donate') }}</span>
                  <span
                    v-if="book.reserved_quantity && book.reserved_quantity > 0"
                    class="text-[9.5px] opacity-75 font-normal ms-0.5"
                  >
                    ({{ languageStore.n(book.available_quantity ?? (book.quantity - book.reserved_quantity)) }})
                  </span>
                </Button>

                <!-- Admin Action Row: Increase Stock, Edit, Delete -->
                <div class="flex items-center justify-between gap-1 pt-0.5">
                  <button
                    type="button"
                    class="flex-1 flex items-center justify-center gap-0.5 text-[9.5px] font-bold text-emerald-600 hover:text-emerald-700 py-1 rounded-md hover:bg-emerald-500/10 transition-colors cursor-pointer"
                    :title="languageStore.t('افزایش موجودی', '+ Stock')"
                    @click.stop="openStockDialog(book)"
                  >
                    <PlusIcon class="size-2.5" />
                    <span>موجودی</span>
                  </button>
                  <div class="h-3 w-px bg-border/50" />
                  <button
                    type="button"
                    class="flex-1 flex items-center justify-center gap-0.5 text-[9.5px] text-muted-foreground hover:text-foreground py-1 rounded-md hover:bg-muted/50 transition-colors cursor-pointer"
                    :title="languageStore.t('ویرایش', 'Edit')"
                    @click.stop="openEditDialog(book)"
                  >
                    <PencilIcon class="size-2.5" />
                    <span>ویرایش</span>
                  </button>
                  <div class="h-3 w-px bg-border/50" />
                  <button
                    type="button"
                    class="flex items-center justify-center p-1 text-muted-foreground hover:text-destructive rounded-md hover:bg-destructive/10 transition-colors cursor-pointer"
                    :title="languageStore.t('حذف', 'Delete')"
                    @click.stop="confirmDeleteBook(book)"
                  >
                    <Trash2Icon class="size-3" />
                  </button>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ── TAB 2: ADMIN DONATIONS REPORT (Read-Only) ── -->
    <template v-else-if="isStaff && adminActiveTab === 'reports'">
      <Card class="rounded-3xl border-border/60 shadow-sm overflow-hidden">
        <CardContent class="p-4 flex flex-col gap-3">
          <div class="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-border/40">
            <div class="flex items-center gap-2">
              <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <FileTextIcon class="size-4" />
              </div>
              <div class="flex flex-col">
                <h3 class="text-sm font-extrabold text-foreground">
                  {{ languageStore.t('سوابق و گزارش اهدای کتاب تفکر', 'Donation Records') }}
                </h3>
                <span class="text-[11px] text-muted-foreground">
                  {{ languageStore.t('فهرست کامل کتب اهدا شده به همراه مشخصات گیرنده و تاریخ', 'Complete log of gifted books') }}
                </span>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              size="xs"
              class="rounded-xl gap-1 text-[11px]"
              :disabled="isLoadingReports"
              @click="loadAdminReports"
            >
              <Loader2Icon v-if="isLoadingReports" class="size-3 animate-spin" />
              <span>{{ languageStore.t('بروزرسانی', 'Refresh') }}</span>
            </Button>
          </div>

          <!-- Loading -->
          <div v-if="isLoadingReports" class="flex flex-col gap-2 py-4">
            <Skeleton v-for="n in 4" :key="n" class="h-16 w-full rounded-2xl" />
          </div>

          <!-- Empty Reports -->
          <div
            v-else-if="adminReports.length === 0"
            class="py-12 flex flex-col items-center text-center gap-2 text-muted-foreground"
          >
            <HandHeartIcon class="size-10 text-muted-foreground/40" />
            <span class="text-xs font-bold">{{ languageStore.t('هنوز گزارشی از اهدای کتاب ثبت نشده است', 'No donation records yet') }}</span>
          </div>

          <!-- Reports List / Table -->
          <div v-else class="flex flex-col gap-2.5">
            <div
              v-for="rep in adminReports"
              :key="rep.id"
              class="rounded-2xl border border-border/50 bg-card p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs hover:border-primary/30 transition-colors"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-10 h-14 rounded-xl bg-muted/60 border border-border/40 overflow-hidden shrink-0 flex items-center justify-center">
                  <img
                    v-if="resolveMediaUrl(rep.cover_image)"
                    :src="resolveMediaUrl(rep.cover_image)!"
                    :alt="rep.book_title"
                    class="size-full object-cover"
                  />
                  <BookOpenIcon v-else class="size-5 text-muted-foreground/60" />
                </div>

                <div class="flex flex-col gap-0.5 min-w-0">
                  <span class="text-xs font-bold text-foreground truncate">
                    {{ rep.book_title }}
                  </span>
                  <div class="flex items-center gap-2 text-[11px] text-muted-foreground flex-wrap">
                    <span class="font-bold text-foreground">
                      {{ languageStore.n(rep.quantity) }} {{ languageStore.t('جلد', 'copies') }}
                    </span>
                    <span>•</span>
                    <span class="flex items-center gap-1">
                      <UserCheckIcon class="size-3 text-emerald-600" />
                      <span>گیرنده:</span>
                      <strong class="text-foreground">{{ rep.recipient_name || rep.recipient_phone }}</strong>
                      <span v-if="rep.recipient_name" class="font-mono text-[10px]" dir="ltr">({{ rep.recipient_phone }})</span>
                    </span>
                  </div>
                  <div class="flex items-center gap-2 mt-1 text-[10.5px] text-muted-foreground flex-wrap">
                    <span>ثبت توسط: <strong class="text-foreground">{{ rep.admin_name || 'ادمین تفکر' }}</strong></span>
                    <span>•</span>
                    <span class="flex items-center gap-1">
                      <ClockIcon class="size-3 text-muted-foreground" />
                      <span>{{ formatDateTime(rep.created_at) }}</span>
                    </span>
                  </div>
                </div>
              </div>

              <div class="self-end sm:self-center shrink-0">
                <Badge class="bg-emerald-600 text-white text-[10.5px] px-2 py-0.5 rounded-xl font-bold">
                  {{ rep.status_display || 'اهدا شده' }}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </template>

    <!-- ── RECIPIENT VIEW-ONLY DETAILS DIALOG ── -->
    <Dialog v-model:open="isViewDetailOpen">
      <DialogContent class="sm:max-w-md rounded-3xl p-5">
        <DialogHeader class="gap-1 text-start">
          <DialogTitle class="text-base font-extrabold text-foreground flex items-center gap-2">
            <BookOpenIcon class="size-5 text-emerald-600 shrink-0" />
            <span>{{ languageStore.t('مشخصات کتاب اهدایی', 'Book Details') }}</span>
          </DialogTitle>
          <DialogDescription class="text-xs text-muted-foreground">
            {{ languageStore.t('کتاب اهدایی موجود در قفسه شما', 'Gifted book in your shelf') }}
          </DialogDescription>
        </DialogHeader>

        <div v-if="viewingBook" class="flex flex-col gap-4 py-2">
          <!-- Book Header -->
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
              <div class="flex items-center gap-1.5 mt-1">
                <Badge class="bg-emerald-600 text-white text-[10px] px-2 py-0.5 rounded-full font-bold">
                  هدیه از طرف {{ viewingBook.gifted_by_name || 'ادمین تفکر' }}
                </Badge>
              </div>
            </div>
          </div>

          <!-- Info Details -->
          <div class="flex flex-col gap-2 text-xs">
            <div v-if="viewingBook.book_title.publisher" class="flex items-center justify-between p-2 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground">ناشر:</span>
              <span class="font-bold text-foreground">{{ viewingBook.book_title.publisher }}</span>
            </div>
            <div v-if="viewingBook.book_title.category" class="flex items-center justify-between p-2 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground">دسته‌بندی:</span>
              <span class="font-bold text-foreground">{{ viewingBook.book_title.category }}</span>
            </div>
            <div v-if="viewingBook.book_title.description" class="flex flex-col gap-1 p-2.5 rounded-xl bg-card border border-border/40">
              <span class="text-muted-foreground font-semibold">توضیحات:</span>
              <p class="text-muted-foreground leading-relaxed text-[11.5px]">{{ viewingBook.book_title.description }}</p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" class="w-full rounded-2xl bg-black text-white dark:bg-emerald-600 font-bold" @click="isViewDetailOpen = false">
            {{ languageStore.t('بستن', 'Close') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- ── ADMIN QUICK STOCK INCREASE DIALOG ── -->
    <Dialog v-model:open="isStockDialogOpen">
      <DialogContent class="sm:max-w-sm rounded-3xl p-5">
        <DialogHeader class="gap-1 text-start">
          <DialogTitle class="text-base font-extrabold text-foreground flex items-center gap-2">
            <PlusIcon class="size-5 text-emerald-600 shrink-0" />
            <span>{{ languageStore.t('افزایش موجودی انبار', 'Increase Stock') }}</span>
          </DialogTitle>
          <DialogDescription class="text-xs text-muted-foreground">
            {{ stockBook?.book_title.title }}
          </DialogDescription>
        </DialogHeader>

        <div v-if="stockBook" class="flex flex-col gap-3 py-2">
          <div class="flex items-center justify-between text-xs bg-muted/40 p-2.5 rounded-2xl border border-border/40">
            <span class="text-muted-foreground">موجودی فعلی:</span>
            <span class="font-bold text-foreground text-sm">{{ languageStore.n(stockBook.quantity) }} جلد</span>
          </div>

          <div class="flex flex-col gap-1.5">
            <span class="text-xs font-bold text-foreground">تعداد جلدهای جدید برای افزودن:</span>
            <div class="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="rounded-xl px-3 font-bold"
                :disabled="stockAdjustment <= 1"
                @click="stockAdjustment = Math.max(1, stockAdjustment - 1)"
              >
                -
              </Button>
              <Input
                v-model.number="stockAdjustment"
                type="number"
                min="1"
                class="text-center font-bold text-sm h-9 rounded-xl"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="rounded-xl px-3 font-bold"
                @click="stockAdjustment += 1"
              >
                +
              </Button>
            </div>
            <span class="text-[11px] text-muted-foreground text-center">
              موجودی جدید: {{ languageStore.n((stockBook.quantity || 1) + stockAdjustment) }} جلد
            </span>
          </div>
        </div>

        <DialogFooter class="gap-2">
          <Button
            type="button"
            class="rounded-2xl bg-black text-white hover:bg-neutral-800 dark:bg-emerald-600 dark:text-white font-bold"
            :disabled="isUpdatingStock || stockAdjustment < 1"
            @click="handleStockIncrease"
          >
            <Loader2Icon v-if="isUpdatingStock" class="size-3.5 animate-spin" />
            <span>{{ languageStore.t('ثبت افزایش موجودی', 'Save Stock') }}</span>
          </Button>
          <Button type="button" variant="outline" class="rounded-2xl" @click="isStockDialogOpen = false">
            {{ languageStore.t('انصراف', 'Cancel') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- QR Handover / Claim Dialog -->
    <BookDonationDetailDialog
      v-model:open="isClaimDialogOpen"
      :code-lookup-mode="true"
      @changed="handleBookSaved"
    />

    <!-- Add / Edit Dialog -->
    <AddShelfBookDialog
      v-model:open="isAddEditDialogOpen"
      :book="editingBook"
      @saved="handleBookSaved"
    />

    <!-- Donate Book Dialog -->
    <DonateSpecificBookDialog
      v-model:open="isDonateDialogOpen"
      :book="donatingBook"
      @donated="handleBookSaved"
    />

    <!-- Delete Confirmation AlertDialog -->
    <AlertDialog v-model:open="isDeleteDialogOpen">
      <AlertDialogContent class="rounded-3xl bg-card border-border/60">
        <AlertDialogHeader class="text-start">
          <AlertDialogTitle class="text-base font-extrabold">
            {{ languageStore.t('حذف کتاب از قفسه؟', 'Remove book from shelf?') }}
          </AlertDialogTitle>
          <AlertDialogDescription class="text-xs text-muted-foreground leading-relaxed">
            {{
              languageStore.t(
                `آیا مطمئن هستید که می‌خواهید «${deletingBook?.book_title.title || ''}» را از قفسه خود حذف کنید؟`,
                `Are you sure you want to remove "${deletingBook?.book_title.title || ''}" from your shelf?`
              )
            }}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter class="gap-2 sm:justify-start">
          <AlertDialogAction
            class="bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-2xl"
            :disabled="isDeleting"
            @click.prevent="executeDeleteBook"
          >
            {{ isDeleting ? languageStore.t('در حال حذف...', 'Removing...') : languageStore.t('بله، حذف شود', 'Delete') }}
          </AlertDialogAction>
          <AlertDialogCancel class="rounded-2xl" :disabled="isDeleting">
            {{ languageStore.t('انصراف', 'Cancel') }}
          </AlertDialogCancel>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>
