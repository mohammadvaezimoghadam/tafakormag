<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import {
  cancelBookHandover,
  claimBookCopy,
  confirmBookHandover,
  depositBookToStation,
  extractApiErrorMessage,
  getBookCopyJourney,
  initiateBookHandover,
  inspectBookCopy,
  listBookStations,
  pickupBookFromStation,
  submitDonationRequest,
} from '@/api/shelf'
import type {
  BookCopyInspectResult,
  BookCopyJourneyResult,
  BookStationSummary,
  DonationMethod,
  HomeMarketplaceItem,
} from '@/types/shelf'
import { generateQrDataUrl } from '@/utils/qrCode'
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
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  BookOpenIcon,
  CheckCircle2Icon,
  CopyIcon,
  HandHeartIcon,
  KeyRoundIcon,
  Loader2Icon,
  LogInIcon,
  MapPinIcon,
  PackageIcon,
  QrCodeIcon,
  RefreshCwIcon,
  SearchIcon,
  SendIcon,
  SmartphoneIcon,
  XCircleIcon,
} from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    item?: HomeMarketplaceItem | null
    initialShortCode?: string
    initialOtp?: string
    codeLookupMode?: boolean
    inPersonOnly?: boolean
  }>(),
  {
    item: null,
    initialShortCode: '',
    initialOtp: '',
    codeLookupMode: false,
    inPersonOnly: false,
  }
)

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'changed'): void
}>()

const languageStore = useLanguageStore()
const userStore = useUserStore()
const toastStore = useToastStore()

const codeInput = ref('')
const isLoadingCopy = ref(false)
const copyInspect = ref<BookCopyInspectResult | null>(null)
const copyJourney = ref<BookCopyJourneyResult | null>(null)
const copyError = ref('')

const stations = ref<BookStationSummary[]>([])
const selectedStationId = ref('__none__')
const generatedOtp = ref('')
const otpInput = ref('')
const donorNote = ref('')
const recipientNote = ref('')
const handoverQty = ref(1)
const requestMessage = ref('')
const requestSubmitted = ref(false)
const handoverSuccess = ref(false)

const isSubmittingAction = ref(false)

const maxHandoverQty = computed(() => Math.max(1, copyInspect.value?.available_quantity ?? 1))

const isAuthenticated = computed(
  () =>
    userStore.isAuthenticated ||
    Boolean(
      (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('auth_token')) ||
        (typeof localStorage !== 'undefined' && localStorage.getItem('auth_token'))
    )
)

const shareQrUrl = computed(() => {
  const code = copyInspect.value?.short_code?.trim()
  if (!code) return ''
  const origin =
    typeof window !== 'undefined' && window.location?.origin
      ? window.location.origin
      : 'https://tafakormag.ir'
  return `${origin}/b/${code}`
})

const qrImageUrl = computed(() => {
  if (!shareQrUrl.value) return ''
  try {
    return generateQrDataUrl(shareQrUrl.value, 2)
  } catch {
    return ''
  }
})

const activeShortCode = computed(() => {
  return (
    props.initialShortCode ||
    props.item?.physical_copy_summary?.short_code ||
    ''
  ).trim()
})

const effectiveMethods = computed<DonationMethod[]>(() => {
  if (!props.item) return []
  if (props.item.donation_methods?.length) return props.item.donation_methods
  if (props.item.delivery_type === 'digital') return ['digital']
  if (props.item.station_summary) return ['station']
  if (props.item.physical_copy_summary) return ['in_person']
  return ['postal']
})

const supportsRequestFlow = computed(() =>
  Boolean(
    !props.inPersonOnly &&
      props.item &&
      (effectiveMethods.value.includes('postal') ||
        effectiveMethods.value.includes('digital') ||
        (effectiveMethods.value.includes('station') && !copyInspect.value))
  )
)

const isOwnListing = computed(() => {
  if (!props.item?.seller || !userStore.userProfile?.id) return false
  return Number(props.item.seller) === Number(userStore.userProfile.id)
})

const methodMeta = (method: DonationMethod) => {
  switch (method) {
    case 'in_person':
      return {
        label: languageStore.t('اهدای حضوری (کد QR)', 'In-Person (QR)'),
        icon: QrCodeIcon,
      }
    case 'postal':
      return {
        label: languageStore.t('ارسال پستی', 'Postal'),
        icon: PackageIcon,
      }
    case 'station':
      return {
        label: languageStore.t('ایستگاه تفاخر', 'Book Station'),
        icon: MapPinIcon,
      }
    case 'digital':
    default:
      return {
        label: languageStore.t('نسخه دیجیتال', 'Digital Copy'),
        icon: SmartphoneIcon,
      }
  }
}

const loadCopyData = async (rawCode: string) => {
  const code = rawCode.trim()
  if (!code) {
    copyInspect.value = null
    copyJourney.value = null
    return
  }
  isLoadingCopy.value = true
  copyError.value = ''
  try {
    const inspected = await inspectBookCopy(code)
    copyInspect.value = inspected
    const maxAvail = Math.max(1, inspected.available_quantity ?? 1)
    const activeQty = inspected.active_transfer?.quantity
    handoverQty.value = activeQty ? Math.min(maxAvail, Math.max(1, activeQty)) : 1
    try {
      copyJourney.value = await getBookCopyJourney(inspected.short_code || code)
    } catch {
      copyJourney.value = null
    }
  } catch (err) {
    copyInspect.value = null
    copyJourney.value = null
    copyError.value = extractApiErrorMessage(
      err,
      languageStore.t('کد گردش یافت نشد', 'Book circulation code not found')
    )
  } finally {
    isLoadingCopy.value = false
  }
}

watch(
  () => [props.open, props.item, props.initialShortCode, props.initialOtp] as const,
  async ([open]) => {
    if (!open) return
    copyError.value = ''
    generatedOtp.value = ''
    otpInput.value = (props.initialOtp || '').trim()
    donorNote.value = ''
    recipientNote.value = ''
    handoverQty.value = 1
    requestMessage.value = ''
    requestSubmitted.value = false
    handoverSuccess.value = false
    selectedStationId.value = '__none__'
    codeInput.value = activeShortCode.value

    if (activeShortCode.value) {
      await loadCopyData(activeShortCode.value)
    } else {
      copyInspect.value = null
      copyJourney.value = null
    }

    if (!props.inPersonOnly && stations.value.length === 0) {
      try {
        stations.value = await listBookStations()
      } catch {
        stations.value = []
      }
    }
  },
  { immediate: true }
)

watch(isAuthenticated, async (authed) => {
  if (authed && props.open && copyInspect.value?.short_code) {
    await loadCopyData(copyInspect.value.short_code)
  }
})

const copyShortText = async (text: string, msg: string) => {
  try {
    await navigator.clipboard.writeText(text)
    toastStore.triggerToast(msg, 'success')
  } catch {
    toastStore.triggerToast(languageStore.t('امکان کپی خودکار نبود', 'Unable to copy'), 'info')
  }
}

const openLoginForHandover = () => {
  userStore.isLoginModalOpen = true
}

const handleInspectManualCode = async () => {
  if (!codeInput.value.trim()) return
  await loadCopyData(codeInput.value.trim())
}

const handleClaimInPerson = async () => {
  if (!copyInspect.value) return
  isSubmittingAction.value = true
  try {
    await claimBookCopy({
      short_code: copyInspect.value.short_code,
      quantity: Math.min(maxHandoverQty.value, Math.max(1, Math.floor(handoverQty.value || 1))),
      recipient_note: recipientNote.value.trim(),
    })
    toastStore.triggerToast(
      languageStore.t(
        'درخواست تحویل حضوری ثبت شد و برای اهداکننده ارسال گردید',
        'In-person claim sent to the holder'
      ),
      'success'
    )
    await loadCopyData(copyInspect.value.short_code)
    emit('changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در ثبت دریافت حضوری', 'Failed to claim copy')),
      'error'
    )
  } finally {
    isSubmittingAction.value = false
  }
}

const handlePickupStation = async () => {
  if (!copyInspect.value) return
  isSubmittingAction.value = true
  try {
    await pickupBookFromStation({
      short_code: copyInspect.value.short_code,
      recipient_note: recipientNote.value.trim(),
    })
    toastStore.triggerToast(
      languageStore.t('برداشت کتاب از ایستگاه تفاخر با موفقیت ثبت شد', 'Book picked up from station'),
      'success'
    )
    await loadCopyData(copyInspect.value.short_code)
    emit('changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در برداشت از ایستگاه', 'Station pickup failed')),
      'error'
    )
  } finally {
    isSubmittingAction.value = false
  }
}

const handleConfirmHandover = async (transferId: number, withOtp = false) => {
  isSubmittingAction.value = true
  try {
    await confirmBookHandover(transferId, {
      otp_code: withOtp ? otpInput.value.trim() : undefined,
      quantity: !withOtp
        ? Math.min(maxHandoverQty.value, Math.max(1, Math.floor(handoverQty.value || 1)))
        : undefined,
      donor_note: !withOtp ? donorNote.value.trim() : undefined,
      recipient_note: recipientNote.value.trim(),
    })
    handoverSuccess.value = true
    generatedOtp.value = ''
    otpInput.value = ''
    donorNote.value = ''
    recipientNote.value = ''
    toastStore.triggerToast(
      languageStore.t(
        'تحویل حضوری کتاب با موفقیت تایید و در سفرنامه و قفسه ثبت شد',
        'In-person handover confirmed and shelf updated'
      ),
      'success'
    )
    if (copyInspect.value) {
      await loadCopyData(copyInspect.value.short_code)
    }
    emit('changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در تایید انتقال', 'Handover confirmation failed')),
      'error'
    )
  } finally {
    isSubmittingAction.value = false
  }
}

const handleCancelTransfer = async (transferId: number) => {
  isSubmittingAction.value = true
  try {
    await cancelBookHandover(transferId)
    generatedOtp.value = ''
    toastStore.triggerToast(
      languageStore.t('درخواست انتقال لغو شد', 'Transfer cancelled'),
      'success'
    )
    if (copyInspect.value) {
      await loadCopyData(copyInspect.value.short_code)
    }
    emit('changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('لغو انتقال انجام نشد', 'Failed to cancel transfer')),
      'error'
    )
  } finally {
    isSubmittingAction.value = false
  }
}

const handleGenerateOtp = async () => {
  if (!copyInspect.value) return
  isSubmittingAction.value = true
  try {
    const trf = await initiateBookHandover({
      short_code: copyInspect.value.short_code,
      method: 'otp_fallback',
      quantity: Math.min(maxHandoverQty.value, Math.max(1, Math.floor(handoverQty.value || 1))),
      donor_note: donorNote.value.trim(),
    })
    generatedOtp.value = trf.otp_code || ''
    toastStore.triggerToast(
      languageStore.t('کد ۴ رقمی تحویل حضوری ایجاد شد', '4-digit handover OTP generated'),
      'success'
    )
    await loadCopyData(copyInspect.value.short_code)
    emit('changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در ساخت کد تحویل', 'Failed to generate OTP')),
      'error'
    )
  } finally {
    isSubmittingAction.value = false
  }
}

const handleDepositToStation = async () => {
  if (!copyInspect.value || selectedStationId.value === '__none__') return
  isSubmittingAction.value = true
  try {
    await depositBookToStation({
      short_code: copyInspect.value.short_code,
      station_id: Number(selectedStationId.value),
      donor_note: recipientNote.value.trim(),
    })
    toastStore.triggerToast(
      languageStore.t('کتاب در قفسه ایستگاه تفاخر ثبت شد', 'Book deposited to station'),
      'success'
    )
    await loadCopyData(copyInspect.value.short_code)
    emit('changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('خطا در تحویل به ایستگاه', 'Station deposit failed')),
      'error'
    )
  } finally {
    isSubmittingAction.value = false
  }
}

const handleSubmitRequest = async () => {
  if (!props.item) return
  isSubmittingAction.value = true
  try {
    await submitDonationRequest({
      item_id: props.item.id,
      message: requestMessage.value.trim(),
    })
    requestSubmitted.value = true
    toastStore.triggerToast(
      languageStore.t(
        'درخواست دریافت کتاب برای اهداکننده ارسال شد',
        'Donation request sent to the donor'
      ),
      'success'
    )
    emit('changed')
  } catch (err) {
    toastStore.triggerToast(
      extractApiErrorMessage(err, languageStore.t('ثبت درخواست انجام نشد', 'Failed to submit request')),
      'error'
    )
  } finally {
    isSubmittingAction.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px] max-h-[90vh] overflow-y-auto no-scrollbar bg-card border-border/60 rounded-3xl">
      <DialogHeader class="text-start">
        <DialogTitle class="text-base font-extrabold text-foreground">
          {{
            item
              ? item.title
              : copyInspect?.book_title.title || languageStore.t('تحویل و کد گردش کتاب', 'Book Handover & QR Code')
          }}
        </DialogTitle>
        <DialogDescription v-if="item || copyInspect" class="text-xs text-muted-foreground">
          {{ item?.author || copyInspect?.book_title.author || item?.seller_name }}
          <template v-if="item?.seller_name">
            · {{ languageStore.t('اهداکننده:', 'Donor:') }} {{ item.seller_name }}
          </template>
        </DialogDescription>
      </DialogHeader>

      <div class="flex flex-col gap-4 py-1">
        <!-- QR Short Code Manual Search Bar (when in lookup mode) -->
        <div v-if="codeLookupMode" class="flex items-center gap-2">
          <div class="relative flex-1">
            <QrCodeIcon class="size-4 text-muted-foreground absolute start-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <Input
              v-model="codeInput"
              dir="ltr"
              class="ps-9 rounded-2xl font-mono uppercase"
              :placeholder="languageStore.t('مثلاً: TK-U65P', 'e.g. TK-U65P')"
              @keyup.enter="handleInspectManualCode"
            />
          </div>
          <Button type="button" size="sm" :disabled="isLoadingCopy || !codeInput.trim()" @click="handleInspectManualCode">
            <SearchIcon data-icon="inline-start" />
            <span>{{ languageStore.t('بررسی کد', 'Inspect') }}</span>
          </Button>
        </div>

        <!-- Book Overview Card -->
        <div
          v-if="item"
          class="flex items-start gap-3 rounded-2xl border border-border/60 bg-muted/25 p-3"
        >
          <div class="w-14 h-20 rounded-xl overflow-hidden bg-muted/60 border border-border/50 flex items-center justify-center shrink-0">
            <img
              v-if="item.cover_image"
              :src="item.cover_image"
              :alt="item.title"
              class="size-full object-cover"
            />
            <BookOpenIcon v-else class="size-5 text-muted-foreground" />
          </div>

          <div class="flex-1 min-w-0 flex flex-col gap-1.5">
            <div class="flex items-center gap-1.5 flex-wrap">
              <Badge
                v-for="m in effectiveMethods"
                :key="m"
                variant="secondary"
                class="gap-1 text-[10.5px]"
              >
                <component :is="methodMeta(m).icon" class="size-3" />
                <span>{{ methodMeta(m).label }}</span>
              </Badge>
              <Badge v-if="item.physical_copy_summary" variant="outline" class="font-mono text-[10.5px]" dir="ltr">
                {{ item.physical_copy_summary.short_code }}
              </Badge>
            </div>

            <p v-if="item.station_summary" class="text-[11px] text-muted-foreground flex items-center gap-1">
              <MapPinIcon class="size-3 text-primary shrink-0" />
              <span>{{ item.station_summary.name }} ({{ item.station_summary.city_name }})</span>
            </p>

            <p v-if="effectiveMethods.includes('postal')" class="text-[11px] text-muted-foreground">
              {{
                item.shipping_payer === 'donor'
                  ? languageStore.t('هزینه ارسال پستی بر عهده اهداکننده است.', 'Shipping paid by donor.')
                  : languageStore.t('هزینه ارسال پستی بر عهده گیرنده است.', 'Shipping paid by recipient.')
              }}
            </p>
          </div>
        </div>

        <!-- Physical Copy / QR Circulation Inspection & Handover -->
        <div v-if="isLoadingCopy" class="flex flex-col gap-2">
          <Skeleton class="h-20 w-full rounded-2xl" />
          <Skeleton class="h-14 w-full rounded-2xl" />
        </div>

        <div
          v-else-if="copyError"
          class="rounded-2xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive font-semibold"
        >
          {{ copyError }}
        </div>

        <div v-else-if="copyInspect" class="flex flex-col gap-3 rounded-2xl border border-border/60 bg-background/60 p-3">
          <!-- Immediate Success Banner After Handover -->
          <div
            v-if="handoverSuccess"
            class="rounded-2xl border border-primary/40 bg-primary/10 px-3 py-2.5 flex items-center gap-2 text-xs font-bold text-foreground"
          >
            <CheckCircle2Icon class="size-4 text-primary shrink-0" />
            <span>
              {{
                languageStore.t(
                  'تحویل حضوری با موفقیت انجام شد و قفسه کتاب‌ها به‌روزرسانی گردید.',
                  'In-person handover completed and bookshelves updated.'
                )
              }}
            </span>
          </div>

          <div class="flex items-center justify-between gap-2 flex-wrap">
            <div class="flex items-center gap-2">
              <QrCodeIcon class="size-4 text-primary" />
              <span class="text-xs font-extrabold">{{ copyInspect.book_title?.title || item?.title }}</span>
              <Badge variant="outline" class="font-mono text-[11px]" dir="ltr">
                {{ copyInspect.short_code }}
              </Badge>
            </div>
            <div class="flex items-center gap-1.5 flex-wrap">
              <Badge variant="outline" class="text-[10.5px]">
                {{ languageStore.n(maxHandoverQty) }} {{ languageStore.t('جلد موجود', 'copies available') }}
              </Badge>
              <Badge variant="secondary" class="text-[10.5px]">
                {{ copyInspect.status_display || copyInspect.status }}
              </Badge>
            </div>
          </div>

          <!-- Compact Scannable QR Card for Holder / Sharing -->
          <div
            v-if="qrImageUrl"
            class="rounded-2xl border border-border/50 bg-muted/25 p-2.5 flex items-center gap-3"
          >
            <div class="size-20 rounded-xl bg-white p-1.5 border border-border/60 shrink-0 flex items-center justify-center">
              <img :src="qrImageUrl" :alt="copyInspect.short_code" class="size-full object-contain" />
            </div>
            <div class="flex-1 min-w-0 flex flex-col gap-1.5">
              <span class="text-xs font-bold text-foreground">
                {{
                  copyInspect.is_holder
                    ? languageStore.t('کد اسکن تحویل حضوری شما', 'Your Scannable Handover QR')
                    : languageStore.t('شناسه دیجیتال این جلد', 'Physical Copy QR Identity')
                }}
              </span>
              <span class="text-[11px] text-muted-foreground leading-snug">
                {{
                  copyInspect.is_holder
                    ? languageStore.t(
                        'گیرنده می‌تواند با دوربین گوشی این کد QR را اسکن کند یا شناسه آن را وارد نماید.',
                        'The recipient can scan this QR code or enter the code below.'
                      )
                    : languageStore.t(
                        'این QR مخصوص همین نسخه چاپی برای ثبت سفرنامه خوانندگان است.',
                        'Unique QR code linking this physical copy journey.'
                      )
                }}
              </span>
              <div class="flex items-center gap-1.5 flex-wrap">
                <Button
                  type="button"
                  size="xs"
                  variant="outline"
                  class="rounded-xl"
                  @click="copyShortText(copyInspect.short_code, languageStore.t('کد کتاب کپی شد', 'Code copied'))"
                >
                  <CopyIcon data-icon="inline-start" />
                  <span>{{ languageStore.t('کپی کد', 'Copy Code') }}</span>
                </Button>
                <Button
                  type="button"
                  size="xs"
                  variant="outline"
                  class="rounded-xl"
                  @click="copyShortText(shareQrUrl, languageStore.t('لینک QR کپی شد', 'QR link copied'))"
                >
                  <QrCodeIcon data-icon="inline-start" />
                  <span>{{ languageStore.t('کپی لینک', 'Copy Link') }}</span>
                </Button>
              </div>
            </div>
          </div>

          <div
            v-if="!inPersonOnly && copyInspect.station"
            class="rounded-xl bg-muted/40 px-3 py-2 text-xs text-foreground flex items-center gap-2"
          >
            <MapPinIcon class="size-4 text-primary shrink-0" />
            <div>
              <p class="font-bold">{{ copyInspect.station.name }}</p>
              <p class="text-[11px] text-muted-foreground">{{ copyInspect.station.address_text }}</p>
            </div>
          </div>

          <!-- Donor Actions -->
          <template v-if="copyInspect.is_holder">
            <div
              v-if="copyInspect.active_transfer?.status === 'pending_donor'"
              class="rounded-2xl border border-primary/30 bg-primary/5 p-3 flex flex-col gap-2.5"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs font-bold text-foreground">
                  {{ languageStore.t('درخواست تحویل حضوری ثبت شده است — آماده تایید شما:', 'In-person claim waiting for your confirmation:') }}
                </span>
                <Button
                  type="button"
                  size="icon-xs"
                  variant="ghost"
                  :disabled="isLoadingCopy"
                  @click="loadCopyData(copyInspect.short_code)"
                >
                  <RefreshCwIcon class="size-3.5" />
                </Button>
              </div>
              <p
                v-if="copyInspect.active_transfer.recipient_note"
                class="text-[11px] rounded-xl bg-background/80 border border-border/50 px-2.5 py-1.5 text-muted-foreground"
              >
                {{ languageStore.t('یادداشت گیرنده:', 'Recipient note:') }} «{{ copyInspect.active_transfer.recipient_note }}»
              </p>
              <QuantityStepper
                v-model="handoverQty"
                :min="1"
                :max="maxHandoverQty"
                :label="languageStore.t('تعداد جلد تحویلی', 'Handover Quantity')"
                :hint="languageStore.t(`درخواستی: ${languageStore.n(copyInspect.active_transfer.quantity ?? 1)} جلد`, `Requested: ${copyInspect.active_transfer.quantity ?? 1}`)"
                compact
              />
              <Input
                v-model="donorNote"
                :placeholder="languageStore.t('یادداشت شما در سفرنامه برای خواننده بعدی (اختیاری)', 'Optional note for book journey')"
              />
              <div class="flex items-center gap-2 flex-wrap">
                <Button
                  type="button"
                  size="sm"
                  :disabled="isSubmittingAction"
                  @click="handleConfirmHandover(copyInspect.active_transfer!.id)"
                >
                  <Loader2Icon v-if="isSubmittingAction" data-icon="inline-start" class="animate-spin" />
                  <CheckCircle2Icon v-else data-icon="inline-start" />
                  <span>{{ languageStore.t('تایید و تحویل نهایی کتاب', 'Confirm Final Handover') }}</span>
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  :disabled="isSubmittingAction"
                  @click="handleCancelTransfer(copyInspect.active_transfer!.id)"
                >
                  <XCircleIcon data-icon="inline-start" />
                  <span>{{ languageStore.t('لغو', 'Cancel') }}</span>
                </Button>
              </div>
            </div>

            <div
              v-else-if="copyInspect.active_transfer?.status === 'pending_recipient'"
              class="rounded-2xl border border-border/60 bg-muted/40 p-3 flex flex-col gap-2"
            >
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="text-xs font-bold">
                    {{ languageStore.t('در انتظار تایید گیرنده با کد ۴ رقمی', 'Waiting for recipient 4-digit OTP confirmation') }}
                  </span>
                  <Badge variant="outline" class="text-[10.5px]">
                    {{ languageStore.n(copyInspect.active_transfer.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}
                  </Badge>
                </div>
                <Button
                  type="button"
                  size="icon-xs"
                  variant="ghost"
                  :disabled="isLoadingCopy"
                  @click="loadCopyData(copyInspect.short_code)"
                >
                  <RefreshCwIcon class="size-3.5" />
                </Button>
              </div>
              <div v-if="generatedOtp" class="text-center py-2.5 rounded-xl bg-background border border-primary/40 font-mono text-2xl font-black tracking-widest text-primary" dir="ltr">
                {{ generatedOtp }}
              </div>
              <p v-else class="text-[11px] text-muted-foreground leading-relaxed">
                {{
                  languageStore.t(
                    'کد ۴ رقمی قبلی هم‌اکنون فعال است. اگر کد را فراموش کرده‌اید، لغو کرده و کد جدید بسازید.',
                    'An active 4-digit OTP is pending. Cancel it to generate a fresh code if needed.'
                  )
                }}
              </p>
              <Button
                type="button"
                size="xs"
                variant="outline"
                class="self-start"
                :disabled="isSubmittingAction"
                @click="handleCancelTransfer(copyInspect.active_transfer!.id)"
              >
                <span>{{ languageStore.t('لغو کد تحویل فعلی', 'Cancel Active Code') }}</span>
              </Button>
            </div>

            <div v-else class="flex flex-col gap-2.5 pt-1">
              <QuantityStepper
                v-model="handoverQty"
                :min="1"
                :max="maxHandoverQty"
                :label="languageStore.t('تعداد جلد برای تحویل', 'Copies to Hand Over')"
                :hint="languageStore.t(`موجود: ${languageStore.n(maxHandoverQty)} جلد`, `Available: ${maxHandoverQty}`)"
                compact
              />
              <Input
                v-model="donorNote"
                :placeholder="languageStore.t('یادداشت یا خاطره در سفرنامه برای گیرنده (اختیاری)', 'Optional journey note for the next reader')"
              />
              <Button
                type="button"
                size="sm"
                :disabled="isSubmittingAction"
                @click="handleGenerateOtp"
              >
                <Loader2Icon v-if="isSubmittingAction" data-icon="inline-start" class="animate-spin" />
                <KeyRoundIcon v-else data-icon="inline-start" />
                <span>{{ languageStore.t('ایجاد کد ۴ رقمی تحویل حضوری (OTP)', 'Generate 4-Digit Meetup OTP') }}</span>
              </Button>

              <div v-if="!inPersonOnly && stations.length > 0" class="flex items-center gap-2 pt-1 border-t border-border/40">
                <Select v-model="selectedStationId" class="flex-1">
                  <SelectTrigger class="rounded-2xl bg-input/50 border-transparent text-xs font-semibold">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem value="__none__">{{ languageStore.t('تحویل در ایستگاه تفاخر...', 'Deposit in station...') }}</SelectItem>
                      <SelectItem v-for="st in stations" :key="st.id" :value="String(st.id)">
                        {{ st.name }} ({{ st.city_name }})
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  :disabled="isSubmittingAction || selectedStationId === '__none__'"
                  @click="handleDepositToStation"
                >
                  {{ languageStore.t('سپردن', 'Deposit') }}
                </Button>
              </div>
            </div>
          </template>

          <!-- Guest prompt when scanning / opening QR code while logged out -->
          <div
            v-else-if="!isAuthenticated && !handoverSuccess"
            class="rounded-2xl border border-primary/30 bg-primary/5 p-3 flex flex-col gap-2"
          >
            <span class="text-xs font-bold text-foreground">
              {{ languageStore.t('برای ثبت تحویل حضوری این کتاب وارد حساب شوید', 'Sign in to claim this book in person') }}
            </span>
            <p class="text-[11px] text-muted-foreground leading-relaxed">
              {{
                languageStore.t(
                  'پس از ورود سریع با شماره تلفن، می‌توانید درخواست تحویل حضوری ثبت کنید یا کد ۴ رقمی اهداکننده را وارد نمایید.',
                  'After quick OTP sign-in, you can submit a meetup claim or verify the 4-digit handover code.'
                )
              }}
            </p>
            <Button type="button" size="sm" class="self-start" @click="openLoginForHandover">
              <LogInIcon data-icon="inline-start" />
              <span>{{ languageStore.t('ورود و دریافت حضوری کتاب', 'Sign In to Claim Book') }}</span>
            </Button>
          </div>

          <!-- Recipient Actions (In-Person QR / Station Pickup / OTP Confirm) -->
          <template v-else-if="copyInspect.can_claim">
            <div class="flex flex-col gap-2.5">
              <div v-if="!inPersonOnly && copyInspect.status === 'in_station'" class="flex flex-col gap-2">
                <Input
                  v-model="recipientNote"
                  :placeholder="languageStore.t('یادداشت یا خاطره برای صفحه اول کتاب (اختیاری)', 'Optional note for book journey')"
                />
                <Button type="button" class="w-full" :disabled="isSubmittingAction" @click="handlePickupStation">
                  <MapPinIcon data-icon="inline-start" />
                  <span>{{ languageStore.t('برداشت کتاب از ایستگاه تفاخر', 'Pick Up from Station') }}</span>
                </Button>
              </div>

              <!-- Claim already submitted and pending donor 1-tap approval -->
              <div
                v-else-if="copyInspect.active_transfer?.status === 'pending_donor'"
                class="rounded-2xl border border-primary/30 bg-primary/5 p-3 flex flex-col gap-2"
              >
                <div class="flex items-center justify-between gap-2 flex-wrap">
                  <span class="text-xs font-bold text-foreground">
                    {{
                      languageStore.t(
                        'درخواست تحویل حضوری شما ثبت شد — منتظر تایید اهداکننده',
                        'Your in-person claim is pending donor confirmation'
                      )
                    }}
                  </span>
                  <Badge variant="outline" class="text-[10.5px]">
                    {{ languageStore.n(copyInspect.active_transfer.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}
                  </Badge>
                </div>
                <p class="text-[11px] text-muted-foreground leading-relaxed">
                  {{
                    languageStore.t(
                      'اهداکننده در گوشی خود همین کتاب را باز کرده و روی دکمه «تایید و تحویل نهایی» بزند تا مالکیت کتاب به قفسه شما منتقل شود.',
                      'Ask the donor to tap Confirm Final Handover on their device to transfer this book to your shelf.'
                    )
                  }}
                </p>
                <div class="flex items-center gap-2 flex-wrap">
                  <Button
                    type="button"
                    size="xs"
                    variant="outline"
                    :disabled="isLoadingCopy"
                    @click="loadCopyData(copyInspect.short_code)"
                  >
                    <RefreshCwIcon data-icon="inline-start" />
                    <span>{{ languageStore.t('بررسی وضعیت تایید', 'Refresh Status') }}</span>
                  </Button>
                  <Button
                    type="button"
                    size="xs"
                    variant="ghost"
                    :disabled="isSubmittingAction"
                    @click="handleCancelTransfer(copyInspect.active_transfer!.id)"
                  >
                    <XCircleIcon data-icon="inline-start" />
                    <span>{{ languageStore.t('لغو درخواست', 'Cancel Claim') }}</span>
                  </Button>
                </div>
              </div>

              <div
                v-else-if="copyInspect.active_transfer?.method === 'otp_fallback' && copyInspect.active_transfer.status === 'pending_recipient'"
                class="flex flex-col gap-2"
              >
                <div class="flex items-center justify-between gap-2 text-xs font-bold text-foreground">
                  <span>{{ languageStore.t('تحویل حضوری با کد ۴ رقمی', 'OTP Handover Verification') }}</span>
                  <Badge variant="outline" class="text-[10.5px]">
                    {{ languageStore.n(copyInspect.active_transfer.quantity ?? 1) }} {{ languageStore.t('جلد', 'copies') }}
                  </Badge>
                </div>
                <Input
                  v-model="recipientNote"
                  :placeholder="languageStore.t('یادداشت یا خاطره برای سفرنامه کتاب (اختیاری)', 'Optional note for book journey')"
                />
                <div class="flex items-center gap-2">
                  <Input
                    v-model="otpInput"
                    dir="ltr"
                    maxlength="6"
                    class="font-mono text-center"
                    :placeholder="languageStore.t('کد ۴ رقمی اهداکننده', '4-digit OTP')"
                  />
                  <Button
                    type="button"
                    :disabled="isSubmittingAction || !otpInput.trim()"
                    @click="handleConfirmHandover(copyInspect.active_transfer!.id, true)"
                  >
                    <Loader2Icon v-if="isSubmittingAction" data-icon="inline-start" class="animate-spin" />
                    <span>{{ languageStore.t('تایید دریافت', 'Verify OTP') }}</span>
                  </Button>
                </div>
              </div>

              <div v-else class="flex flex-col gap-2">
                <QuantityStepper
                  v-model="handoverQty"
                  :min="1"
                  :max="maxHandoverQty"
                  :label="languageStore.t('تعداد جلد درخواستی', 'Requested Copies')"
                  :hint="languageStore.t(`موجود: ${languageStore.n(maxHandoverQty)} جلد`, `Available: ${maxHandoverQty}`)"
                  compact
                />
                <Input
                  v-model="recipientNote"
                  :placeholder="languageStore.t('یادداشت یا خاطره برای صفحه اول کتاب (اختیاری)', 'Optional note for book journey')"
                />
                <Button type="button" class="w-full" :disabled="isSubmittingAction" @click="handleClaimInPerson">
                  <Loader2Icon v-if="isSubmittingAction" data-icon="inline-start" class="animate-spin" />
                  <QrCodeIcon v-else data-icon="inline-start" />
                  <span>{{ languageStore.t('درخواست تحویل حضوری (در ملاقات هستم)', 'Claim In-Person (QR Handover)') }}</span>
                </Button>
              </div>
            </div>
          </template>

          <!-- Timeline Journey -->
          <div v-if="copyJourney?.journey?.length" class="flex flex-col gap-1.5 pt-2 border-t border-border/50">
            <span class="text-[11px] font-bold text-muted-foreground">
              {{ languageStore.t(`سفرنامه کتاب (${copyJourney.total_transfers} جابه‌جایی)`, `Book Journey (${copyJourney.total_transfers} handovers)`) }}
            </span>
            <div class="flex flex-col gap-1.5 max-h-40 overflow-y-auto no-scrollbar pe-1">
              <div
                v-for="ev in copyJourney.journey"
                :key="ev.id"
                class="text-[11px] rounded-xl bg-muted/35 px-2.5 py-2 flex flex-col gap-1"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="font-bold text-foreground truncate">
                    {{ ev.from_display_name || '—' }} ← {{ ev.to_display_name || ev.station_name || '—' }}
                  </span>
                  <span v-if="ev.date" class="text-[10px] text-muted-foreground shrink-0">
                    {{ new Date(ev.date).toLocaleDateString('fa-IR') }}
                  </span>
                </div>
                <div class="flex items-center gap-2 flex-wrap text-[10px] text-muted-foreground">
                  <span v-if="ev.method_display">{{ ev.method_display }}</span>
                  <span v-if="(ev.quantity ?? 1) > 1" class="font-bold text-foreground">
                    · {{ languageStore.n(ev.quantity!) }} {{ languageStore.t('جلد', 'copies') }}
                  </span>
                  <span v-if="ev.station_name" class="text-primary">· {{ ev.station_name }}</span>
                </div>
                <p v-if="ev.donor_note" class="text-[10.5px] text-foreground/85 bg-background/70 rounded-lg px-2 py-1 border border-border/40">
                  {{ languageStore.t('اهداکننده:', 'Donor:') }} «{{ ev.donor_note }}»
                </p>
                <p v-if="ev.recipient_note" class="text-[10.5px] text-foreground/85 bg-background/70 rounded-lg px-2 py-1 border border-border/40">
                  {{ languageStore.t('گیرنده:', 'Recipient:') }} «{{ ev.recipient_note }}»
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Postal / Digital Donation Request Flow (C2C DonationRequest) -->
        <div
          v-if="supportsRequestFlow && !isOwnListing"
          class="flex flex-col gap-2.5 rounded-2xl border border-border/60 bg-muted/20 p-3"
        >
          <div class="flex items-center gap-2">
            <HandHeartIcon class="size-4 text-primary" />
            <Label class="text-xs font-bold text-foreground">
              {{
                effectiveMethods.includes('digital')
                  ? languageStore.t('درخواست دریافت نسخه دیجیتال', 'Request Digital Book')
                  : languageStore.t('ثبت درخواست دریافت پستی / هماهنگی اهدا', 'Request Donation / Postal Delivery')
              }}
            </Label>
          </div>

          <div
            v-if="requestSubmitted"
            class="rounded-xl bg-primary/10 border border-primary/25 px-3 py-2 text-xs font-semibold text-foreground"
          >
            {{
              languageStore.t(
                'درخواست شما با موفقیت ثبت شد و به اهداکننده اطلاع داده شد.',
                'Your request has been sent to the donor.'
              )
            }}
          </div>

          <template v-else>
            <Textarea
              v-model="requestMessage"
              rows="2"
              :placeholder="
                languageStore.t(
                  'پیام کوتاه برای اهداکننده (مثلاً شهر یا نحوه هماهنگی پستی/حضوری)...',
                  'Short note for the donor (city or preferred handover)...'
                )
              "
            />
            <Button type="button" :disabled="isSubmittingAction" @click="handleSubmitRequest">
              <Loader2Icon v-if="isSubmittingAction" data-icon="inline-start" class="animate-spin" />
              <SendIcon v-else data-icon="inline-start" />
              <span>{{ languageStore.t('ارسال درخواست دریافت کتاب', 'Send Donation Request') }}</span>
            </Button>
          </template>
        </div>
      </div>

      <DialogFooter class="sm:justify-start">
        <Button type="button" variant="outline" @click="emit('update:open', false)">
          {{ languageStore.t('بستن', 'Close') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
