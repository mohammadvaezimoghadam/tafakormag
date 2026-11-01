<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { XIcon, PlusIcon, CheckIcon, Loader2Icon } from '@lucide/vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import type { TopicFAQ } from '@/api'

const props = defineProps<{
  isOpen: boolean
  faqToEdit?: TopicFAQ | null
  isSubmitting?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', payload: { question: string; answer: string; order: number; is_published: boolean }): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()

const question = ref('')
const answer = ref('')
const order = ref<number>(0)
const isPublished = ref(true)

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      if (props.faqToEdit) {
        question.value = props.faqToEdit.question || ''
        answer.value = props.faqToEdit.answer || ''
        order.value = props.faqToEdit.order ?? 0
        isPublished.value = props.faqToEdit.is_published ?? true
      } else {
        question.value = ''
        answer.value = ''
        order.value = 0
        isPublished.value = true
      }
    }
  },
  { immediate: true }
)

const handleSubmit = () => {
  if (!question.value.trim()) {
    toastStore.triggerToast(languageStore.t('لطفاً عنوان سوال را وارد کنید.', 'Please enter the question title.'), 'error')
    return
  }
  if (!answer.value.trim()) {
    toastStore.triggerToast(languageStore.t('لطفاً پاسخ سوال را وارد کنید.', 'Please enter the answer.'), 'error')
    return
  }

  emit('save', {
    question: question.value.trim(),
    answer: answer.value.trim(),
    order: Number(order.value) || 0,
    is_published: isPublished.value
  })
}

const handleCancel = () => {
  emit('close')
}
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => { if (!val) handleCancel() }">
    <DialogContent
      :show-close-button="false"
      class="max-w-[400px] p-0 overflow-hidden flex flex-col text-start"
      :dir="languageStore.dir"
    >
      <!-- Accessibility Description -->
      <DialogDescription class="sr-only">
        {{ faqToEdit ? languageStore.t('فرم ویرایش سوال متداول تاپیک', 'Edit topic FAQ form') : languageStore.t('فرم ایجاد سوال متداول جدید برای تاپیک', 'Create new topic FAQ form') }}
      </DialogDescription>

      <!-- Header -->
      <DialogHeader class="px-5 py-4 border-b border-border/40 flex flex-row items-center justify-between bg-gradient-to-br from-secondary/30 to-secondary/10 space-y-0">
        <DialogTitle class="text-xs font-extrabold text-foreground">
          {{ faqToEdit ? languageStore.t('ویرایش سوال متداول', 'Edit FAQ') : languageStore.t('افزودن سوال متداول جدید', 'Add New FAQ') }}
        </DialogTitle>
        <button
          @click="handleCancel"
          class="size-6.5 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none"
          :title="languageStore.t('بستن', 'Close')"
        >
          <XIcon class="size-3.5" />
        </button>
      </DialogHeader>

      <!-- Body Form -->
      <div class="p-5 flex flex-col gap-4">
        <!-- Question Title -->
        <div class="flex flex-col gap-1.5">
          <Label for="faq-question" class="text-[10.5px] text-muted-foreground font-semibold">
            {{ languageStore.t('عنوان سوال:', 'Question Title:') }}
          </Label>
          <Input
            id="faq-question"
            type="text"
            v-model="question"
            :placeholder="languageStore.t('مثال: نحوه پیوستن به گروه چگونه است؟', 'e.g., How to join the group?')"
            class="h-9.5 text-xs font-semibold focus-visible:ring-primary/20 text-start"
            maxlength="250"
            dir="auto"
            :disabled="isSubmitting"
          />
        </div>

        <!-- Answer Textarea -->
        <div class="flex flex-col gap-1.5">
          <Label for="faq-answer" class="text-[10.5px] text-muted-foreground font-semibold">
            {{ languageStore.t('پاسخ تشریحی:', 'Detailed Answer:') }}
          </Label>
          <Textarea
            id="faq-answer"
            v-model="answer"
            :placeholder="languageStore.t('پاسخ کامل و شفاف به این سوال را بنویسید...', 'Write a clear, complete answer to this question...')"
            class="min-h-[110px] text-xs font-medium leading-relaxed focus-visible:ring-primary/20 text-start resize-none"
            dir="auto"
            :disabled="isSubmitting"
          />
        </div>

        <!-- Order & Publish Toggle -->
        <div class="flex items-center justify-between pt-1">
          <div class="flex items-center gap-2">
            <Label for="faq-order" class="text-[10.5px] text-muted-foreground font-semibold">
              {{ languageStore.t('اولویت نمایش:', 'Order / Priority:') }}
            </Label>
            <Input
              id="faq-order"
              type="number"
              v-model.number="order"
              class="h-8 w-18 text-xs font-semibold text-center"
              min="0"
              :disabled="isSubmitting"
            />
          </div>

          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              v-model="isPublished"
              class="rounded border-border/80 text-primary focus:ring-primary/20 size-3.5"
              :disabled="isSubmitting"
            />
            <span class="text-[11px] font-medium text-foreground">
              {{ languageStore.t('انتشار عمومی', 'Published') }}
            </span>
          </label>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-5 py-3.5 bg-muted/20 border-t border-border/40 flex justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          @click="handleCancel"
          class="text-xs cursor-pointer"
          :disabled="isSubmitting"
        >
          {{ languageStore.t('انصراف', 'Cancel') }}
        </Button>
        <Button
          size="sm"
          @click="handleSubmit"
          class="text-xs flex items-center gap-1.5 cursor-pointer"
          :disabled="isSubmitting"
        >
          <Loader2Icon v-if="isSubmitting" class="size-3.5 animate-spin" />
          <component :is="faqToEdit ? CheckIcon : PlusIcon" v-else class="size-3.5" />
          {{ faqToEdit ? languageStore.t('ذخیره تغییرات', 'Save Changes') : languageStore.t('افزودن سوال', 'Add FAQ') }}
        </Button>
      </div>
    </DialogContent>
  </Dialog>
</template>
