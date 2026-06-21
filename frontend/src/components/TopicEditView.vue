<script setup lang="ts">
import { ref } from 'vue'
import PlatformHeader from './PlatformHeader.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { SaveIcon, RefreshCwIcon, CheckCircle2Icon } from '@lucide/vue'

const props = defineProps<{
  topic: {
    title: string
    description: string
    image?: string
    [key: string]: any
  }
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'save', updatedTopic: { title: string; description: string; image: string }): void
}>()

const title = ref(props.topic.title)
const description = ref(props.topic.description)
const image = ref(props.topic.image || '')

const isSaving = ref(false)
const saveSuccess = ref(false)

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
      image: image.value.trim()
    })
    
    setTimeout(() => {
      saveSuccess.value = false
      emit('back')
    }, 1000)
  }, 1200)
}
</script>

<template>
  <div class="w-full flex flex-col gap-5 text-right font-sans" dir="rtl">
    <!-- Header -->
    <PlatformHeader 
      is-inner-page
      inner-title="ویرایش تاپیک"
      :show-options-button="false"
      @back="emit('back')"
    />

    <!-- Edit Form Card -->
    <div class="w-full bg-card/25 dark:bg-card/15 border border-border/50 rounded-3xl p-5 shadow-xs flex flex-col gap-4.5">
      <div class="flex flex-col gap-2">
        <Label for="topic-title" class="text-xs font-bold text-foreground/80">نام تاپیک</Label>
        <Input 
          id="topic-title" 
          v-model="title" 
          placeholder="مثال: پشتیبانی فنی پلتفرم" 
          class="rounded-xl border-border/60 focus-visible:ring-primary/20 bg-background/50 h-10.5 font-bold"
        />
      </div>

      <div class="flex flex-col gap-2">
        <Label for="topic-desc" class="text-xs font-bold text-foreground/80">توضیحات تاپیک</Label>
        <Textarea 
          id="topic-desc" 
          v-model="description" 
          placeholder="توضیحاتی درباره این تاپیک بنویسید..." 
          class="rounded-xl border-border/60 focus-visible:ring-primary/20 bg-background/50 min-h-[90px] resize-none"
        />
      </div>

      <div class="flex flex-col gap-2">
        <Label for="topic-image" class="text-xs font-bold text-foreground/80">آدرس تصویر تاپیک (اختیاری)</Label>
        <Input 
          id="topic-image" 
          v-model="image" 
          placeholder="https://example.com/image.jpg" 
          class="rounded-xl border-border/60 focus-visible:ring-primary/20 bg-background/50 h-10.5 text-left"
          dir="ltr"
        />
        <p class="text-[9px] text-muted-foreground leading-normal">
          یک لینک تصویر یا آدرس تصویر از اینترنت وارد کنید تا به عنوان آیکون تاپیک استفاده شود.
        </p>
      </div>

      <div class="h-[1px] bg-border/40 my-1" />

      <!-- Save Button -->
      <Button 
        @click="handleSave"
        :disabled="isSaving || saveSuccess || !title.trim()"
        class="w-full h-11 rounded-xl font-bold transition-all relative overflow-hidden active:scale-[0.98] cursor-pointer"
        :variant="saveSuccess ? 'secondary' : 'default'"
      >
        <transition name="btn-content" mode="out-in">
          <div v-if="isSaving" class="flex items-center gap-2 justify-center">
            <RefreshCwIcon class="size-4 animate-spin" />
            <span>در حال ذخیره‌سازی...</span>
          </div>
          <div v-else-if="saveSuccess" class="flex items-center gap-2 justify-center text-emerald-600 dark:text-emerald-400">
            <CheckCircle2Icon class="size-4" />
            <span>تغییرات با موفقیت ذخیره شد</span>
          </div>
          <div v-else class="flex items-center gap-2 justify-center">
            <SaveIcon class="size-4" />
            <span>ذخیره تغییرات</span>
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
