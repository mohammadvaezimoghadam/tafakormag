<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { DonationCampaignProps, PayoutRequestItem } from '@/types/kindness'
import { uploadTransparencyLog, fetchCampaignPayouts, requestCampaignPayout } from '@/api'
import { useToastStore } from '@/stores/toastStore'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useLanguageStore } from '@/stores/languageStore'
import { cn } from '@/lib/utils'
import {
  formatKindnessNumber,
  getCampaignCategoryLabel,
  getCampaignDaysRemaining,
  getCampaignStatusConfig,
} from '@/utils/kindness'
import {
  BanIcon,
  CalendarIcon,
  CheckCircle2Icon,
  ClockIcon,
  FileTextIcon,
  HandHeartIcon,
  HeartIcon,
  ImageIcon,
  LayersIcon,
  PencilIcon,
  Share2Icon,
  Trash2Icon,
  UserIcon,
  UsersIcon,
  UploadIcon,
  PlusCircleIcon,
  Loader2Icon,
  CreditCardIcon,
  WalletIcon,
  AlertCircleIcon,
  XIcon,
  ArrowDownToLineIcon,
} from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    campaign: DonationCampaignProps
    loading?: boolean
  }>(),
  {
    loading: false,
  }
)

const emit = defineEmits<{
  (e: 'donate-click', campaignId: string | number): void
  (e: 'topic-click', topicId: string | number): void
  (e: 'transparency-click', imageIndex: number, imageUrl: string): void
  (e: 'share-click', campaignId: string | number): void
  (e: 'edit-click', campaignId: string | number): void
  (e: 'delete-click', campaignId: string | number): void
  (e: 'transparency-uploaded'): void
  (e: 'payout-requested'): void
}>()

const languageStore = useLanguageStore()

const currentMediaIndex = ref(0)
const defaultTab = computed(() =>
  props.campaign.status === 'executed' ||
  (props.campaign.status === 'completed' && props.campaign.transparency?.isAvailable)
    ? 'transparency'
    : 'overview'
)
const activeTab = ref<'overview' | 'donors' | 'transparency'>(defaultTab.value)

const toastStore = useToastStore()

// Transparency upload form state
const showTransparencyForm = ref(false)
const transparencySubmitting = ref(false)
const transparencyForm = ref({
  title: '',
  description: '',
  amount: null as number | null,
  receiptFile: null as File | null,
})
const transparencyFileInputRef = ref<HTMLInputElement | null>(null)

const canUploadTransparency = computed(() => {
  return Boolean(props.campaign.canEdit)
})

const onTransparencyFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    transparencyForm.value.receiptFile = input.files[0]
  }
}

const resetTransparencyForm = () => {
  transparencyForm.value = { title: '', description: '', amount: null, receiptFile: null }
  showTransparencyForm.value = false
  if (transparencyFileInputRef.value) transparencyFileInputRef.value.value = ''
}

const submitTransparencyLog = async () => {
  const form = transparencyForm.value
  if (!form.title.trim()) {
    toastStore.triggerToast('عنوان گزارش الزامی است.', 'error')
    return
  }
  if (!form.amount || form.amount <= 0) {
    toastStore.triggerToast('مبلغ باید بزرگتر از صفر باشد.', 'error')
    return
  }

  transparencySubmitting.value = true
  try {
    const formData = new FormData()
    formData.append('title', form.title.trim())
    if (form.description) formData.append('description', form.description.trim())
    formData.append('amount', String(form.amount))
    if (form.receiptFile) formData.append('receipt_image', form.receiptFile)

    await uploadTransparencyLog(props.campaign.id, formData)
    toastStore.triggerToast('گزارش شفافیت با موفقیت ثبت شد.', 'success')
    resetTransparencyForm()
    // Emit to parent to refresh campaign data
    emit('transparency-uploaded')
  } catch (err: any) {
    const msg = err?.response?.data?.error || err?.response?.data?.detail || 'خطا در ثبت گزارش شفافیت'
    toastStore.triggerToast(String(msg), 'error')
  } finally {
    transparencySubmitting.value = false
  }
}

// Payout modal & request state
const isPayoutModalOpen = ref(false)
const payoutSubmitting = ref(false)
const payoutHistoryLoading = ref(false)
const payoutHistory = ref<PayoutRequestItem[]>([])
const payoutForm = ref({
  amount: null as number | null,
  iban: '',
  account_holder_name: '',
})

const availablePayoutBalance = computed(() => {
  if (typeof props.campaign.availablePayoutBalance === 'number') {
    return props.campaign.availablePayoutBalance
  }
  return Math.max(0, (props.campaign.collectedAmount || 0) - (props.campaign.totalSettledAmount || 0))
})

const openPayoutModal = async () => {
  isPayoutModalOpen.value = true
  payoutForm.value = {
    amount: availablePayoutBalance.value > 0 ? availablePayoutBalance.value : null,
    iban: props.campaign.iban || '',
    account_holder_name: props.campaign.authorName || '',
  }
  await loadPayoutHistory()
}

const fillMaxPayoutAmount = () => {
  payoutForm.value.amount = availablePayoutBalance.value
}

const loadPayoutHistory = async () => {
  payoutHistoryLoading.value = true
  try {
    const res = await fetchCampaignPayouts(props.campaign.id)
    payoutHistory.value = res.data?.results || []
  } catch (err) {
    console.warn('Could not load payout history:', err)
  } finally {
    payoutHistoryLoading.value = false
  }
}

const submitPayoutRequest = async () => {
  const form = payoutForm.value
  if (!form.amount || form.amount < 10000) {
    toastStore.triggerToast('حداقل مبلغ قابل تسویه ۱۰,۰۰۰ تومان است.', 'error')
    return
  }
  if (form.amount > availablePayoutBalance.value) {
    toastStore.triggerToast('مبلغ درخواستی بیشتر از موجودی قابل تسویه است.', 'error')
    return
  }
  if (!form.iban.trim()) {
    toastStore.triggerToast('شماره شبا الزامی است.', 'error')
    return
  }
  if (!form.account_holder_name.trim()) {
    toastStore.triggerToast('نام و نام خانوادگی صاحب حساب الزامی است.', 'error')
    return
  }

  payoutSubmitting.value = true
  try {
    await requestCampaignPayout(props.campaign.id, {
      amount: form.amount,
      iban: form.iban.trim(),
      account_holder_name: form.account_holder_name.trim(),
    })
    toastStore.triggerToast('درخواست تسویه با موفقیت ثبت شد و در نوبت بررسی قرار گرفت.', 'success')
    await loadPayoutHistory()
    emit('payout-requested')
  } catch (err: any) {
    const msg = err?.response?.data?.amount || err?.response?.data?.iban || err?.response?.data?.detail || err?.response?.data?.error || 'خطا در ثبت درخواست تسویه'
    toastStore.triggerToast(Array.isArray(msg) ? msg[0] : String(msg), 'error')
  } finally {
    payoutSubmitting.value = false
  }
}

watch(
  () => props.campaign.id,
  () => {
    currentMediaIndex.value = 0
    activeTab.value = defaultTab.value
  }
)

const selectMedia = (idx: number) => {
  if (props.campaign.mediaGallery && idx < props.campaign.mediaGallery.length) {
    currentMediaIndex.value = idx
  }
}

const completionPercentage = computed(() => {
  if (!props.campaign.targetAmount || props.campaign.targetAmount <= 0) return 0
  const pct = Math.round((props.campaign.collectedAmount / props.campaign.targetAmount) * 100)
  return Math.min(100, Math.max(0, pct))
})

const remainingAmount = computed(() => {
  return Math.max(0, (props.campaign.targetAmount || 0) - (props.campaign.collectedAmount || 0))
})

const categoryLabel = computed(() =>
  getCampaignCategoryLabel(props.campaign.category, languageStore.isFa)
)

const statusConfig = computed(() =>
  getCampaignStatusConfig(props.campaign.status, languageStore.isFa)
)

const isCampaignEnded = computed(() => {
  if (props.campaign.isEnded) return true
  if (['completed', 'expired', 'inactive'].includes(props.campaign.status)) return true
  if (props.campaign.deadline && new Date(props.campaign.deadline).getTime() < Date.now()) return true
  if (props.campaign.targetAmount && props.campaign.collectedAmount >= props.campaign.targetAmount) return true
  return false
})

const canRequestPayout = computed(() => {
  if (!props.campaign.canEdit) return false
  if (availablePayoutBalance.value <= 0) return false
  if (typeof props.campaign.canRequestPayout === 'boolean') {
    return props.campaign.canRequestPayout
  }
  return isCampaignEnded.value
})

const daysRemaining = computed(() => getCampaignDaysRemaining(props.campaign.deadline))

const formattedDeadline = computed(() => {
  if (!props.campaign.deadline) return null
  const dt = new Date(props.campaign.deadline)
  if (Number.isNaN(dt.getTime())) return null
  return dt.toLocaleDateString(languageStore.isFa ? 'fa-IR' : 'en-US')
})

const totalTransparencyCost = computed(() => {
  if (!props.campaign.transparency?.costBreakdown) return 0
  return Object.values(props.campaign.transparency.costBreakdown).reduce((acc, curr) => acc + curr, 0)
})

const hasDonations = computed(() =>
  Boolean(
    (props.campaign.donorsCount && props.campaign.donorsCount > 0) ||
      (props.campaign.collectedAmount && props.campaign.collectedAmount > 0) ||
      (props.campaign.recentDonors && props.campaign.recentDonors.length > 0)
  )
)
</script>

<template>
  <div
    class="flex flex-col gap-4 w-full pb-28 text-start font-sans animate-in fade-in slide-in-from-bottom-2 duration-250"
    :dir="languageStore.dir"
  >
    <!-- 1. HERO MEDIA BANNER (Flutter CampaignDetailScreen Style) -->
    <div class="relative w-full aspect-[16/10] sm:aspect-[16/9] rounded-2xl overflow-hidden border border-border/60 bg-gradient-to-br from-primary/10 via-primary/5 to-muted/60 shadow-xs">
      <img
        v-if="campaign.mediaGallery && campaign.mediaGallery.length > 0"
        :src="campaign.mediaGallery[currentMediaIndex] || campaign.mediaGallery[0]"
        :alt="campaign.title"
        class="size-full object-cover"
      />
      <div v-else class="size-full flex flex-col items-center justify-center gap-2 text-primary/65">
        <HandHeartIcon class="size-12 stroke-[1.5]" />
        <span class="text-xs font-semibold text-muted-foreground">
          {{ categoryLabel }}
        </span>
      </div>

      <div
        v-if="campaign.mediaGallery && campaign.mediaGallery.length > 0"
        class="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/65 via-black/20 to-transparent pointer-events-none"
      />

      <!-- Status Pill -->
      <Badge
        :variant="statusConfig.variant"
        class="absolute top-3 start-3 rounded-xl text-[11px] px-2.5 py-1 font-bold backdrop-blur-md shadow-xs border border-border/40"
        :class="
          statusConfig.variant === 'secondary'
            ? 'bg-background/90 text-foreground'
            : ''
        "
      >
        <CheckCircle2Icon
          v-if="campaign.status === 'completed' || campaign.status === 'executed'"
          class="size-3.5 shrink-0"
          data-icon="inline-start"
        />
        <BanIcon v-else-if="campaign.status === 'inactive'" class="size-3.5 shrink-0" data-icon="inline-start" />
        <span>{{ statusConfig.label }}</span>
      </Badge>

      <!-- Category & Remaining Days Pills -->
      <div class="absolute top-3 end-3 flex items-center gap-1.5">
        <span
          v-if="daysRemaining !== null && campaign.status === 'active'"
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-black/65 text-white backdrop-blur-md text-[10.5px] font-bold"
        >
          <ClockIcon class="size-3 shrink-0" />
          <span>
            {{ formatKindnessNumber(daysRemaining, languageStore.isFa) }}
            {{ languageStore.t('روز مانده', 'days left') }}
          </span>
        </span>
      </div>

      <!-- Multi-Image Thumbnail Switcher -->
      <div
        v-if="campaign.mediaGallery && campaign.mediaGallery.length > 1"
        class="absolute bottom-2.5 inset-x-3 flex items-center justify-center gap-1.5 p-1 bg-background/85 backdrop-blur-md rounded-xl max-w-fit mx-auto border border-border/50"
      >
        <button
          v-for="(img, idx) in campaign.mediaGallery.slice(0, 5)"
          :key="idx"
          type="button"
          @click="selectMedia(idx)"
          :class="
            cn(
              'size-7 rounded-lg overflow-hidden border transition-all cursor-pointer',
              idx === currentMediaIndex
                ? 'border-primary ring-2 ring-primary/70 scale-105'
                : 'border-border/40 opacity-75 hover:opacity-100'
            )
          "
        >
          <img :src="img" :alt="`تصویر ${idx + 1}`" class="size-full object-cover" />
        </button>
      </div>
    </div>

    <!-- 2. TITLE, TOPIC/ORGANIZER METADATA & ACTIONS -->
    <Card class="rounded-2xl border border-border/70 bg-card/95 backdrop-blur-md shadow-xs py-0 gap-0">
      <CardContent class="p-4 flex flex-col gap-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <Badge variant="outline" class="rounded-lg text-[11px] px-2.5 py-0.5 font-semibold bg-muted/40 border-border/60">
            {{ categoryLabel }}
          </Badge>

          <div class="flex items-center gap-1.5">
            <Button
              v-if="canRequestPayout"
              type="button"
              variant="outline"
              size="sm"
              class="h-8 px-2.5 rounded-xl text-[11px] font-semibold gap-1 text-foreground border-border/70 hover:bg-muted/50 cursor-pointer"
              @click="openPayoutModal"
            >
              <CreditCardIcon class="size-3.5" />
              <span>{{ languageStore.t('تسویه حساب', 'Payout') }}</span>
            </Button>

            <Button
              v-if="campaign.canEdit && campaign.status !== 'inactive'"
              type="button"
              variant="outline"
              size="sm"
              class="h-8 px-2.5 rounded-xl text-[11px] font-semibold gap-1 text-primary border-border/60 cursor-pointer"
              @click="emit('edit-click', campaign.id)"
            >
              <PencilIcon class="size-3.5" />
              <span>{{ languageStore.t('ویرایش', 'Edit') }}</span>
            </Button>

            <Button
              v-if="campaign.canEdit && campaign.status !== 'inactive'"
              type="button"
              variant="outline"
              size="sm"
              class="h-8 px-2.5 rounded-xl text-[11px] font-semibold gap-1 text-destructive border-destructive/30 hover:bg-destructive/10 cursor-pointer"
              @click="emit('delete-click', campaign.id)"
            >
              <Trash2Icon class="size-3.5" />
              <span>{{ hasDonations ? languageStore.t('توقف', 'Stop') : languageStore.t('حذف', 'Delete') }}</span>
            </Button>

            <Button
              type="button"
              variant="outline"
              size="icon"
              class="size-8 rounded-xl border-border/60 text-muted-foreground hover:text-foreground cursor-pointer"
              :title="languageStore.t('اشتراک‌گذاری لینک', 'Share Link')"
              @click="emit('share-click', campaign.id)"
            >
              <Share2Icon class="size-3.5" />
            </Button>
          </div>
        </div>

        <h1 class="text-base sm:text-lg font-extrabold text-foreground leading-snug">
          {{ campaign.title }}
        </h1>

        <div class="flex flex-wrap items-center gap-x-4 gap-y-2 pt-2 border-t border-border/40 text-xs text-muted-foreground">
          <button
            type="button"
            class="inline-flex items-center gap-1.5 font-semibold text-foreground hover:text-primary transition-colors cursor-pointer"
            @click="emit('topic-click', campaign.topicId)"
          >
            <LayersIcon class="size-3.5 text-primary shrink-0" />
            <span>{{ campaign.topicName }}</span>
          </button>

          <div v-if="campaign.authorName" class="inline-flex items-center gap-1.5">
            <Avatar class="size-5 border border-border/50">
              <AvatarImage v-if="campaign.authorAvatar" :src="campaign.authorAvatar" :alt="campaign.authorName" />
              <AvatarFallback class="bg-primary/10 text-primary text-[9px] font-bold">
                {{ campaign.authorName.charAt(0) }}
              </AvatarFallback>
            </Avatar>
            <span>{{ campaign.authorName }}</span>
          </div>

          <div v-if="campaign.timestamp" class="inline-flex items-center gap-1">
            <ClockIcon class="size-3 text-primary shrink-0" />
            <span>{{ campaign.timestamp }}</span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 3. FUNDING PROGRESS CARD -->
    <Card class="rounded-2xl border border-border/70 bg-card/95 backdrop-blur-md shadow-xs py-0 gap-0">
      <CardContent class="p-4 flex flex-col gap-3">
        <div class="flex items-center justify-between gap-2">
          <span class="text-xs font-bold text-muted-foreground">
            {{ languageStore.t('پیشرفت تامین پویش', 'Campaign Funding Progress') }}
          </span>
          <span class="text-base font-extrabold text-primary">
            {{ formatKindnessNumber(completionPercentage, languageStore.isFa) }}٪
          </span>
        </div>

        <Progress :model-value="completionPercentage" class="h-2 w-full bg-muted rounded-full" />

        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1">
          <div class="p-2.5 rounded-xl bg-muted/35 border border-border/40 flex flex-col gap-0.5">
            <span class="text-[10.5px] text-muted-foreground">
              {{ languageStore.t('جمع‌آوری شده', 'Raised') }}
            </span>
            <span class="text-xs font-extrabold text-primary">
              {{ formatKindnessNumber(campaign.collectedAmount, languageStore.isFa) }}
              <span class="text-[10px] font-normal text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
            </span>
          </div>

          <div class="p-2.5 rounded-xl bg-muted/35 border border-border/40 flex flex-col gap-0.5">
            <span class="text-[10.5px] text-muted-foreground">
              {{ languageStore.t('مبلغ هدف', 'Goal') }}
            </span>
            <span class="text-xs font-extrabold text-foreground">
              {{ formatKindnessNumber(campaign.targetAmount, languageStore.isFa) }}
              <span class="text-[10px] font-normal text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
            </span>
          </div>

          <div class="col-span-2 sm:col-span-1 p-2.5 rounded-xl bg-muted/35 border border-border/40 flex flex-col gap-0.5">
            <span class="text-[10.5px] text-muted-foreground">
              {{ languageStore.t('تعداد حامیان', 'Supporters') }}
            </span>
            <span class="text-xs font-extrabold text-foreground inline-flex items-center gap-1">
              <UsersIcon class="size-3.5 text-primary shrink-0" />
              <span>{{ formatKindnessNumber(campaign.donorsCount, languageStore.isFa) }} {{ languageStore.t('نفر', 'donors') }}</span>
            </span>
          </div>
        </div>

        <div
          v-if="remainingAmount > 0 && campaign.status === 'active'"
          class="text-[11px] text-muted-foreground flex items-center justify-between pt-1 border-t border-border/30"
        >
          <span>{{ languageStore.t('مبلغ باقی‌مانده تا تحقق هدف:', 'Remaining to reach goal:') }}</span>
          <span class="font-bold text-foreground">
            {{ formatKindnessNumber(remainingAmount, languageStore.isFa) }}
            {{ languageStore.t('تومان', 'Toman') }}
          </span>
        </div>
      </CardContent>
    </Card>

    <!-- 4. DETAILED TABS (Intro / Supporters / Transparency Report) -->
    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="grid w-full grid-cols-3 bg-muted/70 p-1 rounded-2xl h-10 border border-border/40">
        <TabsTrigger value="overview" class="text-xs font-bold h-8 rounded-xl cursor-pointer">
          {{ languageStore.t('معرفی پویش', 'Overview') }}
        </TabsTrigger>
        <TabsTrigger value="donors" class="text-xs font-bold h-8 rounded-xl cursor-pointer">
          {{ languageStore.t('حامیان', 'Supporters') }} ({{ formatKindnessNumber(campaign.donorsCount, languageStore.isFa) }})
        </TabsTrigger>
        <TabsTrigger value="transparency" class="text-xs font-bold h-8 rounded-xl cursor-pointer">
          {{ languageStore.t('شفافیت', 'Transparency') }}
        </TabsTrigger>
      </TabsList>

      <!-- Tab 1: Overview & Details -->
      <TabsContent value="overview" class="pt-3 focus-visible:outline-none">
        <Card class="rounded-2xl border border-border/60 bg-card/90 py-0 gap-0">
          <CardContent class="p-4 flex flex-col gap-3">
            <p class="text-xs sm:text-[13px] text-foreground/90 leading-7 whitespace-pre-line">
              {{ campaign.description }}
            </p>

            <div
              v-if="formattedDeadline || campaign.iban"
              class="pt-3 border-t border-border/40 flex flex-col gap-2 text-xs text-muted-foreground"
            >
              <div v-if="formattedDeadline" class="flex items-center justify-between">
                <span class="inline-flex items-center gap-1.5">
                  <CalendarIcon class="size-3.5 text-primary shrink-0" />
                  <span>{{ languageStore.t('مهلت پویش:', 'Deadline:') }}</span>
                </span>
                <span class="font-semibold text-foreground">{{ formattedDeadline }}</span>
              </div>
              <div v-if="campaign.iban" class="flex items-center justify-between gap-2">
                <span>{{ languageStore.t('شماره شبا:', 'IBAN:') }}</span>
                <span dir="ltr" class="font-mono text-[11px] font-semibold text-foreground">{{ campaign.iban }}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Tab 2: Supporters List -->
      <TabsContent value="donors" class="pt-3 focus-visible:outline-none">
        <div v-if="campaign.recentDonors && campaign.recentDonors.length > 0" class="flex flex-col gap-2">
          <div
            v-for="donor in campaign.recentDonors"
            :key="donor.id"
            class="flex items-center justify-between p-3 rounded-2xl bg-card/90 border border-border/60 text-xs shadow-2xs"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <Avatar class="size-8 border border-border/50 shrink-0">
                <AvatarImage v-if="!donor.isAnonymous && donor.avatarUrl" :src="donor.avatarUrl" :alt="donor.name" />
                <AvatarFallback class="bg-primary/10 text-primary font-bold text-[10px]">
                  <UserIcon v-if="donor.isAnonymous" class="size-3.5 text-muted-foreground" />
                  <span v-else>{{ donor.name.substring(0, 2) }}</span>
                </AvatarFallback>
              </Avatar>
              <div class="flex flex-col min-w-0">
                <span class="font-bold text-foreground text-xs truncate">
                  {{ donor.isAnonymous ? languageStore.t('کاربر ناشناس', 'Anonymous') : donor.name }}
                </span>
                <span class="text-[10px] text-muted-foreground">{{ donor.donatedAt }}</span>
              </div>
            </div>
            <div class="font-extrabold text-primary shrink-0 text-xs">
              {{ formatKindnessNumber(donor.amount, languageStore.isFa) }}
              <span class="text-[10px] font-normal text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
            </div>
          </div>
        </div>
        <div
          v-else
          class="py-8 text-center text-muted-foreground text-xs bg-card/60 rounded-2xl border border-dashed border-border/60"
        >
          {{ languageStore.t('هنوز مشارکتی برای این پویش ثبت نشده است.', 'No supporters recorded yet.') }}
        </div>
      </TabsContent>

      <!-- Tab 3: Transparency Report -->
      <TabsContent value="transparency" class="pt-3 focus-visible:outline-none flex flex-col gap-3">
        <!-- Transparency Upload Form (for campaign creator / staff) -->
        <Card v-if="canUploadTransparency" class="rounded-2xl border border-primary/30 bg-primary/5 py-0 gap-0">
          <CardContent class="p-4 flex flex-col gap-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-foreground flex items-center gap-1.5">
                <UploadIcon class="size-4 text-primary" />
                {{ languageStore.t('ثبت گزارش شفافیت', 'Upload Transparency Log') }}
              </span>
              <Button
                v-if="!showTransparencyForm"
                type="button"
                variant="outline"
                size="sm"
                class="h-7 px-2.5 rounded-lg text-[11px] font-semibold gap-1 text-primary border-primary/40 cursor-pointer"
                @click="showTransparencyForm = true"
              >
                <PlusCircleIcon class="size-3.5" />
                {{ languageStore.t('ثبت جدید', 'New Log') }}
              </Button>
            </div>

            <div v-if="showTransparencyForm" class="flex flex-col gap-2.5 pt-1 border-t border-primary/20">
              <input
                v-model="transparencyForm.title"
                type="text"
                :placeholder="languageStore.t('عنوان هزینه (مثلاً: خرید مصالح)', 'Expense title')"
                class="w-full h-9 px-3 rounded-xl border border-border/60 bg-background text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
              <textarea
                v-model="transparencyForm.description"
                :placeholder="languageStore.t('توضیحات (اختیاری)', 'Description (optional)')"
                rows="2"
                class="w-full px-3 py-2 rounded-xl border border-border/60 bg-background text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
              />
              <div class="flex items-center gap-2">
                <input
                  v-model.number="transparencyForm.amount"
                  type="number"
                  min="1"
                  :placeholder="languageStore.t('مبلغ (تومان)', 'Amount (Toman)')"
                  class="flex-1 h-9 px-3 rounded-xl border border-border/60 bg-background text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                <span class="text-[10px] text-muted-foreground shrink-0">{{ languageStore.t('تومان', 'Toman') }}</span>
              </div>
              <div class="flex items-center gap-2">
                <input
                  ref="transparencyFileInputRef"
                  type="file"
                  accept="image/*"
                  class="flex-1 text-[11px] text-muted-foreground file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-[11px] file:font-semibold file:bg-primary/10 file:text-primary file:cursor-pointer"
                  @change="onTransparencyFileSelect"
                />
              </div>
              <div class="flex items-center gap-2 pt-1">
                <Button
                  type="button"
                  variant="default"
                  size="sm"
                  class="h-8 px-4 rounded-xl text-[11px] font-bold gap-1.5 cursor-pointer"
                  :disabled="transparencySubmitting"
                  @click="submitTransparencyLog"
                >
                  <Loader2Icon v-if="transparencySubmitting" class="size-3.5 animate-spin" />
                  <UploadIcon v-else class="size-3.5" />
                  {{ transparencySubmitting ? languageStore.t('در حال ارسال...', 'Submitting...') : languageStore.t('ثبت گزارش', 'Submit') }}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  class="h-8 px-3 rounded-xl text-[11px] text-muted-foreground cursor-pointer"
                  @click="resetTransparencyForm"
                  :disabled="transparencySubmitting"
                >
                  {{ languageStore.t('انصراف', 'Cancel') }}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <template v-if="campaign.transparency && campaign.transparency.isAvailable">
          <Card class="rounded-2xl border border-border/60 bg-card/90 py-0 gap-0">
            <CardContent class="p-4 flex flex-col gap-3 text-xs">
              <div class="flex items-center justify-between font-bold text-foreground">
                <span class="flex items-center gap-1.5">
                  <CheckCircle2Icon class="size-4 text-primary shrink-0" />
                  {{ languageStore.t('گزارش رسمی اجرای پویش', 'Official Execution Report') }}
                </span>
                <span v-if="campaign.transparency.executedAt" class="font-normal text-muted-foreground text-[10.5px]">
                  {{ campaign.transparency.executedAt }}
                </span>
              </div>
              <p class="text-muted-foreground leading-relaxed whitespace-pre-line">
                {{ campaign.transparency.description }}
              </p>

              <div v-if="campaign.transparency.costBreakdown && Object.keys(campaign.transparency.costBreakdown).length > 0" class="flex flex-col gap-1.5 pt-1">
                <span class="font-bold text-foreground text-xs flex items-center gap-1">
                  <FileTextIcon class="size-3.5 text-primary" />
                  {{ languageStore.t('ریز هزینه‌ها:', 'Cost Breakdown:') }}
                </span>
                <div class="rounded-xl border border-border/50 overflow-hidden text-xs">
                  <table class="w-full text-start border-collapse">
                    <thead>
                      <tr class="bg-muted/70 text-muted-foreground border-b border-border/50 font-semibold text-[11px]">
                        <th class="p-2">{{ languageStore.t('شرح هزینه', 'Item') }}</th>
                        <th class="p-2 text-end">{{ languageStore.t('مبلغ (تومان)', 'Amount') }}</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-border/30">
                      <tr v-for="(cost, item) in campaign.transparency.costBreakdown" :key="item">
                        <td class="p-2 text-foreground font-medium">{{ item }}</td>
                        <td class="p-2 text-end font-bold text-primary">
                          {{ formatKindnessNumber(cost, languageStore.isFa) }}
                        </td>
                      </tr>
                      <tr class="bg-muted/40 font-bold border-t border-border/60">
                        <td class="p-2 text-foreground">{{ languageStore.t('جمع کل', 'Total') }}</td>
                        <td class="p-2 text-end text-primary">
                          {{ formatKindnessNumber(totalTransparencyCost, languageStore.isFa) }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div v-if="campaign.transparency.receiptImages && campaign.transparency.receiptImages.length > 0" class="flex flex-col gap-2 pt-1">
                <span class="font-bold text-foreground text-xs flex items-center gap-1">
                  <ImageIcon class="size-3.5 text-primary" />
                  {{ languageStore.t('تصاویر فاکتورها و مستندات:', 'Receipts & Invoices:') }}
                </span>
                <div class="grid grid-cols-3 gap-2">
                  <div
                    v-for="(receipt, idx) in campaign.transparency.receiptImages"
                    :key="idx"
                    class="relative aspect-square rounded-xl overflow-hidden border border-border/50 group cursor-pointer"
                    @click="emit('transparency-click', idx, receipt)"
                  >
                    <img :src="receipt" :alt="`فاکتور ${idx + 1}`" class="size-full object-cover transition-transform group-hover:scale-105" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </template>

        <div
          v-else
          class="py-8 px-4 text-center text-muted-foreground text-xs bg-card/60 rounded-2xl border border-dashed border-border/60"
        >
          {{ languageStore.t('اسناد و فاکتورهای شفافیت پس از اجرا و تکمیل طرح در این بخش بارگذاری می‌شود.', 'Transparency logs and receipts will be published here once executed.') }}
        </div>
      </TabsContent>
    </Tabs>

    <!-- 5. STICKY BOTTOM DONATION BAR (Flutter CampaignDetailScreen Style) -->
    <div class="fixed bottom-0 left-1/2 -translate-x-1/2 z-40 w-full max-w-[500px] bg-background/85 backdrop-blur-md border-t border-border/60 px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      <Button
        v-if="campaign.status === 'active'"
        type="button"
        variant="default"
        size="lg"
        class="w-full h-11 rounded-xl text-xs sm:text-sm font-bold shadow-md shadow-primary/15 active:scale-[0.985] transition-all cursor-pointer gap-2"
        @click="emit('donate-click', campaign.id)"
      >
        <HeartIcon class="size-4 fill-current shrink-0" />
        <span>{{ languageStore.t('مشارکت در این مهربانی', 'Support This Campaign') }}</span>
      </Button>

      <div
        v-else
        class="w-full h-10 rounded-xl bg-muted/70 border border-border/50 flex items-center justify-center gap-2 text-xs font-bold text-muted-foreground"
      >
        <BanIcon v-if="campaign.status === 'inactive'" class="size-4 text-destructive shrink-0" />
        <CheckCircle2Icon v-else class="size-4 text-primary shrink-0" />
        <span>{{ statusConfig.label }}</span>
      </div>
    </div>

    <!-- 6. PAYOUT & SETTLEMENT DIALOG -->
    <Dialog v-model:open="isPayoutModalOpen">
      <DialogContent class="max-w-[480px] p-5 rounded-2xl max-h-[85vh] overflow-y-auto font-sans" :dir="languageStore.dir">
        <DialogHeader class="text-start pb-2 border-b border-border/50">
          <div class="flex items-center gap-2">
            <div class="p-2 rounded-xl bg-muted/60 text-foreground">
              <WalletIcon class="size-5" />
            </div>
            <div>
              <DialogTitle class="text-sm sm:text-base font-extrabold text-foreground">
                {{ languageStore.t('تسویه حساب و واریز وجوه', 'Payout & Settlement') }}
              </DialogTitle>
              <DialogDescription class="text-xs text-muted-foreground mt-0.5">
                {{ languageStore.t('درخواست انتقال مبالغ جمع‌آوری‌شده به حساب بانکی', 'Request transfer of collected funds to your bank account') }}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <!-- Balance Summary Card -->
        <div class="grid grid-cols-3 gap-2 my-3">
          <div class="p-2.5 rounded-xl bg-muted/40 border border-border/60 flex flex-col gap-0.5 text-start">
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('قابل تسویه', 'Available') }}</span>
            <span class="text-xs font-extrabold text-foreground">
              {{ formatKindnessNumber(availablePayoutBalance, languageStore.isFa) }}
            </span>
            <span class="text-[9px] text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
          </div>

          <div class="p-2.5 rounded-xl bg-muted/40 border border-border/40 flex flex-col gap-0.5 text-start">
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('کل جمع‌آوری', 'Total Raised') }}</span>
            <span class="text-xs font-extrabold text-foreground">
              {{ formatKindnessNumber(campaign.collectedAmount, languageStore.isFa) }}
            </span>
            <span class="text-[9px] text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
          </div>

          <div class="p-2.5 rounded-xl bg-muted/40 border border-border/40 flex flex-col gap-0.5 text-start">
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('تسویه‌شده', 'Settled') }}</span>
            <span class="text-xs font-extrabold text-foreground">
              {{ formatKindnessNumber(campaign.totalSettledAmount || 0, languageStore.isFa) }}
            </span>
            <span class="text-[9px] text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
          </div>
        </div>

        <!-- Payout Request Form (Visible if balance > 0) -->
        <div v-if="availablePayoutBalance > 0" class="flex flex-col gap-3 p-3.5 rounded-xl bg-card border border-border/60">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-foreground">
              {{ languageStore.t('ثبت درخواست تسویه جدید', 'New Payout Request') }}
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              class="h-6 px-2 rounded-lg text-[10.5px] font-semibold text-foreground hover:text-foreground/80 cursor-pointer"
              @click="fillMaxPayoutAmount"
            >
              <ArrowDownToLineIcon class="size-3 mr-1" />
              {{ languageStore.t('تسویه کل موجودی', 'Settle Full Balance') }}
            </Button>
          </div>

          <!-- Amount Input -->
          <div class="flex flex-col gap-1 text-start">
            <label class="text-[11px] font-medium text-muted-foreground">
              {{ languageStore.t('مبلغ درخواستی (تومان)', 'Requested Amount (Toman)') }}
            </label>
            <div class="relative">
              <input
                v-model.number="payoutForm.amount"
                type="number"
                min="10000"
                :max="availablePayoutBalance"
                class="w-full h-9 px-3 text-start rounded-xl border border-border/60 bg-background text-xs focus:outline-none focus:ring-2 focus:ring-primary/30"
                :placeholder="languageStore.t('حداقل ۱۰,۰۰۰ تومان', 'Min 10,000 Tomans')"
              />
            </div>
          </div>

          <!-- IBAN Input -->
          <div class="flex flex-col gap-1 text-start">
            <label class="text-[11px] font-medium text-muted-foreground">
              {{ languageStore.t('شماره شبا (بدون IR یا با IR)', 'IBAN (Sheba)') }}
            </label>
            <input
              v-model="payoutForm.iban"
              type="text"
              dir="ltr"
              maxlength="26"
              class="w-full h-9 px-3 font-mono text-xs rounded-xl border border-border/60 bg-background focus:outline-none focus:ring-2 focus:ring-primary/30 text-start"
              placeholder="IR000000000000000000000000"
            />
          </div>

          <!-- Account Holder Name Input -->
          <div class="flex flex-col gap-1 text-start">
            <label class="text-[11px] font-medium text-muted-foreground">
              {{ languageStore.t('نام و نام خانوادگی صاحب حساب', 'Account Holder Full Name') }}
            </label>
            <input
              v-model="payoutForm.account_holder_name"
              type="text"
              class="w-full h-9 px-3 text-xs rounded-xl border border-border/60 bg-background focus:outline-none focus:ring-2 focus:ring-primary/30 text-start"
              :placeholder="languageStore.t('مطابق با کارت بانکی', 'As on bank card')"
            />
          </div>

          <Button
            type="button"
            variant="default"
            size="sm"
            class="h-9 rounded-xl text-xs font-bold gap-1.5 bg-primary hover:bg-primary/90 text-primary-foreground cursor-pointer mt-1"
            :disabled="payoutSubmitting"
            @click="submitPayoutRequest"
          >
            <Loader2Icon v-if="payoutSubmitting" class="size-3.5 animate-spin" />
            <CreditCardIcon v-else class="size-3.5" />
            {{ payoutSubmitting ? languageStore.t('در حال ارسال...', 'Submitting...') : languageStore.t('ارسال درخواست تسویه', 'Submit Request') }}
          </Button>
        </div>

        <div v-else class="p-3 rounded-xl bg-muted/40 border border-border/40 text-center text-xs text-muted-foreground">
          {{ languageStore.t('موجودی قابل تسویه‌ای برای این پویش وجود ندارد.', 'No available balance to settle.') }}
        </div>

        <!-- Payout History Section -->
        <div class="flex flex-col gap-2 pt-2 text-start">
          <span class="text-xs font-bold text-foreground">
            {{ languageStore.t('سوابق تسویه حساب این پویش', 'Payout History') }}
          </span>

          <div v-if="payoutHistoryLoading" class="py-4 text-center text-xs text-muted-foreground">
            <Loader2Icon class="size-4 animate-spin mx-auto text-primary" />
          </div>

          <div v-else-if="payoutHistory.length > 0" class="flex flex-col gap-2">
            <div
              v-for="p in payoutHistory"
              :key="p.id"
              class="p-3 rounded-xl border border-border/50 bg-card/60 flex flex-col gap-1.5 text-xs"
            >
              <div class="flex items-center justify-between">
                <span class="font-extrabold text-foreground">
                  {{ formatKindnessNumber(p.amount, languageStore.isFa) }}
                  <span class="text-[10px] font-normal text-muted-foreground">{{ languageStore.t('تومان', 'Toman') }}</span>
                </span>

                <Badge
                  :variant="
                    p.status === 'completed' ? 'default' :
                    p.status === 'pending' ? 'secondary' :
                    p.status === 'approved' ? 'outline' : 'destructive'
                  "
                  class="text-[10px] px-2 py-0.5 rounded-lg font-semibold"
                  :class="
                    p.status === 'completed' ? 'bg-primary hover:bg-primary/90 text-primary-foreground' :
                    p.status === 'pending' ? 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30' :
                    ''
                  "
                >
                  {{ p.status_display }}
                </Badge>
              </div>

              <div class="flex items-center justify-between text-[11px] text-muted-foreground">
                <span dir="ltr" class="font-mono">{{ p.iban }}</span>
                <span>{{ p.account_holder_name }}</span>
              </div>

              <div v-if="p.tracking_number" class="text-[10.5px] text-foreground flex items-center gap-1 font-semibold">
                <span>{{ languageStore.t('کد پیگیری ساتنا/پایا:', 'Tracking Code:') }}</span>
                <span dir="ltr" class="font-mono">{{ p.tracking_number }}</span>
              </div>

              <div v-if="p.receipt_url" class="pt-0.5">
                <a
                  :href="p.receipt_url"
                  target="_blank"
                  rel="noopener"
                  class="text-[10.5px] text-primary hover:underline font-semibold inline-flex items-center gap-1"
                >
                  <FileTextIcon class="size-3" />
                  {{ languageStore.t('مشاهده فیش واریزی', 'View Bank Receipt') }}
                </a>
              </div>

              <div v-if="p.rejection_reason && p.status === 'rejected'" class="text-[10.5px] text-destructive flex items-center gap-1">
                <AlertCircleIcon class="size-3 shrink-0" />
                <span>{{ p.rejection_reason }}</span>
              </div>
            </div>
          </div>

          <div v-else class="py-4 text-center text-xs text-muted-foreground">
            {{ languageStore.t('تاکنون درخواست تسویه‌ای برای این پویش ثبت نشده است.', 'No payout requests yet.') }}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

