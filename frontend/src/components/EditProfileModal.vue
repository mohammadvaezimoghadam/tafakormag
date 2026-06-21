<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CameraIcon, XIcon, SaveIcon } from '@lucide/vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'

const props = defineProps<{
  isOpen: boolean
  userProfile: {
    first_name?: string
    last_name?: string
    avatar?: string
    phone: string
    [key: string]: any
  } | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: { first_name: string; last_name: string; avatarFile?: File }): void
}>()

const firstName = ref('')
const lastName = ref('')
const avatarPreview = ref('')
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const errorMsg = ref('')

// Initialize fields when userProfile is loaded
watch(() => props.userProfile, (newVal) => {
  if (newVal) {
    firstName.value = newVal.first_name || ''
    lastName.value = newVal.last_name || ''
    avatarPreview.value = newVal.avatar || ''
    selectedFile.value = null
  }
}, { immediate: true })

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
    selectedFile.value = file
    const reader = new FileReader()
    reader.onload = (event) => {
      avatarPreview.value = event.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const handleSubmit = () => {
  errorMsg.value = ''
  emit('save', {
    first_name: firstName.value.trim(),
    last_name: lastName.value.trim(),
    avatarFile: selectedFile.value || undefined
  })
}

const handleCancel = () => {
  firstName.value = props.userProfile?.first_name || ''
  lastName.value = props.userProfile?.last_name || ''
  avatarPreview.value = props.userProfile?.avatar || ''
  selectedFile.value = null
  errorMsg.value = ''
  emit('close')
}

const nameLetter = computed(() => {
  if (firstName.value) return firstName.value.charAt(0)
  return props.userProfile?.phone?.charAt(0) || 'ک'
})
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => { if (!val) handleCancel() }">
    <DialogContent :show-close-button="false" class="max-w-[380px] p-0 overflow-hidden flex flex-col text-right font-sans" dir="rtl">
      
      <DialogDescription class="sr-only">
        فرم ویرایش اطلاعات شخصی پروفایل کاربر در سامانه تفکر.
      </DialogDescription>

      <!-- Header -->
      <DialogHeader class="px-5 py-4 border-b border-border/40 flex flex-row items-center justify-between bg-gradient-to-br from-secondary/30 to-secondary/10 space-y-0">
        <DialogTitle class="text-xs font-extrabold text-foreground">ویرایش اطلاعات حساب</DialogTitle>
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
          <Label class="text-[10px] text-muted-foreground font-semibold align-self-start">تصویر پروفایل شما:</Label>
          
          <div 
            @click="handleTriggerUpload"
            class="size-16 rounded-full bg-primary/5 hover:bg-primary/10 border border-border/80 hover:border-primary/30 flex items-center justify-center cursor-pointer relative overflow-hidden group transition-all"
            title="تغییر تصویر پروفایل"
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
          <span class="text-[9px] text-muted-foreground">کلیک برای تغییر عکس</span>
        </div>

        <!-- Fields -->
        <div class="flex flex-col gap-1.5">
          <Label for="profile-firstname" class="text-[10.5px] text-muted-foreground font-semibold">نام:</Label>
          <Input 
            id="profile-firstname" 
            type="text" 
            v-model="firstName" 
            placeholder="نام خود را وارد کنید" 
            class="h-9.5 text-xs font-semibold focus-visible:ring-primary/20"
            maxlength="30"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="profile-lastname" class="text-[10.5px] text-muted-foreground font-semibold">نام خانوادگی:</Label>
          <Input 
            id="profile-lastname" 
            type="text" 
            v-model="lastName" 
            placeholder="نام خانوادگی خود را وارد کنید" 
            class="h-9.5 text-xs font-semibold focus-visible:ring-primary/20"
            maxlength="35"
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
          <SaveIcon class="size-3.5" />
          ذخیره تغییرات
        </Button>
      </div>

    </DialogContent>
  </Dialog>
</template>
