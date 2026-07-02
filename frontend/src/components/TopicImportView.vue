<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import PlatformHeader from './PlatformHeader.vue'
import { Button } from '@/components/ui/button'
import LoadingDialog from '@/components/LoadingDialog.vue'
import { useLanguageStore } from '@/stores/languageStore'
import { importHistory, getImportStatus } from '@/api'
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
  (e: 'back'): void
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

// Active Polling Interval reference
let pollingInterval: any = null

const startStatusPolling = (taskId: string) => {
  pollingInterval = setInterval(async () => {
    try {
      const res = await getImportStatus(taskId)
      const taskData = res.data
      
      globalProgress.value = taskData.progress
      
      // Map backend status to loading dialog stage status codes
      const statusMap: Record<string, typeof currentStatus.value> = {
        'PENDING': 'uploading',
        'EXTRACTING': 'validating',
        'IMPORTING': 'importing',
        'COMPLETED': 'completed',
        'FAILED': 'failed'
      }
      currentStatus.value = statusMap[taskData.status] || 'idle'

      if (taskData.status === 'COMPLETED') {
        clearInterval(pollingInterval)
        pollingInterval = null
        isProcessing.value = false
        emit('import-complete')
      } else if (taskData.status === 'FAILED') {
        clearInterval(pollingInterval)
        pollingInterval = null
        isProcessing.value = false
        emit('import-failed', taskData.error_message || 'خطا در درون‌ریزی تاریخچه.')
      }
    } catch (err) {
      console.error('Polling import status failed:', err)
    }
  }, 1200)
}

const startImportPipeline = async () => {
  if (!selectedFile.value || !props.topicId) return

  isImporting.value = true
  isProcessing.value = true
  globalProgress.value = 0
  currentStatus.value = 'uploading'

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    // Call Django API multipart upload
    const res = await importHistory(props.topicId, formData)
    const taskId = res.data.id
    
    // Start tracking background process status
    startStatusPolling(taskId)
  } catch (err: any) {
    isImporting.value = false
    isProcessing.value = false
    const errMsg = err.response?.data?.error || 'خطا در آپلود فایل تاریخچه تلگرام.'
    emit('import-failed', errMsg)
  }
}

const handleDialogClose = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  if (!isProcessing.value) {
    isImporting.value = false
    removeFile()
    currentStatus.value = 'idle'
  }
}

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
})
</script>

<template>
  <div 
    class="w-full flex flex-col gap-5 text-start font-sans" 
    :dir="languageStore.dir"
  >
    <!-- Header -->
    <PlatformHeader 
      is-inner-page
      :inner-title="languageStore.t('درون‌ریزی تاریخچه', 'Import History')"
      :show-options-button="false"
      @back="emit('back')"
    />

    <!-- Main Card wrapper -->
    <div class="w-full bg-card/25 dark:bg-card/15 border border-border/50 rounded-3xl p-5 shadow-xs flex flex-col gap-5">
      
      <!-- Info Banner -->
      <div class="bg-indigo-50/50 dark:bg-indigo-950/20 rounded-2xl p-4 border border-indigo-50 dark:border-indigo-900/30 text-xs text-indigo-700 dark:text-indigo-400 leading-relaxed text-start">
        {{ languageStore.t('💡 پیام‌های کانال تلگرام خود را با بارگذاری فایل خروجی JSON به راحتی وارد این تاپیک کنید تا با ربات‌های فعال همگام‌سازی شوند.', '💡 Import your Telegram channel messages into this topic by uploading the JSON export file to sync with active bots.') }}
      </div>

      <!-- File Dropzone Section -->
      <div class="flex flex-col gap-3">
        <div class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
          <span class="size-2 rounded-full bg-primary shrink-0" />
          {{ languageStore.t('انتخاب فایل پشتیبان', 'Select Backup File') }}
        </div>
        
        <!-- Dropzone Box -->
        <div 
          v-if="!selectedFile"
          @dragover.prevent="isDragActive = true"
          @dragleave.prevent="isDragActive = false"
          @drop.prevent="handleFileDrop"
          @click="fileInput?.click()"
          class="flex flex-col items-center justify-center p-6 border border-dashed border-border/70 rounded-2xl bg-background/25 hover:bg-muted/30 hover:border-primary/45 transition-all duration-200 cursor-pointer h-36"
          :class="[isDragActive ? 'border-primary bg-primary/[0.02]' : '']"
        >
          <input 
            type="file" 
            ref="fileInput" 
            class="hidden" 
            accept=".json" 
            @change="handleFileSelect" 
          />
          <UploadCloudIcon class="w-8 h-8 mb-2 text-muted-foreground/60" />
          <div class="text-[11px] font-bold text-foreground">
            {{ languageStore.t('برای بارگذاری کلیک کنید یا فایل را بکشید', 'Click to upload or drag file here') }}
          </div>
          <div class="text-[9.5px] text-muted-foreground mt-0.5">
            {{ languageStore.t('فقط فایل result.json تلگرام', 'Only Telegram result.json file allowed') }}
          </div>
        </div>

        <!-- File Metadata Preview -->
        <div v-else class="flex items-center justify-between p-3.5 border border-border/50 rounded-2xl bg-background/45">
          <div class="flex items-center gap-3 min-w-0">
            <div class="size-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
              <FileJsonIcon class="size-5" />
            </div>
            <div class="flex flex-col text-start min-w-0">
              <span class="text-[11px] font-extrabold text-foreground truncate max-w-[190px]" dir="ltr">
                {{ selectedFile.name }}
              </span>
              <span class="text-[9.5px] text-muted-foreground font-mono leading-none mt-1">
                {{ formatBytes(selectedFile.size) }}
              </span>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            @click="removeFile" 
            class="text-destructive hover:bg-destructive/10 rounded-xl size-8 cursor-pointer shadow-none"
          >
            <Trash2Icon class="size-4" />
          </Button>
        </div>
      </div>

      <!-- Step-by-Step Guide Section -->
      <div class="flex flex-col gap-3">
        <div class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
          <span class="size-2 rounded-full bg-primary shrink-0" />
          {{ languageStore.t('راهنمای خروجی گرفتن از تلگرام', 'How to Export from Telegram') }}
        </div>

        <div class="flex flex-col gap-3 p-4 bg-background/40 dark:bg-card/30 rounded-2xl border border-border/50 text-start">
          <div class="flex gap-2.5 text-[11px] text-muted-foreground leading-relaxed">
            <span class="font-extrabold text-primary">۱.</span>
            <div class="flex-1">
              {{ languageStore.t('نسخه دسکتاپ تلگرام (Telegram Desktop) را باز کرده و وارد کانال خود شوید.', 'Open Telegram Desktop and go to your channel.') }}
            </div>
          </div>
          
          <div class="flex gap-2.5 text-[11px] text-muted-foreground leading-relaxed">
            <span class="font-extrabold text-primary">۲.</span>
            <div class="flex-1">
              {{ languageStore.t('از منوی سه نقطه بالا سمت راست، گزینه Export channel history را انتخاب کنید.', 'Select Export channel history from the three-dots menu.') }}
            </div>
          </div>
          
          <div class="flex gap-2.5 text-[11px] text-muted-foreground leading-relaxed">
            <span class="font-extrabold text-primary">۳.</span>
            <div class="flex-1">
              {{ languageStore.t('تیک دانلود عکس‌ها و ویدیوها را بردارید تا فرآیند سبک‌تر انجام شود.', 'Uncheck media options to make the file size smaller.') }}
            </div>
          </div>
          
          <div class="flex gap-2.5 text-[11px] text-muted-foreground leading-relaxed font-bold text-amber-600 dark:text-amber-500">
            <span class="font-extrabold">۴.</span>
            <div class="flex-1">
              {{ languageStore.t('حیاتی: قالب خروجی (Format) را حتماً روی حالت JSON تنظیم کنید.', 'CRITICAL: Change the format from HTML to JSON.') }}
            </div>
          </div>
          
          <div class="flex gap-2.5 text-[11px] text-muted-foreground leading-relaxed">
            <span class="font-extrabold text-primary">۵.</span>
            <div class="flex-1">
              {{ languageStore.t('روی دکمه Export کلیک کرده و فایل نهایی را در بخش بالا آپلود نمایید.', 'Click Export and upload the resulting file in the box above.') }}
            </div>
          </div>

          <!-- Alert Note -->
          <div class="mt-1 flex items-start gap-2.5 p-3 rounded-xl bg-amber-500/[0.03] border border-amber-500/10 text-[10px] text-amber-700 dark:text-amber-400 font-bold leading-normal">
            <InfoIcon class="size-4 text-amber-500 shrink-0 mt-0.5" />
            <div class="flex-1">
              {{ languageStore.t(
                'توجه: فایل‌های دارای فرمت HTML پشتیبانی نشده و بلافاصله در مرحله اعتبارسنجی رد خواهند شد.',
                'Make sure the exported file format is strictly JSON. HTML formats will be rejected.'
              ) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="flex justify-end pt-1">
        <Button 
          class="w-full rounded-xl px-5 py-4 text-xs font-bold transition-all cursor-pointer h-10"
          :disabled="!selectedFile" 
          @click="startImportPipeline"
        >
          {{ languageStore.t('تایید و شروع درون‌ریزی', 'Confirm & Start Import') }}
        </Button>
      </div>
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
