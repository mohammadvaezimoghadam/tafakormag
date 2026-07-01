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
import { useToastStore } from '@/stores/toastStore'
import { useLanguageStore } from '@/stores/languageStore'
import type { UserProfile } from '@/stores/userStore'

const props = defineProps<{
  isOpen: boolean
  userProfile?: UserProfile | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update', profile: { firstName: string; lastName: string; avatarUrl?: string }): void
}>()

const toastStore = useToastStore()
const languageStore = useLanguageStore()

const firstName = ref('')
const lastName = ref('')
const avatarPreview = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

watch(() => props.isOpen, (newVal) => {
  if (newVal && props.userProfile) {
    firstName.value = props.userProfile.first_name || ''
    lastName.value = props.userProfile.last_name || ''
    avatarPreview.value = props.userProfile.avatar || ''
  }
})

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
  if (!firstName.value.trim()) {
    toastStore.triggerToast(languageStore.t('لطفا نام خود را وارد کنید.', 'Please enter your first name.'), 'error')
    return
  }
  if (!lastName.value.trim()) {
    toastStore.triggerToast(languageStore.t('لطفا نام خانوادگی خود را وارد کنید.', 'Please enter your last name.'), 'error')
    return
  }

  emit('update', {
    firstName: firstName.value.trim(),
    lastName: lastName.value.trim(),
    avatarUrl: avatarPreview.value || undefined
  })
}

const handleCancel = () => {
  emit('close')
}

// Letter computation
const nameLetter = computed(() => {
  if (firstName.value) return firstName.value.trim().charAt(0)
  return props.userProfile?.phone?.charAt(0) || languageStore.t('ک', 'U')
})
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => { if (!val) handleCancel() }">
    <DialogContent 
      :show-close-button="false" 
      class="max-w-[380px] p-0 overflow-hidden flex flex-col text-start font-sans" 
      :dir="languageStore.dir"
    >
      
      <DialogDescription class="sr-only">
        {{ languageStore.t('فرم ویرایش اطلاعات شخصی پروفایل کاربر در سامانه تفکر.', 'Form to edit user personal profile information in Tafakor system.') }}
      </DialogDescription>

      <!-- Header -->
      <DialogHeader class="px-5 py-4 border-b border-border/40 flex flex-row items-center justify-between bg-gradient-to-br from-secondary/30 to-secondary/10 space-y-0">
        <DialogTitle class="text-xs font-extrabold text-foreground">{{ languageStore.t('ویرایش اطلاعات حساب', 'Edit Account Details') }}</DialogTitle>
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
        <!-- Avatar Uploader -->
        <div class="flex flex-col items-center gap-2">
          <Label class="text-[10px] text-muted-foreground font-semibold align-self-start">{{ languageStore.t('تصویر پروفایل شما:', 'Your Profile Image:') }}</Label>
          
          <div 
            @click="handleTriggerUpload"
            class="size-16 rounded-full bg-primary/5 hover:bg-primary/10 border border-border/80 hover:border-primary/30 flex items-center justify-center cursor-pointer relative overflow-hidden group transition-all"
            :title="languageStore.t('تغییر تصویر پروفایل', 'Change Profile Image')"
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
          <span class="text-[9px] text-muted-foreground">{{ languageStore.t('کلیک برای تغییر عکس', 'Click to change photo') }}</span>
        </div>

        <!-- Fields -->
        <div class="flex flex-col gap-1.5">
          <Label for="profile-firstname" class="text-[10.5px] text-muted-foreground font-semibold">{{ languageStore.t('نام:', 'First Name:') }}</Label>
          <Input 
            id="profile-firstname" 
            type="text" 
            v-model="firstName" 
            :placeholder="languageStore.t('نام خود را وارد کنید', 'Enter your first name')" 
            class="h-9.5 text-xs font-semibold focus-visible:ring-primary/20 text-start"
            maxlength="30"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="profile-lastname" class="text-[10.5px] text-muted-foreground font-semibold">{{ languageStore.t('نام خانوادگی:', 'Last Name:') }}</Label>
          <Input 
            id="profile-lastname" 
            type="text" 
            v-model="lastName" 
            :placeholder="languageStore.t('نام خانوادگی خود را وارد کنید', 'Enter your last name')" 
            class="h-9.5 text-xs font-semibold focus-visible:ring-primary/20 text-start"
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
          {{ languageStore.t('انصراف', 'Cancel') }}
        </Button>
        <Button 
          size="sm" 
          @click="handleSubmit"
          class="text-xs flex items-center gap-1.5 cursor-pointer"
        >
          <SaveIcon class="size-3.5" />
          {{ languageStore.t('ذخیره تغییرات', 'Save Changes') }}
        </Button>
      </div>

    </DialogContent>
  </Dialog>
</template>
