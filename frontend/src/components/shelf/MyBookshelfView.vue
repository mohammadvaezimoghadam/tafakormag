<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import {
  confirmGift,
  deleteShelfBook,
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
import AddShelfBookDialog from './AddShelfBookDialog.vue'
import DonateSpecificBookDialog from './DonateSpecificBookDialog.vue'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
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
  GiftIcon,
  HandHeartIcon,
  Loader2Icon,
  PencilIcon,
  PlusIcon,
  SearchIcon,
  SmartphoneIcon,
  SparklesIcon,
  Trash2Icon,
} from '@lucide/vue'

const emit = defineEmits<{
  (e: 'shelf-changed'): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()

const books = ref<ShelfBook[]>([])
const incomingGifts = ref<IncomingGiftItem[]>([])
const isActioningGift = ref<number | null>(null)

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

let searchDebounce: ReturnType<typeof setTimeout> | null = null

const hasActiveFilter = computed(() => Boolean(searchQuery.value.trim()))

const loadShelfData = async () => {
  isLoading.value = true
  try {
    const [listData, summaryData, giftsData] = await Promise.all([
      listMyShelfBooks({
        search: searchQuery.value,
      }),
      getMyShelfSummary(),
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

const openAddDialog = () => {
  editingBook.value = null
  isAddEditDialogOpen.value = true
}

const openEditDialog = (book: ShelfBook) => {
  editingBook.value = book
  isAddEditDialogOpen.value = true
}

const handleDonateClick = (book: ShelfBook) => {
  donatingBook.value = book
  isDonateDialogOpen.value = true
}

const handleBookSaved = async () => {
  await loadShelfData()
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
      languageStore.t('کتاب از قفسه شما حذف شد', 'Book removed from shelf'),
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
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Header / Summary Card -->
    <Card class="rounded-3xl border-border/60 shadow-sm py-4">
      <CardContent class="px-4 flex flex-col gap-3">
        <div class="flex items-center justify-between gap-3 flex-wrap">
          <div class="flex items-center gap-2.5">
            <div class="size-10 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <BookOpenIcon class="size-5" />
            </div>
            <div class="flex flex-col">
              <h2 class="text-base font-extrabold text-foreground">
                {{ languageStore.t('قفسه کتاب من', 'My Bookshelf') }}
              </h2>
              <p class="text-xs text-muted-foreground">
                {{
                  languageStore.t(
                    'فهرست کتاب‌ها و موجودی قفسه شما',
                    'Manage your book collection and quantities'
                  )
                }}
              </p>
            </div>
          </div>

          <Button type="button" class="rounded-2xl shrink-0" @click="openAddDialog">
            <PlusIcon data-icon="inline-start" />
            <span>{{ languageStore.t('ثبت کتاب جدید', 'Add Book') }}</span>
          </Button>
        </div>

        <!-- Clean single summary banner -->
        <div class="rounded-2xl bg-muted/40 border border-border/40 px-3.5 py-2.5 flex items-center justify-between text-xs">
          <span class="text-muted-foreground font-medium">
            {{ languageStore.t('موجودی کل کتاب‌ها:', 'Total Books in Shelf:') }}
          </span>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-foreground text-sm">
              {{ languageStore.n(summary.total_copies ?? summary.total) }} {{ languageStore.t('جلد', 'copies') }}
            </span>
            <span class="text-muted-foreground text-[11px]">
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
                  'کتاب‌هایی که کاربران به شماره همراه شما هدیه داده‌اند. برای ثبت در قفسه تحویل را تأیید کنید.',
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

    <!-- Search input -->
    <div class="relative">
      <SearchIcon class="size-4 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3.5 pointer-events-none" />
      <Input
        v-model="searchQuery"
        class="ps-10 h-10 bg-card border-border/60 rounded-2xl"
        :placeholder="languageStore.t('جستجو در نام کتاب یا نویسنده...', 'Search title or author...')"
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

    <!-- Empty state -->
    <Card v-else-if="books.length === 0" class="rounded-3xl border-dashed border-border/70 py-8">
      <CardContent class="px-6 flex flex-col items-center text-center gap-3">
        <div class="size-12 rounded-2xl bg-muted flex items-center justify-center text-muted-foreground">
          <BookOpenIcon class="size-6" />
        </div>
        <div class="flex flex-col gap-1 max-w-sm">
          <span class="text-sm font-bold text-foreground">
            {{
              hasActiveFilter
                ? languageStore.t('کتابی با این عبارت پیدا نشد', 'No matching books found')
                : languageStore.t('قفسه کتاب شما هنوز خالی است', 'Your bookshelf is still empty')
            }}
          </span>
          <span class="text-xs text-muted-foreground leading-relaxed">
            {{
              hasActiveFilter
                ? languageStore.t('عبارت جستجو را تغییر دهید یا پاک کنید.', 'Try changing or clearing your search.')
                : languageStore.t(
                    'کتاب‌های خود را ثبت کنید تا در قفسه شما نمایش داده شوند.',
                    'Add your books so they appear in your shelf.'
                  )
            }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <Button v-if="hasActiveFilter" type="button" variant="outline" size="sm" class="rounded-xl" @click="clearFilters">
            {{ languageStore.t('پاک کردن جستجو', 'Reset Search') }}
          </Button>
          <Button v-else type="button" size="sm" class="rounded-xl" @click="openAddDialog">
            <PlusIcon data-icon="inline-start" />
            <span>{{ languageStore.t('ثبت اولین کتاب', 'Add First Book') }}</span>
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Shelf Books Grid: 3 columns (matching Home items exactly) -->
    <div v-else class="grid grid-cols-3 gap-2.5 sm:gap-3.5">
      <div
        v-for="book in books"
        :key="book.id"
        role="button"
        tabindex="0"
        @click="openEditDialog(book)"
        @keydown.enter.prevent="openEditDialog(book)"
        class="w-full min-w-0 h-auto rounded-2xl border border-border/60 bg-card/85 dark:bg-card/65 backdrop-blur-md shadow-xs hover:border-primary/40 hover:shadow-sm transition-all overflow-hidden flex flex-col select-none cursor-pointer group"
      >
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

          <!-- Total Quantity Badge -->
          <div
            class="absolute top-1.5 start-1.5 px-1.5 py-0.5 rounded-md bg-background/95 border text-[10px] font-bold shadow-2xs"
            :class="(book.quantity ?? 1) <= 0 ? 'text-amber-600 dark:text-amber-400 border-amber-500/40' : 'text-foreground border-border/60'"
          >
            <span>{{ languageStore.n(book.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}</span>
          </div>

          <!-- Gifted Badge -->
          <div
            v-if="book.is_gift"
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
            <!-- Gifted Book indicator (cannot donate) -->
            <div
              v-if="book.is_gift || book.can_donate === false"
              class="w-full py-1 text-center text-[10px] text-muted-foreground font-medium bg-muted/40 rounded-xl truncate px-1"
            >
              <span>{{ book.gifted_by_name ? `هدیه از طرف ${book.gifted_by_name}` : languageStore.t('کتاب هدیه', 'Gifted book') }}</span>
            </div>

            <!-- Dedicated Donate Button on Shelf -->
            <Button
              v-else
              type="button"
              size="xs"
              class="w-full h-7 rounded-xl text-[10.5px] font-bold gap-1 justify-center bg-black text-white hover:bg-neutral-800 dark:bg-secondary dark:text-secondary-foreground dark:hover:bg-secondary/80 transition-colors shadow-2xs"
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

            <!-- Secondary Actions: Edit & Delete -->
            <div class="flex items-center justify-between gap-1 pt-0.5">
              <button
                type="button"
                class="flex-1 flex items-center justify-center gap-1 text-[10px] text-muted-foreground hover:text-foreground py-1 rounded-md hover:bg-muted/50 transition-colors"
                :title="languageStore.t('ویرایش', 'Edit')"
                @click.stop="openEditDialog(book)"
              >
                <PencilIcon class="size-3" />
                <span>{{ languageStore.t('ویرایش', 'Edit') }}</span>
              </button>
              <div class="h-3 w-px bg-border/50" />
              <button
                type="button"
                class="flex-1 flex items-center justify-center gap-1 text-[10px] text-muted-foreground hover:text-destructive py-1 rounded-md hover:bg-destructive/10 transition-colors"
                :title="languageStore.t('حذف', 'Delete')"
                @click.stop="confirmDeleteBook(book)"
              >
                <Trash2Icon class="size-3" />
                <span>{{ languageStore.t('حذف', 'Delete') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

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
