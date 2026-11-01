<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { 
  PencilIcon, 
  SparklesIcon, 
  Loader2Icon, 
  CheckCircle2Icon,
  AlertCircleIcon,
  XIcon
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import { submitEditProposal } from '@/api'
import type { PostEditProposal } from '@/types/editorial'

const languageStore = useLanguageStore()

const props = defineProps<{
  open: boolean
  postId: string | number
  currentContent?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'submitted', proposal: PostEditProposal): void
}>()

const proposedContent = ref('')
const reason = ref('')
const isSubmitting = ref(false)
const errorMessage = ref<string | null>(null)
const isSuccess = ref(false)

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    proposedContent.value = props.currentContent || ''
    reason.value = ''
    errorMessage.value = null
    isSuccess.value = false
  }
})

const handleSubmit = async () => {
  if (!proposedContent.value.trim()) {
    errorMessage.value = languageStore.t('متن پیشنهادی نمی‌تواند خالی باشد.', 'Proposed content cannot be empty.')
    return
  }

  if (proposedContent.value.trim() === props.currentContent?.trim()) {
    errorMessage.value = languageStore.t('متن پیشنهادی با متن فعلی یکسان است. لطفاً تغییرات خود را اعمال کنید.', 'Proposed content is identical to current content. Please apply your changes.')
    return
  }

  isSubmitting.value = true
  errorMessage.value = null

  try {
    const res = await submitEditProposal({
      post_id: props.postId,
      proposed_content: proposedContent.value.trim(),
      reason: reason.value.trim() || undefined
    })

    isSuccess.value = true
    emit('submitted', res.data)

    setTimeout(() => {
      emit('update:open', false)
    }, 1200)
  } catch (err: any) {
    errorMessage.value = err.response?.data?.error || languageStore.t('خطا در ارسال پیشنهاد ویرایش.', 'Failed to submit edit proposal.')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent 
      :show-close-button="false"
      class="max-w-[460px] p-0 overflow-hidden flex flex-col text-start font-sans rounded-3xl border border-border/50 bg-background shadow-2xl" 
      :dir="languageStore.dir"
    >
      <!-- Header Banner -->
      <DialogHeader class="px-5 py-4 bg-gradient-to-br from-primary/15 via-primary/10 to-transparent border-b border-border/40 flex flex-row items-center justify-between space-y-0">
        <div class="flex items-center gap-3">
          <div class="size-9 rounded-2xl bg-primary/20 text-primary flex items-center justify-center shadow-xs shrink-0">
            <PencilIcon class="size-4.5" />
          </div>
          <div class="flex flex-col text-start">
            <DialogTitle class="text-xs sm:text-sm font-black text-foreground font-sans">
              {{ languageStore.t('پیشنهاد ویرایش پست', 'Suggest Post Edit') }}
            </DialogTitle>
            <DialogDescription class="text-[10px] sm:text-[10.5px] text-muted-foreground mt-0.5">
              {{ languageStore.t('اصلاحات شما پس از تایید توسط ادمین در تاپیک و پیام‌رسان‌ها اعمال می‌شود.', 'Applied to channels once approved by admins.') }}
            </DialogDescription>
          </div>
        </div>

        <button 
          @click="emit('update:open', false)"
          class="size-7 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none shrink-0"
          :title="languageStore.t('بستن', 'Close')"
        >
          <XIcon class="size-4" />
        </button>
      </DialogHeader>

      <!-- Form Body -->
      <form @submit.prevent="handleSubmit" class="p-4 sm:p-5 flex flex-col gap-3.5 text-start">
        <!-- Error Alert -->
        <div 
          v-if="errorMessage" 
          class="p-2.5 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl text-xs flex items-center gap-2"
        >
          <AlertCircleIcon class="size-4 shrink-0" />
          <span>{{ errorMessage }}</span>
        </div>

        <!-- Success Alert -->
        <div 
          v-if="isSuccess" 
          class="p-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-xl text-xs flex items-center gap-2 font-medium"
        >
          <CheckCircle2Icon class="size-4 shrink-0 text-emerald-500" />
          <span>{{ languageStore.t('پیشنهاد ویرایش با موفقیت ثبت شد و به صف ویراستاری رفت.', 'Proposal submitted successfully to review queue.') }}</span>
        </div>

        <!-- Proposed Content Textarea -->
        <div class="flex flex-col gap-1.5">
          <Label class="text-[11px] font-extrabold text-foreground">
            {{ languageStore.t('متن پیشنهادی (ویرایش‌شده):', 'Proposed Content:') }}
          </Label>
          <textarea
            v-model="proposedContent"
            rows="5"
            class="w-full text-xs sm:text-[12.5px] p-3 rounded-2xl border border-border/70 bg-background/50 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all resize-y leading-relaxed text-foreground placeholder:text-muted-foreground"
            :placeholder="languageStore.t('متن اصلاح شده را اینجا وارد کنید...', 'Enter your revised text here...')"
          />
        </div>

        <!-- Reason Input -->
        <div class="flex flex-col gap-1.5">
          <Label class="text-[10.5px] font-semibold text-muted-foreground">
            {{ languageStore.t('دلیل یا توضیح ویرایش (اختیاری):', 'Reason for Edit (Optional):') }}
          </Label>
          <input
            v-model="reason"
            type="text"
            class="w-full text-xs h-9 px-3 rounded-xl border border-border/60 bg-background/50 focus:border-primary outline-none transition-all text-foreground placeholder:text-muted-foreground"
            :placeholder="languageStore.t('مثال: اصلاح غلط املایی، بهینه‌سازی لحن، افزودن پیوند...', 'e.g. Fixed typos, improved tone, added link...')"
          />
        </div>

        <!-- Footer -->
        <div class="pt-3 border-t border-border/40 flex items-center justify-end gap-2 mt-1">
          <Button
            type="button"
            variant="outline"
            size="sm"
            class="rounded-xl text-xs h-8.5 px-4 cursor-pointer border-border/70"
            @click="emit('update:open', false)"
          >
            {{ languageStore.t('انصراف', 'Cancel') }}
          </Button>

          <Button
            type="submit"
            size="sm"
            :disabled="isSubmitting || isSuccess"
            class="bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl text-xs h-8.5 px-4 gap-1.5 cursor-pointer font-bold shadow-none"
          >
            <Loader2Icon v-if="isSubmitting" class="size-3.5 animate-spin" />
            <SparklesIcon v-else class="size-3.5" />
            <span>{{ languageStore.t('ارسال برای بررسی', 'Submit Proposal') }}</span>
          </Button>
        </div>
      </form>
    </DialogContent>
  </Dialog>
</template>
