<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import {
  cancelBookHandover,
  claimBookCopy,
  confirmBookHandover,
  extractApiErrorMessage,
  initiateBookHandover,
  inspectBookCopy,
  listIncomingBookHandovers,
  listMyShelfBooks,
  startShelfBookCirculation,
} from '@/api/shelf'
import type { BookCopyInspectResult, BookTransferRecord, ShelfBook } from '@/types/shelf'
import { generateQrDataUrl, generateQrSvgString } from '@/utils/qrCode'
import AddShelfBookDialog from './AddShelfBookDialog.vue'
import QuantityStepper from './QuantityStepper.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  BookOpenIcon,
  CheckCircle2Icon,
  ChevronDownIcon,
  CopyIcon,
  DownloadIcon,
  HandHeartIcon,
  KeyRoundIcon,
  Loader2Icon,
  LogInIcon,
  PlusIcon,
  QrCodeIcon,
  RefreshCwIcon,
  SearchIcon,
  SmartphoneIcon,
  UserCheckIcon,
} from '@lucide/vue'

interface HandoverSession {
  book: ShelfBook
  shortCode: string
  quantity: number
  otpCode: string
  transferId: number | null
  assignedPhone: string
}

const props = withDefaults(
  defineProps<{
    open: boolean
    initialBookId?: number | null
    initialMode?: 'donate' | 'receive'
  }>(),
  {
    initialBookId: null,
    initialMode: 'donate',
  }
)

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'donated', book?: ShelfBook): void
  (e: 'open-handover', shortCode: string): void
}>()

const languageStore = useLanguageStore()
const userStore = useUserStore()
const toastStore = useToastStore()

const activeMode = ref<'donate' | 'receive'>('donate')

// Donate Tab State
const shelfBooks = ref<ShelfBook[]>([])
const isLoadingBooks = ref(false)
const searchQuery = ref('')
const selectedBookId = ref<number | null>(null)
const donationQuantity = ref(1)
const donationNote = ref('')
const isSubmitting = ref(false)
const formError = ref('')
const isAddShelfBookOpen = ref(false)

// Live Step-2 Handover Session (inside the SAME dialog)
const handoverSession = ref<HandoverSession | null>(null)
const activeInspect = ref<BookCopyInspectResult | null>(null)
const isPhoneOptionOpen = ref(false)
const recipientPhoneInput = ref('')
const phoneError = ref('')
const isSendingPhone = ref(false)
const handoverCompleted = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

// Receive Tab State (inside the SAME dialog)
const incomingTransfers = ref<BookTransferRecord[]>([])
const isLoadingIncoming = ref(false)
const receiveCodeInput = ref('')
const receiveInspect = ref<BookCopyInspectResult | null>(null)
const receiveOtpInput = ref('')
const receiveQty = ref(1)
const receiveNote = ref('')
const receiveError = ref('')
const isInspectingCode = ref(false)
const isCompletingReceive = ref(false)
const receiveCompletedTitle = ref('')

const hasAuthSession = computed(
  () =>
    userStore.isAuthenticated ||
    Boolean(
      (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('auth_token')) ||
        (typeof localStorage !== 'undefined' && localStorage.getItem('auth_token'))
    )
)

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onBeforeUnmount(() => {
  stopPolling()
})

const isSelectableForDonation = (book: ShelfBook): boolean => {
  if ((book.quantity ?? 1) <= 0) return false
  if (book.book_format !== 'physical') return false
  if (book.physical_copy_summary?.is_transferred_away) return false
  if (book.physical_copy_summary?.status === 'in_station') return false
  return (
    book.disposition === 'keeping' ||
    book.disposition === 'circulating' ||
    book.disposition === 'for_donation'
  )
}

const isCirculatingReadyBook = (book: ShelfBook): boolean =>
  (book.quantity ?? 1) > 0 &&
  book.book_format === 'physical' &&
  !book.physical_copy_summary?.is_transferred_away &&
  book.disposition === 'circulating' &&
  Boolean(book.physical_copy_summary?.short_code)

const loadBooks = async () => {
  if (!hasAuthSession.value) {
    shelfBooks.value = []
    return
  }
  isLoadingBooks.value = true
  formError.value = ''
  try {
    shelfBooks.value = await listMyShelfBooks()
  } catch (err) {
    formError.value = extractApiErrorMessage(
      err,
      languageStore.t('دریافت کتاب‌های قفسه ناموفق بود', 'Failed to load your bookshelf')
    )
  } finally {
    isLoadingBooks.value = false
  }
}

const loadIncoming = async () => {
  if (!hasAuthSession.value) {
    incomingTransfers.value = []
    return
  }
  isLoadingIncoming.value = true
  try {
    incomingTransfers.value = await listIncomingBookHandovers()
  } catch {
    incomingTransfers.value = []
  } finally {
    isLoadingIncoming.value = false
  }
}

const resetAllState = () => {
  stopPolling()
  searchQuery.value = ''
  selectedBookId.value = null
  donationQuantity.value = 1
  donationNote.value = ''
  formError.value = ''
  handoverSession.value = null
  activeInspect.value = null
  isPhoneOptionOpen.value = false
  recipientPhoneInput.value = ''
  phoneError.value = ''
  handoverCompleted.value = false
  receiveCodeInput.value = ''
  receiveInspect.value = null
  receiveOtpInput.value = ''
  receiveQty.value = 1
  receiveNote.value = ''
  receiveError.value = ''
  receiveCompletedTitle.value = ''
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      stopPolling()
      return
    }
    resetAllState()
    activeMode.value = props.initialMode || 'donate'

    if (hasAuthSession.value) {
      await Promise.all([loadBooks(), loadIncoming()])
      if (props.initialBookId) {
        const pre = shelfBooks.value.find((b) => b.id === props.initialBookId)
        if (pre && isSelectableForDonation(pre)) {
          selectedBookId.value = pre.id
          return
        }
      }
      const firstEligible = shelfBooks.value.find((b) => isSelectableForDonation(b))
      if (firstEligible) {
        selectedBookId.value = firstEligible.id
      }
    }
  },
  { immediate: true }
)

watch(hasAuthSession, async (authed) => {
  if (authed && props.open) {
    await Promise.all([loadBooks(), loadIncoming()])
    if (!selectedBookId.value) {
      const firstEligible = shelfBooks.value.find((b) => isSelectableForDonation(b))
      if (firstEligible) {
        selectedBookId.value = firstEligible.id
      }
    }
  }
})

watch(activeMode, (mode) => {
  if (mode === 'receive' && hasAuthSession.value) {
    loadIncoming()
  }
})

const filteredBooks = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const ordered = [...shelfBooks.value].sort((a, b) => {
    const score = (x: ShelfBook) =>
      isCirculatingReadyBook(x) ? 0 : isSelectableForDonation(x) ? 1 : 2
    return score(a) - score(b)
  })
  if (!q) return ordered
  return ordered.filter((b) => {
    const t = b.book_title.title?.toLowerCase() || ''
    const a = b.book_title.author?.toLowerCase() || ''
    return t.includes(q) || a.includes(q)
  })
})

const selectedBook = computed<ShelfBook | null>(
  () => shelfBooks.value.find((b) => b.id === selectedBookId.value) || null
)

const maxDonationQty = computed(() => Math.max(1, selectedBook.value?.quantity ?? 1))

watch(selectedBookId, () => {
  donationQuantity.value = 1
})

const resolveMediaUrl = (raw?: string | null): string | null => {
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw
  }
  return `/${raw}`
}

const sessionShareUrl = computed(() => {
  const session = handoverSession.value
  if (!session?.shortCode) return ''
  const origin =
    typeof window !== 'undefined' && window.location?.origin
      ? window.location.origin
      : 'https://tafakormag.ir'
  const base = `${origin}/b/${session.shortCode}`
  return session.otpCode ? `${base}?otp=${encodeURIComponent(session.otpCode)}` : base
})

const sessionQrDataUrl = computed(() => {
  if (!sessionShareUrl.value) return ''
  try {
    return generateQrDataUrl(sessionShareUrl.value, 2)
  } catch {
    return ''
  }
})

const getBookStatusLabel = (book: ShelfBook): string => {
  if ((book.quantity ?? 1) <= 0 || book.physical_copy_summary?.is_transferred_away) {
    return languageStore.t('اهدا شده', 'Donated')
  }
  if (book.book_format !== 'physical') {
    return languageStore.t('دیجیتال', 'Digital')
  }
  if (isCirculatingReadyBook(book)) {
    return languageStore.t(
      `آماده تحویل (${book.physical_copy_summary?.short_code})`,
      `Ready (${book.physical_copy_summary?.short_code})`
    )
  }
  if (book.disposition === 'for_sale') {
    return languageStore.t('در فروش', 'For Sale')
  }
  if (book.disposition === 'for_donation') {
    return languageStore.t('در لیست اهدا', 'Offered')
  }
  return languageStore.t('در قفسه', 'In Shelf')
}

const pollHandoverStatus = async () => {
  const session = handoverSession.value
  if (!session || handoverCompleted.value || !props.open) return
  try {
    const inspected = await inspectBookCopy(session.shortCode)
    activeInspect.value = inspected
    if (!inspected.is_holder) {
      handoverCompleted.value = true
      stopPolling()
      await loadBooks()
      emit('donated')
    }
  } catch {
    // Ignore transient poll errors
  }
}

const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(() => {
    pollHandoverStatus()
  }, 3500)
}

const enterHandoverStep = async (book: ShelfBook, qty: number, note: string) => {
  isSubmitting.value = true
  formError.value = ''
  try {
    let workingBook = book
    let shortCode = workingBook.physical_copy_summary?.short_code || ''
    if (!shortCode || workingBook.disposition !== 'circulating') {
      workingBook = await startShelfBookCirculation(workingBook.id, {
        condition: workingBook.condition || 'good',
      })
      shortCode = workingBook.physical_copy_summary?.short_code || ''
    }
    if (!shortCode) {
      throw new Error(languageStore.t('کد گردش کتاب ایجاد نشد', 'Failed to generate book code'))
    }

    const inspected = await inspectBookCopy(shortCode)
    activeInspect.value = inspected

    if (inspected.active_transfer?.status === 'pending_donor') {
      handoverSession.value = {
        book: workingBook,
        shortCode,
        quantity: inspected.active_transfer.quantity ?? qty,
        otpCode: '',
        transferId: inspected.active_transfer.id,
        assignedPhone: '',
      }
      startPolling()
      return
    }

    const trf = await initiateBookHandover({
      short_code: shortCode,
      method: 'otp_fallback',
      quantity: qty,
      donor_note: note,
    })

    const refreshedInspect = await inspectBookCopy(shortCode).catch(() => inspected)
    activeInspect.value = refreshedInspect

    handoverSession.value = {
      book: workingBook,
      shortCode,
      quantity: trf.quantity ?? qty,
      otpCode: trf.otp_code || '',
      transferId: trf.id,
      assignedPhone: '',
    }
    startPolling()
    await loadBooks()
    emit('donated', workingBook)
  } catch (err) {
    formError.value = extractApiErrorMessage(
      err,
      languageStore.t('آماده‌سازی تحویل حضوری انجام نشد', 'Failed to prepare handover')
    )
  } finally {
    isSubmitting.value = false
  }
}

const handleCardClick = (book: ShelfBook) => {
  if (!isSelectableForDonation(book)) return
  selectedBookId.value = book.id
  formError.value = ''
}

const handleNewBookAdded = async (created: ShelfBook) => {
  await loadBooks()
  if (isSelectableForDonation(created)) {
    selectedBookId.value = created.id
    toastStore.triggerToast(
      languageStore.t(
        'کتاب به قفسه شما اضافه و آماده اهدا شد',
        'Book saved to shelf and selected for handover'
      ),
      'success'
    )
  }
  emit('donated', created)
}

const handleProceedToHandover = async () => {
  if (!selectedBook.value) {
    formError.value = languageStore.t(
      'لطفاً ابتدا یکی از کتاب‌های قفسه خود را انتخاب کنید.',
      'Please select a book from your shelf first.'
    )
    return
  }
  const qty = Math.min(maxDonationQty.value, Math.max(1, Math.floor(donationQuantity.value || 1)))
  await enterHandoverStep(selectedBook.value, qty, donationNote.value.trim())
}

const handleConfirmPendingClaim = async () => {
  const trfId = activeInspect.value?.active_transfer?.id
  if (!trfId) return
  isSubmitting.value = true
  try {
    await confirmBookHandover(trfId, { donor_note: donationNote.value.trim() })
    handoverCompleted.value = true
    stopPolling()
    toastStore.triggerToast(
      languageStore.t('تحویل کتاب با موفقیت تایید و منتقل شد', 'Handover confirmed and transferred'),
      'success'
    )
    await loadBooks()
    emit('donated')
  } catch (err) {
    formError.value = extractApiErrorMessage(
      err,
      languageStore.t('تایید انتقال انجام نشد', 'Failed to confirm handover')
    )
  } finally {
    isSubmitting.value = false
  }
}

const handleSendToPhone = async () => {
  const session = handoverSession.value
  const phone = recipientPhoneInput.value.trim()
  if (!session || !phone) return
  isSendingPhone.value = true
  phoneError.value = ''
  try {
    const trf = await initiateBookHandover({
      short_code: session.shortCode,
      recipient_phone: phone,
      method: 'scan_confirm',
      quantity: session.quantity,
      donor_note: donationNote.value.trim(),
    })
    handoverSession.value = {
      ...session,
      transferId: trf.id,
      otpCode: '',
      assignedPhone: phone,
    }
    activeInspect.value = await inspectBookCopy(session.shortCode).catch(() => activeInspect.value)
    toastStore.triggerToast(
      languageStore.t('درخواست تحویل برای شماره گیرنده ثبت شد', 'Handover sent to recipient account'),
      'success'
    )
  } catch (err) {
    phoneError.value = extractApiErrorMessage(
      err,
      languageStore.t('ارسال به این شماره انجام نشد', 'Failed to assign phone')
    )
  } finally {
    isSendingPhone.value = false
  }
}

const handleBackToSelect = async () => {
  stopPolling()
  const session = handoverSession.value
  if (session?.transferId && activeInspect.value?.active_transfer?.status === 'pending_recipient') {
    await cancelBookHandover(session.transferId).catch(() => null)
  }
  handoverSession.value = null
  activeInspect.value = null
  isPhoneOptionOpen.value = false
  recipientPhoneInput.value = ''
  phoneError.value = ''
  handoverCompleted.value = false
}

// Receive Tab Handlers
const handleInspectReceiveCode = async () => {
  const raw = receiveCodeInput.value.trim()
  if (!raw) return
  isInspectingCode.value = true
  receiveError.value = ''
  receiveCompletedTitle.value = ''
  try {
    let extractedCode = raw
    let extractedOtp = ''
    try {
      if (raw.includes('http://') || raw.includes('https://') || raw.includes('/b/')) {
        const parsed = new URL(raw.startsWith('http') ? raw : `https://tafakormag.ir${raw.startsWith('/') ? '' : '/'}${raw}`)
        const seg = parsed.pathname.split('/').filter(Boolean).pop()
        if (seg) extractedCode = seg
        extractedOtp = parsed.searchParams.get('otp') || ''
      }
    } catch {
      // keep raw
    }
    const inspected = await inspectBookCopy(extractedCode)
    receiveInspect.value = inspected
    receiveQty.value = Math.min(
      Math.max(1, inspected.available_quantity ?? 1),
      Math.max(1, inspected.active_transfer?.quantity ?? 1)
    )
    receiveOtpInput.value = extractedOtp
  } catch (err) {
    receiveInspect.value = null
    receiveError.value = extractApiErrorMessage(
      err,
      languageStore.t('کتابی با این شناسه یافت نشد', 'Book code not found')
    )
  } finally {
    isInspectingCode.value = false
  }
}

const handleConfirmIncomingTransfer = async (trf: BookTransferRecord) => {
  isCompletingReceive.value = true
  receiveError.value = ''
  try {
    await confirmBookHandover(trf.id, {
      recipient_note: receiveNote.value.trim(),
    })
    receiveCompletedTitle.value = trf.book_title_name || trf.copy_short_code || ''
    toastStore.triggerToast(
      languageStore.t('کتاب به قفسه شما منتقل شد', 'Book added to your shelf'),
      'success'
    )
    await Promise.all([loadIncoming(), loadBooks()])
    emit('donated')
  } catch (err) {
    receiveError.value = extractApiErrorMessage(
      err,
      languageStore.t('تایید دریافت انجام نشد', 'Failed to confirm receipt')
    )
  } finally {
    isCompletingReceive.value = false
  }
}

const handleVerifyReceiveOtp = async () => {
  const trf = receiveInspect.value?.active_transfer
  if (!trf || !receiveOtpInput.value.trim()) return
  isCompletingReceive.value = true
  receiveError.value = ''
  try {
    await confirmBookHandover(trf.id, {
      otp_code: receiveOtpInput.value.trim(),
      recipient_note: receiveNote.value.trim(),
    })
    receiveCompletedTitle.value = receiveInspect.value?.book_title.title || ''
    receiveInspect.value = null
    toastStore.triggerToast(
      languageStore.t('کتاب با موفقیت تحویل گرفته شد و در قفسه شما ثبت شد', 'Book received and added to your shelf'),
      'success'
    )
    await Promise.all([loadIncoming(), loadBooks()])
    emit('donated')
  } catch (err) {
    receiveError.value = extractApiErrorMessage(
      err,
      languageStore.t('کد تایید نادرست یا منقضی شده است', 'Invalid or expired code')
    )
  } finally {
    isCompletingReceive.value = false
  }
}

const handleClaimReceiveCode = async () => {
  if (!receiveInspect.value) return
  isCompletingReceive.value = true
  receiveError.value = ''
  try {
    await claimBookCopy({
      short_code: receiveInspect.value.short_code,
      quantity: receiveQty.value,
      recipient_note: receiveNote.value.trim(),
    })
    receiveInspect.value = await inspectBookCopy(receiveInspect.value.short_code)
    toastStore.triggerToast(
      languageStore.t('درخواست روی گوشی اهداکننده ارسال شد', 'Claim sent to donor device'),
      'success'
    )
  } catch (err) {
    receiveError.value = extractApiErrorMessage(
      err,
      languageStore.t('ثبت درخواست انجام نشد', 'Failed to submit claim')
    )
  } finally {
    isCompletingReceive.value = false
  }
}

const copyText = async (text: string, label: string) => {
  try {
    await navigator.clipboard.writeText(text)
    toastStore.triggerToast(label, 'success')
  } catch {
    toastStore.triggerToast(
      languageStore.t('امکان کپی خودکار نبود', 'Unable to copy automatically'),
      'info'
    )
  }
}

const downloadQrSvg = () => {
  const url = sessionShareUrl.value
  const code = handoverSession.value?.shortCode
  if (!url || !code) return
  try {
    const svg = generateQrSvgString(url, 3)
    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
    const objUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objUrl
    link.download = `tafakor-${code}.svg`
    link.click()
    URL.revokeObjectURL(objUrl)
  } catch {
    toastStore.triggerToast(
      languageStore.t('دانلود QR با خطا مواجه شد', 'Failed to download QR SVG'),
      'error'
    )
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px] max-h-[90vh] overflow-y-auto no-scrollbar bg-card border-border/60 rounded-3xl">
      <DialogHeader class="text-start">
        <DialogTitle class="text-base font-extrabold text-foreground flex items-center gap-2">
          <HandHeartIcon class="size-5 text-primary shrink-0" />
          <span>{{ languageStore.t('اهدای حضوری کتاب', 'In-Person Book Handover') }}</span>
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground leading-relaxed">
          {{
            languageStore.t(
              'کتاب را مستقیم به همراه دیگر در تفاخر تحویل دهید یا کتاب دریافتی را در قفسه خود ثبت کنید.',
              'Pass a book directly to another Tafakor reader or confirm receiving one.'
            )
          }}
        </DialogDescription>
      </DialogHeader>

      <!-- Clean 2-Option Segmented Bar (hidden when handover completed/in-step2 lock unless user backs out) -->
      <div
        v-if="!handoverSession"
        class="grid grid-cols-2 gap-1.5 p-1 rounded-2xl bg-muted/50 border border-border/50"
      >
        <Button
          type="button"
          size="sm"
          :variant="activeMode === 'donate' ? 'default' : 'ghost'"
          class="rounded-xl text-xs font-bold h-8"
          @click="activeMode = 'donate'"
        >
          <HandHeartIcon data-icon="inline-start" class="size-3.5" />
          <span>{{ languageStore.t('اهدا می‌کنم', 'Donate a Book') }}</span>
        </Button>
        <Button
          type="button"
          size="sm"
          :variant="activeMode === 'receive' ? 'default' : 'ghost'"
          class="rounded-xl text-xs font-bold h-8"
          @click="activeMode = 'receive'"
        >
          <QrCodeIcon data-icon="inline-start" class="size-3.5" />
          <span>{{ languageStore.t('تحویل گرفتم', 'Claim Book') }}</span>
        </Button>
      </div>

      <!-- TAB 2: RECEIVE / CLAIM BOOK -->
      <template v-if="activeMode === 'receive' && !handoverSession">
        <div
          v-if="!hasAuthSession"
          class="rounded-2xl border border-primary/30 bg-primary/5 p-5 flex flex-col items-center text-center gap-3 my-1"
        >
          <div class="size-11 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
            <LogInIcon class="size-5" />
          </div>
          <div class="flex flex-col gap-1 max-w-xs">
            <span class="text-xs font-extrabold text-foreground">
              {{ languageStore.t('ورود به تفاخر الزامی است', 'Sign in required') }}
            </span>
            <span class="text-[11px] text-muted-foreground leading-relaxed">
              {{
                languageStore.t(
                  'برای دریافت حضوری و ثبت کتاب در قفسه، ابتدا وارد حساب تفاخر خود شوید.',
                  'Sign in with your phone to confirm receiving a book onto your shelf.'
                )
              }}
            </span>
          </div>
          <Button type="button" size="sm" @click="userStore.isLoginModalOpen = true">
            <LogInIcon data-icon="inline-start" />
            <span>{{ languageStore.t('ورود سریع با شماره تلفن', 'Sign In with Phone') }}</span>
          </Button>
        </div>

        <div v-else class="flex flex-col gap-3 py-1">
          <!-- Receive Success Screen -->
          <div
            v-if="receiveCompletedTitle"
            class="rounded-3xl border border-border/70 bg-muted/40 p-5 flex flex-col items-center text-center gap-3"
          >
            <CheckCircle2Icon class="size-9 text-primary" />
            <div class="flex flex-col gap-1">
              <span class="text-sm font-extrabold text-foreground">
                {{ languageStore.t('تحویل با موفقیت ثبت شد!', 'Book Received!') }}
              </span>
              <span class="text-xs text-muted-foreground">
                «{{ receiveCompletedTitle }}» {{ languageStore.t('به قفسه شما منتقل گردید.', 'added to your shelf.') }}
              </span>
            </div>
          </div>

          <template v-else>
            <!-- Incoming handovers sent directly to this user's phone -->
            <div
              v-if="isLoadingIncoming"
              class="rounded-2xl border border-border/50 bg-muted/20 p-3 flex items-center gap-2 text-xs text-muted-foreground"
            >
              <Loader2Icon class="size-4 animate-spin" />
              <span>{{ languageStore.t('بررسی کتاب‌های ارسالی برای شما...', 'Checking incoming books...') }}</span>
            </div>

            <div
              v-else-if="incomingTransfers.length > 0"
              class="rounded-2xl border border-primary/35 bg-primary/5 p-3 flex flex-col gap-2.5"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs font-extrabold text-primary">
                  {{ languageStore.t('کتاب در انتظار تایید شما', 'Incoming Handover for You') }}
                </span>
                <Button type="button" size="icon-xs" variant="ghost" @click="loadIncoming">
                  <RefreshCwIcon class="size-3.5" />
                </Button>
              </div>
              <div
                v-for="trf in incomingTransfers"
                :key="trf.id"
                class="rounded-2xl bg-background/85 border border-border/60 p-3 flex flex-col gap-2"
              >
                <div class="flex items-start justify-between gap-2">
                  <div class="flex flex-col gap-0.5 min-w-0">
                    <span class="text-xs font-extrabold text-foreground truncate">
                      {{ trf.book_title_name }}
                    </span>
                    <span class="text-[11px] text-muted-foreground">
                      {{ languageStore.t('از طرف:', 'From:') }} {{ trf.from_user_name }}
                      · {{ languageStore.n(trf.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}
                    </span>
                  </div>
                  <Badge variant="outline" class="font-mono text-[10px] shrink-0" dir="ltr">
                    {{ trf.copy_short_code }}
                  </Badge>
                </div>
                <p v-if="trf.donor_note" class="text-[11px] text-muted-foreground bg-muted/35 rounded-xl px-2.5 py-1.5">
                  «{{ trf.donor_note }}»
                </p>
                <Button
                  type="button"
                  size="sm"
                  class="w-full rounded-xl"
                  :disabled="isCompletingReceive"
                  @click="handleConfirmIncomingTransfer(trf)"
                >
                  <Loader2Icon v-if="isCompletingReceive" data-icon="inline-start" class="animate-spin" />
                  <CheckCircle2Icon v-else data-icon="inline-start" />
                  <span>{{ languageStore.t('تایید دریافت کتاب', 'Confirm Receipt') }}</span>
                </Button>
              </div>
            </div>

            <!-- Lookup by Book Short Code (or pasted URL) -->
            <div class="rounded-2xl border border-border/60 bg-muted/25 p-3.5 flex flex-col gap-2.5">
              <span class="text-xs font-bold text-foreground">
                {{ languageStore.t('دریافت با کد کتاب یا اسکن QR', 'Enter Book Code') }}
              </span>
              <div class="flex items-center gap-2">
                <Input
                  v-model="receiveCodeInput"
                  dir="ltr"
                  class="h-10 font-mono text-center text-sm uppercase tracking-wider rounded-2xl bg-background/80"
                  :placeholder="languageStore.t('مثلاً: TK-U65P', 'e.g. TK-U65P')"
                  @keyup.enter="handleInspectReceiveCode"
                />
                <Button
                  type="button"
                  class="h-10 rounded-2xl shrink-0"
                  :disabled="isInspectingCode || !receiveCodeInput.trim()"
                  @click="handleInspectReceiveCode"
                >
                  <Loader2Icon v-if="isInspectingCode" data-icon="inline-start" class="animate-spin" />
                  <SearchIcon v-else data-icon="inline-start" />
                  <span>{{ languageStore.t('بررسی', 'Find') }}</span>
                </Button>
              </div>

              <!-- Inspected Copy Inside Tab 2 -->
              <div
                v-if="receiveInspect"
                class="rounded-2xl border border-border/60 bg-background/90 p-3 flex flex-col gap-2.5 mt-1"
              >
                <div class="flex items-center justify-between gap-2">
                  <div class="min-w-0">
                    <div class="text-xs font-extrabold text-foreground truncate">
                      {{ receiveInspect.book_title.title }}
                    </div>
                    <div class="text-[11px] text-muted-foreground truncate">
                      {{ receiveInspect.book_title.author }}
                    </div>
                  </div>
                  <Badge variant="secondary" class="text-[10.5px] shrink-0">
                    {{ languageStore.n(receiveInspect.available_quantity ?? 1) }}
                    {{ languageStore.t('جلد', 'copies') }}
                  </Badge>
                </div>

                <div v-if="receiveInspect.is_holder" class="text-xs text-amber-700 dark:text-amber-400 font-semibold">
                  {{ languageStore.t('این کتاب هم‌اکنون در قفسه خودتان است.', 'You already hold this book.') }}
                </div>

                <div
                  v-else-if="receiveInspect.active_transfer?.status === 'pending_donor'"
                  class="rounded-xl border border-primary/30 bg-primary/5 p-2.5 flex flex-col gap-2"
                >
                  <span class="text-xs font-bold text-foreground">
                    {{ languageStore.t('درخواست شما ثبت شد — اهداکننده روی گوشی خود تایید بزند.', 'Claim sent — waiting for donor confirmation.') }}
                  </span>
                  <Button type="button" size="xs" variant="outline" class="self-start" @click="handleInspectReceiveCode">
                    <RefreshCwIcon data-icon="inline-start" />
                    <span>{{ languageStore.t('بررسی مجدد', 'Refresh') }}</span>
                  </Button>
                </div>

                <template v-else-if="receiveInspect.can_claim">
                  <div
                    v-if="receiveInspect.active_transfer?.method === 'otp_fallback' && receiveInspect.active_transfer.status === 'pending_recipient'"
                    class="flex flex-col gap-2"
                  >
                    <Input
                      v-model="receiveNote"
                      class="h-9 text-xs rounded-xl"
                      :placeholder="languageStore.t('یادداشت کوتاه (اختیاری)', 'Optional note')"
                    />
                    <div class="flex items-center gap-2">
                      <Input
                        v-model="receiveOtpInput"
                        dir="ltr"
                        maxlength="6"
                        inputmode="numeric"
                        class="h-10 font-mono text-center text-base font-black tracking-widest rounded-xl"
                        :placeholder="languageStore.t('کد ۴ رقمی', '4-digit code')"
                        @keyup.enter="handleVerifyReceiveOtp"
                      />
                      <Button
                        type="button"
                        class="h-10 rounded-xl shrink-0"
                        :disabled="isCompletingReceive || !receiveOtpInput.trim()"
                        @click="handleVerifyReceiveOtp"
                      >
                        <Loader2Icon v-if="isCompletingReceive" data-icon="inline-start" class="animate-spin" />
                        <span>{{ languageStore.t('تایید دریافت', 'Verify & Claim') }}</span>
                      </Button>
                    </div>
                    <button
                      type="button"
                      class="text-[11px] text-primary hover:underline self-start pt-0.5 cursor-pointer"
                      @click="handleClaimReceiveCode"
                    >
                      {{ languageStore.t('کد ۴ رقمی ندارم؟ ارسال درخواست تایید روی گوشی اهداکننده', 'No code? Send 1-tap claim to donor') }}
                    </button>
                  </div>

                  <div v-else class="flex flex-col gap-2">
                    <QuantityStepper
                      v-if="(receiveInspect.available_quantity ?? 1) > 1"
                      v-model="receiveQty"
                      :min="1"
                      :max="Math.max(1, receiveInspect.available_quantity ?? 1)"
                      :label="languageStore.t('تعداد جلد دریافتی', 'Quantity')"
                      compact
                    />
                    <Input
                      v-model="receiveNote"
                      class="h-9 text-xs rounded-xl"
                      :placeholder="languageStore.t('یادداشت کوتاه (اختیاری)', 'Optional note')"
                    />
                    <Button
                      type="button"
                      class="w-full rounded-xl"
                      :disabled="isCompletingReceive"
                      @click="handleClaimReceiveCode"
                    >
                      <Loader2Icon v-if="isCompletingReceive" data-icon="inline-start" class="animate-spin" />
                      <CheckCircle2Icon v-else data-icon="inline-start" />
                      <span>{{ languageStore.t('درخواست تحویل حضوری', 'Claim In-Person') }}</span>
                    </Button>
                  </div>
                </template>
              </div>
            </div>
          </template>

          <div
            v-if="receiveError"
            class="rounded-2xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive font-semibold"
          >
            {{ receiveError }}
          </div>
        </div>

        <DialogFooter class="sm:justify-start">
          <Button type="button" variant="outline" @click="emit('update:open', false)">
            {{ languageStore.t('بستن', 'Close') }}
          </Button>
        </DialogFooter>
      </template>

      <!-- TAB 1 - STEP 2: UNIFIED HANDOVER SESSION (QR OR CODE + SMALL PHONE OPTION, ALL IN ONE DIALOG) -->
      <template v-else-if="handoverSession">
        <!-- Completed Celebration -->
        <div
          v-if="handoverCompleted"
          class="rounded-3xl border border-border/70 bg-muted/40 p-6 flex flex-col items-center text-center gap-3 my-1"
        >
          <CheckCircle2Icon class="size-10 text-primary" />
          <div class="flex flex-col gap-1">
            <span class="text-sm font-extrabold text-foreground">
              {{ languageStore.t('کتاب با موفقیت تحویل داده شد!', 'Book Handover Completed!') }}
            </span>
            <span class="text-xs text-muted-foreground leading-relaxed">
              {{
                languageStore.t(
                  `«${handoverSession.book.book_title.title}» (${languageStore.n(handoverSession.quantity)} جلد) به قفسه گیرنده منتقل شد.`,
                  `${handoverSession.quantity} copies transferred to recipient's shelf.`
                )
              }}
            </span>
          </div>
          <DialogFooter class="w-full pt-2 sm:justify-center">
            <Button type="button" class="rounded-2xl px-6" @click="emit('update:open', false)">
              {{ languageStore.t('بستن', 'Done') }}
            </Button>
          </DialogFooter>
        </div>

        <template v-else>
          <div class="flex flex-col gap-3 py-1">
            <!-- Selected Book + Back Button -->
            <div class="rounded-2xl border border-border/60 bg-muted/25 px-3 py-2.5 flex items-center justify-between gap-2">
              <div class="flex items-center gap-2.5 min-w-0">
                <div class="w-9 h-12 rounded-xl overflow-hidden bg-muted/60 border border-border/50 flex items-center justify-center shrink-0">
                  <img
                    v-if="resolveMediaUrl(handoverSession.book.book_title.cover_image)"
                    :src="resolveMediaUrl(handoverSession.book.book_title.cover_image)!"
                    :alt="handoverSession.book.book_title.title"
                    class="size-full object-cover"
                  />
                  <BookOpenIcon v-else class="size-4 text-muted-foreground" />
                </div>
                <div class="flex flex-col min-w-0">
                  <span class="text-xs font-extrabold text-foreground truncate">
                    {{ handoverSession.book.book_title.title }}
                  </span>
                  <span class="text-[11px] text-primary font-bold">
                    {{ languageStore.n(handoverSession.quantity) }} {{ languageStore.t('جلد آماده تحویل', 'copies ready') }}
                  </span>
                </div>
              </div>
              <Button type="button" size="xs" variant="ghost" @click="handleBackToSelect">
                {{ languageStore.t('تغییر', 'Back') }}
              </Button>
            </div>

            <!-- Live Incoming Claim Prompt (when recipient scanned/entered code) -->
            <div
              v-if="activeInspect?.active_transfer?.status === 'pending_donor'"
              class="rounded-3xl border border-primary/40 bg-primary/8 p-4 flex flex-col gap-3"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs font-extrabold text-foreground">
                  {{ languageStore.t('گیرنده درخواست دریافت ثبت کرد — آماده تایید نهایی:', 'Recipient submitted claim — confirm handover:') }}
                </span>
                <Button type="button" size="icon-xs" variant="ghost" @click="pollHandoverStatus">
                  <RefreshCwIcon class="size-3.5" />
                </Button>
              </div>
              <p
                v-if="activeInspect.active_transfer.recipient_note"
                class="text-[11px] rounded-xl bg-background/85 px-2.5 py-1.5 text-muted-foreground"
              >
                «{{ activeInspect.active_transfer.recipient_note }}»
              </p>
              <Button type="button" class="w-full rounded-2xl" :disabled="isSubmitting" @click="handleConfirmPendingClaim">
                <Loader2Icon v-if="isSubmitting" data-icon="inline-start" class="animate-spin" />
                <CheckCircle2Icon v-else data-icon="inline-start" />
                <span>{{ languageStore.t('تایید و انتقال نهایی کتاب', 'Confirm Final Transfer') }}</span>
              </Button>
            </div>

            <!-- Assigned to Phone Status -->
            <div
              v-else-if="handoverSession.assignedPhone"
              class="rounded-3xl border border-primary/35 bg-primary/5 p-4 flex flex-col gap-2.5"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs font-extrabold text-foreground">
                  {{ languageStore.t('درخواست تحویل ارسال شد', 'Handover Request Sent') }}
                </span>
                <Button type="button" size="icon-xs" variant="ghost" @click="pollHandoverStatus">
                  <RefreshCwIcon class="size-3.5" />
                </Button>
              </div>
              <p class="text-xs text-muted-foreground leading-relaxed">
                {{
                  languageStore.t(
                    `برای شماره ${handoverSession.assignedPhone} ثبت شد. گیرنده کافی است در تفاخر وارد بخش «تحویل گرفتم» شده و دریافت را تایید کند.`,
                    `Sent to ${handoverSession.assignedPhone}. Recipient can confirm with 1 tap inside "Claim Book".`
                  )
                }}
              </p>
            </div>

            <!-- Primary Dual View: Method 1 (QR) — یا — Method 2 (Code) -->
            <div v-else class="flex flex-col gap-3">
              <!-- Method 1: Scan QR Code -->
              <div class="rounded-3xl border border-border/60 bg-background p-4 flex flex-col items-center gap-2.5">
                <span class="text-xs font-extrabold text-foreground">
                  {{ languageStore.t('اسکن QR Code توسط گیرنده', 'Scan QR Code with Recipient Phone') }}
                </span>
                <div
                  v-if="sessionQrDataUrl"
                  class="size-40 rounded-2xl bg-white p-2 border border-border/60 shadow-xs flex items-center justify-center"
                >
                  <img :src="sessionQrDataUrl" :alt="handoverSession.shortCode" class="size-full object-contain" />
                </div>
                <div class="flex items-center justify-center gap-1.5 flex-wrap">
                  <Button
                    type="button"
                    size="xs"
                    variant="outline"
                    class="rounded-xl"
                    @click="copyText(sessionShareUrl, languageStore.t('لینک QR کپی شد', 'QR link copied'))"
                  >
                    <CopyIcon data-icon="inline-start" />
                    <span>{{ languageStore.t('کپی لینک', 'Copy Link') }}</span>
                  </Button>
                  <Button
                    type="button"
                    size="xs"
                    variant="outline"
                    class="rounded-xl"
                    @click="downloadQrSvg"
                  >
                    <DownloadIcon data-icon="inline-start" />
                    <span>{{ languageStore.t('ذخیره QR', 'Save QR') }}</span>
                  </Button>
                </div>
              </div>

              <!-- Clear "OR / یا" Divider -->
              <div class="flex items-center gap-3 px-2">
                <div class="h-px flex-1 bg-border/70" />
                <span class="text-xs font-extrabold text-muted-foreground px-2">
                  {{ languageStore.t('یا', 'OR') }}
                </span>
                <div class="h-px flex-1 bg-border/70" />
              </div>

              <!-- Method 2: Book Code + 4-Digit Handover Code -->
              <div class="rounded-3xl border border-border/60 bg-muted/20 p-3.5 flex flex-col gap-2.5">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
                    <KeyRoundIcon class="size-3.5 text-primary" />
                    <span>{{ languageStore.t('تحویل با کد (در بخش «تحویل گرفتم»)', 'Handover Codes') }}</span>
                  </span>
                </div>

                <div class="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    class="rounded-2xl border border-border/60 bg-background px-3 py-2 flex flex-col items-center gap-0.5 hover:border-primary/40 transition-colors cursor-pointer"
                    @click="copyText(handoverSession.shortCode, languageStore.t('شناسه کتاب کپی شد', 'Book code copied'))"
                  >
                    <span class="text-[10px] text-muted-foreground">
                      {{ languageStore.t('شناسه کتاب', 'Book Code') }}
                    </span>
                    <span dir="ltr" class="font-mono text-sm font-black text-foreground tracking-wider">
                      {{ handoverSession.shortCode }}
                    </span>
                  </button>

                  <button
                    type="button"
                    class="rounded-2xl border border-primary/35 bg-primary/5 px-3 py-2 flex flex-col items-center gap-0.5 hover:border-primary/60 transition-colors cursor-pointer"
                    @click="copyText(handoverSession.otpCode, languageStore.t('کد ۴ رقمی کپی شد', '4-digit code copied'))"
                  >
                    <span class="text-[10px] text-muted-foreground">
                      {{ languageStore.t('کد ۴ رقمی تحویل', '4-Digit Code') }}
                    </span>
                    <span dir="ltr" class="font-mono text-base font-black text-primary tracking-widest">
                      {{ handoverSession.otpCode || '—' }}
                    </span>
                  </button>
                </div>
              </div>

              <!-- Subtle Collapsed Secondary Option: Recipient Phone (Out of Main View) -->
              <div class="flex flex-col gap-2 pt-1">
                <button
                  type="button"
                  class="self-center inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                  @click="isPhoneOptionOpen = !isPhoneOptionOpen"
                >
                  <SmartphoneIcon class="size-3" />
                  <span>{{ languageStore.t('ارسال مستقیم با شماره موبایل گیرنده', 'Or assign by recipient phone') }}</span>
                  <ChevronDownIcon class="size-3 transition-transform" :class="{ 'rotate-180': isPhoneOptionOpen }" />
                </button>

                <div
                  v-if="isPhoneOptionOpen"
                  class="rounded-2xl border border-border/60 bg-muted/20 p-2.5 flex flex-col gap-2"
                >
                  <div class="flex items-center gap-2">
                    <Input
                      v-model="recipientPhoneInput"
                      dir="ltr"
                      inputmode="tel"
                      class="h-8 text-xs font-mono rounded-xl bg-background/85"
                      :placeholder="languageStore.t('شماره موبایل کاربر تفاخر (09...)', 'Tafakor phone (09...)')"
                      @keyup.enter="handleSendToPhone"
                    />
                    <Button
                      type="button"
                      size="xs"
                      class="h-8 rounded-xl shrink-0"
                      :disabled="isSendingPhone || !recipientPhoneInput.trim()"
                      @click="handleSendToPhone"
                    >
                      <Loader2Icon v-if="isSendingPhone" data-icon="inline-start" class="animate-spin" />
                      <span>{{ languageStore.t('ارسال', 'Send') }}</span>
                    </Button>
                  </div>
                  <span v-if="phoneError" class="text-[11px] text-destructive font-semibold">
                    {{ phoneError }}
                  </span>
                </div>
              </div>
            </div>

            <div
              v-if="formError"
              class="rounded-2xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive font-semibold"
            >
              {{ formError }}
            </div>
          </div>

          <DialogFooter class="gap-2 sm:justify-start">
            <Button type="button" variant="outline" @click="emit('update:open', false)">
              {{ languageStore.t('بستن', 'Close') }}
            </Button>
          </DialogFooter>
        </template>
      </template>

      <!-- TAB 1 - STEP 1: PICK BOOK FROM PERSONAL SHELF & QUANTITY -->
      <template v-else>
        <!-- Guest Login Prompt -->
        <div
          v-if="!hasAuthSession"
          class="rounded-2xl border border-primary/30 bg-primary/5 p-5 flex flex-col items-center text-center gap-3 my-1"
        >
          <div class="size-11 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
            <LogInIcon class="size-5" />
          </div>
          <div class="flex flex-col gap-1 max-w-xs">
            <span class="text-xs font-extrabold text-foreground">
              {{ languageStore.t('ابتدا وارد حساب تفاخر شوید', 'Sign in to access your shelf') }}
            </span>
            <span class="text-[11px] text-muted-foreground leading-relaxed">
              {{
                languageStore.t(
                  'برای انتخاب کتاب از قفسه شخصی یا ثبت کتاب جدید و تحویل حضوری وارد شوید.',
                  'Sign in with OTP to pick or register a book from your shelf for handover.'
                )
              }}
            </span>
          </div>
          <Button type="button" size="sm" @click="userStore.isLoginModalOpen = true">
            <LogInIcon data-icon="inline-start" />
            <span>{{ languageStore.t('ورود سریع با شماره تلفن', 'Sign In with Phone') }}</span>
          </Button>
        </div>

        <template v-else>
          <div class="flex flex-col gap-3.5 py-1">
            <!-- Step 1 Header + Compact "+ Register New Book" Button -->
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-1.5">
                <span class="size-5 rounded-full bg-primary text-primary-foreground text-[11px] font-extrabold flex items-center justify-center shrink-0">
                  {{ languageStore.isFa ? '۱' : '1' }}
                </span>
                <span class="text-xs font-extrabold text-foreground">
                  {{ languageStore.t('انتخاب کتاب از قفسه شما', 'Select a Book from Your Shelf') }}
                </span>
              </div>
              <Button
                type="button"
                size="xs"
                variant="outline"
                class="rounded-full shrink-0"
                @click="isAddShelfBookOpen = true"
              >
                <PlusIcon data-icon="inline-start" />
                <span>{{ languageStore.t('ثبت کتاب جدید', 'Register New Book') }}</span>
              </Button>
            </div>

            <!-- Quick Search when user has multiple books -->
            <div v-if="shelfBooks.length > 3" class="relative">
              <SearchIcon class="size-3.5 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3 pointer-events-none" />
              <Input
                v-model="searchQuery"
                class="ps-8 h-9 text-xs rounded-2xl"
                :placeholder="languageStore.t('جستجو در کتاب‌های قفسه من...', 'Search your shelf...')"
              />
            </div>

            <!-- Loading Skeleton -->
            <div v-if="isLoadingBooks" class="flex flex-col gap-2">
              <Skeleton v-for="n in 2" :key="n" class="h-16 w-full rounded-2xl" />
            </div>

            <!-- Empty Shelf -->
            <div
              v-else-if="shelfBooks.length === 0"
              class="rounded-2xl border border-dashed border-border/70 bg-muted/20 p-5 flex flex-col items-center text-center gap-2.5"
            >
              <div class="size-10 rounded-2xl bg-muted flex items-center justify-center text-muted-foreground">
                <BookOpenIcon class="size-5" />
              </div>
              <p class="text-xs text-muted-foreground leading-relaxed max-w-xs">
                {{
                  languageStore.t(
                    'قفسه شما خالی است. با زدن «ثبت کتاب جدید» کتاب را وارد قفسه کنید و بلافاصله تحویل دهید.',
                    'Your shelf is empty. Register your book and hand it over right away.'
                  )
                }}
              </p>
              <Button type="button" size="xs" @click="isAddShelfBookOpen = true">
                <PlusIcon data-icon="inline-start" />
                <span>{{ languageStore.t('ثبت کتاب جدید', 'Register New Book') }}</span>
              </Button>
            </div>

            <!-- Filtered Empty -->
            <div
              v-else-if="filteredBooks.length === 0"
              class="rounded-2xl border border-border/50 bg-muted/20 px-4 py-4 text-center text-xs text-muted-foreground"
            >
              {{ languageStore.t('کتابی با این عنوان پیدا نشد.', 'No matching book found.') }}
            </div>

            <!-- Shelf Selector List -->
            <div v-else class="flex flex-col gap-2 max-h-56 overflow-y-auto no-scrollbar">
              <div
                v-for="book in filteredBooks"
                :key="book.id"
                role="button"
                :tabindex="isSelectableForDonation(book) ? 0 : -1"
                @click="handleCardClick(book)"
                @keydown.enter.prevent="handleCardClick(book)"
                class="rounded-2xl border p-2.5 flex items-center gap-2.5 transition-all text-start"
                :class="[
                  selectedBookId === book.id
                    ? 'border-primary bg-primary/5 shadow-xs'
                    : isSelectableForDonation(book)
                      ? 'border-border/60 bg-background/70 hover:border-primary/40 cursor-pointer'
                      : 'border-border/40 bg-muted/25 opacity-60 cursor-not-allowed',
                ]"
              >
                <div class="w-10 h-13 rounded-xl overflow-hidden bg-muted/60 border border-border/50 flex items-center justify-center shrink-0">
                  <img
                    v-if="resolveMediaUrl(book.book_title.cover_image)"
                    :src="resolveMediaUrl(book.book_title.cover_image)!"
                    :alt="book.book_title.title"
                    class="size-full object-cover"
                  />
                  <BookOpenIcon v-else class="size-4 text-muted-foreground" />
                </div>

                <div class="flex-1 min-w-0 flex flex-col gap-0.5">
                  <span class="text-xs font-extrabold text-foreground truncate">
                    {{ book.book_title.title }}
                  </span>
                  <span class="text-[11px] text-muted-foreground truncate">
                    {{ book.book_title.author }}
                  </span>
                  <div class="flex items-center gap-1.5 flex-wrap pt-0.5">
                    <Badge variant="outline" class="text-[10px] px-1.5 py-0">
                      {{ getBookStatusLabel(book) }}
                    </Badge>
                    <Badge
                      :variant="(book.quantity ?? 1) > 0 ? 'secondary' : 'outline'"
                      class="text-[10px] px-1.5 py-0"
                    >
                      {{ languageStore.n(book.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}
                    </Badge>
                    <Badge v-if="book.condition_display" variant="ghost" class="text-[10px] px-1.5 py-0">
                      {{ book.condition_display }}
                    </Badge>
                  </div>
                </div>

                <div
                  v-if="selectedBookId === book.id"
                  class="size-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0"
                >
                  <CheckCircle2Icon class="size-3.5" />
                </div>
              </div>
            </div>

            <!-- Quantity & Optional Note -->
            <div v-if="selectedBook" class="rounded-2xl border border-primary/30 bg-primary/5 p-3 flex flex-col gap-2.5">
              <div class="flex items-center gap-2">
                <UserCheckIcon class="size-4 text-primary shrink-0" />
                <span class="text-xs font-extrabold text-foreground">
                  {{ languageStore.t('انتقال حضوری به کاربر تفاخر', 'Direct Transfer to a Tafakor Reader') }}
                </span>
              </div>

              <QuantityStepper
                v-model="donationQuantity"
                :min="1"
                :max="maxDonationQty"
                :label="languageStore.t('تعداد جلد برای اهدا', 'Quantity to Hand Over')"
                :hint="languageStore.t(`موجودی قفسه: ${languageStore.n(maxDonationQty)} جلد`, `In shelf: ${maxDonationQty}`)"
                compact
              />

              <Input
                v-model="donationNote"
                class="h-9 text-xs bg-background/80 rounded-xl"
                :placeholder="
                  languageStore.t(
                    'یادداشت کوتاه برای خواننده بعدی (اختیاری)...',
                    'Short note for the next reader (optional)...'
                  )
                "
              />
            </div>

            <div
              v-if="formError"
              class="rounded-2xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive font-semibold"
            >
              {{ formError }}
            </div>
          </div>

          <DialogFooter class="gap-2 sm:justify-start">
            <Button
              type="button"
              :disabled="isSubmitting || !selectedBook"
              @click="handleProceedToHandover"
            >
              <Loader2Icon v-if="isSubmitting" data-icon="inline-start" class="animate-spin" />
              <QrCodeIcon v-else data-icon="inline-start" />
              <span>
                {{ languageStore.t('ادامه و دریافت کد تحویل', 'Continue to Handover') }}
              </span>
            </Button>
            <Button type="button" variant="outline" :disabled="isSubmitting" @click="emit('update:open', false)">
              {{ languageStore.t('انصراف', 'Cancel') }}
            </Button>
          </DialogFooter>
        </template>
      </template>
    </DialogContent>
  </Dialog>

  <!-- Quick Personal Shelf Book Registration Sub-Dialog -->
  <AddShelfBookDialog
    v-model:open="isAddShelfBookOpen"
    shelf-only
    quick-physical
    default-intent="keeping"
    @saved="handleNewBookAdded"
  />
</template>
