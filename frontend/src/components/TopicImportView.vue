<script setup lang="ts">
import { ref } from 'vue'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import LoadingDialog from '@/components/LoadingDialog.vue'
import { useLanguageStore } from '@/stores/languageStore'
import {
  UploadCloudIcon,
  FileJsonIcon,
  InfoIcon,
  Trash2Icon
} from '@lucide/vue'

const props = withDefaults(defineProps<{
  topicId?: number
}>(), {})

const emit = defineEmits<{
  (e: 'import-complete'): void
  (e: 'import-failed', error: string): void
}>()

const languageStore = useLanguageStore()

// State management
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isDragActive = ref(false)

// Pipeline state
const isImporting = ref(false)
const globalProgress = ref(0)
const currentStatus = ref<'idle' | 'uploading' | 'validating' | 'importing' | 'completed' | 'failed'>('idle')
const isProcessing = ref(false)

// File selection handlers
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const file = target.files[0]
    if (file && file.name.endsWith('.json')) {
      selectedFile.value = file
    } else {
      alert(languageStore.isFa ? 'فقط فایل‌های JSON مجاز هستند.' : 'Only JSON files are allowed.')
    }
  }
}

const handleFileDrop = (event: DragEvent) => {
  isDragActive.value = false
  if (event.dataTransfer && event.dataTransfer.files.length > 0) {
    const file = event.dataTransfer.files[0]
    if (file && file.name.endsWith('.json')) {
      selectedFile.value = file
    } else {
      alert(languageStore.isFa ? 'فقط فایل‌های JSON مجاز هستند.' : 'Only JSON files are allowed.')
    }
  }
}

const removeFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Format bytes to readable size
const formatBytes = (bytes: number, decimals = 2) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

// Simulated Pipeline Process (Upload + Polling Simulation)
let simulationInterval: any = null

const startImportPipeline = () => {
  if (!selectedFile.value) return

  isImporting.value = true
  isProcessing.value = true
  globalProgress.value = 0
  currentStatus.value = 'uploading'

  // Stage 1: Uploading Simulation (Axios onUploadProgress style)
  let progress = 0
  simulationInterval = setInterval(() => {
    if (currentStatus.value === 'uploading') {
      progress += Math.floor(Math.random() * 15) + 5
      if (progress >= 100) {
        progress = 100
        globalProgress.value = 100
        currentStatus.value = 'validating'
        progress = 0
      } else {
        // Pump progress directly to global progress
        globalProgress.value = Math.min(progress * 0.4, 40) // Upload is 40% of overall progress
      }
    } else if (currentStatus.value === 'validating') {
      progress += 10
      globalProgress.value = 40 + Math.min(progress * 0.3, 30) // Validate is next 30%
      if (progress >= 100) {
        currentStatus.value = 'importing'
        progress = 0
      }
    } else if (currentStatus.value === 'importing') {
      progress += 5
      globalProgress.value = 70 + Math.min(progress * 0.3, 30) // Import is final 30%
      if (progress >= 100) {
        currentStatus.value = 'completed'
        globalProgress.value = 100
        isProcessing.value = false
        clearInterval(simulationInterval)
        emit('import-complete')
      }
    }
  }, 150)
}

const handleDialogClose = () => {
  if (!isProcessing.value) {
    isImporting.value = false
    removeFile()
    currentStatus.value = 'idle'
  }
}
</script>

<template>
  <div class="container max-w-5xl py-8 space-y-8 font-[IRANYekanX] text-right" :dir="languageStore.dir">
    <!-- View Header -->
    <div class="flex flex-col gap-2">
      <h1 class="text-2xl font-black text-foreground text-start">
        {{ languageStore.t('وارد کردن تاریخچه پیام‌رسان', 'Import Channel History') }}
      </h1>
      <p class="text-xs text-muted-foreground leading-relaxed text-start">
        {{ languageStore.t('پیام‌های پشتیبان کانال تلگرام خود را به این تاپیک انتقال دهید.', 'Migrate your archived Telegram channel messages into this topic.') }}
      </p>
    </div>

    <!-- Dual Column Grid -->
    <div class="grid gap-6 md:grid-cols-2">
      <!-- Guide Card -->
      <Card class="rounded-3xl border border-border/40 bg-card/60 backdrop-blur-md flex flex-col justify-between overflow-hidden">
        <CardHeader class="pb-3">
          <CardTitle class="text-sm font-extrabold text-foreground flex items-center gap-2">
            <div class="size-7 rounded-lg bg-primary/[0.04] flex items-center justify-center text-primary shrink-0">
              <InfoIcon class="size-4.5" />
            </div>
            <span>{{ languageStore.t('راهنمای خروجی گرفتن از تلگرام', 'How to Export from Telegram') }}</span>
          </CardTitle>
          <CardDescription class="text-[11px] text-muted-foreground">
            {{ languageStore.t('مراحل زیر را برای دریافت فایل بکاپ معتبر دنبال کنید:', 'Follow these steps to get your JSON backup file:') }}
          </CardDescription>
        </CardHeader>
        
        <CardContent class="space-y-4 pb-6">
          <ol class="space-y-3.5 text-xs text-muted-foreground list-decimal list-inside pr-1">
            <li class="leading-relaxed">
              {{ languageStore.t('برنامه ', '') }}
              <span class="font-extrabold text-foreground">{{ languageStore.t('Telegram Desktop', 'Telegram Desktop') }}</span>
              {{ languageStore.t(' را باز کرده و وارد کانال خود شوید.', ' and go to your channel.') }}
            </li>
            <li class="leading-relaxed">
              {{ languageStore.t('روی آیکون سه نقطه در بالا سمت راست کلیک کرده و گزینه ', 'Click the three dots icon in the top right and select ') }}
              <span class="font-extrabold text-foreground">{{ languageStore.t('Export channel history', 'Export channel history') }}</span>
              {{ languageStore.t(' را انتخاب کنید.', '.') }}
            </li>
            <li class="leading-relaxed">
              {{ languageStore.t('اگر مایل به انتقال رسانه‌ها (عکس، ویدیو) نیستید، تیک همه را بردارید تا حجم فایل کاهش یابد.', 'Uncheck all media options if you only want text, or keep them for full backup.') }}
            </li>
            <li class="leading-relaxed font-semibold text-amber-600 dark:text-amber-500">
              {{ languageStore.t('حیاتی: قالب خروجی (Format) را حتماً روی حالت ', 'CRITICAL: Change the format from HTML to ') }}
              <span class="font-black text-foreground underline decoration-amber-500">{{ languageStore.t('JSON', 'JSON') }}</span>
              {{ languageStore.t(' تنظیم کنید.', '.') }}
            </li>
            <li class="leading-relaxed">
              {{ languageStore.t('روی دکمه Export کلیک کرده و فایل نهایی ', 'Click Export and upload the resulting ') }}
              <code class="px-1.5 py-0.5 bg-muted rounded-md text-[10px] font-mono text-primary font-bold">result.json</code>
              {{ languageStore.t(' را در بخش مقابل بارگذاری کنید.', ' file here.') }}
            </li>
          </ol>

          <!-- Security/Technical Alert -->
          <Alert variant="default" class="mt-4 border-amber-500/20 bg-amber-500/[0.02] text-amber-700 dark:text-amber-400 rounded-2xl flex items-start gap-2.5 p-3.5">
            <InfoIcon class="size-4 shrink-0 mt-0.5 text-amber-500" />
            <AlertDescription class="text-[10px] leading-relaxed font-bold">
              {{ languageStore.t(
                'توجه: فایل‌های دارای فرمت HTML توسط سیستم پشتیبانی نشده و بلافاصله در فرآیند اعتبارسنجی رد خواهند شد.',
                'Make sure the exported file format is strictly JSON. HTML formats will be rejected by the validation pipeline.'
              ) }}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <!-- Upload/Dropzone Card -->
      <Card class="rounded-3xl border border-border/40 bg-card/60 backdrop-blur-md flex flex-col justify-between overflow-hidden">
        <CardHeader class="pb-3">
          <CardTitle class="text-sm font-extrabold text-foreground flex items-center gap-2">
            <div class="size-7 rounded-lg bg-primary/[0.04] flex items-center justify-center text-primary shrink-0">
              <UploadCloudIcon class="size-4.5" />
            </div>
            <span>{{ languageStore.t('بارگذاری فایل پشتیبان', 'Upload Backup File') }}</span>
          </CardTitle>
          <CardDescription class="text-[11px] text-muted-foreground">
            {{ languageStore.t('فایل بکاپ JSON خود را در کادر زیر قرار دهید.', 'Select or drag your JSON backup file here.') }}
          </CardDescription>
        </CardHeader>
        
        <CardContent class="flex-1 flex flex-col justify-center pb-6">
          <!-- Dropzone -->
          <div 
            v-if="!selectedFile"
            @dragover.prevent="isDragActive = true"
            @dragleave.prevent="isDragActive = false"
            @drop.prevent="handleFileDrop"
            @click="fileInput?.click()"
            class="flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-200 h-[190px]"
            :class="[
              isDragActive 
                ? 'border-primary bg-primary/[0.02] scale-[1.01]' 
                : 'border-border hover:bg-muted/30 hover:border-primary/40'
            ]"
          >
            <input 
              type="file" 
              ref="fileInput" 
              class="hidden" 
              accept=".json" 
              @change="handleFileSelect" 
            />
            <UploadCloudIcon class="w-10 h-10 mb-3 text-muted-foreground/60 transition-transform group-hover:scale-105" />
            <p class="text-xs font-extrabold text-foreground">
              {{ languageStore.t('کلیک کنید یا فایل را بکشید و رها کنید', 'Click to upload or drag & drop') }}
            </p>
            <p class="text-[10px] text-muted-foreground mt-1">
              {{ languageStore.t('فقط فایل‌های .json مجاز هستند', 'Only .json files are allowed') }}
            </p>
          </div>

          <!-- File Metadata Preview -->
          <div v-else class="flex items-center justify-between p-4 border border-border/40 rounded-2xl bg-muted/20">
            <div class="flex items-center gap-3 min-w-0">
              <div class="size-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <FileJsonIcon class="size-5.5" />
              </div>
              <div class="space-y-0.5 min-w-0 text-right">
                <p class="text-xs font-extrabold text-foreground truncate max-w-[200px]" dir="ltr">
                  {{ selectedFile.name }}
                </p>
                <p class="text-[10px] text-muted-foreground font-semibold">
                  {{ formatBytes(selectedFile.size) }}
                </p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              @click="removeFile" 
              class="text-destructive hover:bg-destructive/10 rounded-xl cursor-pointer shadow-none"
            >
              <Trash2Icon class="size-4.5" />
            </Button>
          </div>
        </CardContent>

        <!-- Footer actions -->
        <CardFooter class="flex justify-end pt-4 border-t border-border/30 pb-4">
          <Button 
            class="rounded-xl px-5 py-4 text-xs font-bold transition-all cursor-pointer"
            :disabled="!selectedFile" 
            @click="startImportPipeline"
          >
            {{ languageStore.t('تایید و شروع درون‌ریزی', 'Confirm & Start Import') }}
          </Button>
        </CardFooter>
      </Card>
    </div>

    <!-- Pipeline Loading Modal Dialog -->
    <LoadingDialog 
      :is-open="isImporting" 
      :progress="globalProgress" 
      :currentStatus="currentStatus" 
      :isProcessing="isProcessing"
      @close="handleDialogClose"
      @action="handleDialogClose"
    />
  </div>
</template>
