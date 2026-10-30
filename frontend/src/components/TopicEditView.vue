<script setup lang="ts">
import { ref, watch } from 'vue'
import PlatformHeader from './PlatformHeader.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { SaveIcon, RefreshCwIcon, CheckCircle2Icon, ImageIcon, UploadIcon, Trash2Icon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = defineProps<{
  topic: {
    title: string
    description: string
    post_badge?: string
    image?: string
    [key: string]: any
  }
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'save', updatedTopic: { title: string; description: string; post_badge: string; image: string | File }): void
}>()

const title = ref(props.topic?.title || '')
const description = ref(props.topic?.description || '')
const postBadge = ref(props.topic?.post_badge || '')

// File upload state refs
const imageFile = ref<File | null>(null)
const imagePreview = ref(props.topic?.image || '')
const fileInputRef = ref<HTMLInputElement | null>(null)

watch(
  () => props.topic,
  (newTopic) => {
    if (newTopic) {
      title.value = newTopic.title || ''
      description.value = newTopic.description || ''
      postBadge.value = newTopic.post_badge || ''
      if (!imageFile.value) {
        imagePreview.value = newTopic.image || ''
      }
    }
  },
  { deep: true }
)

const isSaving = ref(false)
const saveSuccess = ref(false)

const triggerImageSelect = () => {
  fileInputRef.value?.click()
}

const handleImageFileChange = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

const clearImage = () => {
  imageFile.value = null
  imagePreview.value = ''
  if (fileInputRef.value) fileInputRef.value.value = ''
}

const handleSave = () => {
  if (!title.value.trim()) return
  
  isSaving.value = true
  // Simulate network save delay
  setTimeout(() => {
    isSaving.value = false
    saveSuccess.value = true
    emit('save', {
      title: title.value.trim(),
      description: description.value.trim(),
      post_badge: postBadge.value.trim(),
      image: imageFile.value || imagePreview.value
    })
    
    setTimeout(() => {
      saveSuccess.value = false
      emit('back')
    }, 1000)
  }, 1200)
}
</script>

<template>
  <div 
    class="w-full flex flex-col gap-5 text-start font-sans pb-24" 
    :dir="languageStore.dir"
  >
    <!-- Header -->
    <PlatformHeader 
      is-inner-page
      :inner-title="languageStore.t('ویرایش تاپیک', 'Edit Topic')"
      :show-options-button="false"
      @back="emit('back')"
    />

    <!-- Edit Form Card -->
    <div class="w-full bg-card/90 dark:bg-card/90 backdrop-blur-md border border-border/70 dark:border-border/60 rounded-2xl p-5 sm:p-6 shadow-[0_2px_8px_rgba(0,0,0,0.03)] flex flex-col gap-5">
      <div class="flex flex-col gap-2 text-start">
        <Label for="topic-title" class="text-xs font-bold text-foreground/80">{{ languageStore.t('نام تاپیک', 'Topic Name') }}</Label>
        <Input 
          id="topic-title" 
          v-model="title" 
          :placeholder="languageStore.t('مثال: پشتیبانی فنی پلتفرم', 'e.g., Technical Support Platform')" 
          class="rounded-xl border-border/70 dark:border-border/60 bg-muted/20 focus-visible:ring-1 focus-visible:ring-primary/40 h-11 text-xs font-semibold text-start shadow-none"
          dir="auto"
        />
      </div>

      <div class="flex flex-col gap-2 text-start">
        <Label for="topic-desc" class="text-xs font-bold text-foreground/80">{{ languageStore.t('توضیحات تاپیک', 'Topic Description') }}</Label>
        <Textarea 
          id="topic-desc" 
          v-model="description" 
          :placeholder="languageStore.t('توضیحاتی درباره این تاپیک بنویسید...', 'Write a description about this topic...')" 
          class="rounded-xl border-border/70 dark:border-border/60 bg-muted/20 focus-visible:ring-1 focus-visible:ring-primary/40 min-h-[90px] text-xs font-semibold leading-relaxed text-start shadow-none resize-none"
          dir="auto"
        />
      </div>

      <div class="flex flex-col gap-2 text-start">
        <div class="flex items-center justify-between">
          <Label for="topic-badge" class="text-xs font-bold text-foreground/80">{{ languageStore.t('بج پست‌ها (امضای منبع)', 'Post Badge (Source Label)') }}</Label>
          <span class="text-[10px] text-muted-foreground">{{ languageStore.t('اختیاری', 'Optional') }}</span>
        </div>
        <Input 
          id="topic-badge" 
          v-model="postBadge" 
          :placeholder="languageStore.t('مثال: @my_channel یا 📌 منبع: تفکر', 'e.g., @my_channel or 📌 Source: Tafakor')" 
          class="rounded-xl border-border/70 dark:border-border/60 bg-muted/20 focus-visible:ring-1 focus-visible:ring-primary/40 h-11 text-xs font-medium text-start shadow-none"
          dir="auto"
          maxlength="100"
        />
        <span class="text-[10px] text-muted-foreground leading-normal">{{ languageStore.t('این متن کوتاه به صورت خودکار به انتهای پیام پست‌های این تاپیک اضافه می‌شود تا منبع انتشار مشخص باشد.', 'This short text will be automatically appended to the message of posts under this topic to identify the source.') }}</span>
      </div>

      <div class="flex flex-col gap-2 text-start">
        <Label class="text-xs font-bold text-foreground/80">{{ languageStore.t('تصویر تاپیک (اختیاری)', 'Topic Image (Optional)') }}</Label>
        
        <!-- Image Preview and Upload Controls -->
        <div class="flex items-center gap-4 p-3 rounded-xl bg-muted/15 border border-border/60">
          <div class="size-16 rounded-2xl border border-border/70 dark:border-border/60 bg-muted/30 overflow-hidden flex items-center justify-center shrink-0 shadow-[0_2px_6px_rgba(0,0,0,0.03)]">
            <img v-if="imagePreview" :src="imagePreview" class="w-full h-full object-cover" alt="Topic preview" />
            <ImageIcon v-else class="size-6 text-muted-foreground/60" />
          </div>
          <div class="flex flex-col gap-1.5 flex-1 text-start">
            <span class="text-[10px] text-muted-foreground leading-normal">{{ languageStore.t('برای تاپیک خود یک لوگو یا کاور انتخاب کنید.', 'Choose a logo or cover for your topic.') }}</span>
            <div class="flex gap-2">
              <Button 
                variant="secondary" 
                size="sm" 
                class="h-8.5 rounded-xl text-[10px] font-bold cursor-pointer active:scale-95 transition-all"
                @click="triggerImageSelect"
              >
                <UploadIcon class="size-3.5" data-icon="inline-start" />
                {{ languageStore.t('آپلود عکس', 'Upload Photo') }}
              </Button>
              <Button 
                v-if="imagePreview"
                variant="ghost" 
                size="sm" 
                class="h-8.5 rounded-xl text-[10px] font-bold text-destructive hover:bg-destructive/10 cursor-pointer active:scale-95 transition-all"
                @click="clearImage"
              >
                <Trash2Icon class="size-3.5" data-icon="inline-start" />
                {{ languageStore.t('حذف', 'Remove') }}
              </Button>
            </div>
            <input 
              type="file" 
              ref="fileInputRef" 
              @change="handleImageFileChange" 
              accept="image/*" 
              class="hidden" 
            />
          </div>
        </div>
      </div>

      <div class="h-[0.8px] bg-border/60 my-0.5" />

      <!-- Save Button -->
      <Button 
        @click="handleSave"
        :disabled="isSaving || saveSuccess || !title.trim()"
        class="w-full h-11 rounded-xl font-bold transition-all relative overflow-hidden active:scale-[0.98] cursor-pointer shadow-md shadow-primary/20"
        :variant="saveSuccess ? 'secondary' : 'default'"
      >
        <transition name="btn-content" mode="out-in">
          <div v-if="isSaving" class="flex items-center gap-2 justify-center">
            <RefreshCwIcon class="size-4 animate-spin" />
            <span>{{ languageStore.t('در حال ذخیره‌سازی...', 'Saving...') }}</span>
          </div>
          <div v-else-if="saveSuccess" class="flex items-center gap-2 justify-center text-emerald-600 dark:text-emerald-400">
            <CheckCircle2Icon class="size-4" />
            <span>{{ languageStore.t('تغییرات با موفقیت ذخیره شد', 'Changes saved successfully') }}</span>
          </div>
          <div v-else class="flex items-center gap-2 justify-center">
            <SaveIcon class="size-4" />
            <span>{{ languageStore.t('ذخیره تغییرات', 'Save Changes') }}</span>
          </div>
        </transition>
      </Button>
    </div>
  </div>
</template>

<style scoped>
.btn-content-enter-active,
.btn-content-leave-active {
  transition: all 0.2s ease-out;
}
.btn-content-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.btn-content-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
