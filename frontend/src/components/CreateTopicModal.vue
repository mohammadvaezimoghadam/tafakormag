<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PlusIcon, CameraIcon, XIcon } from '@lucide/vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useToastStore } from '@/stores/toastStore'
import { useLanguageStore } from '@/stores/languageStore'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'create', topic: { title: string; description: string; post_badge?: string; image?: string }): void
}>()

const toastStore = useToastStore()
const languageStore = useLanguageStore()

const title = ref('')
const description = ref('')
const postBadge = ref('')
const avatarPreview = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

const handleTriggerUpload = () => {
  fileInputRef.value?.click()
}

const handleFileChange = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    if (file.size > 2 * 1024 * 1024) {
      toastStore.triggerToast(languageStore.t('حجم تصویر باید کمتر از ۲ مگابایت باشد.', 'Image size must be less than 2MB.'), 'error')
      return
    }
    const reader = new FileReader()
    reader.onload = (event) => {
      avatarPreview.value = event.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const handleSubmit = () => {
  if (!title.value.trim()) {
    toastStore.triggerToast(languageStore.t('لطفا نام تاپیک را وارد کنید.', 'Please enter the topic name.'), 'error')
    return
  }
  if (!description.value.trim()) {
    toastStore.triggerToast(languageStore.t('لطفا توضیحات تاپیک را وارد کنید.', 'Please enter the topic description.'), 'error')
    return
  }

  emit('create', {
    title: title.value.trim(),
    description: description.value.trim(),
    post_badge: postBadge.value.trim() || undefined,
    image: avatarPreview.value || undefined
  })

  // Reset inputs
  title.value = ''
  description.value = ''
  postBadge.value = ''
  avatarPreview.value = ''
}

const handleCancel = () => {
  title.value = ''
  description.value = ''
  postBadge.value = ''
  avatarPreview.value = ''
  emit('close')
}

// First letter placeholder computation
const nameLetter = computed(() => {
  return title.value ? title.value.trim().charAt(0) : languageStore.t('ت', 'T')
})
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => { if (!val) handleCancel() }">
    <DialogContent 
      :show-close-button="false" 
      class="max-w-[400px] p-0 overflow-hidden flex flex-col text-start rounded-3xl bg-card/95 backdrop-blur-2xl border border-border/80 dark:border-border/60 shadow-[0_20px_50px_rgba(0,0,0,0.2)]" 
      :dir="languageStore.dir"
    >
      
      <!-- Accessibility Description -->
      <DialogDescription class="sr-only">
        {{ languageStore.t('فرم ایجاد تاپیک جدید در پلتفرم تفکر با امکان بارگذاری آیکون و وارد کردن عنوان و توضیحات.', 'Form to create a new topic in Tafakor platform with image upload and title/description input.') }}
      </DialogDescription>

      <!-- Header -->
      <DialogHeader class="px-6 py-4.5 border-b border-border/40 flex flex-row items-center justify-between bg-gradient-to-br from-secondary/30 via-secondary/15 to-transparent space-y-0">
        <DialogTitle class="text-xs font-black text-foreground">{{ languageStore.t('ایجاد تاپیک جدید', 'Create New Topic') }}</DialogTitle>
        <button 
          @click="handleCancel"
          class="size-8 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none"
          :title="languageStore.t('بستن', 'Close')"
        >
          <XIcon class="size-4" />
        </button>
      </DialogHeader>

      <!-- Body Form -->
      <div class="p-6 flex flex-col gap-4">

        <!-- Avatar Uploader -->
        <div class="flex flex-col items-center gap-2">
          <Label class="text-[10px] text-muted-foreground font-semibold align-self-start">{{ languageStore.t('تصویر پروفایل تاپیک:', 'Topic Profile Image:') }}</Label>
          
          <div 
            @click="handleTriggerUpload"
            class="size-18 rounded-2xl bg-primary/5 hover:bg-primary/10 border border-border/70 hover:border-primary/40 flex items-center justify-center cursor-pointer relative overflow-hidden group transition-all shadow-xs"
            :title="languageStore.t('بارگذاری تصویر', 'Upload Image')"
          >
            <img 
              v-if="avatarPreview" 
              :src="avatarPreview" 
              class="w-full h-full object-cover" 
              alt="Avatar preview"
            />
            <div 
              v-else 
              class="size-full flex items-center justify-center text-primary font-bold text-lg select-none"
            >
              {{ nameLetter }}
            </div>
            
            <!-- Upload Hover Overlay -->
            <div class="absolute inset-0 bg-black/35 flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity">
              <CameraIcon class="size-4.5" />
            </div>
          </div>

          <input 
            ref="fileInputRef" 
            type="file" 
            accept="image/*" 
            class="hidden" 
            @change="handleFileChange" 
          />
          <span class="text-[9px] text-muted-foreground">{{ languageStore.t('کلیک برای بارگذاری تصویر (اختیاری)', 'Click to upload image (optional)') }}</span>
        </div>

        <!-- Fields -->
        <div class="flex flex-col gap-1.5">
          <Label for="topic-title" class="text-[10.5px] text-muted-foreground font-semibold">{{ languageStore.t('نام تاپیک:', 'Topic Name:') }}</Label>
          <Input 
            id="topic-title" 
            type="text" 
            v-model="title" 
            :placeholder="languageStore.t('مثال: سوالات عمومی دیزاین', 'e.g., General Design Questions')" 
            class="h-10 text-xs font-semibold rounded-xl border border-border/70 focus-visible:ring-1 focus-visible:ring-primary/40 text-start"
            maxlength="40"
            dir="auto"
            @keyup.enter="handleSubmit"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="topic-desc" class="text-[10.5px] text-muted-foreground font-semibold">{{ languageStore.t('توضیحات تاپیک:', 'Topic Description:') }}</Label>
          <Input 
            id="topic-desc" 
            type="text" 
            v-model="description" 
            :placeholder="languageStore.t('توضیح کوتاهی درباره این تاپیک بنویسید...', 'Write a short description about this topic...')" 
            class="h-10 text-xs font-semibold rounded-xl border border-border/70 focus-visible:ring-1 focus-visible:ring-primary/40 text-start"
            maxlength="100"
            dir="auto"
            @keyup.enter="handleSubmit"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <Label for="topic-badge" class="text-[10.5px] text-muted-foreground font-semibold">{{ languageStore.t('بج پست‌ها (امضای منبع):', 'Post Badge (Source Label):') }}</Label>
            <span class="text-[9px] text-muted-foreground">{{ languageStore.t('اختیاری', 'Optional') }}</span>
          </div>
          <Input 
            id="topic-badge" 
            type="text" 
            v-model="postBadge" 
            :placeholder="languageStore.t('مثال: @my_channel یا 📌 منبع: تفکر', 'e.g., @my_channel or 📌 Source: Tafakor')" 
            class="h-10 text-xs font-semibold rounded-xl border border-border/70 focus-visible:ring-1 focus-visible:ring-primary/40 text-start"
            maxlength="100"
            dir="auto"
            @keyup.enter="handleSubmit"
          />
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-6 py-4 bg-muted/20 border-t border-border/40 flex justify-end gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          @click="handleCancel"
          class="h-9 text-xs rounded-xl cursor-pointer font-semibold"
        >
          {{ languageStore.t('انصراف', 'Cancel') }}
        </Button>
        <Button 
          size="sm" 
          @click="handleSubmit"
          class="h-9 text-xs rounded-xl flex items-center gap-1.5 cursor-pointer font-semibold shadow-xs"
        >
          <PlusIcon data-icon="inline-start" />
          {{ languageStore.t('ایجاد تاپیک', 'Create Topic') }}
        </Button>
      </div>

    </DialogContent>
  </Dialog>
</template>
