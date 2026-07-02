<script setup lang="ts">
import { computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import {
  Loader2Icon,
  CheckCircle2Icon,
  CircleIcon,
  XCircleIcon,
  FileTextIcon,
  CheckIcon
} from '@lucide/vue'

// Component Props definition
interface Stage {
  id: string
  label: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

const props = withDefaults(defineProps<{
  isOpen: boolean
  title?: string
  description?: string
  progress?: number // 0 to 100
  isProcessing?: boolean
  currentStatus?: 'uploading' | 'validating' | 'importing' | 'completed' | 'failed' | 'idle'
  stages?: Stage[]
  actionButtonText?: string
}>(), {
  title: 'در حال پردازش داده‌ها',
  description: 'لطفاً تا اتمام فرآیند پردازش و درون‌ریزی، این پنجره را نبندید.',
  progress: 0,
  isProcessing: true,
  currentStatus: 'idle',
  actionButtonText: 'انتقال به تاپیک'
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'action'): void
}>()

// Default Pipeline Stages if none are passed custom
const defaultStages = computed<Stage[]>(() => {
  const status = props.currentStatus
  return [
    {
      id: 'upload',
      label: 'بارگذاری و خواندن فایل یادداشت‌ها',
      status: status === 'uploading'
        ? 'processing'
        : ['validating', 'importing', 'completed'].includes(status)
          ? 'completed'
          : status === 'failed' ? 'failed' : 'pending'
    },
    {
      id: 'validate',
      label: 'اعتبارسنجی ساختار مارک‌داون و محتوا',
      status: status === 'validating'
        ? 'processing'
        : ['importing', 'completed'].includes(status)
          ? 'completed'
          : status === 'failed' && ['uploading'].includes(status) ? 'pending' : status === 'failed' ? 'failed' : 'pending'
    },
    {
      id: 'import',
      label: 'درون‌ریزی انبوه و همگام‌سازی با ربات‌ها',
      status: status === 'importing'
        ? 'processing'
        : status === 'completed'
          ? 'completed'
          : status === 'failed' && ['uploading', 'validating'].includes(status) ? 'pending' : status === 'failed' ? 'failed' : 'pending'
    },
    {
      id: 'done',
      label: 'تکمیل نهایی و ثبت یادداشت‌ها',
      status: status === 'completed' ? 'completed' : 'pending'
    }
  ]
})

// Use custom stages if provided, otherwise default pipeline
const activeStages = computed<Stage[]>(() => {
  return props.stages && props.stages.length > 0 ? props.stages : defaultStages.value
})

// Block click outside / Escape key when processing
const handleInteractOutside = (event: Event) => {
  if (props.isProcessing) {
    event.preventDefault()
  }
}

const handleEscapeKeyDown = (event: Event) => {
  if (props.isProcessing) {
    event.preventDefault()
  }
}

const handleActionClick = () => {
  if (!props.isProcessing) {
    emit('action')
  }
}
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => !isProcessing && !val && emit('close')">
    <DialogContent
      class="sm:max-w-md font-[IRANYekanX] text-right rounded-3xl"
      dir="rtl"
      :show-close-button="!isProcessing"
      @pointer-down-outside="handleInteractOutside"
      @escape-key-down="handleEscapeKeyDown"
    >
      <!-- Dialog Header -->
      <DialogHeader class="text-right flex flex-col gap-1.5">
        <DialogTitle class="text-lg font-black text-foreground flex items-center gap-2.5">
          <div class="size-9 rounded-xl bg-primary/[0.04] flex items-center justify-center text-primary shrink-0">
            <FileTextIcon class="size-5" />
          </div>
          <span>{{ title }}</span>
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground leading-relaxed">
          {{ description }}
        </DialogDescription>
      </DialogHeader>

      <!-- Global Progress Section -->
      <div class="flex flex-col gap-2 mt-2">
        <div class="flex items-center justify-between text-xs font-bold px-1">
          <span class="text-muted-foreground">پیشرفت کل فرآیند</span>
          <span class="text-primary font-mono">{{ Math.round(progress) }}%</span>
        </div>
        <Progress :model-value="progress" class="h-2 rounded-full overflow-hidden bg-muted transition-all duration-300" />
      </div>

      <!-- Separator -->
      <Separator class="my-1 bg-border/40" />

      <!-- Pipeline Stages List -->
      <div class="flex flex-col gap-4 py-2">
        <h4 class="text-xs font-extrabold text-muted-foreground mb-1">
          مراحل اجرای عملیات خط لوله:
        </h4>

        <div
          v-for="stage in activeStages"
          :key="stage.id"
          class="flex items-center gap-3.5 px-2 py-1 rounded-xl transition-all duration-300"
          :class="stage.status === 'processing' ? 'bg-primary/[0.02] border border-primary/5 py-2 px-3 shadow-xs' : ''"
        >
          <!-- Stage Icon State -->
          <div class="shrink-0">
            <!-- Processing Spinner -->
            <Loader2Icon
              v-if="stage.status === 'processing'"
              class="size-5 text-primary animate-spin"
            />
            <!-- Completed Check -->
            <CheckCircle2Icon
              v-else-if="stage.status === 'completed'"
              class="size-5 text-green-500 fill-green-500/10"
            />
            <!-- Failed X icon -->
            <XCircleIcon
              v-else-if="stage.status === 'failed'"
              class="size-5 text-destructive fill-destructive/10"
            />
            <!-- Pending Empty Circle -->
            <CircleIcon
              v-else
              class="size-5 text-muted-foreground/45"
            />
          </div>

          <!-- Stage Label -->
          <div class="flex-1 flex flex-col gap-0.5">
            <span
              class="text-xs font-bold transition-colors duration-200"
              :class="{
                'text-foreground font-extrabold': stage.status === 'processing',
                'text-green-600': stage.status === 'completed',
                'text-destructive': stage.status === 'failed',
                'text-muted-foreground/60': stage.status === 'pending'
              }"
            >
              {{ stage.label }}
            </span>
          </div>
        </div>
      </div>

      <!-- Dialog Footer -->
      <DialogFooter class="flex sm:justify-start gap-2 mt-1">
        <Button
          class="w-full rounded-2xl py-5 text-xs font-bold transition-all duration-200"
          :disabled="isProcessing"
          @click="handleActionClick"
          variant="default"
        >
          <Loader2Icon v-if="isProcessing" class="size-4 animate-spin shrink-0 ml-1.5" />
          <CheckIcon v-else class="size-4 shrink-0 ml-1.5" />
          <span>{{ isProcessing ? 'در حال اجرای عملیات...' : actionButtonText }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
