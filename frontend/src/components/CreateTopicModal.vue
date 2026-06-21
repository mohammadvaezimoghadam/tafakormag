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

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'create', topic: { title: string; description: string; image?: string }): void
}>()

const title = ref('')
const description = ref('')
const avatarPreview = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const errorMsg = ref('')

const handleTriggerUpload = () => {
  fileInputRef.value?.click()
}

const handleFileChange = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    if (file.size > 2 * 1024 * 1024) {
      errorMsg.value = 'حجم تصویر باید کمتر از ۲ مگابایت باشد.'
      return
    }
    errorMsg.value = ''
    const reader = new FileReader()
    reader.onload = (event) => {
      avatarPreview.value = event.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const handleSubmit = () => {
  errorMsg.value = ''
  if (!title.value.trim()) {
    errorMsg.value = 'لطفا نام تاپیک را وارد کنید.'
    return
  }
  if (!description.value.trim()) {
    errorMsg.value = 'لطفا توضیحات تاپیک را وارد کنید.'
    return
  }

  emit('create', {
    title: title.value.trim(),
    description: description.value.trim(),
    image: avatarPreview.value || undefined
  })

  // Reset inputs
  title.value = ''
  description.value = ''
  avatarPreview.value = ''
}

const handleCancel = () => {
  title.value = ''
  description.value = ''
  avatarPreview.value = ''
  errorMsg.value = ''
  emit('close')
}

// First letter placeholder computation
const nameLetter = computed(() => {
  return title.value ? title.value.trim().charAt(0) : 'ت'
})
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => { if (!val) handleCancel() }">
    <DialogContent :show-close-button="false" class="max-w-[380px] p-0 overflow-hidden flex flex-col text-right" dir="rtl">
      
      <!-- Accessibility Description (Hidden from view) -->
      <DialogDescription class="sr-only">
        فرم ایجاد تاپیک جدید در پلتفرم تفکر با امکان بارگذاری آیکون و وارد کردن عنوان و توضیحات.
      </DialogDescription>

      <!-- Header -->
      <DialogHeader class="px-5 py-4 border-b border-border/40 flex flex-row items-center justify-between bg-gradient-to-br from-secondary/30 to-secondary/10 space-y-0">
        <DialogTitle class="text-xs font-extrabold text-foreground">ایجاد تاپیک جدید</DialogTitle>
        <button 
          @click="handleCancel"
          class="size-6.5 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none"
          title="بستن"
        >
          <XIcon class="size-3.5" />
        </button>
      </DialogHeader>

      <!-- Body Form -->
      <div class="p-5 flex flex-col gap-4">
        <!-- Error banner -->
        <div v-if="errorMsg" class="p-2.5 bg-destructive/10 border border-destructive/20 rounded-lg text-[10.5px] font-semibold text-destructive">
          {{ errorMsg }}
        </div>

        <!-- Avatar Uploader -->
        <div class="flex flex-col items-center gap-2">
          <Label class="text-[10px] text-muted-foreground font-semibold align-self-start">تصویر پروفایل تاپیک:</Label>
          
          <div 
            @click="handleTriggerUpload"
            class="size-16 rounded-full bg-primary/5 hover:bg-primary/10 border border-border/80 hover:border-primary/30 flex items-center justify-center cursor-pointer relative overflow-hidden group transition-all"
            title="بارگذاری تصویر"
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
          <span class="text-[9px] text-muted-foreground">کلیک برای بارگذاری تصویر (اختیاری)</span>
        </div>

        <!-- Fields -->
        <div class="flex flex-col gap-1.5">
          <Label for="topic-title" class="text-[10.5px] text-muted-foreground font-semibold">نام تاپیک:</Label>
          <Input 
            id="topic-title" 
            type="text" 
            v-model="title" 
            placeholder="مثال: سوالات عمومی دیزاین" 
            class="h-9.5 text-xs font-semibold focus-visible:ring-primary/20"
            maxlength="40"
            @keyup.enter="handleSubmit"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="topic-desc" class="text-[10.5px] text-muted-foreground font-semibold">توضیحات تاپیک:</Label>
          <Input 
            id="topic-desc" 
            type="text" 
            v-model="description" 
            placeholder="توضیح کوتاهی درباره این تاپیک بنویسید..." 
            class="h-9.5 text-xs font-semibold focus-visible:ring-primary/20"
            maxlength="100"
            @keyup.enter="handleSubmit"
          />
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-5 py-3.5 bg-muted/20 border-t border-border/40 flex justify-end gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          @click="handleCancel"
          class="text-xs cursor-pointer"
        >
          انصراف
        </Button>
        <Button 
          size="sm" 
          @click="handleSubmit"
          class="text-xs flex items-center gap-1.5 cursor-pointer"
        >
          <PlusIcon data-icon="inline-start" />
          ایجاد تاپیک
        </Button>
      </div>

    </DialogContent>
  </Dialog>
</template>
