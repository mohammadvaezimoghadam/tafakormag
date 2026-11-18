<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import {
  adminDonateBook,
  donateShelfBookToPhone,
  publishShelfBookListing,
  extractApiErrorMessage,
  searchUsers,
} from '@/api/shelf'
import type {
  ShelfBook,
  DonationMethod,
  ShippingPayer,
  DonateToPhoneResult,
  UserSearchResult,
} from '@/types/shelf'
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
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import {
  BookOpenIcon,
  CheckCircle2Icon,
  CheckIcon,
  CopyIcon,
  HandHeartIcon,
  Loader2Icon,
  PackageIcon,
  PhoneIcon,
  PlusIcon,
  QrCodeIcon,
  SearchIcon,
  StoreIcon,
  UserCheckIcon,
  UserIcon,
  XIcon,
} from '@lucide/vue'

const props = defineProps<{
  open: boolean
  book: ShelfBook | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'donated', book?: ShelfBook): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()
const userStore = useUserStore()

const isStaff = computed(() => userStore.isStaff)

type DonationTab = 'phone' | 'marketplace'
const activeTab = ref<DonationTab>('phone')

// Direct Phone & Admin Donation State
const recipientPhone = ref('')
const selectedUser = ref<UserSearchResult | null>(null)
const userSearchQuery = ref('')
const userSearchResults = ref<UserSearchResult[]>([])
const isSearchingUsers = ref(false)
let searchDebounceTimeout: ReturnType<typeof setTimeout> | null = null

const sendSms = ref(false)
const phoneQuantity = ref(1)
const phoneSuccessResult = ref<DonateToPhoneResult | null>(null)
const adminSuccessMessage = ref('')
const isCopied = ref(false)

// Marketplace Donation State
const marketplaceQuantity = ref(1)
const enableInPerson = ref(true)
const enablePostal = ref(false)
const shippingPayer = ref<ShippingPayer>('recipient')
const description = ref('')

// Common State
const isSubmitting = ref(false)
const formError = ref('')

const availableCopies = computed(() => {
  if (!props.book) return 1
  if (typeof props.book.available_quantity === 'number') {
    return Math.max(1, props.book.available_quantity)
  }
  const total = props.book.quantity ?? 1
  const reserved = props.book.reserved_quantity ?? 0
  return Math.max(1, total - reserved)
})

watch(
  () => [props.open, props.book] as const,
  ([isOpen, book]) => {
    if (isOpen && book) {
      activeTab.value = 'phone'
      phoneQuantity.value = 1
      recipientPhone.value = ''
      selectedUser.value = null
      userSearchQuery.value = ''
      userSearchResults.value = []
      isSearchingUsers.value = false
      sendSms.value = false
      phoneSuccessResult.value = null
      adminSuccessMessage.value = ''
      isCopied.value = false

      marketplaceQuantity.value = 1
      enableInPerson.value = true
      enablePostal.value = false
      shippingPayer.value = 'recipient'
      description.value = ''
      formError.value = ''
    }
  },
  { immediate: true }
)

const resolveMediaUrl = (raw?: string | null): string | null => {
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw
  }
  return `/${raw}`
}

const handleUserSearchInput = () => {
  if (searchDebounceTimeout) clearTimeout(searchDebounceTimeout)
  const q = userSearchQuery.value.trim()
  if (!q) {
    userSearchResults.value = []
    isSearchingUsers.value = false
    return
  }
  isSearchingUsers.value = true
  searchDebounceTimeout = setTimeout(async () => {
    try {
      userSearchResults.value = await searchUsers(q)
    } catch {
      userSearchResults.value = []
    } finally {
      isSearchingUsers.value = false
    }
  }, 250)
}

const selectExistingUser = (u: UserSearchResult) => {
  selectedUser.value = u
  recipientPhone.value = u.phone
  userSearchResults.value = []
  formError.value = ''
}

const selectNewPhone = (phone: string) => {
  const clean = phone.replace(/[^\d+]/g, '').trim()
  selectedUser.value = {
    id: 0,
    phone: clean,
    name: 'کاربر جدید',
  }
  recipientPhone.value = clean
  userSearchResults.value = []
  formError.value = ''
}

const clearSelectedRecipient = () => {
  selectedUser.value = null
  recipientPhone.value = ''
  userSearchQuery.value = ''
  userSearchResults.value = []
  formError.value = ''
}

const copyShortCode = async () => {
  if (!phoneSuccessResult.value?.short_code) return
  try {
    await navigator.clipboard.writeText(phoneSuccessResult.value.short_code)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
    toastStore.triggerToast(
      languageStore.t('کد گردش در حافظه کپی شد', 'Code copied to clipboard'),
      'success'
    )
  } catch {
    // fallback
  }
}

const handlePhoneSubmit = async () => {
  if (!props.book) return

  const cleanPhone = recipientPhone.value.trim()
  if (!cleanPhone) {
    formError.value = languageStore.t(
      'لطفاً شماره همراه یا کاربر گیرنده را مشخص کنید.',
      'Please select recipient user or phone number.'
    )
    return
  }

  formError.value = ''
  isSubmitting.value = true

  try {
    if (isStaff.value) {
      // Admin Direct Donation: Instant execution without recipient confirmation
      const res = await adminDonateBook(props.book.id, {
        recipient_phone: cleanPhone,
        quantity: phoneQuantity.value,
      })
      adminSuccessMessage.value = res.message || 'کتاب با موفقیت اهدا شد و در قفسه گیرنده ثبت گردید.'
      toastStore.triggerToast(adminSuccessMessage.value, 'success')
      emit('donated')
    } else {
      // Normal User Phone Donation: Reservation / transfer
      const result = await donateShelfBookToPhone(props.book.id, {
        recipient_phone: cleanPhone,
        quantity: phoneQuantity.value,
        send_sms: sendSms.value,
      })
      phoneSuccessResult.value = result
      toastStore.triggerToast(
        result.message || languageStore.t('کتاب با موفقیت برای اهدا رزرو شد', 'Book reserved for donation'),
        'success'
      )
      emit('donated')
    }
  } catch (err) {
    const msg = extractApiErrorMessage(
      err,
      languageStore.t('خطا در ثبت اهدا', 'Failed to donate book')
    )
    formError.value = msg
    toastStore.triggerToast(msg, 'error')
  } finally {
    isSubmitting.value = false
  }
}

const handleMarketplaceSubmit = async () => {
  if (!props.book) return

  const methods: DonationMethod[] = []
  if (enableInPerson.value) methods.push('in_person')
  if (enablePostal.value) methods.push('postal')

  if (methods.length === 0) {
    formError.value = languageStore.t(
      'لطفاً حداقل یک شیوه تحویل (حضوری یا پستی) را انتخاب کنید.',
      'Please select at least one handover method.'
    )
    return
  }

  formError.value = ''
  isSubmitting.value = true

  try {
    const updated = await publishShelfBookListing(props.book.id, {
      deal_type: 'donation',
      price: 0,
      stock: Math.min(availableCopies.value, Math.max(1, marketplaceQuantity.value)),
      donation_methods: methods,
      shipping_payer: shippingPayer.value,
      description: description.value.trim(),
    })

    const shortCode = updated.physical_copy_summary?.short_code
    toastStore.triggerToast(
      shortCode
        ? languageStore.t(
            `کتاب «${props.book.book_title.title}» با کد گردش ${shortCode} در بازارچه ثبت شد`,
            `Book listed with code ${shortCode}`
          )
        : languageStore.t(
            `کتاب «${props.book.book_title.title}» با موفقیت برای اهدا منتشر شد`,
            `Book listed successfully`
          ),
      'success'
    )

    emit('donated', updated)
    emit('update:open', false)
  } catch (err) {
    const msg = extractApiErrorMessage(
      err,
      languageStore.t('ثبت اهدا در بازارچه انجام نشد', 'Failed to register donation')
    )
    formError.value = msg
    toastStore.triggerToast(msg, 'error')
  } finally {
    isSubmitting.value = false
  }
}

const closeDialog = () => {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent class="sm:max-w-md max-h-[90vh] overflow-y-auto rounded-3xl p-5">
      <DialogHeader class="gap-1 text-start">
        <DialogTitle class="text-base font-extrabold text-foreground flex items-center gap-2">
          <HandHeartIcon class="size-5 text-primary shrink-0" />
          <span>{{ isStaff ? languageStore.t('اهدای کتاب از انبار تفکر', 'Admin Book Donation') : languageStore.t('اهدای کتاب', 'Donate Book') }}</span>
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground">
          {{
            isStaff
              ? languageStore.t('کتاب به صورت آنی تحویل داده شده و در قفسه کاربر گیرنده ثبت می‌گردد.', 'Book is instantly gifted and added to recipient shelf.')
              : languageStore.t('می‌توانید کتاب را مستقیماً به شماره همراه یک فرد هدیه دهید یا در بازارچه منتشر کنید.', 'Gift this book directly to a phone number or publish to marketplace.')
          }}
        </DialogDescription>
      </DialogHeader>

      <div v-if="book" class="flex flex-col gap-4 py-1">
        <!-- 1. Book Preview Card -->
        <div class="rounded-2xl border border-border/60 bg-muted/30 p-3 flex items-center gap-3">
          <div class="w-12 h-16 rounded-xl overflow-hidden bg-muted/60 border border-border/50 shrink-0 flex items-center justify-center">
            <img
              v-if="resolveMediaUrl(book.book_title.cover_image)"
              :src="resolveMediaUrl(book.book_title.cover_image)!"
              :alt="book.book_title.title"
              class="size-full object-cover"
            />
            <BookOpenIcon v-else class="size-5 text-muted-foreground/60" />
          </div>

          <div class="flex flex-col gap-0.5 min-w-0 flex-1">
            <h3 class="text-sm font-extrabold text-foreground truncate">
              {{ book.book_title.title }}
            </h3>
            <p class="text-xs text-muted-foreground truncate">
              {{ book.book_title.author }}
            </p>
            <div class="flex items-center gap-1.5 mt-1">
              <Badge variant="outline" class="text-[10.5px]">
                {{ languageStore.t('موجودی انبار:', 'Available:') }}
                <span class="font-bold ms-1">{{ languageStore.n(availableCopies) }}</span>
                {{ languageStore.t('جلد', 'copies') }}
              </Badge>
              <Badge
                v-if="book.reserved_quantity && book.reserved_quantity > 0"
                variant="secondary"
                class="text-[10.5px] text-amber-600 dark:text-amber-400"
              >
                {{ languageStore.n(book.reserved_quantity) }} {{ languageStore.t('جلد در انتظار', 'reserved') }}
              </Badge>
            </div>
          </div>
        </div>

        <!-- 2A. Admin Success Screen -->
        <div
          v-if="adminSuccessMessage"
          class="flex flex-col items-center text-center gap-3 py-4 px-3 rounded-2xl bg-muted/50 border border-border/70"
        >
          <div class="size-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-sm">
            <CheckIcon class="size-6 stroke-[3]" />
          </div>

          <div class="flex flex-col gap-1">
            <h4 class="text-sm font-black text-foreground">
              {{ languageStore.t('اهدا با موفقیت انجام شد!', 'Donation Completed Successfully!') }}
            </h4>
            <p class="text-xs text-muted-foreground leading-relaxed">
              {{ adminSuccessMessage }}
            </p>
          </div>

          <Button
            type="button"
            class="w-full rounded-2xl bg-primary text-primary-foreground hover:bg-primary/90 font-bold mt-2"
            @click="closeDialog"
          >
            <span>{{ languageStore.t('متوجه شدم و بستن', 'Done') }}</span>
          </Button>
        </div>

        <!-- 2B. Normal User Phone Success Screen -->
        <div
          v-else-if="phoneSuccessResult"
          class="flex flex-col items-center text-center gap-3 py-3 px-2 rounded-2xl bg-muted/50 border border-border/70"
        >
          <div class="size-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-sm">
            <CheckIcon class="size-6 stroke-[3]" />
          </div>

          <div class="flex flex-col gap-1">
            <h4 class="text-sm font-black text-foreground">
              {{ languageStore.t('هدیه با موفقیت ثبت شد!', 'Gift Created Successfully!') }}
            </h4>
            <p class="text-xs text-muted-foreground leading-relaxed">
              {{
                languageStore.t(
                  'کتاب برای گیرنده رزرو شد. به محض اینکه گیرنده وارد تفکر شود، کتاب به قفسه او اضافه می‌گردد.',
                  'Book is reserved. It will appear on recipient shelf upon login.'
                )
              }}
            </p>
          </div>

          <!-- Code Box -->
          <div class="w-full rounded-2xl bg-card border border-border/60 p-3 flex items-center justify-between gap-2 mt-1">
            <div class="flex flex-col text-start gap-0.5">
              <span class="text-[10.5px] text-muted-foreground font-semibold">
                {{ languageStore.t('کد گردش کتاب (QR Code):', 'Circulation Code:') }}
              </span>
              <span class="text-base font-black tracking-wider text-primary font-mono">
                {{ phoneSuccessResult.short_code }}
              </span>
            </div>
            <Button
              type="button"
              variant="outline"
              size="xs"
              class="rounded-xl gap-1"
              @click="copyShortCode"
            >
              <CheckIcon v-if="isCopied" class="size-3.5 text-primary" />
              <CopyIcon v-else class="size-3.5" />
              <span class="text-[11px]">{{ isCopied ? languageStore.t('کپی شد', 'Copied') : languageStore.t('کپی کد', 'Copy') }}</span>
            </Button>
          </div>

          <div class="w-full flex items-center justify-between text-xs px-1 text-muted-foreground">
            <span>{{ languageStore.t('شماره گیرنده:', 'Recipient:') }}</span>
            <span class="font-bold text-foreground font-mono" dir="ltr">{{ phoneSuccessResult.recipient_phone }}</span>
          </div>

          <Button
            type="button"
            class="w-full rounded-2xl bg-primary text-primary-foreground hover:bg-primary/90 font-bold mt-2"
            @click="closeDialog"
          >
            <span>{{ languageStore.t('متوجه شدم و بستن', 'Done') }}</span>
          </Button>
        </div>

        <!-- 3. Form Body -->
        <template v-else>
          <!-- Mode Tabs (Only for normal users, staff is dedicated direct donation) -->
          <div v-if="!isStaff" class="grid grid-cols-2 p-1 rounded-2xl bg-muted/60 border border-border/50 text-xs font-bold">
            <button
              type="button"
              class="py-2 rounded-xl transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              :class="activeTab === 'phone' ? 'bg-card text-foreground shadow-2xs' : 'text-muted-foreground hover:text-foreground'"
              @click="activeTab = 'phone'"
            >
              <PhoneIcon class="size-3.5" />
              <span>{{ languageStore.t('اهدا به شماره همراه', 'Direct to Phone') }}</span>
            </button>
            <button
              type="button"
              class="py-2 rounded-xl transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              :class="activeTab === 'marketplace' ? 'bg-card text-foreground shadow-2xs' : 'text-muted-foreground hover:text-foreground'"
              @click="activeTab = 'marketplace'"
            >
              <StoreIcon class="size-3.5" />
              <span>{{ languageStore.t('انتشار در بازارچه', 'Marketplace') }}</span>
            </button>
          </div>

          <!-- TAB 1: Direct Donation (Staff or Phone Tab) -->
          <div v-if="isStaff || activeTab === 'phone'" class="flex flex-col gap-3.5">
            <!-- Quantity Stepper -->
            <QuantityStepper
              v-model="phoneQuantity"
              :min="1"
              :max="availableCopies"
              :label="languageStore.t('تعداد جلد برای اهدا', 'Copies to Donate')"
              :hint="languageStore.t(`از ${languageStore.n(availableCopies)} جلد آزاد`, `of ${availableCopies} free`)"
              compact
            />

            <!-- Staff Mode: Autocomplete Search -->
            <div v-if="isStaff" class="flex flex-col gap-1.5">
              <Label class="text-xs font-bold text-foreground">
                {{ languageStore.t('گیرنده کتاب (جستجو در کاربران یا شماره جدید)', 'Recipient (User Search or New Phone)') }}
              </Label>

              <!-- Selected Recipient Card -->
              <div
                v-if="selectedUser"
                class="rounded-2xl border border-border/70 bg-muted/40 p-3 flex items-center justify-between gap-2"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <div class="size-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0">
                    <UserCheckIcon class="size-4" />
                  </div>
                  <div class="flex flex-col min-w-0">
                    <span class="text-xs font-bold text-foreground truncate">{{ selectedUser.name }}</span>
                    <span class="text-[11px] font-mono text-muted-foreground truncate" dir="ltr">{{ selectedUser.phone }}</span>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  class="rounded-xl text-[11px] text-muted-foreground hover:text-destructive gap-1"
                  @click="clearSelectedRecipient"
                >
                  <XIcon class="size-3.5" />
                  <span>{{ languageStore.t('تغییر', 'Change') }}</span>
                </Button>
              </div>

              <!-- Search Input & Autocomplete Dropdown -->
              <div v-else class="relative">
                <div class="relative">
                  <SearchIcon class="size-4 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3.5 pointer-events-none" />
                  <Input
                    v-model="userSearchQuery"
                    type="text"
                    :placeholder="languageStore.t('جستجوی نام یا شماره همراه گیرنده...', 'Search name or phone...')"
                    class="ps-10 h-10 rounded-2xl bg-card border-border/60 text-xs"
                    @input="handleUserSearchInput"
                  />
                  <Loader2Icon v-if="isSearchingUsers" class="size-4 text-primary absolute top-1/2 -translate-y-1/2 end-3.5 animate-spin" />
                </div>

                <!-- Dropdown Results -->
                <div
                  v-if="userSearchQuery.trim()"
                  class="mt-1 rounded-2xl border border-border/60 bg-popover text-popover-foreground shadow-lg overflow-hidden flex flex-col max-h-48 overflow-y-auto"
                >
                  <!-- Found Users List -->
                  <button
                    v-for="u in userSearchResults"
                    :key="u.id"
                    type="button"
                    class="px-3.5 py-2.5 text-start hover:bg-muted/60 transition-colors flex items-center justify-between gap-2 border-b border-border/30 last:border-0 cursor-pointer"
                    @click="selectExistingUser(u)"
                  >
                    <div class="flex items-center gap-2 min-w-0">
                      <UserIcon class="size-4 text-muted-foreground shrink-0" />
                      <span class="text-xs font-bold text-foreground truncate">{{ u.name }}</span>
                    </div>
                    <span class="text-[11px] font-mono text-muted-foreground shrink-0" dir="ltr">{{ u.phone }}</span>
                  </button>

                  <!-- Direct Gift to New Phone Button -->
                  <button
                    type="button"
                    class="px-3.5 py-2.5 text-start hover:bg-primary/10 transition-colors flex items-center gap-2 text-primary font-bold text-xs bg-muted/20 cursor-pointer"
                    @click="selectNewPhone(userSearchQuery)"
                  >
                    <PlusIcon class="size-4 shrink-0" />
                    <span>{{ languageStore.t(`اهدا به شماره جدید: ${userSearchQuery.trim()}`, `Donate to new phone: ${userSearchQuery.trim()}`) }}</span>
                  </button>
                </div>
              </div>

              <p class="text-[10.5px] text-muted-foreground leading-relaxed mt-0.5">
                {{
                  languageStore.t(
                    'کتاب به صورت آنی به نام این کاربر ثبت شده و پیامک کاوه‌نگار برای وی ارسال می‌گردد.',
                    'Book will be instantly assigned and SMS dispatched via Kavenegar.'
                  )
                }}
              </p>
            </div>

            <!-- Normal User Mode: Simple Phone Input -->
            <div v-else class="flex flex-col gap-1.5">
              <Label for="recipient-phone" class="text-xs font-bold text-foreground">
                {{ languageStore.t('شماره همراه گیرنده کتاب', 'Recipient Phone Number') }}
              </Label>
              <div class="relative">
                <PhoneIcon class="size-4 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3.5 pointer-events-none" />
                <Input
                  id="recipient-phone"
                  v-model="recipientPhone"
                  type="tel"
                  dir="ltr"
                  placeholder="09123456789"
                  class="ps-10 h-10 rounded-2xl bg-card border-border/60 text-sm font-mono tracking-wider"
                />
              </div>
              <p class="text-[10.5px] text-muted-foreground leading-relaxed">
                {{
                  languageStore.t(
                    'اگر گیرنده هنوز در تفکر ثبت‌نام نکرده باشد، به محض ثبت‌نام با این شماره کتاب به قفسه او اضافه خواهد شد.',
                    'If not registered yet, the book automatically links upon signup.'
                  )
                }}
              </p>
            </div>

            <!-- Optional SMS Checkbox (Only for normal users, staff sends automated Kavenegar SMS) -->
            <div v-if="!isStaff" class="rounded-2xl border border-border/60 bg-muted/20 p-3 flex items-start gap-3">
              <Checkbox
                id="send-sms"
                :checked="sendSms"
                class="mt-0.5"
                @update:checked="(val) => sendSms = Boolean(val)"
              />
              <div class="flex flex-col gap-0.5">
                <Label for="send-sms" class="text-xs font-bold text-foreground cursor-pointer select-none">
                  {{ languageStore.t('ارسال پیامک اطلاع‌رسانی به گیرنده', 'Send SMS Notification to Recipient') }}
                </Label>
                <span class="text-[10.5px] text-muted-foreground leading-relaxed">
                  {{
                    languageStore.t(
                      'پیامک حاوی لینک دریافت کتاب و کد گردش برای گیرنده ارسال می‌شود.',
                      'Sends SMS with link and circulation code.'
                    )
                  }}
                </span>
              </div>
            </div>
          </div>

          <!-- TAB 2: Marketplace Listing (Normal Users Only) -->
          <div v-else class="flex flex-col gap-3.5">
            <QuantityStepper
              v-model="marketplaceQuantity"
              :min="1"
              :max="availableCopies"
              :label="languageStore.t('تعداد جلد برای اهدا', 'Copies to Donate')"
              :hint="languageStore.t(`از ${languageStore.n(availableCopies)} جلد آزاد`, `of ${availableCopies} free`)"
              compact
            />

            <!-- Handover Methods Selection -->
            <div class="flex flex-col gap-2">
              <Label class="text-xs font-bold text-foreground">
                {{ languageStore.t('شیوهٔ تحویل کتاب', 'Handover Method') }}
              </Label>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  type="button"
                  class="rounded-2xl border p-3 flex flex-col gap-1.5 text-start transition-all cursor-pointer select-none"
                  :class="
                    enableInPerson
                      ? 'border-primary bg-primary/5 shadow-2xs'
                      : 'border-border/60 bg-card hover:bg-muted/40 opacity-75'
                  "
                  @click="enableInPerson = !enableInPerson"
                >
                  <div class="flex items-center justify-between w-full">
                    <div class="flex items-center gap-1.5 font-bold text-xs text-foreground">
                      <QrCodeIcon class="size-4 text-primary shrink-0" />
                      <span>{{ languageStore.t('حضوری (کد QR)', 'In-Person (QR)') }}</span>
                    </div>
                    <CheckCircle2Icon
                      v-if="enableInPerson"
                      class="size-4 text-primary shrink-0"
                    />
                  </div>
                  <span class="text-[10.5px] text-muted-foreground leading-relaxed">
                    {{ languageStore.t('تحویل دست‌به‌دست با ثبت سفرنامه کتاب', 'Meetup handover with journey tracking') }}
                  </span>
                </button>

                <button
                  type="button"
                  class="rounded-2xl border p-3 flex flex-col gap-1.5 text-start transition-all cursor-pointer select-none"
                  :class="
                    enablePostal
                      ? 'border-primary bg-primary/5 shadow-2xs'
                      : 'border-border/60 bg-card hover:bg-muted/40 opacity-75'
                  "
                  @click="enablePostal = !enablePostal"
                >
                  <div class="flex items-center justify-between w-full">
                    <div class="flex items-center gap-1.5 font-bold text-xs text-foreground">
                      <PackageIcon class="size-4 text-primary shrink-0" />
                      <span>{{ languageStore.t('ارسال پستی', 'Postal Shipping') }}</span>
                    </div>
                    <CheckCircle2Icon
                      v-if="enablePostal"
                      class="size-4 text-primary shrink-0"
                    />
                  </div>
                  <span class="text-[10.5px] text-muted-foreground leading-relaxed">
                    {{ languageStore.t('ارسال از طریق پست با آدرس دریافت‌کننده', 'Ship by post after request approval') }}
                  </span>
                </button>
              </div>

              <!-- Postal Shipping Payer Selector -->
              <div
                v-if="enablePostal"
                class="rounded-2xl border border-border/50 bg-muted/20 p-2.5 flex items-center justify-between gap-2 mt-1"
              >
                <span class="text-[11px] font-semibold text-muted-foreground">
                  {{ languageStore.t('پرداخت هزینه ارسال پست:', 'Shipping Payer:') }}
                </span>
                <div class="flex items-center gap-1">
                  <Button
                    type="button"
                    size="xs"
                    :variant="shippingPayer === 'recipient' ? 'default' : 'outline'"
                    class="rounded-xl text-[10.5px]"
                    @click="shippingPayer = 'recipient'"
                  >
                    {{ languageStore.t('گیرنده', 'Recipient') }}
                  </Button>
                  <Button
                    type="button"
                    size="xs"
                    :variant="shippingPayer === 'donor' ? 'default' : 'outline'"
                    class="rounded-xl text-[10.5px]"
                    @click="shippingPayer = 'donor'"
                  >
                    {{ languageStore.t('با من (اهداکننده)', 'Donor') }}
                  </Button>
                </div>
              </div>
            </div>

            <!-- Optional Note -->
            <div class="flex flex-col gap-1.5">
              <Label for="donate-note" class="text-xs font-bold text-muted-foreground">
                {{ languageStore.t('یادداشت اهداکننده (اختیاری)', 'Donor Note (Optional)') }}
              </Label>
              <Textarea
                id="donate-note"
                v-model="description"
                rows="2"
                class="rounded-xl resize-none text-xs"
                :placeholder="languageStore.t('مثلاً: تقدیم به علاقه‌مندان کتاب و ادبیات...', 'e.g. Gift for fellow book lovers...')"
              />
            </div>
          </div>

          <!-- Error Alert -->
          <div
            v-if="formError"
            class="rounded-2xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive font-semibold"
          >
            {{ formError }}
          </div>

          <DialogFooter class="gap-2 sm:justify-start">
            <Button
              v-if="isStaff || activeTab === 'phone'"
              type="button"
              class="rounded-2xl bg-black text-white hover:bg-neutral-800 dark:bg-emerald-600 dark:text-white font-bold"
              :disabled="isSubmitting || !recipientPhone.trim()"
              @click="handlePhoneSubmit"
            >
              <Loader2Icon v-if="isSubmitting" data-icon="inline-start" class="animate-spin" />
              <span>{{ isStaff ? languageStore.t('تایید و اهدا', 'Confirm Donation') : languageStore.t('ثبت اهدا به این شماره', 'Gift to Recipient') }}</span>
            </Button>

            <Button
              v-else
              type="button"
              class="rounded-2xl bg-black text-white hover:bg-neutral-800 dark:bg-primary dark:text-primary-foreground font-bold"
              :disabled="isSubmitting || (!enableInPerson && !enablePostal)"
              @click="handleMarketplaceSubmit"
            >
              <Loader2Icon v-if="isSubmitting" data-icon="inline-start" class="animate-spin" />
              <span>{{ languageStore.t('ثبت و انتشار در بازارچه', 'Publish to Marketplace') }}</span>
            </Button>

            <Button
              type="button"
              variant="outline"
              class="rounded-2xl"
              :disabled="isSubmitting"
              @click="closeDialog"
            >
              {{ languageStore.t('انصراف', 'Cancel') }}
            </Button>
          </DialogFooter>
        </template>
      </div>
    </DialogContent>
  </Dialog>
</template>
