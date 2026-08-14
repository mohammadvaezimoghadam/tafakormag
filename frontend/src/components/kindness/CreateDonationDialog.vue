<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import type { 
  CampaignCategory, 
  CreateDonationFormState, 
  CreateDonationPayload, 
  CreateDonationMediaFile 
} from '@/types/kindness'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectGroup,
  SelectItem
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { 
  toPersianDigits, 
  toEnglishDigits 
} from '@/utils/persianNumbers'
import { useLanguageStore } from '@/stores/languageStore'
import { cn } from '@/lib/utils'
import { 
  HeartIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon, 
  UploadCloudIcon, 
  XIcon, 
  ImageIcon, 
  VideoIcon, 
  PinIcon, 
  CalendarIcon, 
  SendIcon,
  CheckIcon
} from '@lucide/vue'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  open?: boolean
  isInline?: boolean
  topicId?: string | number
  topicName?: string
  authorName?: string
  authorAvatar?: string
  isEditMode?: boolean
  initialData?: {
    id?: string | number
    title?: string
    category?: CampaignCategory
    targetAmount?: number | null
    description?: string
    autoPin?: boolean
    deadline?: string | null
    mediaUrl?: string
  } | null
}>(), {
  open: false,
  isInline: false,
  topicId: 'topic-1',
  topicName: 'تاپیک عمومی',
  authorName: 'مدیر تاپیک',
  authorAvatar: undefined,
  isEditMode: false,
  initialData: null
})

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'created', payload: CreateDonationPayload): void
  (e: 'updated', payload: CreateDonationPayload & { id?: string | number }): void
}>()

// Wizard active step: 1 | 2 | 3
const currentStep = ref<1 | 2 | 3>(1)

// Form reactive state
const formState = reactive<CreateDonationFormState>({
  title: '',
  category: 'mosque',
  targetAmount: null,
  description: '',
  mediaFiles: [],
  autoPin: true,
  deadline: null
})

// Amount formatted input string
const rawAmountInput = ref('')

// Predefined Category list with Persian labels
const CATEGORIES: Array<{ value: CampaignCategory; label: string }> = [
  { value: 'mosque', label: 'مسجد و اماکن مذهبی' },
  { value: 'school', label: 'مدرسه و آموزش' },
  { value: 'health', label: 'درمانی و سلامت' },
  { value: 'livelihood', label: 'نیازمندان و معیشت' },
  { value: 'construction', label: 'عمرانی و تجهیزات' },
  { value: 'other', label: 'متفرقه و عمومی' }
]

// Preset target amounts for quick selection (in Tomans)
const PRESET_AMOUNTS = [
  { amount: 5000000, label: '۵ میلیون' },
  { amount: 15000000, label: '۱۵ میلیون' },
  { amount: 30000000, label: '۳۰ میلیون' },
  { amount: 50000000, label: '۵۰ میلیون' }
]

// Deadline Presets
const DEADLINE_PRESETS = [
  { value: '7_days', label: '۷ روزه' },
  { value: '14_days', label: '۱۴ روزه' },
  { value: '30_days', label: '۳۰ روزه' },
  { value: 'none', label: 'بدون مهلت' }
]
const selectedDeadlinePreset = ref<string>('none')


// Handle Amount Input formatting with commas
const handleAmountInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  const digitsOnly = toEnglishDigits(target.value).replace(/[^0-9]/g, '')
  
  if (!digitsOnly) {
    formState.targetAmount = null
    rawAmountInput.value = ''
    return
  }

  const num = parseInt(digitsOnly, 10)
  formState.targetAmount = num
  rawAmountInput.value = new Intl.NumberFormat('fa-IR').format(num)
}

const selectPresetAmount = (amt: number) => {
  if (formState.targetAmount === amt) {
    formState.targetAmount = null
    rawAmountInput.value = ''
    return
  }
  formState.targetAmount = amt
  rawAmountInput.value = amt ? new Intl.NumberFormat('fa-IR').format(amt) : ''
}

// Deadline selection handler
watch(selectedDeadlinePreset, (newVal) => {
  if (!newVal || newVal === 'none') {
    formState.deadline = null
  } else {
    const matched = DEADLINE_PRESETS.find(p => p.value === newVal)
    formState.deadline = matched ? matched.label : null
  }
})

// Validation per step
const isStep1Valid = computed(() => {
  return (
    formState.title.trim().length > 0 &&
    formState.title.length <= 80 &&
    formState.targetAmount !== null &&
    formState.targetAmount > 0 &&
    !!formState.category
  )
})

const isStep2Valid = computed(() => {
  return formState.description.trim().length >= 15
})

const isStep3Valid = computed(() => {
  return isStep1Valid.value && isStep2Valid.value
})

// Step Navigation
const nextStep = () => {
  if (currentStep.value === 1 && isStep1Valid.value) {
    currentStep.value = 2
  } else if (currentStep.value === 2 && isStep2Valid.value) {
    currentStep.value = 3
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value = (currentStep.value - 1) as 1 | 2 | 3
  }
}

// File Upload & Drag-and-Drop Handling
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFilesSelected = (files: FileList | null) => {
  if (!files || files.length === 0) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (!file) continue
    const isVideo = file.type.startsWith('video/')
    const previewUrl = URL.createObjectURL(file)

    const mediaFile: CreateDonationMediaFile = {
      id: `media_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      file,
      previewUrl,
      isVideo
    }

    formState.mediaFiles.push(mediaFile)
  }
}

const onFileInputChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  handleFilesSelected(target.files)
  if (target) target.value = ''
}

const onDrop = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer?.files) {
    handleFilesSelected(e.dataTransfer.files)
  }
}

const removeMediaFile = (id: string) => {
  const idx = formState.mediaFiles.findIndex(m => m.id === id)
  if (idx !== -1) {
    const item = formState.mediaFiles[idx]
    if (item?.previewUrl) {
      URL.revokeObjectURL(item.previewUrl)
    }
    formState.mediaFiles.splice(idx, 1)
  }
}

// Reset form
const resetForm = () => {
  formState.title = ''
  formState.category = 'mosque'
  formState.targetAmount = null
  formState.description = ''
  // Clean up object URLs
  formState.mediaFiles.forEach(m => {
    if (m.previewUrl) URL.revokeObjectURL(m.previewUrl)
  })
  formState.mediaFiles = []
  formState.autoPin = true
  formState.deadline = null
  selectedDeadlinePreset.value = 'none'
  rawAmountInput.value = ''
  currentStep.value = 1
}

const populateFromInitialData = () => {
  if (props.isEditMode && props.initialData) {
    formState.title = props.initialData.title || ''
    formState.category = props.initialData.category || 'mosque'
    formState.targetAmount = props.initialData.targetAmount ?? null
    rawAmountInput.value = formState.targetAmount ? new Intl.NumberFormat('fa-IR').format(formState.targetAmount) : ''
    formState.description = props.initialData.description || ''
    formState.autoPin = props.initialData.autoPin ?? true
    formState.deadline = props.initialData.deadline || null
    if (props.initialData.deadline) {
      const match = DEADLINE_PRESETS.find(p => p.label === props.initialData?.deadline || p.value === props.initialData?.deadline)
      selectedDeadlinePreset.value = match ? match.value : 'none'
    } else {
      selectedDeadlinePreset.value = 'none'
    }
  }
}

watch(() => [props.open, props.isEditMode, props.initialData], ([isOpen]) => {
  if (isOpen) {
    if (props.isEditMode && props.initialData) {
      populateFromInitialData()
    }
  } else if (!props.isInline) {
    resetForm()
  }
}, { immediate: true, deep: true })

const handleClose = () => {
  emit('update:open', false)
}

// Final Submit
const handleSubmit = () => {
  if (!isStep3Valid.value) return

  const payload: CreateDonationPayload = {
    topic_id: props.topicId,
    title: formState.title.trim(),
    category: formState.category,
    target_amount: formState.targetAmount || 0,
    description: formState.description.trim(),
    media_files: formState.mediaFiles.map(m => m.file),
    auto_pin: formState.autoPin,
    deadline: formState.deadline
  }

  if (props.isEditMode) {
    emit('updated', { ...payload, id: props.initialData?.id })
  } else {
    emit('created', payload)
  }
  emit('update:open', false)
  resetForm()
}
</script>

<template>
  <!-- Inline Mode Container (Mobile First) -->
  <div 
    v-if="isInline"
    class="w-full max-w-[420px] overflow-hidden rounded-3xl p-0 border border-border/80 bg-card text-card-foreground shadow-xs flex flex-col text-start font-sans"
    :dir="languageStore.dir"
  >
    <!-- Minimalist Dialog Header -->
    <div class="px-4 py-3.5 border-b border-border/40 shrink-0 bg-muted/20 flex flex-col gap-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 shadow-xs">
            <HeartIcon class="size-4 fill-primary/20" />
          </div>
          <div class="flex flex-col min-w-0">
            <h2 class="text-sm font-bold text-foreground truncate">
              {{ isEditMode ? languageStore.t('ویرایش پویش مهربانی', 'Edit Kindness Campaign') : languageStore.t('ایجاد پویش مهربانی', 'New Kindness Campaign') }}
            </h2>
            <p class="text-xs text-muted-foreground truncate">
              {{ languageStore.t('پویش مالی جمعی درون تاپیک', 'Crowdfunding campaign in topic') }}
            </p>
          </div>
        </div>

        <Badge variant="outline" class="text-xs px-2.5 py-0.5 rounded-full font-bold">
          {{ toPersianDigits(currentStep) }} / {{ toPersianDigits(3) }}
        </Badge>
      </div>

      <!-- Sleek Minimal Wizard Step Indicator -->
      <div class="grid grid-cols-3 gap-2 pt-0.5">
        <!-- Step 1 -->
        <button
          type="button"
          :class="cn(
            'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer select-none',
            currentStep === 1 
              ? 'border-primary bg-primary/10 text-primary font-bold shadow-xs' 
              : isStep1Valid 
                ? 'border-border/50 bg-muted/40 text-foreground hover:bg-muted/60' 
                : 'border-border/30 bg-muted/15 text-muted-foreground/60'
          )"
          @click="currentStep = 1"
        >
          <span class="size-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold flex items-center justify-center shrink-0">
            <CheckIcon v-if="isStep1Valid && currentStep !== 1" class="size-2.5" />
            <span v-else>{{ toPersianDigits(1) }}</span>
          </span>
          <span class="truncate">{{ languageStore.t('مبلغ و هدف', 'Goal & Amount') }}</span>
        </button>

        <!-- Step 2 -->
        <button
          type="button"
          :class="cn(
            'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer select-none',
            currentStep === 2 
              ? 'border-primary bg-primary/10 text-primary font-bold shadow-xs' 
              : isStep2Valid 
                ? 'border-border/50 bg-muted/40 text-foreground hover:bg-muted/60' 
                : 'border-border/30 bg-muted/15 text-muted-foreground/60'
          )"
          @click="isStep1Valid ? (currentStep = 2) : null"
        >
          <span class="size-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold flex items-center justify-center shrink-0">
            <CheckIcon v-if="isStep2Valid && currentStep !== 2" class="size-2.5" />
            <span v-else>{{ toPersianDigits(2) }}</span>
          </span>
          <span class="truncate">{{ languageStore.t('شرح و مدیا', 'Story & Media') }}</span>
        </button>

        <!-- Step 3 -->
        <button
          type="button"
          :class="cn(
            'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer select-none',
            currentStep === 3 
              ? 'border-primary bg-primary/10 text-primary font-bold shadow-xs' 
              : isStep3Valid 
                ? 'border-border/50 bg-muted/40 text-foreground hover:bg-muted/60' 
                : 'border-border/30 bg-muted/15 text-muted-foreground/60'
          )"
          @click="isStep1Valid && isStep2Valid ? (currentStep = 3) : null"
        >
          <span class="size-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold flex items-center justify-center shrink-0">
            <span>{{ toPersianDigits(3) }}</span>
          </span>
          <span class="truncate">{{ languageStore.t('تنظیمات', 'Settings') }}</span>
        </button>
      </div>
    </div>

    <!-- Wizard Step Scrollable Body -->
    <div class="p-4 flex-1 overflow-y-auto max-h-[calc(90dvh-130px)]">
      
      <!-- ================= STEP 1: Basics & Target Amount ================= -->
      <div v-if="currentStep === 1" class="flex flex-col gap-4 animate-in fade-in-50 duration-200">
        
        <!-- Campaign Title Field -->
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <Label for="campaign-title-inline" class="text-xs font-bold text-foreground">
              {{ languageStore.t('عنوان پویش', 'Campaign Title') }} <span class="text-destructive font-bold">*</span>
            </Label>
            <span class="text-[11px] text-muted-foreground">
              {{ toPersianDigits(formState.title.length) }} / {{ toPersianDigits(80) }}
            </span>
          </div>
          <Input 
            id="campaign-title-inline"
            v-model="formState.title"
            maxlength="80"
            :placeholder="languageStore.t('مثال: خرید تجهیزات آموزشی برای مدرسه روستا', 'e.g., Purchasing equipment for rural school')"
            class="h-10 text-xs rounded-xl border-border/70 focus-visible:ring-primary/20"
            dir="auto"
          />
        </div>

        <!-- Category Select Field -->
        <div class="flex flex-col gap-1.5">
          <Label class="text-xs font-bold text-foreground">
            {{ languageStore.t('دسته‌بندی پویش', 'Category') }} <span class="text-destructive font-bold">*</span>
          </Label>
          <Select v-model="formState.category">
            <SelectTrigger class="h-10 text-xs rounded-xl border-border/70 text-start">
              <SelectValue :placeholder="languageStore.t('انتخاب دسته‌بندی...', 'Select category...')" />
            </SelectTrigger>
            <SelectContent class="rounded-xl border-border bg-card text-card-foreground" :dir="languageStore.dir">
              <SelectGroup>
                <SelectItem 
                  v-for="cat in CATEGORIES" 
                  :key="cat.value" 
                  :value="cat.value"
                  class="text-xs cursor-pointer py-2 rounded-lg"
                >
                  <span>{{ cat.label }}</span>
                </SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <!-- Target Amount Field -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <Label for="target-amount-inline" class="text-xs font-bold text-foreground">
              {{ languageStore.t('مبلغ هدف پویش', 'Target Amount') }} <span class="text-destructive font-bold">*</span>
            </Label>
            <span class="text-[11px] text-muted-foreground">{{ languageStore.t('واحد: تومان', 'Unit: Tomans') }}</span>
          </div>
          
          <div class="relative">
            <Input 
              id="target-amount-inline"
              :value="rawAmountInput"
              placeholder="مثال: ۲۰,۰۰۰,۰۰۰"
              class="h-10 text-sm font-bold border-border/70 pr-3 pl-14 text-start placeholder:text-start tracking-normal focus-visible:ring-primary/20 rounded-xl"
              @input="handleAmountInput"
            />
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-muted-foreground select-none pointer-events-none">
              تومان
            </span>
          </div>

          <!-- Preset Amount Buttons via Rounded Chips (ToggleGroup) -->
          <div class="flex flex-col gap-1.5 pt-1">
            <span class="text-[11px] text-muted-foreground font-medium">{{ languageStore.t('مبالغ پیشنهادی سریع:', 'Quick preset amounts:') }}</span>
            <ToggleGroup 
              type="single" 
              :spacing="2"
              :model-value="formState.targetAmount ? String(formState.targetAmount) : ''"
              @update:model-value="(val) => selectPresetAmount(val ? Number(val) : 0)"
              class="flex flex-wrap justify-start gap-1.5"
            >
              <ToggleGroupItem 
                v-for="preset in PRESET_AMOUNTS" 
                :key="preset.amount"
                :value="String(preset.amount)"
                size="sm"
                class="!rounded-full rounded-full text-xs h-8 px-3.5 border border-border/60 transition-all cursor-pointer data-[state=on]:border-primary data-[state=on]:bg-primary/10 data-[state=on]:text-primary data-[state=on]:font-bold data-[state=on]:shadow-xs hover:border-primary/40"
              >
                {{ preset.label }} تومان
              </ToggleGroupItem>
            </ToggleGroup>
          </div>
        </div>

      </div>

      <!-- ================= STEP 2: Story & Media Attachments ================= -->
      <div v-else-if="currentStep === 2" class="flex flex-col gap-4 animate-in fade-in-50 duration-200">
        
        <!-- Story & Need Statement Textarea -->
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <Label for="campaign-desc-inline" class="text-xs font-bold text-foreground">
              {{ languageStore.t('شرح نیاز و داستان پویش', 'Need Statement & Story') }} <span class="text-destructive font-bold">*</span>
            </Label>
            <span 
              :class="cn(
                'text-[11px]',
                formState.description.trim().length >= 15 
                  ? 'text-muted-foreground' 
                  : 'text-destructive font-bold'
              )"
            >
              {{ toPersianDigits(formState.description.trim().length) }} / حداقل {{ toPersianDigits(15) }} کاراکتر
            </span>
          </div>
          <Textarea 
            id="campaign-desc-inline"
            v-model="formState.description"
            rows="3"
            :placeholder="languageStore.t('توضیح دهید این پویش برای چه نیازی است، چگونه اجرا می‌شود و چه تاثیری خواهد داشت...', 'Describe why this campaign is needed, execution plan, and its impact...')"
            class="rounded-xl text-xs font-medium border-border/70 leading-relaxed resize-none focus-visible:ring-primary/20 min-h-[85px]"
            dir="auto"
          />
        </div>

        <!-- Media Upload Dropzone & Grid -->
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <Label class="text-xs font-bold text-foreground">
              {{ languageStore.t('تصاویر و مستندات پویش (اختیاری)', 'Images & Media (Optional)') }}
            </Label>
            <span class="text-[11px] text-muted-foreground">
              {{ toPersianDigits(formState.mediaFiles.length) }} فایل
            </span>
          </div>

          <!-- Hidden File Input -->
          <input 
            ref="fileInputRef" 
            type="file" 
            accept="image/*,video/*" 
            multiple 
            class="hidden" 
            @change="onFileInputChange"
          />

          <!-- Dropzone Box -->
          <div 
            :class="cn(
              'border-2 border-dashed rounded-2xl p-3.5 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-1.5 group',
              isDragging 
                ? 'border-primary bg-primary/10 scale-[0.99]' 
                : 'border-border/70 hover:border-primary/50 bg-muted/20 hover:bg-muted/30'
            )"
            @click="triggerFileInput"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
          >
            <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center group-hover:scale-110 transition-transform shadow-xs">
              <UploadCloudIcon class="size-4" />
            </div>
            <div class="flex flex-col gap-0.5">
              <p class="text-xs font-bold text-foreground">
                {{ languageStore.t('برای انتخاب یا کشیدن فایل‌ها کلیک کنید', 'Click to upload or drag files here') }}
              </p>
              <p class="text-[10px] text-muted-foreground">
                {{ languageStore.t('پشتیبانی از تصاویر و ویدیوهای کوتاه', 'Supports images & short videos') }}
              </p>
            </div>
          </div>

          <!-- Uploaded Media Grid Preview -->
          <div v-if="formState.mediaFiles.length > 0" class="grid grid-cols-4 gap-2 pt-0.5">
            <div 
              v-for="media in formState.mediaFiles" 
              :key="media.id"
              class="relative aspect-square rounded-xl overflow-hidden border border-border/70 bg-muted/40 group shadow-xs"
            >
              <!-- Thumbnail -->
              <img 
                v-if="!media.isVideo" 
                :src="media.previewUrl" 
                :alt="media.file.name" 
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex flex-col items-center justify-center bg-black/80 text-white">
                <VideoIcon class="size-5 text-primary" />
                <span class="text-[9px] mt-0.5">ویدیو</span>
              </div>

              <!-- Remove Button -->
              <button
                type="button"
                class="absolute top-1 left-1 size-5 rounded-full bg-background/80 hover:bg-destructive text-foreground hover:text-destructive-foreground flex items-center justify-center transition-colors cursor-pointer shadow-xs"
                title="حذف"
                @click.stop="removeMediaFile(media.id)"
              >
                <XIcon class="size-2.5" />
              </button>

              <!-- File Info Tooltip -->
              <div class="absolute bottom-0 inset-x-0 bg-background/80 px-1 py-0.5 text-[8px] text-foreground truncate text-center">
                {{ media.file.name }}
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- ================= STEP 3: Settings Only (Clean & Minimal) ================= -->
      <div v-else-if="currentStep === 3" class="flex flex-col gap-4 animate-in fade-in-50 duration-200">
        
        <!-- Settings Controls Card -->
        <div class="p-4 rounded-2xl border border-border/70 bg-muted/20 flex flex-col gap-4 shadow-xs">
          
          <!-- Auto-Pin Switch -->
          <div class="flex items-center justify-between gap-3">
            <div class="flex flex-col gap-0.5 text-start">
              <div class="flex items-center gap-1.5">
                <PinIcon class="size-3.5 text-primary rotate-45" />
                <Label for="auto-pin-switch-inline" class="text-xs font-bold text-foreground cursor-pointer">
                  {{ languageStore.t('پین کردن در بالای تاپیک', 'Pin at top of topic') }}
                </Label>
              </div>
              <p class="text-[11px] text-muted-foreground leading-relaxed">
                {{ languageStore.t('نمایش به صورت پیام پین‌شده در تاپیک برای مشاهده بهتر اعضا', 'Show as pinned message in topic feed for better visibility') }}
              </p>
            </div>

            <Switch 
              id="auto-pin-switch-inline"
              :checked="formState.autoPin"
              @update:checked="(val: boolean) => formState.autoPin = val"
            />
          </div>

          <Separator class="bg-border/40" />

          <!-- Deadline Preset Selection via Rounded Chips (ToggleGroup) -->
          <div class="flex flex-col gap-2 text-start">
            <div class="flex items-center gap-1.5">
              <CalendarIcon class="size-3.5 text-primary" />
              <Label class="text-xs font-bold text-foreground">
                {{ languageStore.t('مهلت زمانی جمع‌آوری پویش', 'Collection Deadline / Duration') }}
              </Label>
            </div>

            <ToggleGroup 
              type="single" 
              :spacing="2"
              :model-value="selectedDeadlinePreset" 
              @update:model-value="(val) => selectedDeadlinePreset = (val as string) || 'none'"
              class="grid grid-cols-4 gap-1.5"
            >
              <ToggleGroupItem 
                v-for="d in DEADLINE_PRESETS" 
                :key="d.value"
                :value="d.value"
                size="sm"
                class="!rounded-full rounded-full text-xs h-8 font-medium px-2 border border-border/60 transition-all cursor-pointer data-[state=on]:border-primary data-[state=on]:bg-primary/10 data-[state=on]:text-primary data-[state=on]:font-bold data-[state=on]:shadow-xs hover:border-primary/40"
              >
                {{ d.label }}
              </ToggleGroupItem>
            </ToggleGroup>
          </div>

        </div>

        <!-- Quick Summary Summary Card -->
        <div class="p-3.5 rounded-2xl bg-muted/30 border border-border/40 flex flex-col gap-2">
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">عنوان پویش:</span>
            <span class="font-bold text-foreground truncate max-w-[200px]">{{ formState.title }}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">مبلغ هدف:</span>
            <span class="font-bold text-primary">{{ new Intl.NumberFormat('fa-IR').format(formState.targetAmount || 0) }} تومان</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">مهلت انتخابی:</span>
            <span class="font-medium text-foreground">{{ formState.deadline || 'بدون محدودیت زمانی' }}</span>
          </div>
        </div>

      </div>

    </div>

    <!-- Minimal Dialog Footer -->
    <div class="p-4 border-t border-border/40 bg-muted/10 flex flex-row items-center justify-between gap-2 shrink-0">
      <!-- Back Button -->
      <Button 
        v-if="currentStep > 1"
        type="button" 
        variant="outline" 
        class="rounded-xl text-xs font-bold gap-1 px-3.5 h-9"
        @click="prevStep"
      >
        <ChevronRightIcon data-icon="inline-start" />
        <span>{{ languageStore.t('بازگشت', 'Back') }}</span>
      </Button>
      <div v-else />

      <!-- Next / Publish Button -->
      <Button 
        v-if="currentStep < 3"
        type="button" 
        variant="default" 
        class="rounded-xl text-xs font-bold gap-1 px-4 h-9 shadow-xs hover:shadow-sm cursor-pointer"
        :disabled="currentStep === 1 ? !isStep1Valid : !isStep2Valid"
        @click="nextStep"
      >
        <span>{{ languageStore.t('مرحله بعد', 'Next') }}</span>
        <ChevronLeftIcon data-icon="inline-end" />
      </Button>

      <!-- Step 3: Publish / Save Button -->
      <Button 
        v-else
        type="button" 
        variant="default" 
        class="rounded-xl text-xs font-bold px-4 h-9 shadow-sm active:scale-95 transition-all cursor-pointer"
        :disabled="!isStep3Valid"
        @click="handleSubmit"
      >
        <span>{{ isEditMode ? languageStore.t('ذخیره تغییرات', 'Save Changes') : languageStore.t('انتشار در چت', 'Post to Chat') }}</span>
      </Button>
    </div>
  </div>

  <!-- Standard Dialog Overlay Mode (Mobile First) -->
  <Dialog v-else :open="open" @update:open="(val: boolean) => emit('update:open', val)">
    <DialogContent 
      :show-close-button="false"
      class="w-[94vw] max-w-[420px] max-h-[90dvh] overflow-hidden rounded-3xl p-0 border border-border/80 bg-card text-card-foreground shadow-2xl flex flex-col text-start font-sans"
      :dir="languageStore.dir"
    >
      <!-- Minimalist Dialog Header -->
      <DialogHeader class="px-4 py-3.5 border-b border-border/40 shrink-0 bg-muted/20 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 shadow-xs">
              <HeartIcon class="size-4 fill-primary/20" />
            </div>
            <div class="flex flex-col min-w-0">
              <DialogTitle class="text-sm font-bold text-foreground truncate">
                {{ isEditMode ? languageStore.t('ویرایش پویش مهربانی', 'Edit Kindness Campaign') : languageStore.t('ایجاد پویش مهربانی', 'New Kindness Campaign') }}
              </DialogTitle>
              <DialogDescription class="text-xs text-muted-foreground truncate">
                {{ languageStore.t('پویش مالی جمعی درون تاپیک', 'Crowdfunding campaign in topic') }}
              </DialogDescription>
            </div>
          </div>

          <DialogClose as-child>
            <Button 
              variant="ghost" 
              size="icon" 
              class="size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/80 cursor-pointer"
              :title="languageStore.t('بستن', 'Close')"
            >
              <XIcon />
            </Button>
          </DialogClose>
        </div>

        <!-- Sleek Minimal Wizard Step Indicator -->
        <div class="grid grid-cols-3 gap-2 pt-0.5">
          <!-- Step 1 -->
          <button
            type="button"
            :class="cn(
              'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer select-none',
              currentStep === 1 
                ? 'border-primary bg-primary/10 text-primary font-bold shadow-xs' 
                : isStep1Valid 
                  ? 'border-border/50 bg-muted/40 text-foreground hover:bg-muted/60' 
                  : 'border-border/30 bg-muted/15 text-muted-foreground/60'
            )"
            @click="currentStep = 1"
          >
            <span class="size-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold flex items-center justify-center shrink-0">
              <CheckIcon v-if="isStep1Valid && currentStep !== 1" class="size-2.5" />
              <span v-else>{{ toPersianDigits(1) }}</span>
            </span>
            <span class="truncate">{{ languageStore.t('مبلغ و هدف', 'Goal & Amount') }}</span>
          </button>

          <!-- Step 2 -->
          <button
            type="button"
            :class="cn(
              'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer select-none',
              currentStep === 2 
                ? 'border-primary bg-primary/10 text-primary font-bold shadow-xs' 
                : isStep2Valid 
                  ? 'border-border/50 bg-muted/40 text-foreground hover:bg-muted/60' 
                  : 'border-border/30 bg-muted/15 text-muted-foreground/60'
            )"
            @click="isStep1Valid ? (currentStep = 2) : null"
          >
            <span class="size-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold flex items-center justify-center shrink-0">
              <CheckIcon v-if="isStep2Valid && currentStep !== 2" class="size-2.5" />
              <span v-else>{{ toPersianDigits(2) }}</span>
            </span>
            <span class="truncate">{{ languageStore.t('شرح و مدیا', 'Story & Media') }}</span>
          </button>

          <!-- Step 3 -->
          <button
            type="button"
            :class="cn(
              'flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer select-none',
              currentStep === 3 
                ? 'border-primary bg-primary/10 text-primary font-bold shadow-xs' 
                : isStep3Valid 
                  ? 'border-border/50 bg-muted/40 text-foreground hover:bg-muted/60' 
                  : 'border-border/30 bg-muted/15 text-muted-foreground/60'
            )"
            @click="isStep1Valid && isStep2Valid ? (currentStep = 3) : null"
          >
            <span class="size-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold flex items-center justify-center shrink-0">
              <span>{{ toPersianDigits(3) }}</span>
            </span>
            <span class="truncate">{{ languageStore.t('تنظیمات', 'Settings') }}</span>
          </button>
        </div>
      </DialogHeader>

      <!-- Wizard Step Scrollable Body -->
      <div class="p-4 flex-1 overflow-y-auto max-h-[calc(90dvh-130px)]">
        
        <!-- ================= STEP 1: Basics & Target Amount ================= -->
        <div v-if="currentStep === 1" class="flex flex-col gap-4 animate-in fade-in-50 duration-200">
          
          <!-- Campaign Title Field -->
          <div class="flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <Label for="campaign-title" class="text-xs font-bold text-foreground">
                {{ languageStore.t('عنوان پویش', 'Campaign Title') }} <span class="text-destructive font-bold">*</span>
              </Label>
              <span class="text-[11px] text-muted-foreground">
                {{ toPersianDigits(formState.title.length) }} / {{ toPersianDigits(80) }}
              </span>
            </div>
            <Input 
              id="campaign-title"
              v-model="formState.title"
              maxlength="80"
              :placeholder="languageStore.t('مثال: خرید تجهیزات آموزشی برای مدرسه روستا', 'e.g., Purchasing equipment for rural school')"
              class="h-10 text-xs rounded-xl border-border/70 focus-visible:ring-primary/20"
              dir="auto"
            />
          </div>

          <!-- Category Select Field -->
          <div class="flex flex-col gap-1.5">
            <Label class="text-xs font-bold text-foreground">
              {{ languageStore.t('دسته‌بندی پویش', 'Category') }} <span class="text-destructive font-bold">*</span>
            </Label>
            <Select v-model="formState.category">
              <SelectTrigger class="h-10 text-xs rounded-xl border-border/70 text-start">
                <SelectValue :placeholder="languageStore.t('انتخاب دسته‌بندی...', 'Select category...')" />
              </SelectTrigger>
              <SelectContent class="rounded-xl border-border bg-card text-card-foreground" :dir="languageStore.dir">
                <SelectGroup>
                  <SelectItem 
                    v-for="cat in CATEGORIES" 
                    :key="cat.value" 
                    :value="cat.value"
                    class="text-xs cursor-pointer py-2 rounded-lg"
                  >
                    <span>{{ cat.label }}</span>
                  </SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <!-- Target Amount Field -->
          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <Label for="target-amount" class="text-xs font-bold text-foreground">
                {{ languageStore.t('مبلغ هدف پویش', 'Target Amount') }} <span class="text-destructive font-bold">*</span>
              </Label>
              <span class="text-[11px] text-muted-foreground">{{ languageStore.t('واحد: تومان', 'Unit: Tomans') }}</span>
            </div>
            
            <div class="relative">
              <Input 
                id="target-amount"
                :value="rawAmountInput"
                placeholder="مثال: ۲۰,۰۰۰,۰۰۰"
                class="h-10 text-sm font-bold border-border/70 pr-3 pl-14 text-start placeholder:text-start tracking-normal focus-visible:ring-primary/20 rounded-xl"
                @input="handleAmountInput"
              />
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-muted-foreground select-none pointer-events-none">
                تومان
              </span>
            </div>

            <!-- Preset Amount Buttons via Rounded Chips (ToggleGroup) -->
            <div class="flex flex-col gap-1.5 pt-1">
              <span class="text-[11px] text-muted-foreground font-medium">{{ languageStore.t('مبالغ پیشنهادی سریع:', 'Quick preset amounts:') }}</span>
              <ToggleGroup 
                type="single" 
                :spacing="2"
                :model-value="formState.targetAmount ? String(formState.targetAmount) : ''"
                @update:model-value="(val) => selectPresetAmount(val ? Number(val) : 0)"
                class="flex flex-wrap justify-start gap-1.5"
              >
                <ToggleGroupItem 
                  v-for="preset in PRESET_AMOUNTS" 
                  :key="preset.amount"
                  :value="String(preset.amount)"
                  size="sm"
                  class="!rounded-full rounded-full text-xs h-8 px-3.5 border border-border/60 transition-all cursor-pointer data-[state=on]:border-primary data-[state=on]:bg-primary/10 data-[state=on]:text-primary data-[state=on]:font-bold data-[state=on]:shadow-xs hover:border-primary/40"
                >
                  {{ preset.label }} تومان
                </ToggleGroupItem>
              </ToggleGroup>
            </div>
          </div>

        </div>

        <!-- ================= STEP 2: Story & Media Attachments ================= -->
        <div v-else-if="currentStep === 2" class="flex flex-col gap-4 animate-in fade-in-50 duration-200">
          
          <!-- Story & Need Statement Textarea -->
          <div class="flex flex-col gap-1.5">
            <div class="flex items-center justify-between">
              <Label for="campaign-desc" class="text-xs font-bold text-foreground">
                {{ languageStore.t('شرح نیاز و داستان پویش', 'Need Statement & Story') }} <span class="text-destructive font-bold">*</span>
              </Label>
              <span 
                :class="cn(
                  'text-[11px]',
                  formState.description.trim().length >= 15 
                    ? 'text-muted-foreground' 
                    : 'text-destructive font-bold'
                )"
              >
                {{ toPersianDigits(formState.description.trim().length) }} / حداقل {{ toPersianDigits(15) }} کاراکتر
              </span>
            </div>
            <Textarea 
              id="campaign-desc"
              v-model="formState.description"
              rows="3"
              :placeholder="languageStore.t('توضیح دهید این پویش برای چه نیازی است، چگونه اجرا می‌شود و چه تاثیری خواهد داشت...', 'Describe why this campaign is needed, execution plan, and its impact...')"
              class="rounded-xl text-xs font-medium border-border/70 leading-relaxed resize-none focus-visible:ring-primary/20 min-h-[85px]"
              dir="auto"
            />
          </div>

          <!-- Media Upload Dropzone & Grid -->
          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <Label class="text-xs font-bold text-foreground">
                {{ languageStore.t('تصاویر و مستندات پویش (اختیاری)', 'Images & Media (Optional)') }}
              </Label>
              <span class="text-[11px] text-muted-foreground">
                {{ toPersianDigits(formState.mediaFiles.length) }} فایل
              </span>
            </div>

            <!-- Hidden File Input -->
            <input 
              ref="fileInputRef" 
              type="file" 
              accept="image/*,video/*" 
              multiple 
              class="hidden" 
              @change="onFileInputChange"
            />

            <!-- Dropzone Box -->
            <div 
              :class="cn(
                'border-2 border-dashed rounded-2xl p-3.5 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-1.5 group',
                isDragging 
                  ? 'border-primary bg-primary/10 scale-[0.99]' 
                  : 'border-border/70 hover:border-primary/50 bg-muted/20 hover:bg-muted/30'
              )"
              @click="triggerFileInput"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="onDrop"
            >
              <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center group-hover:scale-110 transition-transform shadow-xs">
                <UploadCloudIcon class="size-4" />
              </div>
              <div class="flex flex-col gap-0.5">
                <p class="text-xs font-bold text-foreground">
                  {{ languageStore.t('برای انتخاب یا کشیدن فایل‌ها کلیک کنید', 'Click to upload or drag files here') }}
                </p>
                <p class="text-[10px] text-muted-foreground">
                  {{ languageStore.t('پشتیبانی از تصاویر و ویدیوهای کوتاه', 'Supports images & short videos') }}
                </p>
              </div>
            </div>

            <!-- Uploaded Media Grid Preview -->
            <div v-if="formState.mediaFiles.length > 0" class="grid grid-cols-4 gap-2 pt-0.5">
              <div 
                v-for="media in formState.mediaFiles" 
                :key="media.id"
                class="relative aspect-square rounded-xl overflow-hidden border border-border/70 bg-muted/40 group shadow-xs"
              >
                <!-- Thumbnail -->
                <img 
                  v-if="!media.isVideo" 
                  :src="media.previewUrl" 
                  :alt="media.file.name" 
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex flex-col items-center justify-center bg-black/80 text-white">
                  <VideoIcon class="size-5 text-primary" />
                  <span class="text-[9px] mt-0.5">ویدیو</span>
                </div>

                <!-- Remove Button -->
                <button
                  type="button"
                  class="absolute top-1 left-1 size-5 rounded-full bg-background/80 hover:bg-destructive text-foreground hover:text-destructive-foreground flex items-center justify-center transition-colors cursor-pointer shadow-xs"
                  title="حذف"
                  @click.stop="removeMediaFile(media.id)"
                >
                  <XIcon class="size-2.5" />
                </button>

                <!-- File Info Tooltip -->
                <div class="absolute bottom-0 inset-x-0 bg-background/80 px-1 py-0.5 text-[8px] text-foreground truncate text-center">
                  {{ media.file.name }}
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- ================= STEP 3: Settings Only (Clean & Minimal) ================= -->
        <div v-else-if="currentStep === 3" class="flex flex-col gap-4 animate-in fade-in-50 duration-200">
          
          <!-- Settings Controls Card -->
          <div class="p-4 rounded-2xl border border-border/70 bg-muted/20 flex flex-col gap-4 shadow-xs">
            
            <!-- Auto-Pin Switch -->
            <div class="flex items-center justify-between gap-3">
              <div class="flex flex-col gap-0.5 text-start">
                <div class="flex items-center gap-1.5">
                  <PinIcon class="size-3.5 text-primary rotate-45" />
                  <Label for="auto-pin-switch" class="text-xs font-bold text-foreground cursor-pointer">
                    {{ languageStore.t('پین کردن در بالای تاپیک', 'Pin at top of topic') }}
                  </Label>
                </div>
                <p class="text-[11px] text-muted-foreground leading-relaxed">
                  {{ languageStore.t('نمایش به صورت پیام پین‌شده در تاپیک برای مشاهده بهتر اعضا', 'Show as pinned message in topic feed for better visibility') }}
                </p>
              </div>

              <Switch 
                id="auto-pin-switch"
                :checked="formState.autoPin"
                @update:checked="(val: boolean) => formState.autoPin = val"
              />
            </div>

            <Separator class="bg-border/40" />

            <!-- Deadline Preset Selection via Rounded Chips (ToggleGroup) -->
            <div class="flex flex-col gap-2 text-start">
              <div class="flex items-center gap-1.5">
                <CalendarIcon class="size-3.5 text-primary" />
                <Label class="text-xs font-bold text-foreground">
                  {{ languageStore.t('مهلت زمانی جمع‌آوری پویش', 'Collection Deadline / Duration') }}
                </Label>
              </div>

            <ToggleGroup 
              type="single" 
              :spacing="2"
              :model-value="selectedDeadlinePreset" 
              @update:model-value="(val) => selectedDeadlinePreset = (val as string) || 'none'"
              class="grid grid-cols-4 gap-1.5"
            >
              <ToggleGroupItem 
                v-for="d in DEADLINE_PRESETS" 
                :key="d.value"
                :value="d.value"
                size="sm"
                class="!rounded-full rounded-full text-xs h-8 font-medium px-2 border border-border/60 transition-all cursor-pointer data-[state=on]:border-primary data-[state=on]:bg-primary/10 data-[state=on]:text-primary data-[state=on]:font-bold data-[state=on]:shadow-xs hover:border-primary/40"
              >
                {{ d.label }}
              </ToggleGroupItem>
            </ToggleGroup>
          </div>

        </div>

        <!-- Quick Summary Summary Card -->
        <div class="p-3.5 rounded-2xl bg-muted/30 border border-border/40 flex flex-col gap-2">
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">عنوان پویش:</span>
            <span class="font-bold text-foreground truncate max-w-[200px]">{{ formState.title }}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">مبلغ هدف:</span>
            <span class="font-bold text-primary">{{ new Intl.NumberFormat('fa-IR').format(formState.targetAmount || 0) }} تومان</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">مهلت انتخابی:</span>
            <span class="font-medium text-foreground">{{ formState.deadline || 'بدون محدودیت زمانی' }}</span>
          </div>
        </div>

      </div>

    </div>

    <!-- Minimal Dialog Footer -->
    <DialogFooter class="p-4 border-t border-border/40 bg-muted/10 flex flex-row items-center justify-between gap-2 shrink-0">
      <!-- Back Button -->
      <Button 
        v-if="currentStep > 1"
        type="button" 
        variant="outline" 
        class="rounded-xl text-xs font-bold gap-1 px-3.5 h-9"
        @click="prevStep"
      >
        <ChevronRightIcon data-icon="inline-start" />
        <span>{{ languageStore.t('بازگشت', 'Back') }}</span>
      </Button>
      <div v-else />

      <!-- Next / Publish Button -->
      <Button 
        v-if="currentStep < 3"
        type="button" 
        variant="default" 
        class="rounded-xl text-xs font-bold gap-1 px-4 h-9 shadow-xs hover:shadow-sm cursor-pointer"
        :disabled="currentStep === 1 ? !isStep1Valid : !isStep2Valid"
        @click="nextStep"
      >
        <span>{{ languageStore.t('مرحله بعد', 'Next') }}</span>
        <ChevronLeftIcon data-icon="inline-end" />
      </Button>

      <!-- Step 3: Publish / Save Button -->
      <Button 
        v-else
        type="button" 
        variant="default" 
        class="rounded-xl text-xs font-bold px-4 h-9 shadow-sm active:scale-95 transition-all cursor-pointer"
        :disabled="!isStep3Valid"
        @click="handleSubmit"
      >
        <span>{{ isEditMode ? languageStore.t('ذخیره تغییرات', 'Save Changes') : languageStore.t('انتشار در چت', 'Post to Chat') }}</span>
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
</template>
