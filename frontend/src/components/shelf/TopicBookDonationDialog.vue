<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import { 
  listMyShelfBooks, 
  publishShelfBookListing, 
  extractApiErrorMessage 
} from '@/api/shelf'
import type { ShelfBook, DonationMethod, ShippingPayer } from '@/types/shelf'
import AddShelfBookDialog from './AddShelfBookDialog.vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { 
  BookOpenIcon, 
  PlusIcon, 
  CheckCircle2Icon, 
  QrCodeIcon, 
  PackageIcon, 
  Loader2Icon,
  SparklesIcon,
  XIcon
} from '@lucide/vue'

const props = defineProps<{
  open: boolean
  topicId?: number | string | null
  topicName?: string | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'published', book: ShelfBook): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()
const userStore = useUserStore()

const myBooks = ref<ShelfBook[]>([])
const loadingBooks = ref(false)
const selectedBook = ref<ShelfBook | null>(null)
const isAddBookOpen = ref(false)
const isSubmitting = ref(false)

// Form fields
const enableInPerson = ref(true)
const enablePostal = ref(false)
const shippingPayer = ref<ShippingPayer>('recipient')
const donorNote = ref('')

const isReadyToSubmit = computed(() => {
  return selectedBook.value && (enableInPerson.value || enablePostal.value) && !isSubmitting.value
})

const loadShelfBooks = async () => {
  if (!userStore.isAuthenticated) return
  loadingBooks.value = true
  try {
    const books = await listMyShelfBooks()
    myBooks.value = books
    if (!selectedBook.value && myBooks.value.length > 0) {
      selectedBook.value = myBooks.value[0]
    }
  } catch (err) {
    console.warn('Failed to load shelf books:', err)
  } finally {
    loadingBooks.value = false
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      selectedBook.value = null
      donorNote.value = ''
      enableInPerson.value = true
      enablePostal.value = false
      loadShelfBooks()
    }
  }
)

const handleBookCreated = (createdBook: ShelfBook) => {
  isAddBookOpen.value = false
  myBooks.value.unshift(createdBook)
  selectedBook.value = createdBook
  toastStore.triggerToast(
    languageStore.t('کتاب جدید به قفسه شما افزوده شد.', 'New book added to your shelf.'),
    'success'
  )
}

const handleSubmit = async () => {
  if (!selectedBook.value) {
    toastStore.triggerToast(
      languageStore.t('لطفاً یک کتاب را انتخاب نمایید.', 'Please select a book.'),
      'error'
    )
    return
  }

  const methods: DonationMethod[] = []
  if (enableInPerson.value) methods.push('in_person')
  if (enablePostal.value) methods.push('postal')

  if (methods.length === 0) {
    toastStore.triggerToast(
      languageStore.t('حداقل یک روش اهدا (حضوری یا پستی) را انتخاب نمایید.', 'Select at least one donation method.'),
      'error'
    )
    return
  }

  isSubmitting.value = true
  try {
    const published = await publishShelfBookListing(selectedBook.value.id, {
      deal_type: 'donation',
      topic_id: props.topicId ? Number(props.topicId) : undefined,
      donation_methods: methods,
      shipping_payer: shippingPayer.value,
      description: donorNote.value.trim() || undefined,
    })

    toastStore.triggerToast(
      languageStore.t('کتاب با موفقیت در تاپیک به اشتراک گذاشته شد.', 'Book successfully donated in topic.'),
      'success'
    )
    emit('published', published)
    emit('update:open', false)
  } catch (err: any) {
    const msg = extractApiErrorMessage(err, 'خطا در انتشار کتاب در تاپیک')
    toastStore.triggerToast(msg, 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent class="sm:max-w-lg p-0 overflow-hidden rounded-3xl bg-card border border-border/60 shadow-2xl">
      <!-- Decorative Header -->
      <div class="h-1.5 w-full bg-linear-to-r from-amber-500 via-emerald-500 to-teal-500" />

      <DialogHeader class="p-5 pb-3 text-start">
        <div class="flex items-center gap-2.5">
          <div class="size-10 rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/20">
            <BookOpenIcon class="size-5" />
          </div>
          <div class="flex flex-col">
            <DialogTitle class="text-base font-extrabold text-foreground">
              {{ languageStore.t('اهدای کتاب در تاپیک', 'Donate Book in Topic') }}
            </DialogTitle>
            <DialogDescription class="text-xs text-muted-foreground">
              <span v-if="topicName">{{ topicName }}</span>
              <span v-else>{{ languageStore.t('انتخاب کتاب از قفسه و انتشار کارت در گفتگو', 'Select from shelf and publish card in chat') }}</span>
            </DialogDescription>
          </div>
        </div>
      </DialogHeader>

      <div class="p-5 pt-0 flex flex-col gap-4 max-h-[70vh] overflow-y-auto">
        <!-- 1. BOOK SELECTION SECTION -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label class="text-xs font-bold text-foreground">
              {{ languageStore.t('۱. انتخاب کتاب از قفسه من', '1. Select book from shelf') }}
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="h-7 px-2 rounded-lg text-[11px] gap-1 border-border/60 text-primary cursor-pointer hover:bg-muted"
              @click="isAddBookOpen = true"
            >
              <PlusIcon class="size-3" />
              <span>{{ languageStore.t('افزودن کتاب جدید', 'Add New Book') }}</span>
            </Button>
          </div>

          <!-- Loading state -->
          <div v-if="loadingBooks" class="p-6 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
            <Loader2Icon class="size-4 animate-spin text-primary" />
            <span>{{ languageStore.t('در حال دریافت لیست کتاب‌ها...', 'Loading shelf books...') }}</span>
          </div>

          <!-- Empty shelf -->
          <div
            v-else-if="myBooks.length === 0"
            class="p-4 rounded-2xl border border-dashed border-border/80 text-center flex flex-col items-center gap-2 bg-muted/20"
          >
            <BookOpenIcon class="size-8 text-muted-foreground/60" />
            <p class="text-xs text-muted-foreground">
              {{ languageStore.t('هنوز کتابی در قفسه خود ثبت نکرده‌اید.', 'No books found on your shelf.') }}
            </p>
            <Button
              type="button"
              size="sm"
              class="h-8 rounded-xl text-xs font-bold gap-1 cursor-pointer"
              @click="isAddBookOpen = true"
            >
              <PlusIcon class="size-3.5" />
              <span>{{ languageStore.t('ثبت اولین کتاب', 'Add your first book') }}</span>
            </Button>
          </div>

          <!-- Horizontal Carousel of Books -->
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-1">
            <div
              v-for="b in myBooks"
              :key="b.id"
              class="p-2.5 rounded-2xl border transition-all cursor-pointer flex items-center gap-2.5 text-start select-none"
              :class="selectedBook?.id === b.id 
                ? 'border-amber-500 bg-amber-500/10 shadow-xs' 
                : 'border-border/60 hover:border-border bg-card hover:bg-muted/30'"
              @click="selectedBook = b"
            >
              <!-- Small cover -->
              <div class="size-12 shrink-0 rounded-lg overflow-hidden border border-border/60 bg-muted/50 flex items-center justify-center text-muted-foreground">
                <img 
                  v-if="b.book_title.cover_image" 
                  :src="b.book_title.cover_image" 
                  :alt="b.book_title.title"
                  class="w-full h-full object-cover" 
                />
                <BookOpenIcon v-else class="size-5 text-amber-500/70" />
              </div>

              <!-- Meta -->
              <div class="flex flex-col flex-1 min-w-0">
                <span class="text-xs font-bold text-foreground truncate">
                  {{ b.book_title.title }}
                </span>
                <span class="text-[11px] text-muted-foreground truncate">
                  {{ b.book_title.author }}
                </span>
                <div class="flex items-center gap-1 mt-0.5">
                  <Badge variant="outline" class="text-[9px] px-1 py-0 h-4 border-border/40">
                    {{ b.quantity }} {{ languageStore.t('جلد', 'copies') }}
                  </Badge>
                  <span v-if="selectedBook?.id === b.id" class="text-amber-600 dark:text-amber-400 font-bold text-[10px] mr-auto">
                    ✓
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. HANDOVER METHODS -->
        <div class="flex flex-col gap-2 pt-2 border-t border-border/40">
          <label class="text-xs font-bold text-foreground">
            {{ languageStore.t('۲. شیوه‌های تحویل و اهدا', '2. Delivery & Handover Methods') }}
          </label>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <!-- In-person QR handover -->
            <label 
              class="p-3 rounded-2xl border transition-colors cursor-pointer flex items-start gap-2.5 select-none"
              :class="enableInPerson ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-border/60 bg-card'"
            >
              <input type="checkbox" v-model="enableInPerson" class="mt-0.5 rounded text-emerald-600 cursor-pointer" />
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-1.5">
                  <QrCodeIcon class="size-3.5 text-emerald-600" />
                  <span class="text-xs font-bold text-foreground">
                    {{ languageStore.t('تحویل حضوری (کد QR)', 'In-Person (QR)') }}
                  </span>
                </div>
                <span class="text-[10.5px] text-muted-foreground leading-relaxed">
                  {{ languageStore.t('تولید شناسنامه گردش TK و انتقال با اسکن بارکد', 'Generates QR circulation code') }}
                </span>
              </div>
            </label>

            <!-- Postal handover -->
            <label 
              class="p-3 rounded-2xl border transition-colors cursor-pointer flex items-start gap-2.5 select-none"
              :class="enablePostal ? 'border-blue-500/50 bg-blue-500/5' : 'border-border/60 bg-card'"
            >
              <input type="checkbox" v-model="enablePostal" class="mt-0.5 rounded text-blue-600 cursor-pointer" />
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-1.5">
                  <PackageIcon class="size-3.5 text-blue-600" />
                  <span class="text-xs font-bold text-foreground">
                    {{ languageStore.t('ارسال پستی', 'Postal Delivery') }}
                  </span>
                </div>
                <span class="text-[10.5px] text-muted-foreground leading-relaxed">
                  {{ languageStore.t('ارسال از طریق پست پیشتاز به متقاضی', 'Shipping via post') }}
                </span>
              </div>
            </label>
          </div>

          <!-- Postal Shipping Payer selector -->
          <div v-if="enablePostal" class="flex items-center gap-3 p-2.5 rounded-xl bg-muted/40 border border-border/40 text-xs">
            <span class="text-muted-foreground">{{ languageStore.t('هزینه ارسال پستی:', 'Shipping cost:') }}</span>
            <label class="inline-flex items-center gap-1 cursor-pointer">
              <input type="radio" value="recipient" v-model="shippingPayer" />
              <span>{{ languageStore.t('پس‌کرایه (گیرنده)', 'Recipient pays') }}</span>
            </label>
            <label class="inline-flex items-center gap-1 cursor-pointer">
              <input type="radio" value="donor" v-model="shippingPayer" />
              <span>{{ languageStore.t('اهداکننده (رایگان)', 'Free (Donor pays)') }}</span>
            </label>
          </div>
        </div>

        <!-- 3. DONOR NOTE / MESSAGE -->
        <div class="flex flex-col gap-1.5 pt-2 border-t border-border/40">
          <label class="text-xs font-bold text-foreground">
            {{ languageStore.t('۳. یادداشت یا پیام اهداکننده (اختیاری)', '3. Donor message / note (optional)') }}
          </label>
          <Textarea
            v-model="donorNote"
            rows="2"
            class="text-xs rounded-xl resize-none"
            :placeholder="languageStore.t('مثال: این کتاب را با اشتیاق خوانده‌ام و امیدوارم برای خواننده بعدی هم الهام‌بخش باشد...', 'e.g., A gift for fellow book lovers in this topic...')"
          />
        </div>
      </div>

      <DialogFooter class="p-4 bg-muted/20 border-t border-border/50 flex items-center justify-end gap-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="h-9 rounded-xl text-xs cursor-pointer"
          @click="emit('update:open', false)"
        >
          {{ languageStore.t('انصراف', 'Cancel') }}
        </Button>

        <Button
          type="button"
          size="sm"
          class="h-9 px-4 rounded-xl text-xs font-bold gap-1.5 bg-linear-to-r from-amber-500 to-emerald-600 hover:from-amber-600 hover:to-emerald-700 text-white shadow-xs cursor-pointer active:scale-95 transition-all"
          :disabled="!isReadyToSubmit"
          @click="handleSubmit"
        >
          <Loader2Icon v-if="isSubmitting" class="size-3.5 animate-spin" />
          <SparklesIcon v-else class="size-3.5" />
          <span>{{ languageStore.t('انتشار کارت کتاب در تاپیک', 'Publish Book in Topic') }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <!-- Add Book Sub-Dialog -->
  <AddShelfBookDialog
    v-model:open="isAddBookOpen"
    @created="handleBookCreated"
  />
</template>

